"""Shared helpers: paths, config, hashing."""

import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "judge.config.json"
RULES_PATH = ROOT / "decision_rules.json"
HOLDOUT_PATH = ROOT / "cases" / "holdout.jsonl"
HOLDOUT_SHA_PATH = ROOT / "cases" / "holdout.sha256"
RESULTS_DIR = ROOT / "results"
RELEASES_INDEX = ROOT / "releases" / "index.json"
RELEASED_PROMPTS = ROOT / "prompts" / "releases"


def load_dotenv() -> None:
    """Read KEY=value lines from .env (gitignored) without overriding the real environment."""
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_dotenv()


def sha256_file(path: Path) -> str:
    # Normalize line endings so the hash is the same on Windows and in CI.
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_config() -> dict:
    return load_json(CONFIG_PATH)


def load_cases(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def check_holdout_frozen() -> None:
    pinned = HOLDOUT_SHA_PATH.read_text(encoding="utf-8").split()[0]
    actual = sha256_file(HOLDOUT_PATH)
    if pinned != actual:
        raise SystemExit(
            f"cases/holdout.jsonl changed (pinned {pinned[:12]}, now {actual[:12]}). "
            "The held-out set is frozen; see cases/LABELING.md."
        )


def holdout_result_path(version: str) -> Path:
    return RESULTS_DIR / f"holdout-v{version}.json"
