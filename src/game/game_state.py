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
    GHOST_RESPAWN_DELAY = 10
    EDIBLE_DURATION = 1000

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize the game state."""
        self.config = config
        self.level_manager = LevelManager(config)

        self.is_running = True
        self.invincible = False
        self.freeze_ghost = False
        self.edible_turns = 0
        self.remaining_time = int(self.config["level_max_time"])

        self.scatter_mode = False
        self.scatter_turns = 0

        self.renderer = TerminalRenderer()

        self.highscore_manager = HighscoreManager(
            str(self.config["highscore_filename"])
            )
        self.highscore_manager.load()

        self.load_current_level(first_load=True)

    def load_current_level(self, first_load: bool) -> None:
        """Load current level."""
        self.remaining_time = int(self.config["level_max_time"])
        self.edible_turns = 0

        self.scatter_mode = False
        self.scatter_turns = 0

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
            command = input(
                "WASD move | P pause | I invincible | F freeze | "
                "L life | N next level | Q quit: "
            ).lower()
            # input read from keybaord, return str

            if command == "q":
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
        print(f"Edible turns: {self.edible_turns}")
        print(f"Time left: {self.remaining_time}")
        print(
            "Mode:",
            "Scatter" if self.scatter_mode else "Chase",
        )
        self.renderer.print_map(
            self.map_data,
            self.player.row,
            self.player.col,
            self.ghosts
        )

    def handle_input(self, command: str) -> None:
        """Handle keyboard input."""
        if command == "p":
            self.pause_game()
            return
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

        # speed is in lack

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

    def pause_game(self) -> None:
        """Pause the game until the player resumes or quits."""
        while self.is_running:
            command = input("Paused. Press R to resume or Q to quit:").lower()
            if command == "r":
                return
            if command == "q":
                self.is_running = False
                return
            print("Unknown pause command.")

    def try_move_player(self, row_delta: int, col_delta: int) -> None:
        """Move player if target is not wall."""
        new_row = self.player.row + row_delta
        new_col = self.player.col + col_delta

        if self.map_data.is_wall(new_row, new_col):
            print("You hit a wall")
            return

        self.player.move(row_delta, col_delta)
        self.remaining_time -= 1

        if self._handle_time_limit():
            return

        self._handle_tile_eating()

        self._handle_ghost_collisions()
        if not self.is_running:
            return  # h_g_c => lives <=0 => is_run false

        self._move_ghosts()
        self._handle_ghost_collisions()
        if not self.is_running:
            return

        self._update_timer()

        if not self.map_data.check_pacgum_left():
            self.complete_level()

    def _handle_tile_eating(self) -> None:
        """Eat current tile and apply score or frightened mode effects."""
        gained_score = self.map_data.eat_tile(
            self.player.row,
            self.player.col,
            int(self.config["points_per_pacgum"]),
            int(self.config["points_per_super_pacgum"]),
        )
        if gained_score == int(self.config["points_per_super_pacgum"]):
            self.edible_turns = self.EDIBLE_DURATION

            for ghost in self.ghosts:
                ghost.edible = True

        self.player.score += gained_score

    def _move_ghosts(self) -> None:
        """Move ghosts according to current mode."""
        if self.freeze_ghost:
            return

        for ghost in self.ghosts:
            if not ghost.active:
                continue

            if self.edible_turns > 0:
                ghost.move_away(
                    self.player.row,
                    self.player.col,
                    self.map_data,
                )
                continue

            if self.scatter_mode:
                target_row = ghost.spawn_row
                target_col = ghost.spawn_col

            else:
                target_row, target_col = (
                    ghost.get_chase_target(
                        self.player,
                        self.map_data,
                    )
                )

            ghost.move_towards(
                target_row,
                target_col,
                self.map_data,
            )

    def _update_timer(self) -> None:
        """Update edible and ghost respawn timers after one turn."""
        for ghost in self.ghosts:
            ghost.tick_respawn()

        if self.edible_turns > 0:
            self.edible_turns -= 1
            if self.edible_turns == 0:
                for ghost in self.ghosts:
                    ghost.edible = False

        self.scatter_turns += 1
        if self.scatter_turns >= 40:
            self.scatter_turns = 0
            self.scatter_mode = False
        elif self.scatter_turns >= 20:
            self.scatter_mode = True

    def _handle_time_limit(self) -> bool:
        """Handle level timeout. Return True if level ended."""
        if self.remaining_time > 0:
            return False

        print("Time is up!")
        self.player.lives -= 1

        if self.player.lives <= 0:
            print("Game over!")
            self.is_running = False
            return True

        self.load_current_level(first_load=False)
        return True

    def _handle_ghost_collisions(self) -> None:
        """Handle collisions between player and ghosts."""
        for index, ghost in enumerate(self.ghosts):
            if not ghost.active:
                continue

            if ghost.row != self.player.row or ghost.col != self.player.col:
                continue

            if ghost.edible:
                self.player.score += int(self.config["points_per_ghost"])
                print(f"You eat {ghost.name}!")
                ghost.start_respawn(self.GHOST_RESPAWN_DELAY)
                continue

            if not self.invincible:
                self.player.lives -= 1
                print("Ghost caught you!")

                self.player.row, self.player.col = self.player_start

                for current_ghost in self.ghosts:
                    current_ghost.reset_to_spawn()

                if self.player.lives <= 0:
                    print("Game over!")
                    self.is_running = False
                    return

                return

    def complete_level(self) -> None:
        """Finish current level or win the game."""
        if not self.level_manager.has_next_level():
            print("You win the game!")
            self.is_running = False
            return

        self.level_manager.go_next_level()
        self.load_current_level(first_load=False)
