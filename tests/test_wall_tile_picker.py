from __future__ import annotations

import itertools

from game.wall_tile_picker import BY_NEIGHBORS, pick_for_neighbors
from sprites.sprite_types import TileKind


def test_wall_tile_dict_matches_expected_neighbors() -> None:
    assert len(BY_NEIGHBORS) == 16


def test_pick_wall_tile_all_sixteen_neighbor_patterns() -> None:
    for up, down, left, right in itertools.product((False, True), repeat=4):
        neighbors = (up, down, left, right)
        assert neighbors in BY_NEIGHBORS
        expected = BY_NEIGHBORS[neighbors]
        assert pick_for_neighbors(up, down, left, right) == expected


def test_four_wall_neighbours_use_solid_wall_fill() -> None:
    """A cell walled on all sides is interior wall mass: solid fill."""
    assert pick_for_neighbors(True, True, True, True) == TileKind.WALL


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
