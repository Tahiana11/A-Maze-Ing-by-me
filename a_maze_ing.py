from mazegen.generator import MazeGenerator
from mazegen.imperfect_generator import ImperfectMazeGenerator
from mazegen.solver import MazeSolver
from utils.maze_writer import MazeWriter
from utils.config_parser import Config, ConfigError, parse_config
from display.mlx_view import Render


def build_maze(config: Config) -> tuple[MazeGenerator, list[tuple[int, int]]]:
    """Build a maze and solve it based on the given configuration.

    If ``config.perfect`` is ``False``, an :class:`ImperfectMazeGenerator`
    (a maze containing loops) is used instead of the standard
    :class:`MazeGenerator`.

    Args:
        config: Parsed configuration describing the maze dimensions,
            entry/exit points, seed, and whether it should be perfect.

    Returns:
        A tuple ``(maze, path)`` where ``maze`` is the generated maze
        instance and ``path`` is the list of ``(row, col)`` coordinates
        forming the shortest path from entry to exit.

    Raises:
        ValueError: If the configured entry or exit position is
            invalid (e.g. it falls on a blocked cell).
    """
    if config.perfect:
        maze: MazeGenerator = MazeGenerator(
            config.width,
            config.height,
            config.entry,
            config.exit,
            seed=config.seed,
        )
        for _ in maze.generate_dfs():
            pass
    else:
        maze = ImperfectMazeGenerator(
            config.width,
            config.height,
            config.entry,
            config.exit,
            seed=config.seed,
        )
        for _ in maze.generate_imperfect():
            pass

    path = MazeSolver(maze).solve_bfs()
    return maze, path


def main() -> None:
    """Entry point: load the configuration, build and render the maze.

    Reads ``config.txt``, generates the maze and its solution, writes
    the result to the configured output file, and then opens the
    graphical window (via :class:`display.mlx_view.Render`) to display
    the generation animation and the solved path.

    Any configuration error or invalid maze parameters are caught and
    reported to standard output instead of raising.

    Returns:
        None
    """
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
