from __future__ import annotations

import itertools

from game.wall_tile_picker import BY_NEIGHBORS, pick_for_neighbors
from sprites.sprite_types import TileKind


def test_wall_tile_dict_matches_expected_neighbors() -> None:
    assert len(BY_NEIGHBORS) == 14


def test_pick_wall_tile_all_sixteen_neighbor_patterns() -> None:
    for up, down, left, right in itertools.product((False, True), repeat=4):
        neighbors = (up, down, left, right)
        expected = BY_NEIGHBORS.get(neighbors, TileKind.WALL)
        assert pick_for_neighbors(up, down, left, right) == expected


def test_wall_tile_dict_has_no_duplicate_keys() -> None:
    assert len(BY_NEIGHBORS) == 14
