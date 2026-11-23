"""The heavy-run and eval slots (#668; owner ruling #660 2026-11-06), through the commands: the
gate's plugin as `just check-tests` loads it (`python -m pytest -p tests.gate.heavy_slot`) over a
scratch suite of 30 or 31 items (end-to-end by pytest's e2e marker, so no run of it is the fast
tier's: quality #recipes-static-first), octo-feather-slot (grant, status) and octo-feather-qa, as an
implementer of lane gh7 (its pane in gh7's space, its parent gh7's supervisor) or the director,
with a scratch XDG_STATE_HOME holding the box's slot files and the session's lane records.

refused: a 31-item run without gh7's grant stops before any item runs, naming its count, the
threshold, the current holder (gh8) and the grant to ask for; 30 items need none, and neither
does a run outside a Herdr agent; a non-director's grant is refused. granted: with gh7's grant
the run holds the slot (status names its run) while a nested 31-item run under it is not
refused, a second concurrent one is, and qa needs its own eval grant, then runs beside it.
sandboxed: a 31-item run inside the qc sandbox (a `just qc` demo, as qa runs its cases there)
from that same ungranted agent runs.

The queue (owner ruling 2026-11-14 #906, #976), herdr-say a stand-in first on PATH recording each
message (testkit/argv_recorder.sh), the grace shortened through OCTO_FEATHER_SLOT_GRACE:
queued: queue is the director's and checks its lane; gh8 queued once onto gh7's full heavy slot,
status lists it; nothing passes before a run started under gh7's grant, nor while its run holds
past the grace; after the run ends and the grace passes gh8 holds it, off the queue, and its
supervisor and the director were told. queue_free: queued onto a free kind, granted at once and
told. The hand-over's follow_up and regranted: in-process, tests/gate/kit/test_slot_queue.py.
back_to_back (quality #recipes-static-first, #1113, #1163): two gates of gh7 through the plugin,
one after the other on a grace of WAIT_S, gh8 queued, so no check passes the slot while a gate
starts. The grace is shown over by a check whose own grace is 0 (OCTO_FEATHER_SLOT_GRACE in its
env: octo-feather-slot --help, the grace), never by a sleep: during the second gate's static
check a grace-0 status still shows gh7 holding (its second gate took its slot before it, `hold
--if-granted`), its run holding the lock, gh8 queued, nobody told; after it ends a status at the
long grace, once heavy's own run line says none, keeps gh7, and a grace-0 settle hands to gh8
and tells it and the director.

Compatibility with the reader every unmerged worktree on the box still runs against the one slots
dir: main's octo-feather-slot at 53dacfca (gh906's base, the last commit before the queue), its
text from `git show` (CI checks out full history) written as a scratch kit's command (beside it a
link to octo-feather-state; no gate-budget.toml, so its defaults, the same counts). old_reads_new:
after the queue's commands (queue, hold, release, settle, hand-over) the old command's status names
the holder and the run holding it, and its revoke and grant succeed. new_reads_old: the old
command's grants read by the new; a queued lane the old command grants leaves the queue at the
check; a grant the old command revoked is not brought back; one it made again is a fresh grant,
no earlier run's end inherited, so nothing passes."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from testkit import ROOT, Scratch, kit, main, pnpm_store, tool_homes
from testkit.qc import qc, target

SLOT = kit("octo-feather-slot")
REFUSED = 75
LANES = {"gh7": "w9:p1", "gh8": "w8:p1", "gh6": "w6:p1"}
DIRECTOR = {"OCTO_FEATHER_ROLE": "director", "HERDR_PANE_ID": "w1:p1"}
# An implementer of lane gh7: its own pane in gh7's space, its parent gh7's supervisor.
AGENT = {
    "OCTO_FEATHER_ROLE": "implementer",
    "HERDR_PANE_ID": "w9:p3",
    "OCTO_FEATHER_PARENT": "w9:p1",
    "HERDR_WORKSPACE_ID": "w9",
}
PANE = (*AGENT, "HERDR_SESSION", "OCTO_FEATHER_SPEND_SPACE")
WAIT_S = 60
BOUND = 30  # the bound's checks a scenario starts outlive it this long at most
# The stand-in herdr-say (Herdr, a system the kit does not own): one record per call, as
# testkit/argv_recorder.sh's (NUL-terminated fields, then a newline), its name, the Herdr session
# it was sent in (HERDR_SESSION, or default), then its argv.
SAY = """#!/bin/sh
printf '%s\\0' herdr-say "${HERDR_SESSION:-default}" "$@" >>"$ARGV_LOG"
echo >>"$ARGV_LOG"
"""
# One item of the granted run: a nested 31-item run under it, then it waits for the scenario.
HOLD = """import os, subprocess, sys, time
from pathlib import Path

