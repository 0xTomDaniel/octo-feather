#!/usr/bin/env python3
"""The parity lever (#577, #606): a rewritten kit test catches what the test it replaces caught.

  tests/parity/lever.py [--background] CASE

CASE is a dir here, tests/parity/CASE/: case.toml names the old test (`old`, a tests/*.sh
path or a pytest item id PATH::ITEM, and `old_at`, a commit holding it, as it is gone from HEAD
once parity holds; for an item, PATH is restored from old_at and the item run), every
file under tests/ the old test needs at old_at (`needs`: the libraries it sources, the fixtures
and helpers it runs or reads; a dir stands for every file under it), the new test (`new`, a
pytest path), and how the old run shows it ran each file a defect patches (`ran`, file: fact);
each *.patch there is one seeded defect in a kit command, its first line saying what it breaks.
In one scratch copy of the kit's files (tracked, and new ones git would track), a git repo
holding the kit's history too (fetched, refs/kit/head: a commit a kit file names resolves),
first with no defect, then with each patch applied in turn (git apply), the lever runs the old
test with it and its `needs` restored from old_at, then the new one on the kit's own files,
each through the copy's `just test` (the old as its gate item or its pytest id, the new as its
file; -x: the first failure decides; -rA: every item's output in its log), and prints one line
per run: the defect, the old result, the new. Exit 0 only when both pass with no defect and
both fail on every defect.

The old side must have run what it covers, each an exact fact; the lever refuses the case
(exit 2), naming which does not hold:
  (a) on the clean tree the old run ran every file a defect patches, by its `ran` fact:
      coverage           coverage.py measured it in the old item's processes: the clean old
                         run goes under just fast-map's configuration (COVERAGE_PROCESS_START
                         tests/gate/coverage.toml, COV_MAP_DIR, the item's GATE_ITEM dir) and
                         `octo-feather-gate map` names the files; for a Python file the kit
                         venv runs. Only a case with a coverage fact is measured: coverage.py
                         fails at exit in a process that cannot write its data file (one in
                         the qc sandbox, where only overlays are writable), so a case whose
                         old test starts that sandbox uses exec facts
      exec SUFFIX        a process of the old run (strace -ff, execve) ran a file whose path
                         ends in SUFFIX as its program, or as the script its interpreter
                         (python, node) was given first: a file outside the kit venv, which
                         coverage.py does not see
      open SUFFIX        a process of the old run opened a file whose path ends in SUFFIX
                         (openat): a module loaded, never run as a program
      run PROGRAM ARG    a process of the old run ran PROGRAM with ARG among its arguments: a
                         file no process executes, read by PROGRAM to run ARG (a justfile)
  (b) the old test failed on at least one seeded defect.
A defect patching a file `ran` does not name, a `needs` entry old_at lacks, and a trace fact
without strace on PATH are refused too. Notes, never a verdict: a file under tests/ the old
test or a shell file it sources names that the restored copy lacks or holds at another content
(`source "$(dirname ...)/F"`, `$kit/tests/F`), and, beside a refusal of (a), bash's own "F:
line N: X: No such file or directory" or "... command not found" from the old test or a shell
file it sources (a failed `source` lets a test carry on without its library, print its pass
line and exit 0).

Restoring (#1361, #953): the old test and every file of its `needs` come out of old_at by git
itself (`git checkout OLD_AT -- PATH...` in the copy, which holds old_at through refs/kit/head),
never as blob bytes written by the lever, so each keeps the mode and the link git holds there: an
executable stand-in stays executable, a symlink stays a symlink to its target. Each restored path
is then checked on disk against old_at's tree (mode 100755 executable, 100644 not, 120000 a
symlink); one git cannot reproduce faithfully (a submodule, mode 160000, or a checkout that lands
another kind) is refused, naming it.

No network (#1343, owner ruling 2026-11-28): every old and new run goes through bubblewrap
(`bwrap --dev-bind / / --unshare-net`, the tool the qc sandbox's srt drives for its network
namespace): the same files and user, in a network namespace of its own holding only its own
loopback, so no route out exists (a test reaching for a host, a proxy or a server on the
caller's loopback fails to connect); uv runs offline from its cache, and mise and just from their
installs, as the gate always does. Without a working bwrap the lever refuses to run at all.

Re-anchoring (#1154): when scripts/check-parity names a case's patch, the change that moved its
code remakes that patch against the code as it now is, seeding the same defect (and points the
case's `ran` at the file it now patches), then runs `tests/parity/lever.py CASE` to exit 0; a
case whose target behaviour is gone is deleted in the same change. A case retires when the
behaviour or the input contract its old test relies on was changed on purpose, naming that change
(commit and PR) in the change that retires it; no one-sided case is kept, and no old side mixes
commits.

The CPU budget (quality spec #acceptance-test-cpu-budget): before each run the lever commits what
the run adds (the restored files, the defect) on the copy's own branch, so the copy's default
branch holds them and the gate judges no item of the run as changed (what counts as changed:
`octo-feather-gate --help`, changed): no test the lever runs there is held to the budget. Only
the lever's own copy is so committed; a real gate run reads no new variable, flag or option and
still judges every changed item.

Background (--background, #1368; owner ruling 2026-11-28 #1343, director's terms #1343
issuecomment-7240021242): for a pass running the lever beside lanes' work (the parity survey, the
weekly parity pass). The lever and every run it starts go at the lowest priority (nice 19,
ionice's idle class), single-process (GATE_WORKERS 0: the copy's `just test` runs pytest -n 0, no
xdist worker), and take no fast-run turn (tests/gate/heavy_slot.py, fast_runs), so no lane's
`just fast` waits behind them: the lever writes its own run record, lever-PID.run.json (pid, cwd,
since, case), in the box's slots dir (${XDG_STATE_HOME:-~/.local/state}/octo-feather/slots,
octo-feather-slot --help, Files), removed when it ends, and a fast-tier run started under it is
nested by heavy_slot.py's own rule (an ancestor's record there) and takes none. The record is in
the slots dir every run's is, so the run stays visible to the slot's records; only the lever's own
runs descend from it, and a real gate run reads no new variable, flag or option. The fast-run cap
guards memory (five fast runs at once got earlyoom kills on this 15 GiB box, lane gh1186), so
before the case starts the lever reads the box's available memory (/proc/meminfo MemAvailable)
and waits while it is under the floor, 3 GiB, printing its check, and each wait's start, end and
the memory seen (read every 5 s). The floor: a whole background run's peak memory, measured as
its own cgroup's memory.peak (page cache included) from a scope round it (`systemd-run --user
--scope -p MemoryAccounting=yes -- tests/parity/lever.py --background CASE`, the scope's
memory.peak read as the lever exits; 2026-11-28, this box): 540 MiB for check-ts (tsc and eslint,
the box's heaviest tools), 236 MiB for lane-correction-counts. Once such a run takes its peak, a
3 GiB start leaves about 2.4 GiB available, three times the line where this box's earlyoom starts
killing (-m 5: 5% of 15.6 GiB, 0.8 GiB), the margin covering what others start while it runs, as
the floor is read only at the start. An old test marked e2e is no fast-tier run and still asks the
heavy slot (heavy_slot.py).

The caller's GATE_WORKERS reaches each run (but under --background). The copy: under the git
common dir's octo-feather/, removed after, as is the runs' own mise state dir (the caller's is
never written); each run's output: in the log dir printed last, kept.
"""

