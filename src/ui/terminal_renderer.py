"""Terminal rendering for Pac-Man."""

from src.entities.ghost import Ghost
from src.maze.map_data import MapData


class TerminalRenderer:
    """Render game state in terminal."""

    def print_map(
        self,
        map_data: MapData,
        player_row: int,
        player_col: int,
        ghosts: list[Ghost]
    ) -> None:
        """Print map with player and ghost."""
        for row_index, row in enumerate(map_data.grid):
            for col_index, tile in enumerate(row):
                if row_index == player_row and col_index == player_col:
                    print("P", end="")
                elif self._has_ghost(row_index, col_index, ghosts):
                    print("G", end="")
                else:
                    print(tile.value, end="")
                    # Print("P")==print("P", end="\n")
            print()

    def _has_ghost(self, row: int, col: int, ghosts: list[Ghost]) -> bool:
        """Return True if ghost is on position."""
        for ghost in ghosts:
            if ghost.active and ghost.row == row and ghost.col == col:
                return True

        return False
