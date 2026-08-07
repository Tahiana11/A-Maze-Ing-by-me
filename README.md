*This project has been created as part of the 42 curriculum by mamy-and, firahari.*

---

# A-Maze-ing


## 📌 Description

A-Maze-ing is a maze generator written in Python. Using a simple text-based configuration file, the program generates a random maze (while remaining reproducible through the use of a seed), saves it to an output file using a compact hexadecimal wall encoding, and provides a clear graphical visualization of the result using the MiniLibX (MLX) library.

The generated maze satisfies several structural constraints, including full connectivity, the absence of large open areas, and consistent wall definitions between adjacent cells. It can also be generated in perfect maze mode, ensuring that there is exactly one possible path between the entrance and the exit. The program computes this shortest path and can display it visually.

Beyond the executable script, the maze generation logic is encapsulated in a reusable `MazeGenerator` class and packaged as an installable Python module (`mazegen-*`), making it easy to integrate into future projects.


---

## 🔧 Instructions

### Requirements
- Python 3.10 or later
- pip (or uv/pipx, see make install)


### Setup

Clone the repository, then install the project dependencies:
```bash
git clone git@vogsphere.42antananarivo.mg:vogsphere/intra-uuid-3cda70d8-f366-42c3-8c59-e0cd9d809410-7493845-mamy-and A_Maze_ing
cd A_Maze_ing
```
```bash
make install
```

### Configuration

Before running the program, edit the configuration file (`config.txt` by default, included in the repository) to set your desired maze parameters:
```
WIDTH=30
HEIGHT=30
ENTRY=0,0
EXIT=29,29
OUTPUT_FILE=maze.txt
PERFECT=True
SEED=42
```
See the Configuration File Format section below for the full list of supported keys.

### Running the program
```bash
make run
```
or directly:
```bash
python3 a_maze_ing.py config.txt
```

The generated maze will be written to the file specified by `OUTPUT_FILE`, and a graphical window will open, displaying the maze via MiniLibX.


### Debugging
```bash
make debug
```
Runs the program using Python's built-in debugger (pdb).

### Cleaning
```bash
make clean
```
Removes temporary files and caches (`__pycache__`, `.mypy_cache`, etc.).

### Linting & type checking
```bash
make lint
```
Runs `flake8` and `mypy` with the required flags.

A stricter check is also available:

```bash
make lint-strict
```
### Building the reusable module

The maze generation logic is packaged as an installable module. To rebuild it from source:
```bash
pip install build
python3 -m build
make tarball
```
This produces the `mazegen-1.0.0-py3-none-any.whl` / `mazegen.tar.gz` file(s) at the project root, ready to be installed with:
```bash
pip install lib/mazegen-1.0.0-py3-none-any.whl
```

---

## 📁 Configuration File Format

The configuration file contains one `KEY=VALUE` pair per line. Lines starting with `#` are comments and are ignored.

| Key | Description | Required | Example |
|---|---|---|---|
| `WIDTH` | Maze width (number of cells) | Yes | `WIDTH=20` |
| `HEIGHT` | Maze height (number of cells) | Yes | `HEIGHT=15` |
| `ENTRY` | Entry coordinates `x,y` | Yes | `ENTRY=0,0` |
| `EXIT` | Exit coordinates `x,y` | Yes | `EXIT=19,14` |
| `OUTPUT_FILE` | Output file name | Yes | `OUTPUT_FILE=maze.txt` |
| `PERFECT` | Generate a perfect maze (`True`/`False`) | Yes | `PERFECT=True` |
| `SEED` | Seed for reproducibility | No | `SEED=42` |

A default configuration file (`config.txt`) is provided at the root of the repository.


---

## 📤 Output File Format

Each maze cell is encoded as a single hexadecimal digit representing the state of its walls:

| Bit | Direction | Decimal |
|---|---|---|
| 0 (LSB) | North | 1 |
| 1 | East | 2 |
| 2 | South | 4 |
| 3 | West | 8 |

A closed wall sets the corresponding bit to `1`, an open wall leaves it at `0`. For example, `3` (binary `0011`) means the south and west walls are open; `A` (binary `1010`) means the east and west walls are closed.

