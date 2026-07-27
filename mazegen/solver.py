from collections import deque
from .generator import MazeGenerator


class MazeSolver:
    def __init__(self, maze: MazeGenerator) -> None:
        self.maze = maze

    def solve_bfs(self) -> list[tuple[int, int]]:
        """retourne le chemin le plus court entry -> exit
        renvoie une liste vide si aucun chemin n'exit
        """
        directions = [
            ("N", -1, 0),
            ("S", 1, 0),
            ("E", 0, 1),
            ("W", 0, -1)
        ]
        start = self.maze.entry
        goal = self.maze.exit
        queue = deque([start])
        came_from: dict[
            tuple[int, int], tuple[int, int] | None
        ] = {start: None}

        while queue:
            row, col = queue.popleft()
            if (row, col) == goal:
                return self._reconstruct_path(came_from, goal)
            current_cell = self.maze.grid[row][col]
            for direction, d_row, d_col in directions:
                if current_cell.walls[direction]:
                    continue

                nr, nc = d_row + row, d_col + col
                if not (
                    0 <= nr < self.maze.height and 0 <= nc < self.maze.width
                ):
                    continue

                if (nr, nc) in came_from:
                    continue

                came_from[(nr, nc)] = (row, col)
                queue.append((nr, nc))

        return []

    @staticmethod
    def _reconstruct_path(
        came_from: dict[tuple[int, int], tuple[int, int] | None],
        goal: tuple[int, int]
    ) -> list[tuple[int, int]]:
        path = [goal]
        while came_from[path[-1]] is not None:
            path.append(came_from[path[-1]])
        path.reverse()
        return path
