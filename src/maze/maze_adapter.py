"""Bridge external maze generation to Pac-Man tile grids."""

# [wehan] origin/wehan — A-Maze-ing adaptor and wall-code conversion.

from maze.map_data import TileType


class MazeAdaptor:
    """Convert A-Maze-ing wall codes into Pac-Man ``TileType`` grids."""

    NORTH = 1  # 0001
    EAST = 2  # 0010
    SOUTH = 4  # 0100
    WEST = 8  # 1000

    def generate(
        self, width: int, height: int, seed: int
    ) -> list[list[TileType]]:
        """Build a playable maze grid from the external generator.

        Args:
            width: Maze width in generator cells.
            height: Maze height in generator cells.
            seed: Random seed passed to the generator.

        Returns:
            Tile grid, or a small fallback grid if generation fails.
        """
        try:
            from mazegenerator.mazegenerator import MazeGenerator

            generator = MazeGenerator(
                size=(width, height),
                perfect=False,
                seed=seed,
                entry_cell=(0, 0),  # testing
                exit_cell=(0, 1),  # testing
            )
            return self.convert_maze(generator.maze)
        except Exception as Error:
            print(f"Warning: maze generator failed: {Error}")
            return self.fallback_grid()

    def convert_maze(self, maze: list[list[int]]) -> list[list[TileType]]:
        """Expand wall-bit maze cells into a Pac-Man tile grid.

        Args:
            maze: Raw maze from the generator; each cell is a wall bitmask.

        Returns:
            Expanded grid of ``TileType`` values with corridors carved out.
        """
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
        """Return a minimal playable grid when generation fails.

        Returns:
            5x5 wall grid with a single open center cell.
        """
        grid = [[TileType.WALL] * 5 for _ in range(5)]
        grid[2][2] = TileType.EMPTY
        return grid
