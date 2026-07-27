from typing import Any
from mlx import Mlx
from mazegen.generator import Cell, MazeGenerator
from mazegen.solver import MazeSolver
import random


class Render:
    def __init__(
        self,
        entry: tuple[int, int],
        exit: tuple[int, int],
        grid: list[list[Cell]],
        maze: MazeGenerator | None = None,
        height_win: int = 600,
        width_win: int = 600,
        wall_thickness: int = 1,
    ) -> None:
        self.mlx = Mlx()
        self.mlx_ptr = self.mlx.mlx_init()
        self.height_win = height_win
        self.width_win = width_win
        self.wall_thickness = wall_thickness
        self.width = len(grid[0]) if grid else 0
        self.height = len(grid)
        self.entry = entry
        self.exit = exit
        self.cell_size = min(
            self.width_win // self.width if self.width else 0,
            self.height_win // self.height if self.height else 0,
        )
        self.width_win = self.cell_size * self.width
        self.height_win = self.cell_size * self.height
        self.window = self.mlx.mlx_new_window(
            self.mlx_ptr, self.width_win, self.height_win, "A-Maze-Ing")
        self.grid = grid
        self.img_ptr = self.mlx.mlx_new_image(
            self.mlx_ptr, self.width_win, self.height_win)
        self.data, self.bpp, self.sl, _ = self.mlx.mlx_get_data_addr(
            self.img_ptr)
        self.wall_color = self._random_color()
        self.path_color = self._random_color()
        self.pattern_color = self._random_color()
        self.path = MazeSolver(maze).solve_bfs() if maze is not None else []
        self._maze = maze
        self._gen_steps = None
        self._active = False
        self._speed = 0
        self._counter = 0
        self._path_index = 1
        self.show_path = False
        self._display_cell()

    def _random_color(self) -> int:
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)

        return (0xFF << 24) | (r << 16) | (g << 8) | b

    def _fill_cell(
        self, x0: int, x1: int, y0: int, y1: int, color: int
    ) -> None:
        """Calcule et remplit le buffer de l'image pixel par pixel"""
        x0, x1 = max(0, x0),  min(self.width_win - 1, x1)
        y0, y1 = max(0, y0), min(self.height_win - 1, y1)
        for y in range(y0, y1 + 1):
            row_off = y * self.sl
            for x in range(x0, x1 + 1):
                offset = row_off + x * (self.bpp // 8)
                self.data[offset:offset+4] = color.to_bytes(4, 'little')

    def _display_cell(self) -> None:
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
                    x0,
                    x0 + self.cell_size - 1,
                    y0, y0 + self.cell_size - 1,
                    fill_color
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
                        y0 + self.wall_thickness - 1, self.wall_color)
                if cell.walls["E"]:
                    self._fill_cell(
                        x1 - self.wall_thickness + 1, x1, y0, y1,
                        self.wall_color)
                if cell.walls["S"]:
                    self._fill_cell(
                        x0, x1, y1 - self.wall_thickness + 1, y1,
                        self.wall_color)
                if cell.walls["W"]:
                    self._fill_cell(
                        x0, x0 + self.wall_thickness - 1, y0, y1,
                        self.wall_color)

    def set_path(self, path: list[tuple[int, int]]) -> None:
        """Enregistre le chemin (liste de (row, col)) a dessiner."""
        self.path = path

    def set_grid(self, grid: list[list[Cell]]) -> None:
        """Remplace la grille a afficher
        (fournie par un générateur externe)."""
        self.grid = grid

    def draw_entry_exit(self) -> None:
        """Draw l'entre et le sortie
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
            self._fill_cell(
                x,
                x + mini - 1,
                y,
                y + mini - 1,
                self._random_color()
            )

    def draw_path(self) -> None:
        """Dessin une petit carre au centre de chaque chemin"""
        mini = self.cell_size // 5
        offset = (self.cell_size - mini) // 2
        reveal = self._path_index if self._active else len(self.path)
        for row, col in self.path[:reveal]:
            x = self.cell_size * col + offset
            y = self.cell_size * row + offset
            self._fill_cell(x, x + mini - 1, y, y + mini - 1, self.path_color)

    def draw(self) -> None:
        self._display_cell()
        if self.path and self.show_path:
            self.draw_path()
        self.draw_entry_exit()
        self.mlx.mlx_put_image_to_window(
            self.mlx_ptr, self.window, self.img_ptr, 0, 0)

    def regenerate(self) -> None:
        """Regenere une nouvelle maze"""
        new_maze = MazeGenerator(
            self.width,
            self.height,
            self.entry,
            self.exit
        )
        new_maze.generate_dfs()
        self._maze = new_maze
        self.grid = new_maze.grid
        self.path = MazeSolver(new_maze).solve_bfs()
        self.generation_animation()
        self.draw()

    def generation_animation(self, speed: int = 1) -> None:
        new_maze = MazeGenerator(
            self.width, self.height, self.entry, self.exit
        )
        self._maze = new_maze
        self.grid = new_maze.grid
        self._gen_steps = new_maze.generate_dfs()

        self.path = []
        self._path_index = 0
        self.show_path = False
        self._speed = max(0, speed)
        self._counter = 0
        self._active = True

    def path_animation(self, speed: int = 1) -> None:
        if self._maze is None:
            return
        if not self.path:
            self.path = MazeSolver(self._maze).solve_bfs()

        self._path_index = 0
        self.show_path = True
        self._speed = max(0, speed)
        self._counter = 0
        self._active = True

    def _advance_generation(self) -> None:
        try:
            next(self._gen_steps)
        except StopIteration:
            self._gen_steps = None
            self._active = False
            if self._maze is not None:
                self.path = MazeSolver(self._maze).solve_bfs()

    def _advance_path(self) -> None:
        if self._path_index < len(self.path):
            self._path_index += 1
        if self._path_index >= len(self.path):
            self._active = False

    def loop_hook(self, *args: Any) -> None:
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
        """Quitte la fenêtre avec Échap (65307)
        regenere le maze avec r
        changer de coleur avec c
        afficher et ne pas afficher le chemin avec p"""
        if keycode == 65307:
            self.mlx.mlx_loop_exit(self.mlx_ptr)

        if keycode == ord('r'):
            self.regenerate()

        if keycode == ord('g'):
            self.generation_animation()

        if keycode == ord('a'):
            self.path_animation()

        if keycode == ord('p'):
            self.show_path = not self.show_path
            self.draw()

        if keycode == ord("c"):
            self.wall_color = self._random_color()
            self.path_color = self._random_color()
            self.pattern_color = self._random_color()
            self.draw()

    def expose(self, *args: Any) -> None:
        self.draw()

    def on_close(self, *args: Any) -> None:
        """Quitte proprement lors du clic sur la croix rouge (X)"""
        self.mlx.mlx_loop_exit(self.mlx_ptr)

    def run(self) -> None:
        self.mlx.mlx_expose_hook(self.window, self.expose, None)
        self.mlx.mlx_key_hook(self.window, self.on_key, None)
        self.mlx.mlx_hook(self.window, 33, 0, self.on_close, None)
        self.mlx.mlx_loop_hook(self.mlx_ptr, self.loop_hook, None)
        self.mlx.mlx_loop(self.mlx_ptr)
        self.mlx.mlx_destroy_image(self.mlx_ptr, self.img_ptr)
        self.mlx.mlx_destroy_window(self.mlx_ptr, self.window)
        self.mlx.mlx_release(self.mlx_ptr)
