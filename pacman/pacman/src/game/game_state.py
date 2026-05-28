"""Main game state management."""

from typing import Any

from src.maze.map_data import MapData
from src.entities.player import Player
from src.entities.ghost import Ghost
from src.managers.highscore_manager import HighscoreManager
from src.maze.maze_adaptor import MazeAdaptor


class GameState:
    """Represent the current game state."""

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize the game state."""
        self.config = config
        # self.map_data = MapData()
        level = self.config["levels"][0]
        adaptor = MazeAdaptor()
        grid = adaptor.generate(width=int(level["width"]), height=int(level["height"]), seed=int(self.config["seed"]))
        self.map_data = MapData(grid)

        self.player = Player(row=2, col=2)
        self.player.lives = int(self.config["lives"])
        self.ghost = Ghost(row=1, col=1)
        self.is_running = True
        self.highscore_manager = HighscoreManager(str(self.config["highscore_filename"]))
        self.highscore_manager.load()

    def start(self) -> None:
        """Start the game loop."""
        while self.is_running:
            self.print_state()
            command = input("Move with WASD,  Q to quit: ")
            # input read from keybaord, return str

            if command == "q" or command == "Q":
                print("Quit game.")
                self.is_running = False
            else:
                self.handle_input(command)

            if self.player.lives <= 0:
                print("Game over.")
                self.is_running = False
        self.finish_game()

    def print_state(self) -> None:
        """Print current game state."""
        print("=== PAC-MAN ===")
        print(f"Score: {self.player.score}")
        print(f"Lives: {self.player.lives}")
        self.map_data.print_map(self.player.row, self.player.col,
                                self.ghost.row, self.ghost.col)

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

        gained_score = self.map_data.eat_tile(self.player.row, self.player.col)
        self.player.score += gained_score

        self.ghost.move_towards(self.player.row, self.player.col, self.map_data)
        self.check_collision()

        if not self.map_data.check_pacgum_left():
            print("You win!")
            self.is_running = False

    def check_collision(self) -> None:
        """Check if player and ghost are on the same tile."""
        if self.ghost.row != self.player.row:
            return

        if self.ghost.col != self.player.col:
            return

        self.player.lives -= 1
        print("Ghost caught you!")

        self.player.row = 2
        self.player.col = 2
        self.ghost.row = 1
        self.ghost.col = 1

    def finish_game(self) -> None:
        """Save final score."""
        print(f"Final score: {self.player.score}")
        name = input("Enter your name: ")
        self.highscore_manager.add_score(name, self.player.score)
        self.highscore_manager.print_highscores()
