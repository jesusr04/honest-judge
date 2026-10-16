# Feedback loop

## 1. Capture

Every miss and every undecided ruling (confidence < 0.60) from an eval run is appended automatically to `feedback/disagreements.jsonl` by `eval/run_eval.py`, with the judge version, case, the judge's verdict, the label and `status: open`. Overrides from Judy's trial or Jev's appeals are added by hand in the same format with `source: judy` or `source: jev`.

## 2. Review

Each open row is resolved one of three ways, and the row's `status` and `resolution` are updated:

| Resolution | Meaning | What changes |
| --- | --- | --- |
| `label-wrong` | The label was wrong, not the judge | Fix the case in `cases/dev.jsonl`, note it in `CHANGELOG.md` |
| `judge-wrong` | The judge broke a rule in `criteria/RUBRIC.md` | Becomes a new labelled dev case (same failure tag) and, if no existing rule covers it, a rubric/prompt change |
| `ambiguous` | The criterion allows both readings | Rubric gets an explicit check for it, with an example |

## 3. Fix the smallest thing

One change per version. Re-run `--split dev` and keep the change only if dev metrics improve without a new miss.

## 4. No tuning on the held-out set

- Disagreements on held-out cases are recorded but **never** turned into dev cases or prompt edits for the same version.
- `cases/holdout.jsonl` is frozen: its hash is pinned in `cases/holdout.sha256` and the scripts refuse to run if it changes.
- `eval/run_eval.py --split holdout` refuses to run twice for the same version, so the held-out set can't be used to iterate. Any prompt change means a version bump.

## 5. Release

`python eval/gate.py` then `python eval/release.py` (see `docs/OPERATIONS.md`).
