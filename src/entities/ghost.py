"""Ghost entity for Pac-Man."""

from collections import deque
import random

from src.maze.map_data import MapData


class Ghost:
    """Represent a ghost."""

    def __init__(self, name: str, row: int, col: int) -> None:
        """Initialize ghost position."""
        self.name = name
        self.row = row
        self.col = col
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
        Move one step towards the target using BFS shortest path.
        """
        if not self.active:
            return
        
        chase_row, chase_col = self.get_chase_target(
            target_row, target_col, map_data
        )
        path = self.find_path_bfs(
            self.row, self.col, chase_row, chase_col, map_data)
        if len(path) >= 2:
            self.row, self.col = path[1]
            return
        self.move_away(target_row, target_col, map_data)

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
        path = self.find_path_bfs(
            target_row, target_col, self.row, self.col, map_data)
        if len(path) >= 2:
            avoid_pos = path[-2]

        moves = [
            (0, 1),  # right
            (0, -1),  # left
            (-1, 0),  # up
            (1, 0),  # down
        ]

        valid_moves: list[tuple[int, int]] = []
        for row_delta, col_delta in moves:
            new_row = self.row + row_delta
            new_col = self.col + col_delta
            new_pos = (new_row, new_col)
            if map_data.is_wall(new_row, new_col):
                continue
            if avoid_pos is not None and new_pos == avoid_pos:
                continue
            valid_moves.append(new_pos)

        if valid_moves:
            self.row, self.col = random.choice(valid_moves)

    def start_repawn(self, delay_turns: int) -> None:
        """Temporarily remove ghost before respawning at its corner."""
        self.active = False
        self.edible = False
        self.respawn_turns = delay_turns
        self.row = self.spawn_row
        self.col = self.spawn_col

    def tick_respawn(self) -> None:
        """"Count down respawn turns and reactivate ghost when it reaches 0."""
        if self.active:
            return

        self.respawn_turns -= 1
        if self.respawn_turns <= 0:
            self.active = True
            self.respawn_turns = 0
            self.row = self.spawn_row
            self.col = self.spawn_col

    def reset_to_spawn(self) -> None:
        """"Immediately reset ghost to its spawn position without delay."""
        self.row = self.spawn_row
        self.col = self.spawn_col
        self.edible = False
        self.active = True
        self.respawn_turns = 0

    def get_chase_target(
        self,
        player_row: int,
        player_col: int,
        map_data: MapData,
    ) -> tuple[int, int]:
        """Return a different chase target based on ghost name."""
        if self.name == "Blinky":
            target = (player_row, player_col)
        elif self.name == "Pinky":
            target = (player_row - 2, player_col)
        elif self.name == "Inky":
            target = (player_row, player_col - 2)
        elif self.name == "Clyde":
            target = (player_row, player_col + 2)
        else:
            target = (player_row, player_col)

        target_row, target_col = target

        if map_data.is_wall(target_row, target_col):
            return player_row, player_col

        return target
