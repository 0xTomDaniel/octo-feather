"""The scenario of tests/gate/kit/test_gate_trend_tier.py (its item), this file its command
(testkit.main): the trend line's tier (tests/gate/conftest.py, the hook templates/python copies;
#536). pytest, run as a command (the kit venv's, directly) on a throwaway suite holding a copy of
the hook, appends one check-runs.jsonl line per run whose tier is `full` only when the invocation
narrowed nothing (no paths or node ids, -k, -m, --lf, --deselect, --ignore) and, where the root's
justfile declares GATE_RECIPES, the run carries exactly that value (a bare pytest skips the gate's
static steps), xdist or not, else `subset`. The gate-time budget counts full runs only (comms
#report-field-gate-time)."""

from __future__ import annotations

import json
import shutil
import subprocess

from testkit import ROOT, Scratch, asked, main

TAG = "gate-trend-tier test"


def tier(s: Scratch) -> None:
    py = asked(
        "uv",
        "run",
        "--locked",
        "--offline",
        "--no-sync",
        "python",
        "-c",
        "import sys; print(sys.executable)",
    )
    s.env.pop("HERDR_SESSION", None)
    s.env.pop("GATE_RECIPES", None)
    s.env["XDG_STATE_HOME"] = str(s.root / "xdg")
    trend = s.root / "xdg" / "octo-feather" / "check-runs.jsonl"
    suite = s.root / "s"
    (suite / "tests").mkdir(parents=True)
    shutil.copy(ROOT / "tests" / "gate" / "conftest.py", suite / "tests" / "conftest.py")
    (suite / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\ntestpaths = ["tests"]\n'
        'addopts = "--junitxml=.pytest_cache/junit.xml"\n'
    )
    (suite / "tests" / "test_ab.py").write_text(
        "def test_a():\n    pass\n\n\ndef test_b():\n    pass\n"
    )
    (suite / "tests" / "test_c.py").write_text("def test_c():\n    pass\n")
    n = 0

    def expect(want: str, items: int, *args: str, recipes: str | None = None) -> None:
        """One more trend line, with tier WANT and ITEMS steps, from pytest ARGS (GATE_RECIPES
        RECIPES, else unset)."""
        nonlocal n
        env = dict(s.env)
        if recipes is not None:
            env["GATE_RECIPES"] = recipes
        p = subprocess.run(
            [py, "-m", "pytest", "-q", *args],
            cwd=suite,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert p.returncode == 0, f"{TAG}: pytest {args}: {p.stdout}{p.stderr}"
        n += 1
        lines = trend.read_text().splitlines()
        assert len(lines) == n, f"{TAG}: pytest {args}: no one new trend line"
        d = json.loads(lines[-1])
        got = (d.get("tier"), len(d["steps"]))
        assert got == (want, items), (
            f"{TAG}: pytest {args}: tier and steps {got}, want {want} {items}"
        )

    expect("full", 3)
    expect("full", 3, "-n", "2")
    expect("subset", 2, "tests/test_ab.py")
    expect("subset", 1, "tests/test_ab.py::test_a")
    expect("subset", 1, "-k", "test_c")
    expect("subset", 1, "-n", "2", "-k", "test_c")
    expect("subset", 2, "--deselect", "tests/test_c.py::test_c")
    expect("subset", 2, "--ignore", "tests/test_c.py")
    expect("subset", 3, "-m", "not slow")
    # A justfile declaring the gate's static steps (GATE_RECIPES): full only when the run carries
    # exactly that value, so a bare pytest, which skips them (the template's tests/test_gate.py),
    # records subset.
    (suite / "justfile").write_text('export GATE_RECIPES := "check-a check-b"\n')
    expect("subset", 3)
    expect("subset", 3, recipes="check-a")
    expect("full", 3, recipes="check-a check-b")
    expect("full", 3, "-n", "2", recipes="check-a check-b")


if __name__ == "__main__":
    main(tier)
