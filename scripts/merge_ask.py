#!/usr/bin/env python3
"""The merge ask's rules: a PR's facts read once into a Snapshot, judged by a pure check.

The design: issue #1146 (its design comment); the rules: issue-lifecycle spec #gates-pr-line,
the merge ask (octo-feather-lane --help, merge-ask). Imported by scripts/octo-feather-lane
(`merge-ask` builds one snapshot and adds check's gaps to its own); how a command finds this
module: the docstring of scripts/correction_lanes.py. Standard library only (AGENTS.md Rules,
kit scripts). The merge ask's other rules are still in octo-feather-lane's cmd_merge_ask.

Interface:

    snapshot(body, branch) -> Snapshot
        The one reader: the PR's BODY and head BRANCH as gh printed them, and what the tracker
        skill's key-from-branch BRANCH and pr-line KEY printed (ParentLine) or its refusal
        (NoParent); the real tracker scripts of the target's tracker skill (tracker_calls).
    check(s) -> Ask
        Pure, no I/O: Ask.gaps, each refusal line the merge ask prints for S, in order; none
        when S passes.
"""

__all__ = ["Ask", "NoParent", "ParentLine", "Snapshot", "check", "snapshot"]

import re
from dataclasses import dataclass

from tracker_calls import tracker

# GitHub's closing keywords: a PR body line with one closes that GitHub issue at merge, named
# as #N, as owner/repo#N or by the issue URL.
CLOSES = re.compile(
    r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\b:?\s+"
    r"(?:[\w.-]+/[\w.-]+#|https?://(?:www\.)?github\.com/[\w.-]+/[\w.-]+/issues/|#)(\d+)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ParentLine:
    """The lane's parent as the tracker skill names it: KEY (key-from-branch), LINE (pr-line)."""

    key: str
    line: str


@dataclass(frozen=True)
class NoParent:
    """The tracker skill refused to name the parent: WHY, its error as tracker_calls words it."""

    why: str


@dataclass(frozen=True)
class Snapshot:
    """A PR's facts, read once: its BODY, head BRANCH and the PARENT the tracker skill names."""

    body: str
    branch: str
    parent: ParentLine | NoParent


@dataclass(frozen=True)
class Ask:
    """The merge ask's verdict on a Snapshot: GAPS, each refusal line; none when it passes."""

    gaps: list[str]


class _TrackerError(Exception):
    """A tracker script's refusal, kept as NoParent."""


def snapshot(body: str, branch: str) -> Snapshot:
    try:
        key = tracker("key-from-branch", branch, err=_TrackerError).strip()
        line = tracker("pr-line", key, err=_TrackerError).strip()
    except _TrackerError as e:
        return Snapshot(body, branch, NoParent(str(e)))
    return Snapshot(body, branch, ParentLine(key, line))


def check(s: Snapshot) -> Ask:
    return Ask(parent_line(s))


def parent_line(s: Snapshot) -> list[str]:
    """Spec #gates-pr-line: the body carries the tracker skill's pr-line for the lane's parent
    (the key its key-from-branch reads from the PR branch), and closes no other GitHub issue."""
    if isinstance(s.parent, NoParent):
        return [
            (
                f"parent line: cannot name it for branch {s.branch!r} ({s.parent.why}); "
                "push the lane from its lane branch (docs/adr/0011)"
            )
        ]
    key, want = s.parent.key, s.parent.line
    lines = [ln.strip() for ln in s.body.splitlines()]
    got = [
        ln
        for ln in lines
        if ln == want
        or (ln.startswith(want) and not re.match(r"[\w-]", ln[len(want) : len(want) + 1]))
    ]
    out = (
        []
        if got
        else [
            (
                f"parent line: missing; add the line `{want}` "
                f"(the tracker skill's pr-line {key}) to the PR body"
            )
        ]
    )
    for ln in lines:
        for m in CLOSES.finditer(ln):
            if ln in got and m.end() <= len(want):
                # the parent line's own closing link (GitHub: Closes #<parent>), never the rest
                # of its line
                continue
            out.append(
                f"parent line: `{ln[:80]}` closes GitHub issue #{m.group(1)}, "
                f"not the lane's parent line `{want}`; remove it (the supervisor's close moves "
                "each ticket to done with the tracker skill's issue-done)"
            )
    return out
