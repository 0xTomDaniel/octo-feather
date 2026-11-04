"""The gate's steps as pytest items: each GATE_RECIPES recipe in the justfile, run as a command.

Run through `just check`, `just fast` or `just test`, which export GATE_RECIPES; bare
`uv run pytest` skips them.
"""

import os
import pathlib
import shutil
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if "GATE_RECIPES" not in os.environ:
    pytest.skip(
        "GATE_RECIPES is unset: run the gate through `just check` or `just test`",
        allow_module_level=True,
    )
RECIPES = os.environ["GATE_RECIPES"].split()


@pytest.mark.parametrize("recipe", RECIPES)
def test_recipe(recipe: str) -> None:
    just = shutil.which("just")
    assert just, "just is not on PATH"
    rc = subprocess.run([just, recipe], cwd=ROOT, check=False).returncode
    if rc != 0:
        pytest.fail(f"just {recipe} exited {rc} (its output: Captured stdout/stderr below)")
