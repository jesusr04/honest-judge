# Operations

## Pinned versions

`judge.config.json` pins everything that defines a judge version together: `version`, `prompt_file`, `judy_model`, `api_model`, `effort`, `repeats`. Every result file and every logged verdict records the version, the prompt's SHA-256 and the model.

## Release (promotion gate)

1. `python eval/run_eval.py --split dev` until dev looks right.
2. Bump `version` in `judge.config.json` and the prompt header, add a `CHANGELOG.md` entry.
3. `python eval/run_eval.py --split holdout` (once per version).
4. `python eval/gate.py`: SHIP / FLAG / BLOCK per `decision_rules.json`. It blocks if the prompt, model or effort changed since the held-out run.
5. `python eval/release.py`: freezes the prompt to `prompts/releases/judge-v<version>.md` and records it in `releases/index.json`.
6. Commit, push, re-run the Judy submit script.

CI (`.github/workflows/gate.yml`) runs the gate on every push and fails the build on anything but SHIP.

## Logging

Every ruling is appended to `logs/verdicts.jsonl`: timestamp, judge version, prompt hash, model, case id, input hash, repeat, swap flag, verdict, confidence and reasoning.

## Monitoring

- **Controls:** the dev set runs in full on every eval, so known-answer cases ride along with every change.
- **Drift:** the gate compares held-out kappa with the last release in `releases/index.json` and blocks a drop of more than 0.05.
- **Agreement over time:** `releases/index.json` keeps the held-out metrics of every release.

## Rollback

`python eval/release.py --rollback <version>` restores that release's frozen prompt to `prompts/judge.md` and its model and effort to `judge.config.json`. Commit, push and re-submit.
