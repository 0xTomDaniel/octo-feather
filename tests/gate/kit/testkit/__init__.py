"""The kit tests' one testkit (#606): shared stand-ins, scratch dirs, fixture loading, and the
scenario runner every pytest kit test under tests/gate/kit/ goes through.

A kit test drives the kit's commands for real (AGENTS.md Rules); stand-ins sit only where the
kit does not own the system (what may be stubbed: the tdd skill, Seams and mocking.md): FAKES
names each one, first on a scratch PATH. A scenario file (NAME.py, beside its test_NAME.py)
holds scenarios, functions of a Scratch, and no pytest import, so its command starts light; each
pytest item runs its scenario as that file's command (`python3 FILE SCENARIO`, main below)
through the `case` fixture (tests/gate/kit/conftest.py), so a qc capture, which runs a tagged
item's command in its sandbox with its own /tmp, sees the whole scenario (quality spec
#qc-capture). A setup several items repeat is prepared once per gate run (Scratch.prepare). A
missing fixture fails naming it.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Mapping, Sequence

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FIXTURES = ROOT / "tests" / "fixtures"
# Each stand-in by the command it stands in for: gh (GitHub), herdr (Herdr), pi (Pi, at its
# classifier boundary: tests/fixtures/classify-stub/pi's header says what it answers).
FAKES = {
    "gh": HERE / "gh.py",
    "herdr": HERE / "herdr.py",
    "pi": FIXTURES / "classify-stub" / "pi",
}
# Stand-ins a scenario puts first on PATH itself, where its command reaches the system another
# way: pi_agent.py (Pi at the agent boundary, an eval case's role run, a reflector's reply;
# tests/lib/qa.sh copies it too; reflector below), gh.py (above) on a PATH of its own,
# git_refused.py (a git remote refusing credentials, as `git`), curl.py (OpenRouter's key usage,
# as `curl`), argv_recorder.sh (a caller's argv and cwd, as the command it calls) and uname.sh
# (another OS, as `uname`); each file's header says what it answers. A model provider is no
# command: provider.py serves Pi's provider boundary on 127.0.0.1 (started by `provider`, below;
# its header says what it answers); nor is an MCP server: mcp_stub.py, as an mcp.json names it.
# Unset in every scenario: a user's config, state and auth, a Herdr pane's session, and a check
# run's marker (a scenario's commands start outside any check run: scripts/check-gate-free).
CLEARED = (
    "XDG_CONFIG_HOME",
    "XDG_STATE_HOME",
    "XDG_CACHE_HOME",
    "GH_CONFIG_DIR",
    "OPENROUTER_API_KEY",
    "OCTO_FEATHER_CHECK_RUN",
)


class MissingFixtureError(FileNotFoundError):
    pass


def fixture(name: str) -> str:
    """The text of tests/fixtures/NAME; a missing one fails naming it."""
    p = FIXTURES / name
    if not p.is_file():
        msg = f"testkit: fixture {name} is missing: no file {p}"
        raise MissingFixtureError(msg)
    return p.read_text()


def kit(name: str) -> str:
    """The kit command NAME (scripts/NAME), as a path to run."""
    return str(ROOT / "scripts" / name)


class Ran(NamedTuple):
    """A command's exit, stdout and stderr (a NamedTuple: dataclasses' import is a third of a
    scenario's start)."""

    rc: int
    out: str
    err: str


class Gh:
    """The fake gh's store (testkit/gh.py): its PRs as JSON and its call log."""

    def __init__(self, d: Path) -> None:
        self.dir = d
        (d / "pr").mkdir(parents=True)
        (d / "log").write_text("")

    def pr(self, n: int) -> dict[str, object]:
        return json.loads((self.dir / "pr" / f"{n}.json").read_text())

    def put(self, n: int, d: Mapping[str, object]) -> None:
        (self.dir / "pr" / f"{n}.json").write_text(json.dumps(d))

    def store(self, rel: str, d: object) -> None:
        """The store's REL (its layout: testkit/gh.py's docstring) holding D, JSON unless a
        str."""
        p = self.dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(d if isinstance(d, str) else json.dumps(d))

    def tape(self, tapes: Mapping[str, Sequence[object]]) -> None:
        """The store's tapes (testkit/gh.py's docstring) set to TAPES, each call's recorded
        answers in order, replayed from the first; the call log emptied."""
        (self.dir / "tape.json").write_text(json.dumps(tapes))
        (self.dir / "tape.n.json").unlink(missing_ok=True)
        (self.dir / "log").write_text("")

    def log(self) -> list[str]:
        return (self.dir / "log").read_text().splitlines()

    def writes(self) -> int:
        """The calls that write (`api -X`); a GET carries no -X."""
        return sum(ln.startswith("api -X ") for ln in self.log())


