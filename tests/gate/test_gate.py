"""The kit's gate as pytest items (#224): each check recipe the justfile lists in GATE_RECIPES, then each
tests/*.sh, run as a command by subprocess (docs/adr/0002); nothing here imports a kit script.

Run through `just check` or `just test [pytest args]`, which put the kit's commands on PATH and export
GATE_RECIPES. Items see TMPDIR as its real path (macOS: mktemp paths under the /var symlink would not
match the pwd -P paths tests compare them with). Items are pane-neutral (#493 AC6): none inherits the
variables a Herdr pane gives its shell (every HERDR_* one, as HERDR_SESSION names a named session) or the
route pi-role and herdr-spawn export to a pane, so a gate run in a pane of any session runs every item as
one outside Herdr does. Items share one dir per gate run, GATE_RUN_DIR, where tests/lib/prepared.py prepares the
template installs several items repeat, once per run (pytest-xdist's documented "session fixture once" pattern: the
xdist workers' shared tmp dir, the parent of each worker's basetemp; pytest keeps its last 3 basetemps).
Each item's processes carry its name, GATE_ITEM (a recipe, or a tests/*.sh path), unless a gate this item runs
inside already set it: the coverage map of `just fast-map` files each process under the outermost item.
"""
import os, pathlib, subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
if "GATE_RECIPES" not in os.environ:
    raise pytest.UsageError("GATE_RECIPES is unset: run the gate through `just check` or `just test` (the justfile lists the recipes)")
RECIPES = os.environ["GATE_RECIPES"].split()
PANE = ("OCTO_FEATHER_PARENT", "OCTO_FEATHER_SESSION_ID", "OCTO_FEATHER_ROLE", "OCTO_FEATHER_SPEND_SPACE",
        "OCTO_FEATHER_OPERATING_MODEL")
SCRIPTS = sorted(p.relative_to(ROOT).as_posix() for p in ROOT.glob("tests/*.sh"))


@pytest.fixture(scope="session")
def run_dir(request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory) -> str:
    base = tmp_path_factory.getbasetemp()
    return str(base.parent if hasattr(request.config, "workerinput") else base)   # an xdist worker: the run's shared dir


def run(cmd, run_dir: str, item: str):
    env = {k: v for k, v in os.environ.items() if not k.startswith("HERDR_") and k not in PANE}
    env["GATE_RUN_DIR"] = run_dir
    env.setdefault("GATE_ITEM", item)
    env["TMPDIR"] = os.path.realpath(os.environ.get("TMPDIR") or "/tmp")
    rc = subprocess.run(cmd, cwd=ROOT, env=env).returncode
    if rc != 0:
        pytest.fail(f"{' '.join(cmd)} exited {rc} (its output: Captured stdout/stderr below)", pytrace=False)


@pytest.mark.parametrize("recipe", RECIPES)
def test_recipe(recipe, run_dir: str):
    run(["just", recipe], run_dir, f"{recipe}")


@pytest.mark.parametrize("script", SCRIPTS)
def test_script(script, run_dir: str):
    run([str(ROOT / script)], run_dir, f"{script}")
