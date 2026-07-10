"""Bridge pygame's grid types to the ghost AI's row/col API."""

from __future__ import annotations

from dataclasses import dataclass

from game.level import CellPos, LevelLayout
from game.render_config import DIRECTION_DELTA
from sprites.sprite_types import Direction, GhostKind

_GHOST_NAMES: dict[GhostKind, str] = {
    GhostKind.BLINKY: "Blinky",
    GhostKind.PINKY: "Pinky",
    GhostKind.INKY: "Inky",
    GhostKind.CLYDE: "Clyde",
}


class MapData:
    """Expose a level layout's wall check as a row/col lookup."""

    def __init__(self, layout: LevelLayout) -> None:
        """Wrap an immutable level layout for wall lookups."""
        self._layout = layout

    def is_wall(self, row: int, col: int) -> bool:
        """Return whether a grid cell is out of bounds or a wall tile."""
        return bool(self._layout.is_wall(CellPos(row, col)))


@dataclass
class Player:
    """Player position/direction snapshot used for ghost chase targeting."""

    row: int
    col: int
    last_row_delta: int
    last_col_delta: int


def _ghost_step(
    approach: bool,
    cell: CellPos,
    last: CellPos,
    target: CellPos,
    layout: LevelLayout,
) -> CellPos | None:
    """Take one step via Ghost.move_towards/move_away.

    Args:
        approach: True to chase toward target, False to flee from it.
        cell: Current ghost cell.
        last: Previous cell.
        target: Chase target, or player cell to flee from.
        layout: Level grid used for wall checks.

    Returns:
        Next cell to enter, or None when no move exists.
    """
    from entities.ghost import Ghost

    ghost = Ghost("ghost", cell.row, cell.col)
    ghost.last_row, ghost.last_col = last.row, last.col
    move = ghost.move_towards if approach else ghost.move_away
    move(target.row, target.col, MapData(layout))
    if (ghost.row, ghost.col) == (cell.row, cell.col):
        return None
    return CellPos(ghost.row, ghost.col)


def next_chase_step(
    cell: CellPos,
    last: CellPos,
    target: CellPos,
    layout: LevelLayout,
) -> CellPos | None:
    """Take one chase step toward a target using Ghost.move_towards."""
    return _ghost_step(True, cell, last, target, layout)


def next_flee_step(
    cell: CellPos,
    last: CellPos,
    player: CellPos,
    layout: LevelLayout,
) -> CellPos | None:
    """Step away from the player using Ghost.move_away."""
    return _ghost_step(False, cell, last, player, layout)


def chase_target(
    kind: GhostKind,
    player_cell: CellPos,
    travel_direction: Direction,
    ghost_cell: CellPos,
    home: CellPos,
    layout: LevelLayout,
) -> CellPos:
    """Compute the classic per-ghost chase target using Ghost.get_chase_target.

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
    from entities.ghost import Ghost

    ghost = Ghost(_GHOST_NAMES[kind], ghost_cell.row, ghost_cell.col)
    ghost.spawn_row, ghost.spawn_col = home.row, home.col
    row_delta, col_delta = DIRECTION_DELTA[travel_direction]
    player = Player(player_cell.row, player_cell.col, row_delta, col_delta)
    target_row, target_col = ghost.get_chase_target(player, MapData(layout))
    return CellPos(target_row, target_col)


def next_return_step(
    cell: CellPos,
    home: CellPos,
    layout: LevelLayout,
) -> CellPos | None:
    """Take one step along the shortest path back to a ghost home cell.

    Uses Ghost.find_path_bfs to route the eyes back home after being eaten.

    Args:
        cell: Current ghost cell.
        home: Home corner destination.
        layout: Level grid used for pathfinding.

    Returns:
        Next cell on the return path, or None when already home or blocked.
    """
    from entities.ghost import Ghost

    ghost = Ghost("ghost", cell.row, cell.col)
    path = ghost.find_path_bfs(
        cell.row, cell.col, home.row, home.col, MapData(layout)
    )
    if len(path) >= 2:
        return CellPos(*path[1])
    return None
