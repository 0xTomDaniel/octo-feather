"""The scenarios of tests/gate/kit/test_check_ts.py (its items), this file their command
(testkit.main): `just check-ts` (#245) in a throwaway copy of the kit's tracked files, offline
from the kit's pnpm store (CI's pnpm step fills it; one store, owner ruling #422).

An empty pnpm store fails naming the fetch command, never reaching the network (--offline); the
kit's package.json and lockfile in a dir on another filesystem than the kit's (/dev/shm, a tmpfs,
where the box has one; else TMPDIR) install offline from the kit's store; a type error and a
lint violation added to an extension fail naming each file and line; eslint's baseline only
shrinks: one more `any` in extensions/spend-ledger.ts fails naming its line, and, alone, a fixed
violation leaves an unused suppression that fails naming --prune-suppressions. The clean copy
passing is the kit gate's own check-ts item (tests/gate/test_gate.py, test_recipe): each failing
case names its own lines, so none passes on a copy broken some other way. Each run lints the
kit's TypeScript with typed eslint, the cost floor: two such runs, as eslint reports unused
suppressions only in a run with no other finding.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from testkit import FIXTURES, ROOT, Ran, Scratch, main, tool_homes
from testkit.template import uncoloured

EXT = "extensions/resume-on-error.ts"
LEDGER = "extensions/spend-ledger.ts"


def tool(name: str) -> str:
    """NAME's path on PATH; a missing tool fails naming it."""
    path = shutil.which(name)
    assert path, f"{name} is not on PATH"
    return path


class Copy:
    """The kit's tracked files under SCRATCH/kit, the kit's pnpm store named for every command."""

    def __init__(self, s: Scratch) -> None:
        self.s = s
        self.dir = s.root / "kit"
        self.dir.mkdir()
        files = subprocess.run(
            [tool("git"), "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True
        ).stdout
        tar = subprocess.run(  # a tracked file deleted in the worktree is skipped
            [tool("tar"), "-cf", "-", "--null", "--ignore-failed-read", "-T", "-"],
            cwd=ROOT,
            input=files,
            capture_output=True,
            check=False,
        ).stdout
        subprocess.run([tool("tar"), "-xf", "-"], cwd=self.dir, input=tar, check=True)
        self.store = subprocess.run(  # the caller's HOME finds it, never the scratch HOME
            [tool("pnpm"), "store", "path"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
        s.env |= tool_homes() | {"npm_config_store_dir": self.store}
        uncoloured(s)  # eslint's stylish rows and tsc's lines read here

    def check_ts(self, **env: str) -> Ran:
        p = subprocess.run(
            [tool("just"), "check-ts"],
            cwd=self.dir,
            env={**self.s.env, **env},
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        return Ran(p.returncode, p.stdout, "")

    def append(self, rel: str, text: str) -> int:
        """TEXT appended to REL; the line number of its last line."""
        p = self.dir / rel
        p.write_text(p.read_text() + text)
        return len(p.read_text().splitlines())


def named(c: Copy, out: str, rel: str, line: int) -> None:
    """eslint named LINE of REL for no-explicit-any (the parse: tests/fixtures/check-ts)."""
    p = subprocess.run(
        [
            sys.executable,
            str(FIXTURES / "check-ts" / "eslint_names.py"),
            str(c.dir / rel),
            str(line),
            "@typescript-eslint/no-explicit-any",
        ],
        input=out,
        text=True,
        check=False,
    )
    assert p.returncode == 0, f"eslint did not name line {line} of {rel}: {out}"


def empty_store(s: Scratch) -> None:
    c = Copy(s)
    got = c.check_ts(npm_config_store_dir=str(s.root / "store"))
    assert got.rc != 0, f"passed with an empty pnpm store: {got.out}"
    want = f"fetch them once, with network: pnpm install --frozen-lockfile --dir {c.dir}"
    assert want in got.out, got.out


def other_fs(s: Scratch) -> None:
    """A dir on another filesystem than the kit's installs offline from the kit's store (pnpm
    keeps a store per filesystem: unnamed, a tmpfs copy would install from an empty one)."""
    c = Copy(s)
    fs = tempfile.gettempdir()
    shm = Path("/dev/shm")  # noqa: S108 (the tmpfs probed, never written by name)
    if shm.is_dir() and shm.stat().st_dev != ROOT.stat().st_dev:
        fs = str(shm)
    with tempfile.TemporaryDirectory(prefix="check-ts.", dir=fs) as x:
        for f in ("package.json", "pnpm-lock.yaml"):
            (Path(x) / f).write_bytes((c.dir / f).read_bytes())
        # The kit's pnpm (its mise.toml), as that dir has no mise.toml of its own.
        pnpm = s.run(
            [tool("mise"), "which", "pnpm"],
            cwd=c.dir,
            env={"MISE_TRUSTED_CONFIG_PATHS": str(c.dir)},
        ).out
        s.run([pnpm, "install", "--offline", "--frozen-lockfile"], cwd=Path(x))


def findings(s: Scratch) -> None:
    """A type error and a lint violation in the extension, and one more `any` in baselined
    spend-ledger.ts: one run names each by file and line."""
    c = Copy(s)
    n = c.append(EXT, 'export const typeProbe: number = "x";\n')
    c.append(EXT, "export function lintProbe(x: any): unknown { return x; }\n")
    m = c.append(LEDGER, "export function probe(x: any): unknown { return x; }\n")
    got = c.check_ts()
    assert got.rc != 0, f"a type error and lint violations passed: {got.out}"
    for want in (f"{EXT}({n},14): error TS2322", "check-ts: fix each tsc error above"):
        assert want in got.out, got.out
    named(c, got.out, EXT, n + 1)
    named(c, got.out, LEDGER, m)


def unused_suppression(s: Scratch) -> None:
    """Only an unused suppression (a fixed violation in the fixture): fails naming
    --prune-suppressions."""
    c = Copy(s)
    f = c.dir / "tests" / "fixtures" / "spend-ledger" / "nested-tool.ts"
    text = f.read_text()
    assert "    async execute() {" in text, f"no async execute() in {f}"
    f.write_text(text.replace("    async execute() {", "    execute() {"))
    got = c.check_ts()
    assert got.rc != 0, f"an unused suppression passed: {got.out}"
    for want in ("There are suppressions left that do not occur anymore", "--prune-suppressions"):
        assert want in got.out, got.out


if __name__ == "__main__":
    main(empty_store, other_fs, findings, unused_suppression)
