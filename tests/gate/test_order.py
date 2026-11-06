"""Longest items first, and the box's load on the trend line (tests/gate/conftest.py; #618), on a throwaway suite.

The kit's runner (tests/gate/conftest.py and test_gate.py, copied unchanged) runs by pytest as a command on five
items, tests/a.sh to e.sh, each appending its worker and name to a log as it starts, so the log is the order the
workers received them. The suite is a git repo; its trend file is written before each run: none (no history), or
the fake history: an older line of this repo (e.sh 50 s), a later one (a 1, c 3, d 2, e 0.5; b.sh absent) and a
line of another repo (e.sh 100 s), which must not count.

Run as a script, this file is the scenario: it prints one JSON line, each run's exit, output, log and trend line.
The test runs that command (through qc_command, as test_cpu.py does) and asserts on what it printed.
"""

import json
import os
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest
from test_gate import PANE, ROOT

SCRIPTS = ("a", "b", "c", "d", "e")


@pytest.mark.criterion("quality#acceptance-gate-time-targets")
def test_longest_first_order(
    request: pytest.FixtureRequest, qc_command: Callable[[list[str]], list[str]]
) -> None:
    env = {k: v for k, v in os.environ.items() if not k.startswith("HERDR_") and k not in PANE}
    node = cast("pytest.Item", request.node)  # pyright: ignore[reportUnknownMemberType]
    env.setdefault("GATE_ITEM", node.nodeid)  # pytest leaves request.node unannotated
    cmd = qc_command([sys.executable, str(Path(__file__).resolve())])
    p = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, check=False)
    assert p.returncode == 0, f"the scenario exited {p.returncode}:\n{p.stdout}\n{p.stderr}"
    runs = {r["name"]: r for r in json.loads(p.stdout.strip().splitlines()[-1])}
    for r in runs.values():
        assert r["exit"] == 0, f"{r['name']}: exit {r['exit']}:\n{r['out']}"

    def order(name: str) -> list[str]:
        return [ln.split()[1] for ln in runs[name]["log"]]

    assert order("none") == ["a", "b", "c", "d", "e"], "no history: collection order"
    want = ["c", "b", "d", "a", "e"]  # recorded ones longest first in their places; b.sh keeps its place
    assert order("history") == want, f"-n 1: {order('history')}, want {want}"
    assert order("history-n0") == want, f"-n 0: {order('history-n0')}, want {want}"
    first: dict[str, str] = {}
    for ln in runs["history-n2"]["log"]:
        worker, script = ln.split()
        first.setdefault(worker, script)
    assert sorted(first.values()) == ["b", "c"], (
        f"-n 2: each worker's first item {first}, want the first two of {want}, one per worker"
    )
    trend = runs["history"]["trend"]
    for k in ("load1_start", "load1_end"):
        assert isinstance(trend.get(k), float), f"trend line {k}: {trend.get(k)!r}"
    assert {"start", "repo", "head", "total_s", "exit", "tier", "steps"} <= trend.keys()


def scenario() -> None:
    """The throwaway suite's runs; prints [{name, exit, out, log, trend}]."""
    with tempfile.TemporaryDirectory() as t:
        s = Path(t, "s")
        (s / "tests" / "gate").mkdir(parents=True)
        for f in ("conftest.py", "test_gate.py"):
            (s / "tests" / "gate" / f).write_text((ROOT / "tests" / "gate" / f).read_text())
        (s / "pyproject.toml").write_text(
            '[tool.pytest.ini_options]\ntestpaths = ["tests/gate"]\n'
            'addopts = "--junitxml=.pytest_cache/junit.xml"\n'
        )
        log = Path(t, "log")
        for name in SCRIPTS:
            sh = s / "tests" / f"{name}.sh"
            sh.write_text(f'#!/usr/bin/env bash\necho "${{PYTEST_XDIST_WORKER:-main}} {name}" >> "$ORDER_LOG"\n')
            sh.chmod(0o755)
        subprocess.run(["git", "init", "-q", str(s)], check=True)
        repo = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], cwd=s, capture_output=True, text=True, check=True
        ).stdout.strip()

        def line(at: str, steps: dict[str, float]) -> str:
            rows = [{"name": f"test_script[tests/{n}.sh]", "seconds": v, "result": "ok"} for n, v in steps.items()]
            return json.dumps({"start": "2026-11-01T00:00:00Z", "repo": at, "head": None, "total_s": 1,
                               "exit": 0, "tier": "full", "steps": rows}, separators=(",", ":"))

        history = "\n".join((line(repo, {"e": 50}), line(repo, {"a": 1, "c": 3, "d": 2, "e": 0.5}),
                             line(repo + "-other", {"e": 100}))) + "\n"
        drop = ("HERDR_SESSION", "OCTO_FEATHER_QC_CLAIMS", "OCTO_FEATHER_QC_CAPTURE_DIR")
        env = {k: v for k, v in os.environ.items() if k not in drop}
        env |= {"XDG_STATE_HOME": str(Path(t, "xdg")), "GATE_RECIPES": "", "ORDER_LOG": str(log)}
        trend = Path(t, "xdg", "octo-feather", "check-runs.jsonl")
        trend.parent.mkdir(parents=True)
        pytest_cmd = ["uv", "run", "--project", str(ROOT), "--locked", "--offline", "--no-sync", "pytest"]
        runs: list[dict[str, object]] = []
        for name, past, workers in (("none", "", 1), ("history", history, 1), ("history-n0", history, 0),
                                    ("history-n2", history, 2)):
            trend.write_text(past)
            log.write_text("")
            p = subprocess.run([*pytest_cmd, "-n", str(workers)], cwd=s, env=env, capture_output=True,
                               text=True, check=False)
            lines = trend.read_text().splitlines()
            runs.append({"name": name, "exit": p.returncode, "out": p.stdout + p.stderr,
                         "log": log.read_text().splitlines(), "trend": json.loads(lines[-1]) if lines else {}})
    sys.stdout.write(json.dumps(runs) + "\n")


if __name__ == "__main__":
    scenario()
