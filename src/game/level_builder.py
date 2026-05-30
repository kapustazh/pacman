"""Build a playable Pac-Man level from maze tiles."""

from dataclasses import dataclass

from src.maze.map_data import TileType


@dataclass
class LevelSetup:
    """Store initial level positions."""

    player_start: tuple[int, int]
    ghost_starts: list[tuple[int, int]]


class LevelBuilder:
    """Place player, ghosts, pacgums, and super-pacgums."""
    def __init__(self, pacgum_count: int) -> None:
        """Initialize level builder."""
        self.pacgum_count = pacgum_count

    def build(self, grid: list[list[TileType]]) -> LevelSetup:
        """Populate the grid and return spawn positions."""
        height = len(grid)
        width = len(grid[0])

        player_start = self._nearest_walkable(grid, height // 2, width // 2)  # center may be wall

        corner_targets = [
            (1, 1),
            (1, width - 2),
            (height - 2, 1),
            (height - 2, width - 2),
        ]

        ghost_starts = [
            self._nearest_walkable(grid, row, col)
            for row, col in corner_targets
        ]

        reserved = set(ghost_starts)  # pacgum avoid reserved
        reserved .add(player_start)

        self._place_pacgums(grid, reserved)

        for row, col in ghost_starts:
            grid[row][col] = TileType.SUPER_PACGUM

        player_row, player_col = player_start
        grid[player_row][player_col] = TileType.EMPTY

        return LevelSetup(player_start, ghost_starts)

    def _place_pacgums(self, grid: list[list[TileType]], reserved: set[tuple[int, int]]) -> None:
        """Place normal pacgums in available corridors."""
        candidates = []

        for row, col in self._walkable_positions(grid):
            if (row, col) not in reserved:
                candidates.append((row, col))

        limit = min(self.pacgum_count, len(candidates))

        for row, col in candidates[:limit]:
            grid[row][col] = TileType.PACGUM

    def _nearest_walkable(self, grid: list[list[TileType]], target_row: int, target_col: int) -> tuple[int, int]:
        """Find nearest non-wall tile."""
        best_position = (target_row, target_col)
        best_distance = 999999

        for row, col in self._walkable_positions(grid):
            distance = abs(row - target_row) + abs(col - target_col)

            if distance < best_distance:
                best_distance = distance
                best_position = (row, col)

        return best_position

    def _walkable_positions(self, grid: list[list[TileType]]) -> list[tuple[int, int]]:
        """Return all non-wall positions."""
        positions = []

        for row_index, row in enumerate(grid):
            for col_index, tile in enumerate(row):
                if tile != TileType.WALL:
                    positions.append((row_index, col_index))

        return positions


# MazeAdapter: 造基础地图
# LevelBuilder: 初始化 items + spawn positions
# MapData: 保存当前地图/item状态
# Player/Ghost: 保存当前角色状态