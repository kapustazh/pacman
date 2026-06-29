from __future__ import annotations

from typing import TYPE_CHECKING

from game.level import CellPos
from game.world_ghosts import resolve_actor_collisions
from game.world_spawn import cell_center, direction_delta
from sprites.sprite_types import Direction

if TYPE_CHECKING:
    from game.game_world import GameWorld


def request_turn(world: GameWorld, direction: Direction) -> None:
    """Buffer a direction change from player input."""
    if world._frozen or world.player_is_dying:
        return
    world._requested_direction = direction


def move_player(world: GameWorld, direction: Direction) -> bool:
    """Move player one grid step if target cell is walkable."""
    if world._player is None or world._player.is_dying:
        return False

    row_delta, col_delta = direction_delta(direction)
    target = CellPos(
        world._player.cell.row + row_delta,
        world._player.cell.col + col_delta,
    )
    world._player.face(direction)
    if world._layout.is_wall(target):
        return False

    world._player.move_to(target, cell_center(world, target))
    world._consume_current_cell()
    resolve_actor_collisions(world)
    return True


def auto_step(world: GameWorld) -> None:
    """Try buffered turn first, else keep walking current direction."""
    if world._requested_direction is not None:
        if move_player(world, world._requested_direction):
            world._travel_direction = world._requested_direction
            return
    move_player(world, world._travel_direction)


def update_player_movement(world: GameWorld, dt_s: float, now_ms: int) -> None:
    """Advance player on grid at fixed speed while PLAYING."""
    if world._frozen or world._player is None or world._player.is_dying:
        return
    world._step_now_ms = now_ms
    world._step_accumulator_ms += dt_s * 1000.0
    while world._step_accumulator_ms >= world.PLAYER_STEP_MS:
        world._step_accumulator_ms -= world.PLAYER_STEP_MS
        auto_step(world)