import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn, cast

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
# Git with the copy's commit identity; COPY: the copy's first commit, every run's start.
GIT = ["git", "-c", "user.name=lever", "-c", "user.email=lever@t", "-c", "commit.gpgsign=false"]
COPY = "refs/lever/copy"
# Every old and new run's prefix: the same files, in a network namespace of its own (--help).
OFFLINE = ["bwrap", "--dev-bind", "/", "/", "--unshare-net", "--die-with-parent", "--"]
# What an old test names under tests/: a sourced file beside it, a kit path.
SOURCED = re.compile(
    r'^\s*(?:source|\.)\s+"\$\(dirname "\$(?:0|\{BASH_SOURCE\[0\]\})"\)/([^"]+)"', re.MULTILINE
)
KIT_PATH = re.compile(r'\$\{?kit\}?"?/(tests/[A-Za-z0-9_./-]+)')
# --background (--help, Background): the switch, the memory floor (GiB) and how often a wait reads.
BACKGROUND = "--background"
FLOOR_GIB = 3
POLL_SECONDS = 5


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


def sh(
    cmd: list[str], cwd: Path, log: Path | None = None, add: dict[str, str] | None = None
) -> int:
    env = {k: v for k, v in os.environ.items() if k not in DROP} | (add or {})
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
    for a in (["init", "-q"], ["add", "-A"], ["commit", "-qm", "parity copy"]):
        subprocess.run([*GIT, *a], cwd=dest, capture_output=True, check=True)
    subprocess.run([*GIT, "update-ref", COPY, "HEAD"], cwd=dest, capture_output=True, check=True)
    # The kit's history, its objects copied into the copy's own .git (no link into the kit's), so a
    # commit a kit file names resolves there: check-evals' history fixtures (repo kit, #1204).
    fetch = ["fetch", "-q", "--no-tags", str(ROOT), "+HEAD:refs/kit/head"]
    subprocess.run([*GIT, *fetch], cwd=dest, capture_output=True, check=True)


