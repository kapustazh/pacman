"""Level loading and progression mnagement."""

import random
from typing import Any




class LevelManager:
    """Manage level loading and progression."""
    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize level manager."""
        self.config = config
        self.current_level = 0

    def get_current_level(self) -> dict[str, Any]:
        """Return current level configuration."""
        return dict(self.config["levels"][self.current_level])

    def get_seed(self) -> int:
        """Return fixed seed for level 1 and random seed after."""
        if self.current_level == 0:
            return int(self.config["seed"])

        return random.randint(1, 999999)

    def has_next_level(self) -> bool:
        """Return True if another level exits."""
        return self.current_level + 1 < len(self.config["levels"])

    def go_next_level(self) -> None:
        """Move to next level."""
        self.current_level += 1
