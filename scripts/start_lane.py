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
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn, cast

import lane_brake
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
    seen: dict[str, str]  # step (goal, brief) to what the director saw in the pane: shown, absent


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
    for flag in ("--shown", "--absent"):
        p.add_argument(flag, action="append", choices=SENDS, default=[], metavar="STEP")
    ns = p.parse_args(args)
    shown, absent = cast("list[str]", ns.shown), cast("list[str]", ns.absent)
    if both := set(shown) & set(absent):
        p.error(
            f"--shown and --absent both name {', '.join(sorted(both))}: name what the pane shows"
        )
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
    seen = dict.fromkeys(shown, "shown") | dict.fromkeys(absent, "absent")
    return Ask(ticket, goal, outcome, brief, seen)


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


def current_kit(kit: Path, err: type[Exception]) -> None:
    """Step 0, the kit install KIT current with main on its origin (the rule: `octo-feather-lane
    --help`, start); ERR, nothing made, when it is behind. Seen 2026-11-14: lanes started from a
    stale checkout ran stale kit scripts."""
    step = f"kit (kit install {kit}; nothing made)"
    if not (kit / ".git").exists():
        msg = (
            f"step {step}: {kit} is not a git clone: set OCTO_FEATHER_KIT_INSTALL to the kit"
            " install clone, then rerun"
        )
        raise err(msg)
    run(err, step, ["git", "-C", str(kit), "fetch", "--quiet", "origin"])
    main = run(err, step, ["git", "-C", str(kit), "rev-parse", "--verify", "origin/main^{commit}"])
    head = run(err, step, ["git", "-C", str(kit), "rev-parse", "--verify", "HEAD^{commit}"])
    behind = run(err, step, ["git", "-C", str(kit), "rev-list", "--count", f"{head}..{main}"])
    if behind != "0":
        msg = (
            f"step kit: kit install {kit} at {head} is behind main on its origin ({main}, {behind}"
            " commit(s) it lacks); nothing made: refresh it (octo-feather-lane post-merge step 3,"
            f" the kit refresh) or fast-forward it (git -C {kit} merge --ff-only origin/main),"
            " then rerun"
        )
        raise err(msg)


def read(ask: Ask, lanes: Path, err: type[Exception]) -> Lane:
    """Step 1: the lane's facts, each validated, nothing made; first the brake (lane_brake), its
    line printed, unless a stopped start of the ticket is kept in LANES (a rerun, no new lane)."""
    director = os.environ.get("HERDR_PANE_ID", "")
    if not director:
        msg = "step read: no HERDR_PANE_ID: run the lane start from the director's pane"
        raise err(msg)
    checkout = Path(run(err, "read", ["git", "rev-parse", "--show-toplevel"]))
    repo = repository(err)
    rerun = (
        isinstance(ask.ticket, str)
        and (lanes / f"{tracker('lane-key', ask.ticket, err=err).strip()}.start.json").exists()
    )
    if not rerun:
        sys.stdout.write(lane_brake.brake(os.environ).line + "\n")
        sys.stdout.flush()
    ticket = ask.ticket if isinstance(ask.ticket, str) else file_parent(ask.ticket, err)
    key = tracker("lane-key", ticket, err=err).strip()
    if not KEY.fullmatch(key):
        msg = f"step read: lane-key {ticket} printed {key[:100]!r}, no lane key (roles #lane-key)"
        raise err(msg)
    issue = issue_view(tracker("issue-view", ticket, err=err), ticket, err)
    refuse_sub_issue(issue, ticket, err)
    return Lane(key, director, checkout, issue, repo, ticket)


def workspaces(err: type[Exception]) -> dict[str, str]:
    """Herdr's workspaces, label to id: `herdr workspace list` validated at this edge (each a
    workspace_id and a label string, hand-written: #edge-validation-kit), as octo-feather-start
    reads it for its own one-workspace-per-name refusal."""
    d = json_object(run(err, "exists", ["herdr", "workspace", "list"]), "herdr workspace list", err)
    result = d.get("result")
    got = cast("dict[str, object]", result).get("workspaces") if isinstance(result, dict) else None
    spaces = cast("list[object]", got) if isinstance(got, list) else None
    if spaces is None or not all(
        isinstance(w, dict)
        and isinstance(cast("dict[str, object]", w).get("workspace_id"), str)
        and isinstance(cast("dict[str, object]", w).get("label"), str)
        for w in spaces
    ):
        msg = (
            f"step exists: herdr workspace list printed {json.dumps(d)[:200]}, want"
            " result.workspaces, each a workspace_id and a label string: check the herdr on PATH"
        )
        raise err(msg)
    each = [cast("dict[str, str]", w) for w in spaces]
    return {w["label"]: w["workspace_id"] for w in reversed(each)}


