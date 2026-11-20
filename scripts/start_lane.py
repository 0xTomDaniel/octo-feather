#!/usr/bin/env python3
"""`octo-feather-lane start`, the director's lane start, one command (issue-lifecycle spec
#acceptance-lane-start; the boundary-director-lanes seam). What it does, in order, and its output:
`octo-feather-lane --help`, start; this module holds its steps, each failure raising the caller's
error naming the step and what the start made so far.

No stalled-message retry: herdr-spawn returns only once the new Pi takes input (herdr-comms
SKILL.md, Spawn an agent), so a failed herdr-say is a failure. Standard library only (AGENTS.md:
the kit's scripts); how a command finds this module: scripts/correction_lanes.py's docstring.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn, cast

from correction_lanes import DIRECTOR_LOG
from handoff_log import encode
from tracker_calls import gh, tracker

KIT = Path(__file__).resolve().parent.parent
START = KIT / "scripts" / "octo-feather-start"
SAY = KIT / ".agents" / "skills" / "herdr-comms" / "assets" / "herdr-say"
GOAL = (
    "/goal {outcome} for {key}, delivered through implement-spec; done when an owner gate is"
    " pending (review link or merge ask sent) or PR merged and lane torn down"
)
# A lane key names a branch, a worktree and a record file: one plain token (roles spec #lane-key).
KEY = re.compile(r"[a-z0-9][a-z0-9._-]*")
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
# issue-view's fields (skills spec #tracker-script-issue-view), exactly.
VIEW_STR = ("key", "title", "body", "state", "url")
VIEW_LISTS = ("children", "blocked_by")
VIEW = {*VIEW_STR, *VIEW_LISTS, "parent"}


@dataclass(frozen=True)
class New:
    """A parent ticket to file (--new, --body-file): its title, one line, and its body's file,
    read before anything is made."""

    title: str
    body_file: Path


@dataclass(frozen=True)
class Ask:
    """What the director names: the ticket as its tracker writes it, or the one to file, the lane
    title, the outcome, and the brief's text."""

    ticket: str | New
    goal: str
    outcome: str
    brief: str


@dataclass(frozen=True)
class Issue:
    """The ticket as issue-view prints it, validated at this edge (issue_view)."""

    key: str
    title: str
    url: str
    parent: str | None  # set: a sub-issue, refused (refuse_sub_issue)


@dataclass(frozen=True)
class Lane:
    """The lane's facts, read before anything is made."""

    key: str
    director: str
    checkout: Path
    issue: Issue
    repository: str
    ticket: str  # as the director named it, or the key of the one the start filed

    @property
    def worktree(self) -> Path:
        return self.checkout.with_name(f"{self.checkout.name}-{self.key}")


def parse(args: list[str], err: type[Exception]) -> Ask:
    """ARGS as an Ask (argparse); ERR naming argparse's usage error or the unreadable brief."""

    class Parser(argparse.ArgumentParser):
        def error(self, message: str) -> NoReturn:
            msg = f"{self.format_usage().strip()} ({message})"
            raise err(msg)

    p = Parser(prog="octo-feather-lane start", add_help=False)
    p.add_argument("ticket", metavar="TICKET", nargs="?")
    p.add_argument("--new", metavar="TITLE")
    p.add_argument("--body-file", metavar="FILE", type=Path)
    p.add_argument("--goal", required=True, metavar="TITLE")
    p.add_argument("--outcome", required=True, metavar="TEXT")
    p.add_argument("--brief-file", required=True, metavar="FILE", type=Path)
    ns = p.parse_args(args)
    goal, outcome = cast("str", ns.goal), cast("str", ns.outcome)
    brief_file = cast("Path", ns.brief_file)
    ticket = parent_ticket(p, cast("str | None", ns.ticket), ns.new, ns.body_file, err)
    named = ("TICKET", ticket) if isinstance(ticket, str) else ("--new", ticket.title)
    for name, v in (named, ("--goal", goal), ("--outcome", outcome)):
        if not v.strip():
            p.error(f"{name} is empty")
        try:
            v.encode("utf-8")
        except UnicodeEncodeError:
            p.error(f"{name} is not UTF-8 text")
    if "\n" in goal:
        p.error("--goal is the lane title, one line (comms spec #lane-record, goal)")
    try:
        brief = brief_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        msg = f"--brief-file {brief_file} unreadable ({e}): name the brief's file"
        raise err(msg) from e
    return Ask(ticket, goal, outcome, brief)