`N=1` = bit 0 set (`0001`), `E=2` = bit 1 set (`0010`), `S=4` = bit 2 set (`0100`), `W=8` = bit 3 set (`1000`) — this is exactly the mapping above (North = LSB, East, South, West).

Cells are stored row by row, one row of the maze per line of the file. After a blank line, three additional lines follow:
1. the entry coordinates,
2. the exit coordinates,
3. the shortest valid path between the entry and the exit, encoded using the letters `N`, `E`, `S`, `W`.

All lines end with `\n`.

---

## 🧩 Generation Algorithm

This project uses the recursive backtracking algorithm (depth-first search with backtracking), implemented iteratively with an explicit stack in `MazeGenerator.generate_dfs()`.

**Why this algorithm?**

- It naturally produces a perfect maze (a spanning tree: every cell reachable, exactly one path between any two cells), which directly matches the `PERFECT` mode requirement.
- It generates mazes with long, winding corridors and few short dead ends, resulting in a visually pleasing output.
- Implementing it iteratively with a stack (rather than recursively) avoids Python's recursion depth limit on large mazes.
- Compared to Prim's algorithm (more uniform, shorter mazes) or Kruskal's algorithm (requires a union-find structure), it offered the best simplicity/control trade-off to satisfy all of the subject's constraints.

For the imperfect mode, `ImperfectMazeGenerator` first runs the same recursive backtracking pass, then randomly removes a proportion of additional walls (`walls` ratio) and carves a number of 2×2 open rooms (`rooms_2x2`), producing loops and open areas of at most 2×2 cells while remaining fully connected.

---

## ♻️ Code Reusability

The generation logic is isolated in the `mazegen` package, provided as a standalone module installable via pip, independent of the executable script `a_maze_ing.py`. It contains four files:

- `generator.py`: the `Cell` class and the base `MazeGenerator` class (perfect maze generation via recursive backtracking, plus the "42" pattern).
- `imperfect_generator.py`: `ImperfectMazeGenerator`, a subclass of `MazeGenerator` that adds extra wall removal and 2×2 rooms for imperfect mazes.
- `solver.py`: `MazeSolver`, computing the shortest path between entry and exit with BFS.
- `__init__.py`: exposes `MazeGenerator`, `ImperfectMazeGenerator`, and `MazeSolver` at the package level.

### mazegen

A standalone generic Maze Generator: perfect and imperfect maze generation (`MazeGenerator`, `ImperfectMazeGenerator`) plus a BFS solver (`MazeSolver`).

#### Install

```bash
pip install mazegen-1.0.0-py3-none-any.whl
```

#### Usage

```python
from mazegen.generator import MazeGenerator
from mazegen.imperfect_generator import ImperfectMazeGenerator
from mazegen.solver import MazeSolver
```

#### Example

```python
from mazegen.generator import MazeGenerator
from mazegen.imperfect_generator import ImperfectMazeGenerator
from mazegen.solver import MazeSolver

# --- Perfect maze (exactly one path between entry and exit) ---
maze = MazeGenerator(
    width=10,
    height=10,
    entry=(0, 0),
    exit=(9, 9),
    seed=42
)

# generate_dfs() is a generator: consume it fully to build the maze
# (each yielded step is (row, col, neighbor_row, neighbor_col), useful for animation)
for _ in maze.generate_dfs():
    pass

# Access the grid: a 2D list of Cell objects
# Each Cell exposes .walls: dict[str, bool] for "N", "E", "S", "W" (True = closed)
print(maze.grid[0][0].walls)  # e.g. {"N": True, "E": False, "S": True, "W": True}

# Compute the shortest path between entry and exit
solver = MazeSolver(maze)
path = solver.solve_bfs()  # list[tuple[int, int]], empty if no path exists
print(path)


# --- Imperfect maze (loops + open 2x2 rooms) ---
imperfect_maze = ImperfectMazeGenerator(
    width=10,
    height=10,
    entry=(0, 0),
    exit=(9, 9),
    walls=0.1,      # ratio of extra walls removed after the perfect maze pass
    rooms_2x2=2,    # number of 2x2 open rooms to carve
    seed=42
)

for _ in imperfect_maze.generate_imperfect():
    pass

imperfect_path = MazeSolver(imperfect_maze).solve_bfs()
print(imperfect_path)
```

