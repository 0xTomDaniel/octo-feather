#!/usr/bin/env python3
"""The merge ask's rules: a PR's facts read once into a Snapshot, judged by a pure check.

The design: issue #1146 (its design comment); the rules: issue-lifecycle spec #gates-pr-line,
the merge ask (octo-feather-lane --help, merge-ask). Imported by scripts/octo-feather-lane
(`merge-ask` builds one snapshot and adds check's gaps to its own); how a command finds this
module: the docstring of scripts/correction_lanes.py. Standard library only (AGENTS.md Rules,
kit scripts). The merge ask's other rules are still in octo-feather-lane's cmd_merge_ask.

Interface:

    snapshot(body, branch, lane) -> Snapshot
        The one reader: the PR's BODY and head BRANCH as gh printed them, and what the tracker
        skill's key-from-branch BRANCH and pr-line KEY printed (ParentLine) or its refusal
        (NoParent); the real tracker scripts of the target's tracker skill (tracker_calls).
        Spec #gates-merge-order, for LANE (Lane): every other open PR on its base branch (gh pr
        list), its head fetched (git fetch origin pull/N/head) when this repo lacks it, git
        merge-tree of the lane's head and it, the octo-feather-qa --verdict pins its qc.toml
        demos name at its head, and that command's lines for them at the base and at the base
        merged with the lane's head (a commit-tree, no ref moved), each run in a detached
        scratch worktree (Order).
    check(s) -> Ask
        Pure, no I/O: Ask.gaps, each refusal line the merge ask prints for S, in order; none
        when S passes. Ask.order, the merge-order lines it shows (spec #gates-merge-order),
        never a gap.
"""

__all__ = [
    "Ask",
    "Lane",
    "NoParent",
    "Order",
    "ParentLine",
    "Pin",
    "Sibling",
    "Snapshot",
    "check",
    "snapshot",
]

import json
import os
import re
import shlex
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

import tomllib
from tracker_calls import KIT, gh, tracker

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


# The other open PRs this lane's merge would set back, shown only (spec #gates-merge-order)


@dataclass(frozen=True)
class Pin:
    """A stored eval run an open PR's qc.toml demo pins (RUN_ID/SUITE/CASE, RUN), and the line
    octo-feather-qa --verdict printed for it at the base (MAIN) and at the base merged with this
    lane's head (MERGED)."""

    run: str
    main: str
    merged: str


@dataclass(frozen=True)
class Sibling:
    """Another open PR: NUMBER, head BRANCH, the files git merge-tree finds in conflict between its
    head and this lane's (CONFLICTS), and the runs its demos pin (PINS)."""

    number: int
    branch: str
    conflicts: list[str]
    pins: list[Pin]


@dataclass(frozen=True)
class Order:
    """The other open PRs on BASE (PRS, by number), and each read that failed (UNREAD), one line."""

    base: str
    prs: list[Sibling]
    unread: list[str]


@dataclass(frozen=True)
class Snapshot:
    """A PR's facts, read once: its BODY, head BRANCH and the PARENT the tracker skill names;
    ORDER, the other open PRs (spec #gates-merge-order), None when not read."""

    body: str
    branch: str
    parent: ParentLine | NoParent
    order: Order | None = None


@dataclass(frozen=True)
class Ask:
    """The merge ask's verdict on a Snapshot: GAPS, each refusal line; none when it passes.
    ORDER, the merge-order lines shown beside it, never a gap."""

    gaps: list[str]
    order: list[str] = field(default_factory=list[str])


class _TrackerError(Exception):
    """A tracker script's refusal, kept as NoParent."""


class _UnreadError(Exception):
    """A merge-order read that failed, kept as one Order.unread line."""


@dataclass(frozen=True)
class Lane:
    """This lane's PR as the merge ask reads it: its NUMBER, HEAD oid, BASE_BRANCH (gh's
    baseRefName), BASE (the ref its commits are read against: origin/<base branch> or --base)
    and REPO (--repo; None, this directory's)."""

    number: int
    head: str
    base_branch: str
    base: str
    repo: str | None


def snapshot(body: str, branch: str, lane: Lane) -> Snapshot:
    order = _order(lane)
    try:
        key = tracker("key-from-branch", branch, err=_TrackerError).strip()
        line = tracker("pr-line", key, err=_TrackerError).strip()
    except _TrackerError as e:
        return Snapshot(body, branch, NoParent(str(e)), order)
    return Snapshot(body, branch, ParentLine(key, line), order)


def check(s: Snapshot) -> Ask:
    return Ask(parent_line(s), merge_order(s.order) if s.order else [])


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


# The merge-order rule, pure (spec #gates-merge-order)