def cpu_read() -> float | None:
    # Process-local reads are needed before the parent waits; the portable root gate stays
    # standalone. Its cpu_s alone decides the budget; these stdlib reads only attribute it.
    try:
        import resource  # noqa: PLC0415

        s, c = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    except (ImportError, OSError):
        return None
    return s.ru_utime + s.ru_stime + c.ru_utime + c.ru_stime


@contextlib.contextmanager
def cpu_stage(name: str) -> Generator[None]:
    start = cpu_read()
    completed = False
    try:
        yield
        completed = True
    finally:
        end = cpu_read()
        value = end - start if start is not None and end is not None else None
        status = "completed" if completed and value is not None else "unavailable"
        if not completed:
            status = "incomplete"
            value = None
        print("cpu_stage " + json.dumps({"stage": name, "cpu_s": value, "status": status}))


class Scratch:
    """One scenario's world under a fresh temp dir: HOME, TMPDIR, mise's state dir
    (MISE_STATE_DIR, ROOT/mise-state: what mise trusts and tracks, never the caller's, #683), the
    fakes first on PATH, CLEARED unset, and a fake GitHub store. Removed when the scenario ends."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.home = root / "home"
        self.bin = root / "bin"
        for d in (self.home, self.bin, root / "tmp"):
            d.mkdir()
        self.link_fakes(ROOT)
        self.gh = Gh(root / "gh")
        env = {k: v for k, v in os.environ.items() if k not in CLEARED}
        env |= {
            "HOME": str(self.home),
            "TMPDIR": str(root / "tmp"),
            "MISE_STATE_DIR": str(root / "mise-state"),
            "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}",
            "FAKE_GH": str(self.gh.dir),
            "GH_TOKEN": "testkit-token",  # the caller's gh auth, as the fake gh asks for it
        }
        self.env = env

    def link_fakes(self, kit_dir: Path) -> None:
        """The fakes on PATH from the kit at KIT_DIR: a copy of the kit under test must hold its
        own, as the qc sandbox shows a judge only the kit under test (a link into another kit
        under /tmp would dangle there)."""
        for name, src in FAKES.items():
            (self.bin / name).unlink(missing_ok=True)
            (self.bin / name).symlink_to(kit_dir / src.relative_to(ROOT))

    def prepare(self, name: str, build: Callable[[Scratch], None]) -> None:
        """This scratch filled with prepared NAME: a scratch BUILD fills once per gate run under
        GATE_RUN_DIR (the run's shared dir: tests/gate/test_gate.py), the first caller under an
        exclusive lock, every later one waiting on it, as tests/gate/kit/testkit/prepared.py prepares template
        installs; read-only by contract, copied here (its bin and tmp aside). Outside a gate run,
        BUILD fills this scratch itself."""
        import fcntl  # noqa: PLC0415 (lazy: a scenario's start pays only what it uses)
        import shutil  # noqa: PLC0415

        run = os.environ.get("GATE_RUN_DIR")
        if not run:
            build(self)
            return
        tree, done = Path(run) / f"prepared-{name}", Path(run) / f"prepared-{name}.done"
        with (Path(run) / f"prepared-{name}.lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            if not done.exists():
                shutil.rmtree(tree, ignore_errors=True)  # a caller before failed part way
                tree.mkdir()
                build(Scratch(tree))
                done.touch()

        def own(d: str, names: list[str]) -> set[str]:
            return {"bin", "tmp"} & set(names) if Path(d) == tree else set()

        shutil.copytree(tree, self.root, symlinks=True, dirs_exist_ok=True, ignore=own)

    def run(
        self,
        cmd: Sequence[str],
        *,
        want: int = 0,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
        stdin: str | None = None,
    ) -> Ran:
        """CMD's exit, stdout and stderr (trailing newlines cut, as a shell's $(...)); fails
        unless it exits WANT without a traceback."""
        p = subprocess.run(
            list(cmd),
            cwd=cwd or self.root,
            env={**self.env, **(env or {})},
            input=stdin,
            capture_output=True,
            text=True,
            check=False,
        )
        said = f"{' '.join(cmd)}: exit {p.returncode}, want {want}\n{p.stdout}\n{p.stderr}"
        assert p.returncode == want, said
        assert "Traceback" not in p.stderr, f"a traceback: {said}"
        return Ran(p.returncode, p.stdout.rstrip("\n"), p.stderr.rstrip("\n"))

    def without(self, *names: str) -> None:
        """This scratch's PATH with no program NAMES reachable, whatever the box installed
        globally (a CI image's tsc in /usr/local/bin): each PATH dir holding one is replaced by a
        scratch dir linking every other entry of it, so the dir's other tools stay found. A tool's
        own PATH additions (a justfile's mise dirs) are the scenario's premise to assert."""
        dirs: list[str] = []
        for i, d in enumerate(self.env["PATH"].split(os.pathsep)):
            if not d or not any(os.access(Path(d, n), os.X_OK) for n in names):
                dirs.append(d)
                continue
            mask = self.root / "masked" / str(i)
            mask.mkdir(parents=True)
            for e in os.scandir(d):
                if e.name not in names:
                    (mask / e.name).symlink_to(Path(d, e.name))
            dirs.append(str(mask))
        self.env["PATH"] = os.pathsep.join(dirs)

    def identity(self, name: str = "t", email: str = "t@t") -> None:
        """The factory commit identity set in the scratch HOME's state, through the kit's command
        (`pi-role --set-identity`): a launch of a role that would commit refuses without it
        (scripts/pi-role --help, Commit identity)."""
        self.run([kit("pi-role"), "--set-identity", name, email])

    def git(self, repo: Path, *args: str) -> str:
        """git ARGS in REPO with a scratch identity; its stdout."""
        ident = [
            "-c",
            "user.email=t@example.com",
            "-c",
            "user.name=t",
            "-c",
            "commit.gpgsign=false",
        ]
        return self.run(["git", "-C", str(repo), *ident, *args]).out


# The reflector's question lines (reflection/questions.json's ids, as agents/reflector.md answers).
LANE_QUESTIONS = (
    "Questions: caught-by-hand, slow-or-from-memory, undetected-rule, check-misfired, "
    "mechanical-step, writer-mistake, reflection-missed"
)
DIRECTOR_QUESTIONS = (
    "Questions: owner-asked, answered-from-memory, rework-decision, unblocking-first, "
    "outside-owner-gates, fact-already-recorded, writer-route, director-mechanical-step, "
    "director-reflection-missed"
)


def reflector(s: Scratch, lane: Sequence[str] = (), director: Sequence[str] = ()) -> None:
    """S's Pi the testkit's agent stand-in (pi_agent.py, print mode) first on PATH, its reflector
    replies recorded in S: the lane's FindingS lines (or `Findings: none`), the director's."""
    (s.bin / "pi").unlink(missing_ok=True)
    (s.bin / "pi").symlink_to(HERE / "pi_agent.py")
    s.env["STUB_REPLY_DIR"] = str(s.root)
    for who, q, found in (
        ("lane", LANE_QUESTIONS, lane),
        ("director", DIRECTOR_QUESTIONS, director),
    ):
        body = "\n".join(found) if found else "Findings: none"
        (s.root / f"reply.{who}").write_text(f"{q}\n{body}\n")


def build_kit_repo(p: Scratch) -> None:
    """The kit's tracked files (their worktree content; a tracked file deleted there skipped) in
    P/kit, a git repo of one commit."""
    import shutil  # noqa: PLC0415 (lazy: Scratch.prepare's)

    k = p.root / "kit"
    names = subprocess.run(
        ["git", "ls-files", "-z"],  # noqa: S607
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout.decode()
    for rel in filter(None, names.split("\0")):
        src = ROOT / rel
        if src.is_file() or src.is_symlink():
            (k / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, k / rel, follow_symlinks=False)
    p.git(k, "init", "-q")
    p.git(k, "add", "-A")
    p.git(k, "-c", "core.hooksPath=/dev/null", "commit", "-qm", "base")


def kit_repo(s: Scratch) -> Path:
    """S/kit: a git repo copy of the kit's tracked files (as `git ls-files` names them), one
    commit, prepared once per gate run (Scratch.prepare: the prepared tree read-only, S/kit this
    scenario's own copy of it, free to plant files in), for a scenario that runs the kit's own
    gate recipes or commands on a copy. check_ts.py's Copy and qa_analyst.py's build_kit stay
    file-local: each filters the kit differently (no git repo; a dir subset at two commits)."""
    s.prepare("kit-repo", build_kit_repo)
    return s.root / "kit"


def kit_deps(k: Path) -> None:
    """A kit copy K given the kit's installed JavaScript packages, as a scenario's copy of the kit
    needs them where it runs that copy's scripts: the qc sandbox runs srt from the running kit's
    node_modules at its package.json pin (scripts/octo-feather-qc-sandbox --help), read outside the
    sandbox, so links to this kit's serve. K's package.json linked when the copy has none; in a git
    repo K, both kept out of its status (.git/info/exclude)."""
    names = [n for n in ("package.json", "node_modules") if not (k / n).exists()]
    for n in names:
        (k / n).symlink_to(ROOT / n)
    if (k / ".git").is_dir() and names:
        ex = k / ".git" / "info" / "exclude"
        ex.parent.mkdir(parents=True, exist_ok=True)
        with ex.open("a") as f:
            f.write("".join(f"/{n}\n" for n in names))


def asked(*cmd: str) -> str:
    """CMD's answer, a path it prints (stdout, stripped), asked from the kit's dir with the
    caller's HOME, uncoloured: NO_COLOR, no FORCE_COLOR, and uv's own --color never, as uv
    colours even a path under FORCE_COLOR (as a CI runner may set it), and a coloured path is no
    dir. The testkit's one way to ask a tool where its things are."""
    import shutil  # noqa: PLC0415 (lazy: a scenario's start pays only what it uses)

    exe = shutil.which(cmd[0]) or cmd[0]
    args = ["--color", "never", *cmd[1:]] if cmd[0] == "uv" else list(cmd[1:])
    env = {k: v for k, v in os.environ.items() if k != "FORCE_COLOR"} | {"NO_COLOR": "1"}
    p = subprocess.run([exe, *args], cwd=ROOT, env=env, capture_output=True, text=True, check=True)
    return p.stdout.strip()


def tool_homes() -> dict[str, str]:
    """The tools' own installs and caches as the caller's HOME finds them, for a scenario that
    runs the tools of a repo (mise.toml, uv, pnpm), never the scratch HOME's, where each would
    fetch again, from the network: mise's installed tools and download cache (its defaults:
    MISE_DATA_DIR, MISE_CACHE_DIR), uv's package cache and Pythons (`uv cache dir`, `uv python
    dir`, through asked)."""
    home = Path(os.environ["HOME"])
    data = os.environ.get("XDG_DATA_HOME") or str(home / ".local" / "share")
    cache = os.environ.get("XDG_CACHE_HOME") or str(home / ".cache")
    return {
        "MISE_DATA_DIR": os.environ.get("MISE_DATA_DIR") or f"{data}/mise",
        "MISE_CACHE_DIR": os.environ.get("MISE_CACHE_DIR") or f"{cache}/mise",
        "UV_CACHE_DIR": asked("uv", "cache", "dir"),
        "UV_PYTHON_INSTALL_DIR": asked("uv", "python", "dir"),
    }


def pnpm_store() -> str:
    """pnpm's store as the caller's HOME and the kit's dir find it (`pnpm store path`, through
    asked; one store for the kit and its test copies, owner ruling #422), for
    npm_config_store_dir."""
    return asked("pnpm", "store", "path")


# settled's reaper: this process the subreaper of what CMD starts (prctl PR_SET_CHILD_SUBREAPER,
# 36), so a process CMD leaves behind, detached or not, is reparented here; its own children
# waited for until none is left (ECHILD: no descendant can live without a live child of this one).
REAPER = """import ctypes, os, subprocess, sys
libc = ctypes.CDLL(None, use_errno=True)
assert libc.prctl(36, 1, 0, 0, 0) == 0, "testkit: no subreaper (Linux only)"
rc = subprocess.call(sys.argv[1:])
while True:
    try:
        os.wait()
    except ChildProcessError:
        break
sys.exit(rc)
"""


def settled(cmd: Sequence[str]) -> list[str]:
    """CMD as a command that exits, with CMD's exit, only once CMD and every process it started,
    detached ones too (a Pi extension's unref'd writer or herdr-say), have exited: readiness
    through the process tree this command owns, never a wait and never another process's /proc.
    Linux only."""
    return [sys.executable, "-c", REAPER, *cmd]


# Spec Chat's installer (scripts/install-spec-chat of a Spec Chat clone; the pinned extract,
# check-vendored --extract spec-chat, holds only its skills): the stand-in records its argv in the
# clone's `argv` (one per line), links the three skills into PREFIX/.agents/skills (a present link
# kept), writes its onboarding state under XDG_STATE_HOME, and says where it linked, as the real
# one does.
SPEC_CHAT_INSTALLER = """#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd -P)"
printf '%s\\n' "$@" > "$root/argv"
prefix=""; while [[ $# -gt 0 ]]; do [[ "$1" == --prefix ]] && { prefix="$2"; shift; }; shift; done
mkdir -p "$prefix/.agents/skills" "$XDG_STATE_HOME/spec-chat"
for p in spec-chat-shape:shape-spec spec-chat-review:review-spec repair-specs:repair-specs; do
  to="$prefix/.agents/skills/${p%%:*}"
  [[ -L "$to" ]] || ln -s "$root/skill/${p#*:}" "$to"
done
echo 'status = "pending"' > "$XDG_STATE_HOME/spec-chat/onboarding.toml"
echo "fake installer: linked into $prefix"
"""


def spec_chat_clone(d: Path) -> Path:
    """A Spec Chat clone at D (for SPEC_CHAT_CLONE): its three skills and the installer stand-in
    (SPEC_CHAT_INSTALLER, above)."""
    for name in ("shape-spec", "review-spec", "repair-specs"):
        (d / "skill" / name).mkdir(parents=True)
        (d / "skill" / name / "SKILL.md").write_text(f"# {name}\n")
    (d / "scripts").mkdir()
    (d / "scripts" / "install-spec-chat").write_text(SPEC_CHAT_INSTALLER)
    (d / "scripts" / "install-spec-chat").chmod(0o755)
    return d


@contextlib.contextmanager
def provider(*args: str) -> Generator[int]:
    """The fake model provider (testkit/provider.py, ARGS its own) serving while the block runs: its
    port, read off its own stdout pipe once it listens (readiness, never a wait); stopped after."""
    p = subprocess.Popen(
        [sys.executable, str(HERE / "provider.py"), *args], stdout=subprocess.PIPE, text=True
    )
    try:
        line = p.stdout.readline() if p.stdout else ""
        assert line.strip().isdigit(), f"testkit: the fake provider did not start: {line!r}"
        yield int(line)
    finally:
        p.kill()
        p.wait()


def real_pi(tag: str, *, pinned: bool = True) -> str:
    """The real pi on the caller's PATH (never testkit's stand-in), PINNED: at the kit's pin
    (pi-version), else failing naming the install command; its path."""
    import shutil  # noqa: PLC0415 (lazy: a scenario's start pays only what it uses)

    pin = (ROOT / "pi-version").read_text().strip()
    install = f"npm install -g --ignore-scripts @earendil-works/pi-coding-agent@{pin}"
    pi = shutil.which("pi", path=os.environ["PATH"])
    assert pi, f"{tag}: pi not on PATH; install Pi {pin}: {install}"
    if not pinned:
        return pi
    v = subprocess.run([pi, "--version"], capture_output=True, text=True, check=False)
    got = next(iter(re.findall(r"[0-9]+\.[0-9]+\.[0-9]+", v.stdout + v.stderr)), "no version")
    assert got == pin, f"{tag}: pi reports {got}, the kit pins {pin} (pi-version); {install}"
    return pi


def main(*scenarios: Callable[..., None]) -> None:
    """A test file's own command: `python3 FILE NAME [ARG...]` runs scenario NAME(scratch, *ARGS)
    in a fresh Scratch."""
    by = {s.__name__: s for s in scenarios}
    name, *args = sys.argv[1:] or [""]
    if name not in by:
        sys.exit(f"usage: {sys.argv[0]} SCENARIO [ARG...], SCENARIO one of {', '.join(by)}")
    t = scratch_dir(name)
    try:
        by[name](Scratch(t), *args)
    finally:
        subprocess.run(["rm", "-rf", "--", str(t)], check=False)  # noqa: S607 (the real rm)
    sys.stdout.write(f"{name}: ok\n")


def scratch_dir(name: str) -> Path:
    """A new dir NAME-PID-N under the temp dir ($TMPDIR, else /tmp, resolved), mkdir's own
    exclusivity making it new, as tempfile.mkdtemp does: here without tempfile's and shutil's
    imports (random, bz2, lzma: a quarter of every scenario's start; the dir is removed with rm)."""
    base = Path(os.environ.get("TMPDIR") or "/tmp").resolve()  # noqa: S108 (tempfile's own default)
    for n in range(100):
        d = base / f"{name}-{os.getpid()}-{n}"
        try:
            d.mkdir(mode=0o700)
        except FileExistsError:
            continue
        return d
    msg = f"testkit: no new scratch dir {name}-{os.getpid()}-N under {base}"
    raise FileExistsError(msg)
