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
import fcntl
import fnmatch
import hashlib
import json
import os
import resource
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple, TypeVar, cast

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

T = TypeVar("T")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FIXTURES = ROOT / "tests" / "fixtures"
# scripts/ on sys.path once, here, so a scenario run as its file's command imports a kit module as
# a pytest test does (how: pyproject.toml, [tool.pytest.ini_options] pythonpath's comment).
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
# Each stand-in by the command it stands in for: gh (GitHub), herdr (Herdr), pi (Pi, at its
# classifier boundary: tests/fixtures/classify-stub/pi's header says what it answers), busctl and
# systemctl (the systemd user manager: systemd.py's header).
FAKES = {
    "gh": HERE / "gh.py",
    "herdr": HERE / "herdr.py",
    "pi": FIXTURES / "classify-stub" / "pi",
    "busctl": HERE / "systemd.py",
    "systemctl": HERE / "systemd.py",
}
# Stand-ins a scenario puts first on PATH itself, where its command reaches the system another
# way: pi_agent.py (Pi at the agent boundary, an eval case's role run; qa_box.py copies it
# too), and gh.py (above) on a PATH of its own; systemd.py as systemd-run (a transient unit;
# agent_scope.py runs the box's real one); each file's header says what it answers.
# provider.py stands in for a model provider, a server its caller starts (its header).
# tests/fixtures/install-check/pi stands in for Pi at its version and its model proxy, the
# install-check items' one (install_check.py, its header).
# pi_agent.py with FAKE_QC set: the qc sandbox items' judge (qc_box.py; its docstring).
# tests/fixtures/qa-bench/registry.mjs stands in for the model at a judgment bench's classify path,
# the qa items' `pi-extension` (qa_box.py, its header).
# Unset in every scenario: a user's config, state and auth, a Herdr pane's session, and a check
# run's marker (a scenario's commands start outside any check run: scripts/check-gate-free).
# GH_REPO, gh's repo override, too: the fake gh's request names it (testkit/gh.py).
CLEARED = (
    "XDG_CONFIG_HOME",
    "XDG_STATE_HOME",
    "XDG_CACHE_HOME",
    "GH_CONFIG_DIR",
    "GH_REPO",
    "OPENROUTER_API_KEY",
    "OCTO_FEATHER_CHECK_RUN",
)
# Set in every scenario as git's environment config (GIT_CONFIG_COUNT, outranking any repo's
# own): no git a scenario runs starts automatic maintenance (gc --auto, maintenance run --auto),
# which would keep writing in a .git a prepared scratch's copy reads (#916).
QUIET_GIT = {"maintenance.auto": "false", "gc.auto": "0"}


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
        return sum(ln.startswith("api") for ln in self.log())


class Scratch:
    """One scenario's world under a fresh temp dir: HOME, TMPDIR, the fakes first on PATH,
    CLEARED unset, QUIET_GIT set, and a fake GitHub store. Removed when the scenario ends."""

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
        n = int(env.get("GIT_CONFIG_COUNT") or 0)  # appended to the caller's, never replacing
        for i, (k, v) in enumerate(QUIET_GIT.items(), n):
            env |= {f"GIT_CONFIG_KEY_{i}": k, f"GIT_CONFIG_VALUE_{i}": v}
        env["GIT_CONFIG_COUNT"] = str(n + len(QUIET_GIT))
        self.env = env

    def link_fakes(self, kit_dir: Path) -> None:
        """The fakes on PATH from the kit at KIT_DIR: a copy of the kit under test must hold its
        own, as the qc sandbox shows a judge only the kit under test (a link into another kit
        under /tmp would dangle there)."""
        for name, src in FAKES.items():
            (self.bin / name).unlink(missing_ok=True)
            (self.bin / name).symlink_to(kit_dir / src.relative_to(ROOT))

    def prepare(
        self, name: str, build: Callable[[Scratch], None], *, linked: Sequence[str] = ()
    ) -> None:
        """This scratch filled with prepared NAME: a scratch BUILD fills once per gate run under
        GATE_RUN_DIR (the run's shared dir: tests/gate/test_gate.py), the first caller under an
        exclusive lock, every later one waiting on it, as tests/lib/prepared.py prepares template
        installs; read-only by contract, copied here (its bin and tmp aside); BUILD's CPU billed to
        its own line, shared-NAME (GATE_SHARED_CPU: tests/gate/conftest.py); each file whose path
        (relative to the scratch) matches a LINKED glob (fnmatch: `*` crosses `/`) hard-linked, not
        copied, where one filesystem holds both: files no case and no tool writes, as pnpm links
        its store's package files into node_modules. Outside a gate run, BUILD fills this scratch
        itself."""
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
                cpu = _cpu()
                build(Scratch(tree))
                _bill(f"shared-{name}", _cpu() - cpu)
                done.touch()

        def own(d: str, names: list[str]) -> set[str]:
            return {"bin", "tmp"} & set(names) if Path(d) == tree else set()

        def copy(src: str, dst: str) -> object:
            if any(fnmatch.fnmatchcase(os.path.relpath(src, tree), g) for g in linked):
                with contextlib.suppress(OSError):  # another filesystem: copied
                    os.link(src, dst)
                    return dst
            return shutil.copy2(src, dst)

        shutil.copytree(
            tree, self.root, symlinks=True, dirs_exist_ok=True, ignore=own, copy_function=copy
        )

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


