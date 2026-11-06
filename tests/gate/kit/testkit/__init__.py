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

import fcntl
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

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
# way: pi_agent.py (Pi at the agent boundary, an eval case's role run; tests/lib/qa.sh copies it
# too), and gh.py (above) on a PATH of its own; each file's header says what it answers.
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


@dataclass(frozen=True)
class Ran:
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
        """The store's REL (testkit/gh.py: issue/N.json, run/N.json, repo.json, api/PATH.json,
        pr/N.diff) holding D, JSON unless a str."""
        p = self.dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(d if isinstance(d, str) else json.dumps(d))

    def log(self) -> list[str]:
        return (self.dir / "log").read_text().splitlines()

    def writes(self) -> int:
        """The calls that write (`api -X`); a GET carries no -X."""
        return sum(ln.startswith("api -X ") for ln in self.log())


class Scratch:
    """One scenario's world under a fresh temp dir: HOME, TMPDIR, the fakes first on PATH,
    CLEARED unset, and a fake GitHub store. Removed when the scenario ends."""

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
        exclusive lock, every later one waiting on it, as tests/lib/prepared.py prepares template
        installs; read-only by contract, copied here (its bin and tmp aside). Outside a gate run,
        BUILD fills this scratch itself."""
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


def asked(*cmd: str) -> str:
    """CMD's answer, a path it prints (stdout, stripped), asked from the kit's dir with the
    caller's HOME, uncoloured: NO_COLOR, no FORCE_COLOR, and uv's own --color never, as uv
    colours even a path under FORCE_COLOR (as a CI runner may set it), and a coloured path is no
    dir. The testkit's one way to ask a tool where its things are."""
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


def main(*scenarios: Callable[..., None]) -> None:
    """A test file's own command: `python3 FILE NAME [ARG...]` runs scenario NAME(scratch, *ARGS)
    in a fresh Scratch."""
    by = {s.__name__: s for s in scenarios}
    name, *args = sys.argv[1:] or [""]
    if name not in by:
        sys.exit(f"usage: {sys.argv[0]} SCENARIO [ARG...], SCENARIO one of {', '.join(by)}")
    base = Path(tempfile.gettempdir()).resolve()
    t = Path(tempfile.mkdtemp(prefix=f"{name}-", dir=base))
    try:
        by[name](Scratch(t), *args)
    finally:
        shutil.rmtree(t, ignore_errors=True)
    sys.stdout.write(f"{name}: ok\n")
