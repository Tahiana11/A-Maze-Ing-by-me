import random
from typing import Generator
from .generator import MazeGenerator


class ImperfectMazeGenerator(MazeGenerator):
    """Generates an "imperfect" maze that may contain loops and rooms.

    Builds on top of :class:`MazeGenerator` by first carving a perfect
    maze via DFS, then randomly removing additional walls to create
    loops, and optionally carving a number of 2x2 open rooms.

    Attributes:
        walls (float): Fraction (between 0.0 and 1.0) of removable
            walls that will be knocked down after the perfect maze has
            been generated, creating loops.
        rooms_2x2 (int): Number of 2x2 open rooms to carve into the
            maze.
    """

    def __init__(
        self,
        width: int,
        height: int,
        entry: tuple[int, int],
        _exit: tuple[int, int],
        walls: float = 0.05,
        rooms_2x2: int = 3,
        seed: int | None = None,
    ) -> None:
        """Initialize the imperfect maze generator.

        Args:
            width: Number of columns in the grid.
            height: Number of rows in the grid.
            entry: Entry point of the maze as ``(row, col)``.
            _exit: Exit point of the maze as ``(row, col)``.
            walls: Fraction of removable walls (0.0 to 1.0) to knock
                down after DFS generation in order to create loops.
            rooms_2x2: Number of 2x2 open rooms to carve into the maze.
            seed: Optional seed forwarded to the base
                :class:`MazeGenerator` to make generation reproducible.

        Raises:
            ValueError: If ``walls`` is not between 0.0 and 1.0, or if
                ``rooms_2x2`` is negative.
        """
        super().__init__(width, height, entry, _exit, seed=seed)
        if not 0.0 <= walls <= 1.0:
            raise ValueError("the walls must be between 0 and 1")
        if rooms_2x2 < 0:
            raise ValueError("rooms_2x2 must be positive or equal to zero")
        self.walls = walls
        self.rooms_2x2 = rooms_2x2

    def _removable_walls(self) -> list[tuple[int, int, str, int, int]]:
        """Find walls that can be removed to introduce loops.

        Scans the grid (skipping blocked cells) and collects the
        northern and eastern walls that still stand between two
        unblocked, in-bounds cells.

        Returns:
            A list of tuples ``(row, col, direction, neighbor_row,
            neighbor_col)`` describing each removable wall.
        """
        directions = [("N", -1, 0), ("E", 0, 1)]
        removable: list[tuple[int, int, str, int, int]] = []

        for row in range(self.height):
            for col in range(self.width):
                if (row, col) in self.blocked:
                    continue
                cell = self.grid[row][col]
                for direction, d_row, d_col in directions:
                    nr, nc = row + d_row, col + d_col
                    if not (0 <= nr < self.height and 0 <= nc < self.width):
                        continue
                    if (nr, nc) in self.blocked:
                        continue
                    if cell.walls[direction]:
                        removable.append((row, col, direction, nr, nc))

        return removable

    def _room_candidates(self) -> list[tuple[int, int]]:
        """Find top-left coordinates of valid 2x2 room locations.

        A location is a valid candidate if all four cells of the
        corresponding 2x2 block are within the grid and none of them
        is blocked.

        Returns:
            A list of ``(row, col)`` tuples, each being the top-left
            corner of a valid 2x2 block of cells.
        """
        candidates: list[tuple[int, int]] = []

        for row in range(self.height - 1):
            for col in range(self.width - 1):
                cells = (
                    (row, col),
                    (row, col + 1),
                    (row + 1, col),
                    (row + 1, col + 1),
                )
                if any(cell in self.blocked for cell in cells):
                    continue
                candidates.append((row, col))

        return candidates

    def _carve_room(
        self, row: int, col: int
    ) -> Generator[tuple[int, int, int, int], None, None]:
        """Remove the internal walls of a 2x2 block to form an open room.

        Args:
            row: Row index of the top-left cell of the 2x2 block.
            col: Column index of the top-left cell of the 2x2 block.

        Yields:
            Tuples ``(row, col, neighbor_row, neighbor_col)`` for each
            internal wall that was actually removed, useful for
            step-by-step animation.
        """
        opposite = {"N": "S", "S": "N", "E": "W", "W": "E"}
        internal_walls = (
            (row, col, "E", row, col + 1),
            (row, col, "S", row + 1, col),
            (row, col + 1, "S", row + 1, col + 1),
            (row + 1, col, "E", row + 1, col + 1),
        )

        for r, c, direction, nr, nc in internal_walls:
            current_cell = self.grid[r][c]
            neighbor_cell = self.grid[nr][nc]
            if current_cell.walls[direction]:
                current_cell.walls[direction] = False
                neighbor_cell.walls[opposite[direction]] = False
                yield (r, c, nr, nc)

    def generate_imperfect(
        self
    ) -> Generator[tuple[int, int, int, int], None, None]:
        """Generate an imperfect maze with loops and open rooms.

        First delegates to :meth:`MazeGenerator.generate_dfs` to build
        a perfect maze, then randomly removes a fraction (``self.walls``)
        of the removable walls to create loops, and finally carves
        ``self.rooms_2x2`` open 2x2 rooms at random locations.

        Yields:
            Tuples ``(row, col, neighbor_row, neighbor_col)`` describing
            every wall removal performed during the whole process
            (DFS carving, loop creation, and room carving), useful for
            step-by-step animation.
        """
        yield from self.generate_dfs()

        opposite = {"N": "S", "S": "N", "E": "W", "W": "E"}
        removable = self._removable_walls()
        random.shuffle(removable)

        nb_extra = int(len(removable) * self.walls)
        for row, col, direction, nr, nc in removable[:nb_extra]:
            current_cell = self.grid[row][col]
            neighbor_cell = self.grid[nr][nc]
            current_cell.walls[direction] = False
            neighbor_cell.walls[opposite[direction]] = False
            yield (row, col, nr, nc)

        room_candidates = self._room_candidates()
        random.shuffle(room_candidates)

        nb_rooms = min(self.rooms_2x2, len(room_candidates))
        for row, col in room_candidates[:nb_rooms]:
            yield from self._carve_room(row, col)
