"""tests/fast.sh's pytest kit test file, copied to tests/gate/kit/ of its throwaway kit: each
function is its own gate item; each appends its name to $FAST_RAN, and test_one runs fixture-a,
test_two fixture-g, test_e2e (pytest's e2e marker) nothing."""

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


def ran(name: str, script: str = "") -> None:
    with Path(os.environ["FAST_RAN"]).open("a") as f:
        f.write(name + "\n")
    if script:
        subprocess.run([str(ROOT / "scripts" / script)], check=True)


def test_one() -> None:
    ran("one", "fixture-a")


def test_two() -> None:
    ran("two", "fixture-g")


@pytest.mark.e2e
def test_e2e() -> None:
    ran("x")
