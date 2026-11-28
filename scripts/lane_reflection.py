#!/usr/bin/env python3
"""lane_reflection: octo-feather-lane's reflect and intake, and archive's reflection half. Moved from scripts/octo-feather-lane, the dispatcher (ticket #1333)."""

import hashlib
import os
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from correction_lanes import (
    DIRECTOR,
    DIRECTOR_LOG,
    KIT_REPO,
    MARK_WORD,
    Refused,
    correction_issues,
    corrections,
    counts,
    lane_logs,
)
from correction_lanes import file_corrections as correction_filer
from gate_time import stamp
from handoff_log import read_log
from lane_cli import Refuse, lane_name, lanes_dir, reflect_module

if TYPE_CHECKING:
    from collections.abc import Callable


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def director_source_args(args: list[str]) -> tuple[list[str], tuple[str, Path] | None]:
    if "--director-source" not in args:
        return args, None
    at = args.index("--director-source")
    if at + 3 != len(args) or not args[at + 1] or not Path(args[at + 2]).is_absolute():
        raise Refuse("usage: --director-source CURRENT_DIRECTOR_PANE EXACT_ABSOLUTE_PI_SESSION_FILE (last option)")
    return args[:at], (args[at + 1], Path(args[at + 2]))


def cmd_archive(args: list[str]) -> int:
    args, source = director_source_args(args)
    name = lane_name(args)
    lanes = lanes_dir(); archive = lanes / "archive"
    record, log = lanes / f"{name}.toml", lanes / f"{name}.handoffs.jsonl"
    import stat
    files = []  # regular sources, checked with lstat so a symlink is never followed
    for f in (record, log):
        try:
            mode = os.lstat(f).st_mode
        except FileNotFoundError:
            if f == record:
                raise Refuse(f"no lane record {record}: name an open lane (ls {lanes}), and check HERDR_SESSION is the lane's session")
            continue
        except OSError as e:
            raise Refuse(f"cannot read {f} ({e}): fix its permissions, then rerun") from e
        if not stat.S_ISREG(mode):
            raise Refuse(f"not a regular file: {f}; replace it with the real file (a lane's record and hand-off log are plain files), then rerun")
        files.append(f)
    results = lanes / f"{name}.results"   # its workers' result files (octo-feather-handoff --help, report)
    if os.path.lexists(results) and (results.is_symlink() or not results.is_dir()):
        raise Refuse(f"not a directory: {results}; a lane's result files sit in a plain directory: replace it, then rerun")
    moved = results.is_dir()
    for f in (record, log, *([results] if moved else [])):
        if (archive / f.name).exists() or (archive / f.name).is_symlink():
            raise Refuse(f"archive target exists: {archive / f.name}; compare it with {f}, then remove or rename the archived one by hand")
    pre = log.stat().st_size if log in files else None   # the log's length before the reflection appends
    reflect_lane(name, lanes, source)   # spec comms #reflection-lane: before any file moves
    dlog = lanes.parent / DIRECTOR_LOG
    dpre = dlog.stat().st_size if dlog.is_file() else None
    try:
        reflect_director(lanes, source=source)
    except Refuse as e:
        unreflect(log, pre)   # every file left as it was: the lane reflection's lines cut too
        raise Refuse(f"{e}; the lane reflection's lines undone, every file left in {lanes}") from e
    try:
        file_corrections(lanes)   # spec comms #reflection-correction
    except Refuse as e:
        unreflect(log, pre)
        unreflect(dlog, dpre)
        raise Refuse(f"{e}; the reflections' lines undone, every file left in {lanes}") from e
    if log not in files and os.path.lexists(log):
        cast("list[Path]", files).append(log)   # the reflection wrote the lane's first hand-off line
    try:
        before = {f.name: sha256(f) for f in files}
    except OSError as e:
        raise Refuse(f"cannot read a lane file ({e}): fix its permissions, then rerun") from e
    made_dir = not archive.is_dir()
    created = []  # destinations this run linked, recorded before the source is unlinked
    try:
        archive.mkdir(exist_ok=True)
        for f in files:
            # link then unlink: never overwrites a target that appeared meanwhile.
            os.link(f, archive / f.name, follow_symlinks=False); created.append(f)
            got = sha256(archive / f.name)
            if got != before[f.name]:
                raise ValueError(f"{f} changed before the move: sha256 {before[f.name]} -> {got}")
            f.unlink()
        if moved:
            results.rename(archive / results.name)   # last: nothing after it can fail
    except Exception as e:
        rollback(created, archive)
        unreflect(log, pre)
        unreflect(dlog, dpre)
        if made_dir:
            try:
                archive.rmdir()
            except OSError:
                pass
        raise Refuse(f"move failed ({e}); nothing archived, every file left in {lanes}: fix the cause, then rerun") from e
    for f in files:
        print(f"archived: {archive / f.name} sha256={before[f.name]}")
    if moved:
        print(f"archived: {archive / results.name}")
    return 0


