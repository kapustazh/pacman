"""Map data structures for Pac-Man."""

from enum import Enum


class TileType(Enum):
    """All possible map tile types."""

    WALL = "#"
    EMPTY = " "
    PACGUM = "."
    SUPER_PACGUM = "o"
#  Enum = 给固定选项正式命名


class MapData:
    """Store and manage the maze grid."""

    def __init__(self) -> None:
        """Initialize a simple test map."""
        self.grid: list[list[TileType]] = [
            [TileType.WALL, TileType.WALL, TileType.WALL,
             TileType.WALL, TileType.WALL, TileType.WALL, TileType.WALL, TileType.WALL],
            [TileType.WALL, TileType.PACGUM, TileType.PACGUM,
             TileType.PACGUM, TileType.PACGUM, TileType.WALL, TileType.PACGUM, TileType.WALL],
            [TileType.WALL, TileType.PACGUM, TileType.WALL, TileType.PACGUM,
             TileType.PACGUM, TileType.PACGUM, TileType.PACGUM, TileType.WALL],
            [TileType.WALL, TileType.PACGUM, TileType.WALL, TileType.SUPER_PACGUM, TileType.SUPER_PACGUM, TileType.SUPER_PACGUM,
             TileType.PACGUM, TileType.WALL],
            [TileType.WALL, TileType.WALL, TileType.WALL,
             TileType.WALL, TileType.WALL, TileType.WALL, TileType.WALL, TileType.WALL,]
        ]

    def is_wall(self, row: int, col: int) -> bool:
        """Return True if tile is wall."""
        return self.grid[row][col] == TileType.WALL

    def print_map(self, player_row: int, player_col: int, ghost_row: int, ghost_col: int) -> None:
        """Print maze with player and ghost."""
        for row_index, row in enumerate(self.grid):
            for col_index, tile in enumerate(row):
                if row_index == player_row and col_index == player_col:
                    print("P", end="")
                elif row_index == ghost_row and col_index == ghost_col:
                    print("G", end="")
                else:
                    print(tile.value, end="")
                    # Print("P")==print("P", end="\n")
            print()

    def eat_tile(self, row: int, col: int) -> int:
        """Eat tile and return score."""
        tile = self.grid[row][col]

        if tile == TileType.PACGUM:
            self.grid[row][col] == TileType.EMPTY
            return 10

        if tile == TileType.SUPER_PACGUM:
            self.grid[row][col] == TileType.EMPTY
            return 50

        return 0

