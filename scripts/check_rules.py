#!/usr/bin/env python3
"""The kit's check rules: each a function of a repo dir and its tracked files, returning a Report.

A kit module, imported by name, never loaded by file path: by its command (scripts/check-dashes;
how: correction_lanes.py's docstring) and by tests (how: pyproject.toml, [tool.pytest.ini_options]
pythonpath). Standard library only (AGENTS.md Rules, kit scripts).

Interface:

    check_dashes(root, tracked) -> Report
        The dash rule (#121 D7): no line of a tracked file holds an en dash (U+2013) or an em dash
        (U+2014), outside its carve-outs: docs/specs/.viz/, docs/specs/.style/, .agents/skills/NAME/
        for each Skillfile `github` entry (NAME its third field), .skillfile/ and the root LICENSE.
        ROOT the repo dir, its Skillfile and files read under it; TRACKED its `git ls-files` paths,
        in git's order. Each hit an out line `path:n:line` (the line's bytes as read); then the err
        line asking for the fix, code 1. A file in scope that cannot be read: an err line naming
        it, code 1, never ok (fail closed). Else the out line `dashes: ok (N files)`, N the files in
        scope, code 0. A Skillfile that cannot be read raises OSError.
    Report: the exact lines the command prints, each with its stream, in order (no newline), and
        the exit code.
"""

__all__ = ["Report", "Stream", "check_dashes"]

import os
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Stream = Literal["out", "err"]


@dataclass(frozen=True)
class Report:
    lines: tuple[tuple[Stream, bytes], ...]
    code: int


# En and em dash, as bytes, so this file passes the scan it holds.
DASHES = (b"\xe2\x80\x93", b"\xe2\x80\x94")


def check_dashes(root: Path, tracked: Sequence[str]) -> Report:
    skillfile = (root / "Skillfile").read_text(encoding="utf-8")
    entries = (line.split() for line in skillfile.splitlines())
    vendored = tuple(f".agents/skills/{e[2]}/" for e in entries if e[:1] == ["github"] and e[2:])
    skip = ("docs/specs/.viz/", "docs/specs/.style/", ".skillfile/", *vendored)
    files = [p for p in tracked if p != "LICENSE" and not p.startswith(skip)]
    lines: list[tuple[Stream, bytes]] = []
    hit = unread = False
    for path in files:
        try:
            text = (root / path).read_bytes()
        except OSError as e:
            why = f"check-dashes: cannot read {path}: {e.strerror}; the check cannot pass"
            lines.append(("err", why.encode()))
            unread = True
            continue
        rows = text.split(b"\n")
        if rows[-1] == b"":
            rows.pop()  # the final newline ends the last line, it is not a line
        for n, row in enumerate(rows, 1):
            if any(d in row for d in DASHES):
                lines.append(("out", os.fsencode(path) + f":{n}:".encode() + row))
                hit = True
    if hit:
        fix = b"check-dashes: replace the em/en dashes above with a colon, comma or parentheses"
        lines.append(("err", fix))
    elif not unread:
        lines.append(("out", f"dashes: ok ({len(files)} files)".encode()))
    return Report(tuple(lines), 1 if hit or unread else 0)
