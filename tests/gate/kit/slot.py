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
from that same ungranted agent runs."""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

from testkit import ROOT, Scratch, kit, main, pnpm_store, tool_homes
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
    s.env = {k: v for k, v in s.env.items() if k not in PANE}
    s.env |= {"XDG_STATE_HOME": str(s.root / "state"), "PYTHONPATH": str(ROOT)}


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
            "ask the director: octo-feather-slot grant gh7 --kind heavy",
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


if __name__ == "__main__":
    main(refused, granted, sandboxed, user_mise_gate)