def reflect_lane(name: str, lanes: Path, source: tuple[str, Path] | None = None) -> None:
    """Run the lane reflection of lane NAME and append its lines to the lane's hand-off log; Refuse when it fails."""
    import lane_reporting
    from lane_reporting import ReportSources
    herdr_agents = cast("Callable[[], list[dict[Any, Any]]]", lane_reporting.herdr_agents)
    report_lane = cast("Callable[[Path, list[dict[Any, Any]] | None, str | None, Any, list[str], list[Any], ReportSources], list[str]]", lane_reporting.report_lane)
    import datetime, tomllib
    r = reflect_module()
    record, log, state = lanes / f"{name}.toml", lanes / f"{name}.handoffs.jsonl", lanes.parent
    try:
        rec = tomllib.loads(record.read_text(encoding="utf-8"))
        lines = read_log(log)[0] if log.exists() else []
        dlog = state / "director.handoffs.jsonl"
        qs = r.questions("lane")
        now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
        unread: list[str] = []
        try:
            agents, why = cast("list[dict[str, object]]", herdr_agents()), None
        except Refuse as e:
            agents, why = None, str(e)
        report = report_lane(record, agents, why, now, unread, [], ReportSources(state, unread))
        binding = r.director_binding(state, source)
        binding.require()
        talk = r.lane_transcripts(lines, rec.get("supervisor")) + [binding.description]
        brief = r.brief(r.LaneRecords(name, record, log, dlog, report, talk), qs)
        brief.director = binding
        found, ids = r.parse(r.run(brief, Path.cwd()), qs)
        brief.verify()
        r.append(log, r.log_lines(found, ids, inputs=brief.provenance))
    except r.FailedError as e:
        raise Refuse(f"lane reflection of {name} failed ({e}); nothing appended, every file left in {lanes}: fix the cause, then rerun") from e
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
        raise Refuse(f"lane reflection of {name} failed: cannot read its inputs or write its log ({e}); every file left in {lanes}: fix the cause, then rerun") from e
    print(f"reflection: lane {name}, {len(found)} finding{'s' if len(found) != 1 else ''}, questions {', '.join(ids)}: appended to {log}")
    for f in found:
        print(f"  finding {f['class']} ({f['question']}) -> {f['route']}: {f['summary']}")


DAY = 86400   # when a start's director reflection is due: spec comms #reflection-director


