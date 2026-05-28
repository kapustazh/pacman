"""Main game state management."""

from typing import Any

from src.maze.map_data import MapData


class GameState:
    """Represent the current game state."""

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize the game state."""
        self.config = config
        self.map_data = MapData()

    def start(self) -> None:
        """Start the game."""
        print("=== PAC-MAN ===")
        print(f"Lives: {self.config['lives']}")
        self.map_data.print_map()