def lowest() -> None:
    """The lever, and every process it starts, at the lowest processor and disk priority; its
    runs single-process (--help, Background)."""
    os.setpriority(os.PRIO_PROCESS, 0, 19)
    subprocess.run(["ionice", "-c", "3", "-p", str(os.getpid())], check=True)  # noqa: S607
    os.environ["GATE_WORKERS"] = "0"
    sys.stdout.write("lever: background: nice 19, idle IO, GATE_WORKERS 0, no fast-run turn\n")


def available() -> float:
    """The box's MemAvailable (/proc/meminfo), in GiB."""
    m = re.search(r"^MemAvailable:\s+(\d+) kB$", Path("/proc/meminfo").read_text(), re.MULTILINE)
    if m is None:
        refuse("/proc/meminfo has no MemAvailable: the memory floor cannot be read")
    return int(m[1]) / 2**20


def memory_floor() -> None:
    """Waited while MemAvailable is under FLOOR_GIB, the check and each wait printed."""
    seen = available()
    floor = f"the floor {FLOOR_GIB} GiB"
    if seen >= FLOOR_GIB:
        sys.stdout.write(f"lever: memory: MemAvailable {seen:.1f} GiB, {floor}: no wait\n")
        sys.stdout.flush()
        return
    start, since = time.monotonic(), time.strftime("%Y-%m-%dT%H:%M:%S%z")
    sys.stdout.write(
        f"lever: memory: waiting from {since}: MemAvailable {seen:.1f} GiB, under {floor}\n"
    )
    sys.stdout.flush()
    while seen < FLOOR_GIB:
        time.sleep(POLL_SECONDS)
        seen = available()
    sys.stdout.write(
        f"lever: memory: wait ended {time.strftime('%Y-%m-%dT%H:%M:%S%z')} after "
        f"{time.monotonic() - start:.0f} s: MemAvailable {seen:.1f} GiB, {floor}\n"
    )
    sys.stdout.flush()


def turnless(name: str) -> Path | None:
    """The lever's run record in the box's slots dir: a fast-tier run under it takes no fast-run
    turn (--help, Background). None where the dir cannot be made or written: heavy_slot.py takes no
    turn there either."""
    state = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state")
    rec = state / "octo-feather" / "slots" / f"lever-{os.getpid()}.run.json"
    since = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    run = {"pid": os.getpid(), "cwd": str(Path.cwd()), "since": since, "case": name}
    try:
        rec.parent.mkdir(parents=True, exist_ok=True)
        rec.write_text(json.dumps(run))
    except OSError:
        return None
    return rec