def reflect_director(lanes: Path, due: bool = False, source: tuple[str, Path] | None = None) -> bool:
    """Run the director reflection and append its lines to the director log; Refuse when it fails. DUE: only when
    one is due at a start (DAY), and not while another runs. Whether it ran."""
    from lane_reporting import cmd_report
    import contextlib, datetime, fcntl, io
    r = reflect_module()
    state = lanes.parent
    dlog = state / DIRECTOR_LOG
    try:
        state.mkdir(parents=True, exist_ok=True)
        lock = os.open(state, os.O_RDONLY)   # the state dir's own fd: the lock creates no file
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | (fcntl.LOCK_NB if due else 0))
        except BlockingIOError:
            os.close(lock)
            print(f"director reflection: not due, another one is running ({state})")
            return False
        try:
            dlines = read_log(dlog)[0] if dlog.exists() else []
            now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
            last = r.reflected_at(dlines)
            if due and (not dlines if last is None else (now - last).total_seconds() <= DAY):
                print("director reflection: not due, " + (f"last ran {stamp(f'{last:%Y-%m-%dT%H:%M:%SZ}', now)}" if last
                                                         else f"no director log lines to reflect on ({dlog})"))
                return False
            since, _ = r.since_last_reflection(dlines)
            logs: dict[str, list[dict[str, object]]] = {}
            listed: list[str] = []
            for lane, p, lines in lane_logs(lanes):
                logs[lane] = logs.get(lane, []) + lines
                listed.append(r.lane_log_line(lane, p, lines))
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                cmd_report([])
            binding = r.director_binding(state, source)
            binding.require()
            rec = r.DirectorRecords(dlog, since, buf.getvalue().splitlines(),
                                    binding.description, listed, r.class_counts(logs))
            qs = r.questions("director")
            brief = r.director_brief(rec, qs)
            brief.director = binding
            found, ids = r.parse(r.run(brief, Path.cwd()), qs)
            brief.verify()
            r.append(dlog, r.log_lines(found, ids, lane=False, inputs=brief.provenance))
        finally:
            os.close(lock)   # releases the lock
    except r.FailedError as e:
        raise Refuse(f"director reflection failed ({e}); nothing appended to {dlog}: fix the cause, then rerun") from e
    except (OSError, UnicodeDecodeError) as e:
        raise Refuse(f"director reflection failed: cannot read its inputs or write {dlog} ({e}): fix the cause, then rerun") from e
    print(f"reflection: director, {len(found)} finding{'s' if len(found) != 1 else ''}, questions {', '.join(ids)}: appended to {dlog}")
    for f in found:
        print(f"  finding {f['class']} ({f['question']}) -> {f['route']}: {f['summary']}")
    return True


def file_corrections(lanes: Path) -> None:
    """Spec comms #reflection-correction: correction_lanes' file_corrections, each outcome's lines printed, then
    `correction lanes: none filed or commented` when none filed or commented; Refuse on its refusal, after the lines of
    the outcomes before it."""
    try:
        outcomes = correction_filer(lanes)
    except Refused as e:
        for o in e.outcomes:
            print(o.text)
        raise Refuse(str(e)) from e
    for o in outcomes:
        print(o.text)
    if all(o.key is None for o in outcomes):
        print("correction lanes: none filed or commented")


def cmd_intake(args: list[str]) -> int:
    """`octo-feather-lane intake` (spec comms #reflection-correction): every open correction-lane issue, grouped by
    class, with the rule's evidence (scripts/correction_lanes.py `corrections`, `counts`); reads only."""
    import tomllib
    if args:
        raise Refuse(f"usage: octo-feather-lane intake (got {' '.join(args)})")
    lanes = lanes_dir()
    dlog = lanes.parent / DIRECTOR_LOG
    logs: dict[str, list[dict[str, object]]] = {}
    for lane, _, lines in lane_logs(lanes):
        logs[lane] = logs.get(lane, []) + lines
    director = read_log(dlog)[0] if dlog.exists() else []
    due = {d.cls for d in corrections(logs, director)}
    repos: list[str] = []
    for rec in sorted(lanes.glob("archive/*.toml")) + sorted(lanes.glob("*.toml")):
        try:
            repo = tomllib.loads(rec.read_text(encoding="utf-8")).get("repository")
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
            continue
        if isinstance(repo, str) and repo and repo not in repos:
            repos.append(repo)
    if KIT_REPO not in repos:
        repos.append(KIT_REPO)
    mark = re.compile(r"\[" + re.escape(MARK_WORD) + r" ([^\]]+)\]")
    by: dict[str, list[tuple[str, str, dict[str, object]]]] = {}
    for repo in repos:
        try:
            issues = correction_issues(repo)
        except Refused as e:
            raise Refuse(str(e)) from e
        for i in issues:
            m = mark.search(str(i.get("title")))
            if m and str(i.get("state")).upper() == "OPEN":
                subject = m.group(1)
                by.setdefault(subject.split(" ")[0], []).append((repo, subject, i))
    found = [(log, d) for log, lines in [*logs.items(), (DIRECTOR, director)] for d in lines
             if d.get("kind") == "finding" and isinstance(d.get("class"), str)]
    print(f"correction intake: {sum(len(v) for v in by.values())} open correction-lane issue(s) in {len(by)} class(es);"
          f" trackers searched (github-issues): {', '.join(repos)}; rule: issue-lifecycle #lanes-correction")
    for cls in sorted(by):
        mine = [(log, d) for log, d in found if d["class"] == cls]
        counted = [(log, d) for log, d in mine if counts(log, d)]
        lanes_ = sorted({log for log, _ in counted})
        print(f"class {cls}: due {'yes' if cls in due else 'no'}; blocking {len(counted)} in {len(lanes_)} lane(s)"
              + (f" ({', '.join(lanes_)})" if lanes_ else "") + f"; findings {len(mine)}")
        for repo, _, i in by[cls]:
            print(f"  issue {repo}#{i.get('number')}: {i.get('title')}")
        if len(by[cls]) > 1:
            print(f"  duplicates: {len(by[cls])} open issues of class {cls}")
        for log, d in sorted(mine, key=lambda x: str(x[1].get("at") or "")):
            print(f"  finding {log} {d.get('at')} {d.get('source') or DIRECTOR} {'blocking' if d.get('blocking') is True else 'not blocking'}"
                  f": {' '.join(str(d.get('summary') or '').split())[:200]}")
    return 0


