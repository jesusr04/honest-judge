# Work log

Dated record of everything we build, test, find and decide. Newest at the bottom. Research notes live in `research/`, eval outputs in `results/`, every ruling in `logs/verdicts.jsonl`.

## 2026-10-16

### Setup (v1.0.0)
- Read the event rules, Judge Protocol v1 and the 24 audited practices (`/api/audit/checks`). Mapped each practice to a file in this repo (see `JUDY.md`).
- Chose a **prompt judge** on `claude-opus-5.5` for v1: accuracy is the largest charge (30) and the strongest model is the safest start. Endpoint judge is under evaluation (`research/`).
- Wrote the rubric (`criteria/RUBRIC.md`) and prompt (`prompts/judge.md`) around the trial's charges: candidate text is data, authority and length earn nothing, whole criterion applies, pairwise slots graded independently, confidence bands, never 1.0.
- Drafted 24 dev + 12 held-out cases tagged by failure mode; froze the held-out set by SHA-256 (`cases/holdout.sha256`). Label review pending (`cases/REVIEW.md`).

### Testing the eval harness itself (before spending API calls)
- Fed `score()` a synthetic perfect judge and a synthetic rubber-stamp judge (always pass / always A).
- **Found a bug:** position consistency scored the perfect judge at 0.33. Swapped verdicts were mapped back to the original order in `run()` and then flipped again in `score()`. Fixed in `eval/run_eval.py`; re-test gave perfect = 1.0, rubber stamp = 0.0, as expected.
- Gate check: `eval/gate.py` correctly returns BLOCK with no held-out result.

### Ops
- Added `.env` loading (gitignored) for the API key; `.env.example` committed instead.
