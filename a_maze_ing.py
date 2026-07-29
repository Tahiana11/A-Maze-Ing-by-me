from mazegen.generator import MazeGenerator
from mazegen.imperfect_generator import ImperfectMazeGenerator
from mazegen.solver import MazeSolver
from utils.maze_writer import MazeWriter
from utils.config_parser import Config, ConfigError, parse_config
from display.mlx_view import Render


def build_maze(config: Config) -> tuple[MazeGenerator, list[tuple[int, int]]]:
    """Génère le labyrinthe et son chemin résolu à partir de la config.

    Si `config.perfect` est False, on utilise `ImperfectMazeGenerator`
    (labyrinthe avec des boucles) au lieu du `MazeGenerator` classique.
    """
    if config.perfect:
        maze: MazeGenerator = MazeGenerator(
            config.width,
            config.height,
            config.entry,
            config.exit,
        )
        for _ in maze.generate_dfs():
            pass
    else:
        maze = ImperfectMazeGenerator(
            config.width,
            config.height,
            config.entry,
            config.exit,
        )
        for _ in maze.generate_imperfect():
            pass

    path = MazeSolver(maze).solve_bfs()
    return maze, path


def main() -> None:
    try:
        config = parse_config("config.txt")
    except ConfigError as e:
        print(f"Configuration error: {e}")
        return

    try:
        maze, path = build_maze(config)
    except ValueError as e:
        print(e)
        return

    MazeWriter(maze, path).write(config.output_file)

    render = Render(config.entry, config.exit, maze.grid, config, maze=maze)
    render.generation_animation()
    render.show_path = True
    render.set_path(path)
    render.run()


if __name__ == "__main__":
    main()
