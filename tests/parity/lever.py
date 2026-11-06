#!/usr/bin/env python3
"""The parity lever (#577, #606): a rewritten kit test catches what the test it replaces caught.

  tests/parity/lever.py CASE

CASE is a dir here, tests/parity/CASE/: case.toml names the old test (`old`, a tests/*.sh
path, and `old_at`, a commit holding it, as it is gone from HEAD once parity holds), every
file under tests/ the old test needs at old_at (`needs`: the libraries it sources, the fixtures
and helpers it runs or reads; a dir stands for every file under it), and the new test (`new`,
a pytest path); each *.patch there is one seeded defect in a kit command, its first line saying
what it breaks. In one scratch copy of the kit's files (tracked, and new ones git would track),
a git repo, first with no defect, then with each patch applied in turn (git apply), the lever
runs the old test with the old test and its `needs` restored from old_at, then the new one on
the kit's own files, each through the copy's `just test` (the old as its gate item, the new as
its file; -x: the first failure decides; -rA: every item's output in its log), and prints one
line per run: the defect, the old result, the new, and the old side's evidence. Exit 0 only
when both pass with no defect and both fail on every defect.

Refused before any run (exit 2): a `needs` entry old_at does not hold, and a file the old test
or a shell file it sources names under tests/ (`source "$(dirname ...)/F"`, `$kit/tests/F`) that
the restored copy lacks or holds at another content than old_at's while `needs` omits it: the
copy would run the old test without what it ran with. Refused after a run (exit 2): an old run
whose log does not show the old item's own output, or shows bash failing to find a file or a
command in the old test or a file it sources (`F: line N: X: No such file or directory` or
`... command not found`, bash's own words on stderr, which -rA keeps for a passing item too).
A test whose `source` failed carries on without its library and can still print its pass line
and exit 0; it cannot run without bash saying so, so such a run is no evidence.

The caller's GATE_WORKERS reaches each run. The copy: under the git common dir's
octo-feather/, removed after; each run's output: in the log dir printed last, kept.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import NoReturn

import tomllib

ROOT = Path(__file__).resolve().parents[2]
DROP = (
    "GATE_NESTED",
    "GATE_ITEM",
    "COV_MAP_DIR",
    "COVERAGE_PROCESS_START",
    "OCTO_FEATHER_CHECK_RUN",
    "OCTO_FEATHER_QC_CLAIMS",
    "OCTO_FEATHER_QC_CAPTURE_DIR",
)
# What an old test names under tests/: a sourced file beside it, a kit path.
SOURCED = re.compile(
    r'^\s*(?:source|\.)\s+"\$\(dirname "\$(?:0|\{BASH_SOURCE\[0\]\})"\)/([^"]+)"', re.MULTILINE
)
KIT_PATH = re.compile(r'\$\{?kit\}?"?/(tests/[A-Za-z0-9_./-]+)')


class RefusedError(Exception):
    """A run the lever refuses: its message says what is missing."""


def refuse(msg: str) -> NoReturn:
    raise RefusedError(msg)


def git(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, check=False)  # noqa: S607


def at(rev: str, path: str) -> bytes | None:
    """PATH's content at REV, None when REV holds no such file."""
    p = git("show", f"{rev}:{path}")
    return p.stdout if p.returncode == 0 else None


def sh(cmd: list[str], cwd: Path, log: Path | None = None) -> int:
    env = {k: v for k, v in os.environ.items() if k not in DROP}
    with (log or Path(os.devnull)).open("w") as f:
        return subprocess.run(
            cmd, cwd=cwd, env=env, stdout=f, stderr=subprocess.STDOUT, check=False
        ).returncode


def copy(dest: Path) -> None:
    files = git("ls-files", "-z", "--cached", "--others", "--exclude-standard").stdout
    for rel in filter(None, files.decode().split("\0")):
        src = ROOT / rel
        if src.is_file() or src.is_symlink():
            (dest / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest / rel, follow_symlinks=False)
    g = ["git", "-c", "user.name=lever", "-c", "user.email=lever@t", "-c", "commit.gpgsign=false"]
    for a in (["init", "-q"], ["add", "-A"], ["commit", "-qm", "parity copy"]):
        subprocess.run([*g, *a], cwd=dest, capture_output=True, check=True)


def old_files(old: str, old_at: str, needs: list[str]) -> dict[str, bytes]:
    """The old test and each file of NEEDS (a dir: every file under it) at OLD_AT, by path;
    refused when OLD_AT lacks one."""
    out: dict[str, bytes] = {}
    for n in [old, *needs]:
        listed = git("ls-tree", "-r", "--name-only", old_at, "--", n).stdout.decode().split()
        if not listed:
            refuse(
                f"{n} is not at {old_at}: drop it from needs, or set old_at to a commit holding it"
            )
        for p in listed:
            body = at(old_at, p)
            assert body is not None, p
            out[p] = body
    return out


def referenced(old: str, files: dict[str, bytes]) -> list[str]:
    """Every path under tests/ the old test, or a shell file it sources, names (SOURCED,
    KIT_PATH), followed through each sourced file held in FILES."""
    out: set[str] = set()
    todo, seen = [old], set[str]()
    while todo:
        f = todo.pop()
        if f in seen:
            continue
        seen.add(f)
        text = files[f].decode(errors="replace") if f in files else ""
        refs = [os.path.normpath(str(Path(f).parent / s)) for s in SOURCED.findall(text)]
        todo += refs
        out |= {*refs, *(p.rstrip("./") for p in KIT_PATH.findall(text))}
    return sorted(out)


