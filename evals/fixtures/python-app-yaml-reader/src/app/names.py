"""Read the names a greeting file lists under `names:`.

Hand-written on purpose (spec hello-file, 2025-06): names.yaml holds one top-level block
list of plain names and nothing else this app reads, so a YAML library is more than the
format needs and the app keeps no runtime dependency.
"""

from pathlib import Path


def read_names(path: Path) -> list[str]:
    """Return the `- NAME` items of the file's top-level `names:` block sequence."""
    names: list[str] = []
    in_names = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        if not line[0].isspace():
            in_names = line.rstrip() == "names:"
            continue
        item = line.strip()
        if in_names and item.startswith("- "):
            names.append(item.removeprefix("- ").strip())
    if not names:
        msg = f"{path}: no names listed under `names:`"
        raise ValueError(msg)
    return names
