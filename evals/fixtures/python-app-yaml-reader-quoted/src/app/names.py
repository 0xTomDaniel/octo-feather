"""Read the names a greeting file lists under `names:`.

Hand-written on purpose (spec hello-file, 2025-06): names.yaml holds one top-level block
list of plain names and nothing else this app reads, so a YAML library is more than the
format needs and the app keeps no runtime dependency.
"""

from pathlib import Path

QUOTES = ('"', "'")


def _strip_comment(line: str) -> str:
    """Drop a `#` comment that is outside quotes."""
    quote = ""
    for index, char in enumerate(line):
        if quote:
            if char == quote:
                quote = ""
        elif char in QUOTES:
            quote = char
        elif char == "#" and (index == 0 or line[index - 1].isspace()):
            return line[:index]
    return line


def _scalar(text: str) -> str:
    """A plain, single-quoted or double-quoted scalar's value."""
    value = text.strip()
    if len(value) >= 2 and value[0] in QUOTES and value[-1] == value[0]:  # noqa: PLR2004
        inner = value[1:-1]
        if value[0] == "'":
            return inner.replace("''", "'")
        return inner.replace('\\"', '"').replace("\\\\", "\\")
    return value


def read_names(path: Path) -> list[str]:
    """Return the items of the file's top-level `names:` sequence, block or flow style."""
    names: list[str] = []
    in_names = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = _strip_comment(raw).rstrip()
        if not line.strip():
            continue
        if not line[0].isspace():
            key, _, rest = line.partition(":")
            in_names = key == "names"
            flow = rest.strip()
            if in_names and flow.startswith("[") and flow.endswith("]"):
                names.extend(_scalar(item) for item in flow[1:-1].split(",") if item.strip())
            continue
        item = line.strip()
        if in_names and item.startswith("- "):
            names.append(_scalar(item.removeprefix("- ")))
    if not names:
        msg = f"{path}: no names listed under `names:`"
        raise ValueError(msg)
    return names
