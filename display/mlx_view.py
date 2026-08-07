from typing import Any
from mlx import Mlx
from mazegen.generator import Cell, MazeGenerator
from mazegen.imperfect_generator import ImperfectMazeGenerator
from mazegen.solver import MazeSolver
from utils.config_parser import Config
from utils.maze_writer import MazeWriter
import random
import os
import signal


class Render:
    """Renders and animates a maze in an MLX graphical window.
    Handles drawing the maze grid, the solved path, the entry/exit
    markers, and the footer, as well as driving the step-by-step
    generation and path-reveal animations and dispatching keyboard
    events.
    Attributes:
        mlx (Mlx): The MLX library wrapper instance.
        mlx_ptr (Any): Pointer to the initialized MLX context.
        config (Config): The maze configuration in use.
        height_win (int): Height, in pixels, of the maze drawing area.
        width_win (int): Width, in pixels, of the maze drawing area.
        footer_height (int): Height, in pixels, of the footer area.
        wall_thickness (int): Thickness, in pixels, of drawn walls.
        width (int): Number of columns in the maze grid.
        height (int): Number of rows in the maze grid.
        entry (tuple[int, int]): Entry point of the maze as ``(row, col)``.
        exit (tuple[int, int]): Exit point of the maze as ``(row, col)``.
        cell_size (int): Size, in pixels, of a single grid cell.
        win_total_height (int): Total window height including footer.
        window (Any): Pointer to the created MLX window.
        grid (list[list[Cell]]): The grid currently being displayed.
        img_ptr (Any): Pointer to the MLX image buffer.
        data (Any): Raw pixel buffer of the image.
        bpp (int): Bits per pixel of the image buffer.
        sl (int): Size, in bytes, of a single line of the image buffer.
        wall_color (int): Current RGBA color used to draw walls.
        path_color (int): Current RGBA color used to draw the path.
        pattern_color (int): Current RGBA color used to draw pattern
            cells.
        path (list[tuple[int, int]]): Currently known solved path.
        show_path (bool): Whether the path should be drawn.
    """
    def __init__(
        self,
        entry: tuple[int, int],
        _exit: tuple[int, int],
        grid: list[list[Cell]],
        config: Config,
        maze: MazeGenerator | None = None,
        height_win: int = 800,
        width_win: int = 800,
        wall_thickness: int = 1,
        footer_height: int = 30,
    ) -> None:
        """Initialize the MLX window and precompute display parameters.
        Args:
            entry: Entry point of the maze as ``(row, col)``.
            _exit: Exit point of the maze as ``(row, col)``.
            grid: Two-dimensional grid of `Cell` objects to display.
            config: Maze configuration, used when regenerating mazes.
            maze: Optional maze instance used to compute the initial
                solved path via :class:`MazeSolver`. If ``None``, the
                initial path is empty.
            height_win: Requested window height, in pixels, before
                being adjusted to fit an integer number of cells.
            width_win: Requested window width, in pixels, before being
                adjusted to fit an integer number of cells.
            wall_thickness: Thickness, in pixels, used to draw walls.
            footer_height: Height, in pixels, of the footer area
                displaying the controls hint.
        """
        self.mlx = Mlx()
        self.mlx_ptr = self.mlx.mlx_init()
        self.config = config
        self.height_win = height_win
        self.width_win = width_win
        self.footer_height = footer_height
        self.wall_thickness = wall_thickness
        self.width = len(grid[0]) if grid else 0
        self.height = len(grid)
        self.entry = entry
        self.exit = _exit
        self.cell_size = min(
            self.width_win // self.width if self.width else 0,
            self.height_win // self.height if self.height else 0,
        )
        self.width_win = self.cell_size * self.width
        self.height_win = self.cell_size * self.height
        self.win_total_height = self.height_win + self.footer_height
        self.window = self.mlx.mlx_new_window(
            self.mlx_ptr, self.width_win, self.win_total_height, "A-Maze-Ing"
        )
        self.grid = grid
        self.img_ptr = self.mlx.mlx_new_image(
            self.mlx_ptr, self.width_win, self.win_total_height
        )
        self.data, self.bpp, self.sl, _ = self.mlx.mlx_get_data_addr(
            self.img_ptr)
        self.wall_color = self._random_color()
        self.path_color = self._random_color()
        self.pattern_color = self._random_color()
        self.path = MazeSolver(maze).solve_bfs() if maze is not None else []
        self._maze = maze
        self._gen_steps: Any = None
        self._active = False
        self._speed = 1
        self._counter = 0
        self._path_index = 1
        self.show_path = False
        self._stop_requested = False
        signal.signal(signal.SIGINT, self._on_sigint)
        self._display_cell()

    def _on_sigint(self, signum: int, frame: Any) -> None:
        """Handle Ctrl+C by requesting a clean shutdown of the MLX loop.
        Only sets an internal flag; the actual exit from the MLX loop
        happens in :meth:`loop_hook` to avoid raising a
        ``KeyboardInterrupt`` in the middle of a ctypes callback.
        Args:
            signum: The signal number received (unused).
            frame: The current stack frame (unused).
        Returns:
            None
        """
        self._stop_requested = True

    def _random_color(self) -> int:
        """Generate a random opaque RGBA color.
        Returns:
            A 32-bit integer encoding an opaque color as
            ``0xFFRRGGBB``.
        """
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)

        return (0xFF << 24) | (r << 16) | (g << 8) | b

    def _fill_cell(
            self,
            x0: int,
            x1: int,
            y0: int,
            y1: int, color: int) -> None:
        """Fill a rectangular pixel region of the image buffer with a color.

        Coordinates are clamped to the image bounds before filling.

        Args:
            x0: Left edge x-coordinate of the rectangle, in pixels.
            x1: Right edge x-coordinate of the rectangle, in pixels.
            y0: Top edge y-coordinate of the rectangle, in pixels.
            y1: Bottom edge y-coordinate of the rectangle, in pixels.
            color: RGBA color to fill the rectangle with, as produced
                by :meth:`_random_color`.
        Returns:
            None
        """
        x0, x1 = max(0, x0), min(self.width_win - 1, x1)
        y0, y1 = max(0, y0), min(self.win_total_height - 1, y1)
        try:
            for y in range(y0, y1 + 1):
                row_off = y * self.sl
                for x in range(x0, x1 + 1):
                    offset = row_off + x * (self.bpp // 8)
                    self.data[offset: offset + 4] = color.to_bytes(
                        4, "little")

        except KeyboardInterrupt:
            os._exit(1)
            return

    def _display_cell(self) -> None:
        """Draw the base grid: pattern/background fills, then all walls.
        Returns:
            None
        """
        for row in range(self.height):
            for col in range(self.width):
                x0 = col * self.cell_size
                y0 = row * self.cell_size
                cell = self.grid[row][col]
                fill_color = (
                    self.pattern_color
                    if getattr(cell, "is_pattern", False)
                    else 0xFF000000
                )
                self._fill_cell(
                    x0, x0 + self.cell_size - 1,
                    y0, y0 + self.cell_size - 1, fill_color
                )

        for row in range(self.height):
            for col in range(self.width):
                cell = self.grid[row][col]
                x0 = col * self.cell_size
                y0 = row * self.cell_size
                x1 = x0 + self.cell_size - 1
                y1 = y0 + self.cell_size - 1

                if cell.walls["N"]:
                    self._fill_cell(
                        x0, x1, y0,
                        y0 + self.wall_thickness - 1,
                        self.wall_color
                    )
                if cell.walls["E"]:
                    self._fill_cell(
                        x1 - self.wall_thickness + 1,
                        x1, y0, y1, self.wall_color
                    )
                if cell.walls["S"]:
                    self._fill_cell(
                        x0, x1, y1 - self.wall_thickness + 1,
                        y1, self.wall_color
                    )
                if cell.walls["W"]:
                    self._fill_cell(
                        x0, x0 + self.wall_thickness - 1,
                        y0, y1, self.wall_color
                    )

    def set_path(self, path: list[tuple[int, int]]) -> None:
        """Set the path to be drawn.

        Args:
            path: Ordered list of ``(row, col)`` coordinates describing
                the path to draw.

        Returns:
            None
        """
        self.path = path

    def set_grid(self, grid: list[list[Cell]]) -> None:
        """Replace the grid currently being displayed.

        Args:
            grid: New two-dimensional grid of `Cell` objects, typically
                provided by an external generator.

        Returns:
            None
        """
        self.grid = grid

    def draw_entry_exit(self) -> None:
        """Draw markers for the maze's entry and exit cells.

        Returns:
            None
        """
        entry_exit: list[str] = ["entry", "exit"]
        for e in entry_exit:
            if e == "exit":
                er, ec = self.exit
            else:
                er, ec = self.entry
            mini = self.cell_size // 2
            offset = (self.cell_size - mini) // 2
            x = ec * self.cell_size + offset
            y = er * self.cell_size + offset
            self._fill_cell(x,
                            x + mini - 1, y,
                            y + mini - 1, self._random_color())

    def _draw_footer(
        self, text: str = "1:regen; 2:path; 3:color; 4:quit; 5 or 6:animate"
    ) -> None:
        """Draw the footer bar with the keyboard controls hint.

        Args:
            text: Text to display in the footer.

        Returns:
            None
        """
        y0 = self.height_win
        y1 = self.win_total_height - 1
        self._fill_cell(0, self.width_win - 1, y0, y1, 0xFF000000)
        self.mlx.mlx_string_put(
            self.mlx_ptr,
            self.window,
            10,
            y0 + self.footer_height // 10,
            0xFFFFFFFF,
            text,
        )

    def draw_path(self) -> None:
        """Draw a small square at the center of each revealed path cell.

        When an animation is active (``self._active``), only the first
        ``self._path_index`` cells of ``self.path`` are drawn; otherwise
        the whole path is drawn.

        Returns:
            None
        """
        mini = self.cell_size // 5
        offset = (self.cell_size - mini) // 2
        reveal = self._path_index if self._active else len(self.path)
        for row, col in self.path[:reveal]:
            x = self.cell_size * col + offset
            y = self.cell_size * row + offset
            self._fill_cell(x, x + mini - 1, y, y + mini - 1, self.path_color)

    def draw(self) -> None:
        """Redraw the full frame: grid, path (if shown), markers, footer.

        Returns:
            None
        """
        self._display_cell()
        if self.path and self.show_path:
            self.draw_path()
        self.draw_entry_exit()
        self.mlx.mlx_put_image_to_window(self.mlx_ptr,
                                         self.window, self.img_ptr, 0, 0)
        self._draw_footer()

    def _new_maze_and_steps(self) -> tuple[MazeGenerator, Any]:
        """Create a new maze and its step generator, ready for animation.

        Builds either a perfect or imperfect maze depending on
        ``self.config.perfect``, without consuming its generator, so it
        can be advanced step by step by the animation loop.

        Returns:
            A tuple ``(maze, steps)`` where ``maze`` is the newly
            created maze instance and ``steps`` is the generator
            yielding wall-removal steps.
        """
        if self.config.perfect:
            maze: MazeGenerator = MazeGenerator(
                self.width, self.height, self.entry, self.exit
            )
            steps = maze.generate_dfs()
        else:
            maze = ImperfectMazeGenerator(
                self.width, self.height, self.entry, self.exit
            )
            steps = maze.generate_imperfect()

        return maze, steps

    def _write_maze_file(self) -> None:
        """Write the current maze and path to the configured output file.

        Does nothing if no maze is currently set.

        Returns:
            None
        """
        if self._maze is None:
            return
        MazeWriter(self._maze, self.path).write(self.config.output_file)

    def regenerate(self) -> None:
        """Regenerate a new maze and replay its generation and path animations.

        Generates a new maze (perfect or not, depending on the
        configuration), animates its construction, then animates the
        reveal of its solved path, and redraws the final frame. The
        output file is updated automatically once generation completes.

        Returns:
            None
        """
        self.generation_animation()
        self.path_animation()
        self.draw()

    def generation_animation(self, speed: int = 1) -> None:
        """Start (or restart) the step-by-step maze generation animation.

        Creates a new maze and step generator, resets the path and
        animation state, and marks the animation as active so that
        subsequent calls to :meth:`loop_hook` advance it.

        Args:
            speed: Number of loop ticks to wait between animation
                updates; higher values slow down the animation. Values
                below 0 are clamped to 0.

        Returns:
            None
        """
        new_maze, steps = self._new_maze_and_steps()
        self._maze = new_maze
        self.grid = new_maze.grid
        self._gen_steps = steps

        self.path = []
        self._path_index = 0
        self.show_path = False
        self._speed = max(0, speed)
        self._counter = 0
        self._active = True

    def path_animation(self, speed: int = 1) -> None:
        """Start (or restart) the step-by-step path-reveal animation.

        Computes the solved path if it has not been computed yet, then
        resets the reveal index and marks the animation as active.

        Args:
            speed: Number of loop ticks to wait between animation
                updates; higher values slow down the animation. Values
                below 0 are clamped to 0.

        Returns:
            None
        """
        if self._maze is None:
            return
        if not self.path:
            self.path = MazeSolver(self._maze).solve_bfs()

        self._path_index = 0
        self.show_path = True
        self._speed = max(0, speed)
        self._counter = 0
        self._active = True

    def _advance_generation(self, steps: int = 10) -> None:
        """Advance the generation animation by a number of steps.

        Pulls up to ``steps`` values from ``self._gen_steps``. When the
        generator is exhausted, the animation is marked inactive, the
        solved path is (re)computed, and the maze file is rewritten.

        Args:
            steps: Maximum number of generation steps to advance in
                this call.

        Returns:
            None
        """
        for _ in range(steps):
            try:
                next(self._gen_steps)
            except StopIteration:
                self._gen_steps = None
                self._active = False
                if self._maze is not None:
                    self.path = MazeSolver(self._maze).solve_bfs()
                    self._write_maze_file()
                break

    def _advance_path(self) -> None:
        """Reveal one more cell of the path animation.

        Increments the reveal index and marks the animation inactive
        once the whole path has been revealed.

        Returns:
            None
        """
        if self._path_index < len(self.path):
            self._path_index += 1
        if self._path_index >= len(self.path):
            self._active = False

    def loop_hook(self, *args: Any) -> None:
        """MLX loop callback driving animations and handling shutdown.

        Exits the MLX loop if a shutdown was requested (e.g. via
        Ctrl+C). Otherwise, if an animation is active, advances either
        the generation or path animation (throttled by ``self._speed``)
        and redraws the frame.

        Args:
            *args: Additional arguments passed by the MLX loop hook,
                unused.

        Returns:
            None
        """
        if self._stop_requested:
            self.mlx.mlx_loop_exit(self.mlx_ptr)
            return

        if not self._active:
            return

        self._counter += 1
        if self._counter < self._speed:
            return
        self._counter = 0

        if self._gen_steps is not None:
            self._advance_generation()
        elif self.show_path:
            self._advance_path()

        self.draw()

    def on_key(self, keycode: int, *args: Any) -> None:
        """Handle keyboard input for the MLX window.

        Key bindings:
            - ``4``: quit the window.
            - ``1``: regenerate the maze.
            - ``5``: start the path-reveal animation.
            - ``6``: start the maze-generation animation.
            - ``2``: toggle whether the path is shown.
            - ``3``: randomize the wall, path, and pattern colors.

        Args:
            keycode: Code of the key that was pressed.
            *args: Additional arguments passed by the MLX key hook,
                unused.

        Returns:
            None
        """
        if keycode == ord("4"):
            self.mlx.mlx_loop_exit(self.mlx_ptr)

        if keycode == ord("1"):
            self.regenerate()

        if keycode == ord("5"):
            self.path_animation()

        if keycode == ord("6"):
            self.generation_animation()

        if keycode == ord("2"):
            self.show_path = not self.show_path
            self.draw()

        if keycode == ord("3"):
            self.wall_color = self._random_color()
            self.path_color = self._random_color()
            self.pattern_color = self._random_color()
            self.draw()

    def expose(self, *args: Any) -> None:
        """Redraw the frame in response to an MLX expose event.

        Args:
            *args: Additional arguments passed by the MLX expose hook,
                unused.

        Returns:
            None
        """
        self.draw()

    def on_close(self, *args: Any) -> None:
        """Cleanly exit the MLX loop when the window's close button is clicked.

        Args:
            *args: Additional arguments passed by the MLX hook, unused.

        Returns:
            None
        """
        self.mlx.mlx_loop_exit(self.mlx_ptr)

    def run(self) -> None:
        """Register all MLX hooks and start the main event loop.

        Blocks until the loop exits (via the close button, the quit
        key, or a requested shutdown), then destroys the image and
        window and releases the MLX context.

        Returns:
            None
        """
        self.mlx.mlx_expose_hook(self.window, self.expose, None)
        self.mlx.mlx_key_hook(self.window, self.on_key, None)
        self.mlx.mlx_hook(self.window, 33, 0, self.on_close, None)
        self.mlx.mlx_loop_hook(self.mlx_ptr, self.loop_hook, None)
        self.mlx.mlx_loop(self.mlx_ptr)
        self.mlx.mlx_destroy_image(self.mlx_ptr, self.img_ptr)
        self.mlx.mlx_destroy_window(self.mlx_ptr, self.window)
        self.mlx.mlx_release(self.mlx_ptr)
