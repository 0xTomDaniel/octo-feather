"""The scenarios of tests/gate/kit/test_review_host.py (its items), this file their command
(testkit.main): scripts/review-host (issue #65) through its CLI, over the Spec Chat at its pin (the
Skillfile fetch-only entry, `check-vendored --extract spec-chat`, given as $SPEC_CHAT_CLONE; never
the box's clone, #96). Only --test rows in a scratch state dir with a space in its path.

`refusals` (no server starts): on a spawned pane's PATH (herdr-spawn over the testkit's Herdr
stand-in) review-host is the kit script and --help passes through; register refuses a page with no
Spec Chat runtime <script>, then one whose .viz/runtime.js is missing, registering nothing; a lane
key as --slug is refused (remote #review-one-row), exit 2, no row: gh230 for a GitHub target, eng-12
for a Linear one.

`servers` (e2e, quality #test-kinds: its purpose is Spec Chat's real review server working, on
loopback): re-registering at a new commit keeps the link, which answers 200 with the new version; a
lane-key slug on a live registry leaves it as it was; project and spec slugs, and gh230 on a Linear
target, register; a process that only names the registry (the reviewed repro, one passing the real
server path as a plain argument, one running another review-serve.py) is never stopped, even by a
register that then fails, and is reported; a real review-serve on the registry it does not own is
stopped; where review-host.py cannot see the live server (no /proc, as on macOS: register in a
user+mount namespace with /proc covered, the testkit's ps stand-in showing this scenario's own
processes only, as launched) the link holds and the old server is replaced, and a sleeper whose args
end with the exact launch text is left running and reported. Which servers run is proved through
what this scenario owns, never a process listing: it is the subreaper of every server review-host
starts (prctl PR_SET_CHILD_SUBREAPER), so a replaced server is reaped here (waitpid) and, at the
end, with the registry's own stopped, no server is left (waitpid until ECHILD); a lookalike or stray
is this scenario's own child, its handle saying whether it runs. Each wait is bounded by an alarm
that fails the item (never a pacing sleep)."""

from __future__ import annotations

import ctypes
import os
import re
import shutil
import signal
import subprocess
import sys
import urllib.request
from typing import TYPE_CHECKING

from testkit import HERE, ROOT, Scratch, kit, main

if TYPE_CHECKING:
    from pathlib import Path

TAG = "review-host test"
SCRIPT = '<script defer src="./.viz/runtime.js"></script>'
HOST = kit("review-host")
BOUND_S = 20  # a wait's failure bound, never a pacing delay


