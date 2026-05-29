"""Player entity for Pac-Man."""


class Player:
    """Represent the player."""

    def __init__(self, row: int, col: int) -> None:
        """Initialize player position."""
        self.row = row
        self.col = col
        self.score = 0
        self.lives = 3

    def move(self, row_delta: int, col_delta: int) -> None:
        """Move player."""
        self.row += row_delta
        self.col += col_delta
