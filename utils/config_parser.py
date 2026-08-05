from dataclasses import dataclass
from pathlib import Path

_REQUIRED_KEYS = ("WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE")


class ConfigError(Exception):
    """Raised when the configuration file is missing, malformed, or
    contains invalid values."""

    ...


@dataclass
class Config:
    """Holds the parsed settings needed to generate and render a maze.

    Attributes:
        width: Number of columns in the maze grid.
        height: Number of rows in the maze grid.
        entry: Entry point of the maze as ``(row, col)``.
        exit: Exit point of the maze as ``(row, col)``.
        output_file: Path of the file the generated maze will be
            written to.
        perfect: Whether the maze should be perfect (no loops). Defaults
            to ``False``.
        seed: Optional seed used to make maze generation reproducible.
            Defaults to ``None``.
    """

    width: int
    height: int
    entry: tuple[int, int]
    exit: tuple[int, int]
    output_file: str
    perfect: bool = False
    seed: int | None = None


def parse_coord(raw: str, key: str) -> tuple[int, int]:
    """Parse a coordinate string of the form ``"x,y"`` into ``(row, col)``.

    Args:
        raw: Raw coordinate string, expected as ``"x,y"``.
        key: Name of the configuration key being parsed, used in error
            messages (e.g. ``"ENTRY"`` or ``"EXIT"``).

    Returns:
        The parsed coordinate as ``(row, col)``, i.e. ``(y, x)``.

    Raises:
        ConfigError: If ``raw`` is not in ``"x,y"`` format or does not
            contain two integers.
    """
    parts = raw.split(",")
    if len(parts) != 2:
        raise ConfigError(f"{key} must be in x,y format (received: {raw!r})")
    try:
        x, y = (int(p.strip()) for p in parts)
    except ValueError as e:
        raise ConfigError(f"{key} must contain " f"integers (received: {raw!r})") from e
    return (y, x)


def parse_bool(raw: str, key: str = "PERFECT") -> bool:
    """Parse a boolean configuration value.

    Args:
        raw: Raw string value, expected to be ``"True"`` or ``"False"``
            (case-insensitive, surrounding whitespace allowed).
        key: Name of the configuration key being parsed, used in the
            error message.

    Returns:
        ``True`` or ``False`` corresponding to the parsed value.

    Raises:
        ConfigError: If ``raw`` is neither ``"True"`` nor ``"False"``
            (case-insensitive).
    """
    normalized = raw.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ConfigError(f"{key} must be 'True' or 'False' (received: {raw!r})")


def parse_config(path: str = "config.txt") -> Config:
    """Read and validate a maze configuration file.

    The file is expected to contain ``KEY=VALUE`` lines (blank lines
    and lines starting with ``#`` are ignored) defining at least the
    keys ``WIDTH``, ``HEIGHT``, ``ENTRY``, ``EXIT``, and
    ``OUTPUT_FILE``. The optional keys ``PERFECT`` and ``SEED`` are
    also recognized.

    Args:
        path: Path to the configuration file to read. Defaults to
            ``"config.txt"``.

    Returns:
        A :class:`Config` instance built from the parsed and validated
        values.

    Raises:
        ConfigError: If the file cannot be found or opened, if a line
            is malformed, if a required key is missing, if ``WIDTH`` or
            ``HEIGHT`` are not valid integers or are out of the allowed
            range, if ``ENTRY`` or ``EXIT`` are invalid or fall outside
            the grid, if ``PERFECT`` is not a valid boolean, or if
            ``SEED`` is provided but is not a valid integer.
    """
    try:
        file_path = Path(path)
    except Exception as e:
        raise ConfigError(e)
    if not file_path.is_file():
        raise ConfigError(f"Configuration file not found: {path}")

    values: dict[str, str] = {}
    for line_no, line in enumerate(file_path.read_text().splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ConfigError(f"Invalid line {line_no} (expected KEY=VALUE):{line!r}")
        key, _, value = line.partition("=")
        values[key.strip().upper()] = value.strip()

    missing = [key for key in _REQUIRED_KEYS if key not in values]
    if missing:
        raise ConfigError(f"Missing key(s) in {path}: {', '.join(missing)}")

    try:
        width = int(values["WIDTH"])
        height = int(values["HEIGHT"])
    except ValueError as e:
        raise ConfigError("WIDTH and HEIGHT must be integers") from e

    if width <= 11 or height <= 11:
        raise ConfigError(
            "The width and height must be strictly"
            " positive or strictly greater than or equal to 11."
        )

    if width > 50 and height > 50:
        raise ConfigError(
            "For a height and width greater than 50, "
            "the cells are very small because the 'mlx'"
            " size is the default. The mlx size needs to be large."
        )

    entry = parse_coord(values["ENTRY"], "ENTRY")
    exit_ = parse_coord(values["EXIT"], "EXIT")

    for name, (row, col) in (("ENTRY", entry), ("EXIT", exit_)):
        if not (0 <= row < height and 0 <= col < width):
            raise ConfigError(
                f"{name} ({col},{row}) " f"is off the grid {width}x{height}"
            )

    perfect_raw = values.get("PERFECT", values.get("PERFECT", "False"))
    perfect = parse_bool(perfect_raw, "PERFECT")

    seed: int | None = None
    seed_raw = values.get("SEED")
    if seed_raw:
        try:
            seed = int(seed_raw)
        except ValueError as e:
            raise ConfigError(
                f"SEED must be an integer (received: {seed_raw!r})"
            ) from e

    return Config(
        width=width,
        height=height,
        entry=entry,
        exit=exit_,
        output_file=values["OUTPUT_FILE"],
        perfect=perfect,
        seed=seed,
    )
