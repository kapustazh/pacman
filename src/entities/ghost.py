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
        target_row: int,
        target_col: int,
        map_data: MapData,
    ) -> list[tuple[int, int]]:
        """Find shortest path from ghost to target using BFS."""
        start = (self.row, self.col)
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
        Move one step towards the target without crossing walls
        using BFS shortest path.
        """
        path = self.find_path_bfs(target_row, target_col, map_data)
        if len(path) >= 2:
            self.row, self.col = path[1]

    def move_away(
            self,
            target_row: int,
            target_col: int,
            map_data: MapData
            ) -> None:
        """
        Move one step away from the target without crossing walls.
        -check 4 directions
        -ignore walls
        -choose biggest Manhattan distance
        -if no better move exists, choose any valid move
        """
        moves = [
            (0, 1),  # right
            (0, -1),  # left
            (-1, 0),  # up
            (1, 0),  # down
        ]

        best_row = self.row
        best_col = self.col
        valid_moves: list[tuple[int, int]] = []

        best_distance = (
            abs(self.row - target_row)
            + abs(self.col - target_col)
        )

        for row_delta, col_delta in moves:
            new_row = self.row + row_delta
            new_col = self.col + col_delta

            if map_data.is_wall(new_row, new_col):
                continue

            valid_moves.append((new_row, new_col))

            distance = (
                abs(new_row - target_row)
                + abs(new_col - target_col)
            )

            if distance > best_distance:
                best_distance = distance
                best_row = new_row
                best_col = new_col

        if valid_moves and best_row == self.row and best_col == self.col:
            best_row, best_col = random.choice(valid_moves)

        self.row = best_row
        self.col = best_col

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

 