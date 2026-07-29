from pathlib import Path
from mazegen.generator import Cell, MazeGenerator

WALL_BITS: dict[str, int] = {"N": 1, "E": 2, "S": 4, "W": 8}

_DIRECTION: dict[tuple[int, int], str] = {
    (-1, 0): "N",
    (1, 0): "S",
    (0, 1): "E",
    (0, -1): "O",
}


def cell_to_hex(cell: Cell) -> str:
    value = 0
    for direction, bit in WALL_BITS.items():
        if cell.walls[direction]:
            value |= bit
    return format(value, "x").upper()


def code_grid(grid: list[list[Cell]]) -> list[str]:
    return ["".join(cell_to_hex(cell) for cell in row) for row in grid]


def path_to_directions(path: list[tuple[int, int]]) -> str:
    directions = []
    for (row_a, col_a), (row_b, col_b) in zip(path, path[1:]):
        delta = (row_b - row_a, col_b - col_a)
        direction = _DIRECTION.get(delta)
        if direction is None:
            raise ValueError(
                f"Invalid move between {(row_a, col_a)} "
                f"and {(row_b, col_b)}"
            )
        directions.append(direction)
    return "".join(directions)


class MazeWriter:
    def __init__(
        self,
        maze: MazeGenerator,
        path: list[tuple[int, int]] | None = None
    ) -> None:
        self.maze = maze
        self.path = path or []

    def to_lines(self) -> list[str]:
        lines = []
        lines.extend(code_grid(self.maze.grid))

        entry_row, entry_col = self.maze.entry
        exit_row, exit_col = self.maze.exit
        lines.append(f"\n{entry_row},{entry_col}")
        lines.append(f"{exit_row},{exit_col}")

        if self.path:
            lines.append(f"{path_to_directions(self.path)}")
        else:
            lines.append("DIRECTIONS")

        return lines

    def write(self, output_file: str) -> None:
        content = "\n".join(self.to_lines()) + "\n"
        Path(output_file).write_text(content)


def write_maze(
    maze: MazeGenerator,
    output_file: str,
    path: list[tuple[int, int]] | None = None
) -> None:
    MazeWriter(maze, path).write(output_file)
