"""Map data structures for Pac-Man."""

from enum import Enum


class TileType(Enum):
    """All possible map tile types."""

    WALL = "#"
    EMPTY = " "
    PACGUM = "."
    SUPER_PACGUM = "o"
