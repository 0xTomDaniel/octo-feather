#!/usr/bin/env python3
"""Existing handoff JSONL encoding and line-isolated reading, using kit stdlib json."""

import json
from pathlib import Path
from typing import cast


def encode(record: dict[str, object]) -> str:
    """Encode every field without imposing a handoff schema."""
    return json.dumps(record, ensure_ascii=False)


def read_log(path: Path) -> tuple[list[dict[str, object]], list[int]]:
    """The hand-off log's JSON object lines, and numbers of lines that are not one."""
    lines: list[dict[str, object]] = []
    bad: list[int] = []
    for i, line in enumerate(path.read_bytes().splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except ValueError:
            record = None
        if isinstance(record, dict):
            lines.append(cast("dict[str, object]", record))
        else:
            bad.append(i)
    return lines, bad
