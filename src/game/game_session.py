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
    """Tracks lives, level index, score, timer, and current gameplay phase."""

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
        """Return whole seconds left on the level timer.

        Returns:
            Non-negative seconds remaining.
        """
        return max(0, self.remaining_time_ms // 1000)

    def level_elapsed_s(self) -> int:
        """Return whole seconds elapsed since the level timer started.

        Returns:
            Non-negative seconds elapsed.
        """
        return max(0, self.level_time_limit_s - self.remaining_time_s())

    def reset_level_timer(self) -> None:
        """Reset the countdown to the full level time limit."""
        self.remaining_time_ms = self.level_time_limit_s * 1000

    def update_high_score(self, score: int) -> None:
        """Update the session high score if the given score is higher.

        Args:
            score: Score to compare against the current high score.
        """
        if score > self.high_score:
            self.high_score = score

    def sync_score(self, world_score: int) -> None:
        """Persist the active world's score before teardown.

        Args:
            world_score: Score from the live game world.
        """
        self.score = max(self.score, world_score)

    def tick_timer(self, dt_s: float) -> bool:
        """Subtract elapsed play time while in the PLAYING phase.

        Args:
            dt_s: Elapsed time in seconds since the last tick.

        Returns:
            True when the timer reaches zero during active play.
        """
        if self.phase != GameplayPhase.PLAYING:
            return False
        elapsed_ms = int(dt_s * 1000)
        if elapsed_ms <= 0:
            return self.remaining_time_ms == 0
        self.remaining_time_ms = max(0, self.remaining_time_ms - elapsed_ms)
        return self.remaining_time_ms == 0

    def enter_ready(self, now_ms: int) -> None:
        """Enter the pre-round READY phase.

        Args:
            now_ms: Current timestamp in milliseconds.
        """
        self.phase = GameplayPhase.READY
        self.phase_started_at_ms = now_ms

    def begin_play(self, now_ms: int) -> None:
        """Start active gameplay and the level timer.

        Args:
            now_ms: Current timestamp in milliseconds.
        """
        self.phase = GameplayPhase.PLAYING
        self.phase_started_at_ms = now_ms

    def lose_life(self, now_ms: int) -> None:
        """Decrement lives and enter the life-lost phase.

        Args:
            now_ms: Current timestamp in milliseconds.
        """
        self.lives = max(0, self.lives - 1)
        self.phase = GameplayPhase.LIFE_LOST
        self.phase_started_at_ms = now_ms

    def enter_game_over(self, now_ms: int) -> None:
        """Enter the game-over phase.

        Args:
            now_ms: Current timestamp in milliseconds.
        """
        self.phase = GameplayPhase.GAME_OVER
        self.phase_started_at_ms = now_ms

    def enter_level_complete(self, now_ms: int) -> None:
        """Enter the level-complete transition phase.

        Args:
            now_ms: Current timestamp in milliseconds.
        """
        self.phase = GameplayPhase.LEVEL_COMPLETE
        self.phase_started_at_ms = now_ms

    def advance_level(self) -> None:
        """Increment the level index for the next round."""
        self.level_number += 1

    def phase_elapsed_ms(self, now_ms: int) -> int:
        """Return milliseconds spent in the current phase.

        Args:
            now_ms: Current timestamp in milliseconds.

        Returns:
            Non-negative milliseconds since the phase started.
        """
        return max(0, now_ms - self.phase_started_at_ms)
