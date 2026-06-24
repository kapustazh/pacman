from __future__ import annotations

import itertools

from game.wall_tile_picker import WallTilePicker
from sprites.sprite_types import TileKind

# Golden values from the original if-chain before dict refactor.
_EXPECTED_WALL_TILES: dict[tuple[bool, bool, bool, bool], TileKind] = {
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


def test_wall_tile_dict_matches_expected_neighbors() -> None:
    assert WallTilePicker.BY_NEIGHBORS == _EXPECTED_WALL_TILES


def test_pick_wall_tile_all_sixteen_neighbor_patterns() -> None:
    for up, down, left, right in itertools.product((False, True), repeat=4):
        neighbors = (up, down, left, right)
        expected = _EXPECTED_WALL_TILES.get(neighbors, TileKind.WALL)
        assert WallTilePicker.pick_for_neighbors(up, down, left, right) == expected


def test_wall_tile_dict_has_no_duplicate_keys() -> None:
    assert len(WallTilePicker.BY_NEIGHBORS) == len(_EXPECTED_WALL_TILES)
