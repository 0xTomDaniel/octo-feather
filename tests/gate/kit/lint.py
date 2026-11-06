"""The scenarios of tests/gate/kit/test_lint.py (its items), this file their command
(testkit.main): octo-feather-lint (#244; its --help) run as a command in a throwaway target repo
(any repo, not the kit), with ruff and basedpyright from the kit's environment, offline: the
interpreter running this file, its bin first on PATH, the command run directly (no uv run).

`init` takes the baselines (prepared once per gate run: `baselined`); then a new ruff code in a
file fails `lint` naming file:line and rule, a new basedpyright error fails `types` naming
file:line and rule (also in an extensionless script under a dot directory, which basedpyright
skips unless the mirror works), a new unformatted file fails `format`; a fixed violation leaves
a stale entry that fails naming `octo-feather-lint shrink`, and shrink deletes only it; shrink
never adds an entry, even with a new violation present (grew). With no tracked Python no tool
runs; with every baselined file gone every entry is stale and shrink empties both baselines.
basedpyright is most of each item's CPU (about 1.3 s a run; init and shrink run it twice: a
product fact), so each fact a call shows is read off that call: init's and shrink's own
closing lint/types lines say the repo is green after them.
"""

from __future__ import annotations

import difflib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import cast

import tomllib
from testkit import Ran, Scratch, kit, main

LINT = kit("octo-feather-lint")
VENV_BIN = str(Path(sys.executable).parent)
TOOL = "bin/tool"
RUN = ".agents/skills/s/scripts/run"
PYPROJECT = """\
[project]
name = "target"
version = "0"
requires-python = ">=3.12"

[tool.ruff]
line-length = 100
# The extensionless scripts by name: the file set is ruff's own list (bin/shell stays out).
extend-include = ["bin/tool", ".agents/skills/s/scripts/run"]

# A table between [tool.ruff] and its sub-tables: init and shrink edit it as split tables.
[tool.basedpyright]
typeCheckingMode = "strict"

[tool.ruff.lint]
select = ["ALL"]
ignore = ["COM812", "CPY001", "D"]

[tool.ruff.format]
quote-style = "double"  # config beside the baseline's exclude, kept as written
"""
BARE = '[tool.ruff.lint]\nselect = ["ALL"]\n\n[tool.basedpyright]\ntypeCheckingMode = "strict"\n'
M_PY = "def double(n: int) -> int:\n    return n * 2\n"
# bin/tool: one ruff code (T201) and one type error, both baselined by init.
TOOL_PY = '#!/usr/bin/env python3\nN: int = "x"\nprint(N)\n'
RUN_PY = "#!/usr/bin/env -S uv run --script\nVALUE = 1\n"


def lint(s: Scratch, repo: Path, cmd: str, want: int = 0) -> str:
    """`octo-feather-lint CMD` in REPO exits WANT; its stdout and stderr together."""
    env = {"PATH": f"{VENV_BIN}:{s.env['PATH']}"}
    r: Ran = s.run([sys.executable, LINT, cmd], want=want, cwd=repo, env=env)
    return f"{r.out}\n{r.err}"


def says(out: str, *texts: str) -> None:
    for x in texts:
        assert x in out, f"did not print {x!r}:\n{out}"


def write(path: Path, text: str, *, mode: str = "w") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open(mode) as f:
        f.write(text)


def repo_of(s: Scratch, t: Path, files: dict[str, str]) -> Path:
    """A git repo at T holding FILES, committed."""
    for rel, text in files.items():
        write(t / rel, text)
    for rel in (TOOL, "bin/shell", RUN):
        if (t / rel).exists():
            (t / rel).chmod(0o755)
    s.git(t, "init", "-q")
    s.git(t, "add", "-A")
    s.git(t, "commit", "-qm", "base")
    return t


def build_baselined(p: Scratch) -> None:
    """The target with its three Python files, a shell script, and init's baselines committed;
    init's output kept in init.out (read by baselines)."""
    t = repo_of(
        p,
        p.root / "t",
        {
            "pyproject.toml": PYPROJECT,
            "pkg/m.py": M_PY,
            TOOL: TOOL_PY,
            RUN: RUN_PY,
            "bin/shell": "#!/bin/sh\necho not python\n",
        },
    )
    (p.root / "init.out").write_text(lint(p, t, "init"))
    p.git(t, "add", "-A")
    p.git(t, "commit", "-qm", "baselines")


