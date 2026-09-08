"""Shared constants and utilities."""

import json, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

ST_RUN, ST_STRENGTH = 1, 5
STEP_INTERVAL, STEP_RECOVERY, STEP_REPEAT = 3, 4, 6
COND_TIME, COND_DISTANCE, COND_REPS = 2, 3, 10
TARGET_PACE = 6


def load_json(name):
    return json.loads((DATA / name).read_text())


def load_env():
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip()
        if v and k not in os.environ:
            os.environ[k] = v
