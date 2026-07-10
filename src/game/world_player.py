"""Pac-Man grid movement: buffered turns and the fixed-step auto-walk."""

from __future__ import annotations

from typing import TYPE_CHECKING

from game.ghost_logic import resolve_actor_collisions
from game.level import CellPos
from game.render_config import DIRECTION_DELTA
from sprites.sprite_types import Direction

if TYPE_CHECKING:
    from game.game_world import GameWorld


def request_turn(world: GameWorld, direction: Direction) -> None:
    """Buffer a direction change from player input.

    Args:
        world: Active game world receiving the input.
        direction: Requested travel direction.
    """
    if world.frozen or world.player_is_dying:
        return
    world._requested_direction = direction


def _move_player(world: GameWorld, direction: Direction) -> bool:
    """Move Pac-Man one grid step if the target cell is walkable.

    Args:
        world: Active game world.
        direction: Direction to attempt.

    Returns:
        True when the move succeeded.
    """
    if world._player is None or world._player.dying:
        return False

    row_delta, col_delta = DIRECTION_DELTA[direction]
    target = CellPos(
        world._player.cell.row + row_delta,
        world._player.cell.col + col_delta,
    )
    world._player.face(direction)
    if world._layout.is_wall(target):
        return False

    world._player.move_to(
        target,
        world._render_config.cell_center(target),
    )
    world._consume_current_cell()
    return True


def _auto_step(world: GameWorld) -> None:
    """Try a buffered turn, otherwise continue in the travel direction.

    Args:
        world: Active game world.
    """
    if world._requested_direction is not None:
        if _move_player(world, world._requested_direction):
            world._travel_direction = world._requested_direction
            return
    _move_player(world, world._travel_direction)


def _begin_player_visual_step(world: GameWorld) -> None:
    """Start visual interpolation for Pac-Man's next grid step.

    Args:
        world: Active game world.
    """
    if world._player is not None:
        world._player.begin_step()


def update_player_movement(world: GameWorld, dt_s: float, now_ms: int) -> None:
    """Advance Pac-Man on the grid while gameplay is active.

    Args:
        world: Active game world.
        dt_s: Elapsed time in seconds since the last update.
        now_ms: Current timestamp in milliseconds.
    """
    if world.frozen or world._player is None or world._player.dying:
        return
    world._step_now_ms = now_ms
    world._ghost_step_elapsed_ms += dt_s * 1000.0
    while world._ghost_step_elapsed_ms >= world.player_step_ms:
        world._ghost_step_elapsed_ms -= world.player_step_ms
        _begin_player_visual_step(world)
        _auto_step(world)
        resolve_actor_collisions(world)
