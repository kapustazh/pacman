"""Player entity for Pac-Man."""


class Player:
    """Represent the player."""

    def __init__(self, row: int, col: int) -> None:
        """Initialize player position."""
        self.row = row
        self.col = col
        self.score = 0
        self.lives = 3

        # Store the player's last movement direction for Pinky/Inky
        self.last_row_delta = 0
        self.last_col_delta = 0

    def move(self, row_delta: int, col_delta: int) -> None:
        """Move player."""
        self.last_row_delta = row_delta
        self.last_col_delta = col_delta
        self.row += row_delta
        self.col += col_delta
