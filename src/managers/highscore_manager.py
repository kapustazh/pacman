"""Highscore management for Pac-Man."""

import json
from typing import Any


class HighscoreManager:
    """Manage loading, saving, and updating highscore."""

    def __init__(self, filename: str) -> None:
        """Initialize highscore manager."""
        self.filename = filename
        self.highscores: list[dict[str, Any]] = []

    def load(self) -> None:
        """Load highscores from file."""
        try:
            with open(self.filename, "r", encoding="utf-8") as file:
                data = json.load(file)
                self.highscores = self.validate_highscores(data)
        except OSError:
            self.highscores = []
            return
        except json.JSONDecodeError:
            self.highscores = []

    def save(self) -> None:
        """Save highscores to file."""
        try:
            with open(self.filename, "w", encoding="utf-8") as file:
                json.dump(self.highscores, file, indent=2)
        except OSError:
            print(f"Warning: could not save highscores to {self.filename}")

    def add_score(self, name: str, score: int) -> None:
        """Add score and keep only top 10."""
        clean_name = self.clean_name(name)

        self.highscores.append(
            {
                "name": clean_name,
                "score": score,
            }
        )

        self.highscores.sort(
            key=lambda entry: int(entry["score"]),
            reverse=True,
        )
        self.highscores = self.highscores[:10]
        self.save()

    def clean_name(self, name: str) -> str:
        """Clean player name."""
        cleaned = ""

        for char in name:
            if char.isalnum() or char == " ":
                cleaned += char

        if not cleaned:
            return "Player"

        return cleaned[:10]

    def validate_highscores(
        self,
        data: object,
    ) -> list[dict[str, Any]]:
        """Validate loaded highscore data."""
        valid_scores: list[dict[str, Any]] = []

        if not isinstance(data, list):
            return valid_scores

        for entry in data:
            if not isinstance(entry, dict):
                continue

            name = entry.get("name")
            score = entry.get("score")

            if not isinstance(name, str):
                continue
            if not isinstance(score, int):
                continue
            if score < 0:
                continue
            valid_scores.append(
                {
                    "name": self.clean_name(name),
                    "score": score,
                }
            )
        valid_scores.sort(
            key=lambda entry: int(entry["score"]),
            reverse=True,
        )

        return valid_scores[:10]

    def print_highscores(self) -> None:
        """Print highscores."""
        print("=== HIGHSCORES ===")

        if not self.highscores:
            print("No highscores yet.")
            return

        for index, entry in enumerate(self.highscores, start=1):
            print(f"{index}. {entry['name']} - {entry['score']}")
