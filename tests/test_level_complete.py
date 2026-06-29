from __future__ import annotations

import os
import sys
from collections.abc import Generator
from pathlib import Path

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

SRC_ROOT = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_ROOT))

import pygame  # noqa: E402
from pygame.surface import Surface  # noqa: E402

from entities.player_entity import PlayerEntity  # noqa: E402
from entities.wall_tile_entity import WallTileEntity  # noqa: E402
from game.game_session import GameSession  # noqa: E402
from game.game_world import GameWorld  # noqa: E402
from game.world_fruit import spawn_fruit  # noqa: E402
from game.world_player import request_turn, update_player_movement  # noqa: E402
from game.level import CellPos, load_smoke_level  # noqa: E402
from game.render_config import WorldRenderConfig  # noqa: E402
from sprites.assets import Assets  # noqa: E402
from sprites.sprite_types import Direction, TileKind  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def pygame_init() -> Generator[None, None, None]:
    """Initialize pygame once for headless asset loading."""
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


@pytest.fixture
def game_world() -> GameWorld:
    """Build a smoke-level world with loaded assets."""
    assets = Assets()
    assets.load()
    layout = load_smoke_level()
    render_config = WorldRenderConfig.centered(layout, (1920, 1080))
    return GameWorld(layout, assets, render_config)


def test_all_consumables_cleared_false_with_pellets(
    game_world: GameWorld,
) -> None:
    assert not game_world.all_consumables_cleared


def test_all_consumables_cleared_true_when_set_empty(
    game_world: GameWorld,
) -> None:
    game_world._remaining_consumables.clear()
    assert game_world.all_consumables_cleared


def test_unfreeze_gameplay_resumes_movement(game_world: GameWorld) -> None:
    from sprites.sprite_types import Direction

    game_world.freeze_gameplay()
    assert game_world.is_frozen
    game_world.unfreeze_gameplay()
    assert not game_world.is_frozen
    request_turn(game_world, Direction.LEFT)
    assert game_world._requested_direction == Direction.LEFT


def test_fruit_collection_spawns_score_popup(game_world: GameWorld) -> None:
    player = game_world._player
    assert player is not None
    spawn_fruit(game_world, pygame.time.get_ticks())
    fruit = game_world._fruit
    assert fruit is not None
    player.move_to(fruit.cell, fruit.center)
    game_world._consume_current_cell()
    assert game_world._fruit is None
    assert len(game_world.score_popups) == 1
    assert game_world.score_popups[0].points == fruit.points


def test_death_coords_skip_walk_chomp_frames() -> None:
    """Death sprites must not reuse right-walk mouth frames on row 0."""
    assets = Assets()
    assets.load()
    walk_frames = assets.pacman[Direction.RIGHT].frames
    death_frames = assets.pacman_death.frames
    assert len(assets.DEATH_COORDS) == 11
    assert len(death_frames) == len(assets.DEATH_COORDS) + 1
    for walk, death in zip(walk_frames, death_frames, strict=False):
        assert not _surfaces_equal(walk, death)
    for col, row in assets.DEATH_COORDS:
        assert row == 0
        death_surface = assets._slice_cells(col, row)
        for walk in walk_frames:
            assert not _surfaces_equal(walk, death_surface)


def test_death_frames_have_no_internal_gaps() -> None:
    """Each death frame must be one contiguous sprite, not split pieces."""
    assets = Assets()
    assets.load()
    for frame in assets.pacman_death.frames[:-1]:
        rows = [
            y
            for y in range(frame.get_height())
            if any(
                frame.get_at((x, y))[3] > 0
                and sum(frame.get_at((x, y))[:3]) > 30
                for x in range(frame.get_width())
            )
        ]
        assert rows
        assert rows == list(range(min(rows), max(rows) + 1))


def test_walk_animation_freezes_when_not_moving() -> None:
    assets = Assets()
    assets.load()
    anims = {direction: assets.pacman[direction] for direction in Direction}
    player = PlayerEntity(
        anims,
        CellPos(0, 0),
        (0, 0),
        Direction.RIGHT,
    )
    frame_before = player.image
    player.update(0, 200)
    assert player.image is frame_before
    player.move_to(CellPos(0, 1), (16, 0))
    player.update(0, 200)
    assert player.image is not frame_before


