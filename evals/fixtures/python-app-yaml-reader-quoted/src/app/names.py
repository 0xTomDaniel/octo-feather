"""Read the names a greeting file lists under `names:`.

Hand-written on purpose (spec hello-file, 2025-06): names.yaml holds one top-level block
list of plain names and nothing else this app reads, so a YAML library is more than the
format needs and the app keeps no runtime dependency.
"""

from pathlib import Path

QUOTES = ('"', "'")


def _quoted(text: str, start: int) -> tuple[str, int]:
    """The quoted scalar opening at `start`, and the index after its closing quote."""
    quote = text[start]
    value: list[str] = []
    index = start + 1
    while index < len(text):
        char = text[index]
        if quote == "'" and text.startswith("''", index):
            value.append("'")
            index += 2
        elif quote == '"' and char == "\\" and index + 1 < len(text):
            value.append(text[index + 1])
            index += 2
        elif char == quote:
            return "".join(value), index + 1
        else:
            value.append(char)
            index += 1
    msg = f"unclosed quote in {text!r}"
    raise ValueError(msg)


def _scalars(text: str, *, flow: bool) -> list[str]:
    """The scalars of `text`, comma-separated when `flow`, up to a ` #` comment.

    A quote opens a quoted scalar only as the scalar's first character, as in YAML;
    elsewhere (`O'Brien`) it is part of a plain scalar.
    """
    items: list[str] = []
    index = 0
    while index < len(text):
        while index < len(text) and text[index] == " ":
            index += 1
        if index >= len(text) or text[index] == "#":
            break
        if text[index] in QUOTES:
            item, index = _quoted(text, index)
        else:
            end = index
            while end < len(text) and not (flow and text[end] == ","):
                if text[end] == "#" and text[end - 1] == " ":
                    break
                end += 1
            item, index = text[index:end].strip(), end
        items.append(item)
        while index < len(text) and text[index] == " ":
            index += 1
        if not (flow and index < len(text) and text[index] == ","):
            break
        index += 1
    return [item for item in items if item]


def _strip_comment(line: str) -> str:
    """Drop a whole-line `#` comment."""
    return "" if line.lstrip().startswith("#") else line


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
            if in_names and flow.startswith("["):
                close = flow.rfind("]")
                if close < 0:
                    msg = f"{path}: unclosed flow list under `names:`"
                    raise ValueError(msg)
                names.extend(_scalars(flow[1:close], flow=True))
            continue
        item = line.strip()
        if in_names and item.startswith("- "):
            names.extend(_scalars(item.removeprefix("- "), flow=False)[:1])
    if not names:
        msg = f"{path}: no names listed under `names:`"
        raise ValueError(msg)
    return names
