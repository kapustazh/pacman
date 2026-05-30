"""Map data structures for Pac-Man."""

from enum import Enum


class TileType(Enum):
    """All possible map tile types."""

    WALL = "#"
    EMPTY = " "
    PACGUM = "."
    SUPER_PACGUM = "o"


class MapData:
    """Store and manage the maze grid."""

    def __init__(self, grid: list[list[TileType]]) -> None:
        """Initialize a simple test map."""
        self.grid = grid

    def is_wall(self, row: int, col: int) -> bool:
        """Return True if tile is wall."""
        return self.grid[row][col] == TileType.WALL

    def is_walkable(self, row: int, col: int) -> bool:
        """Return True if tile is not wall."""
        return not self.is_wall(row, col)

    def eat_tile(self, row: int, col: int) -> int:
        """Eat tile and return gained score."""
        tile = self.grid[row][col]

        if tile == TileType.PACGUM:
            self.grid[row][col] = TileType.EMPTY
            return 10

        if tile == TileType.SUPER_PACGUM:
            self.grid[row][col] = TileType.EMPTY
            return 50

        return 0

    def check_pacgum_left(self) -> bool:
        """Return True if any pacgum or super pacgum is left. """
        for row in self.grid:
            for tile in row:
                if tile == TileType.PACGUM:
                    return True
                elif tile == TileType.SUPER_PACGUM:
                    return True
        return False
