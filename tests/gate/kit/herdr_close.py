"""The scenarios of tests/gate/kit/test_herdr_close.py (its items), this file their command
(testkit.main): herdr-close over the testkit's Herdr world (testkit/herdr.py, FAKE_HERDR), each
run in a PID namespace of its own beside the one process the scenario tags (its sweep of tagged
processes sees only those), under a scenario-only HERDR_SESSION. Issue #76: a pane id closes its
tab exactly as that tab id would (same report, its tagged process TERMed); a pane id it cannot map
fails naming TAB|SPACE|PANE with nothing closed; tab and space ids close as before. Park (--park):
the hand-off line alone on stdout, the close report on stderr, the pane's original Pi session and
every field kept, its cwd's quote intact."""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

from testkit import ROOT, Ran, Scratch, main

if TYPE_CHECKING:
    from pathlib import Path

CLOSE = str(ROOT / ".agents" / "skills" / "herdr-comms" / "assets" / "herdr-close")
PIDNS = ("unshare", "--map-current-user", "--pid", "--fork", "--mount-proc")
# In the namespace: a process tagged with TAGS (the env assignments before the fifo's `--`),
# ready once it says so on the scenario's fifo (readiness through a pipe it owns, never a wait),
# then herdr-close ARGS; the tagged process's end (its wait status, 143 when TERMed) on stderr,
# KILLed first so the wait cannot hang (a fatal signal's exit status is the first one sent).
TAGGED = """f=$1; shift; tags=; while [ "$1" != -- ]; do tags="$tags $1"; shift; done; shift
env $tags sh -c 'echo ready > "$0"; exec sleep 300' "$f" & p=$!
read -r _ < "$f"
"$@"; rc=$?
kill -KILL "$p" 2>/dev/null; wait "$p"; echo "tagged exit $?" >&2
exit $rc
"""


def world(s: Scratch) -> Path:
    """S's Herdr world: agent impl in pane w6:p4 of tab w6:t4, idle; the caller no pane."""
    d = s.root / "herdr"
    d.mkdir()
    impl = {"name": "impl", "pane_id": "w6:p4", "workspace_id": "w6", "tab_id": "w6:t4"}
    (d / "agents.json").write_text(json.dumps({"w6:p4": impl | {"agent_status": "idle"}}))
    for k in [k for k in s.env if k.startswith(("HERDR_", "OCTO_FEATHER_"))]:
        del s.env[k]
    s.env |= {"FAKE_HERDR": str(d), "HERDR_SESSION": f"herdr-close-test-{os.getpid()}"}
    os.mkfifo(s.root / "ready")
    return d


def close(
    s: Scratch, *args: str, tags: tuple[str, ...] = (), want: int = 0, cwd: Path | None = None
) -> Ran:
    """herdr-close ARGS in a PID namespace, beside a process tagged TAGS (none: none)."""
    if not tags:
        return s.run([*PIDNS, CLOSE, *args], want=want, cwd=cwd)
    cmd = [*PIDNS, "sh", "-c", TAGGED, "sh", str(s.root / "ready"), *tags, "--", CLOSE, *args]
    return s.run(cmd, want=want, cwd=cwd)


def lines(p: Path) -> list[str]:
    return p.read_text().splitlines() if p.exists() else []


def close_ids(s: Scratch) -> None:
    """A pane id: its tab w6:t4 closed, tab= printed, the tab's tagged process TERMed by the
    sweep; an unknown pane id: non-zero, stderr naming TAB|SPACE|PANE, no close call; a tab id and
    a space id close as before (no process tagged: killed=0)."""
    d = world(s)
    ran = close(s, "w6:p4", tags=("HERDR_TAB_ID=w6:t4",))
    assert ran.out == "tab=w6:t4 tab_close_rc=0 killed=1", ran.out
    assert "tagged exit 143" in ran.err.splitlines(), f"tagged process not TERMed: {ran.err}"
    assert lines(d / "closed") == ["w6:t4"], lines(d / "closed")
    n = len(lines(d / "log"))
    ran = close(s, "w6:p7", want=65)
    assert "TAB|SPACE|PANE" in ran.err, ran.err
    assert not [x for x in lines(d / "log")[n:] if "close" in x], lines(d / "log")
    (d / "workspaces.json").write_text('[{"label": "gh6", "workspace_id": "w6"}]')
    ran = close(s, "w6:t4")
    assert ran.out == "tab=w6:t4 tab_close_rc=0 killed=0", ran.out
    assert lines(d / "closed") == ["w6:t4", "w6:t4"], lines(d / "closed")
    ran = close(s, "w6")
    assert ran.out == "space=w6 space_close_rc=0 killed=0", ran.out
    assert "workspace close w6" in lines(d / "log"), lines(d / "log")


def park(s: Scratch) -> None:
    """--park w6:p4, its Pi (herdr-spawn's tags: pane, tab, session, role, parent) running in a
    dir whose name holds a quote: stdout the parked JSON line alone (the original session, kind
    parked, that cwd, exactly its fields), stderr the close report, the Pi TERMed."""
    world(s)
    cwd = s.root / 'cwd"quoted'
    cwd.mkdir()
    tags = (
        "HERDR_PANE_ID=w6:p4",
        "HERDR_TAB_ID=w6:t4",
        "OCTO_FEATHER_SESSION_ID=original-session",
        "OCTO_FEATHER_ROLE=implementer",
        "OCTO_FEATHER_PARENT=w6:p1",
    )
    ran = close(s, "--park", "w6:p4", tags=tags, cwd=cwd)
    d = json.loads(ran.out)
    assert (d["session"], d["kind"], d["cwd"]) == ("original-session", "parked", str(cwd)), d
    fields = {"at", "kind", "pane", "name", "label", "role", "parent", "cwd", "session"}
    assert set(d) == fields, d
    assert "tab=w6:t4 tab_close_rc=0 killed=1" in ran.err.splitlines(), ran.err
    assert "tagged exit 143" in ran.err.splitlines(), ran.err


if __name__ == "__main__":
    main(close_ids, park)
