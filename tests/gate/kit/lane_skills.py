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
is a scratch one: lane gh644's record with the supervisor's pane, and its hand-off log's spawn
lines naming that session for each ticket, as herdr-spawn records them.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from testkit import FIXTURES, ROOT, Scratch, kit, main

TAPE = Path(__file__).parent / "testkit" / "recordings" / "lane-skills.json"
TICKETS = Path(__file__).parent / "testkit" / "recordings" / "lane-tickets-644.json"
SESSION = "4fd43c0c-7119-4cb4-866f-e114e16ecdb4"
SUP = "w1:p2"  # the supervisor's pane, the lane record's `supervisor`
WORKER = "w1:p3"


def world(s: Scratch) -> Path:
    """The scratch lane gh644 (record and hand-off log), the Pi sessions and the target repo t;
    the log's path."""
    s.gh.store("tape.json", json.loads(TAPE.read_text()))
    s.env.pop("HERDR_SESSION", None)
    shutil.copytree(FIXTURES / "lane-skills" / "sessions", s.root / "pi" / "sessions")
    s.env |= {"PI_CODING_AGENT_DIR": str(s.root / "pi"), "HERDR_PANE_ID": SUP}
    lanes = Path(s.run([kit("octo-feather-state")]).out) / "lanes"
    lanes.mkdir(parents=True)
    (lanes / "gh644.toml").write_text(f'supervisor = "{SUP}"\nissue = "gh644"\n')
    spawns = [
        {
            "at": "2026-11-19T19:48:30Z",
            "kind": "spawn",
            "name": f"implementer-{t}",
            "role": "implementer",
            "pane": WORKER,
            "cwd": f"/w/gh644-{t}",
            "session": SESSION,
            "ticket": t,
        }
        for t in ("1094", "1099")
    ]
    log = lanes / "gh644.handoffs.jsonl"
    log.write_text("".join(json.dumps(x) + "\n" for x in spawns))
    s.git(s.root, "init", "-q", "-b", "main", "t")
    return log


def skills(s: Scratch, ticket: str, want: int = 0, **env: str) -> str:
    """`octo-feather-lane skills TICKET` in repo t exiting WANT, the tape replayed afresh; its
    stdout."""
    (s.gh.dir / "log").write_text("")
    r = s.run([kit("octo-feather-lane"), "skills", ticket], want=want, cwd=s.root / "t", env=env)
    return r.out if want != 2 else r.err


def findings(log: Path) -> list[dict[str, object]]:
    return [x for x in map(json.loads, log.read_text().splitlines()) if x["kind"] == "finding"]


def strip(f: dict[str, object]) -> dict[str, object]:
    return {k: v for k, v in f.items() if k not in ("at", "summary")}


def miss(sk: str, *, blocking: bool) -> dict[str, object]:
    """A skills finding line for #1099 and SK, as the log holds it (comms #handoff-kind-finding)."""
    return {
        "kind": "finding",
        "source": "skills",
        "class": "skill-not-loaded",
        "blocking": blocking,
        "ticket": "1099",
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
    before = log.read_text()
    out = skills(s, "1094")
    assert out.splitlines()[1:] == ["1094: skill eval-cases: loaded"], out
    assert f"worker implementer-1094 ({WORKER}), Pi session " in out, out
    assert log.read_text() == before, "a loaded skill logged a finding"
    out = skills(s, "1099", want=1)
    lines = out.splitlines()
    assert lines[1:3] == [
        "1099: skill tdd: not loaded",
        "1099: skill codebase-design: not loaded",
    ], out
    fix = (
        "1099: fix: send implementer-1099 back before integrate: "
        f"herdr-say {WORKER} 'Load tdd, codebase-design"
    )
    assert fix in out, out
    assert "sent back once already" not in out, out
    assert [strip(f) for f in findings(log)] == [
        miss("tdd", blocking=True),
        miss("codebase-design", blocking=True),
    ]
    assert all("implementer-1099" in str(f["summary"]) for f in findings(log)), findings(log)
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
    assert f"herdr-say {WORKER} 'Load codebase-design (" in out, out
    got = [strip(f) for f in findings(log)][1:]
    assert got == [miss("tdd", blocking=False), miss("codebase-design", blocking=True)], got


def refusals(s: Scratch) -> None:
    """No caller pane and a pane owning no lane: exit 2, nothing logged."""
    log = world(s)
    n = len(log.read_text())
    assert "HERDR_PANE_ID is unset" in skills(s, "1099", want=2, HERDR_PANE_ID="")
    assert "pane w9:p9 owns no lane record" in skills(s, "1099", want=2, HERDR_PANE_ID="w9:p9")
    assert len(log.read_text()) == n, "a refused run wrote to the log"


def tickets_comment(s: Scratch) -> None:
    """`tickets 644` (lane gh644's parent) on real gh's answers, unmodified
    (testkit/recordings/lane-tickets-644.json, 2026-11-19): #1094's body has no `Skills:` line,
    its comment does, so `tickets` reads its notes and passes it; #1099's body line passes with no
    notes read. The target is a scratch repo with the kit's specs and its scripts/ demos tracked."""
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
    asked = [x.split(" ", 3)[:3] for x in s.gh.log()]
    assert asked.count(["api", "graphql", "-F"]) == 1, s.gh.log()


if __name__ == "__main__":
    main(send_back_once, refusals, tickets_comment)
