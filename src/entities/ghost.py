"""Ghost entity for Pac-Man."""

from src.maze.map_data import MapData
import random


class Ghost:
    """Represent a ghost."""

    def __init__(self, name: str, row: int, col: int) -> None:
        """Initialize ghost position."""
        self.name = name
        self.row = row
        self.col = col
        self.edible = False

    def move_towards(self, target_row: int, target_col: int, map_data: MapData) -> None:
        """
        Move one step towards the target without crossing walls.
        -check 4 directions
        -ignore walls
        -choose smallest Manhattan distance
        -if no better move exists, choose any valid move
        """
        moves = [
            (0, 1),  # right
            (0, -1),  # left
            (-1, 0),  # up
            (1, 0),  # down
        ]

        best_row = self.row
        best_col = self.col
        valid_moves: list[tuple[int, int]] = []

        best_distance = (
            abs(self.row - target_row)
            + abs(self.col - target_col)
        )

        for row_delta, col_delta in moves:
            new_row = self.row + row_delta
            new_col = self.col + col_delta

            if map_data.is_wall(new_row, new_col):
                continue

            valid_moves.append((new_row, new_col))

            distance = (
                abs(new_row - target_row)
                + abs(new_col - target_col)
            )

            if distance < best_distance:
                best_distance = distance
                best_row = new_row
                best_col = new_col

            if valid_moves and best_row == self.row and best_col == self.col:
                best_row, best_col = random.choice(valid_moves)

        self.row = best_row
        self.col = best_col

    def move_away(self, target_row: int, target_col: int, map_data: MapData) -> None:
        """
        Move one step away from the target without crossing walls.
        -check 4 directions
        -ignore walls
        -choose smallest Manhattan distance
        -if no better move exists, choose any valid move
        """
        moves = [
            (0, 1),  # right
            (0, -1),  # left
            (-1, 0),  # up
            (1, 0),  # down
        ]

        best_row = self.row
        best_col = self.col
        valid_moves: list[tuple[int, int]] = []

        best_distance = (
            abs(self.row - target_row)
            + abs(self.col - target_col)
        )

        for row_delta, col_delta in moves:
            new_row = self.row + row_delta
            new_col = self.col + col_delta

            if map_data.is_wall(new_row, new_col):
                continue

            valid_moves.append((new_row, new_col))

            distance = (
                abs(new_row - target_row)
                + abs(new_col - target_col)
            )

            if distance > best_distance:
                best_distance = distance
                best_row = new_row
                best_col = new_col

            if valid_moves and best_row == self.row and best_col == self.col:
                best_row, best_col = random.choice(valid_moves)

        self.row = best_row
        self.col = best_col
