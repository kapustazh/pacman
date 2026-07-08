# [wehan] origin/wehan aa1639b — junction-greedy chase, BFS-avoiding flee,
# and per-ghost chase targeting live in entities.ghost.Ghost, wrapped by
# the CellPos/LevelLayout adapters in entities.ghost_map_adapter. This
# module only orchestrates *when* ghosts move and how mode/collisions/
# death play out in pygame — none of which existed in her terminal game.

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from entities.ghost_map_adapter import (
    chase_target,
    next_chase_step,
    next_flee_step,
    next_return_step,
)
from game.render_config import cell_center

if TYPE_CHECKING:
    from game.game_world import GameWorld


def move_ghosts(world: GameWorld) -> None:
    """Advance every visible ghost one grid step.

    Frightened ghosts move at a reduced rate so Pac-Man can catch them;
    eaten ghosts returning home are not slowed.

    Args:
        world: Active game world.
    """
    if world._player is None or world._ghosts_frozen:
        return
    layout = world._layout
    player_cell = world._player.cell
    fleeing = world.frightened
    world._ghost_step_count += 1
    frightened_step_due = (
        world._ghost_step_count % world.FRIGHTENED_GHOST_SPEED_DIVISOR == 0
    )
    for kind, ghost in world._ghosts.items():
        if ghost.hidden:
            continue
        home = world._ghost_home.get(kind, ghost.cell)
        if ghost.returning:
            for _ in range(2):  # eyes fly home at double speed
                if ghost.cell == home:
                    break
                step = next_return_step(ghost.cell, home, layout)
                if step is None:
                    break
                ghost.last_cell = ghost.cell
                ghost.move_to(step, cell_center(world._render_config, step))
            if ghost.cell == home:
                ghost.arrive_home()
                if world.frightened:
                    ghost.set_frightened(True)
            continue
        if fleeing:
            if not frightened_step_due:
                continue
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
            continue
        ghost.last_cell = ghost.cell
        ghost.move_to(step, cell_center(world._render_config, step))


def activate_frightened_mode(world: GameWorld) -> None:
    """Start frightened mode for all visible ghosts after a power pellet.

    Args:
        world: Active game world.
    """
    now_ms = pygame.time.get_ticks()
    world._frightened_until_ms = now_ms + world.FRIGHTENED_DURATION_MS
    world.frightened = True
    for ghost in world._ghosts.values():
        if not ghost.hidden:
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
        if not ghost.hidden:
            ghost.set_frightened(world.frightened, flashing)


def resolve_actor_collisions(world: GameWorld) -> None:
    """Handle player-ghost collisions for eat or death outcomes.

    Args:
        world: Active game world.
    """
    if world._player is None or world._player.dying:
        return
    for ghost in world._ghosts.values():
        if ghost.hidden or ghost.returning:
            continue
        if ghost.cell != world._player.cell:
            continue
        if world.frightened:
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
