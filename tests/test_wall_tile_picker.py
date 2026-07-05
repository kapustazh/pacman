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
        assert pick_for_neighbors(up, down, left, right) == BY_NEIGHBORS[neighbors]


def test_interior_and_isolated_walls_use_solid_fill() -> None:
    assert pick_for_neighbors(True, True, True, True) == TileKind.WALL
    assert pick_for_neighbors(False, False, False, False) == TileKind.WALL


def test_wall_tile_dict_has_no_duplicate_keys() -> None:
    assert len(BY_NEIGHBORS) == 16
