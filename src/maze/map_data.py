"""Tile type enum for Pac-Man maze grids."""

# [wehan] origin/wehan — TileType grid model.

from enum import Enum


class TileType(Enum):
    """Symbols used for walls, paths, and pellets in maze data."""

    WALL = "#"
    EMPTY = " "
    PACGUM = "."
    SUPER_PACGUM = "o"