def offline() -> None:
    """Refused unless OFFLINE starts a command here: no run goes with the caller's network."""
    p = subprocess.run([*OFFLINE, "true"], capture_output=True, check=False)
    if p.returncode:
        refuse(f"bwrap cannot give a run a network of its own here: {p.stderr.decode().strip()}")


def old_files(old: str, old_at: str, needs: list[str]) -> dict[str, bytes]:
    """The old test and each file of NEEDS (a dir: every file under it) at OLD_AT, by path;
    refused when OLD_AT lacks one, or holds a submodule there (git restores none faithfully)."""
    out: dict[str, bytes] = {}
    for n in [old.partition("::")[0], *needs]:
        tree = git("ls-tree", "-r", "-z", old_at, "--", n).stdout.decode().split("\0")
        rows = [t.partition("\t") for t in filter(None, tree)]
        if not rows:
            refuse(
                f"{n} is not at {old_at}: drop it from needs, or set old_at to a commit holding it"
            )
        if subs := [p for m, _, p in rows if m.startswith("160000")]:
            refuse(f"{', '.join(subs)} at {old_at}: a submodule, which git restores as no file")
        listed = [p for _, _, p in rows]
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


def bash_errors(log: Path, old: str, shells: list[str]) -> list[str]:
    """Bash's own "F: line N: X: No such file or directory" or "... command not found" lines in
    LOG, F the old test or a shell file it sources: a note beside a refusal, never a verdict."""
    names = "|".join(re.escape(s) for s in [old, *shells])
    pat = rf"^(?:\S*/)?(?:{names}): line \d+: .*(?:No such file or directory|command not found)$"
    return re.findall(pat, log.read_text(errors="replace"), re.MULTILINE)


# A traced exec or open (strace -ff): execve("PROG", ["ARGV0", ...], ...) = 0, or
# openat(DIR, "PATH", ...) = FD.
EXECVE = re.compile(r'^execve\("((?:[^"\\]|\\.)*)", \[(.*?)\], .*\) = 0$', re.MULTILINE)
OPENAT = re.compile(r'^openat\([^,]+, "((?:[^"\\]|\\.)*)", .*\) = \d+$', re.MULTILINE)
ARG = re.compile(r'"((?:[^"\\]|\\.)*)"')
INTERPRETER = re.compile(r"^(?:python[0-9.]*|node)$")


class Trace:
    """What the old run's processes executed and opened (strace -ff files under DIR)."""

    def __init__(self, d: Path) -> None:
        self.execs: list[tuple[str, list[str]]] = []
        self.opened: list[str] = []
        for f in d.iterdir():
            text = f.read_text(errors="replace")
            self.execs += [(m[1], ARG.findall(m[2])) for m in EXECVE.finditer(text)]
            self.opened += [m[1] for m in OPENAT.finditer(text)]

    def executed(self, suffix: str) -> bool:
        """A process ran the file at SUFFIX: as the program, or as the script its interpreter
        (python, node) was given first."""

        def at(p: str) -> bool:
            return p == suffix or p.endswith("/" + suffix)

        return any(
            at(prog) or (len(argv) > 1 and INTERPRETER.match(Path(argv[0]).name) and at(argv[1]))
            for prog, argv in self.execs
        )

    def ran(self, program: str, arg: str) -> bool:
        """A process ran PROGRAM with ARG among its arguments."""
        return any(Path(p).name == program and arg in argv[1:] for p, argv in self.execs)

    def opens(self, suffix: str) -> bool:
        return any(p.endswith("/" + suffix) for p in self.opened)


