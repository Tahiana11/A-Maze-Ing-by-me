from pathlib import Path
from mazegen.generator import Cell, MazeGenerator

WALL_BITS: dict[str, int] = {"N": 1, "E": 2, "S": 4, "W": 8}

_DIRECTION: dict[tuple[int, int], str] = {
    (-1, 0): "N",
    (1, 0): "S",
    (0, 1): "E",
    (0, -1): "W",
}


def cell_to_hex(cell: Cell) -> str:
    """Encode a cell's walls as a single hexadecimal digit.

    Each wall direction contributes a bit (``N=1``, ``E=2``, ``S=4``,
    ``W=8``) that is set when the corresponding wall is present.

    Args:
        cell: The cell whose walls should be encoded.

    Returns:
        A single uppercase hexadecimal character representing the
        combined wall bitmask.
    """
    value = 0
    for direction, bit in WALL_BITS.items():
        if cell.walls[direction]:
            value |= bit
    return format(value, "x").upper()


def code_grid(grid: list[list[Cell]]) -> list[str]:
    """Encode a full maze grid as a list of hexadecimal strings.

    Args:
        grid: Two-dimensional grid of `Cell` objects.

    Returns:
        A list where each element is a string of hexadecimal digits
        (one per cell, produced by :func:`cell_to_hex`) representing a
        row of the grid.
    """
    return ["".join(cell_to_hex(cell) for cell in row) for row in grid]


def path_to_directions(path: list[tuple[int, int]]) -> str:
    """Convert a list of grid coordinates into a string of moves.

    Args:
        path: Ordered list of ``(row, col)`` coordinates describing a
            path through the maze, from entry to exit.

    Returns:
        A string where each character represents the direction
        (``"N"``, ``"S"``, ``"E"``, or ``"O"`` for west) taken to move
        from one coordinate in ``path`` to the next.

    Raises:
        ValueError: If two consecutive coordinates in ``path`` are not
            adjacent in one of the four cardinal directions.
    """
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
    """Serializes a generated maze (and optionally its solution) to a file.

    Attributes:
        maze (MazeGenerator): The maze to serialize.
        path (list[tuple[int, int]]): The solved path to serialize,
            empty if no path is provided.
    """

    def __init__(
        self, maze: MazeGenerator, path: list[tuple[int, int]] | None = None
    ) -> None:
        """Initialize the writer with a maze and an optional path.

        Args:
            maze: The maze to serialize.
            path: Ordered list of ``(row, col)`` coordinates describing
                the solved path from entry to exit. If ``None``, an
                empty path is used and the ``"DIRECTIONS"`` placeholder
                is written instead of actual directions.
        """
        self.maze = maze
        self.path = path or []

    def to_lines(self) -> list[str]:
        """Build the textual representation of the maze as a list of lines.

        The output contains, in order: the hex-encoded grid rows, a
        blank line, the entry coordinates, the exit coordinates, and
        either the directions of the solved path or the
        ``"DIRECTIONS"`` placeholder if no path was provided.

        Returns:
            The list of lines making up the serialized maze file
            content.
        """
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
        """Write the serialized maze content to a file.

        Any exception raised while writing (e.g. an invalid path or a
        permission error) is silently swallowed and the method simply
        returns without writing the file.

        Args:
            output_file: Path of the file to write the maze content to.

        Returns:
            None
        """
        try:
            content = "\n".join(self.to_lines()) + "\n"
            Path(output_file).write_text(content)
        except Exception:
            return


def write_maze(
    maze: MazeGenerator,
    output_file: str,
    path: list[tuple[int, int]] | None = None
) -> None:
    """Serialize and write a maze to a file in a single call.

    Convenience wrapper around :class:`MazeWriter` for callers that do
    not need to keep a writer instance around.

    Args:
        maze: The maze to serialize.
        output_file: Path of the file to write the maze content to.
        path: Ordered list of ``(row, col)`` coordinates describing the
            solved path from entry to exit, or ``None`` if no path
            should be included.

    Returns:
        None
    """
    MazeWriter(maze, path).write(output_file)
