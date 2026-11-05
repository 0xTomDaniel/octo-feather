from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Counts:
    path: str
    words: int


def count(path: Path) -> Counts:
    text = path.read_text(encoding="utf-8")
    return Counts(path=str(path), words=len(text.split()))
