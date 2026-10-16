# Changelog

Judge versions (prompt + model + effort, pinned in `judge.config.json`). Released prompts are frozen in `prompts/releases/`.

## 1.1.0 (2026-10-16)

From `research/2026-10-16-research-decisions.md`:
- Prompt: explicit authority hierarchy (candidate = untrusted data), legit-injection exception, criterion decomposition (AND/OR/NOT/exactly), solve before reading, tie defined as substantive equivalence, confidence bands lowered (top 0.93), 4-part reasoning, final audit.
- Dev cases 24 → 36: fake system line, fake closing tag, Spanish injection, legit injection, fake citation, OR/NOT/exactly/at-least logic, verbose tie, opponent attack, fake gold label.
- v1.0.0 prompt kept at `prompts/experiments/judge-v1.0.0.md` for A/B comparison (`run_eval.py --prompt`).

## 1.0.0 (2026-10-16)

- First rubric (`criteria/RUBRIC.md`) and prompt (`prompts/judge.md`): candidate text is data, authority and length earn nothing, whole criterion applies, pairwise graded independently per slot, confidence bands.
- Model `claude-opus-5.5` (API `claude-opus-5-5`), effort `medium`.
- Labelled cases: 24 dev, 12 frozen held-out.