def test_hold():
    inner = subprocess.run([sys.executable, *{inner!r}], capture_output=True, text=True)
    Path({nested!r}).write_text(f"{{inner.returncode}}\\n{{inner.stdout}}")
    Path({ready!r}).touch()
    end = time.time() + {wait}
    while not Path({done!r}).exists():
        assert time.time() < end, "the scenario never said done"
        time.sleep(0.1)
"""


def gate(workers: int) -> list[str]:
    """The gate's pytest with the plugin, as check-tests runs it, on WORKERS xdist workers."""
    return [sys.executable, "-m", "pytest", "-q", "-p", "tests.gate.heavy_slot", "-n", str(workers)]


def suite(s: Scratch, name: str, n: int, extra: str = "", *, trend: bool = False) -> Path:
    """S's suite NAME: N trivial items, plus EXTRA as one more test file; with TREND, the gate's
    runner (tests/gate/conftest.py, copyable unchanged) and its junit xml, so a run that reaches
    its session's end writes its trend line."""
    d = s.root / name
    d.mkdir()
    junit = " --junitxml=junit.xml" if trend else ""
    (d / "pytest.ini").write_text(f"[pytest]\naddopts = -p no:cacheprovider{junit}\n")
    if trend:
        shutil.copy(ROOT / "tests" / "gate" / "conftest.py", d)
    many = (
        "import pytest\n@pytest.mark.e2e\n"
        f"@pytest.mark.parametrize('n', range({n}))\ndef test_n(n): pass\n"
    )
    (d / "test_many.py").write_text(many)
    if extra:
        (d / "test_extra.py").write_text(extra)
    return d


def world(s: Scratch) -> None:
    """The scratch box: its state dir, gh7's and gh8's lane records, the kit importable."""
    lanes = s.root / "state" / "octo-feather" / "lanes"
    lanes.mkdir(parents=True)
    for lane, sup in LANES.items():
        (lanes / f"{lane}.toml").write_text(f'supervisor = "{sup}"\n')
    (lanes.parent / "director.toml").write_text('pane = "w1:p1"\n')
    (s.bin / "herdr-say").write_text(SAY)
    (s.bin / "herdr-say").chmod(0o755)
    s.env = {k: v for k, v in s.env.items() if k not in PANE}
    s.env |= {"XDG_STATE_HOME": str(s.root / "state"), "PYTHONPATH": str(ROOT)}
    s.env |= {"ARGV_LOG": str(s.root / "said"), "OCTO_FEATHER_SLOT_GRACE": "0"}
    s.env |= {"OCTO_FEATHER_SLOT_BOUND": str(BOUND)}


def run_gate(s: Scratch, d: Path, *, want: int, env: dict[str, str], workers: int = 2) -> str:
    ran = s.run(gate(workers), cwd=d, want=want, env=env)
    return ran.out + ran.err


def refused(s: Scratch) -> None:
    world(s)
    no = s.run([SLOT, "grant", "gh7", "--kind", "heavy"], want=77, env=AGENT)
    assert "grant is the director's" in no.err, no.err
    s.run([SLOT, "grant", "gh8", "--kind", "heavy"], env=DIRECTOR)
    big = suite(s, "big", 31, trend=True)
    trend = s.root / "state" / "octo-feather" / "check-runs.jsonl"
    for workers in (0, 2):
        out = run_gate(s, big, want=REFUSED, env=AGENT, workers=workers)
        for want in (
            "refused, nothing ran: this heavy run selects 31 items, over heavy_items 30",
            "lane gh7 holds no heavy grant; current holder: gh8 (granted ",
            "ask the director: octo-feather-slot queue gh7 --kind heavy",
        ):
            assert want in out, out
        assert "passed" not in out, out
        assert not trend.exists(), "a refused run wrote a trend line"
        assert not (big / "junit.xml").exists(), "a refused run wrote its junit xml"
    assert "31 passed" in run_gate(s, big, want=0, env={})  # outside a Herdr agent
    assert len(trend.read_text().splitlines()) == 1, "the run that ran wrote no trend line"
    small = run_gate(s, suite(s, "small", 30), want=0, env=AGENT)
    assert "heavy slot: free: 30 items" in small, small
    assert "30 passed" in small, small


