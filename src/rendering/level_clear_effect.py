from __future__ import annotations

from typing import ClassVar


class LevelClearEffect:
    """Maze wall flash timing during LEVEL_COMPLETE."""

    FLASH_PERIOD_MS: ClassVar[int] = 200
    FLASH_COUNT: ClassVar[int] = 6

    def is_white_phase(self, elapsed_ms: int) -> bool:
        """Return True during the white half of each flash cycle."""
        cycle_ms = elapsed_ms % (self.FLASH_PERIOD_MS * 2)
        return cycle_ms < self.FLASH_PERIOD_MS
