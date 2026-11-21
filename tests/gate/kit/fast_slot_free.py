"""The fast tier takes no heavy-run slot (quality #acceptance-fast-slot-free, #recipes-static-first;
#1210), through `just fast`, `just check` and `just test` in a throwaway git copy of the kit
(tests/gate/kit/gate_recipes_first.py's: two static checks, test items tests/a.sh and tests/b.sh
each logging its name to PROBE, tests/a.sh end-to-end by its header) whose octo-feather-slot is the
kit's own, run against a scratch XDG_STATE_HOME (the box's slot files and lane records, as
tests/gate/kit/slot.py builds them; the box's own never touched). The copy's gate-budget.toml says
heavy_items 2, so every run here is over it, and fast_workers CAP. Lane gh8 holds the heavy
grant, and its run holds the slot's lock (`octo-feather-slot hold`, its stdin kept open); the runs
are an implementer of lane gh7, which holds no grant.

fast: `just fast`, the caller's GATE_WORKERS 8, starts at once: it says it runs as the fast tier on
CAP workers, runs the static checks and tests/b.sh (never the e2e tests/a.sh) and passes; gh8's run
still holds the slot after it.
heavy (check): `just check` on CAP workers holds the e2e tests/a.sh, so it asks the slot and is
refused for want of a grant (exit 75), no test item run. (workers): `just test -m 'not e2e'` holds
what the fast tier may, but on CAP + 1 workers: refused the same."""

from __future__ import annotations

import re
import subprocess
from contextlib import contextmanager
from typing import TYPE_CHECKING

from gate_recipes_first import gate, kit_copy
from testkit import ROOT, Scratch, main

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

CAP = 2
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
    budget = k / "gate-budget.toml"
    text = re.sub(r"^heavy_items = \d+$", "heavy_items = 2", budget.read_text(), flags=re.MULTILINE)
    cap = f"fast_workers = {CAP}"
    budget.write_text(re.sub(r"^fast_workers = \d+$", cap, text, flags=re.MULTILINE))
    s.git(k, "commit", "-qam", "the slot, the budget")
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


def fast(s: Scratch) -> None:
    k = box(s)
    with held(s, k) as pid:
        ran, probe = gate(s, k, "fast", GATE_WORKERS="8", **agent("w9"))
        said = f"just fast: exit {ran.rc}\nprobe: {probe}\n{ran.out}"
        assert ran.rc == 0, said
        assert f"heavy slot: not needed: fast tier, {CAP} workers (cap {CAP})" in ran.out, said
        assert sorted(probe) == ["b", "check-probe"], f"want the static checks and b.sh: {said}"
        st = status(s, k)
        assert f"run holding it now: pid {pid} of lane gh8" in st, st


def heavy(s: Scratch, how: str) -> None:
    """HOW: check (`just check`, an e2e item, CAP workers) or workers (`just test -m 'not e2e'`, no
    e2e item, CAP + 1 workers)."""
    k = box(s)
    with held(s, k):
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
        assert not {"a", "b"} & set(probe), f"a test item ran: {said}"


if __name__ == "__main__":
    main(fast, heavy)
