from collections import deque
from typing import Optional, Dict, List, Tuple
from .generator import MazeGenerator


class MazeSolver:
    """Solves a maze by finding the shortest path from entry to exit.

    Attributes:
        maze (MazeGenerator): The maze instance to solve, providing the
            grid, entry point, and exit point.
    """

    def __init__(self, maze: MazeGenerator) -> None:
        """Initialize the solver with the maze to solve.

        Args:
            maze: The maze instance to solve.
        """
        self.maze = maze

    def solve_bfs(self) -> List[Tuple[int, int]]:
        """Find the shortest path from the maze entry to its exit.

        Performs a breadth-first search over the grid, moving between
        cells only where no wall blocks the way.

        Returns:
            An ordered list of ``(row, col)`` coordinates forming the
            shortest path from the entry to the exit, inclusive. Returns
            an empty list if no path exists.
        """
        directions = [("N", -1, 0), ("S", 1, 0), ("E", 0, 1), ("W", 0, -1)]
        start = self.maze.entry
        goal = self.maze.exit
        queue = deque([start])
        came_from: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {
            start: None}

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
                    0 <= nr < self.maze.height and
                    0 <= nc < self.maze.width
                ):
                    continue

                if (nr, nc) in came_from:
                    continue

                came_from[(nr, nc)] = (row, col)
                queue.append((nr, nc))

        return []

    @staticmethod
    def _reconstruct_path(
        came_from: Dict[Tuple[int, int], Optional[Tuple[int, int]]],
        goal: Tuple[int, int],
    ) -> List[Tuple[int, int]]:
        """Rebuild the path from the entry to the goal.

        Walks backward from ``goal`` through the ``came_from`` mapping
        produced during the breadth-first search, then reverses the
        result to obtain the path in entry-to-exit order.

        Args:
            came_from: Mapping of each visited cell to the cell it was
                reached from. The starting cell must map to ``None``.
            goal: The target cell, i.e. the maze exit.

        Returns:
            An ordered list of ``(row, col)`` coordinates forming the
            path from the entry to ``goal``, inclusive.
        """
        path = [goal]
        current = came_from[path[-1]]
        while current is not None:
            path.append(current)
            current = came_from[current]

        path.reverse()
        return path