def granted(s: Scratch) -> None:
    world(s)
    s.run([SLOT, "grant", "gh7", "--kind", "heavy"], env=DIRECTOR)
    inner = suite(s, "inner", 31)
    files = {f: str(s.root / f) for f in ("nested", "ready", "done")}
    hold = HOLD.format(inner=[*gate(0)[1:], str(inner)], wait=WAIT_S, **files)
    outer = suite(s, "outer", 30, hold)
    env = {**s.env, **AGENT}
    with subprocess.Popen(gate(2), cwd=outer, env=env, stdout=subprocess.PIPE, text=True) as p:
        try:
            end = time.time() + WAIT_S
            while not Path(files["ready"]).exists():
                assert p.poll() is None, f"the outer run ended: {p.communicate()[0]}"
                assert time.time() < end, "the outer run never got ready"
                time.sleep(0.1)
            nested = Path(files["nested"]).read_text()
            assert nested.startswith("0\n"), nested
            assert "heavy slot: nested: under the heavy run pid " in nested, nested
            st = s.run([SLOT, "status"]).out
            assert f"run holding it now: pid {p.pid} of lane gh7 since " in st, st
            assert "holder: gh7 (granted " in st, st
            second = run_gate(s, suite(s, "second", 31), want=REFUSED, env=AGENT, workers=0)
            assert "lane gh7 holds the heavy grant, but every heavy slot is held now" in second
            assert f"by a run: pid {p.pid} of lane gh7" in second, second
            qa = [kit("octo-feather-qa"), "--suite", "no-such-suite"]
            no = s.run(qa, want=REFUSED, env=AGENT)
            assert "this eval run (octo-feather-qa) runs model evals, and lane gh7" in no.err
            assert "ask the director: octo-feather-slot grant gh7 --kind eval" in no.err, no.err
            s.run([SLOT, "grant", "gh7", "--kind", "eval"], env=DIRECTOR)
            ok = s.run(qa, want=64, env=AGENT)  # past the slot: the unknown suite
            assert "qa: eval slot: held: the eval slot for lane gh7" in ok.out, ok.out
            assert "no suite no-such-suite" in ok.err, ok.err
        finally:
            Path(files["done"]).touch()
        out = p.communicate(timeout=WAIT_S)[0]
    assert p.returncode == 0, out
    assert "heavy slot: held: the heavy slot for lane gh7" in out, out
    assert "31 passed" in out, out
    assert "run holding it now: none" in s.run([SLOT, "status"]).out


def user_mise_gate(s: Scratch) -> None:
    """`just check-user-mise` (tests/user-mise.sh --gate) in the fixture's pane: the run takes the
    heavy slot in the caller's env and lane, so it is refused without gh7's grant, naming it; with
    it, it holds the slot and the gate in the fixture's pane runs nested under it."""
    world(s)
    s.env |= tool_homes() | {"npm_config_store_dir": pnpm_store()}
    big = str(suite(s, "big", 31))
    cmd = [str(ROOT / "tests" / "user-mise.sh"), "--gate", big]
    no = s.run(cmd, want=REFUSED, env=AGENT)
    assert "ask the director: octo-feather-slot grant gh7 --kind heavy" in no.err, no.err
    s.run([SLOT, "grant", "gh7", "--kind", "heavy"], env=DIRECTOR)
    ran = s.run(cmd, env=AGENT)
    out = ran.out + ran.err
    for want in (
        "user-mise: heavy slot: held: the heavy slot for lane gh7, run pid ",
        "heavy slot: nested: under the heavy run pid ",
        "31 passed",
    ):
        assert want in out, out


QC_TOML = """format = 1
[entry]
command = "true"
[services]
[fixture]
[values]
[demo."demo#acceptance-a"]
command = "{cmd}"
covers = ["src/a"]
tests = ["tests/a.sh"]
"""


def sandboxed(s: Scratch) -> None:
    world(s)
    run = (
        f"out=$(PYTHONPATH={ROOT} {' '.join(gate(0))} big) && echo $out | grep -q '31 passed' "
        "&& echo $out | grep -q 'heavy slot: free: outside a Herdr agent'"
    )
    files = {"qc.toml": QC_TOML.format(cmd=run)}
    many = (
        "import pytest\n@pytest.mark.e2e\n"
        "@pytest.mark.parametrize('n', range(31))\ndef test_n(n): pass\n"
    )
    files |= {"big/pytest.ini": "[pytest]\naddopts = -p no:cacheprovider\n"}
    files |= {"big/test_many.py": many}
    target(s, files)
    ran = qc(s, s.root / "repo", "5", "acceptance-a", want=0, env={**AGENT, **tool_homes()})
    assert "PASS acceptance-a" in ran.out, ran.out


GRACE = 2
TOLD = (
    "octo-feather-slot: the heavy slot is granted to lane gh8 until {until} (lane gh7's run "
    f"ended, no run within the {GRACE} s grace); run your heavy run now."
)
PASSED = "octo-feather-slot: heavy slot passed from lane gh7 to lane gh8; queue left: none."