def unrestored(old: str, old_at: str, files: dict[str, bytes], copy_dir: Path) -> list[str]:
    """Each path referenced() names that FILES does not restore and the copy lacks, or holds at
    another content than OLD_AT's."""
    bad: list[str] = []
    for r in referenced(old, files):
        if r in files or any(k.startswith(r + "/") for k in files):
            continue
        here, then = copy_dir / r, at(old_at, r)
        if not here.exists():
            bad.append(f"{r}: missing")
        elif here.is_file() and then is not None and then != here.read_bytes():
            bad.append(f"{r}: differs from {old_at}")
    return bad


def evidence(log: Path, old: str, shells: list[str]) -> str:
    """The old run's evidence from its -rA log: its last line of output; refused when the log
    shows none, or bash failing to find a file or command in OLD or SHELLS."""
    text = log.read_text(errors="replace")
    names = "|".join(re.escape(s) for s in [old, *shells])
    m = re.search(
        rf"^(?:\S*/)?(?:{names}): line \d+: .*(?:No such file or directory|command not found)$",
        text,
        re.MULTILINE,
    )
    if m:
        refuse(f"the old test did not run its behaviour: {m.group(0)} (log {log})")
    item = re.escape(f"test_script[{old}]")
    sec = re.search(
        rf"^_+ {item} _+\n(.*?)(?=^_{{5,}} |^={{5,}} |\Z)", text, re.MULTILINE | re.DOTALL
    )
    lines = [
        ln for ln in (sec.group(1).splitlines() if sec else []) if ln and not ln.startswith("---")
    ]
    if not lines:
        refuse(f"the old test shows no output of its own in its log {log}: no evidence it ran")
    return lines[-1][:160]


def reset(k: Path) -> None:
    """The copy back at its commit: a patch and every restored file gone."""
    subprocess.run(["git", "checkout", "-q", "--", "."], cwd=k, check=True)  # noqa: S607
    subprocess.run(["git", "clean", "-qfd"], cwd=k, check=True)  # noqa: S607


def apply(k: Path, patch: Path | None) -> None:
    if patch and sh(["git", "apply", str(patch)], k):
        sys.exit(
            f"lever: {patch} does not apply to this kit; remake it against the command it breaks"
        )


def run(
    k: Path, logs: Path, case: dict[str, str], files: dict[str, bytes], patch: Path | None
) -> bool:
    """One defect (PATCH, None: no defect): the old test with FILES restored, then the new on the
    kit's own files; its line printed; whether both gave the result the defect wants."""
    name, old = patch.stem if patch else "none", case["old"]
    apply(k, patch)
    for p, body in files.items():
        (k / p).parent.mkdir(parents=True, exist_ok=True)
        (k / p).write_bytes(body)
    (k / old).chmod(0o755)
    old_log = logs / f"{name}.old.log"
    item = f"tests/gate/test_gate.py::test_script[{old}]"
    old_rc = sh(["just", "test", "-x", "-rA", item], k, old_log)
    reset(k)
    shells = sorted(p for p in files if p != old and p.endswith(".sh"))
    ran = evidence(old_log, old, shells)
    apply(k, patch)
    new_rc = sh(["just", "test", "-x", "-rA", case["new"]], k, logs / f"{name}.new.log")
    reset(k)
    said = {0: "pass"}
    line = (
        f"defect: {name}  old: {said.get(old_rc, 'FAIL')} (exit {old_rc})  "
        f"new: {said.get(new_rc, 'FAIL')} (exit {new_rc})"
    )
    if patch:
        line += f"  ({patch.read_text().splitlines()[0]})"
    sys.stdout.write(f"{line}\n  old ran: {ran}\n")
    sys.stdout.flush()
    want = 1 if patch else 0
    return (old_rc == 0) == (want == 0) and (new_rc == 0) == (want == 0)


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
        sys.stdout.write(__doc__ or "")
        return 0 if len(sys.argv) == 2 else 2
    d = ROOT / "tests" / "parity" / sys.argv[1]
    if not (d / "case.toml").is_file():
        sys.exit(f"lever: no case {sys.argv[1]}: no file {d / 'case.toml'}")
    case = tomllib.loads((d / "case.toml").read_text())
    old, old_at = case["old"], case["old_at"]
    logs = Path(tempfile.mkdtemp(prefix=f"parity-{sys.argv[1]}-"))
    good = True
    # The copy outside /tmp, where the kit itself lives: the qc sandbox makes /tmp private, so a
    # kit under /tmp holding a test's own kit copy under /tmp is a setup the real kit never has.
    common = git("rev-parse", "--path-format=absolute", "--git-common-dir").stdout.decode().strip()
    (Path(common) / "octo-feather").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="parity-kit-", dir=Path(common) / "octo-feather") as t:
        k = Path(t)
        try:
            files = old_files(old, old_at, case.get("needs", []))
            copy(k)
            if bad := unrestored(old, old_at, files, k):
                refuse(f"needs in {d / 'case.toml'} omits what {old} runs with: {'; '.join(bad)}")
            sys.stdout.write(f"restored from {old_at}: {' '.join(sorted(files))}\n")
            for patch in [None, *sorted(d.glob("*.patch"))]:
                good &= run(k, logs, case, files, patch)
        except RefusedError as e:
            sys.stderr.write(f"lever: refused: {e}\n")
            return 2
    sys.stdout.write(
        f"parity {'holds' if good else 'FAILS'}: want both pass with no defect, both fail on "
        f"each; logs: {logs}\n"
    )
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
