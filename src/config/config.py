"""Configuration loading and validation for Pac-man."""

import json
from typing import Any
from typing import cast

DEFAULT_CONFIG: dict[str, Any] = {
    "highscore_filename": "highscores.json",
    "lives": 3,
    "pacgum": 42,
    "points_per_pacgum": 10,
    "points_per_super_pacgum": 50,
    "points_per_ghost": 200,
    "seed": 42,
    "level_max_time": 90,
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
        {"width": 29, "height": 29}
        ],
    }


def remove_comments(content: str) -> str:
    """Remove lines starting with # from a JSON-like config file."""
    lines: list[str] = []

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        lines.append(line)
    return "\n".join(lines)


def load_config(path: str) -> dict[str, Any]:
    """load config safely. Never crash with traceback."""
    try:
        with open(path, "r", encoding="utf-8") as file:
            raw_content = file.read()
    except OSError:
        print(f"Warning: cannot open config file: {path}")
        print("Using default configuration.")
        return DEFAULT_CONFIG.copy()

    try:
        clean_content = remove_comments(raw_content)
        loaded = json.loads(clean_content)
    except json.JSONDecodeError:
        print("Warning: invalid JSON config.")
        print("Using default configuration.")
        return DEFAULT_CONFIG.copy()

    config = DEFAULT_CONFIG.copy()
    config.update(validate_config(loaded))
    return config


def get_positive_int(data: dict[str, Any], key: str, default: int) -> int:
    """Read a positive integer from config."""
    value = data.get(key, default)

    if not isinstance(value, int) or value <= 0:
        print(f"Warning: invalid value for {key}, using default {default}.")
        return default
    return value


def validate_config(data: dict[str, Any]) -> dict[str, Any]:
    """Validate known config keys and ignore unknown keys."""
    return {
        "highscore_filename": get_string(data, "highscore_filename",
                                         "highscores.json"),
        "lives": get_positive_int(data, "lives", 3),
        "pacgum": get_positive_int(data, "pacgum", 42),
        "points_per_pacgum": get_positive_int(data, "points_per_pacgum", 10),
        "points_per_super_pacgum": get_positive_int(
            data, "points_per_super_pacgum", 50),
        "points_per_ghost": get_positive_int(data, "points_per_ghost", 200),
        "seed": get_positive_int(data, "seed", 42),
        "level_max_time": get_positive_int(data, "level_max_time", 90),
        "levels": get_levels(data),
    }


def get_string(data: dict[str, Any], key: str, default: str) -> str:
    """Read a string from config"""
    value = data.get(key, default)

    if not isinstance(value, str) or not value:
        print(f"Warning: invalid value for {key}, using default {default}.")
        return default
    return value


def get_levels(data: dict[str, Any]) -> list[dict[str, int]]:
    """Read level definitions from config."""
    value = data.get("levels", DEFAULT_CONFIG["levels"])

    if not isinstance(value, list) or not value:
        print("Warning: invalid levels, using default levels.")
        return cast(list[dict[str, int]], DEFAULT_CONFIG["levels"])

    levels: list[dict[str, int]] = []

    for level in value:
        if not isinstance(level, dict):
            continue

        width = level.get("width", 21)
        height = level.get("height", 21)

        if not isinstance(width, int) or width < 5:
            width = 21
        if not isinstance(height, int) or height < 5:
            height = 21

        levels.append({"width": width, "height": height})

    if not levels:
        print("Warning: invalid levels, using default levels.")
        return cast(list[dict[str, int]], DEFAULT_CONFIG["levels"])

    if len(levels) < 10:
        print(
            "Warning: less than 10 levels configured. "
            "Using default levels."
        )
        return cast(list[dict[str, int]], DEFAULT_CONFIG["levels"])

    return levels
