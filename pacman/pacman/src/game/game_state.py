"""Main game state management."""

from typing import Any

from src.maze.map_data import MapData
from src.entities.player import Player


class GameState:
    """Represent the current game state."""

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize the game state."""
        self.config = config
        self.map_data = MapData()
        self.player = Player(row=2, col=2)

    def start(self) -> None:
        """Start the game loop."""
        while True:
            self.print_state()
            command = input("Move with WASD,  Q to quit: ")  
            # input read from keybaord, return str

            if command == "q" or command == "Q":
                print("Quit game.")
                break

            self.handle_input(command)  #

    def print_state(self) -> None:
        """Print current game state."""
        print("=== PAC-MAN ===")
        print(f"Score: {self.player.score}")
        print(f"Lives: {self.player.lives}")
        self.map_data.print_map(self.player.row, self.player.col)

    def handle_input(self, command: str) -> None:
        """Handle keyboard input."""
        row_delta = 0
        col_delta = 0

        if command == "w" or command == "W":
            row_delta = -1
        elif command == "s" or command == "S":
            row_delta = 1
        elif command == "a" or command == "A":
            col_delta = -1
        elif command == "d" or command == "D":
            col_delta = 1

        else:
            print("Unknown command.")
            return
        
        self.try_move_player(row_delta, col_delta)

    def try_move_player(self, row_delta: int, col_delta: int) -> None:
        """Move player if target is not wall."""
        new_row = self.player.row + row_delta
        new_col = self.player.col + col_delta

        if self.map_data.is_wall(new_row, new_col):
            print("You hit a wall")
            return
        self.player.move(row_delta, col_delta)
