"""quality #acceptance-fast-slot-free (#1210; the rule: quality #recipes-static-first), through
`just fast`, `just check` and `just test` in a throwaway git copy of the kit
(tests/gate/kit/gate_recipes_first.py's: test items tests/a.sh and tests/b.sh each logging its name
to its run's PROBE, tests/a.sh end-to-end by its header; here one static check, check-probe, so two
gate runs fit one item's CPU budget), each item logging with its name the processor and disk
priority it runs at (nice(1), ionice(1)), whose octo-feather-slot is the kit's own, run against a
scratch XDG_STATE_HOME (the box's slot files and lane records, as tests/gate/kit/slot.py builds
them; the box's own never touched). The copy's gate-budget.toml says heavy_items 1, so every run
here is over it, and fast_workers CAP. Lane gh8 holds the heavy grant; the runs of gh7, which
holds none, are an implementer's.

fast: gh8's full gate, `just check` on FULL workers (over the cap), holds the slot (its `heavy
slot: held:` line read from its output as it runs; its tests/a.sh then waits on a lock this
scenario holds, no clock). Meanwhile gh7's `just fast`, the caller's GATE_WORKERS FULL, starts,
says it runs as the fast tier on CAP workers at the lowest priority, runs check-probe and tests/b.sh
at nice 19 and idle disk class, never the e2e tests/a.sh, and passes; the slot's status still
names gh8's run holding it. Released, gh8's gate passes on FULL workers (xdist's `created: N/N
workers`), each of its items run at the priority its caller has, this scenario's.
heavy: lane gh8's run holding the slot's lock (`octo-feather-slot hold`, its stdin kept open).
(check) `just check` on CAP workers holds the e2e tests/a.sh, so it asks the slot and is refused
for want of a grant (exit 75), no test item run; (workers) `just test -m 'not e2e'` holds no e2e
item, but on CAP + 1 workers: refused the same. gh8's run still holds the slot after either."""

from __future__ import annotations

import fcntl
import re
import subprocess
from contextlib import contextmanager
from typing import TYPE_CHECKING

from gate_recipes_first import gate, gate_env, kit_copy
from testkit import ROOT, Scratch, main

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

CAP = 1
FULL = CAP + 1  # the full gate's width, over the cap (its default, 8, costs this item 3 s of CPU)
TIER = f"{CAP} worker (cap {CAP}), at the lowest priority (nice 19, disk idle)"
PRIO = "$(nice) $(ionice)"  # what each item logs after its name
LOWEST = "19 idle"
HELD = "heavy slot: held: the heavy slot for lane gh8"
PIPE = subprocess.PIPE
# gh8's tests/a.sh: with HOLD set, it waits for a shared lock on that file, the scenario's.
A_SH = """#!/usr/bin/env bash
# gate: e2e
lock='import fcntl, sys; fcntl.flock(open(sys.argv[1]), fcntl.LOCK_SH)'
[[ -z "${HOLD:-}" ]] || python3 -c "$lock" "$HOLD"
echo "a $(nice) $(ionice)" >> "$PROBE"
"""
B_SH = A_SH.replace("# gate: e2e\n", "").replace('"a ', '"b ')  # waits on HOLD too, no e2e
WAIT = "fast tier: waiting my turn, 1 fast run at once (fast_runs, gate-budget.toml), held by: pid "
REFUSED = 75
LANES = {"gh7": "w9:p1", "gh8": "w8:p1"}
DIRECTOR = {"OCTO_FEATHER_ROLE": "director", "HERDR_PANE_ID": "w1:p1"}
PANE = (
    "HERDR_PANE_ID",
    "HERDR_SESSION",
    "OCTO_FEATHER_PARENT",
    "HERDR_WORKSPACE_ID",
    "OCTO_FEATHER_SPEND_SPACE",
)


def agent(space: str) -> dict[str, str]:
    """An implementer of the lane whose supervisor is SPACE's p1, in its own pane there."""
    return {
        "OCTO_FEATHER_ROLE": "implementer",
        "HERDR_PANE_ID": f"{space}:p3",
        "OCTO_FEATHER_PARENT": f"{space}:p1",
        "HERDR_WORKSPACE_ID": space,
    }


