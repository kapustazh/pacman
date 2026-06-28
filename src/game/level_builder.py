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

        player_start = self._nearest_walkable(grid, height // 2, width // 2)
        # center may be wall

        corner_targets = [
            (1, 1),
            (1, width - 2),
            (height - 2, 1),
            (height - 2, width - 2),
        ]

        corner_positions = self._find_corner_positions(grid, corner_targets)
        ghost_starts = corner_positions.copy()

        reserved = set(ghost_starts)  # pacgum avoid reserved
        reserved.add(player_start)

        self._place_pacgums(grid, reserved)
        self._place_super_pacgums(grid, corner_positions)

        player_row, player_col = player_start
        grid[player_row][player_col] = TileType.EMPTY

        return LevelSetup(player_start, ghost_starts)

    def _place_pacgums(self, grid: list[list[TileType]],
                       reserved: set[tuple[int, int]]) -> None:
        """Place normal pacgums in available corridors."""
        candidates = []

        for row, col in self._walkable_positions(grid):
            if (row, col) not in reserved:
                candidates.append((row, col))

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
    ) -> list[tuple[int, int]]:
        """Find four unique walkable positions near the four corners."""
        positions: list[tuple[int, int]] = []

        for target_row, target_col in corner_targets:
            position = self._nearest_walkable_excluding(
                grid,
                target_row,
                target_col,
                set(positions),  # exclude added ghost respawn spots
            )
            positions.append(position)
        return positions

    def _nearest_walkable(self, grid: list[list[TileType]],
                          target_row: int, target_col: int) -> tuple[int, int]:
        """Find nearest non-wall tile."""
        best_position = (target_row, target_col)
        best_distance = 999999

        for row, col in self._walkable_positions(grid):
            distance = abs(row - target_row) + abs(col - target_col)

            if distance < best_distance:
                best_distance = distance
                best_position = (row, col)

        return best_position

    def _nearest_walkable_excluding(
        self,
        grid: list[list[TileType]],
        target_row: int,
        target_col: int,
        excluded: set[tuple[int, int]],
    ) -> tuple[int, int]:
        """Find nearest non-wall tile that is not excluded."""
        best_position = (target_row, target_col)
        best_distance = 999999

        for row, col in self._walkable_positions(grid):
            if (row, col) in excluded:
                continue
            distance = abs(row - target_row) + abs(col - target_col)
            if distance < best_distance:
                best_distance = distance
                best_position = (row, col)
        return best_position

    def _walkable_positions(
            self,
            grid: list[list[TileType]]
    ) -> list[tuple[int, int]]:
        """Return all non-wall positions."""
        positions = []

        for row_index, row in enumerate(grid):
            for col_index, tile in enumerate(row):
                if tile != TileType.WALL:
                    positions.append((row_index, col_index))

        return positions

# MazeAdapter: 生成基础迷宫（WALL / EMPTY）
# LevelBuilder: 选择玩家和鬼出生点，并放置 Pacgums、Super Pacgums
# MapData: 保存当前地图和所有物品状态
# Player/Ghost: 保存角色当前位置和状态
