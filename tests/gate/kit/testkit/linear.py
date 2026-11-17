#!/usr/bin/env python3
"""Fake `linear` (the testkit's stand-in for Linear, which the kit does not own, at the CLI the
linear tracker skill runs: schpet/linear-cli at its cli-version pin, v3.1.0): a tape replayer,
never a simulator (the tdd skill, mocking.md). A scenario puts this dir first on PATH. Each call
appends one line to $FAKE_LINEAR/log, the JSON list [ARGV, STDIN] (STDIN read only when an
argument is `-`, else null), and answers from the tape $FAKE_LINEAR/tape.json:

  {"source": TEXT, "calls": [{"argv": [ARG, ...], "stdin": TEXT or null, "answers": [ANSWER, ...]}]}
  ANSWER  {"rc": N, "err": TEXT, and "out": TEXT or "json": VALUE}: its exit status, stderr and
          stdout; a VALUE printed as linear-cli prints a piped `api` response: compact, one line.

The Nth time a call is made it gets the tape's Nth answer for it (the last, once they run out):
what Linear answered that call each time, in order. A call no tape records, or a tape field
missing, unknown or of the wrong type, exits 2 naming it.
"""

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn, cast


@dataclass(frozen=True)
class Answer:
    rc: int
    out: str
    err: str


@dataclass(frozen=True)
class Call:
    argv: list[str]
    stdin: str | None
    answers: list[Answer]


def bad(where: str, why: str) -> NoReturn:
    sys.stderr.write(f"fake linear: tape {where}: {why}\n")
    sys.exit(2)


def obj(d: object, where: str, need: tuple[str, ...], may: tuple[str, ...] = ()) -> dict[str, Any]:
    """D, a JSON object with every field in NEED and no field outside NEED and MAY."""
    if not isinstance(d, dict):
        bad(where, "not an object")
    o = cast("dict[str, Any]", d)
    for k in sorted(set(o) - set(need) - set(may)):
        bad(where, f"unknown field {k}")
    for k in need:
        if k not in o:
            bad(where, f"missing field {k}")
    return o


def answer(d: object, where: str) -> Answer:
    a = obj(d, where, ("rc", "err"), ("out", "json"))
    if type(a["rc"]) is not int:
        bad(f"{where}.rc", "not an integer")
    if ("out" in a) == ("json" in a):
        bad(where, "wants one of out and json")
    for k in ("err", "out"):
        if not isinstance(a.get(k, ""), str):
            bad(f"{where}.{k}", "not text")
    out = a["out"] if "out" in a else json.dumps(a["json"], separators=(",", ":")) + "\n"
    return Answer(a["rc"], out, a["err"])


def call(d: object, where: str) -> Call:
    c = obj(d, where, ("argv", "stdin", "answers"))
    argv = cast("list[object]", c["argv"]) if isinstance(c["argv"], list) else None
    if argv is None or not all(isinstance(x, str) for x in argv):
        bad(f"{where}.argv", "not a list of text")
    if not (c["stdin"] is None or isinstance(c["stdin"], str)):
        bad(f"{where}.stdin", "not text or null")
    given = cast("list[object]", c["answers"]) if isinstance(c["answers"], list) else []
    if not given:
        bad(f"{where}.answers", "not a list of answers")
    answers = [answer(a, f"{where}.answers[{j}]") for j, a in enumerate(given)]
    return Call(cast("list[str]", argv), c["stdin"], answers)


def tape(p: Path) -> list[Call]:
    t = obj(json.loads(p.read_text()), str(p), ("source", "calls"))
    if not isinstance(t["calls"], list):
        bad(f"{p} calls", "not a list")
    return [call(c, f"{p} calls[{i}]") for i, c in enumerate(cast("list[object]", t["calls"]))]


d = Path(os.environ.get("FAKE_LINEAR") or sys.exit("fake linear: FAKE_LINEAR unset"))
calls = tape(d / "tape.json")
argv = sys.argv[1:]
stdin = sys.stdin.read() if "-" in argv else None
asked = [argv, stdin]
log = d / "log"
before = log.read_text().splitlines().count(json.dumps(asked)) if log.exists() else 0
with log.open("a") as f:
    f.write(json.dumps(asked) + "\n")
hit = next((c for c in calls if [c.argv, c.stdin] == asked), None)
if hit is None:
    sys.stderr.write(f"fake linear: no recording for linear {json.dumps(argv)} stdin {stdin!r}\n")
    sys.exit(2)
a = hit.answers[min(before, len(hit.answers) - 1)]
sys.stdout.write(a.out)
sys.stderr.write(a.err)
sys.exit(a.rc)
