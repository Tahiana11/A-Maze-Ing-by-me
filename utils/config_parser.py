from dataclasses import dataclass
from pathlib import Path

_REQUIRED_KEYS = ("WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE")


class ConfigError(Exception):
    ...


@dataclass
class Config:
    width: int
    height: int
    entry: tuple[int, int]
    exit: tuple[int, int]
    output_file: str
    perfect: bool = False


def parse_coord(raw: str, key: str) -> tuple[int, int]:
    parts = raw.split(",")
    if len(parts) != 2:
        raise ConfigError(f"{key} must be in x,y format (received: {raw!r})")
    try:
        x, y = (int(p.strip()) for p in parts)
    except ValueError as e:
        raise ConfigError(f"{key} must contain "
                          f"integers (received: {raw!r})") from e
    return (y, x)


def parse_bool(raw: str, key: str = "PERFECT") -> bool:
    normalized = raw.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ConfigError(
        f"{key} must be 'True' or 'False' (received: {raw!r})"
    )


def parse_config(path: str = "config.txt") -> Config:
    file_path = Path(path)
    if not file_path.is_file():
        raise ConfigError(f"Configuration file not found: {path}")

    values: dict[str, str] = {}
    for line_no, line in enumerate(
        file_path.read_text().splitlines(), start=1
    ):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ConfigError(
                f"Invalid line {line_no} (expected KEY=VALUE):{line!r}"
            )
        key, _, value = line.partition("=")
        values[key.strip().upper()] = value.strip()

    missing = [key for key in _REQUIRED_KEYS if key not in values]
    if missing:
        raise ConfigError(
            f"Missing key(s) in {path}: {', '.join(missing)}"
        )

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

    # if width > 50 and height > 50:
    #     raise ConfigError(
    #         "For a height and width greater than 50, "
    #         "the cells are very small because the 'mlx'"
    #         " size is the default. The mlx size needs to be large."
    #     )

    entry = parse_coord(values["ENTRY"], "ENTRY")
    exit_ = parse_coord(values["EXIT"], "EXIT")

    for name, (row, col) in (("ENTRY", entry), ("EXIT", exit_)):
        if not (0 <= row < height and 0 <= col < width):
            raise ConfigError(f"{name} ({col},{row}) "
                              f"is off the grid {width}x{height}")

    perfect_raw = values.get("PERFECT", values.get("PREFECT", "False"))
    perfect = parse_bool(perfect_raw, "PERFECT")

    return Config(
        width=width,
        height=height,
        entry=entry,
        exit=exit_,
        output_file=values["OUTPUT_FILE"],
        perfect=perfect,
    )
