"""Adaptor for the assigned A-Maze-ing package."""

import random

from maze.map_data import TileType


class MazeAdaptor:
    """Convert external maze output into Pac-Man tile grid."""
    NORTH = 1  # 0001
    EAST = 2   # 0010
    SOUTH = 4  # 0100
    WEST = 8   # 1000

    def generate(
        self, width: int,
        height: int,
        seed: int
    ) -> list[list[TileType]]:
        """Generate a maze using the external package."""
        try:
            from mazegenerator.mazegenerator import MazeGenerator

            class _FastMazeGenerator(MazeGenerator):
                # ponytail: skip _find_short_path — unused, ~15s on 21x21
                def generate(self, seed: int = 0) -> None:
                    random.seed(seed) if seed > 0 else random.seed()
                    self._seed = seed
                    self._create_empty_maze()
                    self._add_42_to_maze()
                    self._generate_maze(self._entryx, self._entryy, 0)

            generator = _FastMazeGenerator(
                size=(width, height),
                perfect=False,
                seed=seed,
            )
            return self.convert_maze(generator.maze)
        except Exception as Error:
            print(f"Warning: maze generator failed: {Error}")
            return self.fallback_grid()

    def convert_maze(self, maze: list[list[int]]) -> list[list[TileType]]:
        """Convert wall-code maze into TileType grid."""
        grid_height = len(maze) * 2 + 1
        grid_width = len(maze[0]) * 2 + 1

        grid = [
            [TileType.WALL for _ in range(grid_width)]
            for _ in range(grid_height)
        ]

        for row_index, row in enumerate(maze):
            for col_index, cell in enumerate(row):
                grid_row = row_index * 2 + 1
                grid_col = col_index * 2 + 1

                grid[grid_row][grid_col] = TileType.EMPTY

                if cell & self.NORTH == 0 and grid_row > 1:
                    grid[grid_row - 1][grid_col] = TileType.EMPTY
                if cell & self.EAST == 0 and grid_col < grid_width - 2:
                    grid[grid_row][grid_col + 1] = TileType.EMPTY
                if cell & self.SOUTH == 0 and grid_row < grid_height - 2:
                    grid[grid_row + 1][grid_col] = TileType.EMPTY
                if cell & self.WEST == 0 and grid_col > 1:
                    grid[grid_row][grid_col - 1] = TileType.EMPTY
        return grid

    def fallback_grid(self) -> list[list[TileType]]:
        """Return a minimal fallback grid if generation fails."""
        grid = [[TileType.WALL] * 5 for _ in range(5)]
        grid[2][2] = TileType.EMPTY
        return grid
