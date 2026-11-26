"""The qc sandbox test's box (#508, #997): tests/qc.sh and each tests/qc-<section>.sh (their
scenarios: tests/gate/kit/qc_sections.py) run scripts/octo-feather-qc on it, no model.

offline() first: the item re-runs itself in a fresh user and network namespace (`unshare -cn`,
no route anywhere, proved), bounded as a whole by QC_TEST_TIMEOUT s (default 600), each qc run by
QC_TEST_RUN_TIMEOUT s (default 90): a hang fails naming what hung (#55). Needs unprivileged user
namespaces. A Box is then the item's world: a throwaway HOME holding a "live" box (a live Herdr
session, gh and git credentials, live and archived lanes, another repo, Pi's auth.json and
models.json), the judged test repo (its qc.toml declaring acceptance-a's demo, `pi qc-demo`: the
stand-in Pi's turn in FAKE_QC's mode, run in the demo's qc sandbox, and acceptance-b's, a failing
one), the reports dir, a per-run token, and run, report, jr, copycase and piok.

Stand-ins, only for systems the kit does not own: Pi, the testkit's pi_agent.py with FAKE_QC set
(its docstring: the turn per mode; the advisory's classify run gets it too); Herdr, the testkit's
herdr (FAKES), in a dir of its own
after the Pi's, as the pane case's real-Herdr mode (QC_TEST_HERDR=real, `just qc-real-herdr`)
takes it off PATH. Real: the qc sandbox, user namespaces, srt, mise, just (the kit's mise.lock
pin), git, gh (offline, so every call fails, as on the old box).
"""

from __future__ import annotations

import contextlib
import errno
import json
import os
import re
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn, Self

from testkit import FIXTURES, HERE, ROOT, Scratch, kit
from testkit.install_check import field
from testkit.jsonwalk import at

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from types import TracebackType

STATUS = "docs/specs/demo.status.json"
# The judged repo's contract (quality spec #qc-contract): acceptance-a's demo the stand-in Pi's
# turn, b's a failure.
DEMOS = (
    'format = 1\n[entry]\ncommand = "true"\n[services]\n[fixture]\n[values]\n'
    '[demo."demo#acceptance-a"]\ncommand = "pi qc-demo"\ncovers = ["src/a"]\n'
    'tests = ["tests/a.sh"]\n'
    '[demo."demo#acceptance-b"]\ncommand = "echo b broke >&2; exit 1"\ncovers = ["src/b"]\n'
    'tests = ["tests/b.sh"]\n'
)
PI = HERE / "pi_agent.py"


def fail(msg: str) -> NoReturn:
    sys.exit(f"qc test: {msg}")


def note(msg: str) -> None:
    sys.stderr.write(f"qc test: {msg}\n")


def offline() -> None:
    """The item offline and bounded (module docstring); on macOS it skips, exit 0. Returns inside
    the namespace, the no-route proof printed; TERM there exits 143 through the scenario's
    cleanup."""
    if sys.platform == "darwin":
        sys.stdout.write("qc: skipped, not on macOS (just qc needs Linux; CI runs it)\n")
        sys.exit(0)
    if not os.environ.get("QC_TEST_NETNS"):
        probe = ["unshare", "-cn", "true"]
        if subprocess.run(probe, capture_output=True, check=False).returncode:
            fail(
                "unshare -cn failed: the test runs offline in a user+network namespace "
                "(enable unprivileged user namespaces)"
            )
        lim = os.environ.get("QC_TEST_TIMEOUT", "600")
        cmd = ["timeout", "-k", "10", lim, "unshare", "-cn", sys.executable, *sys.argv]
        env = os.environ | {"QC_TEST_NETNS": "1"}
        rc = subprocess.run(cmd, env=env, check=False).returncode
        if rc in (124, 137):
            note(f"timed out after {lim} s (QC_TEST_TIMEOUT), killed")
        sys.exit(rc)
    for fam, addr in ((socket.AF_INET, "192.0.2.1"), (socket.AF_INET6, "2001:db8::1")):
        try:
            with socket.socket(fam, socket.SOCK_STREAM) as c:
                c.settimeout(2)
                c.connect((addr, 9))
        except OSError as e:
            if e.errno in (errno.ENETUNREACH, errno.EAFNOSUPPORT, errno.EADDRNOTAVAIL):
                continue
            fail(f"network reachable: the test must run with no route (unshare -cn): {addr}: {e}")
        fail(f"network reachable: the test must run with no route (unshare -cn): {addr}: connected")
    note("offline: no route to any network (user+network namespace)")
    why = "worktree overlay needs: scripts/octo-feather-qc-sandbox header"
    note(f"kernel {os.uname().release} ({why})")

    def term(_sig: int, _frame: object) -> None:  # timeout signals twice (child, group)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        sys.exit(143)

    signal.signal(signal.SIGTERM, term)