# What a stopped start keeps, in lanes/<key>.start.json (`octo-feather-lane --help`, start): its
# ask, then each step's fact once that step is done. Gone once the start finishes.
ASKED = ("ticket", "goal", "outcome", "brief_sha256")
SENDS = ("goal", "brief")
KEPT = {*ASKED, "main", "pane", "name", "workspace", "started_at"} | {
    f"{s}_{k}" for s in SENDS for k in ("sent", "unknown")
}
# herdr-say exits that prove nothing was typed (herdr-comms SKILL.md, Send a message): a send that
# ended so is rejected and sent again on a rerun; any other failure leaves it unknown (send).
REJECTED = {64, 69, 75, 77}


@dataclass
class Kept:
    """A start's facts so far (KEPT's keys), kept in PATH after each done step."""

    path: Path
    facts: dict[str, str]
    err: type[Exception]

    def done(self, step: str, made: str, **facts: str) -> None:
        """STEP done with FACTS, written whole (a rename); ERR naming it and MADE when not."""
        self.facts |= facts
        tmp = self.path.with_name(self.path.name + ".tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp.write_text(json.dumps(self.facts, ensure_ascii=False) + "\n", encoding="utf-8")
            tmp.replace(self.path)
        except OSError as e:
            msg = f"step {step}: {self.path} not written ({e}), a rerun cannot continue; {made}"
            raise self.err(msg) from e

    def seen(self, seen: dict[str, str]) -> None:
        """ERR when SEEN, what the director saw in the pane, names a step with no unknown send."""
        if bad := [f"--{v} {k}" for k, v in seen.items() if f"{k}_unknown" not in self.facts]:
            msg = f"step goal: {', '.join(bad)}, but no unknown send of it is kept: drop it"
            raise self.err(msg)

    def send(self, step: str, pane: str, text: str, seen: str | None, made: str) -> None:
        """TEXT sent to PANE with herdr-say as STEP once: skipped when sent; an unknown send kept
        (comms spec #delivery-unknown) never sent again blind: ERR naming what to look at, until
        SEEN, the director's look at the pane, says shown (counted sent) or absent (sent again)."""
        sent, unknown = f"{step}_sent", f"{step}_unknown"
        if sent in self.facts:
            return
        at = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        look = (
            f"look at supervisor pane {pane} (herdr pane read {pane}): when it shows the {step},"
            f" rerun this start with --shown {step}; when it does not and is not compacting,"
            f" with --absent {step} (sent once more)"
        )
        if unknown in self.facts and seen is None:
            msg = (
                f"step {step}: the {step} send to {pane} is unknown ({self.facts[unknown]}), so it"
                f" is not sent again blind (comms spec #delivery-unknown): {look}; {made}"
            )
            raise self.err(msg)
        if seen == "shown":
            del self.facts[unknown]
            self.done(step, made, **{sent: at})
            return
        self.done(step, made, **{unknown: "sent, no result kept"})
        p = subprocess.run(
            [str(SAY), pane, text],
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            check=False,
        )
        said = (p.stderr or p.stdout).strip().splitlines()
        why = f"herdr-say {pane} exit {p.returncode} ({said[-1][:300] if said else 'no output'})"
        if p.returncode == 0:
            del self.facts[unknown]
            self.done(step, made, **{sent: at})
            return
        if p.returncode in REJECTED:
            del self.facts[unknown]
            self.done(step, made)
            msg = f"step {step} ({made}): {why}: not delivered; rerun once the cause is fixed"
            raise self.err(msg)
        self.done(step, made, **{unknown: why})
        msg = f"step {step} ({made}): {why}: delivery unknown, not sent again blind: {look}"
        raise self.err(msg)


def stopped(lane: Lane, ask: Ask, lanes: Path, err: type[Exception]) -> Kept:
    """What a stopped start of LANE kept in lanes/<key>.start.json (its ask alone when none did).
    ERR when it was another ask, or when a record, worktree, branch or workspace of the lane exists
    that no stopped start left, naming each; nothing changed (#acceptance-lane-start-exists)."""
    kept = lanes / f"{lane.key}.start.json"
    sha = hashlib.sha256(ask.brief.encode("utf-8")).hexdigest()
    p = {"ticket": lane.ticket, "goal": ask.goal, "outcome": ask.outcome, "brief_sha256": sha}
    if kept.exists():
        try:
            got: object = json.loads(kept.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            msg = f"step exists: stopped start's {kept} unreadable ({e}): read it, remove it, rerun"
            raise err(msg) from e
        d = cast("dict[str, object]", got) if isinstance(got, dict) else {}
        if not d or set(d) - KEPT or not all(isinstance(v, str) for v in d.values()):
            msg = f"step exists: stopped start's {kept} is no object of {sorted(KEPT)} strings"
            raise err(msg)
        if diff := [k for k in ASKED if d.get(k) != p[k]]:
            msg = (
                f"step exists: {kept} is a stopped start of {lane.key} with another"
                f" {', '.join(diff)}: rerun that start as it was"
            )
            raise err(msg)
        p = cast("dict[str, str]", d)
    record = lanes / f"{lane.key}.toml"
    branch = run(err, "exists", ["git", "branch", "--list", lane.key], lane.checkout)
    space = workspaces(err).get(lane.key)
    found = [
        ("started_at", record.exists(), f"lane record {record}"),
        ("main", lane.worktree.exists(), f"worktree {lane.worktree}"),
        ("main", bool(branch), f"branch {lane.key}"),
        ("pane", space is not None, f"Herdr workspace {lane.key} ({space})"),
    ]
    if there := [what for step, exists, what in found if exists and step not in p]:
        msg = (
            f"step exists: lane {lane.key} exists: {', '.join(there)}; nothing changed, no"
            " supervisor started (a finished start, or another lane of this key)"
        )
        raise err(msg)
    return Kept(kept, p, err)


def write(path: Path, text: str, mode: str, made: str, err: type[Exception]) -> None:
    """TEXT written to PATH (MODE "x" a new file, "a" appended); ERR naming MADE, its step first."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open(mode, encoding="utf-8") as f:
            f.write(text)
    except OSError as e:
        step, _, made = made.partition("; ")
        msg = f"{step}: {path} not written ({e}); {made}"
        raise err(msg) from e


def start(args: list[str], lanes: Path, err: type[Exception]) -> str:
    """Start the lane ARGS name, its record in LANES (the session's lanes dir); the line to print.
    Every failure raises ERR naming its step and what the start made so far; a rerun continues
    from that step, each done one skipped (stopped, Kept)."""
    ask = parse(args, err)
    lane = read(ask, lanes, err)
    wt, top = lane.worktree, lane.checkout
    kept = stopped(lane, ask, lanes, err)
    facts = kept.facts
    made = f"made so far: worktree {wt} on branch {lane.key}"
    if "main" not in facts:
        run(err, "worktree", ["git", "fetch", "--quiet", "origin"], top)
        main = run(err, "worktree", ["git", "rev-parse", "--verify", "origin/main^{commit}"], top)
        run(
            err,
            "worktree",
            ["git", "worktree", "add", "--quiet", "-b", lane.key, str(wt), main],
            top,
        )
        kept.done("worktree", made, main=main)
    main = facts["main"]
    if "pane" not in facts:
        kept.done("supervisor", f"{made}, a supervisor", **supervisor(lane.ticket, wt, made, err))
    pane, name = facts["pane"], facts["name"]
    made += f", supervisor {pane} in workspace {facts['workspace']}"

    at = facts.get("started_at") or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    record = lanes / f"{name}.toml"
    keys = {"supervisor": pane, "repository": lane.repository, "issue": lane.key}
    keys |= {"goal": ask.goal, "started_at": at, "waiting_on": ""}
    if "started_at" not in facts:
        text = "".join(f"{k} = {toml_str(v)}\n" for k, v in keys.items())
        write(record, text, "x", f"step record; {made}", err)
        kept.done("record", f"{made}, record {record}", started_at=at)
    made += f", record {record}"

    goal = GOAL.format(outcome=ask.outcome, key=lane.key)
    kept.seen(ask.seen)
    kept.send("goal", pane, goal, ask.seen.get("goal"), made)
    header = (
        f"Lane facts (octo-feather-lane start):\nLane key: {lane.key}\n"
        f"Parent issue: {lane.issue.key} {lane.issue.title} ({lane.issue.url})\n"
        f"Director pane: {lane.director}\nWorktree: {wt}\n"
        f"Branch: {lane.key}\nMain commit: {main}\n\n"
    )
    made += ", goal sent"
    kept.send("brief", pane, header + ask.brief, ask.seen.get("brief"), made)

    log = lanes.parent / DIRECTOR_LOG
    note = f"lane start: {lane.key} supervisor {pane}, worktree {wt} on {lane.key}"
    note += f" from main {main[:12]}; goal and brief sent"
    line = encode({"at": at, "kind": "prod", "issue": lane.key, "note": note}) + "\n"
    write(log, line, "a", f"step log; {made}, brief sent", err)
    try:
        kept.path.unlink()
    except OSError as e:
        msg = f"step log: {kept.path} not removed ({e}): the start finished; remove it"
        raise err(msg) from e
    return f"key={lane.key} pane={pane} issue={lane.ticket}"


def supervisor(ticket: str, wt: Path, made: str, err: type[Exception]) -> dict[str, str]:
    """The supervisor octo-feather-start started at WT for TICKET: its pane, name and workspace."""
    p = subprocess.run(  # its stderr shown as it comes
        [str(START), "--issue", ticket, "--cwd", str(wt)],
        stdout=subprocess.PIPE,
        text=True,
        stdin=subprocess.DEVNULL,
        check=False,
    )
    spawned = dict(w.split("=", 1) for w in p.stdout.split() if "=" in w)
    pane, name = spawned.get("pane", ""), spawned.get("name", "")
    if p.returncode or not pane or not name:
        msg = (
            f"step supervisor: octo-feather-start --issue {ticket} exit {p.returncode}"
            f" (stdout {p.stdout.strip()[:300]!r}, stderr above); {made}"
        )
        raise err(msg)
    return {"pane": pane, "name": name, "workspace": spawned.get("workspace", "?")}
