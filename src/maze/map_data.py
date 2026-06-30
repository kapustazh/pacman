"""Map data structures for Pac-Man."""

# [wehan] origin/wehan — TileType grid model.

from enum import Enum


class TileType(Enum):
    """All possible map tile types."""

    WALL = "#"
    EMPTY = " "
    PACGUM = "."
    SUPER_PACGUM = "o"
