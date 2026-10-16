"""Promotion gate: decide ship / flag / block for the current judge version.

    python eval/gate.py

Reads results/holdout-v<version>.json, checks it was produced by the prompt that is
in the repo now and by the frozen held-out set, then applies decision_rules.json.
Exit code 0 only on SHIP. Runs in CI (.github/workflows/gate.yml).
"""

import json
import sys

from common import (
    ROOT, RELEASES_INDEX, RULES_PATH, check_holdout_frozen, holdout_result_path,
    load_config, load_json, sha256_file,
)


def decide(metrics: dict, rules: dict, previous: dict | None) -> tuple[str, list[str]]:
    reasons = []
    hard = rules["hard_stops"]
    if metrics["manipulation_resistance"] < hard["manipulation_resistance_min"]:
        reasons.append(f"HARD STOP: manipulation_resistance {metrics['manipulation_resistance']:.2f} < {hard['manipulation_resistance_min']}")
    if metrics["parse_errors"] > hard["parse_error_max"]:
        reasons.append(f"HARD STOP: {metrics['parse_errors']} parse errors")
    if previous and previous["kappa"] - metrics["kappa"] > rules["max_kappa_drop_vs_previous_release"]:
        reasons.append(f"HARD STOP: kappa dropped {previous['kappa']:.2f} -> {metrics['kappa']:.2f} vs last release")
    if reasons:
        return "BLOCK", reasons

    def meets(level: str) -> list[str]:
        t = rules[level]
        fails = []
        if metrics["kappa"] < t["kappa_min"]:
            fails.append(f"kappa {metrics['kappa']:.2f} < {t['kappa_min']}")
        if metrics["determinism"] < t["determinism_min"]:
            fails.append(f"determinism {metrics['determinism']:.2f} < {t['determinism_min']}")
        if metrics["position_consistency"] < t["position_consistency_min"]:
            fails.append(f"position_consistency {metrics['position_consistency']:.2f} < {t['position_consistency_min']}")
        if metrics["brier"] > t["brier_max"]:
            fails.append(f"brier {metrics['brier']:.3f} > {t['brier_max']}")
        return fails

    ship_fails = meets("ship")
    if not ship_fails:
        return "SHIP", []
    flag_fails = meets("flag")
    return ("FLAG", ship_fails) if not flag_fails else ("BLOCK", flag_fails)


def last_release_metrics() -> dict | None:
    if not RELEASES_INDEX.exists():
        return None
    releases = load_json(RELEASES_INDEX)
    return releases[-1]["holdout_metrics"] if releases else None


def evaluate() -> tuple[str, list[str], dict]:
    cfg = load_config()
    rules = load_json(RULES_PATH)
    check_holdout_frozen()
    path = holdout_result_path(cfg["version"])
    if not path.exists():
        return "BLOCK", [f"no held-out result for v{cfg['version']}: run `python eval/run_eval.py --split holdout`"], {}
    result = load_json(path)
    prompt_sha = sha256_file(ROOT / cfg["prompt_file"])
    if result["prompt_sha256"] != prompt_sha:
        return "BLOCK", ["prompt changed since the held-out run; bump the version and re-run"], result
    if result["api_model"] != cfg["api_model"] or result["effort"] != cfg["effort"]:
        return "BLOCK", ["model or effort changed since the held-out run"], result
    verdict, reasons = decide(result["metrics"], rules, last_release_metrics())
    return verdict, reasons, result


if __name__ == "__main__":
    verdict, reasons, result = evaluate()
    print(f"GATE: {verdict}")
    for r in reasons:
        print(f"  - {r}")
    if result:
        print(json.dumps(result["metrics"], indent=2))
    sys.exit(0 if verdict == "SHIP" else 1)
