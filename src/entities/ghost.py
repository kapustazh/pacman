"""Ghost entity for Pac-Man."""

from collections import deque
import random

from src.maze.map_data import MapData
from src.entities.player import Player


# Original Pac-Man direction priority used for tie-breaking.
# Priority: Up -> Left -> Down -> Right.
DIRECTION_ORDER = [
    (-1, 0),  # up
    (0, -1),  # left
    (1, 0),  # down
    (0, 1),  # right
]


class Ghost:
    """Represent a ghost."""

    def __init__(self, name: str, row: int, col: int) -> None:
        """Initialize ghost position."""
        self.name = name
        self.row = row
        self.col = col
        self.last_row = row
        self.last_col = col
        self.spawn_row = row
        self.spawn_col = col
        self.edible = False

        self.active = True
        self.respawn_turns = 0

    def find_path_bfs(
        self,
        start_row: int,
        start_col: int,
        target_row: int,
        target_col: int,
        map_data: MapData,
    ) -> list[tuple[int, int]]:
        """Find shortest path from ghost to target using BFS."""
        start = (start_row, start_col)
        target = (target_row, target_col)

        queue: deque[tuple[int, int]] = deque([start])
        came_from: dict[tuple[int, int],
                        tuple[int, int] | None] = {start: None}

        moves = [
            (0, 1),  # right
            (0, -1),  # left
            (-1, 0),  # up
            (1, 0),  # down
        ]

        while queue:
            current_row, current_col = queue.popleft()

            if (current_row, current_col) == target:
                break

            for row_delta, col_delta in moves:
                next_row = current_row + row_delta
                next_col = current_col + col_delta
                next_pos = (next_row, next_col)

                if next_pos in came_from:
                    continue

                if map_data.is_wall(next_row, next_col):
                    continue

                queue.append(next_pos)
                came_from[next_pos] = (current_row, current_col)

        if target not in came_from:
            return []

        path = []
        current: tuple[int, int] | None = target

        while current is not None:
            path.append(current)
            current = came_from[current]

        path.reverse()
        return path

    def move_towards(
            self,
            target_row: int,
            target_col: int,
            map_data: MapData
            ) -> None:
        """
        Move one step towards the target using original Pac-Man style logic.

        Normal ghosts do not compute a full shortest path. They keep moving
        straight in corridors and only choose a new direction at junctions.
        At a junction, each possible neighboring tile is compared by squared
        distance to the target, using a fixed tie-breaking order.
        """
        if not self.active:
            return

        next_pos = self._choose_pacman_step(target_row, target_col, map_data)
        if next_pos is None:
            self.move_random_allow_back(map_data)
            return

        self.last_row = self.row
        self.last_col = self.col
        self.row, self.col = next_pos

    def _current_direction(self) -> tuple[int, int] | None:
        """Return the current movement direction based on previous position."""
        row_delta = self.row - self.last_row
        col_delta = self.col - self.last_col
        if (row_delta, col_delta) in DIRECTION_ORDER:
            return (row_delta, col_delta)
        return None

    def _valid_directions(
        self,
        map_data: MapData,
        allow_reverse: bool = False,
    ) -> list[tuple[int, int]]:
        """Return valid directions in a fixed priority order."""
        current_direction = self._current_direction()
        reverse_direction = None
        if current_direction is not None:
            reverse_direction = (-current_direction[0], -current_direction[1])

        valid_directions = []
        for row_delta, col_delta in DIRECTION_ORDER:
            if (
                not allow_reverse
                and (row_delta, col_delta) == reverse_direction
            ):
                continue
            new_row = self.row + row_delta
            new_col = self.col + col_delta

            if not map_data.is_wall(new_row, new_col):
                valid_directions.append((row_delta, col_delta))
        return valid_directions

    def _is_junction(self, map_data: MapData) -> bool:
        """Return True if the ghost has multiple forward choices."""
        return len(self._valid_directions(map_data)) >= 2
        # Reverse is excluded, so:
        # 2 forward choices == 3 total directions in the original game.

    def _choose_pacman_step(
            self,
            target_row: int,
            target_col: int,
            map_data: MapData,
    ) -> tuple[int, int] | None:
        """
        Choose the next grid cell using the original Pac-Man
        junction-based movement algorithm.

        The ghost only evaluates neighbouring tiles at
        intersections instead of computing a global shortest
        path.
        """
        current_direction = self._current_direction()

        if current_direction is not None and not self._is_junction(map_data):
            next_row = self.row + current_direction[0]
            next_col = self.col + current_direction[1]

            if not map_data .is_wall(next_row, next_col):
                return next_row, next_col

        directions = self._valid_directions(map_data)
        if not directions:
            directions = self._valid_directions(map_data, allow_reverse=True)
        if not directions:
            return None

        best_direction: tuple[int, int] = directions[0]
        best_distance = float("inf")

        for row_delta, col_delta in directions:
            new_row = self.row + row_delta
            new_col = self.col + col_delta
            row_distance = new_row - target_row
            col_distance = new_col - target_col
            distance = (
                row_distance * row_distance
                + col_distance * col_distance
            )
            if distance < best_distance:
                best_distance = distance
                best_direction = (row_delta, col_delta)

        return self.row + best_direction[0], self.col + best_direction[1]

    def move_away(
            self,
            target_row: int,
            target_col: int,
            map_data: MapData
            ) -> None:
        """
        Move one step away from the player avoiding reverse BFS path chosen.
        """

        if not self.active:
            return

        avoid_pos: tuple[int, int] | None = None

        path = self.find_path_bfs(
            target_row, target_col, self.row, self.col, map_data)

        if len(path) >= 2:
            avoid_pos = path[-2]

        moves = DIRECTION_ORDER

        valid_moves: list[tuple[int, int]] = []
        back_pos = (self.last_row, self.last_col)

        for row_delta, col_delta in moves:
            new_row = self.row + row_delta
            new_col = self.col + col_delta
            new_pos = (new_row, new_col)
            if map_data.is_wall(new_row, new_col):
                continue
            if avoid_pos is not None and new_pos == avoid_pos:
                continue
            if new_pos == back_pos:
                continue
            valid_moves.append(new_pos)

        if not valid_moves:
            self.move_random_allow_back(map_data)
            return

        self.last_row = self.row
        self.last_col = self.col
        self.row, self.col = random.choice(valid_moves)

    def move_random_allow_back(self, map_data: MapData) -> None:
        """Move randomly to any valid corridor, including previous cell."""
        if not self.active:
            return

        moves = DIRECTION_ORDER

        valid_moves: list[tuple[int, int]] = []

        for row_delta, col_delta in moves:
            new_row = self.row + row_delta
            new_col = self.col + col_delta
            new_pos = (new_row, new_col)

            if not map_data.is_wall(new_row, new_col):
                valid_moves.append(new_pos)

        if valid_moves:
            self.last_row = self.row
            self.last_col = self.col
            self.row, self.col = random.choice(valid_moves)

    def move_random(self, map_data: MapData) -> None:
        """Move randomly to a valid corridor when no path to target is found"""
        if not self.active:
            return

        moves = DIRECTION_ORDER

        valid_moves: list[tuple[int, int]] = []
        back_pos = (self.last_row, self.last_col)

        for row_delta, col_delta in moves:
            new_row = self.row + row_delta
            new_col = self.col + col_delta
            new_pos = (new_row, new_col)
            if map_data.is_wall(new_row, new_col):
                continue
            if new_pos == back_pos:
                continue
            valid_moves.append(new_pos)

        if not valid_moves:
            self.move_random_allow_back(map_data)
            return

        self.last_row = self.row
        self.last_col = self.col
        self.row, self.col = random.choice(valid_moves)

    def start_respawn(self, delay_turns: int) -> None:
        """Temporarily remove ghost before respawning at its corner."""
        self.active = False
        self.edible = False
        self.respawn_turns = delay_turns
        self.row = self.spawn_row
        self.col = self.spawn_col
        self.last_row = self.spawn_row  # last round should also be spawn place
        self.last_col = self.spawn_col

    def tick_respawn(self) -> None:
        """Count down respawn turns and reactivate ghost when it reaches 0."""
        if self.active:
            return

        self.respawn_turns -= 1
        if self.respawn_turns <= 0:
            self.active = True
            self.respawn_turns = 0
            self.row = self.spawn_row
            self.col = self.spawn_col
            self.last_row = self.spawn_row
            self.last_col = self.spawn_col

    def reset_to_spawn(self) -> None:
        """Immediately reset ghost to its spawn position without delay."""
        self.row = self.spawn_row
        self.col = self.spawn_col
        self.last_row = self.spawn_row
        self.last_col = self.spawn_col
        self.edible = False
        self.active = True
        self.respawn_turns = 0

    def get_chase_target(
        self,
        player: Player,
        map_data: MapData,
    ) -> tuple[int, int]:
        """Return a different chase target based on ghost name."""
        if self.name == "Blinky":
            target = (player.row, player.col)
        elif self.name == "Pinky":
            target = (
                player.row + player.last_row_delta * 4,
                player.col + player.last_col_delta * 4,
            )
        elif self.name == "Inky":
            target = (
                player.row + player.last_row_delta * 2 + random.randint(-1, 1),
                player.col + player.last_col_delta * 2 + random.randint(-1, 1),
            )
        elif self.name == "Clyde":
            distance = self.manhattan_distance(
                self.row,
                self.col,
                player.row,
                player.col,
            )
            if distance > 8:
                target = (player.row, player.col)
            else:
                target = (self.spawn_row, self.spawn_col)
        else:
            target = (player.row, player.col)

        target_row, target_col = target

        if map_data.is_wall(target_row, target_col):
            return player.row, player.col

        return target

    def manhattan_distance(
        self,
        row1: int,
        col1: int,
        row2: int,
        col2: int,
    ) -> int:
        """Return Manhattan distance between two positions."""
        return abs(row1 - row2) + abs(col1 - col2)