def covered(k: Path, cov: Path, junit: Path, old: str) -> set[str]:
    """The kit files coverage.py measured in the old item's processes: the coverage map the
    kit's own `octo-feather-gate map` builds from the run's data (just fast-map's mechanism)."""
    gate = [
        "uv",
        "run",
        "--locked",
        "--offline",
        "--no-sync",
        "python3",
        "scripts/octo-feather-gate",
    ]
    sh([*gate, "map", str(cov), "--junit", str(junit)], k, cov / "map.log")
    common = git("rev-parse", "--path-format=absolute", "--git-common-dir", cwd=k)
    head = git("rev-parse", "HEAD", cwd=k).stdout.decode().strip()
    m = Path(common.stdout.decode().strip()) / "octo-feather" / "fast-map" / f"{head}.json"
    items: dict[str, list[str]] = json.loads(m.read_text())["items"] if m.is_file() else {}
    return set(items.get(old, []))


def facts(case: dict[str, object], defects: list[Path]) -> dict[str, str]:
    """Each file the case's defects patch and how the old run shows it ran it (`ran` in
    case.toml: `coverage`, `exec SUFFIX`, `open SUFFIX` or `run PROGRAM ARG`); refused when a
    patched file has none, or its form is not one of these."""
    ran = cast("dict[str, str]", case.get("ran", {}))
    out: dict[str, str] = {}
    for patch in defects:
        for f in re.findall(r"^\+\+\+ b/(\S+)$", patch.read_text(), re.MULTILINE):
            how = ran.get(f)
            if how is None:
                refuse(f"{patch.name} patches {f}, and case.toml's ran names no way to show it ran")
            if not re.fullmatch(r"coverage|(exec|open) \S+|run \S+ \S+", how):
                refuse(f"case.toml ran {f} = {how!r}: want coverage, exec S, open S or run P A")
            out[f] = how
    return out


def check_ran(how: dict[str, str], trace: Trace | None, cov: set[str]) -> list[str]:
    """Each patched file the clean old run did not run, by its fact (facts())."""
    missing: list[str] = []
    for f, h in sorted(how.items()):
        kind, *rest = h.split()
        if kind == "coverage":
            held = f in cov
        elif trace is None:
            held = False
        elif kind == "exec":
            held = trace.executed(rest[0])
        elif kind == "open":
            held = trace.opens(rest[0])
        else:
            held = trace.ran(rest[0], rest[1])
        if not held:
            missing.append(f"{f} ({h})")
    return missing


def restore(k: Path, old_at: str, paths: list[str]) -> None:
    """PATHS checked out of OLD_AT into the copy K by git (mode and links as git holds them), then
    each checked on disk against OLD_AT's tree; refused where one is not as git holds it."""
    co = subprocess.run(
        ["git", "--literal-pathspecs", "checkout", old_at, "--", *paths],  # noqa: S607
        cwd=k,
        capture_output=True,
        check=False,
    )
    if co.returncode:
        refuse(f"git checkout {old_at} in the copy: {co.stderr.decode().strip()}")
    tree = git("--literal-pathspecs", "ls-tree", "-r", "-z", old_at, "--", *paths, cwd=k)
    for meta, _, p in (t.partition("\t") for t in filter(None, tree.stdout.decode().split("\0"))):
        mode, f = meta.split()[0], k / p
        st = f.lstat() if os.path.lexists(f) else None
        reg = st is not None and stat.S_ISREG(st.st_mode)
        held = {
            "120000": st is not None and stat.S_ISLNK(st.st_mode),
            "100755": reg and st is not None and st.st_mode & 0o100 != 0,
            "100644": reg and st is not None and st.st_mode & 0o100 == 0,
        }.get(mode, False)
        if not held:
            got = stat.filemode(st.st_mode) if st else "nothing"
            refuse(f"{p} is mode {mode} at {old_at}, restored as {got}: git cannot reproduce it")