def cmd_reflect(args: list[str]) -> int:
    args, source = director_source_args(args)
    if args[:1] == ["--director"]:
        if args[1:] not in ([], ["--due"]):
            raise Refuse(f"usage: octo-feather-lane reflect --director [--due] (got {' '.join(args)})")
        lanes = lanes_dir()
        if reflect_director(lanes, due=args[1:] == ["--due"], source=source):
            file_corrections(lanes)
        return 0
    name = lane_name(args, "reflect")
    lanes = lanes_dir()
    if not (lanes / f"{name}.toml").is_file():
        raise Refuse(f"no lane record {lanes / f'{name}.toml'}: name an open lane (ls {lanes}), and check HERDR_SESSION is the lane's session")
    reflect_lane(name, lanes, source)
    file_corrections(lanes)
    return 0


def unreflect(log: Path, pre: int | None) -> None:
    """Undo this archive's reflection lines after a failed move, so every file is left as it was: the log cut back
    to its length PRE, or removed when the reflection created it (PRE None)."""
    try:
        os.truncate(log, pre) if pre is not None else log.unlink(missing_ok=True)
    except OSError as e:
        print(f"could not undo the reflection lines in {log} ({e}): cut them by hand", file=sys.stderr)


def rollback(created: list[Path], archive: Path) -> None:
    """Undo a failed archive: restore each source, then drop each destination this run made.
    A destination whose source cannot be restored is kept (the only copy) and named."""
    for f in reversed(created):
        dest = archive / f.name
        try:
            if not os.path.lexists(f):
                os.link(dest, f, follow_symlinks=False)
            dest.unlink()
        except OSError as e:
            print(f"rollback failed for {dest} ({e}): move it back to {f} by hand", file=sys.stderr)


