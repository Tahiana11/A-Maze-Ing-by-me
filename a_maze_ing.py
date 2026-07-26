from mazegen.generator import MazeGenerator
from display.mlx_view import Render


def main() -> None:
    width = 40
    height = 40
    entry = (0, 0)
    exit = (18, 16)
    try:
        maze = MazeGenerator(width, height, entry, exit)
        maze.generate()
        path = maze.solve()
        if not path:
            print("Aucun chemin trouvé entre l'entrée et la sortie")
        render = Render(entry, exit, maze.grid)
        render.set_path(path)
        render.run()
    except ValueError as e:
        print(e)

if __name__ == "__main__":
    main()
