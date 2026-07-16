"""Configuration loading and validation for Pac-man."""

import json
import sys
from pathlib import Path
from typing import Any
from typing import cast

from core.paths import is_frozen_build

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
        {"width": 29, "height": 29},
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


def reject_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    """ "Reject duplicate keys in JSON object."""
    result: dict[str, Any] = {}

    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate key: '{key}'")
        result[key] = value

    return result


def default_config() -> dict[str, Any]:
    """Return a copy of the built-in default configuration."""
    return DEFAULT_CONFIG.copy()


def resolve_config() -> dict[str, Any]:
    """Load the CLI config, or packaged defaults when no path is given.

    Returns:
        The resolved configuration.
    """
    frozen = is_frozen_build()
    usage = (
        f"Usage: {Path(sys.argv[0]).name} "
        f"{'[config.json]' if frozen else 'config.json'}"
    )
    if len(sys.argv) == 1 and frozen:
        return default_config()
    if len(sys.argv) != 2:
        raise SystemExit(usage)

    path = Path(sys.argv[1])
    if path.suffix.lower() != ".json":
        raise SystemExit(f"Error: configuration file must be JSON: {path}")
    if not path.is_file():
        raise SystemExit(f"Error: configuration file not found: {path}")
    return load_config(str(path))


def load_config(path: str) -> dict[str, Any]:
    """Load config safely. Never crash with traceback."""
    try:
        with open(path, "r", encoding="utf-8") as file:
            raw_content = file.read()
    except OSError:
        print(f"Warning: cannot open config file: {path}")
        print("Using default configuration.")
        return DEFAULT_CONFIG.copy()

    try:
        clean_content = remove_comments(raw_content)
        loaded = json.loads(
            clean_content,
            object_pairs_hook=reject_duplicate_keys,
        )
    except (json.JSONDecodeError, ValueError) as error:
        print(f"Warning: {error}.")
        print("Using default configuration.")
        return DEFAULT_CONFIG.copy()

    if not isinstance(loaded, dict):
        print("Warning: config must be a JSON object.")
        print("Using default configuration.")
        return DEFAULT_CONFIG.copy()

    config = DEFAULT_CONFIG.copy()
    config.update(validate_config(loaded))
    return config


def get_positive_int(data: dict[str, Any], key: str, default: int) -> int:
    """Read a positive integer from config."""
    if key not in data:
        print(f"Warning: missing {key}, using default {default}.")
        return default

    value = data[key]

    if type(value) is not int or value <= 0:
        print(f"Warning: invalid value for {key}, using default {default}.")
        return default
    return value


def validate_config(data: dict[str, Any]) -> dict[str, Any]:
    """Validate known config keys and ignore unknown keys."""
    return {
        "highscore_filename": get_string(
            data, "highscore_filename", "highscores.json"
        ),
        "lives": get_positive_int(data, "lives", 3),
        "pacgum": get_positive_int(data, "pacgum", 42),
        "points_per_pacgum": get_positive_int(data, "points_per_pacgum", 10),
        "points_per_super_pacgum": get_positive_int(
            data, "points_per_super_pacgum", 50
        ),
        "points_per_ghost": get_positive_int(data, "points_per_ghost", 200),
        "seed": get_positive_int(data, "seed", 42),
        "level_max_time": get_positive_int(data, "level_max_time", 90),
        "levels": get_levels(data),
    }


def get_string(data: dict[str, Any], key: str, default: str) -> str:
    """Read a string from config."""
    if key not in data:
        print(f"Warning: missing {key}, using default {default}.")
        return default

    value = data[key]

    if type(value) is not str or not value:
        print(f"Warning: invalid value for {key}, using default {default}.")
        return default
    return value


def get_levels(data: dict[str, Any]) -> list[dict[str, int]]:
    """Read level definitions from config."""
    if "levels" not in data:
        print("Warning: missing levels, using default levels.")
        return cast(list[dict[str, int]], DEFAULT_CONFIG["levels"])

    value = data["levels"]

    if not isinstance(value, list) or not value:
        print("Warning: invalid levels, using default levels.")
        return cast(list[dict[str, int]], DEFAULT_CONFIG["levels"])

    levels: list[dict[str, int]] = []

    for level in value:
        if not isinstance(level, dict):
            print("Warning: invalid level entry, skipping it.")
            continue

        if "width" not in level:
            print("Warning: missing level width, using default 21.")
            width = 21
        else:
            width = level["width"]
            if type(width) is not int or width < 5:
                print("Warning: invalid level width, using default 21.")
                width = 21
        if "height" not in level:
            print("Warning: missing level height, using default 21.")
            height = 21
        else:
            height = level["height"]
            if type(height) is not int or height < 5:
                print("Warning: invalid level height, using default 21.")
                height = 21

        levels.append({"width": width, "height": height})

    if not levels:
        print("Warning: invalid levels, using default levels.")
        return cast(list[dict[str, int]], DEFAULT_CONFIG["levels"])

    if len(levels) < 10:
        print(
            "Warning: less than 10 levels configured. " "Using default levels."
        )
        return cast(list[dict[str, int]], DEFAULT_CONFIG["levels"])

    return levels
