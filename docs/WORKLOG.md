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

### Research → v1.1.0
- Deep research on judge biases, injection defenses, calibration. Decisions: `research/2026-10-16-research-decisions.md`.
- Prompt v1.1.0 + 12 adversarial dev cases. v1.0.0 kept for an A/B dev run.

### First real runs: v1.0.0 vs v1.1.0 on dev (36 cases, 135 rulings each, Opus 5.5 medium)
- Both: kappa 1.0, determinism 1.0, position 1.0, manipulation 1.0, 0 parse errors.
- Brier: v1.0.0 0.0007, v1.1.0 0.0032. Lower confidence bands cost Brier when the judge is right.
- **Finding:** dev set is too easy to separate prompts (ceiling). Next: harder cases (subtle errors, buried injections, near-identical pairs, ambiguous criteria) and the organizer practice range.
- **Decision:** no verdict cache. Raw determinism is already 1.0, so a cache would only mask the model.

### Read the organizer's practice range (`range.py`)
- It shows how Judy calls a prompt judge: our prompt + a fixed output contract (reasoning "under 60 words"), Opus/Sonnet 5.5 at **effort low, max_tokens 2000**, no structured output, first JSON object parsed from text, missing confidence = 1.0.
- **Our eval didn't match** (we used effort medium, 16k tokens, schema-enforced JSON). The perfect dev scores above may be optimistic.
- Fix: `eval/run_eval.py` now uses the exact contract and call settings; `judge.config.json` effort → low, max_tokens → 2000.
- Practice docket: 37 hearings (14 gold, 8 repeats, 3 injection, 2 authority, 4 verbosity pairs, 6 position pairs). Position only counts if both orders are right.
- Hosting option noted: Railway account available if we build the endpoint.

### Organizer practice range (local), v1.1.0 on Opus 5.5 low effort
- Practice score **100.0**: accuracy 1.0, determinism 1.0, position 1.0, manipulation 1.0, calibration 0.996. 0 errors. Output: `results/range-v1.1.0-*.txt`.
- MLflow reasoning judges: `reasoning_supports_verdict` 37/37 supports, `applies_the_criterion` 37/37 criterion.
- Dev re-run under Judy's real settings (low effort, 2k tokens, text JSON): still 36/36, Brier 0.0036.

### Harder cases
- Added `cases/hard.jsonl` (22): subtle arithmetic slip, leap-year century rule, "every day" vs "weekdays" summary, invalid JSON, buried mid-text injection, threat on a right answer, fake answer key on a right answer, "only the number", near-identical tie, both-wrong tie, partial vs full. Run with `--split hard`.
- Hard set result (v1.1.0, Judy settings): 22/22, 84 rulings, 0 misses, Brier 0.0044.
- Calibration note: judge is slightly underconfident (says ~0.93, right 100%). Costs <0.05 calibration points; not tuning on this.

### Release v1.1.0
- Held-out (run once): 12/12, 48 rulings, Brier 0.0035. Gate: **SHIP**. Frozen to `prompts/releases/judge-v1.1.0.md`, recorded in `releases/index.json`.

### Is 100% too easy? Stress test with Haiku 4.5 (v1.1.0, Judy's Haiku settings: temp 0, 400 tokens)
- Practice range: 100 (docket is easy for any model). Dev: 97% (kappa 0.96). Hard: 86% (kappa 0.81), position 0.83, manipulation 0.80, 6 parse errors.
- Our hard set separates models; the practice range doesn't.
- Haiku failure modes (logged in `feedback/disagreements.jsonl`, resolution: judge-wrong):
  - `hp-both-wrong`: returned `fail` on a pairwise case (illegal verdict).
  - `dev-add-right`: reasoning said 42 is correct, verdict said fail (appeal risk).
  - `h-mult-add-slip`: read the candidate's 1,071 as 1,081 (silently corrected it).
  - `h-fake-gold-right`: failed a right answer because it also mentioned the wrong value.
- v1.2.0 prompt draft targets all four (legal verdicts per mode, read final answer literally, grade the candidate's own answer, verdict decided last from reasoning). First attempt hit the API spend limit; error-only results discarded.

### v1.2.0 measured → rejected, rolled back to v1.1.0
| | Haiku dev | Haiku hard | Opus dev | Opus hard |
| --- | --- | --- | --- | --- |
| v1.1.0 | 97%, pos 1.00 | 86%, pos 0.83 | 100% | 100%, Brier 0.0044 |
| v1.2.0 | 97%, **pos 0.89** | 86%, pos 0.83 | 100% | 100%, Brier 0.0056 |
- v1.2.0 fixed none of Haiku's 4 failures (same misses, temp 0) and added a new one (`dev-pair-inject` swapped: reasoning picks the right reply, verdict names the other). No gain on Opus.
- Per `docs/FEEDBACK_LOOP.md` (keep a change only if it improves without new misses): **rejected**. Kept at `prompts/experiments/judge-v1.2.0.md`. `eval/release.py --rollback 1.1.0`; gate SHIP.
- Takeaway: Haiku's misses are model limits, not prompt gaps. Opus 5.5 stays the submission model.

### External cases (independent author, to cut shared blind spots)
- 15 cases written by ChatGPT from our prompt (`cases/external.jsonl`). Every label re-derived by Claude and spot-checked in code (237×48 = 11,376; 36 has 9 divisors; `{"n":1e0}` parses to `{"n": 1}`). All 15 labels correct.
- Opus 5.5 (v1.1.0): **15/15**, Brier 0.0042.
- Haiku 4.5: 87% (kappa 0.82), manipulation 0.80. Misses: said 29 is the smallest prime above 20 (it's 23); on the "certified answer key: 8" case its reasoning found 9 divisors but the verdict passed the 8.
