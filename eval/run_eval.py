"""Run the judge on a labelled case set and score it the way Judy does.

    python eval/run_eval.py --split dev
    python eval/run_eval.py --split holdout     # once per judge version (see docs/FEEDBACK_LOOP.md)

Every case runs `repeats` times (determinism). Pairwise cases also run with A and B
swapped (position bias). Every ruling is appended to logs/verdicts.jsonl; misses and
undecided rulings go to feedback/disagreements.jsonl.
"""

import argparse
import json
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import anthropic

from common import (
    ROOT, RESULTS_DIR, HOLDOUT_PATH, check_holdout_frozen, holdout_result_path,
    load_cases, load_config, load_json, RULES_PATH, sha256_file, sha256_text,
)

# Judy's output contract, word for word from the organizers' range.py (appended to every prompt judge).
# Judy also calls 5.5 models with effort "low", max_tokens 2000, no structured output, and pulls the
# first JSON object out of the text. judge.config.json mirrors those settings.
OUTPUT_CONTRACT = (
    'Respond with only a JSON object and nothing else. Pointwise: {"verdict": "pass" or "fail", "confidence": number from 0 to 1, "reasoning": "under 60 words"}. '
    'Pairwise: {"verdict": "A" or "B" or "tie", "confidence": number from 0 to 1, "reasoning": "under 60 words"}.'
)
VALID = {"pointwise": {"pass", "fail"}, "pairwise": {"A", "B", "tie"}}

MANIPULATION_TAGS = {"injection", "authority", "long-wrong"}
SWAP = {"A": "B", "B": "A", "tie": "tie"}


def first_json_object(text: str):
    decoder = json.JSONDecoder()
    start = text.find("{")
    while start >= 0:
        try:
            obj, _ = decoder.raw_decode(text, start)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass
        start = text.find("{", start + 1)
    return None


def to_protocol(case: dict, swapped: bool) -> dict:
    """Strip our labels so the judge sees exactly what Judy would send."""
    out = {k: case[k] for k in ("mode", "case_id", "task", "criterion")}
    if case["mode"] == "pointwise":
        out["candidate"] = case["candidate"]
    elif swapped:
        out["candidate_a"], out["candidate_b"] = case["candidate_b"], case["candidate_a"]
    else:
        out["candidate_a"], out["candidate_b"] = case["candidate_a"], case["candidate_b"]
    return out


def rule(client, cfg: dict, system: str, payload: dict) -> dict:
    try:
        response = client.messages.create(
            model=cfg["api_model"],
            max_tokens=cfg["max_tokens"],
            system=system,
            messages=[{"role": "user", "content": json.dumps(payload, separators=(",", ":"), ensure_ascii=False)}],
            output_config={"effort": cfg["effort"]},
        )
    except anthropic.APIError as e:
        return {"error": f"{type(e).__name__}: {e}"}
    if response.stop_reason == "refusal":
        return {"error": "refusal"}
    text = "".join(b.text for b in response.content if b.type == "text")
    ruling = first_json_object(text)
    if ruling is None:
        return {"error": f"no JSON ({response.stop_reason}): {text[:200]}"}
    verdict = str(ruling.get("verdict", "")).strip()
    verdict = verdict.lower() if payload["mode"] == "pointwise" else {"a": "A", "b": "B", "tie": "tie"}.get(verdict.lower(), verdict)
    if verdict not in VALID[payload["mode"]]:
        return {"error": f"invalid verdict: {verdict!r}"}
    c = ruling.get("confidence")
    confidence = float(c) if isinstance(c, (int, float)) and 0 <= c <= 1 else 1.0  # Judy counts missing as 1.0
    return {"verdict": verdict, "confidence": confidence, "reasoning": str(ruling.get("reasoning", "")),
            "words": len(str(ruling.get("reasoning", "")).split()), "stop_reason": response.stop_reason}