def settle(k: Path) -> None:
    """What the run adds to the copy (restored files, a defect) committed on its branch: the
    copy's default branch then holds it, so the gate judges none of it changed (--help, budget)."""
    for a in (["add", "-A"], ["commit", "-q", "--allow-empty", "-m", "parity run"]):
        subprocess.run([*GIT, *a], cwd=k, capture_output=True, check=True)


def reset(k: Path) -> None:
    """The copy back at its commit: a patch and every restored file gone."""
    subprocess.run(["git", "reset", "-q", "--hard", COPY], cwd=k, check=True)  # noqa: S607
    subprocess.run(["git", "clean", "-qfd"], cwd=k, check=True)  # noqa: S607


def apply(k: Path, patch: Path | None) -> None:
    if patch and sh(["git", "apply", str(patch)], k):
        sys.exit(
            f"lever: {patch} does not apply to this kit; remake it: lever --help, Re-anchoring"
        )


@dataclass
class Lever:
    """One case's runs in the kit copy K: CASE (case.toml), FILES (restored from old_at), each
    run's log under LOGS."""

    k: Path
    logs: Path
    case: dict[str, str]
    files: dict[str, bytes]

    def run_old(self, name: str, how: dict[str, str] | None) -> int:
        """The old test with FILES restored by git (restore(); committed, settle(): the coverage
        map sees it as the kit's, the budget as unchanged), with no network (OFFLINE);
        with HOW (the clean run), traced and measured, and refused unless it ran every file HOW
        names."""
        k, logs, files, old = self.k, self.logs, self.files, self.case["old"]
        restore(k, self.case["old_at"], sorted(files))
        item = "::" in old  # a pytest item id: run as itself, its file restored above
        settle(k)
        log = logs / f"{name}.old.log"
        cmd = [
            "just",
            "test",
            "-x",
            "-rA",
            old if item else f"tests/gate/test_gate.py::test_script[{old}]",
        ]
        if how is None:
            return sh([*OFFLINE, *cmd], k, log)
        with tempfile.TemporaryDirectory(prefix="lever-old-") as w:
            cov, tr = Path(w) / "cov", Path(w) / "trace"
            cov.mkdir()
            tr.mkdir()
            # Measured only when a fact asks: coverage.py fails at exit in a process that cannot
            # write its data file (one inside the qc sandbox, where only overlays are writable).
            measured = any(h == "coverage" for h in how.values())
            env = (
                {
                    "COV_MAP_DIR": str(cov),
                    "COVERAGE_PROCESS_START": str(k / "tests/gate/coverage.toml"),
                }
                if measured
                else {}
            )
            cmd += [f"--junitxml={cov / 'junit.xml'}"]
            traced = any(not h.startswith("coverage") for h in how.values())
            if traced:
                strace = shutil.which("strace")
                if strace is None:
                    refuse(
                        "strace is not on PATH: the old run's exec and open facts cannot be read"
                    )
                cmd = [
                    strace,
                    "-ff",
                    "-qq",
                    "--seccomp-bpf",
                    "-s",
                    "4096",
                    "-e",
                    "trace=execve,openat",
                    "-o",
                    str(tr / "t"),
                    *cmd,
                ]
            rc = sh([*OFFLINE, *cmd], k, log, env)
            missing = check_ran(
                how,
                Trace(tr) if traced else None,
                covered(k, cov, cov / "junit.xml", old) if measured else set(),
            )
        if missing:
            shells = sorted(p for p in files if p != old and p.endswith(".sh"))
            note = (
                "; bash said: " + " | ".join(bash_errors(log, old, shells)[:3])
                if bash_errors(log, old, shells)
                else ""
            )
            ran = ", ".join(missing)
            refuse(
                f"(a) on the clean tree the old test did not run {ran} (exit {rc}, log {log}){note}"
            )
        sys.stdout.write(
            f"  old ran (clean tree): {', '.join(f'{f} ({h})' for f, h in sorted(how.items()))}\n"
        )
        return rc

    def run(self, patch: Path | None, how: dict[str, str] | None) -> tuple[int, int]:
        """One defect (PATCH; None: no defect, the run HOW checks): the old test, then the new
        on the kit's own files; its line printed; the old and new exit statuses."""
        k, logs, case = self.k, self.logs, self.case
        name = patch.stem if patch else "none"
        apply(k, patch)
        old_rc = self.run_old(name, how)
        reset(k)
        apply(k, patch)
        settle(k)
        new = [*OFFLINE, "just", "test", "-x", "-rA", case["new"]]
        new_rc = sh(new, k, logs / f"{name}.new.log")
        reset(k)
        said = {0: "pass"}
        line = (
            f"defect: {name}  old: {said.get(old_rc, 'FAIL')} (exit {old_rc})  "
            f"new: {said.get(new_rc, 'FAIL')} (exit {new_rc})"
        )
        if patch:
            line += f"  ({patch.read_text().splitlines()[0]})"
        sys.stdout.write(line + "\n")
        sys.stdout.flush()
        return old_rc, new_rc


