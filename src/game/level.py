# [transition] SCRUM-35 — LevelLayout from wehan LevelManager/MapData.

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from maze.map_data import TileType
from sprites.sprite_types import GhostKind


@dataclass(frozen=True, slots=True)
class CellPos:
    """Immutable row/column position on the level grid."""

    row: int
    col: int


@dataclass(frozen=True, slots=True)
class LevelLayout:
    """Immutable maze snapshot used to spawn a game world."""

    cells: tuple[tuple[TileType, ...], ...]
    pellet_cells: frozenset[CellPos]
    power_pellet_cells: frozenset[CellPos]
    player_spawn: CellPos
    ghost_spawns: tuple[tuple[GhostKind, CellPos], ...]
    fruit_spawn: CellPos
    # Floor cells the player can never reach: holes enclosed inside wall
    # formations. Rendered as solid wall-mass fill.
    unreachable_floor: frozenset[CellPos] = frozenset()

    @property
    def height(self) -> int:
        """Return the number of rows in the grid.

        Returns:
            Row count.
        """
        return len(self.cells)

    @property
    def width(self) -> int:
        """Return the number of columns in the grid.

        Returns:
            Column count, or zero when the grid is empty.
        """
        return len(self.cells[0]) if self.cells else 0

    def is_wall(self, pos: CellPos) -> bool:
        """Return whether a position is out of bounds or a wall tile.

        Args:
            pos: Grid position to test.

        Returns:
            True when the cell is blocked.
        """
        if pos.row < 0 or pos.col < 0:
            return True
        if pos.row >= self.height or pos.col >= self.width:
            return True
        return bool(self.cells[pos.row][pos.col] == TileType.WALL)


def load_level(
    config: dict[str, Any],
    level_index: int,
    seed: int,
) -> LevelLayout:
    """Build a procedural level layout from game config.

    Args:
        config: Game configuration dict with level sizes and pacgum count.
        level_index: Zero-based index into the configured level list.
        seed: Random seed for maze generation.

    Returns:
        A populated level layout ready for spawning.
    """
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
    layout: LevelLayout = LevelBuilder(pacgum_count).build(grid)
    return layout