def parent_ticket(
    p: argparse.ArgumentParser,
    ticket: str | None,
    new: str | None,
    body_file: Path | None,
    err: type[Exception],
) -> str | New:
    """TICKET, or the New one --new and --body-file name (its body read here, before anything is
    made); P's usage error when neither or both are named."""
    if (ticket is None) == (new is None):
        p.error("name a TICKET, or file one with --new TITLE --body-file FILE, not both")
    if (new is None) != (body_file is None):
        p.error("--new and --body-file go together: the new parent's title and body")
    if new is None or body_file is None:
        return cast("str", ticket)
    if "\n" in new:
        p.error("--new is the new parent's title, one line")
    try:
        body_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        msg = f"--body-file {body_file} unreadable ({e}): name the new parent's body file"
        raise err(msg) from e
    return New(new, body_file)


def file_parent(new: New, err: type[Exception]) -> str:
    """File NEW with the target's tracker skill's issue-create, a top-level issue (never
    --parent: a lane's parent is no other issue's sub-issue); print its key at once, so a start
    that stops later is rerun naming it; the key."""
    out = tracker("issue-create", "--title", new.title, "--body-file", str(new.body_file), err=err)
    key = out.strip()
    if not key or len(key.split()) != 1:
        msg = f"step file: issue-create printed {out[:200]!r}, no issue key: check the tracker"
        raise err(msg)
    sys.stdout.write(f"filed={key}\n")
    sys.stdout.flush()
    return key


def refuse_sub_issue(issue: Issue, ticket: str, err: type[Exception]) -> None:
    """ERR naming ISSUE's parent when it has one: a lane never starts under another issue."""
    if issue.parent is not None:
        msg = (
            f"step read: ticket {ticket} is a sub-issue of {issue.parent} (issue-view's parent):"
            " a lane's parent ticket is a top-level issue; name one, or file one with"
            " --new TITLE --body-file FILE"
        )
        raise err(msg)


def toml_str(s: str) -> str:
    """S as a TOML basic string: written by hand, the stdlib has no TOML writer (tomli-w exists;
    kit scripts stay stdlib only, AGENTS.md). TOML escapes only the quote, the backslash and
    control characters; every other character, astral ones included, is written as itself."""
    out: list[str] = []
    for ch in s:
        if ch in ('"', "\\"):
            out.append("\\" + ch)
        elif ord(ch) < 0x20 or ord(ch) == 0x7F:  # noqa: PLR2004 (TOML's control characters)
            out.append(f"\\u{ord(ch):04X}")
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def json_object(raw: str, what: str, err: type[Exception]) -> dict[str, object]:
    """RAW parsed as one JSON object; ERR naming WHAT when it is not."""
    try:
        got: object = json.loads(raw)
    except ValueError as e:
        msg = f"step read: {what} printed no JSON ({e}): {raw[:200]!r}"
        raise err(msg) from e
    if not isinstance(got, dict):
        msg = f"step read: {what} printed no JSON object: {raw[:200]!r}"
        raise err(msg)
    return cast("dict[str, object]", got)


def issue_view(raw: str, ticket: str, err: type[Exception]) -> Issue:
    """issue-view TICKET's RAW output as an Issue. A hand-written check, not a schema library:
    kit scripts stay standard-library-only (quality spec #edge-validation-kit). Exactly its
    fields, each typed; ERR naming the field it rejects."""
    what = f"issue-view {ticket}"
    d = json_object(raw, what, err)
    lists = {k: d.get(k) for k in VIEW_LISTS}
    bad = (
        f"fields {sorted(d)}, want exactly {sorted(VIEW)}"
        if set(d) != VIEW
        else next((f"{k} is no string" for k in VIEW_STR if not isinstance(d[k], str)), None)
        or next((f"{k} is empty" for k in ("key", "title", "url") if not d[k]), None)
        or (
            "parent is neither null nor a string"
            if d["parent"] is not None and not isinstance(d["parent"], str)
            else None
        )
        or next(
            (
                f"{k} is no list of strings"
                for k, v in lists.items()
                if not isinstance(v, list)
                or not all(isinstance(x, str) for x in cast("list[object]", v))
            ),
            None,
        )
    )
    if bad:
        msg = f"step read: {what} printed {bad}: check the tracker skill's issue-view, then rerun"
        raise err(msg)
    parent = d["parent"]
    return Issue(
        str(d["key"]), str(d["title"]), str(d["url"]), parent if isinstance(parent, str) else None
    )


def repository(err: type[Exception]) -> str:
    """owner/name of the checkout's repo, `gh repo view --json nameWithOwner` validated at this
    edge: exactly that field, an owner/name string (hand-written: #edge-validation-kit)."""
    out = gh(
        ["repo", "view", "--json", "nameWithOwner"],
        "check the checkout's origin and gh auth status",
        err=err,
    )
    d = json_object(out, "gh repo view", err)
    name = d.get("nameWithOwner")
    if set(d) != {"nameWithOwner"} or not isinstance(name, str) or not REPO.fullmatch(name):
        msg = (
            f"step read: gh repo view printed {json.dumps(d)[:200]}, want exactly nameWithOwner,"
            " an owner/name string: check the gh on PATH, then rerun"
        )
        raise err(msg)
    return name