# The freshness tail of an octo-feather-qa --verdict line (its --help, Verdict): fresh, stale with
# each stale item, or missing with why.
FRESHNESS = re.compile(
    r"^\S+ \S+: stored \S+, run \S+, kit \S+, [^;]*; "
    r"(?:fresh at HEAD \w+|stale at HEAD \w+: (?P<stale>.*)|missing: .*)$"
)


def _stale(line: str) -> list[str] | None:
    """The stale items LINE names (none when fresh); None when it judged no freshness."""
    m = FRESHNESS.match(line)
    if m is None or line.split("; ", 1)[1].startswith("missing: "):
        return None
    return m.group("stale").split("; ") if m.group("stale") else []


def merge_order(o: Order) -> list[str]:
    """Spec #gates-merge-order: each other open PR whose pinned runs fresh on the base go stale
    with this lane merged in (the items octo-feather-qa names stale only then), and each whose
    head conflicts with this lane's head; shown only, never a gap."""
    out: list[str] = []
    for p in o.prs:
        who = f"PR #{p.number} ({p.branch})"
        if p.conflicts:
            out.append(f"- {who}: its head conflicts with this head in {', '.join(p.conflicts)}")
        for pin in p.pins:
            was, now = _stale(pin.main), _stale(pin.merged)
            if was is None or now is None:
                said = pin.main if was is None else pin.merged
                out.append(f"- not read: {who} pinned run {pin.run}: octo-feather-qa said {said}")
            elif new := [x for x in now if x not in was]:
                out.append(f"- {who}: this merge stales its pinned run {pin.run}: {'; '.join(new)}")
    out += [f"- not read: {u}" for u in o.unread]
    if not out:
        n = len(o.prs)
        out = [
            (
                f"- none: {n} other open pull request{'s' * (n != 1)} on {o.base}, none this "
                "merge would stale or conflict with"
            )
        ]
    head = (
        "Merge order (issue-lifecycle #gates-merge-order; shown only: this merge ask passes or "
        "fails the same without it):"
    )
    return [head, *out]


# The merge-order reads (spec #gates-merge-order)

QA = KIT / "scripts" / "octo-feather-qa"
SHELL_OPS = {";", "&&", "||", "|", "&", "(", ")"}
IDENT = {
    f"GIT_{who}_{k}": v
    for who in ("AUTHOR", "COMMITTER")
    for k, v in (("NAME", "merge-ask"), ("EMAIL", "merge-ask@localhost"))
}


def _git(*args: str, ok: tuple[int, ...] = (0,)) -> tuple[int, str]:
    """git ARGS in the current repo: (exit, stdout); _UnreadError naming it on another exit."""
    p = subprocess.run(
        ["git", *args],  # noqa: S607 (git from PATH, as the command runs it)
        capture_output=True,
        text=True,
        env={**os.environ, **IDENT},
        check=False,
    )
    if p.returncode not in ok:
        said = (p.stderr or p.stdout).strip().splitlines()
        msg = f"git {' '.join(args[:2])} failed ({said[-1][:200] if said else p.returncode})"
        raise _UnreadError(msg)
    return p.returncode, p.stdout