def main() -> int:
    args = sys.argv[1:]
    background = BACKGROUND in args
    if background:
        args.remove(BACKGROUND)
    if len(args) != 1 or args[0] in ("-h", "--help"):
        sys.stdout.write(__doc__ or "")
        return 0 if len(args) == 1 else 2
    d = ROOT / "tests" / "parity" / args[0]
    if not (d / "case.toml").is_file():
        sys.exit(f"lever: no case {args[0]}: no file {d / 'case.toml'}")
    case = tomllib.loads((d / "case.toml").read_text())
    old, old_at = case["old"], case["old_at"]
    defects = sorted(d.glob("*.patch"))
    logs = Path(tempfile.mkdtemp(prefix=f"parity-{args[0]}-"))
    # The copy outside /tmp, where the kit itself lives: the qc sandbox makes /tmp private, so a
    # kit under /tmp holding a test's own kit copy under /tmp is a setup the real kit never has.
    common = git("rev-parse", "--path-format=absolute", "--git-common-dir").stdout.decode().strip()
    (Path(common) / "octo-feather").mkdir(exist_ok=True)
    with (
        tempfile.TemporaryDirectory(prefix="parity-kit-", dir=Path(common) / "octo-feather") as t,
        tempfile.TemporaryDirectory(prefix="parity-mise-state-") as ms,
    ):
        # mise's state dir one per lever run, removed after it: the `just` shim each run starts in
        # the copy records the copy's mise.toml there (tracked-configs), never in the caller's,
        # where the link dangles once the copy goes (#664).
        os.environ["MISE_STATE_DIR"] = ms
        k = Path(t)
        record = None
        try:
            if background:
                lowest()
                memory_floor()
                record = turnless(args[0])
            how = facts(case, defects)
            offline()
            files = old_files(old, old_at, case.get("needs", []))
            copy(k)
            for b in unrestored(old, old_at, files, k):  # a hint only: the run's facts decide
                sys.stdout.write(f"lever: note: {old} names {b}, and needs omits it\n")
            sys.stdout.write(f"restored from {old_at}: {' '.join(sorted(files))}\n")
            lever = Lever(k, logs, case, files)
            results = [lever.run(None, how)]
            results += [lever.run(p, None) for p in defects]
            if defects and all(o == 0 for o, _ in results[1:]):
                refuse("(b) the old test failed on no seeded defect: it shows no defect it catches")
        except RefusedError as e:
            sys.stderr.write(f"lever: refused: {e}\n")
            return 2
        finally:
            if record is not None:
                record.unlink(missing_ok=True)
    want = [0] + [1] * len(defects)
    good = all(
        (o == 0) == (w == 0) and (n == 0) == (w == 0)
        for (o, n), w in zip(results, want, strict=True)
    )
    sys.stdout.write(
        f"parity {'holds' if good else 'FAILS'}: want both pass with no defect, both fail on "
        f"each; logs: {logs}\n"
    )
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
