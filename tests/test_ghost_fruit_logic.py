from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

SRC_ROOT = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_ROOT))

from config.config import DEFAULT_CONFIG
from game.fruit_schedule import fruit_for_level, spawn_seconds_for_level
from game.level import load_level
from sprites.sprite_types import FruitKind, GhostKind


def test_fruit_schedule_level_one() -> None:
    assert fruit_for_level(1) == FruitKind.CHERRY
    assert spawn_seconds_for_level(1) == (9, 41)


def test_fruit_schedule_high_levels_use_key() -> None:
    assert fruit_for_level(12) == FruitKind.KEY
    assert spawn_seconds_for_level(12) == (9, 41)


def test_level_ghost_spawns_are_walkable() -> None:
    layout = load_level(DEFAULT_CONFIG, 0, 42)
    assert len(layout.ghost_spawns) == 4
    kinds = {kind for kind, _cell in layout.ghost_spawns}
    assert kinds == set(GhostKind)
    for _kind, cell in layout.ghost_spawns:
        assert not layout.is_wall(cell)
