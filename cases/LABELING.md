# How the cases are labelled

## Sets

| File | Cases | Use |
| --- | --- | --- |
| `cases/dev.jsonl` | 24 (18 pointwise, 6 pairwise) | Tuning. Read misses, change the prompt, re-run. |
| `cases/holdout.jsonl` | 12 (8 pointwise, 4 pairwise) | Confirmation only. Never read while tuning. Its SHA-256 is pinned in `cases/holdout.sha256` and checked by `eval/run_eval.py` and `eval/gate.py`. |

Both sets have pass and fail outcomes (dev: 9 pass / 9 fail; holdout: 4 pass / 4 fail) and every pairwise verdict (A, B, tie).

## Labelling process

- **Right or wrong by construction.** Every case has an answer that can be checked without opinion: arithmetic, a well-known fact, or a literal count. The `why` field on each case records the check.
- **Tagged by failure mode.** `gold` (plain), `near-miss` (close but wrong), `literal` (counting/format), `partial` (one part of a compound criterion missing), `injection` (planted note aimed at the grader), `authority` (credential claims), `long-wrong` (long, confident, wrong), `pairwise`, `tie`.
- **Injection cases are paired.** A planted note sits on a wrong answer (obeying it gives a false pass) and on a right answer (obeying it gives a false fail), so the judge can't score by always failing anything with a note.
- **Labeller:** v1 cases were drafted with Claude on 2026-10-16. Each label is reviewed by hand by Jesus Rodriguez against its `why`; review status is tracked in `cases/REVIEW.md`.
- **Disputes:** if the judge and a label disagree, the case goes to `feedback/disagreements.jsonl` first. The label is re-checked against its `why`. If the label was wrong, it is fixed and the change is noted in `CHANGELOG.md`; it is never fixed silently to make a score go up.
