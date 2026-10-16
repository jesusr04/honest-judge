# honest-judge

An LLM-as-a-judge built for Gavel & Gown (Organized AI, Austin, 2026-10-16). It grades a reply against a criterion, pointwise (pass/fail) or pairwise (A/B/tie), and is built to ignore planted instructions, authority claims, length and answer position.

- Judge prompt: `prompts/judge.md` (rubric: `criteria/RUBRIC.md`)
- Pinned config: `judge.config.json`
- How we judge the judge: `JUDY.md`

## Run it

```bash
pip install -r requirements.txt
# copy .env.example to .env and add ANTHROPIC_API_KEY (.env is gitignored)
python eval/run_eval.py --split dev        # tune here
python eval/run_eval.py --split holdout    # once per version
python eval/gate.py                        # SHIP / FLAG / BLOCK
python eval/release.py                     # freeze a SHIP version
```

## Layout

| Path | What |
| --- | --- |
| `prompts/judge.md` | The judge |
| `criteria/RUBRIC.md` | Verdict definitions and checks, with examples |
| `cases/` | Labelled dev and frozen held-out cases, labelling process |
| `eval/` | Eval runner, promotion gate, release and rollback |
| `decision_rules.json` | Ship / flag / block thresholds and hard stops |
| `feedback/disagreements.jsonl` | Misses and undecided rulings, with resolution |
| `logs/verdicts.jsonl` | Every ruling, with version and hashes |
| `results/` | Metrics and misses per run |
| `releases/index.json` | Released versions and their held-out metrics |
| `docs/` | Decision rules, feedback loop, operations |
