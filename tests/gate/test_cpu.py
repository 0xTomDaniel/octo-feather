"""Each gate item's CPU time (tests/gate/conftest.py; #588), proved on a throwaway suite.

The kit's runner (tests/gate/conftest.py and test_gate.py, copied unchanged) runs by pytest as a
command, under xdist (-n 1) and without it (-n 0), on three items: light.sh, heavy.sh (its child
process burns 0.3 s of CPU) and e2e.sh (headed `# gate: e2e`, burning the same), against a per-test
CPU budget of 0.15 s.

Run as a script, this file is the scenario: it builds the suite in a fresh temp dir, runs it both
ways and prints one JSON line, each run's exit, output and trend line. The test runs that command
(through qc_command, so a capturing gate runs it in the qc sandbox, whose /tmp is its own) and
asserts on what it printed.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest
from test_gate import PANE, ROOT

NODE = "tests/gate/test_gate.py::test_script"
BURN = "import time\nt = time.process_time() + 0.3\nwhile time.process_time() < t: pass\n"
BUDGET_LINE = (
    "cpu budget: 0.15s per non-e2e test (gate-budget.toml test_cpu_seconds): 1 over, report-only"
)


def item(script: str) -> str:
    return f"{NODE}[tests/{script}.sh]"


@pytest.mark.criterion("quality#acceptance-test-cpu-shown")
def test_cpu_shown(
    request: pytest.FixtureRequest, qc_command: Callable[[list[str]], list[str]]
) -> None:
    env = {k: v for k, v in os.environ.items() if not k.startswith("HERDR_") and k not in PANE}
    node = cast("pytest.Item", request.node)  # pyright: ignore[reportUnknownMemberType]
    env.setdefault("GATE_ITEM", node.nodeid)  # pytest leaves request.node unannotated
    cmd = qc_command([sys.executable, str(Path(__file__).resolve())])
    p = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, check=False)
    assert p.returncode == 0, f"the scenario exited {p.returncode}:\n{p.stdout}\n{p.stderr}"
    runs = json.loads(p.stdout.strip().splitlines()[-1])
    assert [r["workers"] for r in runs] == [1, 0]
    for r in runs:
        out, n = r["out"], r["workers"]
        assert r["exit"] == 0, f"-n {n}: exit {r['exit']}, want 0 (the budget only reports):\n{out}"
        shown = {
            s: re.search(
                rf"^ *([0-9.]+)s cpu +[0-9.]+s wall +{re.escape(item(s))}", out, re.MULTILINE
            )
            for s in ("light", "heavy", "e2e")
        }
        missing = [s for s, m in shown.items() if not m]
        assert not missing, f"-n {n}: no CPU line for {missing}:\n{out}"
        heavy = shown["heavy"]
        assert heavy is not None
        cpu = heavy.group(1)
        assert 0.27 <= float(cpu) < 3, f"-n {n}: heavy.sh shows {cpu}s CPU, want its child's 0.3 s"
        over = [ln for ln in out.splitlines() if ln.startswith("OVER CPU BUDGET:")]
        want = f"OVER CPU BUDGET: {item('heavy')} {cpu}s CPU, budget 0.15s (report-only)"
        assert over == [want], f"-n {n}: want heavy.sh alone named, with CPU and budget:\n{out}"
        assert BUDGET_LINE in out.splitlines(), f"-n {n}: no budget line:\n{out}"
        steps = {
            s["name"]: s.get("cpu_s")
            for s in r["trend"]["steps"]
            if s["name"].startswith("test_script")
        }
        assert sorted(steps) == [f"test_script[tests/{s}.sh]" for s in ("e2e", "heavy", "light")]
        assert all(isinstance(v, float) for v in steps.values()), f"-n {n}: trend cpu_s {steps}"
        assert steps["test_script[tests/heavy.sh]"] == float(cpu), (
            f"-n {n}: trend {steps}, shown {cpu}"
        )


def test_cpu_stage_records() -> None:
    """The public gate retains bounded stage input and rejects invalid attribution, not the test."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("HERDR_") and k not in PANE}
    p = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--stages"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert p.returncode == 0, p.stdout + p.stderr
    for run in json.loads(p.stdout.strip().splitlines()[-1]):
        assert run["exit"] == 0, run["out"]
        stages = run["stages"]
        valid = stages["valid"]
        assert valid["status"] == "reported", valid
        assert valid["prep_residual_s"] == 0.5, valid
        assert valid["item_residual_s"] == valid["item_cpu_s"] - 1.5, valid
        for name in ("duplicate", "malformed", "overflow", "nonfinite", "bad_keys"):
            assert stages[name]["status"].startswith("invalid:"), stages[name]
            assert isinstance(stages[name]["item_residual_s"], str), stages[name]
        assert stages["unavailable"]["prep"] == "unavailable", stages["unavailable"]
        assert isinstance(stages["unavailable"]["item_residual_s"], str)
        assert "cpu_stage " in run["out"], "the gate lost original scenario stdout"


