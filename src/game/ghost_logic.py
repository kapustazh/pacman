# [transition] SCRUM-35 — ghost AI from wehan ghost.py: junction-greedy chase,
# BFS only for frightened flee.

from __future__ import annotations

import random
from collections import deque
from typing import TYPE_CHECKING

import pygame

from entities.ghost_entity import GhostEntity
from game.level import CellPos, LevelLayout
from game.render_config import cell_center, direction_delta
from sprites.sprite_types import Direction, GhostKind

if TYPE_CHECKING:
    from game.game_world import GameWorld


# Original Pac-Man direction priority used for tie-breaking.
# Priority: Up -> Left -> Down -> Right.
DIRECTION_ORDER = [
    (-1, 0),  # up
    (0, -1),  # left
    (1, 0),  # down
    (0, 1),  # right
]

_NEIGHBORS: tuple[tuple[int, int], ...] = (
    (0, 1),
    (0, -1),
    (-1, 0),
    (1, 0),
)


def _path_bfs(
    start: CellPos,
    target: CellPos,
    layout: LevelLayout,
) -> list[CellPos]:
    """Shortest path from start to target on the level grid (BFS)."""
    queue: deque[CellPos] = deque([start])
    came_from: dict[CellPos, CellPos | None] = {start: None}

    while queue:
        current = queue.popleft()
        if current == target:
            break
        for row_delta, col_delta in _NEIGHBORS:
            nxt = CellPos(current.row + row_delta, current.col + col_delta)
            if nxt in came_from or layout.is_wall(nxt):
                continue
            queue.append(nxt)
            came_from[nxt] = current

    if target not in came_from:
        return []

    path: list[CellPos] = []
    node: CellPos | None = target
    while node is not None:
        path.append(node)
        node = came_from[node]
    path.reverse()
    return path


def _random_step(
    cell: CellPos,
    last: CellPos,
    layout: LevelLayout,
    allow_back: bool = False,
) -> CellPos | None:
    """Random walkable neighbour; honour no-reverse unless allow_back."""
    options: list[CellPos] = []
    for row_delta, col_delta in _NEIGHBORS:
        nxt = CellPos(cell.row + row_delta, cell.col + col_delta)
        if layout.is_wall(nxt):
            continue
        if not allow_back and nxt == last:
            continue
        options.append(nxt)
    if not options:
        if allow_back:
            return None
        return _random_step(cell, last, layout, allow_back=True)
    return random.choice(options)


def _current_direction(cell: CellPos, last_cell: CellPos) -> tuple[int, int] | None:
    """Return the current movement direction based on previous position."""
    row_delta = cell.row - last_cell.row
    col_delta = cell.col - last_cell.col
    if (row_delta, col_delta) in DIRECTION_ORDER:
        return (row_delta, col_delta)
    return None


def _valid_directions(
    cell: CellPos,
    last_cell: CellPos,
    layout: LevelLayout,
    allow_reverse: bool = False,
) -> list[tuple[int, int]]:
    """Return valid directions in a fixed priority order."""
    current_direction = _current_direction(cell, last_cell)
    reverse_direction = None
    if current_direction is not None:
        reverse_direction = (-current_direction[0], -current_direction[1])

    valid_directions: list[tuple[int, int]] = []
    for row_delta, col_delta in DIRECTION_ORDER:
        if not allow_reverse and (row_delta, col_delta) == reverse_direction:
            continue
        nxt = CellPos(cell.row + row_delta, cell.col + col_delta)
        if not layout.is_wall(nxt):
            valid_directions.append((row_delta, col_delta))
    return valid_directions


def _is_junction(cell: CellPos, last_cell: CellPos, layout: LevelLayout) -> bool:
    """Return True if the ghost has multiple forward choices."""
    return len(_valid_directions(cell, last_cell, layout)) >= 2


def _choose_pacman_step(
    cell: CellPos,
    last_cell: CellPos,
    target: CellPos,
    layout: LevelLayout,
) -> CellPos | None:
    """
    Choose the next grid cell using the original Pac-Man
    junction-based movement algorithm.
    """
    current_direction = _current_direction(cell, last_cell)

    if current_direction is not None and not _is_junction(cell, last_cell, layout):
        nxt = CellPos(
            cell.row + current_direction[0],
            cell.col + current_direction[1],
        )
        if not layout.is_wall(nxt):
            return nxt

    directions = _valid_directions(cell, last_cell, layout)
    if not directions:
        directions = _valid_directions(cell, last_cell, layout, allow_reverse=True)
    if not directions:
        return None

    best_direction: tuple[int, int] = directions[0]
    best_distance = float("inf")

    for row_delta, col_delta in directions:
        new_row = cell.row + row_delta
        new_col = cell.col + col_delta
        row_distance = new_row - target.row
        col_distance = new_col - target.col
        distance = row_distance * row_distance + col_distance * col_distance
        if distance < best_distance:
            best_distance = distance
            best_direction = (row_delta, col_delta)

    return CellPos(cell.row + best_direction[0], cell.col + best_direction[1])


