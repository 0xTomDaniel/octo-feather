"""The scenarios of tests/gate/kit/test_check_ts.py (its items), this file their command
(testkit.main): `just check-ts` (#245) in a throwaway copy of the kit's tracked files, offline
from the kit's pnpm store (CI's pnpm step fills it; one store, owner ruling #422).

An empty pnpm store fails naming the fetch command, never reaching the network (--offline); the
kit's package.json and lockfile in a dir on another filesystem than the kit's (/dev/shm, a tmpfs,
where the box has one; else TMPDIR) install offline from the kit's store; a type error and a
lint violation added to an extension fail naming each file and line; eslint's baseline only
shrinks: one more `any` in extensions/spend-ledger.ts fails naming its line, and, alone, a fixed
violation leaves an unused suppression that fails naming --prune-suppressions. The clean copy
passing is the kit gate's own check-ts item (tests/gate/test_gate.py, test_recipe), which runs it
on every file tsconfig.json lists: each failing case names its own lines, so none passes on a copy
broken some other way. Each failing case's copy has tsconfig.json's include cut to the files it
plants in (Copy.only, testkit/kit_copy.py; its data, as check-ts reads its file list from
tsconfig.json): typed eslint and tsc over the whole kit are the cost floor (#686), and every
assertion is about those files.
Two runs, as eslint reports unused suppressions only in a run with no other finding.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from testkit import FIXTURES, ROOT, Scratch, main
from testkit.kit_copy import Copy, tool

EXT = "extensions/resume-on-error.ts"
LEDGER = "extensions/spend-ledger.ts"


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
        for f in ("package.json", "pnpm-lock.yaml", "pnpm-workspace.yaml"):
            (Path(x) / f).write_bytes((c.dir / f).read_bytes())
        shutil.copytree(c.dir / "patches", Path(x) / "patches")
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
    c.only(EXT, LEDGER)
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
    rel = "tests/fixtures/spend-ledger/nested-tool.ts"
    c.only(rel)
    f = c.dir / rel
    text = f.read_text()
    assert "    async execute() {" in text, f"no async execute() in {f}"
    f.write_text(text.replace("    async execute() {", "    execute() {"))
    got = c.check_ts()
    assert got.rc != 0, f"an unused suppression passed: {got.out}"
    for want in ("There are suppressions left that do not occur anymore", "--prune-suppressions"):
        assert want in got.out, got.out


if __name__ == "__main__":
    main(empty_store, other_fs, findings, unused_suppression)
