# [wehan] origin/wehan aa1639b — junction-greedy chase, BFS-avoiding flee,
# and per-ghost chase targeting live in entities.ghost.Ghost, wrapped by
# the CellPos/LevelLayout adapters in entities.ghost_map_adapter. This
# module only orchestrates *when* ghosts move and how mode/collisions/
# death play out in pygame — none of which existed in her terminal game.

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from entities.ghost_entity import GhostEntity
from entities.ghost_map_adapter import (
    chase_target,
    next_chase_step,
    next_flee_step,
    next_return_step,
)
from sprites.sprite_types import GhostKind, GhostMode

if TYPE_CHECKING:
    from game.game_world import GameWorld


def ghost_step_ms(world: GameWorld, ghost: GhostEntity) -> int:
    """Return the grid-step interval for a ghost based on its mode.

    Frightened ghosts use a longer interval (smooth half speed). Eyes use a
    shorter interval (smooth double speed). Normal/scatter use the default.
    """
    if ghost.mode is GhostMode.EYES:
        return int(world.PLAYER_STEP_MS // 2)
    if ghost.mode in (GhostMode.FRIGHTENED, GhostMode.FLASHING):
        return int(world.PLAYER_STEP_MS * world.FRIGHTENED_GHOST_SPEED_DIVISOR)
    return int(world.PLAYER_STEP_MS)


def move_one_ghost(
    world: GameWorld, kind: GhostKind, ghost: GhostEntity
) -> None:
    """Advance one ghost by a single grid step.

    Args:
        world: Active game world.
        kind: Ghost personality key.
        ghost: Ghost sprite to move.
    """
    if world._player is None or world._ghosts_frozen:
        return
    if ghost.mode is GhostMode.HIDDEN:
        return
    layout = world._layout
    player_cell = world._player.cell
    home = world._ghost_home.get(kind, ghost.cell)
    if ghost.mode is GhostMode.EYES:
        step = (
            next_return_step(ghost.cell, home, layout)
            if ghost.cell != home
            else None
        )
        if step is not None:
            ghost.last_cell = ghost.cell
            ghost.move_to(step, world._render_config.cell_center(step))
        if ghost.cell == home or step is None:
            center = world._render_config.cell_center(home)
            ghost.respawn_at(home, center)
            if world.frightened:
                ghost.set_frightened(True)
        return
    if world.frightened:
        step = next_flee_step(
            ghost.cell,
            ghost.last_cell,
            player_cell,
            layout,
        )
    else:
        if world._scatter_mode:
            target = home
        else:
            target = chase_target(
                kind,
                player_cell,
                world._travel_direction,
                ghost.cell,
                home,
                layout,
            )
        step = next_chase_step(
            ghost.cell,
            ghost.last_cell,
            target,
            layout,
        )
    if step is None:
        return
    ghost.last_cell = ghost.cell
    ghost.move_to(step, world._render_config.cell_center(step))


def update_ghost_movement(world: GameWorld, dt_s: float, now_ms: int) -> None:
    """Advance ghosts on per-mode step clocks while gameplay is active.

    Args:
        world: Active game world.
        dt_s: Elapsed time in seconds since the last update.
        now_ms: Current timestamp in milliseconds.
    """
    if world.frozen or world._player is None or world._player.dying:
        return
    world._step_now_ms = now_ms
    dt_ms = dt_s * 1000.0
    moved = False
    for kind, ghost in world._ghosts.items():
        if ghost.mode is GhostMode.HIDDEN:
            continue
        ghost._step_elapsed_ms += dt_ms
        step_ms = ghost_step_ms(world, ghost)
        while ghost._step_elapsed_ms >= step_ms:
            ghost._step_elapsed_ms -= step_ms
            ghost.begin_step()
            move_one_ghost(world, kind, ghost)
            moved = True
    if moved:
        resolve_actor_collisions(world)


def activate_frightened_mode(world: GameWorld) -> None:
    """Start frightened mode for all visible ghosts after a power pellet.

    Args:
        world: Active game world.
    """
    now_ms = pygame.time.get_ticks()
    world._frightened_until_ms = now_ms + world.FRIGHTENED_DURATION_MS
    world.frightened = True
    for ghost in world._ghosts.values():
        if ghost.mode is not GhostMode.HIDDEN:
            ghost.set_frightened(True)


def update_frightened_state(world: GameWorld, now_ms: int) -> None:
    """Refresh frightened and end-of-mode flash state for all ghosts.

    Args:
        world: Active game world.
        now_ms: Current timestamp in milliseconds.
    """
    remaining = world._frightened_until_ms - now_ms
    world.frightened = remaining > 0
    flashing = world.frightened and remaining <= world.FRIGHTENED_FLASH_MS
    for ghost in world._ghosts.values():
        if ghost.mode is not GhostMode.HIDDEN:
            ghost.set_frightened(world.frightened, flashing)


def resolve_actor_collisions(world: GameWorld) -> None:
    """Handle player-ghost collisions for eat or death outcomes.

    Args:
        world: Active game world.
    """
    if world._player is None or world._player.dying:
        return
    for ghost in world._ghosts.values():
        if ghost.mode in (GhostMode.HIDDEN, GhostMode.EYES):
            continue
        if ghost.cell != world._player.cell:
            continue
        if ghost.mode in (GhostMode.FRIGHTENED, GhostMode.FLASHING):
            from game.game_world import add_score_popup

            world.score += world.ghost_points
            add_score_popup(world, ghost.center, world.ghost_points)
            ghost.start_returning_home()
            world.pause_gameplay(world.GHOST_EATEN_PAUSE_MS)
        elif not world._invincible:
            start_player_death(world, world._step_now_ms)
            return


def start_player_death(world: GameWorld, now_ms: int) -> None:
    """Freeze gameplay and begin Pac-Man's death animation.

    Args:
        world: Active game world.
        now_ms: Current timestamp in milliseconds.
    """
    if world._player is None:
        return
    world.freeze_gameplay()
    world._player.start_death(now_ms)
