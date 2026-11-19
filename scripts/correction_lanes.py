#!/usr/bin/env python3
"""The correction filer: the correction lanes due on the hand-off logs, filed in their trackers.

The rule: issue-lifecycle spec #lanes-correction; what files where: comms spec
#reflection-correction. Imported by scripts/octo-feather-lane (`archive`, `reflect NAME`,
`reflect --director` file through `file_corrections`; `intake` reads `corrections`, `counts`,
`correction_issues`) and scripts/octo-feather-reflect (`TARGET`, the route mark its parser checks).
How they find it: Python puts a script's own directory, symlinks resolved, first on sys.path, so
`import correction_lanes` in a script beside this file resolves here from any cwd, as `from
handoff_log import ...` already does. Standard library only (AGENTS.md Rules, kit scripts).

Interface:

    file_corrections(lanes) -> list[Outcome]
        LANES the state dir's lanes/: its hand-off logs (archive/ included) and lane records, and
        the director log (DIRECTOR_LOG) beside it, read here. One Outcome per issue filed, per
        recurrence comment and per class due but not filed (a tracker skill gh cannot search),
        each with the exact text the command prints.
    Refused(message): any refusal; its `outcomes` those before it, the filed ones named in the
        message; nothing files after it.

Invariants: every `target:` route's lane record is checked before anything files; one issue or
one comment per class per tracker per run; a class with an open issue gets a recurrence comment
quoting only findings no issue of its class quotes, or nothing. The tracker: the kit's through
the github-issues skill's scripts, a target's through the current directory's tracker skill with
GH_REPO; read through `gh issue list` and `gh repo view`.
"""

import datetime as dt
import importlib.machinery
import importlib.util
import json
import os
import re
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

import tomllib  # stdlib since 3.11; ruff, at the 3.10 floor, sorts it as third-party
from handoff_log import read_log

KIT = Path(__file__).resolve().parent.parent
LogLine = dict[str, object]  # one parsed hand-off log line

DIRECTOR_LOG = "director.handoffs.jsonl"
TARGET = "target:"  # a route's mark (comms spec #reflection-output)
MARK_WORD = "correction-lane"
MARK = f"[{MARK_WORD} {{}}]"  # a correction-lane issue's one title marker: found and filed by it
MISSED = "reflection-missed"
REPEAT = 2  # distinct lanes whose counted findings make a class due (#lanes-correction)
BLOCKERS = (
    "code-review",
    "qc",
)  # the finding sources that count, blocking only (#lanes-correction)
GATE = "owner-caught-"  # the director's (issue-lifecycle #acceptance-gate-correction-lane)
DIRECTOR = "director"  # the director log's name among the logs: a run of the kit's
KIT_REPO = "0xTomDaniel/octo-feather"  # the kit's tracker: every route but a lane's TARGET one
# The kit's own tracker skill, and the one tracker whose issues the rule can search (gh).
GITHUB_ISSUES = "github-issues"


