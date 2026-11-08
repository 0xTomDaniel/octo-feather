"""The scenarios of tests/gate/kit/test_check_languages.py (its items), this file their command
(testkit.main): scripts/check-languages, the gate behind `just check-languages` (owner rulings
#225, #261).

planted: run directly in a git copy of the kit's tracked files (testkit.kit_repo) with the kit's
mise pins, uv environment and node_modules: the clean copy passes; then planted files fail it,
each named with its fix, all on one run (the checker reports every finding): an Unknown type, an
unmapped language (Go), shell outside ShellCheck's list, Python outside ruff's, TypeScript outside
tsc's, a shebang scc cannot read (env -S), two pnpm pins, a gate tool's recipe out of
GATE_RECIPES. An extensionless file with no shebang passes by design (no language found).

The rest: check-languages fails closed on tsc's real failure, and the gate's race on
node_modules is gone (#663, #548; owner ruling #548 2026-11-04, #660: no silent failures),
through `just check-languages` and `just check-ts` in a throwaway copy of the kit's tracked
files, offline from the kit's uv environment and pnpm store.

tsc a stand-in at node_modules/.bin/tsc (what `pnpm exec tsc` runs): exiting 0 with empty stdout,
or failing with its own stderr, check-languages names the command, its exit code and what it
printed, never a JSON parse error; so for any tool it asks (scc printing only its stderr). No tsc in
node_modules nor on PATH (a box's global tsc masked, the premise asserted first: no_tsc), the
state a concurrent pnpm install leaves for a moment (it unlinks and rewrites
node_modules/.bin/tsc, #548): the real pnpm's exit and its stdout message are named.
And `just check-ts` on a current node_modules writes nothing there: its tsc launcher is the same
file after the run, so a check-languages running beside it (the gate runs both at once, after
check-tests installed) always finds tsc.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from testkit import ROOT, Ran, Scratch, kit, kit_repo, main, tool_homes
from testkit.kit_copy import Copy, no_tsc, tool

if TYPE_CHECKING:
    from pathlib import Path

CMD = "pnpm exec tsc --showConfig"
TAG = "languages test"


def kit_copy(s: Scratch) -> tuple[Path, dict[str, str]]:
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


def planted(s: Scratch) -> None:
    """The clean copy passes; then every planted file on one run, each named."""
    k, env = kit_copy(s)
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


def copy(s: Scratch) -> Copy:
    """The kit copy as a git repo (check-languages scans tracked files), on the kit's venv."""
    c = Copy(s)
    s.env["UV_PROJECT_ENVIRONMENT"] = str(ROOT / ".venv")
    s.git(c.dir, "init", "-q")
    s.git(c.dir, "add", "-A")
    s.git(c.dir, "commit", "-qm", "base")
    return c


def stand_in_tsc(c: Copy, body: str) -> None:
    b = c.dir / "node_modules" / ".bin"
    b.mkdir(parents=True)
    (b / "tsc").write_text(f"#!/bin/sh\n{body}\n")
    (b / "tsc").chmod(0o755)


def languages(c: Copy) -> Ran:
    return c.s.run([tool("just"), "check-languages"], cwd=c.dir, want=1)


def named(got: Ran, *want: str) -> None:
    for w in want:
        assert w in got.err, f"check-languages does not name {w!r}: {got.err}"
    assert "Expecting value" not in got.err, f"a bare parse error: {got.err}"


def tsc_silent(s: Scratch) -> None:
    """tsc exits 0 printing nothing: named, the command, exit 0, both streams empty."""
    c = copy(s)
    stand_in_tsc(c, "exit 0")
    named(
        languages(c),
        f"{CMD} exited 0 but printed no JSON config; stderr: (empty); stdout: (empty)",
    )


def tsc_fails(s: Scratch) -> None:
    """tsc exits 3 with its own stderr: named with that exit code and that stderr."""
    c = copy(s)
    stand_in_tsc(c, "echo 'tsc stand-in: cannot read tsconfig.json' >&2; exit 3")
    named(languages(c), f"{CMD} exited 3; stderr: tsc stand-in: cannot read tsconfig.json")


def tsc_absent(s: Scratch) -> None:
    """No tsc in node_modules nor on PATH: the real pnpm's exit and its message, which it prints
    on stdout."""
    c = copy(s)
    (c.dir / "node_modules").mkdir()
    no_tsc(s, c.dir)
    named(languages(c), f"{CMD} exited 254; stderr: (empty); stdout: ", 'Command "tsc" not found')


def scc_silent(s: Scratch) -> None:
    """Any tool, not only tsc: scc (a stand-in first on PATH) exits 0 printing no JSON, only its
    own stderr: named, that stderr kept through the JSON check (review2 finding 2)."""
    c = copy(s)
    (s.bin / "scc").write_text("#!/bin/sh\necho 'scc: fixture permission denied' >&2\nexit 0\n")
    (s.bin / "scc").chmod(0o755)
    named(
        languages(c),
        "scc --by-file --format json",
        "exited 0 but printed no JSON: stderr: scc: fixture permission denied",
    )


def check_ts_current(s: Scratch) -> None:
    """`just check-ts` on a current node_modules (installed first, as check-tests does) passes and
    leaves its tsc launcher the same file: no install rewrote it under a concurrent reader. One
    small file in tsconfig.json, so tsc and eslint stay cheap."""
    c = Copy(s)
    s.run([tool("pnpm"), "install", "--offline", "--frozen-lockfile"], cwd=c.dir)
    cfg = c.dir / "tsconfig.json"
    text = cfg.read_text()
    assert '"include": ["**/*"]' in text, f"no include in {cfg}"
    cfg.write_text(text.replace('"include": ["**/*"]', '"include": ["eslint.config.js"]'))
    tsc = c.dir / "node_modules" / ".bin" / "tsc"
    before = tsc.stat()
    got = c.check_ts()
    after = tsc.stat()
    assert got.rc == 0, got.out
    assert "ts: ok (1 files: tsc, eslint)" in got.out, got.out
    same = (before.st_ino, before.st_mtime_ns) == (after.st_ino, after.st_mtime_ns)
    assert same, f"check-ts rewrote {tsc} on a current node_modules: {got.out}"


if __name__ == "__main__":
    main(planted, tsc_silent, tsc_fails, tsc_absent, scc_silent, check_ts_current)
