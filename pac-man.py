"""Entry point for the Pac-Man project."""

import sys

from src.config import load_config
from src.game.game_state import GameState


def main() -> int:
    """Start the Pac-Man game."""
    if len(sys.argv) != 2:
        print("Usage: python3 pac-man.py config.json")
        return 1

    config = load_config(sys.argv[1])
    game = GameState(config)
    game.start()

    return 0


if __name__ == "__main__":
    main()
