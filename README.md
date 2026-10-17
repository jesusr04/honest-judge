# honest-judge

An LLM-as-a-judge for Gavel & Gown (Organized AI, Austin, 2026-10-16). It grades a reply against a criterion, pointwise (pass/fail) or pairwise (A/B/tie), and ignores planted instructions, authority claims, length and answer position.

Prompt judge on **Claude Opus 5.5**, released version **v1.1.0**.

## Results

All runs use Judy's exact call settings (copied from the organizer's `range.py`).

| Test | Opus 5.5 (ours) | Haiku 4.5 (stress check) |
| --- | --- | --- |
| Organizer practice range (37) | **100** | 100 |
| Dev cases (36) | **100%** | 97% |
| Hard cases (22) | **100%** | 86% |
| External cases, written by ChatGPT (15) | **100%** | 87% |
| Held-out, run once (12) | **100%**, gate SHIP | n/a |

Haiku dropping on our sets shows the tests catch real failures; the practice range alone doesn't.

## How it works

| Area | What we do | Where |
| --- | --- | --- |
| Criteria | Candidate text is data, never instructions; authority and length earn nothing; solve first, then grade | [prompts/judge.md](prompts/judge.md), [criteria/RUBRIC.md](criteria/RUBRIC.md) |
| Known answers | 85 labelled cases in 4 sets, tagged by trap type, human-reviewed | [cases/](cases/), [cases/REVIEW.md](cases/REVIEW.md) |
| Measurement | Kappa, Brier, calibration; held-out scored once per version | [eval/run_eval.py](eval/run_eval.py), [results/](results/) |
| Robustness | 3 repeats per case, both A/B orders, injection/authority/length traps | [eval/run_eval.py](eval/run_eval.py) |
| Decision rules | Ship / flag / block; any obeyed planted note blocks | [decision_rules.json](decision_rules.json), [docs/DECISION_RULES.md](docs/DECISION_RULES.md) |
| Feedback loop | Misses logged, fixed, measured; v1.2.0 rejected and rolled back | [docs/FEEDBACK_LOOP.md](docs/FEEDBACK_LOOP.md), [feedback/](feedback/), [CHANGELOG.md](CHANGELOG.md) |
| Operations | Pinned config, CI gate, frozen releases, verdict log, one-command rollback | [judge.config.json](judge.config.json), [docs/OPERATIONS.md](docs/OPERATIONS.md), [releases/](releases/) |

Full history: [docs/WORKLOG.md](docs/WORKLOG.md). Self-assessment: [JUDY.md](JUDY.md).

## Run it

```bash
pip install -r requirements.txt
# copy .env.example to .env and add ANTHROPIC_API_KEY (.env is gitignored)
python eval/run_eval.py --split dev        # also: hard, external
python eval/run_eval.py --split holdout    # once per version
python eval/gate.py                        # SHIP / FLAG / BLOCK
python eval/release.py                     # freeze a SHIP version
```
