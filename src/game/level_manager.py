"""Level loading and progression mnagement."""

import random
from typing import Any


class LevelManager:
    """Manage level loading and progression."""
    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize level manager."""
        self.config = config
        self.current_level = 0
        self.current_seed = 42

    def get_current_level(self) -> dict[str, Any]:
        """Return current level configuration."""
        return dict(self.config["levels"][self.current_level])

    def get_seed(self) -> int:
        """Return the current level seed."""
        return self.current_seed

    def has_next_level(self) -> bool:
        """Return True if another level exits."""
        return self.current_level + 1 < len(self.config["levels"])

    def go_next_level(self) -> None:
        """Move to next level."""
        self.current_level += 1
        self.current_seed = random.randint(0, 100000)
