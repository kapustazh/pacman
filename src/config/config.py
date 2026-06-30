"""Configuration loading for Pac-Man."""

# [wehan] origin/wehan — JSON config loading.

from __future__ import annotations

import json
from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    "highscore_filename": "highscores.json",
    "pacgum": 42,
    "seed": 42,
    "levels": [
        {"width": 21, "height": 21},
        {"width": 21, "height": 21},
        {"width": 23, "height": 23},
        {"width": 23, "height": 23},
        {"width": 25, "height": 25},
        {"width": 25, "height": 25},
        {"width": 27, "height": 27},
        {"width": 27, "height": 27},
        {"width": 29, "height": 29},
        {"width": 29, "height": 29},
    ],
}


def _strip_json_comments(text: str) -> str:
    """Drop # comment lines and inline # suffixes."""
    lines: list[str] = []
    for line in text.splitlines():
        if "#" in line:
            line = line[: line.index("#")]
        lines.append(line)
    return "\n".join(lines)


def load_config(path: str) -> dict[str, Any]:
    """Load config JSON, merged over defaults. Never raises."""
    try:
        with open(path, "r", encoding="utf-8") as file:
            loaded = json.loads(_strip_json_comments(file.read()))
    except (OSError, json.JSONDecodeError):
        return DEFAULT_CONFIG.copy()
    if not isinstance(loaded, dict):
        return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG | loaded
