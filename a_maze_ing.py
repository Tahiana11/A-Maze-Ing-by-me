from mazegen.generator import MazeGenerator
from display.mlx_view import Render


def main() -> None:
    maze = MazeGenerator(width=15, height=10)
    maze.generate()
    render = Render(maze.grid)
    render.run()


if __name__ == "__main__":
    main()
