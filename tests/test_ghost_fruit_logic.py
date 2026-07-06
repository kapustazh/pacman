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

from config.config import DEFAULT_CONFIG
from game.fruit_schedule import fruit_for_level, spawn_seconds_for_level
from game.game_world import GameWorld, spawn_fruit, update_fruit_spawns
from game.ghost_logic import (
    activate_frightened_mode,
    move_ghosts,
    resolve_actor_collisions,
    update_frightened_state,
)
from game.level import load_level
from game.render_config import WorldRenderConfig
from sprites.assets import Assets
from sprites.sprite_types import FruitKind, GhostKind


@pytest.fixture(scope="module", autouse=True)
def pygame_init() -> Generator[None, None, None]:
    """Initialize pygame once for headless asset loading."""
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


def test_fruit_schedule_level_one() -> None:
    assert fruit_for_level(1) == FruitKind.CHERRY
    assert spawn_seconds_for_level(1) == (9, 41)


def test_fruit_schedule_high_levels_use_key() -> None:
    assert fruit_for_level(12) == FruitKind.KEY
    assert spawn_seconds_for_level(12) == (9, 41)


def test_level_ghost_spawns_are_walkable() -> None:
    layout = load_level(DEFAULT_CONFIG, 0, 42)
    assert len(layout.ghost_spawns) == 4
    kinds = {kind for kind, _cell in layout.ghost_spawns}
    assert kinds == set(GhostKind)
    for _kind, cell in layout.ghost_spawns:
        assert not layout.is_wall(cell)


def _build_world() -> GameWorld:
    assets = Assets()
    assets.load()
    layout = load_level(DEFAULT_CONFIG, 0, 42)
    render_config = WorldRenderConfig.centered(layout, (1920, 1080))
    return GameWorld(layout, assets, render_config)


def test_reset_fruit_spawns_clears_index_and_active_fruit() -> None:
    world = _build_world()
    spawn_fruit(world, 0)
    world._fruit_spawn_index = 1

    world.reset_fruit_spawns()

    assert world._fruit_spawn_index == 0
    assert world._fruit is None


def test_reset_fruit_spawns_allows_early_spawn_after_life_lost() -> None:
    world = _build_world()
    world._fruit_spawn_index = 1

    world.reset_fruit_spawns()
    update_fruit_spawns(world, level_elapsed_s=9, now_ms=9_000)

    assert world._fruit is not None
    assert world._fruit_spawn_index == 1


def test_frightened_ghosts_flash_only_near_the_end() -> None:
    world = _build_world()
    activate_frightened_mode(world)
    ghost = next(iter(world._ghosts.values()))

    update_frightened_state(world, now_ms=0)
    assert ghost._frightened is True
    assert ghost._flashing is False

    flash_starts_at = world._frightened_until_ms - world.FRIGHTENED_FLASH_MS
    update_frightened_state(world, now_ms=flash_starts_at)
    assert ghost._frightened is True
    assert ghost._flashing is True

    update_frightened_state(world, now_ms=world._frightened_until_ms)
    assert ghost._frightened is False
    assert ghost._flashing is False


def test_scatter_mode_toggles_after_chase_and_scatter_steps() -> None:
    world = _build_world()
    assert world._scatter_mode is False

    for _ in range(world.CHASE_STEPS):
        move_ghosts(world)
    assert world._scatter_mode is True

    for _ in range(world.SCATTER_STEPS):
        move_ghosts(world)
    assert world._scatter_mode is False


def test_cheat_invincible_blocks_death() -> None:
    world = _build_world()
    assert world._player is not None
    world.toggle_invincible()
    ghost = next(iter(world._ghosts.values()))
    ghost.cell = world._player.cell

    resolve_actor_collisions(world)

    assert world.player_is_dying is False


def test_cheat_freeze_stops_ghost_movement() -> None:
    world = _build_world()
    world.toggle_ghosts_frozen()
    ghost = next(iter(world._ghosts.values()))
    before = ghost.cell

    move_ghosts(world)

    assert ghost.cell == before


def test_frightened_flash_alternates_blue_and_white() -> None:
    world = _build_world()
    activate_frightened_mode(world)
    ghost = next(iter(world._ghosts.values()))
    flash_starts_at = world._frightened_until_ms - world.FRIGHTENED_FLASH_MS
    update_frightened_state(world, now_ms=flash_starts_at)
    assert ghost._flashing is True

    interval = ghost.FLASH_INTERVAL_MS
    ghost.update(0, flash_starts_at)
    first_flash_frame = ghost.image
    ghost.update(0, flash_starts_at + interval)
    second_flash_frame = ghost.image

    assert first_flash_frame is not second_flash_frame


def test_eaten_ghost_becomes_eyes_and_returns_home() -> None:
    world = _build_world()
    assert world._player is not None
    activate_frightened_mode(world)
    kind, ghost = next(iter(world._ghosts.items()))
    ghost.cell = world._player.cell

    resolve_actor_collisions(world)

    assert ghost.is_returning is True
    assert ghost._frightened is False

    home = world._ghost_home[kind]
    for _ in range(200):
        if not ghost.is_returning:
            break
        move_ghosts(world)
    assert ghost.is_returning is False
    assert ghost.cell == home


def test_frightened_ghosts_move_slower_than_normal() -> None:
    """Frightened ghosts must only step every FRIGHTENED_GHOST_SPEED_DIVISOR
    move_ghosts() calls, so Pac-Man can outrun and catch them."""
    world = _build_world()
    activate_frightened_mode(world)
    ghost = next(iter(world._ghosts.values()))
    divisor = world.FRIGHTENED_GHOST_SPEED_DIVISOR

    moved_steps = 0
    start = ghost.cell
    previous = start
    for _ in range(divisor * 4):
        move_ghosts(world)
        if ghost.cell != previous:
            moved_steps += 1
            previous = ghost.cell

    # Non-frightened ghosts would move on every one of these calls; a
    # frightened ghost must move on at most half (1/divisor) of them.
    assert moved_steps <= (divisor * 4) // divisor
