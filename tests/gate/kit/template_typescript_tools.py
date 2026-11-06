"""The TypeScript template's check-languages fails closed on a tool's real failure (#663, #548;
owner ruling #548 2026-11-04, #660: no silent failures), through `just check-languages` in the
template's repo (testkit/template.py, its own copy of the run's one package install).

tsc a stand-in at node_modules/.bin/tsc (what `pnpm exec tsc` runs) exiting 0 with empty stdout,
or no tsc at all (the real pnpm prints "Command tsc not found" on stdout, exit 254), eslint a
stand-in crashing (exit 2, its own stderr), scc a stand-in first on PATH printing no JSON, only
its own stderr: each is named with the command, its exit code and what it printed, never a JSON
parse error. The template's check-ts installs nothing, so the kit's install race (#548) has no
counterpart here.
"""

from __future__ import annotations

from testkit import Ran, Scratch, main
from testkit.template import Repo


def stand_in(r: Repo, tool: str, body: str) -> None:
    b = r.dir / "node_modules" / ".bin" / tool
    b.unlink()
    r.write(f"node_modules/.bin/{tool}", f"#!/bin/sh\n{body}\n", mode=0o755)


def languages(r: Repo, *want: str) -> Ran:
    got = r.run("just", "check-languages", want=1)
    for w in want:
        assert w in got.out, f"check-languages does not name {w!r}: {got.out}"
    assert "SyntaxError" not in got.out, f"a bare parse error: {got.out}"
    assert "is not valid JSON" not in got.out, f"a bare parse error: {got.out}"
    return got


def tsc_silent(s: Scratch) -> None:
    r = Repo(s, "typescript")
    stand_in(r, "tsc", "exit 0")
    languages(
        r,
        "ts-files: pnpm exec tsc --showConfig exited 0 but printed no JSON config;"
        " stderr: (empty); stdout: (empty)",
    )


def tsc_absent(s: Scratch) -> None:
    r = Repo(s, "typescript")
    (r.dir / "node_modules" / ".bin" / "tsc").unlink()
    languages(
        r,
        "ts-files: pnpm exec tsc --showConfig exited 254; stderr: (empty); stdout: ",
        'Command "tsc" not found',
    )


def eslint_crash(s: Scratch) -> None:
    r = Repo(s, "typescript")
    stand_in(r, "eslint", "echo 'eslint stand-in: config crashed' >&2; exit 2")
    languages(
        r,
        "eslint-files: pnpm exec eslint --format json . exited 2;"
        " stderr: eslint stand-in: config crashed; stdout: (empty)",
    )


def scc_silent(s: Scratch) -> None:
    r = Repo(s, "typescript")
    (s.bin / "scc").write_text("#!/bin/sh\necho 'scc: fixture permission denied' >&2\nexit 0\n")
    (s.bin / "scc").chmod(0o755)
    languages(
        r,
        "scc --by-file --format json",
        "exited 0 but printed no JSON: stderr: scc: fixture permission denied",
    )


if __name__ == "__main__":
    main(tsc_silent, tsc_absent, eslint_crash, scc_silent)
