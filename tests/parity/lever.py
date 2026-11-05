#!/usr/bin/env python3
"""The parity lever (#577, #606): a rewritten kit test catches what the test it replaces caught.

  tests/parity/lever.py CASE

CASE is a dir here, tests/parity/CASE/: case.toml names the old test (`old`, a tests/*.sh
path, and `old_at`, a commit holding it, as it is gone from HEAD once parity holds) and the new
one (`new`, a pytest path); each *.patch there is one seeded defect in a kit command, its first
line saying what it breaks. In one scratch copy of the kit's files (tracked, and new ones git
would track), a git repo with the old test restored from old_at, first with no defect, then
with each patch applied in turn (git apply), the lever runs the old test and the new one, each
through the copy's `just test` (the old as its gate item, the new as its file; -x: the first
failure decides), and prints one line per run: the defect, the old result, the new. Exit 0
only when both pass with no defect and both fail on every defect. The caller's GATE_WORKERS
reaches each run. The copy: under the git common dir's octo-feather/, removed after; each
run's output: in the log dir printed last, kept.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

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


def sh(cmd: list[str], cwd: Path, log: Path | None = None) -> int:
    env = {k: v for k, v in os.environ.items() if k not in DROP}
    with (log or Path(os.devnull)).open("w") as f:
        return subprocess.run(
            cmd, cwd=cwd, env=env, stdout=f, stderr=subprocess.STDOUT, check=False
        ).returncode


def copy(dest: Path, old: str, old_at: str) -> None:
    files = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],  # noqa: S607
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout
    for rel in filter(None, files.decode().split("\0")):
        src = ROOT / rel
        if src.is_file() or src.is_symlink():
            (dest / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest / rel, follow_symlinks=False)
    body = subprocess.run(
        ["git", "show", f"{old_at}:{old}"],  # noqa: S607
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout
    (dest / old).write_bytes(body)
    (dest / old).chmod(0o755)
    g = ["git", "-c", "user.name=lever", "-c", "user.email=lever@t", "-c", "commit.gpgsign=false"]
    for a in (["init", "-q"], ["add", "-A"], ["commit", "-qm", "parity copy"]):
        subprocess.run([*g, *a], cwd=dest, capture_output=True, check=True)


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
        sys.stdout.write(__doc__ or "")
        return 0 if len(sys.argv) == 2 else 2
    d = ROOT / "tests" / "parity" / sys.argv[1]
    if not (d / "case.toml").is_file():
        sys.exit(f"lever: no case {sys.argv[1]}: no file {d / 'case.toml'}")
    case = tomllib.loads((d / "case.toml").read_text())
    old, old_at, new = case["old"], case["old_at"], case["new"]
    defects = sorted(d.glob("*.patch"))
    logs = Path(tempfile.mkdtemp(prefix=f"parity-{sys.argv[1]}-"))
    good = True
    # The copy outside /tmp, where the kit itself lives: the qc sandbox makes /tmp private, so a
    # kit under /tmp holding a test's own kit copy under /tmp is a setup the real kit never has.
    common = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],  # noqa: S607
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    (Path(common) / "octo-feather").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="parity-kit-", dir=Path(common) / "octo-feather") as t:
        k = Path(t)
        copy(k, old, old_at)
        for patch in [None, *defects]:
            name = patch.stem if patch else "none"
            if patch and sh(["git", "apply", str(patch)], k):
                sys.exit(
                    f"lever: {patch} does not apply to this kit; remake it against the command "
                    "it breaks"
                )
            want = 1 if patch else 0
            old_rc = sh(
                ["just", "test", "-x", f"tests/gate/test_gate.py::test_script[{old}]"],
                k,
                logs / f"{name}.old.log",
            )
            new_rc = sh(["just", "test", "-x", new], k, logs / f"{name}.new.log")
            said = {0: "pass"}
            line = (
                f"defect: {name}  old: {said.get(old_rc, 'FAIL')} (exit {old_rc})  "
                f"new: {said.get(new_rc, 'FAIL')} (exit {new_rc})"
            )
            if patch:
                line += f"  ({patch.read_text().splitlines()[0]})"
            sys.stdout.write(line + "\n")
            sys.stdout.flush()
            good &= (old_rc == 0) == (want == 0) and (new_rc == 0) == (want == 0)
            subprocess.run(["git", "checkout", "-q", "--", "."], cwd=k, check=True)  # noqa: S607
    sys.stdout.write(
        f"parity {'holds' if good else 'FAILS'}: want both pass with no defect, both fail on "
        f"each; logs: {logs}\n"
    )
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
