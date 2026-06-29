from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pygame

from entities.pellet_entity import PelletEntity
from game.fruit_schedule import (
    FRUIT_VISIBLE_DURATION_S,
    fruit_for_level,
    spawn_seconds_for_level,
)
from game.world_spawn import cell_center
from sprites.sprite_types import FRUIT_POINTS

if TYPE_CHECKING:
    from game.game_world import GameWorld


@dataclass(slots=True, frozen=True)
class ScorePopup:
    """Short-lived point label shown where a fruit was eaten."""

    center: tuple[int, int]
    points: int
    expires_at_ms: int


def spawn_fruit(world: GameWorld, now_ms: int) -> None:
    kill_fruit(world)
    kind = fruit_for_level(world._level_number)
    fruit_sprite = world._catalog.fruits.get(kind)
    if fruit_sprite is None:
        return
    cell = world._layout.fruit_spawn
    world._fruit = PelletEntity(
        fruit_sprite.surface,
        cell,
        cell_center(world, cell),
        FRUIT_POINTS[kind],
    )
    world.all_sprites.add(world._fruit, layer=world._fruit.layer)
    world._fruit_kill_at_ms = now_ms + FRUIT_VISIBLE_DURATION_S * 1000


def kill_fruit(world: GameWorld) -> None:
    if world._fruit is None:
        return
    world._fruit.kill()
    world._fruit = None
    world._fruit_kill_at_ms = 0


def update_fruit_spawns(
    world: GameWorld,
    level_elapsed_s: int,
    now_ms: int,
) -> None:
    """Spawn bonus fruit at configured level-play seconds."""
    spawn_times = spawn_seconds_for_level(world._level_number)
    while (
        world._fruit_spawn_index < len(spawn_times)
        and level_elapsed_s >= spawn_times[world._fruit_spawn_index]
    ):
        spawn_fruit(world, now_ms)
        world._fruit_spawn_index += 1
    if world._fruit is not None and now_ms >= world._fruit_kill_at_ms:
        kill_fruit(world)


def collect_fruit(world: GameWorld) -> None:
    if world._player is None or world._fruit is None:
        return
    if world._player.cell != world._fruit.cell:
        return
    points = world._fruit.points
    center = world._fruit.center
    world._score += points
    spawn_score_popup(world, center, points)
    kill_fruit(world)


def spawn_score_popup(
    world: GameWorld,
    fruit_center: tuple[int, int],
    points: int,
) -> None:
    """Show classic point value beneath a collected fruit."""
    tile_px = world._render_config.tile_px
    center = (fruit_center[0], fruit_center[1] + tile_px // 2 + 2)
    expires_at_ms = pygame.time.get_ticks() + world.SCORE_POPUP_DURATION_MS
    world._score_popups.append(
        ScorePopup(center=center, points=points, expires_at_ms=expires_at_ms)
    )


def prune_score_popups(world: GameWorld, now_ms: int) -> None:
    if not world._score_popups:
        return
    world._score_popups = [
        popup for popup in world._score_popups if now_ms < popup.expires_at_ms
    ]
