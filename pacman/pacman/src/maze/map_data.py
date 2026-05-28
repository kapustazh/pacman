from enum import Enum


class TileType(Enum):
    """All possible map tile types."""

    WALL = "#"
    EMPTY = " "
    PACGUM = "."
    SUPER_PACGUM = "o"


class MapData:
    """Store and manage the maze grid."""

    def __init__(self) -> None:
        """Initialize a simple test map."""
        self.grid: list[list[TileType]] = [
            [TileType.WALL, TileType.WALL, TileType.WALL,
             TileType.WALL, TileType.WALL],
            [TileType.WALL, TileType.PACGUM, TileType.PACGUM,
             TileType.PACGUM, TileType.WALL],
            [TileType.WALL, TileType.PACGUM, TileType.EMPTY,
             TileType.PACGUM, TileType.WALL],
            [TileType.WALL, TileType.PACGUM, TileType.SUPER_PACGUM,
             TileType.PACGUM, TileType.WALL],
            [TileType.WALL, TileType.WALL, TileType.WALL,
             TileType.WALL, TileType.WALL],
        ]

    def print_map(self) -> None:
        """Print the maze to the terminal."""
        for row in self.grid:
            for tile in row:
                print(tile.value, end="")
            print()
