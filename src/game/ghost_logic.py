# [transition] SCRUM-35 — ghost AI from wehan ghost.py: junction-greedy chase,
# BFS only for frightened flee.

from __future__ import annotations

import random
from collections import deque
from typing import TYPE_CHECKING

import pygame

from game.level import CellPos, LevelLayout
from game.render_config import DIRECTION_DELTA, cell_center
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
    """Find the shortest walkable path between two grid cells.

    Args:
        start: Starting cell.
        target: Destination cell.
        layout: Level grid used for wall checks.

    Returns:
        Ordered path from start to target, or empty when unreachable.
    """
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
    """Pick a random walkable neighbor, avoiding reverse unless allowed.

    Args:
        cell: Current ghost cell.
        last: Previous cell used to block immediate reversal.
        layout: Level grid used for wall checks.
        allow_back: When True, permit moving back onto the previous cell.

    Returns:
        Chosen neighbor cell, or None when no move exists.
    """
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


def _current_direction(
    cell: CellPos, last_cell: CellPos
) -> tuple[int, int] | None:
    """Derive the current movement direction from the last step.

    Args:
        cell: Current cell.
        last_cell: Previous cell.

    Returns:
        (row_delta, col_delta) when valid, otherwise None.
    """
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
    """List walkable directions in classic Pac-Man priority order.

    Args:
        cell: Current cell.
        last_cell: Previous cell used to block reversal.
        layout: Level grid used for wall checks.
        allow_reverse: When True, include the reverse direction.

    Returns:
        Valid (row_delta, col_delta) pairs in priority order.
    """
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


def _is_junction(
    cell: CellPos, last_cell: CellPos, layout: LevelLayout
) -> bool:
    """Return whether a ghost has more than one forward choice.

    Args:
        cell: Current cell.
        last_cell: Previous cell used for direction checks.
        layout: Level grid used for wall checks.

    Returns:
        True when multiple non-reverse directions are available.
    """
    return len(_valid_directions(cell, last_cell, layout)) >= 2


def _choose_pacman_step(
    cell: CellPos,
    last_cell: CellPos,
    target: CellPos,
    layout: LevelLayout,
) -> CellPos | None:
    """Choose the next cell using classic junction-greedy ghost movement.

    Args:
        cell: Current ghost cell.
        last_cell: Previous cell.
        target: Chase target cell.
        layout: Level grid used for wall checks.

    Returns:
        Next cell to enter, or None when blocked.
    """
    current_direction = _current_direction(cell, last_cell)

    if current_direction is not None and not _is_junction(
        cell, last_cell, layout
    ):
        nxt = CellPos(
            cell.row + current_direction[0],
            cell.col + current_direction[1],
        )
        if not layout.is_wall(nxt):
            return nxt

    directions = _valid_directions(cell, last_cell, layout)
    if not directions:
        directions = _valid_directions(
            cell, last_cell, layout, allow_reverse=True
        )
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
    """Take one chase step toward a target, falling back to random movement.

    Args:
        cell: Current ghost cell.
        last: Previous cell.
        target: Chase target cell.
        layout: Level grid used for wall checks.

    Returns:
        Next cell to enter, or None when no move exists.
    """
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
    """Step away from the player while avoiding the direct return path.

    Args:
        cell: Current ghost cell.
        last: Previous cell.
        player: Player cell used to compute flee direction.
        layout: Level grid used for wall checks.

    Returns:
        Next cell to enter, or None when no move exists.
    """
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
    """Compute the classic per-ghost chase target cell.

    Args:
        kind: Ghost personality determining targeting behavior.
        player_cell: Current player position.
        travel_direction: Player's current travel direction.
        ghost_cell: Current ghost position.
        home: Ghost's home corner cell.
        layout: Level grid used to clamp invalid targets.

    Returns:
        Target cell for chase or scatter pathing.
    """
    row_delta, col_delta = DIRECTION_DELTA[travel_direction]
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


def _next_return_step(
    cell: CellPos,
    home: CellPos,
    layout: LevelLayout,
) -> CellPos | None:
    """Take one step along the shortest path back to a ghost home cell.

    Args:
        cell: Current ghost cell.
        home: Home corner destination.
        layout: Level grid used for pathfinding.

    Returns:
        Next cell on the return path, or None when already home or blocked.
    """
    path = _path_bfs(cell, home, layout)
    if len(path) >= 2:
        return path[1]
    return None


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
                step = _next_return_step(ghost.cell, home, layout)
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
            step = _next_flee_step(
                ghost.cell,
                ghost.last_cell,
                player_cell,
                layout,
            )
        else:
            if world._scatter_mode:
                target = home
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