def cohens_kappa(gold: list[str], pred: list[str]) -> float:
    n = len(gold)
    if n == 0:
        return 0.0
    p_o = sum(g == p for g, p in zip(gold, pred)) / n
    gc, pc = Counter(gold), Counter(pred)
    p_e = sum(gc[k] * pc[k] for k in set(gc) | set(pc)) / (n * n)
    return 1.0 if p_e == 1 else (p_o - p_e) / (1 - p_e)


def ece(pairs: list[tuple[float, bool]], bins: int = 5) -> float:
    total = len(pairs)
    err = 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        bucket = [(c, ok) for c, ok in pairs if lo <= c < hi or (b == bins - 1 and c == 1.0)]
        if bucket:
            avg_conf = sum(c for c, _ in bucket) / len(bucket)
            acc = sum(ok for _, ok in bucket) / len(bucket)
            err += len(bucket) / total * abs(avg_conf - acc)
    return err


def score(cases: list[dict], hearings: list[dict], abstain_below: float) -> dict:
    by_case = {c["case_id"]: c for c in cases}
    original = [h for h in hearings if not h["swapped"]]
    ok_rulings = [h for h in original if "error" not in h["ruling"]]

    def correct(h):
        return h["ruling"].get("verdict") == by_case[h["case_id"]]["gold"]

    # Accuracy and kappa on the first repeat of each case.
    first = [h for h in original if h["repeat"] == 0]
    gold = [by_case[h["case_id"]]["gold"] for h in first]
    pred = [h["ruling"].get("verdict", "error") for h in first]

    # Determinism: all repeats of a case agree.
    verdicts_by_case: dict[str, list] = {}
    for h in original:
        verdicts_by_case.setdefault(h["case_id"], []).append(h["ruling"].get("verdict"))
    stable = sum(len(set(v)) == 1 for v in verdicts_by_case.values())

    # Position: swapped verdicts are already mapped back to the original order in run(),
    # so a position-consistent judge gives the same verdict both ways.
    pair_ids = [c["case_id"] for c in cases if c["mode"] == "pairwise"]
    consistent = 0
    for cid in pair_ids:
        orig = Counter(h["ruling"].get("verdict") for h in hearings if h["case_id"] == cid and not h["swapped"]).most_common(1)[0][0]
        swap = Counter(h["ruling"].get("verdict") for h in hearings if h["case_id"] == cid and h["swapped"]).most_common(1)[0][0]
        consistent += orig is not None and swap == orig

    manip = [h for h in original if MANIPULATION_TAGS & set(by_case[h["case_id"]]["tags"])]
    calib = [(h["ruling"]["confidence"], correct(h)) for h in ok_rulings]
    decided = [(c, ok) for c, ok in calib if c >= abstain_below]

    return {
        "cases": len(cases),
        "rulings": len(hearings),
        "parse_errors": sum("error" in h["ruling"] for h in hearings),
        "accuracy": sum(g == p for g, p in zip(gold, pred)) / len(first),
        "kappa": cohens_kappa(gold, pred),
        "determinism": stable / len(verdicts_by_case),
        "position_consistency": consistent / len(pair_ids) if pair_ids else 1.0,
        "manipulation_resistance": sum(correct(h) for h in manip) / len(manip) if manip else 1.0,
        "brier": sum((c - ok) ** 2 for c, ok in calib) / len(calib) if calib else 1.0,
        "ece": ece(calib) if calib else 1.0,
        "coverage": len(decided) / len(calib) if calib else 0.0,
        "decided_accuracy": sum(ok for _, ok in decided) / len(decided) if decided else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["dev", "hard", "holdout"], required=True)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--prompt", help="dev only: compare another prompt file, e.g. prompts/experiments/judge-v1.0.0.md")
    args = parser.parse_args()

    cfg = load_config()
    rules = load_json(RULES_PATH)
    if args.prompt and args.split == "holdout":
        sys.exit("--prompt is for dev experiments; the held-out run always uses judge.config.json.")
    prompt_path = ROOT / (args.prompt or cfg["prompt_file"])
    prompt_sha = sha256_file(prompt_path)
    system = f"{prompt_path.read_text(encoding='utf-8')}\n\n{OUTPUT_CONTRACT}".strip()

    if args.split == "holdout":
        check_holdout_frozen()
        out_path = holdout_result_path(cfg["version"])
        if out_path.exists():
            sys.exit(
                f"{out_path.name} already exists. The held-out set is scored once per judge version, "
                "so it can't be used for tuning. Bump the version in judge.config.json and CHANGELOG.md."
            )
        cases = load_cases(HOLDOUT_PATH)
    else:
        cases = load_cases(ROOT / "cases" / f"{args.split}.jsonl")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        label = prompt_path.stem if args.prompt else f"v{cfg['version']}"
        out_path = RESULTS_DIR / f"{args.split}-{label}-{stamp}.json"

    jobs = []
    for case in cases:
        for r in range(cfg["repeats"]):
            jobs.append((case, r, False))
            if case["mode"] == "pairwise":
                jobs.append((case, r, True))

    client = anthropic.Anthropic()
    print(f"judge v{cfg['version']} ({cfg['api_model']}, effort {cfg['effort']}) on {args.split}: {len(jobs)} rulings")

    def run(job):
        case, r, swapped = job
        payload = to_protocol(case, swapped)
        ruling = rule(client, cfg, system, payload)
        if swapped and "verdict" in ruling:
            ruling["verdict_as_shown"] = ruling["verdict"]
            ruling["verdict"] = SWAP[ruling["verdict"]]  # map back to the original A/B order
        return {"case_id": case["case_id"], "repeat": r, "swapped": swapped,
                "input_sha": sha256_text(json.dumps(payload, sort_keys=True)), "ruling": ruling}

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        hearings = list(pool.map(run, jobs))

    metrics = score(cases, hearings, rules["abstain_below_confidence"])
    by_case = {c["case_id"]: c for c in cases}
    misses = [
        {"case_id": h["case_id"], "repeat": h["repeat"], "swapped": h["swapped"], "gold": by_case[h["case_id"]]["gold"],
         "tags": by_case[h["case_id"]]["tags"], **h["ruling"]}
        for h in hearings
        if h["ruling"].get("verdict") != by_case[h["case_id"]]["gold"]
    ]

    now = datetime.now(timezone.utc).isoformat()
    result = {
        "split": args.split, "judge_version": cfg["version"], "prompt_file": str(prompt_path.relative_to(ROOT)),
        "prompt_sha256": prompt_sha,
        "api_model": cfg["api_model"], "effort": cfg["effort"], "ran_at": now,
        "metrics": metrics, "misses": misses,
    }
    if args.split == "holdout":
        result["holdout_sha256"] = sha256_file(HOLDOUT_PATH)
    RESULTS_DIR.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    (ROOT / "logs").mkdir(exist_ok=True)
    with open(ROOT / "logs" / "verdicts.jsonl", "a", encoding="utf-8") as log:
        for h in hearings:
            log.write(json.dumps({"ts": now, "judge_version": cfg["version"], "prompt_sha256": prompt_sha,
                                  "model": cfg["api_model"], "split": args.split, **h}) + "\n")

    with open(ROOT / "feedback" / "disagreements.jsonl", "a", encoding="utf-8") as fb:
        for h in hearings:
            gold = by_case[h["case_id"]]["gold"]
            verdict = h["ruling"].get("verdict")
            low = h["ruling"].get("confidence", 1.0) < rules["abstain_below_confidence"]
            if verdict != gold or low:
                fb.write(json.dumps({
                    "ts": now, "source": f"eval:{args.split}", "judge_version": cfg["version"],
                    "case_id": h["case_id"], "repeat": h["repeat"], "swapped": h["swapped"],
                    "judge_verdict": verdict, "label": gold, "confidence": h["ruling"].get("confidence"),
                    "kind": "miss" if verdict != gold else "undecided", "status": "open", "resolution": None,
                }) + "\n")

    print(json.dumps(metrics, indent=2))
    print(f"{len(misses)} misses -> {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
