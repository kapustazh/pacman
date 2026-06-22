from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

DEFAULT_LIVES = 3
DEFAULT_LEVEL_TIME_S = 90

READY_DURATION_MS = 2000
LIFE_LOST_DURATION_MS = 2000
LEVEL_COMPLETE_DURATION_MS = 2000
GAME_OVER_DURATION_MS = 2000


class GameplayPhase(Enum):
    """In-level gameplay phases for classic Pac-Man flow."""

    READY = auto()
    PLAYING = auto()
    LIFE_LOST = auto()
    LEVEL_COMPLETE = auto()
    GAME_OVER = auto()
    VICTORY = auto()


@dataclass(frozen=True, slots=True)
class HudSnapshot:
    """Read-only HUD values for one draw frame."""

    score: int
    high_score: int
    lives: int
    spare_lives: int
    level_number: int
    remaining_time_s: int
    phase: GameplayPhase
    message: str | None


@dataclass(slots=True)
class GameSession:
    """Run-level metadata: lives, level index, timer, and gameplay phase."""

    level_number: int = 1
    lives: int = DEFAULT_LIVES
    level_time_limit_s: int = DEFAULT_LEVEL_TIME_S
    remaining_time_ms: int = DEFAULT_LEVEL_TIME_S * 1000
    high_score: int = 0
    phase: GameplayPhase = GameplayPhase.READY
    phase_started_at_ms: int = 0

    def spare_lives(self) -> int:
        """Return spare lives shown as icons (classic shows lives minus current)."""
        return max(0, self.lives - 1)

    def remaining_time_s(self) -> int:
        """Return whole seconds left on the current level."""
        return max(0, self.remaining_time_ms // 1000)

    def reset_level_timer(self) -> None:
        """Reset countdown to full level limit."""
        self.remaining_time_ms = self.level_time_limit_s * 1000

    def update_high_score(self, score: int) -> None:
        """Track best score seen this session until persistence lands."""
        if score > self.high_score:
            self.high_score = score

    def tick_timer(self, dt_s: float) -> bool:
        """Subtract elapsed time while playing. Return True when timer hits zero."""
        if self.phase != GameplayPhase.PLAYING:
            return False
        elapsed_ms = int(dt_s * 1000)
        if elapsed_ms <= 0:
            return self.remaining_time_ms == 0
        self.remaining_time_ms = max(0, self.remaining_time_ms - elapsed_ms)
        return self.remaining_time_ms == 0

    def enter_ready(self, now_ms: int) -> None:
        """Enter pre-round ready state."""
        self.phase = GameplayPhase.READY
        self.phase_started_at_ms = now_ms

    def begin_play(self, now_ms: int) -> None:
        """Start active gameplay and level timer."""
        self.phase = GameplayPhase.PLAYING
        self.phase_started_at_ms = now_ms

    def lose_life(self, now_ms: int) -> None:
        """Decrement lives and enter life-lost phase."""
        self.lives = max(0, self.lives - 1)
        self.phase = GameplayPhase.LIFE_LOST
        self.phase_started_at_ms = now_ms

    def enter_game_over(self, now_ms: int) -> None:
        """Enter terminal game-over phase."""
        self.phase = GameplayPhase.GAME_OVER
        self.phase_started_at_ms = now_ms

    def enter_level_complete(self, now_ms: int) -> None:
        """Enter level-complete transition phase."""
        self.phase = GameplayPhase.LEVEL_COMPLETE
        self.phase_started_at_ms = now_ms

    def advance_level(self) -> None:
        """Increment level index and reset timer for next round."""
        self.level_number += 1
        self.reset_level_timer()

    def phase_elapsed_ms(self, now_ms: int) -> int:
        """Return milliseconds spent in the current phase."""
        return max(0, now_ms - self.phase_started_at_ms)

    def snapshot(self, score: int) -> HudSnapshot:
        """Build HUD snapshot from current session and score."""
        self.update_high_score(score)
        return HudSnapshot(
            score=score,
            high_score=self.high_score,
            lives=self.lives,
            spare_lives=self.spare_lives(),
            level_number=self.level_number,
            remaining_time_s=self.remaining_time_s(),
            phase=self.phase,
            message=_phase_message(self.phase),
        )


def _phase_message(phase: GameplayPhase) -> str | None:
    """Return centered overlay text for a gameplay phase."""
    if phase == GameplayPhase.READY:
        return "READY!"
    if phase == GameplayPhase.LEVEL_COMPLETE:
        return "LEVEL CLEAR"
    if phase == GameplayPhase.GAME_OVER:
        return "GAME OVER"
    if phase == GameplayPhase.VICTORY:
        return "YOU WIN"
    return None