def run(err: type[Exception], step: str, cmd: list[str], cwd: Path | None = None) -> str:
    """CMD's stdout, stripped; ERR naming STEP, CMD and its last line of error when it fails."""
    p = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, stdin=subprocess.DEVNULL, check=False
    )
    if p.returncode:
        said = (p.stderr or p.stdout).strip().splitlines()
        why = said[-1][:300] if said else "no output"
        msg = f"step {step}: {Path(cmd[0]).name} {cmd[1]} exit {p.returncode} ({why})"
        raise err(msg)
    return p.stdout.strip()


def read(ask: Ask, err: type[Exception]) -> Lane:
    """Step 1: the lane's facts, each validated, nothing made."""
    director = os.environ.get("HERDR_PANE_ID", "")
    if not director:
        msg = "step read: no HERDR_PANE_ID: run the lane start from the director's pane"
        raise err(msg)
    checkout = Path(run(err, "read", ["git", "rev-parse", "--show-toplevel"]))
    repo = repository(err)
    ticket = ask.ticket if isinstance(ask.ticket, str) else file_parent(ask.ticket, err)
    key = tracker("lane-key", ticket, err=err).strip()
    if not KEY.fullmatch(key):
        msg = f"step read: lane-key {ticket} printed {key[:100]!r}, no lane key (roles #lane-key)"
        raise err(msg)
    issue = issue_view(tracker("issue-view", ticket, err=err), ticket, err)
    refuse_sub_issue(issue, ticket, err)
    return Lane(key, director, checkout, issue, repo, ticket)


def start(args: list[str], lanes: Path, err: type[Exception]) -> str:
    """Start the lane ARGS name, its record in LANES (the session's lanes dir); the line to print.
    Every failure raises ERR naming its step and what the start made so far."""
    ask = parse(args, err)
    lane = read(ask, err)
    wt, top = lane.worktree, lane.checkout
    run(err, "worktree", ["git", "fetch", "--quiet", "origin"], top)
    main = run(err, "worktree", ["git", "rev-parse", "--verify", "origin/main^{commit}"], top)
    run(err, "worktree", ["git", "worktree", "add", "--quiet", "-b", lane.key, str(wt), main], top)
    made = f"made so far: worktree {wt} on branch {lane.key}"

    p = subprocess.run(  # its stderr shown as it comes
        [str(START), "--issue", lane.ticket, "--cwd", str(wt)],
        stdout=subprocess.PIPE,
        text=True,
        stdin=subprocess.DEVNULL,
        check=False,
    )
    spawned = dict(w.split("=", 1) for w in p.stdout.split() if "=" in w)
    pane, name = spawned.get("pane", ""), spawned.get("name", "")
    if p.returncode or not pane or not name:
        msg = (
            f"step supervisor: octo-feather-start --issue {lane.ticket} exit {p.returncode}"
            f" (stdout {p.stdout.strip()[:300]!r}, stderr above); {made}"
        )
        raise err(msg)
    made += f", supervisor {pane} in workspace {spawned.get('workspace', '?')}"

    at = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    record = lanes / f"{name}.toml"
    keys = {"supervisor": pane, "repository": lane.repository, "issue": lane.key}
    keys |= {"goal": ask.goal, "started_at": at, "waiting_on": ""}
    try:
        lanes.mkdir(parents=True, exist_ok=True)
        with record.open("x", encoding="utf-8") as f:
            f.write("".join(f"{k} = {toml_str(v)}\n" for k, v in keys.items()))
    except OSError as e:
        msg = f"step record: {record} not written ({e}); {made}"
        raise err(msg) from e
    made += f", record {record}"

    goal = GOAL.format(outcome=ask.outcome, key=lane.key)
    run(err, f"goal ({made})", [str(SAY), pane, goal])
    header = (
        f"Lane facts (octo-feather-lane start):\nLane key: {lane.key}\n"
        f"Parent issue: {lane.issue.key} {lane.issue.title} ({lane.issue.url})\n"
        f"Director pane: {lane.director}\nWorktree: {wt}\n"
        f"Branch: {lane.key}\nMain commit: {main}\n\n"
    )
    made += ", goal sent"
    run(err, f"brief ({made})", [str(SAY), pane, header + ask.brief])

    log = lanes.parent / DIRECTOR_LOG
    note = f"lane start: {lane.key} supervisor {pane}, worktree {wt} on {lane.key}"
    note += f" from main {main[:12]}; goal and brief sent"
    try:
        with log.open("a", encoding="utf-8") as f:
            f.write(encode({"at": at, "kind": "prod", "issue": lane.key, "note": note}) + "\n")
    except OSError as e:
        msg = f"step log: director log {log} not written ({e}); {made}, brief sent"
        raise err(msg) from e
    return f"key={lane.key} pane={pane} issue={lane.ticket}"
