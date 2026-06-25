from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

SRC_ROOT = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_ROOT))

import pygame  # noqa: E402

from entities.wall_tile_entity import WallTileEntity  # noqa: E402
from game.entity_factory import EntityFactory  # noqa: E402
from game.game_session import GameSession  # noqa: E402
from game.game_world import GameWorld  # noqa: E402
from game.level import load_smoke_level  # noqa: E402
from game.render_config import WorldRenderConfig  # noqa: E402
from rendering.level_clear_effect import LevelClearEffect  # noqa: E402
from sprites.assets import Assets  # noqa: E402
from sprites.sprite_types import TileKind  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def pygame_init() -> None:
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
    factory = EntityFactory(assets, render_config, layout)
    return GameWorld(layout, factory)


def test_all_consumables_cleared_false_with_pellets(
    game_world: GameWorld,
) -> None:
    assert not game_world.all_consumables_cleared


def test_all_consumables_cleared_true_when_set_empty(
    game_world: GameWorld,
) -> None:
    game_world._remaining_consumables.clear()
    assert game_world.all_consumables_cleared


def test_freeze_gameplay_stops_turn_requests(game_world: GameWorld) -> None:
    from sprites.sprite_types import Direction

    game_world.freeze_gameplay()
    assert game_world.is_frozen
    game_world.request_turn(Direction.LEFT)
    game_world.update_player_movement(1.0)
    assert game_world.is_frozen


def test_initial_score_carried_into_world() -> None:
    assets = Assets()
    assets.load()
    layout = load_smoke_level()
    render_config = WorldRenderConfig.centered(layout, (1920, 1080))
    factory = EntityFactory(assets, render_config, layout)
    world = GameWorld(layout, factory, initial_score=420)
    assert world.score == 420


def test_advance_level_increments_without_resetting_timer() -> None:
    session = GameSession(
        level_number=1,
        remaining_time_ms=12_345,
    )
    session.advance_level()
    assert session.level_number == 2
    assert session.remaining_time_ms == 12_345


def test_sync_score_keeps_highest_value() -> None:
    session = GameSession(score=100)
    session.sync_score(250)
    assert session.score == 250
    session.sync_score(200)
    assert session.score == 250


def test_level_clear_effect_white_phase_timing() -> None:
    effect = LevelClearEffect()
    assert effect.is_white_phase(0)
    assert effect.is_white_phase(199)
    assert not effect.is_white_phase(250)
    assert effect.is_white_phase(400)


def test_maze_white_tiles_loaded_for_all_tile_kinds() -> None:
    assets = Assets()
    assets.load()
    for tile_kind in TileKind:
        assert tile_kind in assets.maze.tiles
        assert tile_kind in assets.maze.white_tiles
        blue = assets.maze.tiles[tile_kind].surface
        white = assets.maze.white_tiles[tile_kind].surface
        assert blue is not white


def test_set_wall_flash_swaps_wall_surfaces(game_world: GameWorld) -> None:
    wall_sprite = game_world._wall_sprites[0]
    wall = wall_sprite.entity
    assert isinstance(wall, WallTileEntity)
    blue_surface = wall.image

    game_world.set_wall_flash(True)
    assert wall.image is not blue_surface

    game_world.set_wall_flash(False)
    assert wall.image is blue_surface
