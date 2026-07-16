# [transition] SCRUM-35 — wall autotile picker for pygame UI.

from __future__ import annotations

from game.level import CellPos, LevelLayout
from maze.map_data import TileType
from sprites.sprite_types import TileKind

# up, down, left, right
_BY_NEIGHBORS: dict[tuple[bool, bool, bool, bool], TileKind] = {
    (False, True, False, True): TileKind.CORNER_TL,
    (False, True, True, False): TileKind.CORNER_TR,
    (True, False, False, True): TileKind.CORNER_BL,
    (True, False, True, False): TileKind.CORNER_BR,
    (False, False, True, True): TileKind.HORIZONTAL,
    (True, True, False, False): TileKind.VERTICAL,
    (False, False, False, True): TileKind.HORIZONTAL,
    (False, False, True, False): TileKind.HORIZONTAL,
    (True, False, False, False): TileKind.VERTICAL,
    (False, True, False, False): TileKind.VERTICAL,
    # Three-wall-neighbour cells are T-junctions; four are a cross. These
    # used to drop the odd branch (rendering a plain straight) or fall back
    # to a solid block, which left gaps and stray squares in the maze.
    (True, False, True, True): TileKind.T_UP,
    (False, True, True, True): TileKind.T_DOWN,
    (True, True, True, False): TileKind.T_LEFT,
    (True, True, False, True): TileKind.T_RIGHT,
    # Four thin arms crossing (a wall mass is caught earlier by pick()).
    (True, True, True, True): TileKind.CROSS,
    # A wall cell with no wall neighbours at all is a lone post at a 4-way
    # junction (common in this maze generator's checkerboard layout), not an
    # enclosed wall mass — give it its own small "pillar" art, not a full
    # solid-fill block that reads as a disconnected obstacle.
    (False, False, False, False): TileKind.PILLAR,
}

_BUILT_TILES = frozenset(
    {
        TileKind.PILLAR,
        TileKind.T_UP,
        TileKind.T_DOWN,
        TileKind.T_LEFT,
        TileKind.T_RIGHT,
        TileKind.CROSS,
    }
)
BUILT_TILE_NEIGHBOR_MASKS: dict[TileKind, tuple[bool, bool, bool, bool]] = {
    kind: mask for mask, kind in _BY_NEIGHBORS.items() if kind in _BUILT_TILES
}


def pick(layout: LevelLayout, cell: CellPos) -> TileKind:
    """Choose a wall sprite for one grid cell from its neighbors.

    Args:
        layout: Level grid used to inspect adjacent cells.
        cell: Wall cell whose tile art is needed.

    Returns:
        Autotile kind matching local wall connectivity.
    """
    up = _has_wall_neighbor(layout, CellPos(cell.row - 1, cell.col))
    down = _has_wall_neighbor(layout, CellPos(cell.row + 1, cell.col))
    left = _has_wall_neighbor(layout, CellPos(cell.row, cell.col - 1))
    right = _has_wall_neighbor(layout, CellPos(cell.row, cell.col + 1))
    return _BY_NEIGHBORS.get((up, down, left, right), TileKind.WALL)


def _has_wall_neighbor(layout: LevelLayout, pos: CellPos) -> bool:
    """Return whether an adjacent cell is an in-bounds wall.

    Args:
        layout: Level grid to query.
        pos: Neighbor position to inspect; out-of-bounds counts as open.

    Returns:
        True when the neighbor exists and is a wall tile.
    """
    if pos.row < 0 or pos.col < 0:
        return False
    if pos.row >= layout.height:
        return False
    row = layout.cells[pos.row]
    if pos.col >= len(row):
        return False
    cell_type = row[pos.col]
    return bool(cell_type == TileType.WALL)
