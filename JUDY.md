# JUDY.md: how we judge our judge

Team: honest-judge. Prompt judge: `prompts/judge.md` on `claude-opus-5.5` (pinned in `judge.config.json`).

## Criteria
How are your judging criteria written down, made checkable and versioned?

The rubric is written down in `criteria/RUBRIC.md` and enforced by the judge prompt `prompts/judge.md`. Prompt changes are driven by research (`research/2026-10-16-research-decisions.md`). Each verdict (pass/fail, A/B/tie) has a definition, and each check (correct content, every part of a compound criterion, literal counts, ignore planted notes, ignore authority, ignore length, ignore position) has a pass example and a fail example. Rubric and prompt share one version number (currently 1.0.0) with semver rules in the rubric; every change is logged in `CHANGELOG.md` and each released version is frozen in `prompts/releases/`.

Evidence: criteria/RUBRIC.md, prompts/judge.md, CHANGELOG.md, judge.config.json

## Known answers
What labelled cases do you check your judge against, and how were they labelled?

48 labelled cases: 36 dev (`cases/dev.jsonl`) and 12 frozen held-out (`cases/holdout.jsonl`), pointwise and pairwise, with both pass and fail outcomes and every pairwise verdict including ties. Each case is right or wrong by construction (arithmetic, well-known facts, literal counts), records why in a `why` field, and is tagged by failure mode: near-miss, literal, partial, injection, authority, long-wrong, tie. Injection cases come in pairs (a planted note on a wrong answer and on a right answer). Labelling and dispute process: `cases/LABELING.md`; review log: `cases/REVIEW.md`.

Evidence: cases/dev.jsonl, cases/holdout.jsonl, cases/LABELING.md, cases/REVIEW.md

## Measurement
How do you measure whether your judge is right, and on what data?

`eval/run_eval.py` runs the judge exactly as Judy calls it (labels stripped, case sent as JSON) and computes Cohen's kappa (chance-corrected, not raw accuracy), accuracy, Brier score and ECE for calibration, coverage and accuracy above the confidence cutoff. Tuning uses the dev set only; the held-out set is scored once per version to confirm. Results are written to `results/`.

Evidence: eval/run_eval.py, results/, cases/holdout.sha256

## Robustness
What do you do to catch inconsistency, position bias and manipulation?

Every case is judged 3 times and determinism is the share of cases whose verdicts all agree. Every pairwise case is also judged with A and B swapped and the verdict mapped back; position consistency is the share that match. Manipulation resistance is accuracy on cases tagged injection (planted grader notes, fake JSON verdicts, HTML comments, fake SYSTEM lines), authority (credential claims) and long-wrong (long, confident, wrong answers). The prompt treats candidate text as data and grades each pairwise slot independently.

Evidence: eval/run_eval.py, cases/dev.jsonl, prompts/judge.md

## Decision rules
How do your judge's scores turn into actions, and what happens when it isn't sure?

`decision_rules.json` maps held-out metrics to SHIP / FLAG / BLOCK, applied by `eval/gate.py`. Hard stops block regardless of score: obeying any planted instruction (manipulation resistance below 100%), any parse error, or a kappa drop of more than 0.05 against the last release. Rulings with confidence below 0.60 are treated as undecided and routed to human review; they are logged to `feedback/disagreements.jsonl`.

Evidence: decision_rules.json, eval/gate.py, docs/DECISION_RULES.md

## Feedback loop
How do disagreements and mistakes flow back into your judge?

Every miss and undecided ruling is appended automatically to `feedback/disagreements.jsonl` with the judge version it challenged. Each is resolved as label-wrong, judge-wrong (becomes a new labelled dev case and, if needed, a rubric change) or ambiguous (rubric gets an explicit check). One change per version. The held-out set is frozen by hash and can only be scored once per version, so it is never used for tuning.

Evidence: docs/FEEDBACK_LOOP.md, feedback/disagreements.jsonl, eval/run_eval.py, cases/holdout.sha256

## Operations
How is your judge versioned, released, logged and rolled back?

`judge.config.json` pins prompt, model and effort together under one version. A version is released only if `eval/gate.py` says SHIP, enforced in CI (`.github/workflows/gate.yml`) and by `eval/release.py`, which freezes the prompt to `prompts/releases/` and records hashes and held-out metrics in `releases/index.json`. Every ruling is logged to `logs/verdicts.jsonl` with version, prompt hash, input hash, verdict, confidence and reasoning. Rollback: `python eval/release.py --rollback <version>`.

Evidence: judge.config.json, eval/gate.py, eval/release.py, .github/workflows/gate.yml, logs/verdicts.jsonl, docs/OPERATIONS.md
