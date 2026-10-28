"""tests/lint.sh's assertion that octo-feather-lint shrink never grows a baseline (#244).

Run in the target repo: `python3 baseline_grew.py`. Compares each baseline in the working tree
with its last commit (HEAD): the ruff tables of pyproject.toml
([tool.ruff.lint.extend-per-file-ignores], [tool.ruff.format] exclude) and basedpyright's
.basedpyright/baseline.json, each entry counted. Exit 1 naming every entry the working tree holds
more of than HEAD; exit 0 when nothing grew.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import cast

import tomllib

PYPROJECT = "pyproject.toml"
PYRIGHT = ".basedpyright/baseline.json"


def head(path: str) -> str:
    r = subprocess.run(
        ["git", "show", f"HEAD:{path}"],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    )
    return r.stdout if r.returncode == 0 else ""


def sub(node: object, *keys: str) -> object:
    for key in keys:
        node = cast("dict[str, object]", node).get(key, {}) if isinstance(node, dict) else {}
    return node


def ruff_entries(text: str) -> Counter[str]:
    data = tomllib.loads(text) if text else {}
    table = sub(data, "tool", "ruff", "lint", "extend-per-file-ignores")
    lint = cast("dict[str, list[str]]", table)
    fmt = cast("list[str]", sub(data, "tool", "ruff", "format", "exclude") or [])
    found = Counter(f"ruff check {path} {code}" for path, codes in lint.items() for code in codes)
    found.update(f"ruff format {path}" for path in fmt)
    return found


def pyright_entries(text: str) -> Counter[str]:
    files = cast("dict[str, list[object]]", sub(json.loads(text) if text else {}, "files"))
    return Counter(
        f"basedpyright {path} {json.dumps(error, sort_keys=True)}"
        for path, errors in files.items()
        for error in errors
    )


def main() -> int:
    now = ruff_entries(Path(PYPROJECT).read_text(encoding="utf-8"))
    then = ruff_entries(head(PYPROJECT))
    pyright = Path(PYRIGHT)
    now += pyright_entries(pyright.read_text(encoding="utf-8") if pyright.is_file() else "")
    then += pyright_entries(head(PYRIGHT))
    grown = sorted((now - then).elements())
    if grown:
        sys.stderr.write("".join(f"baseline grew: {entry}\n" for entry in grown))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
