"""The scenarios of tests/gate/kit/test_import_contract.py (its items), this file their command
(testkit.main): the import contract that keeps shared test support in the testkit (#684; owner
ruling #577; the contract type: tests/gate/import_contracts.py), `lint-imports` from the kit's
environment (the interpreter running this file), offline, as check-lint runs it.

kit: the kit as is keeps the contract; then the kit's own config and contract type in a scratch
tree laid out as tests/gate/kit/ (a testkit, a scenario and its test_ importing it, the testkit
imported by both) with a test importing a helper beside it, and a scenario importing another
test's scenario: the contract breaks naming each importing file, line and module, and no allowed
import. template_python: templates/python's config and its copy of the contract type keep the
template as is, and break naming a test that imports a helper beside it. Each run's output is
printed. templates/typescript's rule is dependency-cruiser's own (its .dependency-cruiser.cjs),
run by that template's gate.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from testkit import ROOT, Ran, Scratch, main
from testkit.template import uncoloured

LINT_IMPORTS = str(Path(sys.executable).parent / "lint-imports")
HELPER = "def helper() -> int:\n    return 1\n"
USES_HELPER = "from b_helpers import helper\n\n\ndef test_a() -> None:\n    assert helper() == 1\n"


def contract(s: Scratch, cwd: Path, want: int, **env: str) -> str:
    """lint-imports run in CWD, exiting WANT; its output (rich wraps at COLUMNS: wide here)."""
    uncoloured(s)
    got: Ran = s.run(
        [LINT_IMPORTS, "--no-cache", "--no-logo"], cwd=cwd, want=want, env={"COLUMNS": "300", **env}
    )
    sys.stdout.write(f"$ lint-imports in {cwd}\n{got.out}\n")
    return got.out


def write(root: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)


def kit(s: Scratch) -> None:
    out = contract(s, ROOT, 0)
    assert "kit tests import shared support only from the testkit KEPT" in out, out
    t = s.root / "tree"
    (t / "tests/gate").mkdir(parents=True)
    shutil.copy(ROOT / "pyproject.toml", t / "pyproject.toml")
    shutil.copy(ROOT / "tests/gate/import_contracts.py", t / "tests/gate/import_contracts.py")
    write(
        t / "tests/gate/kit",
        {
            "testkit/__init__.py": "ROOT = 1\n",
            "lint.py": "from testkit import ROOT\n\n\ndef baselines() -> int:\n    return ROOT\n",
            "test_lint.py": "from lint import baselines\nfrom testkit import ROOT\n\n\n"
            "def test_lint() -> None:\n    assert baselines() == ROOT\n",
            "b_helpers.py": HELPER,
            "test_a.py": USES_HELPER,
            "other.py": "from lint import baselines\n\nN = baselines()\n",
        },
    )
    out = contract(s, t, 1)
    for want in (
        (
            "tests/gate/kit/test_a.py:1 imports b_helpers, a module beside it "
            "(tests/gate/kit/b_helpers.py): from b_helpers import helper"
        ),
        "tests/gate/kit/other.py:1 imports lint, a module beside it (tests/gate/kit/lint.py)",
        "Shared test support lives in one place (testkit): move it there.",
    ):
        assert want in out, f"no {want!r} in:\n{out}"
    assert "test_lint.py" not in out, f"an allowed import named:\n{out}"
    assert "imports testkit" not in out, f"an allowed import named:\n{out}"


def template_python(s: Scratch) -> None:
    t = s.root / "template"
    tpl = ROOT / "templates" / "python"
    t.mkdir()
    shutil.copy(tpl / "pyproject.toml", t / "pyproject.toml")
    for d in ("src", "tests"):
        shutil.copytree(tpl / d, t / d)
    src = str(t / "src")  # the app package, as the template's own environment installs it
    out = contract(s, t, 0, PYTHONPATH=src)
    assert "tests import shared support only from the testkit KEPT" in out, out
    write(t / "tests/integration", {"b_helpers.py": HELPER, "test_a.py": USES_HELPER})
    out = contract(s, t, 1, PYTHONPATH=src)
    want = (
        "tests/integration/test_a.py:1 imports b_helpers, a module beside it "
        "(tests/integration/b_helpers.py): from b_helpers import helper"
    )
    assert want in out, f"no {want!r} in:\n{out}"


if __name__ == "__main__":
    main(kit, template_python)
