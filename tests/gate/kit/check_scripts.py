"""The scenario of tests/gate/kit/test_check_scripts.py (its item), this file its command
(testkit.main): `just check-scripts`, a justfile recipe (rules: #121 D1, #361), so run through
just, in a git repo holding what the recipe runs on (the justfile and its guard, the tool pins,
the lint config and lister, .gitattributes, one clean shell file; #507: the kit's own files are
the recipe's gate item, not this test's; prepared once per gate run, the kit's uv environment
serving it offline). Each planted file makes it fail naming it, or pass. ShellCheck runs over the
`shell` attribute's files (.gitattributes); Python byte-compiles over ruff's list; which files
belong to which language is check-languages' rule (tests/gate/kit/check_languages.py). The recipe
stops at its first failing step (ShellCheck, the Python list, compile, executables), so each step
is one run, holding every case of that step:

- clean, with files sourcing each other across ShellCheck's batches (#507: a file and the file it
  sources, by directive or literal path, share one run, so ShellCheck reads what the sourced file
  sets, no SC2154): passes, printing the shellcheck ok line;
- bad shell wherever the attribute names it (a *.sh file, an extensionless script, a skill asset)
  and in a sourced file, still checked as an input: each named;
- D1: parses, but byte-compile refuses (return, break, continue, yield, nonlocal outside a
  function or loop), in ruff's list: each named;
- fails closed (#507): ruff's file list crashing (an environment without the lister's tomlkit, as
  an unsynced kit venv) fails naming the fix, never python: ok (0 files compile);
- a script in scripts/ that is not executable: named.
"""

from __future__ import annotations

import shutil
import subprocess
from typing import TYPE_CHECKING

from testkit import ROOT, Scratch, main, tool_homes

if TYPE_CHECKING:
    from pathlib import Path

TAG = "check-scripts test"
FILES = (
    "justfile",
    ".gitattributes",
    "pyproject.toml",
    "uv.lock",
    ".python-version",
    "mise.toml",
    "mise.lock",
    "mise-version",
    "scripts/check-gate-free",
    "scripts/octo-feather-lint",
)
BAD_SH = "#!/usr/bin/env bash\nif then fi"
LIB = "# shellcheck shell=bash\n# shellcheck disable=SC2034\nx_planted=1"


def build(p: Scratch) -> None:
    r = p.root / "repo"
    for n in FILES:
        (r / n).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / n, r / n)
    plant(r, "tests/x-clean.sh", "#!/usr/bin/env bash\necho ok")
    p.git(r, "init", "-q")
    p.git(r, "add", "-A")
    p.git(r, "commit", "-qm", "base")


def plant(r: Path, rel: str, body: str, mode: int = 0o755) -> None:
    p = r / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body + "\n")
    p.chmod(mode)


def shell(r: Path, rel: str) -> None:
    """REL given the `shell` attribute."""
    with (r / ".gitattributes").open("a") as fh:
        fh.write(f"{rel} shell\n")


def run(s: Scratch, r: Path, want: int, env: dict[str, str] | None = None) -> str:
    """`just check-scripts` on R with every plant tracked, exit WANT; then back to the base."""
    s.git(r, "add", "-A")
    e = {**s.env, "UV_PROJECT_ENVIRONMENT": str(ROOT / ".venv"), **(env or {})}
    # Not Scratch.run: the crashing lister's own traceback is the case below, and the recipe's to
    # print.
    p = subprocess.run(
        ["just", "check-scripts"],  # noqa: S607
        cwd=r,
        env=e,
        capture_output=True,
        text=True,
        check=False,
    )
    out = f"{p.stdout}\n{p.stderr}"
    assert p.returncode == want, (
        f"{TAG}: just check-scripts: exit {p.returncode}, want {want}: {out}"
    )
    s.git(r, "reset", "-q", "--hard")
    s.git(r, "clean", "-qfd")
    return out


def named(out: str, *files: str) -> None:
    for f in files:
        assert f in out, f"{TAG}: {f} not named in the output: {out}"


def scripts(s: Scratch) -> None:
    s.prepare("check-scripts", build)
    s.env |= (
        tool_homes()
    )  # the kit's mise tools and uv cache, never fetched again into the scratch HOME
    r = s.root / "repo"
    # Clean, plus a file and the file it sources sharing one ShellCheck run, by directive or
    # literal path.
    for i in range(1, 9):
        plant(r, f"tests/lib/x-planted-lib{i}.sh", LIB, 0o644)
    plant(
        r,
        "tests/x-planted-a.sh",
        "#!/usr/bin/env bash\n# shellcheck source=tests/lib/x-planted-lib3.sh\n"
        'source "$(dirname "$0")/lib/x-planted-lib3.sh"\necho "$x_planted"',
    )
    plant(
        r,
        "tests/x-planted-b.sh",
        '#!/usr/bin/env bash\nsource tests/lib/x-planted-lib6.sh\necho "$x_planted"',
    )
    named(run(s, r, 0), "scripts: shellcheck ok")
    # Bad shell wherever the attribute names it, and in a sourced file, still an input: one run,
    # each named.
    bad = ["tests/x-planted.sh", "scripts/x-planted", ".agents/skills/herdr-comms/assets/x-planted"]
    for f in bad:
        plant(r, f, BAD_SH)
    shell(r, bad[1])
    shell(r, bad[2])
    plant(r, "tests/lib/x-planted-lib5.sh", "# shellcheck shell=bash\nif then fi", 0o644)
    plant(
        r,
        "tests/x-planted-c.sh",
        "#!/usr/bin/env bash\n# shellcheck source=tests/lib/x-planted-lib5.sh\n"
        'source "$(dirname "$0")/lib/x-planted-lib5.sh"',
    )
    named(run(s, r, 1), *bad, "tests/lib/x-planted-lib5.sh")
    # D1: each refused by byte-compile, one run.
    for n, body in enumerate(("return 1", "break", "continue", "yield 1", "nonlocal x"), 1):
        plant(r, f"scripts/x_planted{n}.py", body, 0o644)
    named(run(s, r, 1), *(f"scripts/x_planted{n}.py" for n in range(1, 6)))
    # Fails closed: a crashing Python file list (a venv without the lister's tomlkit).
    venv = s.root / "venv"
    s.run(["uv", "venv", "--offline", "--quiet", str(venv)])
    out = run(s, r, 1, {"UV_PROJECT_ENVIRONMENT": str(venv)})
    named(
        out,
        "check-scripts: the Python file list (octo-feather-lint files) failed",
        "uv sync --locked",
    )
    assert "python: ok" not in out, f"{TAG}: a crashing Python file list printed python: ok: {out}"
    # A script in scripts/ that is not executable.
    plant(r, "scripts/x-planted.sh", "#!/usr/bin/env bash\necho ok", 0o644)
    named(run(s, r, 1), "scripts/x-planted.sh")


if __name__ == "__main__":
    main(scripts)
