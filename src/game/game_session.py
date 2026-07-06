# [transition] SCRUM-35 — lives, timer, and phase flow from wehan GameState.

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import ClassVar


class GameplayPhase(Enum):
    """In-level gameplay phases for classic Pac-Man flow."""

    READY = auto()
    PLAYING = auto()
    LIFE_LOST = auto()
    LEVEL_COMPLETE = auto()
    GAME_OVER = auto()


@dataclass(slots=True)
class GameSession:
    """Run-level metadata: lives, level index, timer, and gameplay phase."""

    DEFAULT_LIVES: ClassVar[int] = 3
    # [wehan] level_max_time config key; seconds (was turns in wehan)
    DEFAULT_LEVEL_TIME_S: ClassVar[int] = 90
    READY_DURATION_MS: ClassVar[int] = 2000
    LIFE_LOST_DURATION_MS: ClassVar[int] = 2000
    LEVEL_COMPLETE_DURATION_MS: ClassVar[int] = 2500
    GAME_OVER_DURATION_MS: ClassVar[int] = 2000
    PHASE_MESSAGE: ClassVar[dict[GameplayPhase, str | None]] = {
        GameplayPhase.READY: "READY!",
        GameplayPhase.LEVEL_COMPLETE: "LEVEL CLEAR",
        GameplayPhase.GAME_OVER: "GAME OVER",
    }

    level_number: int = 1
    lives: int = DEFAULT_LIVES
    level_time_limit_s: int = DEFAULT_LEVEL_TIME_S
    remaining_time_ms: int = DEFAULT_LEVEL_TIME_S * 1000
    score: int = 0
    high_score: int = 0
    phase: GameplayPhase = GameplayPhase.READY
    phase_started_at_ms: int = 0

    def remaining_time_s(self) -> int:
        """Return whole seconds left on the current level."""
        return max(0, self.remaining_time_ms // 1000)

    def level_elapsed_s(self) -> int:
        """Return whole seconds elapsed in the current level timer."""
        return max(0, self.level_time_limit_s - self.remaining_time_s())

    def reset_level_timer(self) -> None:
        """Reset countdown to full level limit."""
        self.remaining_time_ms = self.level_time_limit_s * 1000

    def update_high_score(self, score: int) -> None:
        """Track best score seen this session until persistence lands."""
        if score > self.high_score:
            self.high_score = score

    def sync_score(self, world_score: int) -> None:
        """Persist run score from the active world before teardown."""
        self.score = max(self.score, world_score)

    def tick_timer(self, dt_s: float) -> bool:
        """Subtract play time. Return True when timer hits zero."""
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
        """Increment level index for the next round."""
        self.level_number += 1

    def phase_elapsed_ms(self, now_ms: int) -> int:
        """Return milliseconds spent in the current phase."""
        return max(0, now_ms - self.phase_started_at_ms)