def _cpu() -> float:
    s, c = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    return s.ru_utime + s.ru_stime + c.ru_utime + c.ru_stime


def _bill(line: str, cpu: float) -> None:
    """Shared set-up's CPU on its own LINE, to the gate's GATE_SHARED_CPU file
    (tests/gate/conftest.py)."""
    if path := os.environ.get("GATE_SHARED_CPU"):
        with contextlib.suppress(OSError), Path(path).open("a") as f:
            f.write(json.dumps({"line": line, "cpu_s": round(cpu, 3)}) + "\n")


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
    npm_config_store_dir: in a gate run, the one check-tests asked and exported to every item
    (npm_config_store_dir, the justfile), never asked again (~0.5 s CPU a run)."""
    # pnpm's own lowercase name for it
    return os.environ.get("npm_config_store_dir") or asked("pnpm", "store", "path")  # noqa: SIM112


def tracked(dest: Path) -> None:
    """DEST, a new dir, holding a copy of the kit's tracked files (a tracked file deleted in the
    worktree skipped)."""
    dest.mkdir()
    git, tar = shutil.which("git") or "git", shutil.which("tar") or "tar"
    files = subprocess.run(
        [git, "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True
    ).stdout
    tar_ = subprocess.run(
        [tar, "-cf", "-", "--null", "--ignore-failed-read", "-T", "-"],
        cwd=ROOT,
        input=files,
        capture_output=True,
        check=False,
    ).stdout
    subprocess.run([tar, "-xf", "-"], cwd=dest, input=tar_, check=True)


def installed_kit(s: Scratch) -> Path:
    """S/kit: the kit's tracked files (tracked) with its JavaScript packages installed, `pnpm
    install --offline --frozen-lockfile` from the kit's pnpm store (pnpm_store), shared set-up
    prepared once per gate run (Scratch.prepare, line shared-kit-copy; the package files in its
    node_modules linked, as pnpm links them from its store, pnpm's own state files copied); S's
    env names the tools' homes (tool_homes) and that store, as the copy's recipes need them. A
    case whose proof is the install itself (an empty store, another filesystem) copies with
    tracked and installs its own."""

    def build(p: Scratch) -> None:
        store = pnpm_store()  # the caller's HOME finds it, never the scratch HOME
        p.env |= tool_homes() | {"npm_config_store_dir": store}
        tracked(p.root / "kit")
        pnpm = shutil.which("pnpm") or "pnpm"
        p.run([pnpm, "install", "--offline", "--frozen-lockfile"], cwd=p.root / "kit")
        (p.root / "pnpm-store").write_text(store)

    s.prepare("kit-copy", build, linked=["kit/node_modules/.pnpm/*/node_modules/*"])
    s.env |= tool_homes() | {"npm_config_store_dir": (s.root / "pnpm-store").read_text()}
    return s.root / "kit"


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


# The reflection's world and readers (the lane and director reflection tests): what
# scripts/octo-feather-reflect shows its reflector and writes, read once into typed records (quality
# #edge-validation-kit), each window checked as a reflector reads it.
QUESTIONS = {
    "lane": [
        "caught-by-hand",
        "slow-or-from-memory",
        "undetected-rule",
        "check-misfired",
        "mechanical-step",
        "writer-mistake",
        "reflection-missed",
    ],
    "director": [
        "owner-asked",
        "answered-from-memory",
        "rework-decision",
        "unblocking-first",
        "outside-owner-gates",
        "fact-already-recorded",
        "writer-route",
        "director-mechanical-step",
        "director-reflection-missed",
    ],
}
DIRECTOR = {"type": "session", "id": "synthetic-director", "cwd": "/synthetic/director"}
MODEL_DOWN = "echo 'Error: 503 model openai/gpt-6.1-sol unreachable' >&2; exit 1"
WINDOW = 32768


def reflector(s: Scratch) -> Path:
    """S's reflection world, its state dir's octo-feather dir: Pi the testkit's agent in print
    mode first on PATH (pi_agent.py: records and turn in S), each reflector replying no gap; the
    director record naming pane w9:p99, its Pi session S/director.jsonl named natively there
    (director)."""
    for k in ("HERDR_PANE_ID", "PI_SESSION_FILE", "PI_SESSION_ID", "OCTO_FEATHER_REFLECT_ARGS"):
        s.env.pop(k, None)
    (s.bin / "pi").unlink()
    (s.bin / "pi").symlink_to(HERE / "pi_agent.py")
    top = s.root / "state" / "octo-feather"
    top.mkdir(parents=True)
    s.env |= {"XDG_STATE_HOME": str(s.root / "state"), "HERDR_SESSION": ""}
    s.env |= {"STUB_REPLY_DIR": str(s.root), "FAKE_HERDR": str(s.root / "herdr")}
    (s.root / "herdr").mkdir()
    for who in QUESTIONS:
        reply(s, who)
    (top / "director.toml").write_text('pane = "w9:p99"\n')
    (s.root / "director.jsonl").write_text(json.dumps(DIRECTOR) + "\n")
    director(s)
    return top


def director(s: Scratch, native: str | None = "path", pane: str = "w9:p99") -> None:
    """Herdr's world (testkit herdr): the director's Pi working at PANE, its session named
    natively by NATIVE (`path` S/director.jsonl, `id` its header's id) or not (None)."""
    g: dict[str, object] = {"name": "director", "pane_id": pane, "workspace_id": "w9"}
    g |= {"tab_id": "w9:t1", "agent": "pi", "agent_status": "working", "terminal_id": "t"}
    g["cwd"] = DIRECTOR["cwd"]
    if native:
        v = str(s.root / "director.jsonl") if native == "path" else DIRECTOR["id"]
        g["agent_session"] = {"source": "herdr:pi", "agent": "pi", "kind": native, "value": v}
    (s.root / "herdr" / "agents.json").write_text(json.dumps({pane: g}))


def reply(s: Scratch, who: str, *findings: str) -> None:
    """WHO's reflector replies its questions, then FINDINGS (`class: ... | summary: ...`)."""
    body = "".join(f"Finding: {f}\n" for f in findings) or "Findings: none\n"
    (s.root / f"reply.{who}").write_text(f"Questions: {', '.join(QUESTIONS[who])}\n{body}")


def turn(s: Scratch, who: str, cmd: str = "") -> None:
    """WHO's model turn the shell command CMD (pi_agent.py print mode); none when empty."""
    (s.root / f"turn.{who}").unlink(missing_ok=True)
    if cmd:
        (s.root / f"turn.{who}").write_text(cmd)


def tree(d: Path) -> list[tuple[str, str]]:
    """Every entry under D: its path and a file's sha256 (a dir: d)."""
    return sorted(
        (str(p), hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else "d")
        for p in d.rglob("*")
    )


def get(d: Mapping[str, object], key: str, t: type[T], where: str) -> T:
    """D's KEY, a T (a bool no int), else fail naming the field."""
    v = d.get(key)
    ok = isinstance(v, t) and (t is bool or not isinstance(v, bool))
    assert ok, f"{where}: field {key} is no {t.__name__}: {v!r}"
    return cast("T", v)


def maybe(d: Mapping[str, object], key: str, where: str) -> str | None:
    v = d.get(key)
    assert v is None or isinstance(v, str), f"{where}: field {key} is no string: {v!r}"
    return v


def obj(v: object, where: str) -> Mapping[str, object]:
    assert isinstance(v, dict), f"{where} is no JSON object: {v!r}"
    return cast("Mapping[str, object]", v)


def items(d: Mapping[str, object], key: str, where: str) -> list[object]:
    return cast("list[object]", get(d, key, list, where))


class Source(NamedTuple):
    """A source or derived report the reflector was shown: DATA rebuilt from its windows, SPANS
    each window's LF line span in the original; LINES the director log's window of lines."""

    original: str
    size: int
    sha256: str
    data: bytes = b""
    spans: tuple[tuple[int, int], ...] = ()
    windows: int = 0
    lines: list[int] | None = None

    def text(self) -> str:
        all_ = self.data.decode("utf-8", "surrogateescape").splitlines(keepends=True)
        return "".join(all_ if self.lines is None else [all_[i - 1] for i in self.lines])


class Manifest(NamedTuple):
    """A reflection's inputs: the manifest it was shown, the provenance its line keeps. SOURCES:
    the available ones by identity."""

    mode: str | None  # the director binding's
    pane: str | None
    session: str | None
    lane: str | None  # the scope's
    sources: dict[str, Source]
    derived: dict[str, Source]

    def text(self) -> str:
        return "".join(x.text() for x in [*self.sources.values(), *self.derived.values()])


def windows(p: Mapping[str, object], seen: Path, at: str) -> tuple[bytes, list[tuple[int, int]]]:
    """The bytes and LF line spans of presentation P's windows, read in SEEN."""
    sid = get(p, "source_id", str, at)
    assert sid.split("-", 1)[1].isdigit(), f"{at}: field source_id {sid}"
    assert get(p, "encoded_bytes", int, at) == WINDOW, f"{at}: field encoded_bytes"
    pattern = Path(get(p, "pattern", str, at))
    out, spans = bytearray(), list[tuple[int, int]]()
    for i in range(get(p, "count", int, at)):
        raw = (seen / pattern.parent.name / pattern.name.format(index=i)).read_bytes()
        w, wat = obj(json.loads(raw), f"{at} window {i}"), f"{at} window {i}"
        assert len(raw) <= WINDOW, f"{wat}: over {WINDOW} bytes"
        assert raw.count(b"\n") == 1, f"{wat}: not one line"
        assert raw.endswith(b"\n"), f"{wat}: no final LF"
        text = get(w, "text", str, wat)
        assert text, f"{wat}: field text empty"
        assert get(w, "source_id", str, wat) == sid, f"{wat}: field source_id"
        assert get(w, "index", int, wat) == i, f"{wat}: field index"
        assert get(w, "start_byte", int, wat) == len(out), f"{wat}: field start_byte"
        out += text.encode("utf-8", errors="surrogateescape")
        assert get(w, "end_byte", int, wat) == len(out), f"{wat}: field end_byte"
        spans.append((get(w, "start_line", int, wat), get(w, "end_line", int, wat)))
    return bytes(out), spans


def source(d: Mapping[str, object], at: str, seen: Path | None) -> Source:
    """D, one manifest entry; read in SEEN, its windows rebuilt to its snapshot's bytes, sha256,
    size and line count."""
    derived = d.get("kind") == "DERIVED"
    original = "" if derived else get(d, "original", str, at)
    size = 0 if derived else get(d, "bytes", int, at)
    sha, p = get(d, "sha256", str, at), obj(d.get("presentation"), f"{at} presentation")
    lines = None
    if "selected_lines" in d:
        lines = [
            get({"i": i}, "i", int, f"{at} selected_lines") for i in items(d, "selected_lines", at)
        ]
    elif "start_line" in d:
        lines = list(range(get(d, "start_line", int, at), get(d, "end_line", int, at) + 1))
    if seen is None:
        return Source(original, size, sha, windows=get(p, "count", int, at), lines=lines)
    data, spans = windows(p, seen, at)
    assert data == (seen / Path(get(d, "snapshot", str, at)).name).read_bytes(), f"{at}: windows"
    assert hashlib.sha256(data).hexdigest() == sha, f"{at}: field sha256"
    if derived:
        assert get(d, "captured_at", str, at), f"{at}: field captured_at"
    else:
        assert len(data) == size, f"{at}: field bytes"
        assert len(data.splitlines()) == get(d, "lines", int, at), f"{at}: field lines"
    return Source(original, size, sha, data, tuple(spans), get(p, "count", int, at), lines)


def manifest(raw: object, seen: Path | None = None) -> Manifest:
    """RAW, a manifest or a reflection line's inputs; read in SEEN (pi_agent.py's seen.WHO), every
    window rebuilt (source)."""
    d = obj(raw, "manifest")
    none: Mapping[str, object] = {}
    bind = obj(d["director"], "manifest director") if d.get("director") is not None else none
    srcs: dict[str, Source] = {}
    for x in items(d, "sources", "manifest"):
        e = obj(x, "manifest source")
        at = f"manifest source {get(e, 'identity', str, 'manifest source')}"
        if get(e, "available", bool, at):
            srcs[str(e["identity"])] = source(e, at, seen)
    derived = {k: source(obj(v, f"derived {k}"), f"derived {k}", seen)
               for k, v in obj(d.get("derived"), "manifest derived").items()}  # fmt: skip
    return Manifest(
        maybe(bind, "mode", "manifest director"),
        maybe(bind, "pane", "manifest director"),
        maybe(bind, "session", "manifest director"),
        maybe(obj(d.get("scope"), "manifest scope"), "lane", "manifest scope"),
        srcs,
        derived,
    )


class Shown(NamedTuple):
    argv: str
    brief: str
    inputs: Manifest


def shown(s: Scratch, who: str) -> Shown | None:
    """What WHO's reflector was shown in its last run (pi_agent.py's records, then removed), None
    when none ran since or its run was killed before its records were whole (argv.WHO, written
    last); the run's captured sources gone once it ended."""
    argv, brief, seen = (s.root / f"{n}.{who}" for n in ("argv", "prompt", "seen"))
    if not argv.exists():
        return None
    got = Shown(argv.read_text().replace("\0", "\n"), brief.read_text(),
                manifest(json.loads((seen / "manifest.json").read_text()), seen))  # fmt: skip
    run = next(x[22:] for x in got.brief.splitlines() if x.startswith("Read source manifest: "))
    assert not Path(run).parent.exists(), f"the run left its captured sources: {run}"
    argv.unlink()
    brief.unlink()
    shutil.rmtree(seen)
    return got


class Finding(NamedTuple):
    cls: str
    question: str
    route: str
    summary: str
    blocking: bool | None  # a lane reflection's: False; a director reflection's: none


class Reflection(NamedTuple):
    findings: int
    questions: list[str]
    inputs: Manifest


FINDING_FIELDS = ("class", "question", "route", "summary")
FINDING_KEYS = {"at", "kind", "source", *FINDING_FIELDS}


def finding(raw: str) -> Finding:
    """RAW, a log line, as a reflection's finding (spec comms #reflection-output)."""
    d = obj(json.loads(raw), "finding line")
    assert set(d) - {"blocking"} == FINDING_KEYS, f"finding line fields {sorted(d)}"
    assert (d["kind"], d["source"]) == ("finding", "reflection"), raw
    cls, q, route, summary = (get(d, k, str, "finding line") for k in FINDING_FIELDS)
    blocking = get(d, "blocking", bool, "finding line") if "blocking" in d else None
    return Finding(cls, q, route, summary, blocking)


def reflection(raw: str) -> Reflection:
    """RAW, a hand-off log line, as a reflection line, its inputs the run's manifest."""
    d = obj(json.loads(raw), "reflection line")
    assert d.get("kind") == "reflection", f"reflection line: field kind {d.get('kind')!r}"
    qs = [
        get({"q": q}, "q", str, "reflection line questions")
        for q in items(d, "questions", "reflection line")
    ]
    return Reflection(get(d, "findings", int, "reflection line"), qs, manifest(d.get("inputs")))


def appended(log: Path, before: int) -> tuple[list[Finding], Reflection]:
    """The lines one reflection appended to LOG after its first BEFORE lines: its findings, then
    its reflection line."""
    *fs, r = log.read_text().splitlines()[before:]
    return [finding(x) for x in fs], reflection(r)
