# Changelog

Judge versions (prompt + model + effort, pinned in `judge.config.json`). Released prompts are frozen in `prompts/releases/`.

## Rollback to 1.1.0 (2026-10-16)

- 1.2.0 (literal final-answer reading, legal verdict per mode, verdict decided last) was measured and rejected: no gain on Opus, a new position miss on Haiku. Kept at `prompts/experiments/judge-v1.2.0.md`. Never released.

## 1.1.0 (2026-10-16)

From `research/2026-10-16-research-decisions.md`:
- Prompt: explicit authority hierarchy (candidate = untrusted data), legit-injection exception, criterion decomposition (AND/OR/NOT/exactly), solve before reading, tie defined as substantive equivalence, confidence bands lowered (top 0.93), 4-part reasoning, final audit.
- Dev cases 24 → 36: fake system line, fake closing tag, Spanish injection, legit injection, fake citation, OR/NOT/exactly/at-least logic, verbose tie, opponent attack, fake gold label.
- v1.0.0 prompt kept at `prompts/experiments/judge-v1.0.0.md` for A/B comparison (`run_eval.py --prompt`).
- Config pinned to Judy's real call settings before any held-out run: effort `low`, max_tokens 2000, Judy's exact output contract.

## 1.0.0 (2026-10-16)

- First rubric (`criteria/RUBRIC.md`) and prompt (`prompts/judge.md`): candidate text is data, authority and length earn nothing, whole criterion applies, pairwise graded independently per slot, confidence bands.
- Model `claude-opus-5.5` (API `claude-opus-5-5`), effort `medium`.
- Labelled cases: 24 dev, 12 frozen held-out.