def _next_chase_step(
    cell: CellPos,
    last: CellPos,
    target: CellPos,
    layout: LevelLayout,
) -> CellPos | None:
    """One junction-greedy step toward target; fall back to random no-reverse."""
    step = _choose_pacman_step(cell, last, target, layout)
    if step is not None:
        return step
    return _random_step(cell, last, layout)


def _next_flee_step(
    cell: CellPos,
    last: CellPos,
    player: CellPos,
    layout: LevelLayout,
) -> CellPos | None:
    """Step away from player, avoiding the BFS path back toward them."""
    avoid: CellPos | None = None
    flee_path = _path_bfs(player, cell, layout)
    if len(flee_path) >= 2:
        avoid = flee_path[-2]

    options: list[CellPos] = []
    for row_delta, col_delta in _NEIGHBORS:
        nxt = CellPos(cell.row + row_delta, cell.col + col_delta)
        if layout.is_wall(nxt) or nxt == last:
            continue
        if avoid is not None and nxt == avoid:
            continue
        options.append(nxt)

    if not options:
        return _random_step(cell, last, layout, allow_back=True)
    return random.choice(options)


def _chase_target(
    kind: GhostKind,
    player_cell: CellPos,
    travel_direction: Direction,
    ghost_cell: CellPos,
    home: CellPos,
    layout: LevelLayout,
) -> CellPos:
    """Classic per-ghost chase target (Blinky/Pinky/Inky/Clyde)."""
    row_delta, col_delta = direction_delta(travel_direction)
    if kind == GhostKind.BLINKY:
        target = player_cell
    elif kind == GhostKind.PINKY:
        target = CellPos(
            player_cell.row + row_delta * 4,
            player_cell.col + col_delta * 4,
        )
    elif kind == GhostKind.INKY:
        target = CellPos(
            player_cell.row + row_delta * 2 + random.randint(-1, 1),
            player_cell.col + col_delta * 2 + random.randint(-1, 1),
        )
    elif kind == GhostKind.CLYDE:
        distance = abs(ghost_cell.row - player_cell.row) + abs(
            ghost_cell.col - player_cell.col
        )
        target = player_cell if distance > 8 else home
    else:
        target = player_cell

    if layout.is_wall(target):
        return player_cell
    return target


def move_ghosts(world: GameWorld) -> None:
    """Step every visible ghost once per player grid step."""
    if world._player is None:
        return
    layout = world._layout
    player_cell = world._player.cell
    fleeing = is_frightened(world)
    for kind, ghost in world._ghosts.items():
        if ghost.is_hidden:
            continue
        home = world._ghost_home.get(kind, ghost.cell)
        if fleeing:
            step = _next_flee_step(
                ghost.cell,
                ghost.last_cell,
                player_cell,
                layout,
            )
        else:
            target = _chase_target(
                kind,
                player_cell,
                world._travel_direction,
                ghost.cell,
                home,
                layout,
            )
            step = _next_chase_step(
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
    now_ms = pygame.time.get_ticks()
    world._frightened_until_ms = now_ms + world.FRIGHTENED_DURATION_MS
    for ghost in world._ghosts.values():
        if not ghost.is_hidden:
            ghost.set_frightened(True)


def is_frightened(world: GameWorld) -> bool:
    return bool(pygame.time.get_ticks() < world._frightened_until_ms)


def update_frightened_state(world: GameWorld, now_ms: int) -> None:
    remaining = world._frightened_until_ms - now_ms
    frightened = remaining > 0
    flashing = frightened and remaining <= world.FRIGHTENED_FLASH_MS
    for ghost in world._ghosts.values():
        if not ghost.is_hidden:
            ghost.set_frightened(frightened, flashing)


def eat_ghost(world: GameWorld, ghost: GhostEntity) -> None:
    world._score += world.ghost_points
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
        ghost.respawn_at(home, cell_center(world._render_config, home))
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