def baselined(s: Scratch) -> Path:
    s.prepare("lint-baselined", build_baselined)
    return s.root / "t"


def head(repo: Path, path: str) -> str:
    r = subprocess.run(
        ["git", "-C", str(repo), "show", f"HEAD:{path}"],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    )
    return r.stdout if r.returncode == 0 else ""


def sub(node: object, *keys: str) -> object:
    for key in keys:
        node = cast("dict[str, object]", node).get(key, {}) if isinstance(node, dict) else {}
    return node


def ruff_entries(text: str) -> Counter[str]:
    data = tomllib.loads(text) if text else {}
    lint_t = cast(
        "dict[str, list[str]]", sub(data, "tool", "ruff", "lint", "extend-per-file-ignores")
    )
    fmt = cast("list[str]", sub(data, "tool", "ruff", "format", "exclude") or [])
    found = Counter(f"ruff check {p} {c}" for p, codes in lint_t.items() for c in codes)
    found.update(f"ruff format {p}" for p in fmt)
    return found


def pyright_entries(text: str) -> Counter[str]:
    files = cast("dict[str, list[object]]", sub(json.loads(text) if text else {}, "files"))
    return Counter(
        f"basedpyright {p} {json.dumps(e, sort_keys=True)}"
        for p, errs in files.items()
        for e in errs
    )


def grown(repo: Path) -> list[str]:
    """Every baseline entry the working tree holds more of than HEAD: the ruff tables of
    pyproject.toml and basedpyright's .basedpyright/baseline.json, each entry counted."""
    now = ruff_entries((repo / "pyproject.toml").read_text())
    then = ruff_entries(head(repo, "pyproject.toml"))
    pyright = repo / ".basedpyright" / "baseline.json"
    now += pyright_entries(pyright.read_text() if pyright.is_file() else "")
    then += pyright_entries(head(repo, ".basedpyright/baseline.json"))
    return sorted((now - then).elements())


def baselines(s: Scratch) -> None:
    """The file set; init's baselines and its green close; init refusing a second time; new
    ruff codes, new type errors (shrink adding nothing beside them) and a new unformatted file
    each failing naming file:line and rule."""
    t = baselined(s)
    files = lint(s, t, "files")
    assert files == f"{RUN}\n{TOOL}\npkg/m.py\n", f"file set is not the 3 Python files: {files}"
    # init's own close: it ran types on the baselined repo, green over the 3 files.
    says((s.root / "init.out").read_text(), "types: ok (basedpyright analyzed 3 files)")
    py = (t / "pyproject.toml").read_text()
    assert '"bin/tool" = [' in py, f"init wrote no ruff baseline for bin/tool: {py}"
    assert '"T201",' in py, f"init wrote no ruff baseline for bin/tool: {py}"
    says(lint(s, t, "init", want=1), "a baseline exists")
    # A new ruff code in a clean file, and one new in a baselined file: one lint run.
    write(t / "pkg/m.py", "import os\n", mode="a")
    write(t / TOOL, "assert N\n", mode="a")
    out = lint(s, t, "lint", want=1)
    says(out, "pkg/m.py:3: F401", "fix:", "never add F401 for pkg/m.py")
    says(out, "bin/tool:4: S101", "never add S101 for bin/tool")
    s.git(t, "checkout", "-q", "--", "pkg/m.py", TOOL)
    # A new basedpyright error in a .py file and in the dot-directory script: one types run.
    write(t / "pkg/m.py", "def name() -> str:\n    return double(1)\n", mode="a")
    write(t / RUN, 'COUNT: int = "two"\n', mode="a")
    out = lint(s, t, "types", want=1)
    says(out, "pkg/m.py:4: reportReturnType", "fix:", f"{RUN}:3: reportAssignmentType")
    # Shrink refuses to grow: with those new errors present it adds nothing to either baseline.
    lint(s, t, "shrink", want=1)
    assert not grown(t), f"shrink grew a baseline: {grown(t)}"
    s.git(t, "checkout", "-q", "--", "pkg/m.py", RUN)
    # A new unformatted file.
    write(t / "pkg/n.py", 'X = {  "a":1 }\n')
    s.git(t, "add", "pkg/n.py")
    says(lint(s, t, "format", want=1), "pkg/n.py:1: unformatted", "ruff format --diff pkg/n.py")


