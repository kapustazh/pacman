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


def test_fully_enclosed_wall_uses_solid_fill() -> None:
    assert pick_for_neighbors(True, True, True, True) == TileKind.WALL


def test_isolated_wall_uses_pillar_not_solid_fill() -> None:
    """A lone post at a 4-way junction must not look like a wall-mass fill."""
    assert pick_for_neighbors(False, False, False, False) == TileKind.PILLAR


def test_wall_tile_dict_has_no_duplicate_keys() -> None:
    assert len(BY_NEIGHBORS) == 16
