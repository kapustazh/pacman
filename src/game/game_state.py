"""Main game state management."""

from typing import Any

from src.maze.map_data import MapData
from src.maze.maze_adapter import MazeAdaptor
from src.entities.player import Player
from src.entities.ghost import Ghost
from src.game.level_builder import LevelBuilder
from src.game.level_manager import LevelManager
from src.managers.highscore_manager import HighscoreManager
from src.ui.terminal_renderer import TerminalRenderer


class GameState:
    """Represent the current game state."""

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize the game state."""
        self.config = config
        self.level_manager = LevelManager(config)

        self.is_running = True
        self.invincible = False
        self.freeze_ghost = False
        self.renderer = TerminalRenderer()

        self.highscore_manager = HighscoreManager(str(self.config["highscore_filename"]))
        self.highscore_manager.load()

        self.load_current_level(first_load=True)

    def load_current_level(self, first_load: bool) -> None:
        """Load current level."""
        level = self.level_manager.get_current_level()
        grid = MazeAdaptor().generate(
            width=int(level["width"]),
            height=int(level["height"]),
            seed=self.level_manager.get_seed(),
        )

        setup = LevelBuilder(int(self.config["pacgum"])).build(grid)
        self.map_data = MapData(grid)

        self.player_start = setup.player_start
        self.ghost_starts = setup.ghost_starts

        if first_load:
            row, col = self.player_start
            self.player = Player(row, col)
            self.player.lives = int(self.config["lives"])
        else:
            self.player.row, self.player.col = self.player_start

        names = ["Blinky", "Pinky", "Inky", "Clyde"]
        self.ghosts = [
            Ghost(names[index], row, col)
            for index, (row, col) in enumerate(setup.ghost_starts)
        ]

    def start(self) -> None:
        """Start the game loop."""
        while self.is_running:
            self.print_state()
            command = input("Move with WASD,  Q to quit: ").lower()
            # input read from keybaord, return str

            if command == "q" or command == "Q":
                print("Quit game.")
                self.is_running = False
            else:
                self.handle_input(command)

        print(f"Final score: {self.player.score}")
        name = input("Enter your name: ")
        self.highscore_manager.add_score(name, self.player.score)
        self.highscore_manager.print_highscores()

    def print_state(self) -> None:
        """Print current game state."""
        print("\033c", end="")  # reset the terminal
        print("=== PAC-MAN ===")
        print(f"Score: {self.player.score}")
        print(f"Lives: {self.player.lives}")
        print(f"Level: {self.level_manager.current_level + 1}")
        self.renderer.print_map(
            self.map_data,
            self.player.row,
            self.player.col,
            self.ghosts
        )

    def handle_input(self, command: str) -> None:
        """Handle keyboard input."""
        if command == "i":
            self.invincible = not self.invincible
            return
        if command == "f":
            self.freeze_ghost = not self.freeze_ghost
            return
        if command == "l":
            self.player.lives += 1
            return
        if command == "n":
            self.complete_level()
            return

        moves = {
            "w": (-1, 0),
            "s": (1, 0),
            "a": (0, -1),
            "d": (0, 1),
        }

        if command not in moves:
            print("Unknown command.")
            return

        row_delta, col_delta = moves[command]
        self.try_move_player(row_delta, col_delta)

    def try_move_player(self, row_delta: int, col_delta: int) -> None:
        """Move player if target is not wall."""
        new_row = self.player.row + row_delta
        new_col = self.player.col + col_delta

        if self.map_data.is_wall(new_row, new_col):
            print("You hit a wall")
            return

        self.player.move(row_delta, col_delta)

        self.player.score += self.map_data.eat_tile(
            self.player.row,
            self.player.col,
        )

        if not self.freeze_ghost:
            for ghost in self.ghosts:
                ghost.move_towards(
                    self.player.row,
                    self.player.col,
                    self.map_data
                )

        for index, ghost in enumerate(self.ghosts):
            if ghost.row == self.player.row and ghost.col == self.player.col:
                if not self.invincible:
                    self.player.lives -= 1
                    print("Ghost caught you!")
                    self.player.row, self.player.col = self.player_start
                    ghost.row, ghost.col = self.ghost_starts[index]

        if self.player.lives <= 0:
            print("Game over.")
            self.is_running = False
            return
    
        if not self.map_data.check_pacgum_left():
            self.complete_level()

    def complete_level(self) -> None:
        """Finish current level or win the game."""
        if not self.level_manager.has_next_level():
            print("You win the game!")
            self.is_running = False
            return 

        self.level_manager.go_next_level()
        self.load_current_level(first_load=False)
