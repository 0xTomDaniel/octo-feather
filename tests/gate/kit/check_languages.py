"""The scenarios of tests/gate/kit/test_check_languages.py (its items), this file their command
(testkit.main): scripts/check-languages, the gate behind `just check-languages` (owner rulings
#225, #261), run directly in a git copy of the kit's tracked files (testkit.kit_repo) with the
kit's mise pins, uv environment and node_modules: the clean copy passes; then planted files fail it,
each named with its fix, all on one run (the checker reports every finding): an Unknown type, an
unmapped language (Go), shell outside ShellCheck's list, Python outside ruff's, TypeScript outside
tsc's, a shebang scc cannot read (env -S), two pnpm pins, a gate tool's recipe out of
GATE_RECIPES. An extensionless file with no shebang passes by design (no language found).
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from testkit import ROOT, Scratch, kit, kit_repo, main, tool_homes

if TYPE_CHECKING:
    from pathlib import Path

TAG = "languages test"


def copy(s: Scratch) -> tuple[Path, dict[str, str]]:
    k = kit_repo(s)
    # A link, which .gitignore's node_modules/ (a directory pattern) does not match: excluded by
    # name.
    (k / "node_modules").symlink_to(ROOT / "node_modules")
    with (k / ".git" / "info" / "exclude").open("a") as fh:
        fh.write("/node_modules\n")
    return k, {**tool_homes(), "UV_PROJECT_ENVIRONMENT": str(ROOT / ".venv")}


def plant(k: Path, rel: str, body: str) -> None:
    p = k / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body + "\n")
    p.chmod(0o755)


def languages(s: Scratch) -> None:
    """The clean copy passes; then every planted file on one run, each named."""
    k, env = copy(s)
    r = s.run([kit("check-languages")], cwd=k, env=env)
    assert "languages: ok (" in r.out, f"{TAG}: the clean copy: {r.out}\n{r.err}"
    plant(k, "notes.xyz", "data")
    plant(k, "tool.go", "package main")
    plant(k, "scripts/x-shell", "#!/usr/bin/env bash\necho ok")
    plant(k, "scripts/x-py", "#!/usr/bin/env python3\nprint(1)")
    plant(k, "scripts/x-envs", "#!/usr/bin/env -S uv run --script\nprint(1)")
    plant(k, ".agents/skills/herdr-comms/assets/x.ts", "export const x = 1;")
    plant(k, "x-data", "just data, no shebang")
    pj = k / "package.json"
    d = json.loads(pj.read_text())
    d["packageManager"] = "pnpm@10.7.0"
    pj.write_text(json.dumps(d, indent=2) + "\n")
    jf = k / "justfile"
    old = 'export GATE_RECIPES := "check-languages check-scripts '
    assert old in jf.read_text(), f"{TAG}: justfile lacks {old!r}"
    jf.write_text(jf.read_text().replace(old, 'export GATE_RECIPES := "check-languages ', 1))
    s.git(k, "add", "-A")
    r = s.run([kit("check-languages")], cwd=k, env=env, want=1)
    out = f"{r.out}\n{r.err}"
    for w in (
        "notes.xyz: scc does not know this file type",
        "Go (tool.go) has no lint or type step",
        (
            "scripts/x-shell: BASH, but shellcheck's own file list misses it; ShellCheck's file "
            "list: give a file the `shell` attribute in .gitattributes (just shell-files)"
        ),
        (
            "scripts/x-py: Python, but ruff's own file list misses it; ruff's own file list, which "
            "basedpyright gets whole: name an extensionless script in pyproject.toml "
            "extend-include (just python-files)"
        ),
        "scripts/x-envs: scc cannot name the language of its shebang",
        ".agents/skills/herdr-comms/assets/x.ts: TypeScript, but tsc's own file list misses it",
        (
            "package.json: packageManager and mise.toml [tools] pnpm both pin pnpm; delete "
            "packageManager"
        ),
        "shellcheck gates BASH, but its recipe check-scripts is not in the gate",
    ):
        assert w in out, f"{TAG}: output lacks: {w}\n{out}"
    assert "x-data" not in out, f"{TAG}: an extensionless file with no shebang was named: {out}"


if __name__ == "__main__":
    main(languages)