class Refused(Exception):  # noqa: N818 (the name ticket #1082 gives the interface)
    """A refusal: the message names the fix; `outcomes` those before it."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.outcomes: list[Outcome] = []


@dataclass(frozen=True)
class Outcome:
    """One tracker write, or one class due but not filed: KEY the issue key or comment url (None
    when not filed), TEXT the lines the command prints for it."""

    kind: Literal["filed", "commented", "due"]
    key: str | None
    text: str


@dataclass(frozen=True)
class Due:
    """One correction lane the rule makes due, before the tracker is asked: its class, the findings
    it quotes as (log, line), the reflection findings giving its routes as (log, line) and the
    latest finding's `at`; as one tracker files it (`owned`), FOREIGN the logs quoted minimally
    and whose routes go unnamed (which: comms spec #reflection-correction)."""

    cls: str
    findings: list[tuple[str, LogLine]]
    routes: list[tuple[str, LogLine]]
    latest: str
    foreign: frozenset[str] = frozenset()

    def title(self) -> str:
        what = "change the question list" if self.cls == MISSED else "repeated finding class"
        return f"{MARK.format(self.cls)} {what}: {self.cls}"

    def route(self) -> str:
        named = dict.fromkeys(str(d["route"]) for log, d in self.routes if log not in self.foreign)
        if not named and self.routes:
            return "given only by lanes of another repository"
        return "; ".join(named) or "none given by a reflection"

    def body(self) -> str:
        quoted = [quote(log, d, minimal=log in self.foreign) for log, d in self.findings]
        changes = (
            "Changes: the question list, reflection/questions.json"
            " (comms spec #reflection-questions)"
        )
        return "\n".join(
            [
                (
                    "Correction lane (issue-lifecycle spec #lanes-correction), filed by"
                    " `octo-feather-lane reflect` (comms spec #reflection-correction)."
                ),
                "",
                f"Class: {self.cls}",
                f"Route: {self.route()}",
                *([changes] if self.cls == MISSED else []),
                "",
                f"Findings ({len(self.findings)}):",
                *quoted,
            ]
        )


def quote(log: str, d: LogLine, *, minimal: bool = False) -> str:
    """Finding line D of LOG as an issue or comment quotes it: its run (LOG), date and source;
    MINIMAL (when: comms spec #reflection-correction): its run, date and class only."""
    if minimal:
        return f"- {log} {d.get('at')} {d.get('class')}"
    return (
        f"- {log} {d.get('at')} {d.get('source') or DIRECTOR}"
        + (f" ({d['question']})" if d.get("question") else "")
        + (f", route {d['route']}" if d.get("route") else "")
        + f": {d.get('summary')}"
    )


def counts(log: str, d: LogLine) -> bool:
    """Whether finding line D of LOG counts toward its class's correction lane (the rule:
    issue-lifecycle #lanes-correction)."""
    return log != DIRECTOR and d.get("source") in BLOCKERS and d.get("blocking") is True


def corrections(logs: dict[str, list[LogLine]], director: list[LogLine]) -> list[Due]:
    """Each correction lane the rule makes due on the finding lines of the lane hand-off logs LOGS
    ({lane: lines}, archived included) and the DIRECTOR log, before the tracker is asked; a due
    class names the routes its reflection findings gave; reflection-missed findings are a due per
    log, its own lane's or the director's."""
    by: dict[tuple[str, str], list[tuple[str, LogLine]]] = {}
    routed: dict[str, list[tuple[str, LogLine]]] = {}
    for log, lines in [*logs.items(), (DIRECTOR, director)]:
        for d in lines:
            cls = d.get("class")
            if d.get("kind") != "finding" or not isinstance(cls, str) or cls.startswith(GATE):
                continue
            if d.get("route"):
                routed.setdefault(cls, []).append((log, d))
            if cls == MISSED or counts(log, d):  # reflection-missed: due at once
                by.setdefault((cls, log if cls == MISSED else ""), []).append((log, d))
    out: list[Due] = []
    for (cls, _), found in by.items():
        if cls != MISSED and len({log for log, _ in found}) < REPEAT:
            continue
        latest = max(str(d.get("at") or "") for _, d in found)
        routes = (
            [(log, d) for log, d in found if d.get("route")]
            if cls == MISSED
            else routed.get(cls, [])
        )
        out.append(Due(cls, found, routes, latest))
    return out


def owned(due: Due, repos: dict[str, str | None]) -> list[tuple[str | None, Due, list[str]]]:
    """The trackers DUE files in and what each quotes (the rule: comms spec #reflection-correction),
    each (its repository, the Due as that tracker files it, the lane logs whose TARGET routes name
    it), REPOS each lane log's record's repository (None: it names none, refused by the caller).
    A kit lane's TARGET route is the kit's; a target's Due also quotes the reflection findings
    giving its routes, so it never quotes none."""

    def repo(log: str) -> str | None:
        r = KIT_REPO if log == DIRECTOR else repos.get(log)
        return KIT_REPO if r and r.lower() == KIT_REPO.lower() else r

    logs = {log for log, _ in [*due.findings, *due.routes]}
    targets: dict[str | None, list[str]] = {}
    kit = due.cls == MISSED or not due.routes
    for log, d in due.routes:
        if due.cls != MISSED and repo(log) != KIT_REPO and str(d["route"]).startswith(TARGET):
            targets.setdefault(repo(log), []).append(log)
        else:
            kit = True
    out: list[tuple[str | None, Due, list[str]]] = []
    if kit:
        foreign = frozenset(log for log in logs if repo(log) != KIT_REPO)
        out.append((KIT_REPO, Due(due.cls, due.findings, due.routes, due.latest, foreign), []))
    for t, by in targets.items():
        routes = [
            (log, d) for log, d in due.routes if log in by and str(d["route"]).startswith(TARGET)
        ]
        found = [(log, d) for log, d in due.findings if repo(log) == t]
        found = sorted([*found, *routes], key=lambda f: str(f[1].get("at") or ""))
        latest = max(str(d.get("at") or "") for _, d in found)
        out.append((t, Due(due.cls, found, routes, latest), by))
    return out


def merge(dues: list[Due]) -> list[Due]:
    """DUES landing in one tracker as one Due per class: its findings (by date), routes, latest
    and foreign logs together."""
    by: dict[str, list[Due]] = {}
    for d in dues:
        by.setdefault(d.cls, []).append(d)
    return [
        ds[0]
        if len(ds) == 1
        else Due(
            cls,
            sorted((f for d in ds for f in d.findings), key=lambda f: str(f[1].get("at") or "")),
            [x for d in ds for x in d.routes],
            max(d.latest for d in ds),
            frozenset(o for d in ds for o in d.foreign),
        )
        for cls, ds in by.items()
    ]


def of_class(due: Due, issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """DUE's class's issues among ISSUES, oldest first: the class the first word of the title's
    marker, so a legacy reflection-missed marker's timestamp and hash never block a match."""
    mark = re.compile(r"\[" + re.escape(MARK_WORD) + r" ([^\]\s]+)[^\]]*\]")
    mine = [i for i in issues if (m := mark.search(str(i.get("title")))) and m[1] == due.cls]
    return sorted(mine, key=lambda i: int(i.get("number") or 0))


def is_open(issue: dict[str, Any]) -> bool:
    return str(issue.get("state")).upper() == "OPEN"


def still_due(due: Due, issues: list[dict[str, Any]]) -> bool:
    """Whether DUE files, given the tracker's ISSUES ({number, title, state, closedAt}): none is
    of its class, or none such is open and its latest finding is dated after the last one closed."""
    mine = of_class(due, issues)
    if not mine:
        return True
    if any(is_open(i) for i in mine):
        return False
    return due.latest > max(str(i.get("closedAt") or "") for i in mine)


QUOTED = re.compile(r"(?m)^- (\S+) (\d{4}-\d\d-\d\dT\S+)(?: .*|$)")  # a quote, its run and date


def quoted(text: str) -> list[tuple[str, tuple[str, str]]]:
    """Each finding TEXT quotes, full or minimal (`quote`), once per quote: its line and its
    (run, date)."""
    return [(m[0].strip(), (m[1], m[2])) for m in QUOTED.finditer(text)]


def recurrence(due: Due, issues: list[dict[str, Any]]) -> tuple[dict[str, Any], str] | None:
    """The issue among ISSUES ({..., body, comments: [{body}]}) and the comment for DUE on a
    recurrence (comms spec #reflection-correction): the oldest open of its class; the running count,
    the findings its issues and this comment quote, each once. None when it adds none. A full quote
    is quoted when any issue of the class quotes it word for word, so legacy duplicate issues each
    quoting one finding of a run quote them all; a minimal one, by its run and date (`quoted`): as
    many of a run and date as the most any one issue quotes, or the full quotes of them all."""
    mine = of_class(due, issues)
    first = next((i for i in mine if is_open(i)), None)
    if first is None:
        return None
    full: set[tuple[str, tuple[str, str]]] = set()  # each full quote, whichever issue holds it
    said: Counter[tuple[str, str]] = Counter()  # how many findings of each (run, date) are quoted
    for i in mine:
        cs = cast("list[dict[str, Any]]", i.get("comments") or [])
        texts = [str(i.get("body") or ""), *(str(c.get("body") or "") for c in cs)]
        short: list[tuple[str, str]] = []  # an issue's minimal quotes: same (run, date), distinct
        long: set[tuple[str, tuple[str, str]]] = set()  # its full ones, each finding once
        for line, (run, at) in (q for x in texts for q in quoted(x)):
            if line == f"- {run} {at} {due.cls}":
                short.append((run, at))
            else:
                long.add((line, (run, at)))
        full |= long
        said |= Counter(short) + Counter(k for _, k in long)
    said |= Counter(k for _, k in full)
    lines = {line for line, _ in full}
    runs: dict[tuple[str, str], list[str]] = {}
    for log, d in due.findings:
        key = (log, str(d.get("at")))
        runs.setdefault(key, []).append(quote(log, d, minimal=log in due.foreign))
    new = [
        q
        for (log, at), qs in runs.items()
        for q in (qs[said[log, at] :] if log in due.foreign else [q for q in qs if q not in lines])
    ]
    if not new:
        return None
    head = (
        f"Recurrence of class {due.cls} (comms spec #reflection-correction), added by"
        f" `octo-feather-lane reflect`: {len(new)} new finding{'s' if len(new) != 1 else ''};"
        f" running count {sum(said.values()) + len(new)}."
    )
    return first, "\n".join([head, "", *new])


def lane_logs(lanes: Path) -> list[tuple[str, Path, list[LogLine]]]:
    """Every lane hand-off log, archived ones first: (lane, path, its lines)."""
    return [
        (p.name.removesuffix(".handoffs.jsonl"), p, read_log(p)[0])
        for p in sorted(lanes.glob("archive/*.handoffs.jsonl"))
        + sorted(lanes.glob("*.handoffs.jsonl"))
    ]


def file_corrections(lanes: Path) -> list[Outcome]:
    """Every correction lane due (`corrections`, `owned`, `merge`, `still_due`, `recurrence`),
    whichever reflection ran, filed through the tracker skill's issue-create or issue-comment in
    each tracker `owned` names: the kit's through github-issues, a target's through the current
    directory's tracker skill with GH_REPO, each target record checked first (`target_repo`).
    Refused when the tracker cannot be read or written (contract: the module docstring)."""
    out: list[Outcome] = []
    try:
        _file(lanes, out)
    except Refused as e:
        e.outcomes = out
        raise
    return out


def _file(lanes: Path, out: list[Outcome]) -> None:
    dlog = lanes.parent / DIRECTOR_LOG
    try:
        logs: dict[str, list[LogLine]] = {}
        for lane, _, lines in lane_logs(lanes):
            logs[lane] = logs.get(lane, []) + lines
        due = corrections(logs, read_log(dlog)[0] if dlog.exists() else [])
    except (OSError, UnicodeDecodeError) as e:
        msg = f"correction lanes: cannot read the hand-off logs ({e}): fix the cause, then rerun"
        raise Refused(msg) from e
    records = {lane: lane_record(lanes, lane) for lane in logs}
    repos = {
        lane: (str(rec[1]["repository"]) if rec and rec[1].get("repository") else None)
        for lane, rec in records.items()
    }
    trackers: dict[tuple[str, str], list[Due]] = {}  # (skill, repo): the dues landing there
    for d in due:
        for repo, there, by in owned(d, repos):
            for lane in by:  # every target refused before anything is filed
                target_repo(records[lane], lane, d.cls)
            skill = GITHUB_ISSUES if repo == KIT_REPO else tracker_skill(Refused)
            trackers.setdefault((skill, str(repo)), []).append(there)
    for (skill, repo), dues in trackers.items():
        _file_in(
            skill, repo, merge(dues), out
        )  # merged: one issue or comment per class per tracker


def _file_in(skill: str, repo: str, mine: list[Due], out: list[Outcome]) -> None:
    """File MINE, one Due per class, in tracker SKILL REPO, appending each Outcome to OUT."""
    where = f"{skill} {repo}"
    if skill != GITHUB_ISSUES:
        out.extend(
            Outcome(
                "due",
                None,
                f"correction lane: due, not filed: {d.cls}: tracker skill {skill} offers no"
                f" search for an existing one; file it by hand through {skill}'s issue-create,"
                f" title `{d.title()}`, unless one is open",
            )
            for d in mine
        )
        return
    issues = correction_issues(repo, full=True)
    for d in mine:
        if not still_due(d, issues):
            if again := recurrence(d, issues):
                n, text = again[0]["number"], again[1]
                url = _write(out, repo, text, "issue-comment", str(n))
                said = "\n".join(f"  {x}" if x else "" for x in text.splitlines())
                head = f"correction lane: commented {url} on {n} in {where} for {d.cls}:"
                out.append(Outcome("commented", url, f"{head}\n{said}"))
            continue
        key = _write(out, repo, d.body(), "issue-create", "--title", d.title())
        n = len(d.findings)
        out.append(
            Outcome(
                "filed",
                key,
                f"correction lane: filed {key} in {where} for {d.cls} ({n} finding"
                f"{'s' if n != 1 else ''}; route: {d.route()})",
            )
        )


def _write(out: list[Outcome], repo: str, text: str, script: str, *args: str) -> str:
    """Run github-issues SCRIPT ARGS on REPO with TEXT as its body; its key or url. Refused naming
    what OUT filed before it."""
    try:
        return tracker(
            script,
            *args,
            "--body-file",
            "-",
            err=Refused,
            skill=GITHUB_ISSUES,
            env={"GH_REPO": repo},
            stdin=text,
        ).strip()
    except Refused as e:
        filed = [o.key for o in out if o.key]
        before = f" (filed before it: {', '.join(filed)})" if filed else ""
        msg = f"correction lanes: {e}{before}"
        raise Refused(msg) from e


def lane_record(lanes: Path, lane: str) -> tuple[Path, dict[str, object]] | None:
    """Lane LANE's record, open or archived, and its keys; None when it has none; Refused when it
    cannot be read."""
    rec = next(
        (p for p in (lanes / f"{lane}.toml", lanes / "archive" / f"{lane}.toml") if p.is_file()),
        None,
    )
    try:
        return (rec, tomllib.loads(rec.read_text(encoding="utf-8"))) if rec else None
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
        msg = f"correction lanes: cannot read lane record {rec} ({e}): fix it, then rerun"
        raise Refused(msg) from e


@dataclass(frozen=True)
class RepoView:
    """`gh repo view R --json nameWithOwner,createdAt`, validated once at this edge (repo_view)."""

    name: str  # nameWithOwner: the repository's current name
    created: dt.datetime  # createdAt, UTC


def repo_view(repo: str, fix: str) -> RepoView:
    """REPO's RepoView. A hand-written check, not a schema library: kit scripts stay
    standard-library-only (quality spec #edge-validation-kit). Exactly the two fields asked, each
    typed; Refused naming the field it rejects."""
    out = _gh(["repo", "view", repo, "--json", "nameWithOwner,createdAt"], fix)
    try:
        got: object = json.loads(out)
    except ValueError as e:
        msg = f"gh repo view {repo} printed no JSON ({e}): check the gh on PATH, then rerun"
        raise Refused(msg) from e
    d = cast("dict[str, object]", got) if isinstance(got, dict) else None
    bad = (
        "not an object"
        if d is None
        else f"fields {sorted(d)}, want exactly createdAt, nameWithOwner"
        if set(d) != {"nameWithOwner", "createdAt"}
        else "nameWithOwner is not a non-empty string"
        if not isinstance(d["nameWithOwner"], str) or not d["nameWithOwner"]
        else f"createdAt {d['createdAt']!r} is not a UTC time"
        if utc(d["createdAt"]) is None
        else None
    )
    if d is None or bad:
        msg = (
            f"gh repo view {repo} printed {bad}: check `gh repo view {repo} --json"
            " nameWithOwner,createdAt`, update gh, then rerun"
        )
        raise Refused(msg)
    return RepoView(str(d["nameWithOwner"]), cast("dt.datetime", utc(d["createdAt"])))


def target_repo(rec: tuple[Path, dict[str, object]] | None, lane: str, cls: str) -> None:
    """Refused: a `target:` route of lane LANE (class CLS) whose record REC is not fit to file in
    (which: spec comms #reflection-correction), naming the record to fix."""
    path = rec[0] if rec else f"{lane}.toml (no lane record)"
    repo, started = (rec[1].get("repository"), rec[1].get("started_at")) if rec else (None, None)
    why = (
        f"correction lanes: lane {lane}'s reflection routed class {cls} to its own repository"
        f" (`target:`), but its record {path}"
    )
    fix = "; nothing filed: fix the record, then rerun"
    if not isinstance(repo, str) or not repo:
        msg = f"{why} names no repository{fix}"
        raise Refused(msg)
    view = repo_view(repo, f"check the repository of {path}, then rerun")
    if view.name.lower() != repo.lower():
        msg = f"{why} names repository {repo}, which is now {view.name}{fix}"
        raise Refused(msg)
    began = utc(started)
    if began is None:
        msg = f"{why} has no started_at, so {repo} may have been re-created since{fix}"
        raise Refused(msg)
    if view.created > began:
        msg = (
            f"{why} names repository {repo}, created {view.created:%Y-%m-%dT%H:%M:%SZ}, after the"
            f" lane started ({started}){fix}"
        )
        raise Refused(msg)


def correction_issues(repo: str | None, *, full: bool = False) -> list[dict[str, object]]:
    """Every correction-lane issue, open or closed, of the github-issues tracker REPO (None: the
    current directory's), found by `MARK_WORD` in its title, as a strict record of gh's raw
    fields: number (int), title, state (str), closedAt (str or null), and when FULL body (str) and
    comments ([{body: str}]); Refused on any other JSON, naming the issue and the fix."""
    fields = ["number", "title", "state", "closedAt", *(["body", "comments"] if full else [])]
    out = _gh(
        [
            "issue",
            "list",
            *(["--repo", repo] if repo else []),
            "--state",
            "all",
            "--limit",
            "1000",
            "--search",
            f'"{MARK_WORD}" in:title',
            "--json",
            ",".join(fields),
        ],
        "check gh auth and network, then rerun",
    )
    try:
        got = json.loads(out)
    except ValueError as e:
        msg = f"correction lanes: gh issue list printed no JSON ({e}): rerun"
        raise Refused(msg) from e
    if not isinstance(got, list):
        msg = "correction lanes: gh issue list printed no list: rerun"
        raise Refused(msg)
    issues: list[dict[str, object]] = []
    for n, i in enumerate(cast("list[object]", got), 1):
        d = cast("dict[str, object]", i) if isinstance(i, dict) else {}
        cs = d.get("comments")
        ok = (
            all(k in d for k in fields)
            and type(d["number"]) is int
            and isinstance(d["title"], str)
            and isinstance(d["state"], str)
            and isinstance(d["closedAt"], (str, type(None)))
            and (
                not full
                or (
                    isinstance(d["body"], str)
                    and isinstance(cs, list)
                    and all(
                        isinstance(c, dict)
                        and isinstance(cast("dict[str, object]", c).get("body"), str)
                        for c in cast("list[object]", cs)
                    )
                )
            )
        )
        if not ok:
            msg = (
                f"correction lanes: gh issue list item {n} (#{d.get('number')}) is not gh's issue"
                " JSON (number an int, title and state strings, closedAt a string or null"
                + (", body a string, comments a list of objects with a string body" if full else "")
                + f"): check `gh issue list --json {','.join(fields)}` on {repo or 'this repo'},"
                " update gh, then rerun"
            )
            raise Refused(msg)
        rec = {k: d[k] for k in fields if k != "comments"}
        if full:
            rec["comments"] = [
                {"body": cast("dict[str, object]", c)["body"]} for c in cast("list[object]", cs)
            ]
        issues.append(rec)
    return issues


def _gh(args: list[str], fix: str) -> str:
    """gh ARGS' stdout; Refused naming FIX when it fails. octo-feather-lane's own `gh`, which
    refuses with that command's Refuse, word for word."""
    try:
        p = subprocess.run(
            ["gh", *args],  # noqa: S607 (gh from PATH, as the command runs it)
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            check=False,
        )
    except FileNotFoundError as e:
        msg = "gh not on PATH: install the GitHub CLI and log in (just install-check)"
        raise Refused(msg) from e
    if p.returncode:
        err = (p.stderr or p.stdout).strip().splitlines()
        why = err[-1][:300] if err else f"exit {p.returncode}"
        msg = f"gh {' '.join(args[:3])} failed ({why}): {fix}"
        raise Refused(msg)
    return p.stdout


def tracker_skill(err: type[Exception]) -> str:
    """The target's tracker skill: scripts/pi-role's tracker_skill resolves it from the
    .octo-feather.toml of the git repo at the current directory, docs/adr/0004."""
    loader = importlib.machinery.SourceFileLoader("pi_role", str(KIT / "scripts" / "pi-role"))
    spec = importlib.util.spec_from_loader("pi_role", loader)
    assert spec is not None, "a SourceFileLoader always yields a spec"
    pr = importlib.util.module_from_spec(spec)
    loader.exec_module(pr)
    try:
        return str(pr.tracker_skill(str(KIT / ".agents" / "skills")))
    except SystemExit as e:
        msg = (
            f"{e.code}: set `tracker` in the target's .octo-feather.toml to a tracker the kit has,"
            " then rerun"
        )
        raise err(msg) from e


def tracker(
    script: str,
    *args: str,
    err: type[Exception],
    skill: str | None = None,
    env: dict[str, str] | None = None,
    stdin: str | None = None,
) -> str:
    """Run SCRIPT of SKILL, by default the target's tracker skill (tracker_skill); its stdout. ENV
    is added to the script's environment, STDIN its input. A failure raises ERR naming the script
    and its reason."""
    skill = skill or tracker_skill(err)
    path = KIT / ".agents" / "skills" / skill / "scripts" / script
    try:
        p = subprocess.run(
            [str(path), *args],
            capture_output=True,
            text=True,
            timeout=120,
            env={**os.environ, **(env or {})},
            input=stdin,
            stdin=subprocess.DEVNULL if stdin is None else None,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        msg = (
            f"tracker script {skill}/{script} {' '.join(args)} did not run ({e}): check the"
            " tracker CLI and network, then rerun"
        )
        raise err(msg) from e
    if p.returncode:
        why = " ".join((p.stderr or p.stdout).split())[:400] or f"exit {p.returncode}"
        msg = (
            f"tracker script {skill}/{script} {' '.join(args)} failed ({why}): fix the cause it"
            " names, then rerun"
        )
        raise err(msg)
    return p.stdout


def utc(s: object) -> dt.datetime | None:
    """S as a UTC instant: an ISO 8601 date and time with Z or an offset, fractional seconds
    allowed (2026-10-29T14:06:08Z, 2026-10-29T14:06:08.770516+00:00); None for anything else, a
    time with no zone included."""
    if not isinstance(s, str) or "T" not in s:
        return None
    try:
        t = dt.datetime.fromisoformat(s[:-1] + "+00:00" if s.endswith("Z") else s)
    except ValueError:
        return None
    return None if t.tzinfo is None else t.astimezone(dt.timezone.utc)
