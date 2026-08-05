from typing import Generator
import random


class Cell:
    """Represents a single cell of the maze grid.

    Attributes:
        walls (dict[str, bool]): Presence of a wall in each of the four
            cardinal directions (``"N"``, ``"E"``, ``"S"``, ``"W"``).
            ``True`` means the wall is present, ``False`` means it has
            been carved away.
        visited (bool): Whether the cell has already been visited by
            the generation algorithm.
        is_pattern (bool): Whether the cell belongs to the decorative
            "42" pattern carved into the grid.
    """

    __slots__ = ("walls", "visited", "is_pattern")

    def __init__(self) -> None:
        """Initialize a new cell with all four walls standing."""
        self.visited = False
        self.is_pattern = False
        self.walls = {"N": True, "E": True, "S": True, "W": True}


class MazeGenerator:
    """Generates a perfect maze (no loops) using a depth-first search.

    Attributes:
        width (int): Number of columns in the grid.
        height (int): Number of rows in the grid.
        grid (list[list[Cell]]): Two-dimensional grid of `Cell` objects.
        entry (tuple[int, int]): Entry point of the maze as ``(row, col)``.
        exit (tuple[int, int]): Exit point of the maze as ``(row, col)``.
        blocked (set[tuple[int, int]]): Set of ``(row, col)`` coordinates
            that are blocked (e.g. by the decorative pattern) and cannot
            be visited by the generation algorithm.
        seed (int | None): Optional seed used to make maze generation
            reproducible.
    """

    def __init__(
        self,
        width: int,
        height: int,
        entry: tuple[int, int],
        exit: tuple[int, int],
        perfect: bool = True,
        seed: int | None = None,
    ) -> None:
        """Initialize the maze grid and its generation parameters.

        Args:
            width: Number of columns in the grid.
            height: Number of rows in the grid.
            entry: Entry point of the maze as ``(row, col)``.
            exit: Exit point of the maze as ``(row, col)``.
            perfect: Whether the maze should be "perfect" (no loops).
                Kept for compatibility with subclasses; not used
                directly by this class beyond being stored implicitly
                through the subclass behavior.
            seed: Optional seed forwarded to :func:`random.seed` to make
                the generation reproducible. If ``None``, the global
                random state is left untouched.
        """
        self.width = width
        self.height = height
        self.grid: list[list[Cell]] = [
            [Cell() for _ in range(width)] for _ in range(height)
        ]
        self.entry = entry
        self.exit = exit
        self.blocked: set[tuple[int, int]] = set()
        self.seed = seed
        if seed is not None:
            random.seed(seed)

    def get_unvisited_neighbor(
        self, row: int, col: int
    ) -> list[tuple[str, int, int]]:
        """List the unvisited neighbors of a given cell.

        Args:
            row: Row index of the reference cell.
            col: Column index of the reference cell.

        Returns:
            A list of tuples ``(direction, neighbor_row, neighbor_col)``
            for each in-bounds neighbor that has not yet been visited,
            where ``direction`` is one of ``"N"``, ``"S"``, ``"W"``,
            ``"E"`` indicating the direction from the reference cell to
            the neighbor.
        """
        neighbors = []
        directions = [
            ("N", -1, 0),
            ("S", 1, 0),
            ("W", 0, -1),
            ("E", 0, 1),
        ]

        for direction, d_row, d_col in directions:
            nr = row + d_row
            nc = col + d_col

            if 0 <= nr < self.height and 0 <= nc < self.width:
                neighbor = self.grid[nr][nc]
                if not neighbor.visited:
                    neighbors.append((direction, nr, nc))

        return neighbors

    def valid_position(self, pos: tuple[int, int]) -> bool:
        """Check whether a position is in-bounds and blocked.
            Despite its name, this method returns ``True`` only when
            the position lies within the grid **and** is present in
            ``self.blocked``. It is used to reject an entry/exit point
            that falls on a blocked cell.

        Args:
            pos: Position to check as ``(row, col)``.

        Returns:
            ``True`` if the position is within the grid bounds and is
            part of ``self.blocked``, ``False`` otherwise.
        """
        row, col = pos
        return (
            0 <= row < self.height and
            0 <= col < self.width and
            pos in self.blocked
        )

    def generate_dfs(self) -> Generator[tuple[int, int, int, int], None, None]:
        """Generate a perfect maze using iterative depth-first search.

        Carves the decorative "42" pattern first, then performs a
        randomized DFS from a random unblocked starting cell, removing
        walls between the current cell and a randomly chosen unvisited
        neighbor at each step.

        Yields:
            Tuples ``(row, col, neighbor_row, neighbor_col)`` describing
            each wall removal performed during generation, useful for
            step-by-step animation.

        Raises:
            ValueError: If the configured entry or exit position lies
                on a blocked cell.
        """
        self.pattern_forty_two()
        if self.valid_position(self.entry):
            raise ValueError("Invalid entry...")
        if self.valid_position(self.exit):
            raise ValueError("Invalid exit...")
        while True:
            row_current = random.randint(0, self.height - 1)
            col_current = random.randint(0, self.width - 1)
            if (row_current, col_current) not in self.blocked:
                break

        random_cell = self.grid[row_current][col_current]
        random_cell.visited = True

        stack = []
        stack.append((row_current, col_current))

        while stack:
            row, col = stack[-1]
            neighbors = self.get_unvisited_neighbor(row, col)
            if neighbors:
                direction, r_neighbor, c_neighbor = random.choice(neighbors)
                current_cell = self.grid[row][col]
                cell_neighbor = self.grid[r_neighbor][c_neighbor]
                opposite = {"N": "S", "S": "N", "E": "W", "W": "E"}
                current_cell.walls[direction] = False
                cell_neighbor.walls[opposite[direction]] = False

                cell_neighbor.visited = True
                stack.append((r_neighbor, c_neighbor))
                yield (row, col, r_neighbor, c_neighbor)

            else:
                stack.pop()

    def pattern_forty_two(self) -> None:
        """ '42' digit pattern into the grid.

        Marks the cells forming the pattern as visited, tags them with
        ``is_pattern = True`` and adds their coordinates to
        ``self.blocked`` so the maze generation algorithm treats them
        as unavailable. If the grid is too small to fit the pattern,
        a message is printed and the method returns without modifying
        the grid.

        Returns:
            None
        """
        digit_4 = [
            "#...",
            "#...",
            "#...",
            "####",
            "...#",
            "...#",
            "...#",
        ]
        digit_2 = [
            "####",
            "...#",
            "...#",
            "####",
            "#...",
            "#...",
            "####",
        ]

        gap = "." * (2 if self.width % 2 == 0 else 1)
        pattern = [row4 + gap + row2 for row4, row2 in zip(digit_4, digit_2)]

        pattern_h = len(pattern)
        pattern_w = len(pattern[0])
        if self.height < pattern_h or self.width < pattern_w:
            print("Grid too small to display pattern '42'")
            return

        start_row = (self.height - pattern_h) // 2
        start_col = (self.width - pattern_w) // 2

        for row, line in enumerate(pattern):
            for col, char in enumerate(line):
                if char == "#":
                    gr, gc = start_row + row, start_col + col
                    self.grid[gr][gc].visited = True
                    self.grid[gr][gc].is_pattern = True
                    self.blocked.add((gr, gc))