def scenario() -> None:
    """The throwaway suite, run with -n 1 then -n 0; prints [{workers, exit, out, trend}]."""
    with tempfile.TemporaryDirectory() as t:
        s = Path(t, "s")
        (s / "tests" / "gate").mkdir(parents=True)
        for f in ("conftest.py", "test_gate.py"):
            (s / "tests" / "gate" / f).write_text((ROOT / "tests" / "gate" / f).read_text())
        (s / "pyproject.toml").write_text(
            '[tool.pytest.ini_options]\ntestpaths = ["tests/gate"]\n'
            'addopts = "--junitxml=.pytest_cache/junit.xml"\n'
        )
        (s / "gate-budget.toml").write_text("budget_seconds = 300\ntest_cpu_seconds = 0.15\n")
        for name, head in (("light", ""), ("heavy", ""), ("e2e", "# gate: e2e\n")):
            body = "echo light\n" if name == "light" else f"python3 -c '{BURN}'\n"
            (s / "tests" / f"{name}.sh").write_text(f"#!/usr/bin/env bash\n{head}{body}")
            (s / "tests" / f"{name}.sh").chmod(0o755)
        stage_mode = sys.argv[1:] == ["--stages"]
        if stage_mode:
            values = {
                "prep": 1.0, "build": 0.25, "install_cp": 0.25,
                "claimedgate": 0.25, "budget_clis": 0.125, "justqc": 0.125,
            }
            rows = [
                "cpu_stage " + json.dumps({"stage": name, "cpu_s": value, "status": "completed"})
                for name, value in values.items()
            ]
            inputs = {
                "valid": "\n".join(rows),
                "duplicate": "\n".join([rows[0], rows[0]]),
                "malformed": "cpu_stage {broken",
                "overflow": "\n".join(rows + [rows[0]]),
                "nonfinite": 'cpu_stage {"stage":"prep","cpu_s":NaN,"status":"completed"}',
                "bad_keys": 'cpu_stage {"stage":"prep","stage":"prep","cpu_s":0,"status":"completed"}',
                "unavailable": 'cpu_stage {"stage":"prep","cpu_s":null,"status":"unavailable"}',
            }
            (s / "tests" / "gate" / "test_stage_inputs.py").write_text(
                "import pytest\n"
                f"INPUTS = {inputs!r}\n"
                "@pytest.mark.parametrize('name', INPUTS)\n"
                "def test_inputs(name, record_property):\n"
                "    record_property('cpu_stage_source', 'scenario-stdout')\n"
                "    print(INPUTS[name])\n"
            )
        drop = ("HERDR_SESSION", "OCTO_FEATHER_QC_CLAIMS", "OCTO_FEATHER_QC_CAPTURE_DIR")
        env = {k: v for k, v in os.environ.items() if k not in drop}
        env |= {"XDG_STATE_HOME": str(Path(t, "xdg")), "GATE_RECIPES": ""}
        trend = Path(t, "xdg", "octo-feather", "check-runs.jsonl")
        pytest_cmd = ["uv", "run", "--project", str(ROOT), "--locked", "--offline", "--no-sync"]
        runs: list[dict[str, object]] = []
        for workers in (1, 0):
            p = subprocess.run(
                [*pytest_cmd, "pytest", "-n", str(workers), *(["-rA"] if stage_mode else [])],
                cwd=s,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            last = trend.read_text().splitlines()[-1] if trend.is_file() else "{}"
            stage_reports: dict[str, object] = {}
            if stage_mode:
                suite = ET.parse(s / ".pytest_cache" / "junit.xml")
                for case in suite.iter("testcase"):
                    prop = case.find("properties/property[@name='cpu_stages']")
                    if prop is not None:
                        name = (case.get("name") or "").split("[", 1)[1].removesuffix("]")
                        stage_reports[name] = json.loads(prop.get("value") or "{}")
            runs.append(
                {
                    "workers": workers,
                    "exit": p.returncode,
                    "out": p.stdout + p.stderr,
                    "trend": json.loads(last),
                    "stages": stage_reports,
                }
            )
    sys.stdout.write(json.dumps(runs) + "\n")


if __name__ == "__main__":
    scenario()