def _pins(command: str) -> list[str]:
    """The RUN_ID/SUITE/CASE arguments of each `octo-feather-qa --verdict` in shell COMMAND."""
    lex = shlex.shlex(command, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    words = list(lex)
    out: list[str] = []
    for i, w in enumerate(words[:-1]):
        if Path(w).name == "octo-feather-qa" and words[i + 1] == "--verdict":
            for a in words[i + 2 :]:
                if a.startswith("-") or a in SHELL_OPS:
                    break
                out.append(a)
    return out


def _demo_pins(oid: str) -> list[str]:
    """The pins of every qc.toml demo at commit OID; none without a qc.toml there."""
    rc, text = _git("show", f"{oid}:qc.toml", ok=(0, 128))
    if rc:
        return []
    try:
        demos: object = tomllib.loads(text).get("demo", {})
        cmds = [
            cast("dict[str, object]", c).get("command")
            for c in cast("dict[str, object]", demos).values()
            if isinstance(c, dict)
        ]
        return list(dict.fromkeys(p for c in cmds if isinstance(c, str) for p in _pins(c)))
    except (tomllib.TOMLDecodeError, ValueError, AttributeError) as e:
        msg = f"qc.toml at {oid[:12]} not parsed ({e})"
        raise _UnreadError(msg) from e


def _merge_tree(ours: str, theirs: str) -> tuple[str, list[str]]:
    """(the tree git merge-tree writes for OURS and THEIRS, the files in conflict)."""
    rc, out = _git(
        "merge-tree", "--write-tree", "--name-only", "--no-messages", ours, theirs, ok=(0, 1)
    )
    lines = out.splitlines()
    if not lines or not re.fullmatch(r"[0-9a-f]{40,64}", lines[0]):
        msg = f"git merge-tree of {ours[:12]} and {theirs[:12]} printed no tree"
        raise _UnreadError(msg)
    return lines[0], list(dict.fromkeys(lines[1:])) if rc else []


def _merged(base: str, head: str, name: str) -> str:
    """A commit of BASE (NAME) merged with HEAD (git merge-tree, then commit-tree: no ref moved)."""
    tree, conflicts = _merge_tree(base, head)
    if conflicts:
        msg = f"this head does not merge cleanly with {name} ({', '.join(conflicts)})"
        raise _UnreadError(msg)
    return _git("commit-tree", tree, "-p", base, "-p", head, "-m", f"merge-ask: {name} + head")[
        1
    ].strip()


def _verdicts(rev: str, pins: list[str]) -> list[str]:
    """octo-feather-qa --verdict PINS, run in a scratch detached worktree at REV: a line per pin."""
    with tempfile.TemporaryDirectory(prefix="merge-ask-order-") as tmp:
        wt = str(Path(tmp) / "wt")
        _git("worktree", "add", "-q", "--detach", wt, rev)
        try:
            p = subprocess.run(
                [str(QA), "--verdict", *pins], capture_output=True, text=True, cwd=wt, check=False
            )
        finally:
            _git("worktree", "remove", "--force", wt, ok=(0, 128))
    lines = p.stdout.splitlines()
    if p.returncode not in (0, 1, 77) or len(lines) != len(pins):
        said = p.stderr.strip().splitlines()
        msg = (
            f"octo-feather-qa --verdict at {rev[:12]} exited {p.returncode}"
            f" ({said[-1][:200] if said else 'no error line'})"
        )
        raise _UnreadError(msg)
    return lines


def _open_prs(lane: Lane) -> list[tuple[int, str, str]]:
    """(number, head branch, head oid) of every other open PR on the lane's base, by number."""
    fields = "number,headRefName,headRefOid"
    args = ["pr", "list", "--state", "open", "--base", lane.base_branch, "--limit", "200"]
    out = gh(
        [*args, "--json", fields, *(["-R", lane.repo] if lane.repo else [])],
        "check gh auth status, then rerun",
        err=_UnreadError,
    )
    try:
        rows = cast("list[dict[str, object]]", json.loads(out))
        got = [(int(str(r["number"])), str(r["headRefName"]), str(r["headRefOid"])) for r in rows]
    except (ValueError, KeyError, TypeError) as e:
        msg = f"gh pr list printed no pull requests ({out[:100]!r})"
        raise _UnreadError(msg) from e
    return sorted(x for x in got if x[0] != lane.number)


def _sibling(
    head: str, n: int, branch: str, oid: str
) -> tuple[int, str, list[str], list[str]] | str:
    """PR N's (number, branch, files in conflict with HEAD, pins), its head OID fetched when this
    repo lacks it; the unread line when a read fails."""
    try:
        if _git("cat-file", "-e", f"{oid}^{{commit}}", ok=(0, 1, 128))[0]:
            _git("fetch", "-q", "--no-write-fetch-head", "origin", f"pull/{n}/head")
        return n, branch, _merge_tree(head, oid)[1], _demo_pins(oid)
    except _UnreadError as e:
        return f"PR #{n} ({branch}) head {oid[:12]}: {e}"


def _order(lane: Lane) -> Order:
    """The Order the reads give (spec #gates-merge-order); each failed read one unread line."""
    try:
        rows = _open_prs(lane)
    except _UnreadError as e:
        return Order(lane.base_branch, [], [f"open pull requests on {lane.base_branch}: {e}"])
    read = [_sibling(lane.head, *r) for r in rows]
    found = [x for x in read if not isinstance(x, str)]
    unread = [x for x in read if isinstance(x, str)]
    pins = list(dict.fromkeys(p for *_, ps in found for p in ps))
    said: dict[str, tuple[str, str]] = {}
    if pins:
        try:
            main = _git("rev-parse", "--verify", f"{lane.base}^{{commit}}")[1].strip()
            at_main = _verdicts(main, pins)
            at_merged = _verdicts(_merged(main, lane.head, lane.base), pins)
            said = {p: (a, b) for p, a, b in zip(pins, at_main, at_merged, strict=True)}
        except _UnreadError as e:
            unread.append(f"pinned runs {' '.join(pins)}: {e}")
    prs = [Sibling(n, b, c, [Pin(p, *said[p]) for p in ps if p in said]) for n, b, c, ps in found]
    return Order(lane.base_branch, prs, unread)
