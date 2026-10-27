"""The kit's gate as pytest items (#224): each check recipe the justfile lists in GATE_RECIPES, then each
tests/*.sh, run as a command by subprocess (docs/adr/0002); nothing here imports a kit script.

Run through `just check` or `just test [pytest args]`, which put the kit's commands on PATH and export
GATE_RECIPES. Items see TMPDIR as its real path (macOS: mktemp paths under the /var symlink would not
match the pwd -P paths tests compare them with).
"""
import os, pathlib, subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
if "GATE_RECIPES" not in os.environ:
    raise pytest.UsageError("GATE_RECIPES is unset: run the gate through `just check` or `just test` (the justfile lists the recipes)")
RECIPES = os.environ["GATE_RECIPES"].split()
SCRIPTS = sorted(p.relative_to(ROOT).as_posix() for p in ROOT.glob("tests/*.sh"))


def run(cmd):
    env = dict(os.environ, TMPDIR=os.path.realpath(os.environ.get("TMPDIR") or "/tmp"))
    rc = subprocess.run(cmd, cwd=ROOT, env=env).returncode
    if rc != 0:
        pytest.fail(f"{' '.join(cmd)} exited {rc} (its output: Captured stdout/stderr below)", pytrace=False)


@pytest.mark.parametrize("recipe", RECIPES)
def test_recipe(recipe):
    run(["just", recipe])


@pytest.mark.parametrize("script", SCRIPTS)
def test_script(script):
    run([str(ROOT / script)])