class World:
    def __init__(self, s: Scratch) -> None:
        self.s, self.t = s, s.root.resolve()
        t = self.t
        sc = t / "sc"
        # The pin cache is the caller's (`just vendored-fetch` fills it), never the scratch HOME's.
        cache = {k: os.environ[k] for k in ("HOME", "XDG_CACHE_HOME") if k in os.environ}
        s.run([kit("check-vendored"), "--extract", "spec-chat", str(sc)], env=cache)
        self.clone = sc.resolve()
        self.server = self.clone / "skill" / "review-spec" / "assets" / "review-serve.py"
        self.state = t / "state space"
        self.registry = self.state / "registry.toml"
        for k in ("HERDR_SESSION",):
            s.env.pop(k, None)
        s.env |= {
            "SPEC_CHAT_CLONE": str(self.clone),
            "XDG_STATE_HOME": str(t / "xdg"),
            "SPEC_CHAT_APPROVED_INGRESS_PORTS": "",  # loopback, any free port
        }
        s.identity()  # the commit identity a role launch needs (#665)
        self.repo = t / "repo"
        s.git(t, "-c", "init.defaultBranch=main", "init", "-q", str(self.repo))
        (self.repo / "docs" / "specs").mkdir(parents=True)

    def page(self, version: str, head: str, repo: Path | None = None) -> None:
        """The spec page showing VERSION in <h1>, HEAD in its <head>, committed."""
        r = repo or self.repo
        (r / "docs" / "specs" / "x.spec.html").write_text(
            f'<!doctype html><html><head>{head}</head><body><article class="spec"><h1>{version}'
            "</h1></article></body></html>\n"
        )
        self.s.git(r, "add", "-A")
        self.s.git(r, "commit", "-qm", version)

    def host(
        self, *args: str, env: dict[str, str] | None = None, wrap: list[str] | None = None
    ) -> tuple[int, str]:
        p = subprocess.run(
            [*(wrap or []), HOST, *args],
            cwd=self.repo,
            env={**self.s.env, **(env or {})},
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        return p.returncode, p.stdout

    def reg(
        self,
        spec: str = "docs/specs/x.spec.html",
        state: Path | None = None,
        env: dict[str, str] | None = None,
        wrap: list[str] | None = None,
    ) -> tuple[int, str]:
        st = str(state or self.state)
        args = ["register", "--state-dir", st, "--test", "--slug", "w65", "--owner", "test/w65"]
        return self.host(*args, "--base", "HEAD", spec, env=env, wrap=wrap)

    def slug(self, slug: str, state: Path, spec: str) -> tuple[int, str]:
        args = [
            "register",
            "--state-dir",
            str(state),
            "--test",
            "--slug",
            slug,
            "--owner",
            "test/w65",
        ]
        return self.host(*args, spec)


def link(out: str) -> str:
    m = re.search(r" URL: (http\S*) ", out)
    return m.group(1) if m else ""


def refusals(s: Scratch) -> None:
    w = World(s)
    try:
        refused(s, w)
    finally:  # a register that was not refused started a server: stopped
        for d in (w.state, w.t / "lanes"):
            w.host("stop", "--state-dir", str(d))


def refused(s: Scratch, w: World) -> None:
    t = w.t
    # 1. A spawned pane's PATH resolves review-host to the kit script; --help passes through.
    hb, world = t / "hbin", t / "herdr"
    hb.mkdir()
    world.mkdir()
    (hb / "herdr").symlink_to(HERE / "herdr.py")
    (t / "cwd").mkdir()
    spawn = str(ROOT / ".agents" / "skills" / "herdr-comms" / "assets" / "herdr-spawn")
    env = {
        "FAKE_HERDR": str(world),
        "PATH": f"{hb}{os.pathsep}{s.env['PATH']}",
        "XDG_CACHE_HOME": str(t / "cache"),
        "HERDR_PANE_ID": "w9:p0",
    }
    s.run(
        [
            spawn,
            "--workspace",
            "w9",
            "--name",
            "t1",
            "--role",
            "implementer",
            "--cwd",
            str(t / "cwd"),
        ],
        env=env,
    )
    made = [ln for ln in (world / "log").read_text().splitlines() if ln.startswith("tab create ")]
    m = re.search(r" --env PATH=(\S+)", made[0]) if made else None
    assert m, f"{TAG}: spawned pane got no PATH: {made}"
    pane_path = m.group(1)
    found = shutil.which("review-host", path=pane_path)
    assert found == HOST, f"{TAG}: review-host on the pane's PATH is {found}"
    r = s.run(["review-host", "--help"], env={"PATH": pane_path})
    assert re.search(r"usage: review-host\.py.*register", r.out, re.DOTALL), (
        f"{TAG}: --help: {r.out}"
    )
    # 2. Refused: no runtime <script>, then a <script> whose .viz/runtime.js is missing.
    w.page("v0", "")
    rc, out = w.reg()
    assert rc != 0, f"{TAG}: no <script>: registered: {out}"
    assert re.search(
        rf"no Spec Chat runtime <script>.*{re.escape(SCRIPT)}.*preflight\.py", out, re.DOTALL
    ), out
    assert not w.registry.exists(), f"{TAG}: no <script>: registered anyway"
    w.page("v0", SCRIPT)
    rc, out = w.reg()
    runtime = f"{w.repo}/docs/specs/.viz/runtime.js is missing; run python3 "
    assert rc != 0, f"{TAG}: no runtime.js: registered: {out}"
    assert runtime in out, f"{TAG}: no runtime.js not named: {out}"
    assert "preflight.py" in out, f"{TAG}: no runtime.js: no fix named: {out}"
    assert not w.registry.exists(), f"{TAG}: no runtime.js: registered anyway"
    # 3. A lane key as --slug: exit 2, no row (gh230 here, GitHub; eng-12 for a Linear target).
    lanes = t / "lanes"
    rc, out = w.slug("gh230", lanes, "docs/specs/x.spec.html")
    said = (
        "refused, --slug gh230 is a lane key (remote spec #review-one-row",
        "register with the spec's slug",
        "nothing registered",
    )
    assert rc == 2, f"{TAG}: lane key gh230: rc={rc} {out}"
    for x in said:
        assert x in out, f"{TAG}: lane key gh230 lacks {x}: {out}"
    lin = t / "linear"
    s.git(t, "-c", "init.defaultBranch=main", "init", "-q", str(lin))
    (lin / "docs" / "specs").mkdir(parents=True)
    (lin / ".octo-feather.toml").write_text('tracker = "linear"\n')
    w.page("v0", SCRIPT, lin)
    rc, out = w.slug("eng-12", lanes, f"{lin}/docs/specs/x.spec.html")
    assert rc == 2, f"{TAG}: linear lane key: rc={rc} {out}"
    assert "--slug eng-12 is a lane key" in out, f"{TAG}: linear lane key: {out}"
    assert not (lanes / "registry.toml").exists(), f"{TAG}: a lane key registered anyway"


class Owned:
    """This scenario as the subreaper of the servers review-host starts, and the processes it
    starts itself."""

    def __init__(self) -> None:
        libc = ctypes.CDLL(None, use_errno=True)
        assert libc.prctl(36, 1, 0, 0, 0) == 0, f"{TAG}: no subreaper (Linux only)"
        self.mine: dict[str, subprocess.Popen[bytes]] = {}

    def start(self, name: str, *argv: str) -> int:
        self.mine[name] = subprocess.Popen(
            list(argv), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True
        )
        return self.mine[name].pid

    def runs(self, name: str) -> bool:
        return self.mine[name].poll() is None

    def stop(self, name: str) -> None:
        p = self.mine.pop(name)
        os.killpg(p.pid, signal.SIGTERM)
        p.wait()

    @staticmethod
    def reaped(pid: int, what: str) -> None:
        """Server PID (this scenario's by reparenting) has exited, reaped here."""
        signal.alarm(BOUND_S)
        try:
            os.waitpid(pid, 0)
        except ChildProcessError:
            msg = f"{TAG}: {what}: server {pid} is not this scenario's to reap"
            raise AssertionError(msg) from None
        finally:
            signal.alarm(0)

    def none_left(self) -> None:
        """No process of this scenario is left: every server stopped (bounded)."""
        for name in list(self.mine):
            self.stop(name)
        signal.alarm(BOUND_S)
        try:
            while True:
                os.wait()
        except ChildProcessError:
            pass
        finally:
            signal.alarm(0)


def owned_pid(registry: Path) -> int:
    m = re.search(r"(?m)^pid = (\d+)$", registry.read_text())
    assert m, f"{TAG}: the registry records no server: {registry.read_text()}"
    return int(m.group(1))


def answers(url: str, version: str) -> None:
    with urllib.request.urlopen(url, timeout=BOUND_S) as r:  # noqa: S310 (loopback, our own server)
        body = r.read().decode()
        assert r.status == 200, f"{TAG}: {url} answered {r.status}"
    assert f"<h1>{version}</h1>" in body, f"{TAG}: {url} answered without {version}"


def timeout(_sig: int, _frame: object) -> None:
    msg = f"{TAG}: a server outlived its bound ({BOUND_S} s): not stopped"
    raise AssertionError(msg)


def servers(s: Scratch) -> None:
    signal.signal(signal.SIGALRM, timeout)
    w, own = World(s), Owned()
    try:
        live(s, w, own)
    finally:
        w.host("stop", "--state-dir", str(w.state))
        own.none_left()


def live(s: Scratch, w: World, own: Owned) -> None:
    t = w.t
    shutil.copytree(
        w.clone / "skill" / "review-spec" / "assets" / "viz", w.repo / "docs" / "specs" / ".viz"
    )
    w.page("v1", SCRIPT)
    rc, out = w.reg()
    first = link(out)
    assert rc == 0, f"{TAG}: register v1: {out}"
    assert first, f"{TAG}: register v1 printed no link: {out}"
    p1 = owned_pid(w.registry)
    w.page("v2", SCRIPT)
    rc, out = w.reg()
    assert rc == 0, f"{TAG}: register v2: {out}"
    assert link(out) == first, f"{TAG}: re-register moved the link: {first} -> {link(out)}"
    p2 = owned_pid(w.registry)
    if p2 != p1:
        own.reaped(p1, "re-register")
    answers(first, "v2")
    # A lane key on a live registry: refused, the registry and its server as they were.
    rc, out = w.slug("gh230", w.state, "docs/specs/x.spec.html")
    assert rc == 2, f"{TAG}: lane key gh230 on a live registry: rc={rc} {out}"
    assert '"gh230"' not in w.registry.read_text(), f"{TAG}: gh230 registered"
    assert owned_pid(w.registry) == p2, f"{TAG}: lane key gh230: the server changed"
    os.kill(p2, 0)  # still running (this scenario's child: no /proc read)
    # Project and spec slugs, and gh230 on a Linear target, pass.
    lanes = t / "lanes"
    lin = t / "linear"
    s.git(t, "-c", "init.defaultBranch=main", "init", "-q", str(lin))
    (lin / "docs" / "specs").mkdir(parents=True)
    (lin / ".octo-feather.toml").write_text('tracker = "linear"\n')
    shutil.copytree(w.repo / "docs" / "specs" / ".viz", lin / "docs" / "specs" / ".viz")
    w.page("l", SCRIPT, lin)
    for slug in ("octo-feather", "x", "implementer-gh230"):
        rc, out = w.slug(slug, lanes, "docs/specs/x.spec.html")
        assert rc == 0, f"{TAG}: slug {slug}: rc={rc} {out}"
        assert f'slug = "{slug}"' in (lanes / "registry.toml").read_text(), f"{TAG}: slug {slug}"
    rc, out = w.slug("gh230", lanes, f"{lin}/docs/specs/x.spec.html")  # no Linear lane key
    assert rc == 0, f"{TAG}: gh230 on a Linear target: rc={rc} {out}"
    lp = owned_pid(lanes / "registry.toml")
    rc, out = w.host("stop", "--state-dir", str(lanes))
    assert rc == 0, f"{TAG}: stop lanes server: {out}"
    own.reaped(lp, "stop of the lanes registry")
    lookalikes(w, own, first, p2)


def lookalikes(w: World, own: Owned, first: str, p2: int) -> None:
    """A process that only names this registry is never stopped, even by a register that then
    fails: the reviewed repro, one passing the real script path as a plain argument, one running
    another review-serve.py; then a real stray stopped; then no /proc."""
    t, reg, srv = w.t, str(w.registry), str(w.server)
    sleep = ("python3", "-c", "import time; time.sleep(3600)")
    other = t / "other" / "review-serve.py"
    other.parent.mkdir()
    other.write_text("import time\ntime.sleep(3600)\n")
    tail = ("--bind", "127.0.0.1", "--port", "1", "--host", "127.0.0.1")
    own.start("sleeper", *sleep, "review-serve.py", "--registry", reg)
    own.start("lookalike", *sleep, srv, "--registry", reg, *tail)
    own.start("otherscript", "python3", str(other), "--registry", reg, *tail)
    plain = t / "plain"  # the reviewed repro word for word: a state path without a space
    own.start("plainsleeper", *sleep, "review-serve.py", "--registry", f"{plain}/registry.toml")
    rc, out = w.reg("docs/specs/missing.spec.html", plain)
    assert rc != 0, f"{TAG}: register of a missing spec passed: {out}"
    assert own.runs("plainsleeper"), f"{TAG}: failing register stopped the repro sleeper: {out}"
    own.stop("plainsleeper")
    names = ("sleeper", "lookalike", "otherscript")
    rc, out = w.reg("docs/specs/missing.spec.html")
    assert rc != 0, f"{TAG}: register of a missing spec passed: {out}"
    for n in names:
        assert own.runs(n), f"{TAG}: failing register: {n} was stopped: {out}"
    w.page("v3", SCRIPT)
    rc, out = w.reg()
    assert rc == 0, f"{TAG}: register v3: {out}"
    assert link(out) == first, f"{TAG}: register v3 moved the link: {out}"
    for n in names:
        assert own.runs(n), f"{TAG}: register: {n} was stopped: {out}"
    n = len(re.findall(r"left pid .* running: it names", out))
    assert n == 3, f"{TAG}: lookalikes not reported ({n}): {out}"
    for n in names:
        own.stop(n)
    p3 = owned_pid(w.registry)
    if p3 != p2:
        own.reaped(p2, "register v3")
    answers(first, "v3")
    # A real review-serve on this registry that the registry does not own is stopped.
    stray = own.start(
        "stray",
        "python3",
        srv,
        "--registry",
        reg,
        "--bind",
        "127.0.0.1",
        "--port",
        "0",
        "--host",
        "127.0.0.1",
    )
    w.page("v4", SCRIPT)
    rc, out = w.reg()
    assert rc == 0, f"{TAG}: register v4: {out}"
    assert link(out) == first, f"{TAG}: register v4 moved the link: {out}"
    assert f"stopped review-serve pid {stray}," in out, f"{TAG}: stray {stray} not reported: {out}"
    signal.alarm(BOUND_S)
    own.mine.pop("stray").wait()  # stopped: its handle says so
    signal.alarm(0)
    p4 = owned_pid(w.registry)
    if p4 != p3:
        own.reaped(p3, "register v4")
    answers(first, "v4")
    no_proc(w, own, first, p4)


def server_row(w: World, python: str) -> str:
    """The ps row of the server this registry records (owned: its own register started it), as
    review-host.py launched it (its record's bind, port and host; review-host's interpreter)."""
    text = w.registry.read_text()

    def field(k: str) -> str:
        m = re.search(rf'(?m)^{k} = "?([^"\n]*)"?$', text)
        assert m, f"{TAG}: the registry records no {k}: {text}"
        return m.group(1)

    argv = [python, str(w.server), "--registry", str(w.registry.resolve())]
    argv += ["--bind", field("bind"), "--port", field("port"), "--host", field("host")]
    return f"{field('pid')} {' '.join(argv)}"


def no_proc(w: World, own: Owned, first: str, p4: int) -> None:
    """Where review-host.py cannot see its live server (no /proc, as on macOS), the link holds and
    the old server is replaced; a prefixed lookalike is left running and reported. The ps
    stand-in shows only this scenario's own processes (FAKE_PS_ROWS): the server the registry
    records and the lookalike this scenario started, each as launched; no process listing."""
    t = w.t
    psbin = t / "psbin"
    psbin.mkdir()
    (psbin / "ps").symlink_to(HERE / "ps.py")
    rows = t / "ps-rows"
    noproc = ["unshare", "-rm", "sh", "-c", 'mount -t tmpfs none /proc && exec "$@"', "sh"]
    probe = subprocess.run(
        [*noproc, "sh", "-c", "! test -e /proc/self"], capture_output=True, check=False
    )
    if probe.returncode != 0:
        sys.stdout.write(
            "review-host: no-/proc case skipped: unshare -rm cannot cover /proc here\n"
        )
        return
    path = f"{psbin}{os.pathsep}{w.s.env['PATH']}"
    env = {"FAKE_PS_ROWS": str(rows), "PATH": path}
    python = os.path.realpath(shutil.which("python3", path=path) or "python3")  # review-host's
    rows.write_text(server_row(w, python) + "\n")
    w.page("v5", SCRIPT)
    rc, out = w.reg(env=env, wrap=noproc)
    assert rc == 0, f"{TAG}: register v5 without /proc: {out}"
    assert link(out) == first, f"{TAG}: without /proc the link moved: {first} -> {link(out)}"
    p5 = owned_pid(w.registry)
    assert p5 != p4, f"{TAG}: without /proc the old server was not replaced"
    own.reaped(p4, "register v5 without /proc")
    answers(first, "v5")
    # The reviewed repro, last: a sleeper whose args end with the exact launch text, the real
    # interpreter path included, is left running and reported.
    reg, srv = str(w.registry), str(w.server)
    tail = ("--bind", "127.0.0.1", "--port", "1", "--host", "127.0.0.1")
    sleeper = ("python3", "-c", "import time; time.sleep(3600)")
    launch = (python, srv, "--registry", reg, *tail)
    pre = own.start("prefixed", *sleeper, *launch)
    planted = f"{pre} {' '.join((*sleeper, *launch))}"
    rows.write_text(f"{server_row(w, python)}\n{planted}\n")
    rc, out = w.reg("docs/specs/missing.spec.html", env=env, wrap=noproc)
    assert rc != 0, f"{TAG}: register of a missing spec without /proc passed: {out}"
    assert own.runs("prefixed"), (
        f"{TAG}: without /proc register stopped the prefixed sleeper: {out}"
    )
    assert f"left pid {pre} running: it names" in out, (
        f"{TAG}: prefixed sleeper not reported: {out}"
    )


if __name__ == "__main__":
    main(refusals, servers)
