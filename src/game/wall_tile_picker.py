from __future__ import annotations

from typing import cast

from game.level import CellPos, CellType, LevelLayout
from sprites.sprite_types import TileKind


def _has_wall_neighbor(layout: LevelLayout, pos: CellPos) -> bool:
    """Return True only for in-bounds wall cells (OOB is open for tile art)."""
    if pos.row < 0 or pos.col < 0:
        return False
    if pos.row >= layout.height or pos.col >= layout.width:
        return False
    cell_type = cast(CellType, layout.cells[pos.row][pos.col])
    return bool(cell_type == CellType.WALL)


def _pick_wall_tile(
    up: bool,
    down: bool,
    left: bool,
    right: bool,
) -> TileKind:
    if down and right and not up and not left:
        return TileKind.CORNER_TL
    if down and left and not up and not right:
        return TileKind.CORNER_TR
    if up and right and not down and not left:
        return TileKind.CORNER_BL
    if up and left and not down and not right:
        return TileKind.CORNER_BR
    if left and right and not up and not down:
        return TileKind.HORIZONTAL
    if up and down and not left and not right:
        return TileKind.VERTICAL
    if right and not up and not down and not left:
        return TileKind.CORNER_TL
    if left and not up and not down and not right:
        return TileKind.CORNER_TR
    if up and not down and not left and not right:
        return TileKind.CORNER_BL
    if down and not up and not left and not right:
        return TileKind.CORNER_TL
    if up and left and right and not down:
        return TileKind.HORIZONTAL
    if down and left and right and not up:
        return TileKind.HORIZONTAL
    if up and down and left and not right:
        return TileKind.VERTICAL
    if up and down and right and not left:
        return TileKind.VERTICAL
    return TileKind.WALL


def pick_wall_tile(layout: LevelLayout, cell: CellPos) -> TileKind:
    """Pick maze wall sprite from neighbor walls around a grid cell."""
    up = _has_wall_neighbor(layout, CellPos(cell.row - 1, cell.col))
    down = _has_wall_neighbor(layout, CellPos(cell.row + 1, cell.col))
    left = _has_wall_neighbor(layout, CellPos(cell.row, cell.col - 1))
    right = _has_wall_neighbor(layout, CellPos(cell.row, cell.col + 1))
    return _pick_wall_tile(up, down, left, right)
