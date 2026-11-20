"""The per-test CPU budget fails the gate on a changed integration test (quality
#acceptance-test-cpu-budget; #1182, #687): `just fast` in a git copy of the kit with its own tests
left out, its gate-budget.toml's test_cpu_seconds 0.1, and one item, heavy.sh, whose child
burns 0.2 s of CPU, committed with a recorded full pass (the diff base). The static checks are
cut to one with just's own override (`just --set GATE_RECIPES check-dashes`). changed: new.sh
added, burning the same, just fast fails naming new.sh, its CPU seconds and the budget, and names
heavy.sh, unchanged, report-only. e2e: the same new.sh marked e2e (`# gate: e2e`), run with heavy.sh
(`just test NODE NODE`): passes, new.sh shown as e2e and never named over the budget, heavy.sh
named report-only. One nested gate run per item, so each stays within the kit's own budget; the
copy prepared once per gate run (Scratch.prepare, billed to its own line). The demo's revert (new.sh
removed, just fast passes) is the e2e item's unchanged over-budget test in a passing run."""

from __future__ import annotations

import re
import subprocess
from typing import TYPE_CHECKING

from testkit import ROOT, Ran, Scratch, kit_deps, main, pnpm_store, tool_homes

if TYPE_CHECKING:
    from pathlib import Path

NODE = "tests/gate/test_gate.py::test_script"
BURN = "import time\nt = time.process_time() + 0.2\nwhile time.process_time() < t: pass\n"
OUT_OF_COPY = re.compile(r"tests/[^/]*\.sh|tests/gate/test_cpu\.py|tests/gate/kit/(.*/)?test_[^/]*\.py")
# The kit gate's own settings, never the copy's run's; GATE_NESTED set below: a gate inside this item.
GATE = ("GATE_RECIPES", "GATE_WORKERS", "GATE_RUN_DIR", "GATE_ITEM", "HERDR_SESSION", "VIRTUAL_ENV")
IDENT = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def item(script: str) -> str:
    return f"{NODE}[tests/{script}.sh]"


def script(k: Path, name: str, head: str = "") -> None:
    p = k / "tests" / f"{name}.sh"
    p.write_text(f"#!/usr/bin/env bash\n{head}python3 -c '{BURN}'\n")
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
    (k / "gate-budget.toml").write_text(re.sub(r"(?m)^test_cpu_seconds = .*$", "test_cpu_seconds = 0.1", budget))
    script(k, "heavy")
    s.git(k, "init", "-q", "-b", "main")
    kit_deps(k)
    s.git(k, "add", "-A")
    s.git(k, "commit", "-qm", "copy")
    s.run([str(k / "scripts" / "octo-feather-gate"), "record", "--reason", "base", "--seconds", "1"], cwd=k, env=IDENT)


def kit_copy(s: Scratch) -> Path:
    s.prepare("cpu-budget-kit", build)
    return s.root / "kit"


def gate(s: Scratch, k: Path, *args: str, want: int) -> Ran:
    """`just --set GATE_RECIPES check-dashes ARGS` in K; its stdout and stderr together."""
    env = {n: v for n, v in s.env.items() if n not in GATE}
    env |= tool_homes() | {"npm_config_store_dir": pnpm_store(), "GATE_NESTED": "1", "PYTEST_ADDOPTS": "--color=no"}
    env["UV_PROJECT_ENVIRONMENT"] = str(ROOT / ".venv")   # the kit's venv: the copy syncs none of its own
    p = subprocess.run(
        ["just", "--set", "GATE_RECIPES", "check-dashes", *args],  # noqa: S607
        cwd=k,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    assert p.returncode == want, f"just {' '.join(args)}: exit {p.returncode}, want {want}\n{p.stdout}"
    return Ran(p.returncode, p.stdout, "")


def over(out: str, name: str, verdict: str) -> float:
    """NAME's OVER CPU BUDGET line with VERDICT: its CPU seconds, the 0.2 s its child burns."""
    m = re.search(
        rf"^OVER CPU BUDGET: {re.escape(item(name))} ([0-9.]+)s CPU, budget 0\.1s \({re.escape(verdict)}\)$",
        out,
        re.MULTILINE,
    )
    assert m, f"no OVER CPU BUDGET line for {name} ({verdict}):\n{out}"
    cpu = float(m.group(1))
    assert 0.18 <= cpu < 3, f"{name} shows {cpu}s CPU, want its child's 0.2 s:\n{out}"
    return cpu


def changed(s: Scratch) -> None:
    """Changed and over: fails, named; unchanged and over: reported only."""
    k = kit_copy(s)
    script(k, "new")
    out = gate(s, k, "fast", want=1).out
    over(out, "new", "changed: the gate fails")
    over(out, "heavy", "report-only")
    assert "cpu budget: 0.1s per non-e2e test (gate-budget.toml test_cpu_seconds): 3 over, 1 of them changed: FAIL" in out, out


def e2e(s: Scratch) -> None:
    """The same new test marked e2e, run beside the unchanged one: passes; the e2e one is never
    held to the budget, the unchanged one over it reported only."""
    k = kit_copy(s)
    script(k, "new", "# gate: e2e\n")
    out = gate(s, k, "test", item("new"), item("heavy"), want=0).out
    assert re.search(rf"^ *[0-9.]+s cpu +[0-9.]+s wall +{re.escape(item('new'))}  \(e2e\)$", out, re.MULTILINE), out
    over(out, "heavy", "report-only")
    assert f"OVER CPU BUDGET: {item('new')}" not in out, out
    assert "cpu budget: 0.1s per non-e2e test (gate-budget.toml test_cpu_seconds): 1 over, report-only" in out, out


if __name__ == "__main__":
    main(changed, e2e)
