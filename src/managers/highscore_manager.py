"""Persist and rank Pac-Man high scores."""

# [wehan] origin/wehan — persistent leaderboard.

from __future__ import annotations

import json
from typing import Any


class HighscoreManager:
    """Load, save, and rank the top ten scores."""

    def __init__(self, filename: str) -> None:
        """Create a manager bound to one JSON file.

        Args:
            filename: Path used for load and save.
        """
        self.filename = filename
        self.highscores: list[dict[str, Any]] = []

    def load(self) -> None:
        """Read scores from disk and keep only valid top-ten entries."""
        try:
            with open(self.filename, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError):
            self.highscores = []
            return
        self.highscores = self._top10(
            entry
            for entry in (data if isinstance(data, list) else [])
            if isinstance(entry, dict)
            and isinstance(entry.get("name"), str)
            and isinstance(entry.get("score"), int)
            and entry.get("score", -1) >= 0
        )

    def save(self) -> None:
        """Write the current top-ten list to disk."""
        try:
            with open(self.filename, "w", encoding="utf-8") as file:
                json.dump(self.highscores, file, indent=2)
        except OSError:
            print(f"Warning: could not save highscores to {self.filename}")

    def add_score(self, name: str, score: int) -> None:
        """Append a score, trim to top ten, and persist.

        Args:
            name: Player initials or name.
            score: Points earned this run.
        """
        self.highscores.append(
            {"name": self._clean_name(name), "score": max(0, score)}
        )
        self.highscores = self._top10(self.highscores)
        self.save()

    def top_score(self) -> int:
        """Return the best stored score.

        Returns:
            Highest score, or 0 when the table is empty.
        """
        return int(self.highscores[0]["score"]) if self.highscores else 0

    @staticmethod
    def _top10(entries: Any) -> list[dict[str, Any]]:
        """Sort entries by score and keep the top ten.

        Args:
            entries: Iterable of ``{name, score}`` dicts.

        Returns:
            Highest-scoring entries, newest ties preserved by sort stability.
        """
        return sorted(
            entries,
            key=lambda entry: int(entry["score"]),
            reverse=True,
        )[:10]

    @staticmethod
    def clean_name(name: str) -> str:
        """Public alias for name cleanup before saving.

        Args:
            name: Raw player input.

        Returns:
            Sanitized name safe to store.
        """
        return HighscoreManager._clean_name(name)

    @staticmethod
    def _clean_name(name: str) -> str:
        """Strip invalid characters and cap length.

        Args:
            name: Raw player input.

        Returns:
            Cleaned name, or ``"Player"`` when empty.
        """
        cleaned = "".join(c for c in name if c.isalnum() or c == " ")
        return cleaned[:10] or "Player"
