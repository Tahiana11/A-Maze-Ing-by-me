import random
from typing import Generator

from .generator import MazeGenerator


class ImperfectMazeGenerator(MazeGenerator):
    def __init__(
        self,
        width: int,
        height: int,
        entry: tuple[int, int],
        exit: tuple[int, int],
        walls: float = 0.05,
        rooms_2x2: int = 3,
    ) -> None:
        super().__init__(width, height, entry, exit, perfect=False)
        if not 0.0 <= walls <= 1.0:
            raise ValueError("the walls must be between 0 and 1")
        if rooms_2x2 < 0:
            raise ValueError("rooms_2x2 must be positive or equal to zero")
        self.walls = walls
        self.rooms_2x2 = rooms_2x2

    def _removable_walls(self) -> list[tuple[int, int, str, int, int]]:
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

    def _carve_2x2_room(
        self, row: int, col: int
    ) -> Generator[tuple[int, int, int, int], None, None]:
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
            yield from self._carve_2x2_room(row, col)