def mise_dir(d: str) -> str:
    """mise's D dir as mise reports it for the caller's HOME (`mise doctor --json`)."""
    cmd = ["mise", "doctor", "--json"]
    p = subprocess.run(cmd, capture_output=True, text=True, check=True)
    # Read through the testkit's one JSON walk (field on jsonwalk.at; why no schema library:
    # testkit/jsonwalk.py).
    return field(p.stdout, "mise doctor --json", "dirs", d)


def has(rx: str, text: str) -> bool:
    """Whether a line of TEXT holds RX (grep -q)."""
    return re.search(rx, text, re.MULTILINE) is not None


def procs() -> dict[int, str]:
    """Every process's cmdline, its args joined by a space (as pgrep -f reads it)."""
    got: dict[int, str] = {}
    for p in Path("/proc").iterdir():
        if p.name.isdigit():
            try:
                got[int(p.name)] = (
                    (p / "cmdline").read_bytes().rstrip(b"\0").replace(b"\0", b" ").decode()
                )
            except OSError:
                continue
    return got


def tree(d: Path) -> list[str]:
    """Every entry under D (find -printf '%P %s %m'), sorted."""
    out: list[str] = []
    for root, ds, fs in os.walk(d):
        for n in ds + fs:
            p = Path(root, n)
            st = p.lstat()
            out.append(f"{p.relative_to(d)} {st.st_size} {st.st_mode & 0o7777:o}")
    return sorted(out)


