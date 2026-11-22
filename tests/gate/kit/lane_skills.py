"""The scenarios of tests/gate/kit/test_lane_skills.py (its items), this file their command
(testkit.main): scripts/octo-feather-lane skills (spec issue-lifecycle #acceptance-ticket-skills;
rules: octo-feather-lane --help (skills)), offline.

GitHub answers only real gh's, unmodified (testkit/recordings/lane-skills.json, issue-view 1094
and 1099 --notes on 2026-11-19): #1094 names `Skills: eval-cases` in a comment, #1099 `Skills:
tdd, codebase-design` in its body. The worker's Pi session is a recorded file, trimmed
(tests/fixtures/lane-skills/sessions/): lines 1, 4, 12, 13 and 14 of #1094's implementer session
4fd43c0c (lane gh644), its thinking blocks dropped and every text but the system prompt's skills
section and role heading cut to `[trimmed]`; it loaded eval-cases (`cat
.agents/skills/eval-cases/SKILL.md`, line 12) and never tdd or codebase-design. The lane state
is a scratch one: lane gh644's record with the supervisor's pane; its hand-off log's spawn lines
are the real herdr-spawn's, each worker spawned the kit's standard way (`implementer-<lane key>`,
#1169) from the supervisor's pane through the testkit's Herdr (testkit/herdr.py, its FAKE_HERDR
world), the recorded session file named by the session id herdr-spawn gave, as Pi names the file
of a `--session-id` launch. Issue-view 1199 --notes is recorded too (2026-11-22, `Skills: tdd,
python` in its body), and #1199's implementer session 97e2c882 (lane gh1197) is trimmed the same
way to its lines 1, 4, 14 and 15: its one bash call reading tdd's and python's SKILL.md after the
word `quality#acceptance-gate-time-targets` (line 14) and that call's result.

Linear (scenario linear, and misread's `Skills: tdd, python.`: #1134, #1136 and #1137 had that
line, but each now has a later corrected one, so no real gh answer holds it): LINEAR_API_KEY is
not set in the factory (director decision on #921);
ENG-123's answers are a tape built here, its source saying so (testkit/linear.py replays it).
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

from lane_tickets import NOTES, VIEW
from testkit import FIXTURES, HERE, ROOT, Scratch, kit, main

TAPE = Path(__file__).parent / "testkit" / "recordings" / "lane-skills.json"
TICKETS = Path(__file__).parent / "testkit" / "recordings" / "lane-tickets-644.json"
SESSION = "4fd43c0c-7119-4cb4-866f-e114e16ecdb4"
RECORDED = next((FIXTURES / "lane-skills" / "sessions").glob(f"*/*_{SESSION}.jsonl"))
HASHED = next((FIXTURES / "lane-skills" / "sessions").glob("*/*_97e2c882-*.jsonl"))
SPAWN = ROOT / ".agents" / "skills" / "herdr-comms" / "assets" / "herdr-spawn"
SUP = "w1:p0"  # the supervisor's pane, the lane record's `supervisor`


def world(s: Scratch) -> Path:
    """The scratch lane gh644 (its record; the testkit's Herdr, empty, the caller's Herdr and kit
    vars cleared; the caller the supervisor's pane) and the target repo t; the lane hand-off log's
    path, which each spawn writes."""
    s.gh.store("tape.json", json.loads(TAPE.read_text()))
    d = s.root / "herdr"
    d.mkdir()
    (d / "agents.json").write_text("{}")
    for k in [k for k in s.env if k.startswith(("HERDR_", "OCTO_FEATHER_"))]:
        del s.env[k]
    s.env |= {"FAKE_HERDR": str(d), "PI_CODING_AGENT_DIR": str(s.root / "pi")}
    s.env |= {"HERDR_PANE_ID": SUP, "HERDR_WORKSPACE_ID": "w1"}
    s.identity()
    lanes = Path(s.run([kit("octo-feather-state")]).out) / "lanes"
    lanes.mkdir(parents=True)
    (lanes / "gh644.toml").write_text(f'supervisor = "{SUP}"\nissue = "gh644"\n')
    s.git(s.root, "init", "-q", "-b", "main", "t")
    return lanes / "gh644.handoffs.jsonl"


def spawn(
    s: Scratch, name: str, lines: int | None = None, recorded: Path = RECORDED
) -> tuple[str, Path]:
    """NAME spawned as an implementer in repo t by the real herdr-spawn from the supervisor's pane
    (it appends the spawn line to the lane log); its Pi session file the RECORDED one (its first
    LINES lines, else all) under the session id herdr-spawn printed. Its pane and that file."""
    cmd = [str(SPAWN), "--workspace", "w1", "--name", name, "--role", "implementer"]
    out = s.run([*cmd, "--cwd", str(s.root / "t")]).out
    got = dict(x.split("=", 1) for x in out.split())
    to = s.root / "pi" / "sessions" / recorded.parent.name
    to.mkdir(parents=True, exist_ok=True)
    sid = recorded.stem.split("_", 1)[1]
    f = to / recorded.name.replace(sid, got["provider_session_id"])
    f.write_text("".join(recorded.read_text().splitlines(keepends=True)[:lines]))
    return got["pane"], f


def skills(s: Scratch, ticket: str, want: int = 0, **env: str) -> str:
    """`octo-feather-lane skills TICKET` in repo t exiting WANT, the tape replayed afresh; its
    stdout."""
    for d in (s.gh.dir, Path(s.env.get("FAKE_LINEAR", s.gh.dir))):
        (d / "log").write_text("")
    r = s.run([kit("octo-feather-lane"), "skills", ticket], want=want, cwd=s.root / "t", env=env)
    return r.out if want != 2 else r.err


def findings(log: Path) -> list[dict[str, object]]:
    return [x for x in map(json.loads, log.read_text().splitlines()) if x["kind"] == "finding"]


def strip(f: dict[str, object]) -> dict[str, object]:
    return {k: v for k, v in f.items() if k not in ("at", "summary")}


def miss(sk: str, *, blocking: bool, ticket: str = "1099") -> dict[str, object]:
    """A skills finding line for TICKET and SK, as the log holds it (comms
    #handoff-kind-finding)."""
    return {
        "kind": "finding",
        "source": "skills",
        "class": "skill-not-loaded",
        "blocking": blocking,
        "ticket": ticket,
        "skill": sk,
    }


def send_back_once(s: Scratch) -> None:
    """#1094's worker loaded eval-cases: `loaded`, nothing logged, exit 0. #1099 names tdd and
    codebase-design, which the session never loaded: a `not loaded` line each; the first miss of
    each logs one blocking finding line (source skills, class skill-not-loaded, ticket, skill),
    prints the fix sending the worker back by its pane and exits 1. Run again, the log holding
    that send-back: one non-blocking line each, `sent back once already`, exit 0. A send-back
    already logged for tdd alone: tdd recorded not blocking, codebase-design sent back, exit 1."""
    log = world(s)
    first, _ = spawn(s, "implementer-gh1094")
    worker, _ = spawn(s, "implementer-gh1099")
    before = log.read_text()
    out = skills(s, "1094")
    assert out.splitlines()[1:] == ["1094: skill eval-cases: loaded"], out
    assert f"worker implementer-gh1094 ({first}), Pi session " in out, out
    assert log.read_text() == before, "a loaded skill logged a finding"
    out = skills(s, "1099", want=1)
    lines = out.splitlines()
    assert lines[1:3] == [
        "1099: skill tdd: not loaded",
        "1099: skill codebase-design: not loaded",
    ], out
    fix = (
        "1099: fix: send implementer-gh1099 back before integrate: "
        f"herdr-say {worker} 'Load tdd, codebase-design"
    )
    assert fix in out, out
    assert "sent back once already" not in out, out
    assert [strip(f) for f in findings(log)] == [
        miss("tdd", blocking=True),
        miss("codebase-design", blocking=True),
    ]
    assert all("implementer-gh1099" in str(f["summary"]) for f in findings(log)), findings(log)
    out = skills(s, "1099")
    for sk in ("tdd", "codebase-design"):
        said = f"1099: skill {sk}: sent back once already; this miss stands recorded, not blocking"
        assert said in out, out
    assert "fix:" not in out, out
    got = [strip(f) for f in findings(log)][2:]
    assert got == [miss("tdd", blocking=False), miss("codebase-design", blocking=False)], got
    log.write_text(
        before + json.dumps(miss("tdd", blocking=True) | {"at": "x", "summary": "x"}) + "\n"
    )
    out = skills(s, "1099", want=1)
    assert "1099: skill tdd: sent back once already" in out, out
    assert f"herdr-say {worker} 'Load codebase-design (" in out, out
    got = [strip(f) for f in findings(log)][1:]
    assert got == [miss("tdd", blocking=False), miss("codebase-design", blocking=True)], got


def refusals(s: Scratch) -> None:
    """A comparison that cannot run never blocks (supervisor ruling on #1099): exit 2 naming the
    cause and `integrate, only exit 1 sends the worker back`. With the caller's log found, one
    non-blocking finding line, class skills-unchecked, with the ticket: a ticket the tracker cannot
    read (#16, no recording: gh exits 2), one with no spawn line in the log (#1094's spawn line
    gone). No caller pane or a pane owning no lane: nothing recorded, said so."""
    log = world(s)
    spawn(s, "implementer-gh1094")
    spawn(s, "implementer-gh1099")
    before = log.read_text()
    err = skills(s, "16", want=2)
    assert "tracker script github-issues/issue-view 16 --notes failed" in err, err
    assert f"could not check, recorded in {log} (class skills-unchecked, not blocking)" in err, err
    assert "integrate, only exit 1 sends the worker back" in err, err
    got = [strip(f) for f in findings(log)]
    want = {"kind": "finding", "source": "skills", "class": "skills-unchecked", "blocking": False}
    assert got == [want | {"ticket": "16"}], got
    kept = [x for x in before.splitlines(keepends=True) if json.loads(x)["ticket"] != "gh1094"]
    log.write_text("".join(kept))
    err = skills(s, "1094", want=2)
    assert "no spawn line for ticket 1094" in err, err
    assert [strip(f) for f in findings(log)] == [want | {"ticket": "1094"}], findings(log)
    n = log.read_text()
    for pane, why in (("", "HERDR_PANE_ID is unset"), ("w9:p9", "pane w9:p9 owns no lane record")):
        err = skills(s, "1099", want=2, HERDR_PANE_ID=pane)
        assert why in err, err
        assert "could not check, not recorded (no hand-off log for this pane)" in err, err
    assert log.read_text() == n, "an unrecorded run wrote to the log"


def tickets_comment(s: Scratch) -> None:
    """`tickets 644` (lane gh644's parent) on real gh's answers, unmodified
    (testkit/recordings/lane-tickets-644.json, 2026-11-20): `tickets` reads each ticket's body and
    comments; #1094's only `Skills:` line is a comment (`Skills: eval-cases`), #1099's is in its
    body (`Skills: tdd, codebase-design`); both pass. The target is a scratch repo with the kit's
    specs and its scripts/ demos tracked."""
    s.gh.store("tape.json", json.loads(TICKETS.read_text()))
    t = s.root / "t"
    shutil.copytree(ROOT / "docs" / "specs", t / "docs" / "specs")
    for p in ("octo-feather-lane", "octo-feather-qa"):
        (t / "scripts").mkdir(exist_ok=True)
        (t / "scripts" / p).write_text("#!/bin/sh\n")
        (t / "scripts" / p).chmod(0o755)
    s.git(s.root, "init", "-q", "-b", "main", "t")
    s.git(t, "add", "-A")
    r = s.run([kit("octo-feather-lane"), "tickets", "644"], cwd=t)
    assert r.out == "1094: ok\n1099: ok\n644: 2 of 2 tickets pass", r.out
    notes = sorted(x.split()[3] for x in s.gh.log() if x.startswith("api graphql "))
    assert notes == ["n=1094", "n=1099"], s.gh.log()


LIN_SOURCE = (
    "Not recorded: LINEAR_API_KEY is not set in the factory (director decision on #921). Built "
    "from schpet/linear-cli v3.1.0's source (the linear skill's cli-version: `api` prints Linear's "
    "response compact) and Linear's GraphQL schema. Each call answered once, as Linear would for "
    "ENG-123 with that description."
)
LIN_URL = "https://linear.app/acme/issue/ENG-123/t"


def linear_tape(d: Path, desc: str) -> None:
    """D's tape: ENG-123, its description DESC, no comment and no history."""
    view: dict[str, object] = {
        "identifier": "ENG-123",
        "title": "t",
        "description": desc,
        "url": LIN_URL,
        "state": {"type": "started"},
        "parent": None,
        "children": {"nodes": [], "pageInfo": {"hasNextPage": False}},
        "inverseRelations": {"nodes": []},
    }
    notes: dict[str, object] = {
        "url": LIN_URL,
        "createdAt": "2026-11-20T00:00:00.000Z",
        "description": desc,
        "comments": {"nodes": [], "pageInfo": {"hasNextPage": False}},
        "history": {"nodes": [], "pageInfo": {"hasNextPage": False}},
    }
    calls: list[dict[str, object]] = [
        {
            "argv": ["api", "--no-input", "--variable", "id=ENG-123", q],
            "stdin": None,
            "answers": [{"rc": 0, "err": "", "json": {"data": {"issue": i}}}],
        }
        for q, i in ((VIEW, view), (NOTES, notes))
    ]
    d.mkdir(exist_ok=True)
    (d / "tape.json").write_text(json.dumps({"source": LIN_SOURCE, "calls": calls}))


def linear(s: Scratch) -> None:
    """A Linear target: worker `implementer-eng-123` spawned by herdr-spawn (its spawn line's
    ticket eng-123, the lane key of ENG-123). ENG-123 naming tdd, which the session never loaded:
    `skills ENG-123` finds that spawn line, says `not loaded`, logs one blocking finding for
    ENG-123 and tdd, prints the send-back by the worker's pane, exit 1. Naming eval-cases, which it
    loaded: `loaded`, exit 0."""
    log = world(s)
    fl = s.root / "fl"
    path = f"{s.bin}{os.pathsep}{HERE / 'linear'}{os.pathsep}{s.env['PATH']}"
    s.env |= {"FAKE_LINEAR": str(fl), "PATH": path}
    (s.root / "t" / ".octo-feather.toml").write_text('tracker = "linear"\n')
    worker, _ = spawn(s, "implementer-eng-123")
    linear_tape(fl, "## What to build\n\nx\n\nSkills: tdd\n")
    out = skills(s, "ENG-123", want=1)
    assert f"ENG-123: worker implementer-eng-123 ({worker}), Pi session " in out, out
    assert "ENG-123: skill tdd: not loaded" in out, out
    fix = "ENG-123: fix: send implementer-eng-123 back before integrate: "
    fix += f"herdr-say {worker} 'Load tdd ("
    assert fix in out, out
    assert [strip(f) for f in findings(log)] == [miss("tdd", blocking=True, ticket="ENG-123")]
    linear_tape(fl, "## What to build\n\nx\n\nSkills: eval-cases\n")
    out = skills(s, "ENG-123")
    assert out.splitlines()[1:] == ["ENG-123: skill eval-cases: loaded"], out


def demo(s: Scratch) -> None:
    """The ticket's demo (#1170): worker implementer-gh1094 spawned by herdr-spawn, its session
    the recorded one up to its offered skills (lines 1 and 4: nothing read). #1094 names
    eval-cases: `skills 1094` exits 1 printing the send-back. The worker then loads it (the
    recorded call and results, lines 12 to 14, appended to its session): exit 0, `loaded`. Then
    #1231's part (misread)."""
    log = world(s)
    worker, session = spawn(s, "implementer-gh1094", lines=2)
    sys.stdout.write(f"herdr-spawn's spawn line in {log.name}:\n{log.read_text()}")
    out = skills(s, "1094", want=1)
    sys.stdout.write(f"octo-feather-lane skills 1094 (exit 1):\n{out}\n")
    assert "1094: skill eval-cases: not loaded" in out, out
    fix = "1094: fix: send implementer-gh1094 back before integrate: "
    fix += f"herdr-say {worker} 'Load eval-cases ("
    assert fix in out, out
    assert [strip(f) for f in findings(log)] == [miss("eval-cases", blocking=True, ticket="1094")]
    with session.open("a") as f:
        f.write("".join(RECORDED.read_text().splitlines(keepends=True)[2:]))
    out = skills(s, "1094")
    sys.stdout.write(f"octo-feather-lane skills 1094 (exit 0):\n{out}\n")
    assert out.splitlines()[1:] == ["1094: skill eval-cases: loaded"], out
    misread(s, log)


def misread(s: Scratch, log: Path) -> None:
    """#1231's part of the demo, in the same lane state: #1199's worker before its one bash call
    (the recorded session's lines 1 and 2) read neither tdd nor python: exit 1, a blocking finding
    each and the send-back line. With that call and its result (the recorded lines 3 and 4), which
    reads both SKILL.md files after the word `quality#acceptance-gate-time-targets`, as bash runs
    it (a `#` inside a word starts no comment): both `loaded`, exit 0, no finding logged. A
    Linear ticket whose line is `Skills: tdd, python.` (a trailing period) with that worker: both
    `loaded`, exit 0, never `not offered`."""
    worker, session = spawn(s, "implementer-gh1199", lines=2, recorded=HASHED)
    before = len(findings(log))
    out = skills(s, "1199", want=1)
    sys.stdout.write(f"octo-feather-lane skills 1199, before its bash call (exit 1):\n{out}\n")
    assert out.splitlines()[1:3] == [
        "1199: skill tdd: not loaded",
        "1199: skill python: not loaded",
    ], out
    fix = "1199: fix: send implementer-gh1199 back before integrate: "
    fix += f"herdr-say {worker} 'Load tdd, python ("
    assert fix in out, out
    got = [strip(f) for f in findings(log)][before:]
    assert got == [miss(k, blocking=True, ticket="1199") for k in ("tdd", "python")], got
    with session.open("a") as f:
        f.write("".join(HASHED.read_text().splitlines(keepends=True)[2:]))
    n = log.read_text()
    out = skills(s, "1199")
    said = "octo-feather-lane skills 1199, its bash call after a mid-word # (exit 0)"
    sys.stdout.write(f"{said}:\n{out}\n")
    assert out.splitlines()[1:] == ["1199: skill tdd: loaded", "1199: skill python: loaded"], out
    assert log.read_text() == n, "a loaded skill logged a finding"
    fl = s.root / "fl"
    path = f"{s.bin}{os.pathsep}{HERE / 'linear'}{os.pathsep}{s.env['PATH']}"
    s.env |= {"FAKE_LINEAR": str(fl), "PATH": path}
    (s.root / "t" / ".octo-feather.toml").write_text('tracker = "linear"\n')
    spawn(s, "implementer-eng-123", recorded=HASHED)
    linear_tape(fl, "## What to build\n\nx\n\n## Skills\n\nSkills: tdd, python.\n")
    n = log.read_text()
    out = skills(s, "ENG-123")
    sys.stdout.write(f"octo-feather-lane skills ENG-123, `Skills: tdd, python.` (exit 0):\n{out}\n")
    assert out.splitlines()[1:] == [
        "ENG-123: skill tdd: loaded",
        "ENG-123: skill python: loaded",
    ], out
    assert log.read_text() == n, "a loaded skill logged a finding"


if __name__ == "__main__":
    main(send_back_once, refusals, tickets_comment, linear, demo)
