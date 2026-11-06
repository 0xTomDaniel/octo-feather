"""check-languages fails closed on tsc's real failure, and the gate's race on node_modules is gone
(#663, #548; owner ruling #548 2026-11-04, #660: no silent failures), through `just
check-languages` and `just check-ts` in a throwaway copy of the kit's tracked files, offline from
the kit's uv environment and pnpm store.

tsc a stand-in at node_modules/.bin/tsc (what `pnpm exec tsc` runs): exiting 0 with empty stdout,
or failing with its own stderr, check-languages names the command, its exit code and what it
printed, never a JSON parse error; so for any tool it asks (scc printing nothing). No tsc in
node_modules at all (the state a concurrent pnpm install leaves for a moment: it unlinks and
rewrites node_modules/.bin/tsc, #548), the real pnpm's exit and its stdout message are named.
And `just check-ts` on a current node_modules writes nothing there: its tsc launcher is the same
file after the run, so a check-languages running beside it (the gate runs both at once, after
check-tests installed) always finds tsc.
"""

from __future__ import annotations

from check_ts import Copy, tool
from testkit import ROOT, Ran, Scratch, main

CMD = "pnpm exec tsc --showConfig"


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
    """No tsc in node_modules: the real pnpm's exit and its message, which it prints on stdout."""
    c = copy(s)
    (c.dir / "node_modules").mkdir()
    named(languages(c), f"{CMD} exited 254; stderr: (empty); stdout: ", 'Command "tsc" not found')


def scc_silent(s: Scratch) -> None:
    """Any tool, not only tsc: scc (a stand-in first on PATH) exits 0 printing nothing: named."""
    c = copy(s)
    (s.bin / "scc").write_text("#!/bin/sh\nexit 0\n")
    (s.bin / "scc").chmod(0o755)
    named(
        languages(c),
        "scc --by-file --format json",
        "exited 0 but printed no JSON",
        "stderr: (empty)",
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
    main(tsc_silent, tsc_fails, tsc_absent, scc_silent, check_ts_current)