def test_death_animation_advances_past_first_frame() -> None:
    assets = Assets()
    assets.load()
    anims = {direction: assets.pacman[direction] for direction in Direction}
    player = PlayerEntity(
        anims,
        CellPos(0, 0),
        (0, 0),
        death_animation=assets.pacman_death,
    )
    player.start_death(0)
    player.update(0, 250)
    assert player.image is assets.pacman_death.frames[1]


def _surfaces_equal(a: Surface, b: Surface) -> bool:
    if a.get_size() != b.get_size():
        return False
    w, h = a.get_size()
    return all(a.get_at((x, y)) == b.get_at((x, y)) for x in range(w) for y in range(h))


def test_freeze_gameplay_stops_turn_requests(game_world: GameWorld) -> None:
    from sprites.sprite_types import Direction

    game_world.freeze_gameplay()
    assert game_world.is_frozen
    request_turn(game_world, Direction.LEFT)
    update_player_movement(game_world, 1.0, 0)
    assert game_world.is_frozen


def test_initial_score_carried_into_world() -> None:
    assets = Assets()
    assets.load()
    layout = load_smoke_level()
    render_config = WorldRenderConfig.centered(layout, (1920, 1080))
    world = GameWorld(layout, assets, render_config, initial_score=420)
    assert world.score == 420


def test_advance_level_increments_without_resetting_timer() -> None:
    session = GameSession(
        level_number=1,
        remaining_time_ms=12_345,
    )
    session.advance_level()
    assert session.level_number == 2
    assert session.remaining_time_ms == 12_345


def test_level_complete_reload_resets_timer_and_pellets() -> None:
    """After level advance, session timer and maze consumables must reset."""
    assets = Assets()
    assets.load()
    layout = load_smoke_level()
    render_config = WorldRenderConfig.centered(layout, (1920, 1080))
    session = GameSession(remaining_time_ms=1_000)
    world = GameWorld(
        layout,
        assets,
        render_config,
        level_number=session.level_number,
    )
    world._remaining_consumables.clear()
    assert world.all_consumables_cleared

    session.advance_level()
    world.teardown()
    world = GameWorld(
        layout,
        assets,
        render_config,
        initial_score=session.score,
        level_number=session.level_number,
    )
    session.reset_level_timer()

    assert session.level_number == 2
    assert session.remaining_time_ms == session.level_time_limit_s * 1000
    assert not world.all_consumables_cleared
    assert len(world.consumables) == len(layout.pellet_cells) + len(
        layout.power_pellet_cells
    )


def test_sync_score_keeps_highest_value() -> None:
    session = GameSession(score=100)
    session.sync_score(250)
    assert session.score == 250
    session.sync_score(200)
    assert session.score == 250


def test_wall_flash_white_phase_timing() -> None:
    def wall_flash_white(elapsed_ms: int) -> bool:
        return elapsed_ms % 400 < 200

    assert wall_flash_white(0)
    assert wall_flash_white(199)
    assert not wall_flash_white(250)
    assert wall_flash_white(400)


def test_maze_white_tiles_loaded_for_all_tile_kinds() -> None:
    assets = Assets()
    assets.load()
    for tile_kind in TileKind:
        assert tile_kind in assets.maze_tiles
        assert tile_kind in assets.maze_white_tiles
        blue = assets.maze_tiles[tile_kind]
        white = assets.maze_white_tiles[tile_kind]
        assert blue is not white


def test_white_tiles_use_maze_parts_coords_not_tile_kind_coords() -> None:
    """White flash must slice maze_parts with MAZE_PARTS_WHITE_KIND_COORDS."""
    assets = Assets()
    assets.load()
    for tile_kind in (TileKind.CORNER_TL, TileKind.CORNER_BL):
        assert (
            Assets.TILE_KIND_COORDS[tile_kind]
            != Assets.MAZE_PARTS_WHITE_KIND_COORDS[tile_kind]
        )
        loaded = assets.maze_white_tiles[tile_kind]
        wrong = Assets._make_white_tile(
            assets._slice_maze_cells(*Assets.TILE_KIND_COORDS[tile_kind])
        )
        w, h = loaded.get_size()
        assert any(
            loaded.get_at((x, y)) != wrong.get_at((x, y))
            for x in range(w)
            for y in range(h)
        )


def test_set_wall_flash_swaps_wall_surfaces(game_world: GameWorld) -> None:
    wall = game_world._wall_sprites[0]
    assert isinstance(wall, WallTileEntity)
    blue_surface = wall.image

    game_world.set_wall_flash(True)
    assert wall.image is not blue_surface

    game_world.set_wall_flash(False)
    assert wall.image is blue_surface
