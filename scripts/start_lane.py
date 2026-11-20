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

import datetime as dt
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from correction_lanes import DIRECTOR_LOG
from handoff_log import encode
from tracker_calls import gh, tracker

KIT = Path(__file__).resolve().parent.parent
START = KIT / "scripts" / "octo-feather-start"
SAY = KIT / ".agents" / "skills" / "herdr-comms" / "assets" / "herdr-say"
FLAGS = ("--goal", "--outcome", "--brief-file")
USAGE = "usage: octo-feather-lane start TICKET --goal TITLE --outcome TEXT --brief-file FILE"
GOAL = (
    "/goal {outcome} for {key}, delivered through implement-spec; done when an owner gate is"
    " pending (review link or merge ask sent) or PR merged and lane torn down"
)


@dataclass(frozen=True)
class Ask:
    """What the director names: the ticket as its tracker writes it, the lane title, the
    outcome, and the brief's text."""

    ticket: str
    goal: str
    outcome: str
    brief: str


@dataclass(frozen=True)
class Lane:
    """The lane's facts, read before anything is made."""

    key: str
    director: str
    checkout: Path
    issue: str  # the parent issue as the brief header names it
    repository: str

    @property
    def worktree(self) -> Path:
        return self.checkout.with_name(f"{self.checkout.name}-{self.key}")


def parse(args: list[str], err: type[Exception]) -> Ask:
    """ARGS as an Ask; ERR naming the usage or the unreadable brief file."""
    opts: dict[str, str] = {}
    rest: list[str] = []
    it = iter(args)
    for a in it:
        if a in FLAGS:
            v = next(it, None)
            if v is None or a in opts:
                msg = f"{USAGE} ({a} needs one value)"
                raise err(msg)
            opts[a] = v
        else:
            rest.append(a)
    if len(rest) != 1 or set(opts) != set(FLAGS) or not all(v.strip() for v in opts.values()):
        msg = f"{USAGE} (got {' '.join(args) or 'nothing'})"
        raise err(msg)
    if "\n" in opts["--goal"]:
        msg = "--goal is the lane title, one line (comms spec #lane-record, goal)"
        raise err(msg)
    try:
        brief = Path(opts["--brief-file"]).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        msg = f"--brief-file {opts['--brief-file']} unreadable ({e}): name the brief's file"
        raise err(msg) from e
    return Ask(rest[0], opts["--goal"], opts["--outcome"], brief)


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
    """Step 1: the lane's facts, nothing made."""
    director = os.environ.get("HERDR_PANE_ID", "")
    if not director:
        msg = "step read: no HERDR_PANE_ID: run the lane start from the director's pane"
        raise err(msg)
    checkout = Path(run(err, "read", ["git", "rev-parse", "--show-toplevel"]))
    key = tracker("lane-key", ask.ticket, err=err).strip()
    raw = tracker("issue-view", ask.ticket, err=err)
    try:
        view = json.loads(raw)
        issue = f"{view['key']} {view['title']} ({view['url']})"
    except (ValueError, KeyError, TypeError) as e:
        msg = f"step read: issue-view {ask.ticket} printed no issue ({raw[:200]!r})"
        raise err(msg) from e
    fix = "check the checkout's origin and gh auth status"
    out = gh(["repo", "view", "--json", "nameWithOwner"], fix, err=err)
    try:
        repository = str(json.loads(out)["nameWithOwner"])
    except (ValueError, KeyError, TypeError) as e:
        msg = f"step read: gh repo view printed no nameWithOwner ({out[:200]!r})"
        raise err(msg) from e
    return Lane(key, director, checkout, issue, repository)


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
        [str(START), "--issue", ask.ticket, "--cwd", str(wt)],
        stdout=subprocess.PIPE,
        text=True,
        stdin=subprocess.DEVNULL,
        check=False,
    )
    spawned = dict(w.split("=", 1) for w in p.stdout.split() if "=" in w)
    pane, name = spawned.get("pane", ""), spawned.get("name", "")
    if p.returncode or not pane or not name:
        msg = (
            f"step supervisor: octo-feather-start --issue {ask.ticket} exit {p.returncode}"
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
        # Written by hand: the stdlib has no TOML writer (tomli-w exists; kit scripts stay
        # stdlib only, AGENTS.md); a record is flat strings, whose JSON escapes TOML shares.
        with record.open("x", encoding="utf-8") as f:
            f.write("".join(f"{k} = {json.dumps(v)}\n" for k, v in keys.items()))
    except OSError as e:
        msg = f"step record: {record} not written ({e}); {made}"
        raise err(msg) from e
    made += f", record {record}"

    goal = GOAL.format(outcome=ask.outcome, key=lane.key)
    run(err, f"goal ({made})", [str(SAY), pane, goal])
    header = (
        f"Lane facts (octo-feather-lane start):\nLane key: {lane.key}\n"
        f"Parent issue: {lane.issue}\nDirector pane: {lane.director}\nWorktree: {wt}\n"
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
    return f"key={lane.key} pane={pane} issue={ask.ticket}"