def stale(s: Scratch) -> None:
    """Fixed violations leave stale entries naming shrink; shrink deletes only them, never an
    emptied array outside the baseline table, and leaves the repo green (its own close)."""
    t = baselined(s)
    write(t / "pyproject.toml", '\n[tool.unrelated]\n"extra" = [\n]\n', mode="a")
    s.git(t, "commit", "-qam", "unrelated")
    write(
        t / TOOL, '#!/usr/bin/env python3\nimport sys\n\nN: int = 1\nsys.stdout.write(f"{N}\\n")\n'
    )
    says(lint(s, t, "lint", want=1), "T201 no longer fires in bin/tool", "octo-feather-lint shrink")
    says(lint(s, t, "types", want=1), "no longer occur", "octo-feather-lint shrink")
    before = (t / "pyproject.toml").read_text()
    out = lint(s, t, "shrink")
    # shrink's own close: lint and types green over the 3 files after it.
    says(out, "lint: ok (3 files, ruff check)", "types: ok (basedpyright analyzed 3 files)")
    after = (t / "pyproject.toml").read_text()
    # Only bin/tool's emptied key went; every other byte of pyproject.toml is as it was.
    diff = difflib.ndiff(before.splitlines(), after.splitlines())
    gone = [ln for ln in diff if ln[:2] in {"- ", "+ "}]
    want = ['- "bin/tool" = [', '-     "T201",', "- ]"]
    assert gone == want, f"shrink changed more of pyproject.toml than bin/tool's key: {gone}"
    assert not grown(t), f"shrink grew a baseline: {grown(t)}"
    assert '"T201",' not in after, "shrink left the stale T201"
    assert '"extra" = [' in after.splitlines(), "shrink deleted [tool.unrelated] extra"


def empty_sets(s: Scratch) -> None:
    """No tracked Python: no tool runs, so an untracked file is never linted, formatted or typed.
    Every baselined file gone: the set is empty, every entry of each baseline stale; shrink
    empties them."""
    t = repo_of(s, s.root / "t", {"pyproject.toml": BARE})
    write(t / "untracked.py", "import nonexistent\n")
    says(lint(s, t, "lint"), "lint: ok (0 files")
    says(lint(s, t, "format"), "format: ok (0 files")
    says(lint(s, t, "types"), "analyzed 0 files")
    bad = {"pyproject.toml": BARE, "bad.py": 'N: int = "x"\nX = {  "a":1 }\n'}
    t = repo_of(s, s.root / "gone", bad)
    lint(s, t, "init")
    s.git(t, "add", "-A")
    s.git(t, "commit", "-qm", "baselines")
    base = t / ".basedpyright" / "baseline.json"
    assert '"./bad.py"' in base.read_text(), "init did not baseline bad.py's type error"
    s.git(t, "rm", "-q", "bad.py")
    s.git(t, "commit", "-qm", "gone")
    says(lint(s, t, "lint", want=1), "bad.py is not in the file set", "octo-feather-lint shrink")
    says(lint(s, t, "format", want=1), "bad.py is formatted or gone", "octo-feather-lint shrink")
    says(lint(s, t, "types", want=1), "no longer occur", "octo-feather-lint shrink")
    lint(s, t, "shrink")
    assert base.read_text() == '{\n    "files": {}\n}', f"shrink left {base.read_text()}"
    assert "bad.py" not in (t / "pyproject.toml").read_text(), "shrink left a bad.py ruff entry"
    lint(s, t, "lint")
    lint(s, t, "format")
    lint(s, t, "types")


if __name__ == "__main__":
    main(baselines, stale, empty_sets)
