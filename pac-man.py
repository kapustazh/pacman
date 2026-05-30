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
    # print(config)

    return 0


if __name__ == "__main__":
    main()

# add level builder and multi ghost gameplay

# - Added LevelBuilder for automated level setup
# - Generate playable levels from maze layouts
# - Added player spawn initialization
# - Added four ghost spawn positions
# - Implemented pacgum placement logic
# - Implemented super pacgum placement
# - Added multi-ghost support
# - Added TerminalRenderer for map display
# - Implemented ghost-player collision handling
# - Added player and ghost respawn system
# - Added cheat mode framework (invincibility, ghost freeze, extra life, level skip)
# - Refactored GameState to separate gameplay and level setup responsibilities