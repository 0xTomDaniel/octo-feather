"""Longest items first, and the box's load on the trend line (tests/gate/conftest.py; #618), as
scenarios (testkit.main).

The kit's runner (tests/gate/conftest.py and test_gate.py, copied unchanged) runs by pytest as
a command on five items, tests/a.sh to e.sh, each appending its worker and name to a log as it
starts, so the log is the order the workers received them. The suite is a git repo with a second
worktree, fresh; the trend file is written before each run: none (no history), or the fake
history: an older line of the suite (e.sh 50 s), a later one (a 1, c 3, d 2, e 0.5; b.sh absent)
and a line of another repo (e.sh 100 s), which must not count. The suite, with history of its
own, keeps to it beside a line of the fresh worktree (a 1, e 9); the fresh worktree, with none,
runs by the suite's.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from typing import TYPE_CHECKING, cast

from testkit import ROOT, Scratch, main

if TYPE_CHECKING:
    from pathlib import Path

SCRIPTS = ("a", "b", "c", "d", "e")
SAME = ("m1", "m2")  # modules holding one same-named item each
DROP = ("HERDR_SESSION", "OCTO_FEATHER_QC_CLAIMS", "OCTO_FEATHER_QC_CAPTURE_DIR")


def _line(repo: str, steps: dict[str, float], same: dict[str, float] | None = None) -> str:
    """A trend line of REPO: STEPS by script, as a line before step node ids (name only), and
    SAME by module, test_same in each, with its node id."""
    rows: list[dict[str, object]] = [
        {"name": f"test_script[tests/{n}.sh]", "seconds": v, "result": "ok"}
        for n, v in steps.items()
    ]
    rows += [
        cast(
            "dict[str, object]",
            {
                "name": "test_same",
                "node": f"tests/gate/test_{m}.py::test_same",
                "seconds": v,
                "result": "ok",
            },
        )
        for m, v in (same or {}).items()
    ]
    run = {"start": "2026-11-01T00:00:00Z", "repo": repo, "head": None, "total_s": 1, "exit": 0}
    return json.dumps({**run, "tier": "full", "steps": rows}, separators=(",", ":"))


def longest_first(s: Scratch) -> None:
    suite = s.root / "s"
    (suite / "tests" / "gate").mkdir(parents=True)
    for f in ("conftest.py", "test_gate.py"):
        (suite / "tests" / "gate" / f).write_text((ROOT / "tests" / "gate" / f).read_text())
    (suite / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\ntestpaths = ["tests/gate"]\n'
        'addopts = "--junitxml=.pytest_cache/junit.xml"\n'
    )
    log = s.root / "log"
    for name in SCRIPTS:
        sh = suite / "tests" / f"{name}.sh"
        log_it = f'echo "${{PYTEST_XDIST_WORKER:-main}} {name}" >> "$ORDER_LOG"'
        sh.write_text(f"#!/usr/bin/env bash\n{log_it}\n")
        sh.chmod(0o755)
    for m in SAME:
        (suite / "tests" / "gate" / f"test_{m}.py").write_text(
            "import os\n\n\ndef test_same():\n"
            '    with open(os.environ["ORDER_LOG"], "a") as f:\n'
            f'        f.write(os.environ.get("PYTEST_XDIST_WORKER", "main") + " {m}\\n")\n'
        )
    git = shutil.which("git")
    assert git, "no git on PATH"
    subprocess.run([git, "init", "-q", str(suite)], check=True)
    s.git(suite, "add", "-A")
    s.git(suite, "commit", "-qm", "suite")
    fresh = s.root / "w"
    s.git(suite, "worktree", "add", "-q", "--detach", str(fresh))
    top = [git, "rev-parse", "--show-toplevel"]
    repo = subprocess.run(top, cwd=suite, capture_output=True, text=True, check=True).stdout.strip()
    wt = subprocess.run(top, cwd=fresh, capture_output=True, text=True, check=True).stdout.strip()
    history = "\n".join(
        (
            _line(repo, {"e": 50}),
            _line(repo, {"a": 1, "c": 3, "d": 2, "e": 0.5}, {"m1": 0.2, "m2": 0.4}),
            _line(repo + "-other", {"e": 100}),
        )
    )
    with_fresh = history + "\n" + _line(wt, {"a": 1, "e": 9})
    env = {k: v for k, v in os.environ.items() if k not in DROP}
    env |= {"XDG_STATE_HOME": str(s.root / "xdg"), "GATE_RECIPES": "", "ORDER_LOG": str(log)}
    trend = s.root / "xdg" / "octo-feather" / "check-runs.jsonl"
    trend.parent.mkdir(parents=True)
    uv = ["uv", "run", "--project", str(ROOT), "--locked", "--offline", "--no-sync", "pytest"]

    def run(
        past: str, workers: int, cwd: Path = suite
    ) -> tuple[list[list[str]], dict[str, object]]:
        trend.write_text(past + "\n" if past else "")
        log.write_text("")
        p = subprocess.run(
            [*uv, "-n", str(workers)],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert p.returncode == 0, f"-n {workers}: exit {p.returncode}:\n{p.stdout}{p.stderr}"
        lines = trend.read_text().splitlines()
        return [ln.split() for ln in log.read_text().splitlines()], json.loads(lines[-1])

    got = [n for _, n in run("", 1)[0]]
    assert got == ["a", "b", "c", "d", "e", "m1", "m2"], f"no history: {got}, want collection order"
    # Recorded ones longest first in their places; b keeps its place; m1 and m2, one name in two
    # modules, each by its own node id.
    want = ["c", "b", "d", "a", "e", "m2", "m1"]
    started, trend_line = run(with_fresh, 1)
    got = [n for _, n in started]
    assert got == want, f"-n 1, own history beside the fresh worktree's: {got}, want {want}"
    got = [n for _, n in run(history, 0, fresh)[0]]
    assert got == want, f"-n 0, fresh worktree, the suite's history: {got}, want {want}"
    first: dict[str, str] = {}
    for worker, name in run(history, 2)[0]:
        first.setdefault(worker, name)
    assert sorted(first.values()) == ["b", "c"], (
        f"-n 2: each worker's first item {first}, want the first two of {want}, one per worker"
    )
    for k in ("load1_start", "load1_end"):
        assert isinstance(trend_line.get(k), float), f"trend line {k}: {trend_line.get(k)!r}"
    old = {"start", "repo", "head", "total_s", "exit", "tier", "steps"}
    assert old <= trend_line.keys(), f"trend line keys {sorted(trend_line)}"
    rows = cast("list[dict[str, str]]", trend_line["steps"])
    steps = {st.get("node"): st["name"] for st in rows}
    for m in SAME:
        assert steps.get(f"tests/gate/test_{m}.py::test_same") == "test_same", steps


if __name__ == "__main__":
    main(longest_first)
