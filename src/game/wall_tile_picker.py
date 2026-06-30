# [transition] SCRUM-35 — wall autotile picker for pygame UI.

from __future__ import annotations

from game.level import CellPos, LevelLayout
from maze.map_data import TileType
from sprites.sprite_types import TileKind

BY_NEIGHBORS: dict[tuple[bool, bool, bool, bool], TileKind] = {
    (False, True, False, True): TileKind.CORNER_TL,
    (False, True, True, False): TileKind.CORNER_TR,
    (True, False, False, True): TileKind.CORNER_BL,
    (True, False, True, False): TileKind.CORNER_BR,
    (False, False, True, True): TileKind.HORIZONTAL,
    (True, True, False, False): TileKind.VERTICAL,
    (False, False, False, True): TileKind.CORNER_TL,
    (False, False, True, False): TileKind.CORNER_TR,
    (True, False, False, False): TileKind.CORNER_BL,
    (False, True, False, False): TileKind.CORNER_TL,
    (True, False, True, True): TileKind.HORIZONTAL,
    (False, True, True, True): TileKind.HORIZONTAL,
    (True, True, True, False): TileKind.VERTICAL,
    (True, True, False, True): TileKind.VERTICAL,
}


def pick_for_neighbors(
    up: bool,
    down: bool,
    left: bool,
    right: bool,
) -> TileKind:
    """Return wall tile kind for four neighbor wall flags."""
    return BY_NEIGHBORS.get((up, down, left, right), TileKind.WALL)


def pick(layout: LevelLayout, cell: CellPos) -> TileKind:
    """Pick maze wall sprite from neighbor walls around a grid cell."""
    up = _has_wall_neighbor(layout, CellPos(cell.row - 1, cell.col))
    down = _has_wall_neighbor(layout, CellPos(cell.row + 1, cell.col))
    left = _has_wall_neighbor(layout, CellPos(cell.row, cell.col - 1))
    right = _has_wall_neighbor(layout, CellPos(cell.row, cell.col + 1))
    return pick_for_neighbors(up, down, left, right)


def _has_wall_neighbor(layout: LevelLayout, pos: CellPos) -> bool:
    """Return True only for in-bounds wall cells (OOB is open for tile art)."""
    if pos.row < 0 or pos.col < 0:
        return False
    if pos.row >= layout.height:
        return False
    row = layout.cells[pos.row]
    if pos.col >= len(row):
        return False
    cell_type = row[pos.col]
    return bool(cell_type == TileType.WALL)
