"""The heavy-run and eval slots (#668; owner ruling #660 2026-11-06), through the commands: the
gate's plugin as `just check-tests` loads it (`python -m pytest -p tests.gate.heavy_slot`) over a
scratch suite of 30 or 31 items, octo-feather-slot (grant, status) and octo-feather-qa, as an
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
supervisor and the director were told. follow_up: a follow-up run of gh7 inside the grace keeps
the slot; it passes after that run ends. queue_free: queued onto a free kind, granted at once and
told.

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

from testkit import HERE, ROOT, Scratch, kit, main, pnpm_store, tool_homes
from testkit.qc import qc, target

SLOT = kit("octo-feather-slot")
REFUSED = 75
LANES = {"gh7": "w9:p1", "gh8": "w8:p1"}
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
    many = f"import pytest\n@pytest.mark.parametrize('n', range({n}))\ndef test_n(n): pass\n"
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
    (s.bin / "herdr-say").symlink_to(HERE / "argv_recorder.sh")
    s.env = {k: v for k, v in s.env.items() if k not in PANE}
    s.env |= {"XDG_STATE_HOME": str(s.root / "state"), "PYTHONPATH": str(ROOT)}
    s.env |= {"ARGV_LOG": str(s.root / "said"), "OCTO_FEATHER_SLOT_GRACE": "0"}


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
    many = "import pytest\n@pytest.mark.parametrize('n', range(31))\ndef test_n(n): pass\n"
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


def said(s: Scratch) -> list[list[str]]:
    """Each herdr-say call's arguments, in order (testkit/argv_recorder.sh's records)."""
    log = s.root / "said"
    recs = log.read_text().split("\0\n") if log.exists() else []
    return [r.split("\0")[2:] for r in recs if r]


def holding(s: Scratch) -> subprocess.Popen[str]:
    """A 31-item heavy run of gh7's implementer, held by `hold` until its stdin closes."""
    cmd = [SLOT, "hold", "--kind", "heavy", "--items", "31"]
    env = {**s.env, **AGENT}
    p = subprocess.Popen(cmd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    assert p.stdout is not None
    line = p.stdout.readline()
    assert line.startswith("held: the heavy slot for lane gh7"), line
    return p


def end(p: subprocess.Popen[str]) -> None:
    assert p.stdin is not None
    p.stdin.close()
    assert p.wait(timeout=WAIT_S) == 0


def holder(s: Scratch, kind: str = "heavy") -> str:
    """KIND's holder line and queue line of `octo-feather-slot status`."""
    lines = s.run([SLOT, "status"]).out.splitlines()
    at = next(i for i, ln in enumerate(lines) if ln.startswith(f"{kind} ("))
    return "\n".join(ln for ln in lines[at + 1 : at + 4] if "holder:" in ln or "queue:" in ln)


def passed(s: Scratch) -> str:
    """The heavy holder and queue once gh8 holds it (within WAIT_S)."""
    stop = time.time() + WAIT_S
    while "holder: gh8 (granted " not in (st := holder(s)):
        assert time.time() < stop, f"the slot never passed to gh8: {st}"
        time.sleep(0.2)
    return st


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


def follow_up(s: Scratch) -> None:
    world(s)
    s.env |= {"OCTO_FEATHER_SLOT_GRACE": str(GRACE)}
    s.run([SLOT, "grant", "gh7", "--kind", "heavy"], env=DIRECTOR)
    s.run([SLOT, "queue", "gh8", "--kind", "heavy"], env=DIRECTOR)
    end(holding(s))
    p = holding(s)  # the follow-up run, inside the grace
    time.sleep(GRACE + 1.5)  # the first run's check has run
    st = holder(s)
    assert "holder: gh7 (granted " in st, st
    assert "1. gh8 (queued " in st, st
    assert said(s) == [], said(s)
    end(p)
    passed(s)


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
    s.env |= {"OCTO_FEATHER_SLOT_GRACE": "1"}
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


def new_reads_old(s: Scratch) -> None:
    world(s)
    s.env |= {"OCTO_FEATHER_SLOT_GRACE": "1"}
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
    time.sleep(2)  # past the grace; the release's own check has run
    s.run([SLOT, "settle", "--kind", "heavy"])
    st = holder(s)
    assert "holder: none" in st, st  # the revoked grant not brought back, nor passed
    assert "  queue: 1. gh8 (queued " in st, st
    time.sleep(1.1)  # a grant made again: a new since
    s.run([old, "grant", "gh7", "--kind", "heavy"], env=DIRECTOR)
    s.run([SLOT, "settle", "--kind", "heavy"])
    st = holder(s)
    assert "holder: gh7 (granted " in st, st  # a fresh grant: no run seen under it
    assert "  queue: 1. gh8 (queued " in st, st
    assert said(s) == [], said(s)


if __name__ == "__main__":
    main(
        refused,
        granted,
        sandboxed,
        user_mise_gate,
        queued,
        follow_up,
        queue_free,
        old_reads_new,
        new_reads_old,
    )