def records(s: Scratch) -> list[list[str]]:
    """Each herdr-say call's record (SAY), in order."""
    log = s.root / "said"
    recs = log.read_text().split("\0\n") if log.exists() else []
    return [r.split("\0") for r in recs if r]


def said(s: Scratch) -> list[list[str]]:
    """Each herdr-say call's arguments, in order."""
    return [r[2:] for r in records(s)]


def said_n(s: Scratch, n: int) -> list[list[str]]:
    """The herdr-say calls, once N were made (within WAIT_S)."""
    stop = time.time() + WAIT_S
    while len(said(s)) < n and time.time() < stop:
        time.sleep(0.2)
    return said(s)


# An implementer of lane gh8, as AGENT is of gh7.
AGENT8 = {**AGENT, "HERDR_PANE_ID": "w8:p3", "OCTO_FEATHER_PARENT": "w8:p1"}
AGENT8["HERDR_WORKSPACE_ID"] = "w8"


def holding(
    s: Scratch, lane: str = "gh7", env: dict[str, str] | None = None
) -> subprocess.Popen[str]:
    """A 31-item heavy run of LANE's implementer (gh7 or gh8), held by `hold` until its stdin
    closes; ENV over the scratch's."""
    cmd = [SLOT, "hold", "--kind", "heavy", "--items", "31"]
    env = {**s.env, **(AGENT8 if lane == "gh8" else AGENT), **(env or {})}
    p = subprocess.Popen(cmd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    assert p.stdout is not None
    line = p.stdout.readline()
    assert line.startswith(f"held: the heavy slot for lane {lane}"), line
    return p


def end(p: subprocess.Popen[str]) -> None:
    assert p.stdin is not None
    p.stdin.close()
    assert p.wait(timeout=WAIT_S) == 0


def section(s: Scratch, kind: str = "heavy") -> list[str]:
    """KIND's holder, run and queue lines of `octo-feather-slot status`."""
    lines = s.run([SLOT, "status"]).out.splitlines()
    at = next(i for i, ln in enumerate(lines) if ln.startswith(f"{kind} ("))
    return lines[at + 1 : at + 4]


def holder(s: Scratch, kind: str = "heavy") -> str:
    """KIND's holder line and queue line of `octo-feather-slot status`."""
    return "\n".join(ln for ln in section(s, kind) if "holder:" in ln or "queue:" in ln)


def passed(s: Scratch, lane: str = "gh8") -> str:
    """The heavy holder and queue once LANE holds it (within WAIT_S)."""
    stop = time.time() + WAIT_S
    while f"holder: {lane} (granted " not in (st := holder(s)):
        assert time.time() < stop, f"the slot never passed to {lane}: {st}"
        time.sleep(0.2)
    return st


def until(st: str) -> str:
    """The expiry in a status holder line ST."""
    return st.split(", expires ", 1)[1].split(")", 1)[0]


def sent(pane: str, msg: str) -> list[str]:
    """A herdr-say call's arguments: MSG to PANE."""
    return ["--timeout", "60", pane, msg]


def freed_to(grace: int, lane: str = "gh8") -> str:
    """The director's notice of a free slot granted to LANE, the queue then empty."""
    return (
        f"octo-feather-slot: heavy slot free for the {grace} s grace, granted to lane {lane}; "
        "queue left: none."
    )


def granted_to(lane: str, kind: str, expires: str, why: str) -> str:
    return (
        f"octo-feather-slot: the {kind} slot is granted to lane {lane} until {expires} ({why}); "
        f"run your {kind} run now."
    )


def queued(s: Scratch) -> None:
    world(s)
    s.env |= {"OCTO_FEATHER_SLOT_GRACE": str(GRACE)}
    no = s.run([SLOT, "queue", "gh8", "--kind", "heavy"], want=77, env=AGENT)
    assert "queue is the director's" in no.err, no.err
    gone = s.run([SLOT, "queue", "gh9", "--kind", "heavy"], want=64, env=DIRECTOR)
    assert "no lane gh9 in " in gone.err, gone.err
    s.run([SLOT, "grant", "gh7", "--kind", "heavy"], env=DIRECTOR)
    q = s.run([SLOT, "queue", "gh8", "--kind", "heavy"], env=DIRECTOR).out
    assert q == "queued: lane gh8 for the heavy slot, position 1", q
    again = s.run([SLOT, "queue", "gh8", "--kind", "heavy"], env=DIRECTOR).out
    assert again == "gh8 is already queued for the heavy slot, position 1; nothing changed", again
    st = holder(s)
    assert "holder: gh7 (granted " in st, st
    assert "  queue: 1. gh8 (queued " in st, st
    assert " by w1:p1)" in st, st
    s.run([SLOT, "settle", "--kind", "heavy"])  # no run yet under gh7's grant: nothing passes
    p = holding(s)
    time.sleep(GRACE + 1)
    s.run([SLOT, "settle", "--kind", "heavy"])  # its run holds the lock past the grace
    assert "holder: gh7 (granted " in holder(s), holder(s)
    assert said(s) == [], said(s)
    end(p)
    st = passed(s)
    assert "  queue: none" in st, st
    until = st.split(", expires ", 1)[1].split(")", 1)[0]
    want = [
        ["--timeout", "60", "w8:p1", TOLD.format(until=until)],
        ["--timeout", "60", "w1:p1", PASSED],
    ]
    stop = time.time() + WAIT_S
    while len(said(s)) < len(want) and time.time() < stop:
        time.sleep(0.2)
    assert said(s) == want, said(s)


def queue_free(s: Scratch) -> None:
    world(s)
    got = s.run([SLOT, "queue", "gh8", "--kind", "eval"], env=DIRECTOR).out
    assert got.startswith("granted: eval slot to lane gh8 (granted "), got
    until = got.split(", expires ", 1)[1].split(")", 1)[0]
    told = (
        f"octo-feather-slot: the eval slot is granted to lane gh8 until {until} (queued onto a "
        "free slot); run your eval run now."
    )
    assert said(s) == [["--timeout", "60", "w8:p1", told]], said(s)
    st = holder(s, "eval")
    assert "holder: gh8 (granted " in st, st
    assert "  queue: none" in st, st


OLD = "53dacfca"


def old_slot(s: Scratch) -> str:
    """Main's octo-feather-slot at OLD, as a scratch kit's command."""
    scripts = s.root / "oldkit" / "scripts"
    scripts.mkdir(parents=True)
    show = ["git", "-C", str(ROOT), "show", f"{OLD}:scripts/octo-feather-slot"]
    text = subprocess.run(show, capture_output=True, text=True, check=True).stdout
    (scripts / "octo-feather-slot").write_text(text)
    (scripts / "octo-feather-slot").chmod(0o755)
    (scripts / "octo-feather-state").symlink_to(ROOT / "scripts" / "octo-feather-state")
    return str(scripts / "octo-feather-slot")


def old_reads_new(s: Scratch) -> None:
    world(s)
    s.env |= {"OCTO_FEATHER_SLOT_GRACE": "3"}
    old = old_slot(s)
    s.run([SLOT, "grant", "gh7", "--kind", "heavy"], env=DIRECTOR)
    s.run([SLOT, "queue", "gh8", "--kind", "heavy"], env=DIRECTOR)
    p = holding(s)
    st = s.run([old, "status"]).out
    assert "holder: gh7 (granted " in st, st
    assert f"run holding it now: pid {os.getpid()} of lane gh7" in st, st
    end(p)
    st = s.run([old, "status"]).out
    assert "holder: gh7 (granted " in st, st  # the run's end, written where the old never reads
    passed(s)
    st = s.run([old, "status"]).out
    assert "holder: gh8 (granted " in st, st
    s.run([SLOT, "settle", "--kind", "heavy"])
    assert "holder: gh8 (granted " in s.run([old, "status"]).out
    s.run([old, "revoke", "gh8", "--kind", "heavy"], env=DIRECTOR)
    s.run([old, "grant", "gh7", "--kind", "heavy"], env=DIRECTOR)
    st = s.run([old, "status"]).out
    assert "holder: gh7 (granted " in st, st
    assert "gh8" not in st, st
    s.run([SLOT, "queue", "gh8", "--kind", "heavy"], env=DIRECTOR)
    s.run([SLOT, "revoke", "gh7", "--kind", "heavy"], env=DIRECTOR)  # a free slot in its grace
    assert "holder: none" in s.run([old, "status"]).out
    s.run([old, "grant", "gh6", "--kind", "heavy"], env=DIRECTOR)
    assert "holder: gh6 (granted " in s.run([old, "status"]).out
    time.sleep(2.2)  # past gh6's bound below
    s.run([SLOT, "settle", "--kind", "heavy"], env={"OCTO_FEATHER_SLOT_BOUND": "1"})  # passed over
    st = s.run([old, "status"]).out
    assert "holder: gh8 (granted " in st, st
    assert " by queue, " in st, st
    s.run([old, "revoke", "gh8", "--kind", "heavy"], env=DIRECTOR)
    s.run([old, "grant", "gh7", "--kind", "heavy"], env=DIRECTOR)
    assert "holder: gh7 (granted " in s.run([old, "status"]).out


def new_reads_old(s: Scratch) -> None:
    world(s)
    grace = 3
    s.env |= {"OCTO_FEATHER_SLOT_GRACE": str(grace)}
    old = old_slot(s)
    s.run([old, "grant", "gh7", "--kind", "heavy"], env=DIRECTOR)
    s.run([SLOT, "queue", "gh8", "--kind", "heavy"], env=DIRECTOR)
    st = holder(s)
    assert "holder: gh7 (granted " in st, st
    assert "  queue: 1. gh8 (queued " in st, st
    s.run([old, "revoke", "gh7", "--kind", "heavy"], env=DIRECTOR)  # the queued lane, by hand
    s.run([old, "grant", "gh8", "--kind", "heavy"], env=DIRECTOR)
    s.run([SLOT, "settle", "--kind", "heavy"])
    st = holder(s)
    assert "holder: gh8 (granted " in st, st
    assert "  queue: none" in st, st
    s.run([old, "revoke", "gh8", "--kind", "heavy"], env=DIRECTOR)
    s.run([old, "grant", "gh7", "--kind", "heavy"], env=DIRECTOR)
    s.run([SLOT, "queue", "gh8", "--kind", "heavy"], env=DIRECTOR)
    end(holding(s))  # a run ended under gh7's grant
    s.run([old, "revoke", "gh7", "--kind", "heavy"], env=DIRECTOR)
    time.sleep(1.1)  # a grant made again: a new since; inside the grace
    s.run([old, "grant", "gh7", "--kind", "heavy"], env=DIRECTOR)
    time.sleep(grace + 0.5)  # the release's own check has run
    s.run([SLOT, "settle", "--kind", "heavy"])
    st = holder(s)
    assert "holder: gh7 (granted " in st, st  # a fresh grant: no earlier run's end inherited
    assert "  queue: 1. gh8 (queued " in st, st
    s.run([old, "revoke", "gh7", "--kind", "heavy"], env=DIRECTOR)  # a free slot, seen by a check
    s.run([SLOT, "settle", "--kind", "heavy"])
    st = s.run([SLOT, "status"]).out
    assert "holder: none" in st, st
    assert f"to the queue's head after the {grace} s grace" in st, st
    s.run([old, "grant", "gh6", "--kind", "heavy"], env=DIRECTOR)  # inside the grace: it wins
    time.sleep(grace + 0.5)
    s.run([SLOT, "settle", "--kind", "heavy"])
    st = holder(s)
    assert "holder: gh6 (granted " in st, st
    assert "  queue: 1. gh8 (queued " in st, st
    assert said(s) == [], said(s)
    s.run([old, "revoke", "gh6", "--kind", "heavy"], env=DIRECTOR)
    s.run([SLOT, "status"])  # first seen free: the grace starts
    st = passed(s)
    why = f"the slot free for the {grace} s grace"
    want = [
        sent("w8:p1", granted_to("gh8", "heavy", until(st), why)),
        sent("w1:p1", freed_to(grace)),
    ]
    assert said_n(s, 2) == want, said(s)


def passed_over(s: Scratch) -> None:
    world(s)
    bound = 3
    s.env |= {"OCTO_FEATHER_SLOT_BOUND": str(bound)}
    s.run([SLOT, "grant", "gh7", "--kind", "heavy"], env=DIRECTOR)
    s.run([SLOT, "queue", "gh8", "--kind", "heavy"], env=DIRECTOR)
    st = holder(s)
    assert "holder: gh7 (granted " in st, st  # inside the bound
    t0 = time.time()
    st = passed(s)
    assert time.time() - t0 >= bound - 2, "passed over before the bound"
    assert "holder: gh8 (granted " in st, st
    assert " by queue, " in st, st
    assert "  queue: none" in st, st
    over = f"lane gh7 started no heavy run within the {bound} s bound"
    told_over = (
        f"octo-feather-slot: lane gh7's heavy grant passed to lane gh8: no heavy run started under "
        f"it within the {bound} s bound; to run, ask the director: octo-feather-slot queue gh7 "
        "--kind heavy."
    )
    moved = (
        f"octo-feather-slot: heavy slot passed over lane gh7 (no run within the {bound} s bound) "
        "to lane gh8; queue left: none."
    )
    want = [
        sent("w8:p1", granted_to("gh8", "heavy", until(st), over)),
        sent("w9:p1", told_over),
        sent("w1:p1", moved),
    ]
    assert said_n(s, 3) == want, said(s)


def unused_alone(s: Scratch) -> None:
    """A grant no run starts under, past the bound, with the queue empty: nothing changes."""
    world(s)
    s.env |= {"OCTO_FEATHER_SLOT_BOUND": "1"}
    s.run([SLOT, "grant", "gh7", "--kind", "heavy"], env=DIRECTOR)
    grants = s.root / "state" / "octo-feather" / "slots" / "heavy.json"
    before = grants.stat().st_mtime_ns, grants.read_text()
    time.sleep(2.2)
    out = s.run([SLOT, "settle", "--kind", "heavy"]).out
    assert "settle heavy: nothing passes (queue: none)" in out, out
    st = holder(s)
    assert "holder: gh7 (granted " in st, st
    assert (grants.stat().st_mtime_ns, grants.read_text()) == before
    assert not grants.with_name("heavy.queue.json").exists()
    assert said(s) == [], said(s)


def revoked(s: Scratch) -> None:
    world(s)
    s.env |= {"OCTO_FEATHER_SLOT_GRACE": str(GRACE)}
    s.run([SLOT, "grant", "gh7", "--kind", "heavy"], env=DIRECTOR)
    s.run([SLOT, "queue", "gh8", "--kind", "heavy"], env=DIRECTOR)
    s.run([SLOT, "queue", "gh6", "--kind", "heavy"], env=DIRECTOR)
    out = s.run([SLOT, "revoke", "gh6", "--kind", "heavy"], env=DIRECTOR).out
    assert out == "gh6 held no heavy grant\ndequeued: lane gh6 off the heavy queue", out
    out = s.run([SLOT, "revoke", "gh7", "--kind", "heavy"], env=DIRECTOR).out
    assert out.startswith("revoked: heavy slot of lane gh7\n"), out
    t0 = time.time()
    st = s.run([SLOT, "status"]).out
    assert "  holder: none" in st, st  # gh7 gone from grants and queue; gh8 not yet granted
    assert "  queue: 1. gh8 (queued " in st, st
    assert "gh7" not in st, st
    assert "gh6" not in st, st
    assert f"to the queue's head after the {GRACE} s grace" in st, st
    st = passed(s)
    assert time.time() - t0 >= GRACE - 1, "granted before the grace"
    assert "  queue: none" in st, st
    why = f"the slot free for the {GRACE} s grace"
    want = [
        sent("w8:p1", granted_to("gh8", "heavy", until(st), why)),
        sent("w1:p1", freed_to(GRACE)),
    ]
    assert said_n(s, 2) == want, said(s)
    s.run([SLOT, "queue", "gh7", "--kind", "heavy"], env=DIRECTOR)
    s.run([SLOT, "revoke", "gh8", "--kind", "heavy"], env=DIRECTOR)
    out = s.run([SLOT, "grant", "gh6", "--kind", "heavy"], env=DIRECTOR).out  # inside the grace
    assert out.startswith("granted: heavy slot to lane gh6 "), out
    time.sleep(GRACE + 1)
    s.run([SLOT, "settle", "--kind", "heavy"])
    st = holder(s)
    assert "holder: gh6 (granted " in st, st  # the director's choice kept
    assert "  queue: 1. gh7 (queued " in st, st
    assert len(said(s)) == 2, said(s)


def queued_late(s: Scratch) -> None:
    """A lane queued after its holder's run ended a grace ago gets the slot at once; a hand-over
    whose check has not fired (its grace long) is made by the next command, a status."""
    world(s)
    s.env |= {"OCTO_FEATHER_SLOT_GRACE": "1"}
    s.run([SLOT, "grant", "gh7", "--kind", "heavy"], env=DIRECTOR)
    end(holding(s))
    time.sleep(1.5)
    q = s.run([SLOT, "queue", "gh8", "--kind", "heavy"], env=DIRECTOR)
    assert q.out == "queued: lane gh8 for the heavy slot, position 1", q.out
    assert "settle heavy: passed from lane gh7 to lane gh8" in q.err, q.err
    assert "holder: gh8 (granted " in s.run([old_slot(s), "status"]).out  # it settles nothing
    s.run([SLOT, "queue", "gh7", "--kind", "heavy"], env=DIRECTOR)
    end(holding(s, "gh8", {"OCTO_FEATHER_SLOT_GRACE": str(WAIT_S)}))  # its check far off
    time.sleep(1.5)
    st = holder(s)  # the status settles it first
    assert "holder: gh7 (granted " in st, st
    assert "  queue: none" in st, st


# A static check (its node id the gate's, tests/gate/heavy_slot.py's STATIC) that says it started,
# then runs until the scenario says done.
STATIC = """import time
from pathlib import Path

import pytest

@pytest.mark.parametrize("name", ["slow"])
def test_recipe(name):
    Path({ready!r}).touch()
    end = time.time() + {wait}
    while not Path({done!r}).exists():
        assert time.time() < end, "the scenario never said done"
        time.sleep(0.1)
"""


def unheld(s: Scratch) -> str:
    """The heavy holder and queue once no run holds the heavy slot (within WAIT_S): a run's end
    is recorded before its lock is freed, so it is recorded then."""
    stop = time.time() + WAIT_S
    while "  run holding it now: none" not in (heavy := section(s)):
        assert time.time() < stop, "the run's heavy hold never ended: " + "\n".join(heavy)
        time.sleep(0.2)
    return holder(s)


def back_to_back(s: Scratch) -> None:
    world(s)
    s.env |= {"OCTO_FEATHER_SLOT_GRACE": str(WAIT_S)}  # no check passes the slot on its own
    over = {"OCTO_FEATHER_SLOT_GRACE": "0"}  # a check this makes: every grace over
    s.run([SLOT, "grant", "gh7", "--kind", "heavy"], env=DIRECTOR)
    s.run([SLOT, "queue", "gh8", "--kind", "heavy"], env=DIRECTOR)
    first = run_gate(s, suite(s, "first", 31), want=0, env=AGENT)
    assert "heavy slot: held: the heavy slot for lane gh7" in first, first
    assert "holder: gh7 (granted " in unheld(s)  # its hold gone, its end recorded
    files = {f: str(s.root / f) for f in ("ready", "done")}
    second = suite(s, "second", 31)
    (second / "tests" / "gate").mkdir(parents=True)
    (second / "tests" / "gate" / "test_gate.py").write_text(STATIC.format(wait=WAIT_S, **files))
    env = {**s.env, **AGENT}
    with subprocess.Popen(gate(2), cwd=second, env=env, stdout=subprocess.PIPE, text=True) as p:
        try:
            stop = time.time() + WAIT_S
            while not Path(files["ready"]).exists():
                assert p.poll() is None, f"the second gate ended: {p.communicate()[0]}"
                assert time.time() < stop, "the static check never started"
                time.sleep(0.1)
            st = s.run([SLOT, "status"], env=over).out  # the first gate's grace over
            assert "holder: gh7 (granted " in st, st
            assert "  queue: 1. gh8 (queued " in st, st
            assert f"run holding it now: pid {p.pid} of lane gh7 since " in st, st
            assert said(s) == [], said(s)
        finally:
            Path(files["done"]).touch()
        out = p.communicate(timeout=WAIT_S)[0]
    assert p.returncode == 0, out
    assert "heavy slot: held: the heavy slot for lane gh7" in out, out
    assert "32 passed" in out, out
    st = unheld(s)  # its end recorded: inside its grace
    assert "holder: gh7 (granted " in st, st
    assert "  queue: 1. gh8 (queued " in st, st
    assert said(s) == [], said(s)
    s.run([SLOT, "settle", "--kind", "heavy"], env=over)
    st = holder(s)
    assert "holder: gh8 (granted " in st, st
    assert "  queue: none" in st, st
    why = "lane gh7's run ended, no run within the 0 s grace"
    want = [sent("w8:p1", granted_to("gh8", "heavy", until(st), why)), sent("w1:p1", PASSED)]
    assert said_n(s, 2) == want, said(s)


def two_sessions(s: Scratch) -> None:
    """Holder gh7 in the default session, gh8 queued from session sb: both notices go to sb."""
    world(s)
    s.env |= {"OCTO_FEATHER_SLOT_GRACE": str(GRACE)}
    sb = s.root / "state" / "octo-feather" / "sessions" / "sb"
    (sb / "lanes").mkdir(parents=True)
    (sb / "lanes" / "gh8.toml").write_text('supervisor = "w8:p1"\n')
    (sb / "director.toml").write_text('pane = "w2:p1"\n')
    s.run([SLOT, "grant", "gh7", "--kind", "heavy"], env=DIRECTOR)
    s.run([SLOT, "queue", "gh8", "--kind", "heavy"], env={**DIRECTOR, "HERDR_SESSION": "sb"})
    end(holding(s))
    st = passed(s)
    said_n(s, 2)
    assert [r[1] for r in records(s)] == ["sb", "sb"], records(s)
    assert said(s) == [
        ["--timeout", "60", "w8:p1", TOLD.format(until=until(st))],
        ["--timeout", "60", "w2:p1", PASSED],
    ], said(s)


if __name__ == "__main__":
    main(
        refused,
        granted,
        sandboxed,
        user_mise_gate,
        queued,
        queue_free,
        old_reads_new,
        new_reads_old,
        passed_over,
        unused_alone,
        revoked,
        queued_late,
        two_sessions,
        back_to_back,
    )
