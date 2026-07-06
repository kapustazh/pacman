"""Build a playable Pac-Man level from maze tiles."""

# [wehan] origin/wehan — LevelBuilder maze population.

from maze.map_data import TileType

import random
from collections import deque

from game.level import CellPos, LevelLayout
from sprites.sprite_types import GhostKind

_GHOST_ORDER: tuple[GhostKind, ...] = (
    GhostKind.BLINKY,
    GhostKind.PINKY,
    GhostKind.INKY,
    GhostKind.CLYDE,
)


class LevelBuilder:
    """Place player, ghosts, pacgums, and super-pacgums."""

    def __init__(self, pacgum_count: int) -> None:
        """Initialize level builder."""
        self.pacgum_count = pacgum_count

    def build(self, grid: list[list[TileType]]) -> LevelLayout:
        """Populate the grid and return a level layout."""
        height = len(grid)
        width = len(grid[0])

        # [wehan] player and ghost spawn placement
        player_start = self._nearest_walkable(grid, height // 2, width // 2)

        reachable = self._reachable_positions(grid, player_start)

        corner_targets = [
            (1, 1),
            (1, width - 2),
            (height - 2, 1),
            (height - 2, width - 2),
        ]

        corner_positions = self._find_corner_positions(
            grid, corner_targets, reachable
        )
        ghost_starts = corner_positions.copy()

        reserved = set(ghost_starts)
        reserved.add(player_start)

        self._place_pacgums(grid, reserved, reachable)
        self._place_super_pacgums(grid, corner_positions)

        player_row, player_col = player_start
        grid[player_row][player_col] = TileType.EMPTY

        pellets: set[CellPos] = set()
        power_pellets: set[CellPos] = set()
        for row_index, row in enumerate(grid):
            for col_index, tile in enumerate(row):
                pos = CellPos(row_index, col_index)
                if tile == TileType.PACGUM:
                    pellets.add(pos)
                elif tile == TileType.SUPER_PACGUM:
                    power_pellets.add(pos)

        player_spawn = CellPos(*player_start)
        ghost_spawns = tuple(
            (kind, CellPos(*corner))
            for kind, corner in zip(_GHOST_ORDER, ghost_starts)
        )

        return LevelLayout(
            cells=tuple(tuple(row) for row in grid),
            pellet_cells=frozenset(pellets),
            power_pellet_cells=frozenset(power_pellets),
            player_spawn=player_spawn,
            ghost_spawns=ghost_spawns,
            fruit_spawn=player_spawn,
        )

    def _place_pacgums(
        self,
        grid: list[list[TileType]],
        reserved: set[tuple[int, int]],
        reachable: set[tuple[int, int]],
    ) -> None:
        """Place normal pacgums in corridors the player can actually reach."""
        candidates = [
            (row, col) for row, col in reachable if (row, col) not in reserved
        ]
        random.shuffle(candidates)
        limit = min(self.pacgum_count, len(candidates))
        for row, col in candidates[:limit]:
            grid[row][col] = TileType.PACGUM

    def _place_super_pacgums(
        self,
        grid: list[list[TileType]],
        positions: list[tuple[int, int]],
    ) -> None:
        """Place exactly four super-pacgums near maze corners."""
        for row, col in positions[:4]:
            grid[row][col] = TileType.SUPER_PACGUM

    def _find_corner_positions(
        self,
        grid: list[list[TileType]],
        corner_targets: list[tuple[int, int]],
        reachable: set[tuple[int, int]],
    ) -> list[tuple[int, int]]:
        """Find four unique reachable positions near the four corners."""
        positions: list[tuple[int, int]] = []
        for target_row, target_col in corner_targets:
            position = self._nearest_walkable(
                grid,
                target_row,
                target_col,
                excluded=set(positions),
                reachable=reachable,
            )
            positions.append(position)
        return positions

    def _nearest_walkable(
        self,
        grid: list[list[TileType]],
        target_row: int,
        target_col: int,
        excluded: set[tuple[int, int]] | None = None,
        reachable: set[tuple[int, int]] | None = None,
    ) -> tuple[int, int]:
        """Find nearest non-wall tile, optionally skipping excluded cells.

        When `reachable` is given, only cells in that set are considered —
        used once the player's start is known, so corner/ghost spawns never
        land in a floor pocket disconnected from the player.
        """
        skip = excluded or set()
        candidates = (
            self._walkable_positions(grid) if reachable is None else reachable
        )
        best_position = (target_row, target_col)
        best_distance = 999999
        for row, col in candidates:
            if (row, col) in skip:
                continue
            distance = abs(row - target_row) + abs(col - target_col)
            if distance < best_distance:
                best_distance = distance
                best_position = (row, col)
        return best_position

    def _reachable_positions(
        self,
        grid: list[list[TileType]],
        start: tuple[int, int],
    ) -> set[tuple[int, int]]:
        """Flood-fill every non-wall cell reachable from start."""
        height = len(grid)
        width = len(grid[0])
        seen = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for delta_row, delta_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                next_row, next_col = row + delta_row, col + delta_col
                if not (0 <= next_row < height and 0 <= next_col < width):
                    continue
                if (next_row, next_col) in seen:
                    continue
                if grid[next_row][next_col] == TileType.WALL:
                    continue
                seen.add((next_row, next_col))
                queue.append((next_row, next_col))
        return seen

    def _walkable_positions(
        self,
        grid: list[list[TileType]],
    ) -> list[tuple[int, int]]:
        """Return all non-wall positions."""
        return [
            (row_index, col_index)
            for row_index, row in enumerate(grid)
            for col_index, tile in enumerate(row)
            if tile != TileType.WALL
        ]
