import tomllib
from pathlib import Path

REQUIRED = ("name", "greeting")


def missing_keys(path: Path) -> list[str]:
    with path.open("rb") as f:
        data = tomllib.load(f)
    return [key for key in REQUIRED if key not in data]