def box(s: Scratch) -> Path:
    """The scratch box (lane records, gh8's grant) and the kit copy, its slot the kit's own."""
    lanes = s.root / "state" / "octo-feather" / "lanes"
    lanes.mkdir(parents=True)
    for lane, sup in LANES.items():
        (lanes / f"{lane}.toml").write_text(f'supervisor = "{sup}"\n')
    (lanes.parent / "director.toml").write_text('pane = "w1:p1"\n')
    (s.root / "user-mise").mkdir()
    s.env = {k: v for k, v in s.env.items() if k not in PANE}
    s.env |= {"XDG_STATE_HOME": str(s.root / "state")}
    k = kit_copy(s)
    slot = (ROOT / "scripts" / "octo-feather-slot").read_text()
    (k / "scripts" / "octo-feather-slot").write_text(slot)
    (k / "tests" / "a.sh").write_text(A_SH)
    (k / "tests" / "b.sh").write_text(B_SH)
    jf = k / "justfile"  # one static check, check-probe: two gate runs here, each kept cheap
    text = jf.read_text().replace('GATE_RECIPES := "check-dashes ', 'GATE_RECIPES := "', 1)
    probe = '@echo check-probe >> "$PROBE"'
    jf.write_text(text.replace(probe, f'@echo "check-probe {PRIO}" >> "$PROBE"', 1))
    budget = k / "gate-budget.toml"
    text = re.sub(r"^heavy_items = \d+$", "heavy_items = 1", budget.read_text(), flags=re.MULTILINE)
    cap = f"fast_workers = {CAP}"
    text = re.sub(r"^fast_workers = \d+$", cap, text, flags=re.MULTILINE)
    budget.write_text(re.sub(r"^fast_runs = \d+$", "fast_runs = 1", text, flags=re.MULTILINE))
    s.git(k, "commit", "-qam", "the slot, the budget, a.sh waiting on HOLD")
    grant = [str(k / "scripts" / "octo-feather-slot"), "grant", "gh8", "--kind", "heavy"]
    s.run(grant, env=DIRECTOR)
    return k


@contextmanager
def held(s: Scratch, k: Path) -> Generator[int]:
    """Lane gh8's run holding the heavy slot's lock while the block runs; its pid. The run is a
    shell this scenario starts, beside the runs it makes, never their ancestor (one would be
    nested under it: octo-feather-slot --help)."""
    slot = [str(k / "scripts" / "octo-feather-slot"), "hold", "--kind", "heavy", "--items", "31"]
    hold = ["sh", "-c", '"$@"; :', "sh", *slot]  # `; :`: sh waits for it, never execs it
    env = {**s.env, **agent("w8")}
    pipe = subprocess.PIPE
    with subprocess.Popen(hold, env=env, stdin=pipe, stdout=pipe, text=True) as p:
        assert p.stdout is not None
        said = p.stdout.readline()
        assert said.startswith("held: the heavy slot for lane gh8"), said
        try:
            yield p.pid
        finally:
            p.communicate()


def status(s: Scratch, k: Path) -> str:
    return s.run([str(k / "scripts" / "octo-feather-slot"), "status"]).out


def held_now(p: subprocess.Popen[str], until: str = HELD) -> str:
    """P's output, read as it runs, up to its line starting UNTIL (default: it holds gh8's slot)."""
    assert p.stdout is not None
    seen = ""
    for line in p.stdout:
        seen += line
        if line.startswith(until):
            return seen
    return seen  # it ended without: the caller's assertion names it


def logged(probe: list[str]) -> dict[str, str]:
    """PROBE's lines: each item's name and the priority it ran at."""
    return dict(ln.split(" ", 1) for ln in probe)


def fast(s: Scratch) -> None:
    k = box(s)
    hold, probe8 = s.root / "hold", s.root / "probe-gh8"
    hold.touch()
    probe8.write_text("")
    env = gate_env(s, probe8, HOLD=str(hold), PYTHONUNBUFFERED="1", **agent("w8"))
    env["GATE_WORKERS"] = str(FULL)
    out = subprocess.STDOUT
    with hold.open() as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        cmd = ["just", "check"]
        with subprocess.Popen(cmd, cwd=k, env=env, stdout=PIPE, stderr=out, text=True) as p:
            try:
                seen = held_now(p)
                assert HELD in seen, f"gh8's just check never held the slot:\n{seen}"
                ran, probe = gate(s, k, "fast", GATE_WORKERS=str(FULL), **agent("w9"))
                said = f"just fast: exit {ran.rc}\nprobe: {probe}\n{ran.out}"
                assert ran.rc == 0, said
                assert f"heavy slot: not needed: fast tier, {TIER}" in ran.out, said
                ran_at = logged(probe)
                assert sorted(ran_at) == ["b", "check-probe"], f"want statics and b.sh: {said}"
                assert set(ran_at.values()) == {LOWEST}, f"want each at {LOWEST}: {said}"
                st = status(s, k)
                assert re.search(r"run holding it now: pid \d+ of lane gh8 since ", st), st
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)
            assert p.stdout is not None
            seen += p.stdout.read()
    said = f"gh8's just check: exit {p.returncode}\n{seen}"
    assert p.returncode == 0, said
    assert f"created: {FULL}/{FULL} workers" in seen, said
    ran_at = logged(probe8.read_text().splitlines())
    assert sorted(ran_at) == ["a", "b", "check-probe"], said
    sh = ["sh", "-c", f'echo "{PRIO}"']
    mine = subprocess.run(sh, capture_output=True, text=True, check=True).stdout
    assert set(ran_at.values()) == {mine.strip()}, f"want each at its caller's {mine}: {said}"


