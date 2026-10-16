# Changelog

Judge versions (prompt + model + effort, pinned in `judge.config.json`). Released prompts are frozen in `prompts/releases/`.

## 1.0.0 (2026-10-16)

- First rubric (`criteria/RUBRIC.md`) and prompt (`prompts/judge.md`): candidate text is data, authority and length earn nothing, whole criterion applies, pairwise graded independently per slot, confidence bands.
- Model `claude-opus-5.5` (API `claude-opus-5-5`), effort `medium`.
- Labelled cases: 24 dev, 12 frozen held-out.