---

## 🖥️ Visual Representation

The visualization is done as a graphical window using the MiniLibX (MLX) library. It clearly displays the walls, the entrance, the exit, and the solution path.

Available interactions:
- Regenerate a new maze and display it
- Show/hide the shortest path between the entrance and the exit
- Change the wall colors

---

## 📚 Resources

### Maze generation

- Maze Generation: [Recursive Backtracking – Jamis Buck](https://weblog.jamisbuck.org/2010/12/27/maze-generation-recursive-backtracking) — reference article on the recursive backtracker algorithm
- Buckblog: [Maze Generation Algorithms series](https://weblog.jamisbuck.org/2011/2/7/maze-generation-algorithm-recap) — overview and comparison of Prim's, Kruskal's, and other algorithms
- [Wikipedia – Maze generation algorithm](https://en.wikipedia.org/wiki/Maze_generation_algorithm)
- [Introduction to spanning trees – graph theory background (relevant to "perfect" mazes)](https://en.wikipedia.org/wiki/Spanning_tree)

### Python

- [Python typing module documentation](https://docs.python.org/3/library/typing.html)
- [PEP 257 – Docstring Conventions](https://peps.python.org/pep-0257/)
- [Packaging Python Projects – official guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
- [mypy documentation](https://mypy.readthedocs.io/)
- [flake8 documentation](https://flake8.pycqa.org/)

### Display

- [MiniLibX documentation – 42 Paris wiki](https://harm-smits.github.io/42docs/libs/minilibx) — reference for window creation, pixel drawing, and event handling used for the graphical rendering

### AI usage

This project made use of AI assistance for the following tasks:
- Clarifying import mechanisms and Python packaging concepts
- Reviewing/discussing the wall-consistency logic between adjacent cells
- Reviewing and correcting the README.md file to ensure compliance with the subject's requirements

---

## 👥 Team & Project Management

| Members | Role |
|---|---|
| mamy-and | `mazegen/generator.py`, `mazegen/solver.py`, `utils/config_parser.py`, `a_maze_ing.py`, `display/mlx_view.py` |
| firahari | `mazegen/imperfect_generator.py`, `utils/maze_writer.py`, `README.md` |

### Planning

The work was split early along the natural boundaries of the pipeline (`config → generation → solving → output → display`), so both members could progress in parallel from day one:

- **mamy-and** focused on the core generation logic (`mazegen/generator.py`, recursive backtracking + "42" pattern), the shortest-path solver (`mazegen/solver.py`), the configuration parsing (`utils/config_parser.py`), the MLX graphical rendering (`display/mlx_view.py`), and the main entry point tying everything together (`a_maze_ing.py`).
- **firahari** focused on the imperfect maze variant (`mazegen/imperfect_generator.py`, extra wall removal and 2×2 rooms), the output file writer (`utils/maze_writer.py`), and the project documentation (`README.md`).

**Initial plan:**
1. Design the `Cell`/`MazeGenerator` data model and get a working perfect maze generator (recursive backtracking).
2. In parallel, design the config file parser and the output file writer against that data model.
3. Build the imperfect maze variant on top of the base generator once its interface was stable.
4. Add the BFS solver once the maze structure was finalized.
5. Build the MLX display last, once the generator/solver output format was frozen, plugging in the animation and user interactions (regenerate, toggle path, change colors).
6. Package the reusable `mazegen` module and finalize the README.

**Evolution:**
- Keeping `MazeGenerator` and `ImperfectMazeGenerator` in a shared inheritance hierarchy (rather than duplicating logic) turned out to simplify the solver and the display, since both expose the same `grid`/`walls` interface — `MazeSolver` and `Render` work unmodified on either class.
- The main script (`a_maze_ing.py`) ended up as a thin orchestration layer (`build_maze` + `main`), which made it easy to plug the animation and path display in at the end without touching the generation or solving logic.

