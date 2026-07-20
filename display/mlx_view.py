from typing import Any
from mlx import Mlx
from mazegen.generator import Cell, MazeGenerator
import random


WALL_THICKNESS = 1

class Render:
    def __init__(
        self,
        # height: int = 15,
        # width: int = 20,
        grid: list[list[Cell]],
        height_win: int = 1000,
        width_win: int = 1000,
        wall_thickness: int = 1,
    ) -> None:
        self.mlx = Mlx()
        self.mlx_ptr = self.mlx.mlx_init()
        self.height_win = height_win
        self.width_win = width_win
        self.width = len(grid[0]) if grid else 0
        self.height = len(grid)
        self.cell_size = min(
            self.width_win // self.width if self.width else 0,
            self.height_win // self.height if self.height else 0,
        )
        self.width_win = self.cell_size * self.width
        self.height_win = self.cell_size * self.height
        self.window = self.mlx.mlx_new_window(
            self.mlx_ptr, self.width_win, self.height_win, "A-Maze-Ing")
        self.grid = grid

        # Créer l'image
        self.img_ptr = self.mlx.mlx_new_image(
            self.mlx_ptr, self.width_win, self.height_win)

        # Récupérer le buffer de pixels
        self.data, self.bpp, self.sl, _ = self.mlx.mlx_get_data_addr(
            self.img_ptr)
        self.wall_color = 0xFF000000
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
                self._fill_cell(
                    x0, x0 + self.cell_size - 1, y0, y0 + self.cell_size - 1, 0xFFECECEC)

        for row in range(self.height):
            for col in range(self.width):
                cell = self.grid[row][col]
                x0 = col * self.cell_size
                y0 = row * self.cell_size
                x1 = x0 + self.cell_size - 1
                y1 = y0 + self.cell_size - 1

                if cell.walls["N"]:
                    self._fill_cell(
                        x0, x1, y0, y0 + WALL_THICKNESS - 1, self.wall_color)
                if cell.walls["E"]:
                    self._fill_cell(
                        x1 - WALL_THICKNESS + 1, x1, y0, y1, self.wall_color)
                if cell.walls["S"]:
                    self._fill_cell(
                        x0, x1, y1 - WALL_THICKNESS + 1, y1, self.wall_color)
                if cell.walls["W"]:
                    self._fill_cell(
                        x0, x0 + WALL_THICKNESS - 1, y0, y1, self.wall_color)

    def set_grid(self, grid: list[list[Cell]]) -> None:
        """Remplace la grille à afficher (fournie par un générateur externe)."""
        self.grid = grid

    def draw(self) -> None:
        self._display_cell()
        self.mlx.mlx_put_image_to_window(
            self.mlx_ptr, self.window, self.img_ptr, 0, 0)

    def regenerate(self) -> None:
        """Regenere une nouvelle maze"""
        new_maze = MazeGenerator(self.width, self.height)
        new_maze.generate()
        self.grid = new_maze.grid
        self.draw()

    def leave_window(self, keycode: int, *args: Any) -> None:
        """Quitte la fenêtre avec Échap (65307)"""
        if keycode == 65307:
            self.mlx.mlx_loop_exit(self.mlx_ptr)

        if keycode == 99:
            self.wall_color = self._random_color()
            self.draw()

        if keycode == 114:
            self.regenerate()

    def expose(self, *args: Any) -> None:
        self.draw()

    def on_close(self, *args: Any) -> None:
        """Quitte proprement lors du clic sur la croix rouge (X)"""
        self.mlx.mlx_loop_exit(self.mlx_ptr)

    def run(self) -> None:
        self.mlx.mlx_expose_hook(self.window, self.expose, None)
        self.mlx.mlx_key_hook(self.window, self.leave_window, None)
        self.mlx.mlx_hook(self.window, 33, 0, self.on_close, None)
        self.mlx.mlx_loop(self.mlx_ptr)
        self.mlx.mlx_destroy_image(self.mlx_ptr, self.img_ptr)
        self.mlx.mlx_destroy_window(self.mlx_ptr, self.window)
        self.mlx.mlx_release(self.mlx_ptr)
