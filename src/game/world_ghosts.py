from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from entities.ghost_entity import GhostEntity
from game.world_spawn import cell_center

if TYPE_CHECKING:
    from game.game_world import GameWorld


def activate_frightened_mode(world: GameWorld) -> None:
    now_ms = pygame.time.get_ticks()
    world._frightened_until_ms = now_ms + world.FRIGHTENED_DURATION_MS
    for ghost in world._ghosts.values():
        if not ghost.is_hidden:
            ghost.set_frightened(True)


def is_frightened(world: GameWorld) -> bool:
    return bool(pygame.time.get_ticks() < world._frightened_until_ms)


def update_frightened_state(world: GameWorld, now_ms: int) -> None:
    frightened = now_ms < world._frightened_until_ms
    for ghost in world._ghosts.values():
        if not ghost.is_hidden:
            ghost.set_frightened(frightened)


def eat_ghost(world: GameWorld, ghost: GhostEntity) -> None:
    world._score += world.GHOST_POINTS
    ghost.hide_eaten()
    world._ghost_respawn_at_ms[ghost.kind] = (
        pygame.time.get_ticks() + world.GHOST_EATEN_RESPAWN_MS
    )


def update_ghost_respawns(world: GameWorld, now_ms: int) -> None:
    for kind, respawn_at_ms in list(world._ghost_respawn_at_ms.items()):
        if now_ms < respawn_at_ms:
            continue
        del world._ghost_respawn_at_ms[kind]
        home = world._ghost_home[kind]
        ghost = world._ghosts.get(kind)
        if ghost is None:
            continue
        ghost.respawn_at(home, cell_center(world, home))
        world.all_sprites.add(ghost, layer=ghost.layer)
        if is_frightened(world):
            ghost.set_frightened(True)


def resolve_actor_collisions(world: GameWorld) -> None:
    if world._player is None or world._player.is_dying:
        return
    for ghost in world._ghosts.values():
        if ghost.is_hidden or ghost.cell != world._player.cell:
            continue
        if is_frightened(world):
            eat_ghost(world, ghost)
        else:
            start_player_death(world, world._step_now_ms)
            return


def start_player_death(world: GameWorld, now_ms: int) -> None:
    if world._player is None:
        return
    world.freeze_gameplay()
    world._player.start_death(now_ms)
