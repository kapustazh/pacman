"""Ghost entity for Pac-Man."""


class Ghost:
    """Represent a ghost."""

    def __init__(self, row: int, col: int) -> None:
        """Initialize ghost position."""
        self.row = row
        self.col = col

    def move_towards(self, target_row: int, target_col: int) -> None:
        """Move one step towards the target."""
        if self.row < target_row:
            self.row += 1
        elif self.row > target_row:
            self.row -= 1
        elif self.col < target_col:
            self.col += 1
        elif self.col > target_col:
            self.col -= 1