class Box:
    """One qc item's world (module docstring); its runs killed when the with block ends."""

    def __init__(self, s: Scratch) -> None:
        self.s, self.t, self.home = s, s.root, s.home
        self.lim = os.environ.get("QC_TEST_RUN_TIMEOUT", "90")
        self.pids: dict[str, int] = {}
        self.out = ""
        cache = os.environ.get("XDG_CACHE_HOME") or f"{os.environ['HOME']}/.cache"
        # The caller's warm check-vendored cache (#69).
        self.vc0 = Path(cache, "octo-feather", "skillfile")
        self.tok = f"{secrets.randbelow(2**32)}{os.getpid()}"  # survivors key on it
        self.live = self.home / ".local" / "state" / "octo-feather"
        agent = self.home / ".pi" / "agent"
        self.pa, self.pm = agent / "auth.json", agent / "models.json"
        self.repo = self.t / "repo"
        self.environ()
        self.lived_in()
        self.stand_ins()
        self.judged()

    def environ(self) -> None:
        """The scratch's env as the box's: the caller's Herdr, gh and XDG dirs unset, mise's dirs
        as mise reports them before HOME moves (the kit justfile pins them the same way: the
        sandbox finds the box's installs whether this test runs bare or through just), the box's
        tokens and parent route set, each judge's FAKE_QC_TOK the run's token."""
        env = self.s.env
        for k in ("FAKE_GH", "XDG_CONFIG_HOME", "XDG_STATE_HOME", "XDG_CACHE_HOME"):
            env.pop(k, None)
        for k in ("GH_CONFIG_DIR", "HERDR_SESSION", "HERDR_SOCKET_PATH", "HERDR_BIN_PATH"):
            env.pop(k, None)
        env.pop("HERDR_ENV", None)
        for d in ("data", "cache", "config"):
            v = f"MISE_{d.upper()}_DIR"
            env[v] = os.environ.get(v) or mise_dir(d)
        env |= {
            "OCTO_FEATHER_QC_DIR": str(self.t / "reports"),
            "LINEAR_API_KEY": "SECRET-linear-key",
            "GH_TOKEN": "SECRET-token",
            "OCTO_FEATHER_PARENT": "wX:p9",
            "HERDR_PANE_ID": "p9",
            "HERDR_TAB_ID": "t9",
            "HERDR_WORKSPACE_ID": "w9",
            "OCTO_FEATHER_SPEND_SPACE": "w9",
            "FAKE_QC_TOK": self.tok,
        }
        for k in ("AUTHOR", "COMMITTER"):
            env |= {f"GIT_{k}_NAME": "t", f"GIT_{k}_EMAIL": "t@t"}

    def lived_in(self) -> None:
        """HOME a "live" box: a live Herdr session, gh and git creds, live and archived lanes,
        another repo (#182), Pi's two credential files, their copies auth0 and models0 beside."""
        h, live = self.home, self.live
        for d in (h / ".config" / "herdr", h / ".config" / "gh", live / "lanes" / "archive"):
            d.mkdir(parents=True)
        (h / ".config" / "herdr" / "herdr.sock").write_text("default\n")
        (h / ".config" / "gh" / "hosts.yml").write_text("oauth_token: SECRET-gh\n")
        (h / ".git-credentials").write_text("https://x:SECRET-git@github.com\n")
        (live / "lanes" / "gh9.toml").write_text("LIVE\n")
        (live / "lanes" / "archive" / "gh1.toml").write_text("ARCHIVED\n")
        (live / "director.handoffs.jsonl").write_text('{"director":1}\n')
        (live / "director.toml").write_text('pane = "LIVE"\n')
        sib = h / "src" / "sib"
        sib.mkdir(parents=True)
        self.s.run(["git", "init", "-q", str(sib)])
        (sib / "notes.md").write_text("SIBSECRET\n")
        self.pa.parent.mkdir(parents=True)
        self.pa.write_text('{"k": "SECRET-pi-auth-0123456789", "exp": 1}\n')
        self.pa.chmod(0o600)
        self.pm.write_text('{"providers": {"p": {"apiKey": "SECRET-pi-models-0123456789"}}}\n')
        shutil.copy2(self.pa, self.t / "auth0")
        shutil.copy2(self.pm, self.t / "models0")

    def stand_ins(self) -> None:
        """PATH: the scratch bin (Pi's stand-in, the kit's just), Herdr's in a dir of its own, the
        kit's scripts, the caller's; gh the real one (offline). BASE: the same without Herdr's.
        The kit's just (its mise.lock pin), as the kit justfile puts it for `just test`: run bare,
        a caller may reach just only through mise's shim, which resolves no version in the judged
        test repo (no mise.toml) and fails closed. The sandbox Herdr mode for the pane test: the
        fake, on every box and in CI; the box's real herdr only on explicit opt-in
        (QC_TEST_HERDR=real), never by presence on PATH."""
        s, fh = self.s, self.t / "fakeherdr"
        fh.mkdir()
        (fh / "herdr").symlink_to(HERE / "herdr.py")
        for n in ("herdr", "pi", "gh"):
            (s.bin / n).unlink()
        (s.bin / "pi").symlink_to(PI)
        just = subprocess.run(
            ["mise", "-C", str(ROOT), "which", "just"],  # noqa: S607
            capture_output=True,
            text=True,
            check=True,
        )
        (s.bin / "just").symlink_to(just.stdout.strip())
        caller, scripts = os.environ["PATH"], str(ROOT / "scripts")
        self.base = os.pathsep.join([str(s.bin), scripts, caller])
        s.env["PATH"] = os.pathsep.join([str(s.bin), str(fh), scripts, caller])
        self.mode, self.real = os.environ.get("QC_TEST_HERDR", "fake"), ""
        if self.mode == "real":
            herdr = shutil.which("herdr", path=self.base)
            self.real = herdr or fail("QC_TEST_HERDR=real but no herdr on PATH")
        elif self.mode != "fake":
            fail(f"QC_TEST_HERDR must be fake or real, got '{self.mode}'")
        note(f"sandbox Herdr mode: {self.mode}{f' ({self.real})' if self.real else ''}")

    def judged(self) -> None:
        """The judged test repo: the good demo spec accepted, its status file initialized, then
        scratch/ ignored and the contract (DEMOS), each a commit; self.head that last one."""
        r = self.repo
        (r / "docs" / "specs").mkdir(parents=True)
        shutil.copy(FIXTURES / "spec-status" / "good" / "demo.spec.html", r / "docs" / "specs")
        self.git("init", "-q", "-b", "main", ".")
        self.git("add", "-A")
        self.git("commit", "-qm", "accepted")
        short = self.git("rev-parse", "--short", "HEAD")
        spec = kit("octo-feather-spec-status")
        self.s.run([spec, "init", "docs/specs/demo.spec.html", short], cwd=r)
        (r / ".gitignore").write_text("scratch/\n")
        (r / "qc.toml").write_text(DEMOS)
        self.git("add", "-A")
        self.git("commit", "-qm", "spec")
        self.head = self.git("rev-parse", "HEAD")

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self, _t: type[BaseException] | None, _e: BaseException | None, _tb: TracebackType | None
    ) -> None:
        """Every process group started here stopped: TERM, up to 5 s (a Herdr server writes its
        snapshot as it exits), then KILL."""
        for g in self.pids.values():
            try:
                os.killpg(g, signal.SIGTERM)
            except OSError:
                continue
            for _ in range(50):
                try:
                    os.killpg(g, 0)
                except OSError:
                    break
                time.sleep(0.1)
            with contextlib.suppress(OSError):
                os.killpg(g, signal.SIGKILL)

    def git(self, *args: str) -> str:
        return self.s.run(["git", *args], cwd=self.repo).out

    def bounded(
        self, cmd: Sequence[str], env: Mapping[str, str] | None = None, unset: Sequence[str] = ()
    ) -> tuple[int, str]:
        """CMD in the repo, killed after QC_TEST_RUN_TIMEOUT s: its exit (124/137: it hung) and its
        stdout and stderr together. timeout gives the run its own process group, so a killed test
        reaches it only through the with block's end, which reclaims its scratch first."""
        e = {k: v for k, v in (self.s.env | dict(env or {})).items() if k not in unset}
        p = subprocess.Popen(
            ["timeout", "-k", "5", self.lim, *cmd],  # noqa: S607
            cwd=self.repo,
            env=e,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        self.pids["run"] = p.pid
        out = p.communicate()[0].decode(errors="replace").rstrip("\n")
        del self.pids["run"]
        return p.returncode, out

    def hung(self, rc: int, what: str, out: str) -> None:
        if rc in (124, 137):
            fail(f"{what} hung: no exit after {self.lim} s (QC_TEST_RUN_TIMEOUT), killed: {out}")

    def run(
        self,
        want: int,
        mode: str,
        *args: str,
        env: Mapping[str, str] | None = None,
        unset: Sequence[str] = (),
    ) -> str:
        """`octo-feather-qc ARGS` at self.head (a passed demo's status commit undone: never carried)
        with the demo in MODE (FAKE_QC); fails unless it exits WANT. Its output, kept as
        self.out."""
        self.git("reset", "-q", "--hard", self.head)
        rc, self.out = self.bounded(
            [kit("octo-feather-qc"), *args], {**(env or {}), "FAKE_QC": mode}, unset
        )
        what = f"FAKE_QC={mode} '{' '.join(args)}'"
        self.hung(rc, what, self.out)
        if rc != want:
            fail(f"{what} want exit {want}, got {rc}: {self.out}")
        return self.out

    def report(self, *keys: str | int) -> object:
        """The newest report's value at KEYS."""
        newest = max((self.t / "reports").glob("*.json"), key=lambda p: p.stat().st_mtime)
        return at(json.loads(newest.read_text()), *keys)

    def jr(self, *keys: str) -> object:
        """KEYS of acceptance-a's demo sandbox record in the newest report (its capture)."""
        return self.report("captures", 0, "sandbox", *keys)

    def started(self) -> bool:
        """Whether acceptance-a's demo ran, by the newest report (its capture's exit)."""
        caps = self.report("captures")
        ran = caps != [] and self.report("captures", 0, "exit") is not None
        return isinstance(caps, list) and ran

    def demo_out(self) -> str:
        """The demo's stdout and stderr, from its evidence record (the newest report names it)."""
        rid = self.report("captures", 0, "record")
        ev = [
            kit("octo-feather-evidence"),
            "read",
            "--repo",
            ".",
            "--criterion",
            "demo#acceptance-a",
        ]
        found = json.loads(self.s.run([*ev, "--json"], cwd=self.repo).out)
        d = Path(next(str(x["dir"]) for x in found if at(x, "record", "id") == rid)) / "outputs"
        return (d / "demo.stdout").read_text() + (d / "demo.stderr").read_text()

    def copycase(self, mode: str, *gone: str) -> None:
        """One demo run in MODE, its credential copies GONE gone, the worktree pristine and no Pi
        credential left (tests/qc-copies.sh, tests/qc-oauth.sh)."""
        self.run(0, mode, STATUS, "5", "acceptance-a")
        for f in gone:
            if (self.repo / f).exists():
                fail(f"{mode}: credential copy {f} survived")
        st = self.git("status", "--porcelain", "--ignored")
        if st:
            fail(f"{mode}: worktree not pristine: {st}")
        left = [str(p) for d in (self.repo, self.home) for p in secret_files(d)]
        if left:
            fail(f"{mode}: a Pi credential survived: {' '.join(left)}")
        n = self.jr("discarded_writes")
        note(f"{mode}: {' '.join(gone)} discarded with the run ({n} writes), exit 0")

    def piok(self, name: str) -> None:
        """The box's Pi files untouched since auth0, models0, never written back."""
        agent = self.pa.parent
        names = sorted(p.name for p in agent.iterdir())
        if names != ["auth.json", "models.json"] or self.pa.stat().st_mode & 0o777 != 0o600:
            fail(f"{name}: Pi dir holds a stray file or auth.json mode changed: {names}")
        same = self.pa.read_bytes() == (self.t / "auth0").read_bytes()
        if not (same and self.pm.read_bytes() == (self.t / "models0").read_bytes()):
            fail(f"{name}: box auth.json or models.json changed (never written back)")
        if "auth_writeback" in self.out + repr(self.jr()):
            fail(f"{name}: auth_writeback still reported")

    def left(self, rx: str) -> list[str]:
        """Each process whose whole cmdline matches RX (pgrep -fx)."""
        return [c for c in procs().values() if re.fullmatch(rx, c)]

    def servers_left(self) -> list[int]:
        """Each Herdr stand-in server (testkit herdr.py's `sleep 600`) this item's runs started
        still alive: its environ holds this run's FAKE_QC_TOK, as every process the sandbox
        starts inherits it, so a concurrent item's server never counts."""
        mark = f"FAKE_QC_TOK={self.tok}".encode()
        got: list[int] = []
        for pid, c in procs().items():
            if c != "sleep 600":
                continue
            try:
                env = Path(f"/proc/{pid}/environ").read_bytes().split(b"\0")
            except OSError:
                continue
            if mark in env:
                got.append(pid)
        return got


def secret_files(d: Path) -> list[Path]:
    """Files under D holding SECRET-pi, any dir named .pi skipped (grep -rla --exclude-dir=.pi)."""
    hits: list[Path] = []
    for root, ds, fs in os.walk(d):
        ds[:] = [x for x in ds if x != ".pi"]
        for n in fs:
            p = Path(root, n)
            try:
                if not p.is_symlink() and b"SECRET-pi" in p.read_bytes():
                    hits.append(p)
            except OSError:
                continue
    return hits
