import random


class Cell:
    __slots__ = ("walls", "visited", "is_pattern")
    def __init__(self) -> None:
        self.visited = False
        self.is_pattern = False
        self.walls = {"N": True, "E": True, "S": True, "W": True}


class MazeGenerator:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.grid: list[list[Cell]] = [
            [Cell() for _ in range(width)] for _ in range(height)
        ]
        self.blocked: set[tuple[int, int]] = set()

    def get_unvisited_neighbor(
        self, row: int, col: int
    ) -> list[tuple[str, int, int]]:
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

    def generate(self) -> None:
        self.pattern_forty_two()
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

            else:
                stack.pop()

    def pattern_forty_two(self) -> None:
        pattern = [
            "#....####",
            "#.......#",
            "#.......#",
            "####.####",
            "...#.#...",
            "...#.#...",
            "...#.####",
        ]
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
