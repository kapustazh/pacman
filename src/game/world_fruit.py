"""Bonus fruit spawn, expiry, and collection on a GameWorld."""

from __future__ import annotations

from typing import TYPE_CHECKING

from entities.pellet_entity import PelletEntity
from game.fruit_schedule import (
    FRUIT_VISIBLE_DURATION_S,
    fruit_spawn_seconds,
    fruit_for_level,
)
from sprites.sprite_types import FRUIT_POINTS

if TYPE_CHECKING:
    from game.game_world import GameWorld


def spawn_fruit(world: GameWorld, now_ms: int) -> None:
    """Place the level's bonus fruit at the fruit spawn cell.

    Args:
        world: Active game world.
        now_ms: Current timestamp in milliseconds.
    """
    kill_fruit(world)
    kind = fruit_for_level(world._level_number)
    surface = world._catalog.fruits.get(kind)
    if surface is None:
        return
    cell = world._layout.fruit_spawn
    world._fruit = PelletEntity(
        surface,
        cell,
        world._render_config.cell_center(cell),
        FRUIT_POINTS[kind],
    )
    world.all_sprites.add(world._fruit, layer=world._fruit.layer)
    world._fruit_kill_at_ms = now_ms + FRUIT_VISIBLE_DURATION_S * 1000
    # Fruit spawns on the player's spawn cell; if Pac-Man is standing there
    # collection must happen now, not on his next move.
    collect_fruit(world)


def kill_fruit(world: GameWorld) -> None:
    """Remove the active bonus fruit sprite, if any.

    Args:
        world: Active game world.
    """
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
    """Spawn or expire bonus fruit based on the level schedule.

    Args:
        world: Active game world.
        level_elapsed_s: Seconds elapsed since level play began.
        now_ms: Current timestamp in milliseconds.
    """
    spawn_times = fruit_spawn_seconds(world._level_max_time_s)
    while (
        world._fruit_spawn_index < len(spawn_times)
        and level_elapsed_s >= spawn_times[world._fruit_spawn_index]
    ):
        spawn_fruit(world, now_ms)
        world._fruit_spawn_index += 1
    if world._fruit is not None and now_ms >= world._fruit_kill_at_ms:
        kill_fruit(world)


def collect_fruit(world: GameWorld) -> None:
    """Award points when Pac-Man occupies the same cell as the fruit.

    Args:
        world: Active game world.
    """
    if world._player is None or world._fruit is None:
        return
    if world._player.cell != world._fruit.cell:
        return
    from game.game_world import add_score_popup

    world.score += world._fruit.points
    add_score_popup(world, world._fruit.center, world._fruit.points)
    kill_fruit(world)
