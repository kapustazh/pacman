"""Entry point for the Pac-Man project."""

import sys

from src.config import load_config


def main() -> int:
    """Run the Pac-Man game."""
    if len(sys.argv) != 2:
        print("Usage: python3 pac-man.py config.json")
        return 1

    config_path = sys.argv[1]
    config = load_config(config_path)
    print(config)

    return 0


if __name__ == "__main__":
    main()
