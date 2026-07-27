from mazegen.generator import MazeGenerator
from display.mlx_view import Render
from mazegen.solver import MazeSolver

def main() -> None:
    width = 20
    height = 20
    entry = (0, 0)
    exit = (18, 16)
    try:
        maze = MazeGenerator(width, height, entry, exit)
        maze.generate_dfs()
        path = MazeSolver(maze).solve_bfs()
        render = Render(entry, exit, maze.grid, maze=maze)
        render.generation_animation()
        render.set_path(path)
        render.run()
    except ValueError as e:
        print(e)


if __name__ == "__main__":
    main()
