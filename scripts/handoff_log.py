#!/usr/bin/env python3
"""Existing handoff JSONL encoding and line-isolated reading, using kit stdlib json."""

import json
from pathlib import Path
from typing import cast

# The identity fields every reader keys on (a line's kind and time, the agent's name, role, pane and
# Pi session id): a string wherever a line has one (quality #acceptance-edge-validated, #1131). A
# hand-written check: kit scripts stay stdlib-only, and the log's other fields are open per kind.
STRINGS = ("kind", "at", "name", "role", "pane", "session")


class MalformedLineError(ValueError):
    """A hand-off log line whose field has the wrong type: names the file, line number and field."""

    def __init__(self, path: Path, line: int, field: str, value: object) -> None:
        super().__init__(
            f"{path} line {line}: field {field} is {type(value).__name__}, not a string:"
            f" fix that line, then rerun"
        )


def encode(record: dict[str, object]) -> str:
    """Encode every field without imposing a handoff schema."""
    return json.dumps(record, ensure_ascii=False)


def read_log(path: Path) -> tuple[list[dict[str, object]], list[int]]:
    """The hand-off log's JSON object lines, and numbers of lines that are not one;
    MalformedLineError on an object line whose STRINGS field is not a string."""
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
            record = cast("dict[str, object]", record)
            for field in STRINGS:
                if field in record and not isinstance(record[field], str):
                    raise MalformedLineError(path, i, field, record[field])
            lines.append(record)
        else:
            bad.append(i)
    return lines, bad
