#!/usr/bin/env python3
"""The post-merge routine's run order: a lane's steps run in order, each one's outcome reported.

The routine and its steps: `octo-feather-lane --help`, post-merge (the rule: issue-lifecycle spec
#gates-main-moved). Imported by scripts/octo-feather-lane (`post-merge`), which passes the steps
in: this module never imports the command. How a command finds it: the docstring of
scripts/correction_lanes.py. Standard library only (AGENTS.md Rules, kit scripts).

Interface:

    run(pm, steps, show) -> list[Step]
        STEPS the routine's (name, function) pairs in order; each function takes PM and returns
        its outcome (ok, stopped or pending) and its line. A step runs only while every step
        before it is ok (octo-feather-lane --help, post-merge); SHOW gets each Step as it
        finishes. The Steps run, in order.
"""

__all__ = ["Body", "Outcome", "Step", "run"]

import datetime as dt
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Literal, TypeVar

Outcome = Literal["ok", "stopped", "pending"]
M = TypeVar("M")
R = TypeVar("R")
Body = Callable[[M], R]  # a step's function of the run's state M


@dataclass(frozen=True)
class Step:
    """One step's outcome: its number (1 first), name, outcome, line and UTC time."""

    number: int
    name: str
    outcome: Outcome
    line: str
    at: str


def run(
    pm: M,
    steps: Sequence[tuple[str, Body[M, tuple[Outcome, str]]]],
    show: Callable[[Step], None],
) -> list[Step]:
    """The steps in order, each while every step before it is ok (the module docstring)."""
    done: list[Step] = []
    for n, (name, step) in enumerate(steps, 1):
        if done and done[-1].outcome != "ok":
            break
        outcome, line = step(pm)
        at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        done.append(Step(n, name, outcome, line, at))
        show(done[-1])
    return done
