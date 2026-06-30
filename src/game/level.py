from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from maze.map_data import TileType
from sprites.sprite_types import GhostKind


@dataclass(frozen=True, slots=True)
class CellPos:
    """Immutable row/column position in level coordinates."""

    row: int
    col: int


@dataclass(frozen=True, slots=True)
class LevelLayout:
    """Immutable snapshot used to spawn GameWorld."""

    cells: tuple[tuple[TileType, ...], ...]
    pellet_cells: frozenset[CellPos]
    power_pellet_cells: frozenset[CellPos]
    player_spawn: CellPos
    ghost_spawns: tuple[tuple[GhostKind, CellPos], ...]
    fruit_spawn: CellPos

    @property
    def height(self) -> int:
        """Return number of rows."""
        return len(self.cells)

    @property
    def width(self) -> int:
        """Return number of columns."""
        return len(self.cells[0]) if self.cells else 0

    def is_wall(self, pos: CellPos) -> bool:
        """Return True when position is outside grid or blocked by wall."""
        if pos.row < 0 or pos.col < 0:
            return True
        if pos.row >= self.height or pos.col >= self.width:
            return True
        return self.cells[pos.row][pos.col] == TileType.WALL


def load_level(
    config: dict[str, Any],
    level_index: int,
    seed: int,
) -> LevelLayout:
    """Generate a LevelLayout from config-driven procedural maze."""
    from game.level_builder import LevelBuilder
    from maze.maze_adapter import MazeAdaptor

    levels = config.get("levels", [])
    fallback = {"width": 21, "height": 21}
    level = levels[level_index] if level_index < len(levels) else fallback
    width = max(5, level.get("width", 21))
    height = max(5, level.get("height", 21))
    pacgum_count = max(0, config.get("pacgum", 42))

    random.seed(seed)
    adaptor = MazeAdaptor()
    grid = adaptor.generate(width, height, seed)
    return LevelBuilder(pacgum_count).build(grid)
