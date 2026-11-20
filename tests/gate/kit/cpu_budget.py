"""The per-test CPU budget fails the gate on a changed integration test (quality
#acceptance-test-cpu-budget; #1182, #687): `just fast` in a git copy of the kit with its own tests
left out, its gate-budget.toml's test_cpu_seconds 0.1, and one item, heavy.sh, whose child burns
0.2 s of CPU, committed on main, the default branch a change is judged against. The static checks
are cut to one with just's own override (`just --set GATE_RECIPES check-dashes`). changed: new.sh
added, burning the same, just fast fails naming new.sh, its CPU seconds, those of its run alone
again and the budget, and names heavy.sh, unchanged, report-only. passes: one just fast with the
same new.sh marked e2e (`# gate: e2e`), skipped and never named over the budget; once.sh, added,
burning only its first time (a scratch file it removes), named over once with both CPU times;
heavy.sh report-only; the run passes. One nested gate run per item, so each stays within the kit's
own budget; the copy prepared once per gate run (Scratch.prepare, billed to its own line). The
demo's revert (new.sh removed, just fast passes) is the passes item's unchanged over-budget test in
a passing run."""

from __future__ import annotations

import re
import subprocess
from typing import TYPE_CHECKING

from testkit import ROOT, Ran, Scratch, kit_deps, main, pnpm_store, tool_homes

if TYPE_CHECKING:
    from pathlib import Path

NODE = "tests/gate/test_gate.py::test_script"
BURN = "import time\nt = time.process_time() + 0.2\nwhile time.process_time() < t: pass\n"
OUT_OF_COPY = re.compile(
    r"tests/[^/]*\.sh|tests/gate/test_cpu\.py|tests/gate/kit/(.*/)?test_[^/]*\.py"
)
# The kit gate's own settings, never the copy's run's; GATE_NESTED set below: a gate in this item.
LINE = "cpu budget: 0.1s per non-e2e test (gate-budget.toml test_cpu_seconds):"
GATE = ("GATE_RECIPES", "GATE_WORKERS", "GATE_RUN_DIR", "GATE_ITEM", "HERDR_SESSION", "VIRTUAL_ENV")


def item(script: str) -> str:
    return f"{NODE}[tests/{script}.sh]"


def script(k: Path, name: str, head: str = "", *, once: bool = False) -> None:
    """tests/NAME.sh burning BURN; ONCE: only while the file $ONCE exists, which it removes."""
    burn = f"python3 -c '{BURN}'"
    body = f'if [[ -e "$ONCE" ]]; then rm "$ONCE"; {burn}; fi' if once else burn
    p = k / "tests" / f"{name}.sh"
    p.write_text(f"#!/usr/bin/env bash\n{head}{body}\n")
    p.chmod(0o755)


def build(s: Scratch) -> None:
    """The kit's files (tracked, and new ones git would track) but its tests, with heavy.sh and a
    0.1 s budget, committed in a repo of its own at S/kit, the kit's packages linked."""
    k = s.root / "kit"
    listed = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],  # noqa: S607
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout.decode()
    files = "\0".join(f for f in listed.split("\0") if f and not OUT_OF_COPY.fullmatch(f))
    k.mkdir()
    tar = subprocess.run(
        ["tar", "-cf", "-", "--null", "-T", "-"],  # noqa: S607
        cwd=ROOT,
        input=files.encode(),
        capture_output=True,
        check=True,
    )
    subprocess.run(["tar", "-xf", "-", "-C", str(k)], input=tar.stdout, check=True)  # noqa: S607
    budget = (k / "gate-budget.toml").read_text()
    (k / "gate-budget.toml").write_text(
        re.sub(r"(?m)^test_cpu_seconds = .*$", "test_cpu_seconds = 0.1", budget)
    )
    script(k, "heavy")
    s.git(k, "init", "-q", "-b", "main")
    kit_deps(k)
    s.git(k, "add", "-A")
    s.git(k, "commit", "-qm", "copy")


def kit_copy(s: Scratch) -> Path:
    s.prepare("cpu-budget-kit", build)
    return s.root / "kit"


def gate(s: Scratch, k: Path, *args: str, want: int, once: Path | None = None) -> Ran:
    """`just --set GATE_RECIPES check-dashes ARGS` in K; its stdout and stderr together."""
    env = {n: v for n, v in s.env.items() if n not in GATE}
    env |= tool_homes() | {
        "npm_config_store_dir": pnpm_store(),
        "GATE_NESTED": "1",
        "PYTEST_ADDOPTS": "--color=no",
        "ONCE": str(once or s.root / "no-once"),
    }
    env["UV_PROJECT_ENVIRONMENT"] = str(
        ROOT / ".venv"
    )  # the kit's venv: the copy syncs none of its own
    p = subprocess.run(
        ["just", "--set", "GATE_RECIPES", "check-dashes", *args],  # noqa: S607
        cwd=k,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    assert p.returncode == want, (
        f"just {' '.join(args)}: exit {p.returncode}, want {want}\n{p.stdout}"
    )
    return Ran(p.returncode, p.stdout, "")


def over(out: str, name: str, verdict: str) -> tuple[float, float | None]:
    """NAME's OVER CPU BUDGET line with VERDICT: its CPU seconds (the 0.2 s its child burns), and
    those of its run alone again when the line names one."""
    m = re.search(
        rf"^OVER CPU BUDGET: {re.escape(item(name))} ([0-9.]+)s CPU"
        rf"(?:, alone again ([0-9.]+)s CPU)?, budget 0\.1s \({re.escape(verdict)}\)$",
        out,
        re.MULTILINE,
    )
    assert m, f"no OVER CPU BUDGET line for {name} ({verdict}):\n{out}"
    cpu = float(m.group(1))
    assert 0.18 <= cpu < 3, f"{name} shows {cpu}s CPU, want its child's 0.2 s:\n{out}"
    return cpu, None if m.group(2) is None else float(m.group(2))


def changed(s: Scratch) -> None:
    """Changed and over, alone again too: fails, both CPU times named; unchanged and over:
    reported only."""
    k = kit_copy(s)
    script(k, "new")
    out = gate(s, k, "fast", want=1).out
    _, again = over(out, "new", "changed, over twice: the gate fails")
    assert again is not None, out
    assert 0.18 <= again < 3, out
    assert over(out, "heavy", "report-only")[1] is None, out
    assert f"{LINE} 3 over, 1 changed over twice, FAIL" in out, out


def passes(s: Scratch) -> None:
    """One just fast, passing: the new test marked e2e is never held to the budget (the fast tier
    skips it, named so); a changed test over it once and under it alone again passes, named with
    both CPU times; the unchanged one over it is reported only."""
    k = kit_copy(s)
    script(k, "new", "# gate: e2e\n")
    script(k, "once", once=True)
    (s.root / "once").touch()
    out = gate(s, k, "fast", want=0, once=s.root / "once").out
    assert "fast: tests/new.sh: e2e (# gate: e2e): skipped" in out, out
    assert item("new") not in out, out
    _, again = over(out, "once", "changed, over once: passes")
    assert again is not None, out
    assert again < 0.1, out
    over(out, "heavy", "report-only")
    assert f"{LINE} 3 over, 1 changed over once, passes" in out, out


if __name__ == "__main__":
    main(changed, passes)
