"""Freeze a judge version that passed the gate, or roll back to an earlier one.

    python eval/release.py               # release the current version (gate must say SHIP)
    python eval/release.py --rollback 1.0.0

A release copies prompts/judge.md to prompts/releases/judge-v<version>.md and records
the prompt hash, model, effort and held-out metrics in releases/index.json. Released
files are never edited; a change is a new version.
"""

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone

from common import CONFIG_PATH, RELEASED_PROMPTS, RELEASES_INDEX, ROOT, load_config, load_json, sha256_file
from gate import evaluate


def release() -> None:
    verdict, reasons, result = evaluate()
    if verdict != "SHIP":
        sys.exit(f"Not released: gate says {verdict}\n" + "\n".join(f"  - {r}" for r in reasons))
    cfg = load_config()
    RELEASED_PROMPTS.mkdir(parents=True, exist_ok=True)
    frozen = RELEASED_PROMPTS / f"judge-v{cfg['version']}.md"
    if frozen.exists():
        sys.exit(f"{frozen.name} already exists; released versions are immutable.")
    shutil.copyfile(ROOT / cfg["prompt_file"], frozen)
    releases = load_json(RELEASES_INDEX) if RELEASES_INDEX.exists() else []
    releases.append({
        "version": cfg["version"], "prompt_file": str(frozen.relative_to(ROOT)).replace("\\", "/"),
        "prompt_sha256": sha256_file(frozen), "judy_model": cfg["judy_model"], "api_model": cfg["api_model"],
        "effort": cfg["effort"], "released_at": datetime.now(timezone.utc).isoformat(),
        "holdout_metrics": result["metrics"],
    })
    RELEASES_INDEX.parent.mkdir(exist_ok=True)
    RELEASES_INDEX.write_text(json.dumps(releases, indent=2), encoding="utf-8")
    print(f"Released v{cfg['version']} -> {frozen.relative_to(ROOT)}")


def rollback(version: str) -> None:
    releases = load_json(RELEASES_INDEX) if RELEASES_INDEX.exists() else []
    match = next((r for r in releases if r["version"] == version), None)
    if not match:
        sys.exit(f"v{version} was never released.")
    shutil.copyfile(ROOT / match["prompt_file"], ROOT / "prompts" / "judge.md")
    cfg = load_config()
    cfg.update(version=version, judy_model=match["judy_model"], api_model=match["api_model"], effort=match["effort"])
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    print(f"Rolled back to v{version}. Note it in CHANGELOG.md, commit, push, and re-run the Judy submit script.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rollback", metavar="VERSION")
    args = parser.parse_args()
    rollback(args.rollback) if args.rollback else release()