# This module's chunks of octo-feather-lane --help, joined in lane_cli.HELP_ORDER by lane_cli.help_doc.
HELP = {
    "archive": """\
  octo-feather-lane archive NAME   close lane NAME: move lanes/NAME.toml and
                                   lanes/NAME.handoffs.jsonl into lanes/archive/

The state dir is the one `octo-feather-state` prints (XDG_STATE_HOME, HERDR_SESSION).
Before moving any file `archive` runs the lane reflection, then the director reflection (`reflect`,
below); when either cannot run, the archive refuses naming the failed reflection, every file left in place.
`archive` creates lanes/archive/ if missing, moves each file byte-for-byte unchanged
and prints `archived: <file> sha256=<hex>` per file. A lane with no hand-off log gets one
from the reflection (its reflection line). It refuses, non-zero with every file left in
place, when the record is missing or either archive target already exists.

""",
    "reflect": """\
  octo-feather-lane reflect NAME   lane reflection (spec comms #reflection-lane): a fresh headless
                                   reflector answers the lane questions; appends its lines to the log

`reflect` gathers what the reflector cannot compute without bash: the record and hand-off log paths, the
director log's lines about the lane (its issue, or a text naming the lane, #N or ghN), the factory report's
lines for the lane (`report`, below), and the transcript paths of the supervisor, each worker the log names
with a session, and the director. It starts agents/reflector.md through pi-role with the lane questions of
reflection/questions.json, parses its labelled reply (form and refusals: scripts/octo-feather-reflect) and
appends to lanes/NAME.handoffs.jsonl (created when absent) its finding and reflection lines (spec comms
#reflection-output; fields: #handoff-kind-finding, #handoff-kind-reflection), in one write; prints
`reflection: ...` and each finding.
A reflector that cannot run or replies outside the form appends nothing: exit 1 naming the failed reflection.

  octo-feather-lane reflect --director [--due]
                                   director reflection (spec comms #reflection-director): a fresh
                                   headless reflector answers the director questions; appends its
                                   lines to the director log

`reflect --director` gathers the director log's lines since its last reflection line, the factory report
(`report`, below), the director's transcript path, every lane hand-off log (lanes/ and lanes/archive/) with its
lane reflection lines, and the finding class counts across those logs by source and frequency (spec comms
#reflection-writer-route). It runs the same reflector, parser and refusals as `reflect NAME`, with the director
questions, and appends to director.handoffs.jsonl its finding and reflection lines (spec comms
#reflection-output; fields: #handoff-director-finding, #handoff-director-reflection). One director reflection
runs at a time (a lock on the state dir). --due runs it only when one is due at a start (spec comms
#reflection-director; `octo-feather-start` runs that in the background) and the director log has lines, else
prints `director reflection: not due ...`, exit 0; also exit 0, nothing run, while another one runs.

Reflection source option (last): `--director-source CURRENT_DIRECTOR_PANE EXACT_ABSOLUTE_PI_SESSION_FILE`
is shared by `reflect NAME`, `reflect --director [--due]`, and `archive NAME`. A supervisor closes a
lane with `octo-feather-lane archive NAME --director-source PANE FILE`; both reflections use that
source. Native Herdr agent_session (id/path) is authoritative when present. Otherwise the option is
an explicit-director-handoff declaration through existing comms, not independently proven current
session ownership: an undetectably old same-pane/cwd declaration cannot be rejected. Record, live
Pi pane, source header/cwd and source prefix are validated/rechecked; native conflict or invalid
explicit input refuses atomically. Missing required director source is an unknown sourcegap and
refuses reflection/archive, never completion. --due's existing not-due cases still run no reflection.

After its reflection, `reflect NAME`, `reflect --director` (when it ran) and `archive` (after both, before any file
moves) file the correction lanes due (spec comms #reflection-correction; the rule: issue-lifecycle #lanes-correction)
through the tracker skill's `issue-create`, each in the tracker spec comms #reflection-correction names (a target's
through the current directory's tracker skill, GH_REPO its lane record's `repository`, refused naming the record that
spec section says is unfit); each issue's title carries the marker of
scripts/correction_lanes.py `MARK`, by which `gh issue list` finds the ones already filed. Prints
`correction lane: filed <key> in <tracker> for <class> (...)` or `correction lane: commented <url> on <key> ...` and
the comment per write (which write: spec comms #reflection-correction), else `correction lanes: none filed or commented`;
a tracker other than github-issues gets `correction lane: due, not filed: ...` naming the title to file by hand.
A tracker that cannot be read or written refuses the archive, its reflections' lines undone, every file in place.

""",
    "intake": """\
  octo-feather-lane intake         every open correction-lane issue by class, with the correction-lane rule's
                                   evidence (spec comms #reflection-correction); reads only, writes nothing

`intake` lists the correction-lane issues (title marker, as `reflect` files them) of the github-issues trackers of
every lane record's `repository` (lanes/ and lanes/archive/) and the kit's, through the same `gh issue list` call
as `reflect`; an issue filed in another tracker (Linear) is not found (gh only). Per class of an open one:
`class <class>: due yes|no; blocking <n> in <m> lane(s) (<lanes>); findings <k>`, under it each open issue
(`issue <repo>#<n>: <title>`), `duplicates: <n> open issues of class <class>` when two or more, and each finding
line of the class in the lane logs and the director log (`finding <lane|director> <at> <source> blocking|not
blocking: <summary>`). Due and what counts: scripts/correction_lanes.py `corrections`, `counts`. Exit 0; 1 when
gh cannot list a tracker.

""",
}
