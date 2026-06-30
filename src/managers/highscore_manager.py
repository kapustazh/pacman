"""Highscore management for Pac-Man."""

from __future__ import annotations

import json
from typing import Any


class HighscoreManager:
    """Load, save, and rank highscores (top 10)."""

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.highscores: list[dict[str, Any]] = []

    def load(self) -> None:
        """Load and validate highscores from file."""
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
        """Persist highscores to file."""
        try:
            with open(self.filename, "w", encoding="utf-8") as file:
                json.dump(self.highscores, file, indent=2)
        except OSError:
            print(f"Warning: could not save highscores to {self.filename}")

    def add_score(self, name: str, score: int) -> None:
        """Add score, keep top 10, persist."""
        self.highscores.append(
            {"name": self._clean_name(name), "score": max(0, score)}
        )
        self.highscores = self._top10(self.highscores)
        self.save()

    def top_score(self) -> int:
        """Return best score, or 0 if empty."""
        return int(self.highscores[0]["score"]) if self.highscores else 0

    @staticmethod
    def _top10(entries: Any) -> list[dict[str, Any]]:
        return sorted(
            entries,
            key=lambda entry: int(entry["score"]),
            reverse=True,
        )[:10]

    @staticmethod
    def clean_name(name: str) -> str:
        return HighscoreManager._clean_name(name)

    @staticmethod
    def _clean_name(name: str) -> str:
        cleaned = "".join(c for c in name if c.isalnum() or c == " ")
        return cleaned[:10] or "Player"
