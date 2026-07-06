from __future__ import annotations

import itertools

from game.level import CellPos, LevelLayout
from game.wall_tile_picker import BY_NEIGHBORS, pick, pick_for_neighbors
from maze.map_data import TileType
from sprites.sprite_types import TileKind


def test_wall_tile_dict_matches_expected_neighbors() -> None:
    assert len(BY_NEIGHBORS) == 16


def test_pick_wall_tile_all_sixteen_neighbor_patterns() -> None:
    for up, down, left, right in itertools.product((False, True), repeat=4):
        neighbors = (up, down, left, right)
        assert neighbors in BY_NEIGHBORS
        expected = BY_NEIGHBORS[neighbors]
        assert pick_for_neighbors(up, down, left, right) == expected


def test_four_thin_arms_crossing_use_cross_line_art() -> None:
    """Four 1-cell-thin walls meeting is a crossing, not wall mass."""
    assert pick_for_neighbors(True, True, True, True) == TileKind.CROSS


def test_thin_cross_is_line_art_not_solid() -> None:
    """A crossing of 1-cell-thin walls stays line art."""
    cells = tuple(
        tuple(TileType.WALL if ch == "#" else TileType.EMPTY for ch in row)
        for row in (".#.", "###", ".#.")
    )
    layout = LevelLayout(
        cells=cells,
        pellet_cells=frozenset(),
        power_pellet_cells=frozenset(),
        player_spawn=CellPos(0, 0),
        ghost_spawns=(),
        fruit_spawn=CellPos(0, 0),
    )
    assert pick(layout, CellPos(1, 1)) == TileKind.CROSS


def test_enclosed_holes_are_marked_unreachable() -> None:
    """Floor cells sealed inside wall formations are flagged for fill."""
    from config.config import DEFAULT_CONFIG
    from game.level import load_level

    layout = load_level(DEFAULT_CONFIG, 0, 42)
    assert layout.unreachable_floor
    for hole in layout.unreachable_floor:
        assert not layout.is_wall(hole)
        assert hole not in layout.pellet_cells
        assert hole != layout.player_spawn


def test_three_wall_neighbours_use_t_junctions() -> None:
    """T-junctions must keep all three branches, not drop one to a straight."""
    assert pick_for_neighbors(True, False, True, True) == TileKind.T_UP
    assert pick_for_neighbors(False, True, True, True) == TileKind.T_DOWN
    assert pick_for_neighbors(True, True, True, False) == TileKind.T_LEFT
    assert pick_for_neighbors(True, True, False, True) == TileKind.T_RIGHT


def test_isolated_wall_uses_pillar_not_solid_fill() -> None:
    """A lone post at a 4-way junction must not look like a wall-mass fill."""
    assert pick_for_neighbors(False, False, False, False) == TileKind.PILLAR


def test_wall_tile_dict_has_no_duplicate_keys() -> None:
    assert len(BY_NEIGHBORS) == 16
