"""Ghost entity for Pac-Man."""

from src.maze.map_data import MapData


class Ghost:
    """Represent a ghost."""

    def __init__(self, name: str, row: int, col: int) -> None:
        """Initialize ghost position."""
        self.name = name
        self.row = row
        self.col = col

    def move_towards(self, target_row: int, target_col: int, map_data: MapData) -> None:
        """
        Move one step towards the target without crossing walls.
        -check 4 directions
        -ignore walls
        -choose smallest Manhattan distance
        """
        moves = [
            (0, 1),  # right
            (0, -1),  # left
            (-1, 0),  # up
            (1, 0),  # down
        ]

        best_row = self.row
        best_col = self.col

        best_distance = (
            abs(self.row - target_row)
            + abs(self.col - target_col)
        )

        for row_delta, col_delta in moves:
            new_row = self.row + row_delta
            new_col = self.col + col_delta

            if map_data.is_wall(new_row, new_col):
                continue

            distance = (
                abs(new_row - target_row)
                + abs(new_col - target_col)
            )

            if distance < best_distance:
                best_distance = distance
                best_row = new_row
                best_col = new_col

        self.row = best_row
        self.col = best_col
