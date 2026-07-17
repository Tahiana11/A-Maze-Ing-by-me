import random


class Cell:
    __slots__ = ("walls", "visited")
    def __init__(self) -> None:
        self.visited = False
        self.walls = {"N": True, "E": True, "S": True, "W": True}


class MazeGenerator:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.grid: list[list[Cell]] = [
            [Cell() for _ in range(width)] for _ in range(height)
        ]

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
        row_current = random.randint(0, self.height - 1)
        col_current = random.randint(0, self.width - 1)
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
        pass