def heavy(s: Scratch, how: str) -> None:
    """HOW: check (`just check`, an e2e item, CAP workers) or workers (`just test -m 'not e2e'`, no
    e2e item, CAP + 1 workers)."""
    k = box(s)
    with held(s, k) as pid:
        if how == "check":
            ran, probe = gate(s, k, "check", GATE_WORKERS=str(CAP), **agent("w9"))
        else:
            env = {"GATE_WORKERS": str(CAP + 1), "PYTEST_ADDOPTS": "--color=no -m 'not e2e'"}
            ran, probe = gate(s, k, "test", **env, **agent("w9"))
        said = f"just ({how}): exit {ran.rc}\nprobe: {probe}\n{ran.out}"
        assert ran.rc == REFUSED, said
        assert "refused, nothing ran: this heavy run selects " in ran.out, said
        assert "lane gh7 holds no heavy grant; current holder: gh8 (granted " in ran.out, said
        assert "fast tier" not in ran.out, said
        assert not {"a", "b"} & set(logged(probe)), f"a test item ran: {said}"
        st = status(s, k)
        assert f"run holding it now: pid {pid} of lane gh8" in st, st


def turn(s: Scratch) -> None:
    """fast_runs 1 (#1213): gh8's `just fast` takes the box's one fast-run turn, its tests/b.sh
    then waiting on a lock this scenario holds. gh7's `just fast`, started meanwhile, says it waits
    its turn and for whom (the holder's pid and checkout), and has run nothing; released, gh8's run
    ends, gh7's takes the turn, says so, and both pass, each item run once."""
    k = box(s)
    hold, probe8, probe7 = s.root / "hold", s.root / "probe-gh8", s.root / "probe-gh7"
    for f in (hold, probe8, probe7):
        f.write_text("")
    env8 = gate_env(s, probe8, HOLD=str(hold), PYTHONUNBUFFERED="1", **agent("w8"))
    env7 = gate_env(s, probe7, PYTHONUNBUFFERED="1", **agent("w9"))
    out, cmd = subprocess.STDOUT, ["just", "fast"]
    with hold.open() as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            with subprocess.Popen(cmd, cwd=k, env=env8, stdout=PIPE, stderr=out, text=True) as p8:
                seen8 = held_now(p8, "heavy slot: not needed: fast tier")
                assert "not needed: fast tier" in seen8, f"gh8's just fast:\n{seen8}"
                with subprocess.Popen(
                    cmd, cwd=k, env=env7, stdout=PIPE, stderr=out, text=True
                ) as p7:
                    seen7 = held_now(p7, "fast tier: waiting my turn")
                    said = f"gh7's just fast:\n{seen7}"
                    assert WAIT in seen7, said
                    assert re.search(rf"held by: pid \d+ in {re.escape(str(k))} since ", seen7), (
                        said
                    )
                    assert probe7.read_text() == "", f"gh7 ran an item while waiting: {said}"
                    fcntl.flock(lock, fcntl.LOCK_UN)
                    assert p7.stdout is not None
                    seen7 += p7.stdout.read()
                assert p8.stdout is not None
                seen8 += p8.stdout.read()
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
    for lane, p, seen, probe in (("gh8", p8, seen8, probe8), ("gh7", p7, seen7, probe7)):
        said = f"{lane}'s just fast: exit {p.returncode}\n{seen}"
        assert p.returncode == 0, said
        assert sorted(logged(probe.read_text().splitlines())) == ["b", "check-probe"], said
    assert re.search(r"fast tier: my turn after \d+ s waiting, fast-0.lock taken", seen7), seen7


if __name__ == "__main__":
    main(fast, heavy, turn)
