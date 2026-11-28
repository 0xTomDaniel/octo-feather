"""The qc sandbox test's sections, one scenario each (#508, #997): each tests/qc*.sh gate item runs
one as this file's command, so the items keep their ids and kinds, and each item's header lists the
facts its scenario proves. Every scenario but creds runs offline and bounded on the box of
testkit/qc_box.py (offline(), then a Box); creds, tests/qc-creds.sh, runs `just qc` on its own
scratch target. A failed fact fails naming it, with the run's output."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from typing import cast

from testkit import FIXTURES, ROOT, Scratch, kit, main
from testkit.qc import MODEL, RID
from testkit.qc_box import PI, STATUS, Box, at, fail, has, note, offline, tree

A = ("5", "acceptance-a")


def say(line: str) -> None:
    sys.stdout.write(line + "\n")


def copies(s: Scratch) -> None:
    """tests/qc-copies.sh."""
    with Box(s) as b:
        # Credential copies cannot survive anywhere: every judge write (ignored scratch/, .git, any
        # size, a copy of an intermediate auth.json between two refreshes, token values alone)
        # lives in the overlay and dies with the run.
        b.copycase("copycreds", "scratch/a", ".git/m")
        b.copycase("bigcopy", "scratch/big")
        # The judge rewrites both Pi files: its per-run copies, discarded; the box files
        # byte-identical; no OAuth warning.
        b.copycase("rewrite")
        b.piok("rewrite")
        if "OAuth" in b.out:
            fail(f"rewrite: OAuth warning without OAuth credentials: {b.out}")
        # A token refresh in place (intermediate copies anywhere discarded): discarded too.
        b.copycase("refresh", "scratch/oldauth", ".git/oldauth", str(b.home / "oldauth"))
        b.piok("refresh")
        if not has(r"qc sandbox: ok   writable persistent paths: none$", b.out):
            fail(f"proof must say writable persistent paths: none: {b.out}")
        b.copycase("token", "scratch/tok", ".git/tok2")
        b.piok("token")
    say(
        "qc-copies: ok (no persistent write: credential copies: >64 MiB, intermediate refresh, "
        "token only, HOME; auth.json and models.json: per-run copies rewritten, box files "
        "unchanged; offline, runs bounded)"
    )


def status(s: Scratch) -> None:
    """tests/qc-status.sh: --no-sandbox, and the status file's one commit, through the declared
    demos (ADR 0035)."""
    with Box(s) as b:
        before = b.git("rev-parse", "HEAD")
        # --no-sandbox: printed, report written, status never changes.
        b.run(1, "mixed", STATUS, "5", "acceptance-a", "acceptance-b", "--no-sandbox")
        if "UNSANDBOXED" not in b.out:
            fail(f"--no-sandbox not printed: {b.out}")
        if b.git("rev-parse", "HEAD") != before or b.git("status", "--porcelain"):
            fail("--no-sandbox changed the status file")
        if b.report("sandbox") is not False:
            fail("--no-sandbox report must record sandbox false")
        flipped(b, before)
    say(
        "qc-status: ok (--no-sandbox, pass flips built, fail stays planned, status-only commit; "
        "offline, runs bounded)"
    )


def flipped(b: Box, before: str) -> None:
    """A passed criterion becomes built and a failed one stays planned, in one status-only
    commit."""
    b.run(1, "mixed", STATUS, "5", "acceptance-a", "acceptance-b")  # a's demo passes, b's fails
    c = at(json.loads((b.repo / STATUS).read_text()), "criteria")
    a = dict(cast("dict[str, object]", at(c, "acceptance-a")))
    # built from its demo: its record, captured at the judged head, the demo's declared tests
    rec = a.pop("record", "")
    assert isinstance(rec, str), c
    assert re.fullmatch(r"\d{8}T\d{6}Z-[0-9a-f]{8}", rec), c
    assert a == {"status": "built", "pr": 5, "commit": before, "tests": ["tests/a.sh"]}, c
    assert at(c, "acceptance-b") == {"status": "planned", "pr": None}, c
    diff = b.git("diff", "--name-only", before, "HEAD")
    if diff != STATUS or b.git("rev-list", "--count", f"{before}..HEAD") != "1":
        fail("expected one commit touching only the status file")


def wheel(links: Path) -> None:
    """A one-file wheel qcw 0.1 in LINKS (zipfile: no build backend, no network)."""
    files = {
        "qcw/__init__.py": "X = 1\n",
        "qcw-0.1.dist-info/METADATA": "Metadata-Version: 2.1\nName: qcw\nVersion: 0.1\n",
        "qcw-0.1.dist-info/WHEEL": (
            "Wheel-Version: 1.0\nGenerator: t\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
        ),
    }

    def h(v: str) -> str:
        return base64.urlsafe_b64encode(hashlib.sha256(v.encode()).digest()).rstrip(b"=").decode()

    with zipfile.ZipFile(links / "qcw-0.1-py3-none-any.whl", "w") as z:
        for k, v in files.items():
            z.writestr(k, v)
        record = "".join(f"{k},sha256={h(v)},{len(v)}\n" for k, v in files.items())
        z.writestr("qcw-0.1.dist-info/RECORD", record + "qcw-0.1.dist-info/RECORD,,\n")


def manifest(r: Path) -> list[str]:
    """Every entry under R: a link's target, a dir, a file's sha256."""
    out: list[str] = []
    for d, ds, fs in sorted(os.walk(r)):
        ds.sort()
        for n in sorted(ds + fs):
            q = Path(d, n)
            rel = os.path.relpath(q, r)
            if q.is_symlink():
                out.append(f"link {rel} {q.readlink()}")
            elif q.is_dir():
                out.append(f"dir {rel}")
            else:
                out.append(f"file {rel} {hashlib.sha256(q.read_bytes()).hexdigest()}")
    return out


def uv_project(b: Box) -> Path:
    """The kit's uv (its mise.lock pin) first on PATH, as the kit justfile puts it (the judged test
    repo has no mise.toml, so mise's shim would resolve no version there), uv's cache dir the
    masked HOME's; a project locking a one-file wheel from a find-links dir, synced on the host,
    the wheel then removed: from here the package is only in uv's cache. The project's dir."""
    env = b.s.env
    p = subprocess.run(
        ["mise", "which", "uv"],  # noqa: S607
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    uvb = p.stdout.strip() if p.returncode == 0 else shutil.which("uv", path=env["PATH"])
    if not uvb:
        fail("no uv: the uv-cache case needs it")
    env["PATH"] = f"{Path(uvb).parent}{os.pathsep}{env['PATH']}"
    uc = b.s.run(["uv", "--color", "never", "cache", "dir"]).out
    if uc != f"{b.home}/.cache/uv":
        fail(f"uv cache dir {uc}, want {b.home}/.cache/uv (the masked cache dir)")
    pj = b.home / "uvp"
    (pj / "links").mkdir(parents=True)
    wheel(pj / "links")
    (pj / "pyproject.toml").write_text(
        '[project]\nname = "p"\nversion = "0"\nrequires-python = ">=3.11"\n'
        f'dependencies = ["qcw"]\n[tool.uv]\npackage = false\nfind-links = ["{pj}/links"]\n'
    )
    venv0 = {"UV_PROJECT_ENVIRONMENT": str(b.t / "venv0")}
    for cmd, e in (
        (["uv", "lock", "--offline", "--quiet"], {}),
        (["uv", "sync", "--locked", "--offline", "--quiet"], venv0),
    ):
        if subprocess.run(cmd, cwd=pj, env=env | e, capture_output=True, check=False).returncode:
            fail("host: uv lock and sync of the local wheel failed")
    for w in (pj / "links").glob("*.whl"):
        w.unlink()
    shutil.rmtree(b.t / "venv0")
    return pj


def uv_cache(s: Scratch) -> None:
    """tests/qc-uv-cache.sh."""
    with Box(s) as b:
        pj = uv_project(b)
        uc = Path(b.home / ".cache" / "uv")
        m0 = manifest(uc)
        if not m0:
            fail("empty host uv cache")
        b.run(0, "uvcache", STATUS, *A, env={"QC_UVP": str(pj)})
        j = b.demo_out()
        if not all(x in j.splitlines() for x in ("UVSYNC exit 0", "UVIMPORT 1", "UVWRITE exit 0")):
            fail(f"in the sandbox: want an offline uv sync from the cache and a write into it: {j}")
        rx = (
            rf"^qc sandbox: ok   uv cache {re.escape(str(uc))} is an overlay, upper dir (/\S+) "
            r"on the run tmpfs and hidden from the judge .*"
        )
        up = re.search(rx, b.out, re.MULTILINE)
        if not up or not has(r"qc sandbox: ok   writable persistent paths: none$", b.out):
            fail(f"no uv cache overlay proof: {b.out}")
        m1 = manifest(uc)
        if m1 != m0:
            fail(f"the host uv cache changed: {sorted(set(m0) ^ set(m1))[:5]}")
        if Path(up.group(1)).exists():
            fail(f"the overlay upper dir {up.group(1)} outlived the run")
    say(
        "qc-uv-cache: ok (uv's cache an overlay in the sandbox: offline uv sync from it and a "
        "write into it succeed; the host cache byte-identical, the upper dir gone; offline, runs "
        "bounded)"
    )


def mise(s: Scratch) -> None:
    """tests/qc-mise.sh."""
    k = re.escape(str(ROOT))
    with Box(s) as b:
        # mise in the sandbox (#437, docs/adr/0022): a bare just call through mise's shim with HOME
        # moved runs, the caller's first pi beating ~/.local/bin's.
        b.run(0, "misepath", STATUS, *A)
        j = b.demo_out()
        if not (has("MISEPATH exit 0", j) and has("MISEPATH stub first", j)):
            fail(f"mise's just shim in the sandbox: {j}")
        # The tools judged, each dir's own config only: the test repo pins none, the kit its
        # mise.toml's (#493 AC3).
        data = re.escape(s.env["MISE_DATA_DIR"])
        rx = (
            r"^qc sandbox: ok   mise offline, auto-install off; tools of the worktree and the kit "
            rf"installed in {data}; judged, each from its own mise config only: [^;]+: none; "
            rf"{k}: ([^ ;]+@[^ ;]+ )*just@[0-9.]+( [^ ;]+@[^ ;]+)*$"
        )
        if not has(rx, b.out):
            fail(f"no mise proof: {b.out}")
        # A tool not installed fails at its shim with no install.
        b.run(0, "misemissing", STATUS, *A)
        j = b.demo_out()
        if has("ESCAPE|MISSING", j):
            fail(f"missing mise tool: {j}")
        if not has("NOTINSTALLED exit [1-9]", j):
            fail(f"a tool not installed ran through its shim: {j}")
        # A caller whose HOME holds no mise installs (its dirs not pinned) fails the proof naming
        # `mise install --locked`, the judge never started. XDG_DATA_HOME too: mise falls back
        # to XDG_DATA_HOME/mise, so a caller exporting it kept its installs (env-coupled, #422
        # item 10).
        unset = ("MISE_DATA_DIR", "MISE_CACHE_DIR", "MISE_CONFIG_DIR", "XDG_DATA_HOME")
        b.run(66, "mixed", STATUS, *A, unset=unset)
        rx = (
            r"qc sandbox: FAIL mise offline, auto-install off; tools of the worktree and the kit "
            rf"installed in {re.escape(str(b.home))}/\.local/share/mise \(NOT installed: {k}: "
            r".*just@.*; the sandbox installs nothing: run outside it: "
            rf".*octo-feather-mise-install {k}\)"
        )
        if not has(rx, b.out):
            fail(f"no mise installs: the proof did not fail naming mise install --locked: {b.out}")
        wrote = [b.home / ".local/share/mise/installs", b.home / ".cache/mise"]
        if any(p.exists() for p in wrote):
            fail(f"the run wrote mise installs or cache: {[str(p) for p in wrote if p.exists()]}")
    say(
        "qc-mise: ok (mise's just shim, a tool not installed, no installs refused; offline, runs "
        "bounded)"
    )


OAUTH = "qc: warning: auth.json has OAuth credentials: a token refresh during this run is discarded"


def oauth(s: Scratch) -> None:
    """tests/qc-oauth.sh."""
    with Box(s) as b:
        # OAuth credentials on the box (type oauth, or only a refresh token field): one warning
        # line, the run proceeds.
        plain = b.pa.read_bytes()
        for a in (
            (
                '{"anthropic": {"type": "oauth", "refresh": "SECRET-pi-oauth-r", '
                '"access": "SECRET-pi-oauth-a", "expires": 1}}'
            ),
            '{"p": {"refresh_token": "SECRET-pi-oauth-r"}}',
        ):
            b.pa.write_text(a + "\n")
            shutil.copy2(b.pa, b.t / "auth0")
            b.copycase("rewrite")
            b.piok("oauth")
            if b.out.splitlines().count(OAUTH) != 1:
                fail(f"oauth: want one warning line: {b.out}")
            if "SECRET-pi-oauth" in b.out:
                fail(f"oauth: credential value printed: {b.out}")
        b.pa.write_bytes(plain)
        venv(b)
    say(
        "qc-oauth: ok (OAuth warned once, never written back; an ignored .venv removed and "
        "recreated in the overlay, discarded; offline, runs bounded)"
    )


def venv(b: Box) -> None:
    """#395: removing an ignored directory the real worktree holds (a .venv with a nested dir and
    file) succeeds in the overlay (userxattr: whiteouts and opaque dirs on the tmpfs upper), and
    recreating it works; all discarded."""
    r = b.repo
    with (r / ".git" / "info" / "exclude").open("a") as f:
        f.write(".venv/\n")
    (r / ".venv" / "lib" / "x.dist-info").mkdir(parents=True)
    (r / ".venv" / "lib" / "x.dist-info" / "RECORD").write_text("real\n")
    b.run(0, "venv", STATUS, *A)
    j = b.demo_out()
    if not (has("VENV rm exit 0", j) and has("VENV recreated", j)):
        fail(f"venv: removing an ignored lower dir failed in the sandbox: {j}")
    dw = b.jr("discarded_writes")
    if not (isinstance(dw, int) and dw > 0):
        fail(f"venv: want the writes discarded: {b.jr()}")
    n = sum(1 for _ in (r / ".venv").rglob("*")) + 1
    kept = (r / ".venv/lib/x.dist-info/RECORD").read_text() == "real\n"
    if not (kept and n == 4 and not b.git("status", "--porcelain")):
        fail("venv: real worktree changed")
    note(f"venv: rm -rf of an ignored lower dir exits 0, recreated, {dw} writes discarded")


def vendored(s: Scratch) -> None:
    """tests/qc-vendored.sh."""
    with Box(s) as b:
        # A warm vendored-skill cache (#69): bound back read-only after the cache tmpfs, so `just
        # check` in the sandbox reaches check-vendored green; the proof names the bind; the judge
        # cannot write it.
        if not ((b.vc0 / "git").is_dir() and (b.vc0 / "bin").is_dir()):
            fail(f"no warm check-vendored cache at {b.vc0}: run just vendored-fetch")
        vc = b.home / ".cache" / "octo-feather" / "skillfile"
        vc.parent.mkdir(parents=True)
        s.run(["cp", "-a", str(b.vc0), str(vc)])
        v0 = tree(vc)
        b.run(0, "vendored", STATUS, *A)
        j = b.demo_out()
        if has("ESCAPE|MISSING", j):
            fail(f"vendored cache: {j}")
        if "VENDORED green" not in j:
            fail(f"check-vendored not green in the sandbox: {j}")
        ro = f"qc sandbox: ok   vendored-skill cache {vc} bound read-only"
        if not (ro in b.out and has(r"qc sandbox: ok   writable persistent paths: none$", b.out)):
            fail(f"no read-only cache proof: {b.out}")
        if tree(vc) != v0:
            fail("the judge changed the vendored-skill cache")
        shutil.rmtree(b.home / ".cache")
        trust(b)
    say(
        "qc-vendored: ok (vendored cache read-only (check-vendored green, writes refused), "
        "new-repo's mise trust in an empty per-run state dir; offline, runs bounded)"
    )


def trust(b: Box) -> None:
    """#428: new-repo in the sandbox, mise's state dir pinned (as the kit justfile pins it) to a
    path the sandbox makes read-only: its `mise trust` lands in a per-run state dir on the run's
    /tmp, named by the proof; nothing persists. The per-run dir starts empty: the caller's trust
    entry for another repo never reaches the judge."""
    if not shutil.which("mise", path=b.s.env["PATH"]):
        fail("no mise on PATH: the new-repo case proves its mise trust in the sandbox")
    ms = b.home / ".local" / "state" / "mise"
    (ms / "trusted-configs").mkdir(parents=True)
    (ms / "trusted-configs" / "src-sib-0123456789abcdef").symlink_to(b.home / "src" / "sib")
    b.run(0, "newrepo", STATUS, *A, env={"MISE_STATE_DIR": str(ms)})
    j = b.demo_out()
    if not (has("NEWREPO exit 0", j) and has(r"mise\.toml trusted \(that file only\)", j)):
        fail(f"new-repo in the sandbox: {j}")
    rx = r"qc sandbox: ok   mise state dir per-run: /tmp/.* started empty: 0 entries"
    if not (has(rx, b.out) and has(r"qc sandbox: ok   writable persistent paths: none$", b.out)):
        fail(f"no per-run mise state proof: {b.out}")
    kept = sorted(p.name for p in (ms / "trusted-configs").iterdir())
    if kept != ["src-sib-0123456789abcdef"]:
        fail(f"the run's mise trust persisted: {kept}")
    shutil.rmtree(ms)


# tests/qc-creds.sh's world: its env unset, its demo's command (it tries to read both Pi files).
CREDS_UNSET = (
    "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "GH_CONFIG_DIR", "HERDR_SESSION", "HERDR_SOCKET_PATH",
    "HERDR_BIN_PATH", "HERDR_ENV", "OCTO_FEATHER_QC_DIR", "PI_CODING_AGENT_DIR", "STUB_KIT",
    "STUB_WANT", "STUB_CONFIDENCE", "FAKE_GH",
)  # fmt: skip
DEMO = (
    "for f in auth.json models.json; do "
    'cat "$HOME/.pi/agent/$f" && exit 1; done; echo neither readable'
)
ADVISORY = (
    "  advisory model judgment (no gate reads it): shows, confidence 0.910 "
    f"(criterion-evidence by {MODEL}; uncalibrated)"
)


def grep_a(out: str, first: str, n: int) -> list[str]:
    """The line of OUT first matching FIRST (a regex, at the line's start) and N after (grep -A)."""
    ls = out.splitlines()
    i = next((i for i, x in enumerate(ls) if re.match(first, x)), None)
    return [] if i is None else ls[i : i + n + 1]


class Creds:
    """tests/qc-creds.sh's scratch target, its runs of `just qc` through the kit justfile with
    the testkit's herdr and its Pi stand-in (FAKE_QC=creds); gh the real one, as
    the old box had it. The owner's credentials: an OAuth entry (qc warns once its refresh would
    be discarded) and a provider key."""

    def __init__(self, s: Scratch) -> None:
        self.s, t, env = s, s.root, s.env
        for k in CREDS_UNSET:
            env.pop(k, None)
        env |= {"XDG_STATE_HOME": str(t / "state"), "STUB_ANSWER": "shows", "FAKE_QC": "creds"}
        for k in ("AUTHOR", "COMMITTER"):
            env |= {f"GIT_{k}_NAME": "t", f"GIT_{k}_EMAIL": "t@t"}
        env["PATH"] = os.pathsep.join([str(s.bin), str(ROOT / "scripts"), os.environ["PATH"]])
        for n in ("pi", "gh"):
            (s.bin / n).unlink()
        (s.bin / "pi").symlink_to(PI)
        agent = s.home / ".pi" / "agent"
        agent.mkdir(parents=True)
        self.pa, self.pm = agent / "auth.json", agent / "models.json"
        self.pa.write_text(
            '{"anthropic": {"type": "oauth", "refresh": "SECRET-pi-oauth-r", '
            '"access": "SECRET-pi-oauth-a", "expires": 1}}\n'
        )
        self.pa.chmod(0o600)
        self.pm.write_text('{"providers": {"p": {"apiKey": "SECRET-pi-models-0123456789"}}}\n')
        self.auth0, self.models0 = self.pa.read_bytes(), self.pm.read_bytes()
        self.jf = str(ROOT / "justfile")
        self.repo = t / "repo"
        self.head = ""

    def recipe_pi(self) -> None:
        """The fake, never the box's pi, is the pi a recipe resolves (a real one would reach a
        model): checked before any run."""
        rpath = self.s.run(["just", "--justfile", self.jf, "--evaluate", "PATH"]).out
        rp = shutil.which("pi", path=rpath)
        say(f"qc-creds: recipe pi: {rp}")
        if rp != str(self.s.bin / "pi"):
            fail(f"a recipe resolves pi to {rp}, not the fake {self.s.bin / 'pi'}: nothing run")

    def git(self, *a: str) -> str:
        return self.s.run(["git", *a], cwd=self.repo).out

    def target(self) -> None:
        """The demo spec accepted, its status initialized, qc.toml declaring acceptance-a's demo."""
        r = self.repo
        (r / "docs" / "specs").mkdir(parents=True)
        self.git("init", "-q", "-b", "main", ".")
        self.git("commit", "-qm", "accepted", "--allow-empty")
        shutil.copy(FIXTURES / "spec-status" / "good" / "demo.spec.html", r / "docs" / "specs")
        self.git("add", "-A")
        self.git("commit", "-qm", "spec")
        short = self.git("rev-parse", "--short", "HEAD")
        spec = kit("octo-feather-spec-status")
        self.s.run([spec, "init", "docs/specs/demo.spec.html", short], cwd=r)
        (r / "qc.toml").write_text(
            'format = 1\n[entry]\ncommand = "true"\n[services]\n[fixture]\n[values]\n'
            f"[demo.\"demo#acceptance-a\"]\ncommand = '{DEMO}'\n"
            'covers = ["src/a"]\ntests = ["tests/a.sh"]\n'
        )
        self.git("add", "-A")
        self.git("commit", "-qm", "contract")
        self.head = self.git("rev-parse", "HEAD")

    def qc(self, *args: str, want: int = 0) -> tuple[str, str, Path]:
        """`just qc STATUS 9 ARGS` at the head, bounded at 180 s: its stdout, its stderr, its
        report; the box's Pi files unchanged."""
        self.git("reset", "-q", "--hard", self.head)
        cmd = ["timeout", "-k", "5", "180", "just", "--justfile", self.jf, "qc", STATUS, "9", *args]
        p = subprocess.run(
            cmd, cwd=self.repo, env=self.s.env, capture_output=True, text=True, check=False
        )
        out, err = p.stdout.rstrip("\n"), p.stderr
        tail = "\n".join(err.splitlines()[-20:])
        if p.returncode in (124, 137):
            fail(f"qc hung: {tail}")
        if p.returncode != want:
            fail(f"{' '.join(args)}: want exit {want}, got {p.returncode}: {out} {tail}")
        reps = (self.s.root / "state" / "octo-feather" / "qc").glob(f"{self.head}-*.json")
        rep = max(reps, key=lambda q: q.stat().st_mtime)
        if self.pa.read_bytes() != self.auth0 or self.pm.read_bytes() != self.models0:
            fail(f"{' '.join(args)}: box auth.json or models.json changed")
        return out, err, rep

    def demo(self, name: str, out: str, err: str, rep: Path) -> None:
        """acceptance-a passed from its demo: its stored record says neither file was readable,
        no secret in it; its sandbox's proof states it holds no Pi model credentials."""
        rx = rf"  evidence complete; decision demo checks; record ({RID})"
        got = [re.fullmatch(rx, x) for x in grep_a(out, "PASS acceptance-a: ", 2)]
        ids = [m.group(1) for m in got if m]
        if not ids:
            fail(f"{name}: want PASS acceptance-a from its demo: {out} {err[-2000:]}")
        ev = [kit("octo-feather-evidence"), "read", "--repo", ".", "--commit", self.head, "--json"]
        rd = cast("list[dict[str, object]]", json.loads(self.s.run(ev, cwd=self.repo).out))
        why = f"{name}: the demo read a credential: {rep.read_text()}"
        x = next(x for x in rd if at(x, "record", "id") == ids[0])
        d = Path(str(x["dir"]))
        o = {
            n: (d / "outputs" / n).read_text() for n in ("demo.exit", "demo.stdout", "demo.stderr")
        }
        assert o["demo.exit"] == "0\n", (why, o)
        assert o["demo.stdout"] == "neither readable\n", (why, o)
        for f in ("auth.json", "models.json"):
            assert f"/.pi/agent/{f}: No such file or directory" in o["demo.stderr"], (why, o)
        for root, _, files in os.walk(d):
            for f in files:
                assert b"SECRET-pi" not in Path(root, f).read_bytes(), (why, root, f)
        cap = cast("list[object]", at(json.loads(rep.read_text()), "captures"))[0]
        proof = [str(ln) for ln in cast("list[object]", at(cap, "sandbox", "proof"))]
        pre = (
            "qc sandbox: ok   no Pi model credentials (no Pi runs here): auth.json and "
            "models.json absent from "
        )
        assert any(ln.startswith(pre) for ln in proof), (why, proof)
        assert not any("SECRET-pi" in ln for ln in proof), (why, proof)

    def mixed(self) -> None:
        """A demo beside a criterion with neither a tagged test nor a declared demo: the demo
        passes, its sandbox none; the other insufficient evidence naming neither, nothing run for it
        (ADR 0035); the advisory classify run reaches the model (both copies there); one OAuth
        warning for the run."""
        out, err, rep = self.qc("acceptance-a", "acceptance-b", want=2)
        self.demo("mixed", out, err, rep)
        want = [
            "  missing: no tagged acceptance test and no declared demo",
            "  evidence incomplete; decision none; record none",
        ]
        if grep_a(out, "INSUFFICIENT EVIDENCE acceptance-b: ", 2)[1:] != want:
            fail(
                f"mixed: want acceptance-b insufficient evidence naming neither: {out} {err[-999:]}"
            )
        if ADVISORY not in grep_a(out, "PASS acceptance-a: ", 4):
            fail(f"mixed: want acceptance-a's advisory answered (the classify run's copies): {out}")
        if "fallback" in json.loads(rep.read_text()):
            fail(f"mixed: a fallback report key: {rep.read_text()}")
        if err.splitlines().count(OAUTH) != 1:
            fail(f"mixed: want one OAuth warning: {err}")
        if "SECRET-pi" in out + err:
            fail("mixed: a credential value printed")


def creds(s: Scratch) -> None:
    """tests/qc-creds.sh."""
    try:
        c = Creds(s)
        c.recipe_pi()
        c.target()
        # A demo alone: its sandbox none; the advisory classify run on its record reaches the
        # model, so one OAuth warning.
        out, err, rep = c.qc("acceptance-a")
        c.demo("demo alone", out, err, rep)
        if ADVISORY not in grep_a(out, "PASS acceptance-a: ", 4):
            fail(
                "demo alone: want the advisory answered (the classify run found both copies): "
                f"{out}"
            )
        if err.splitlines().count(OAUTH) != 1:
            fail(f"demo alone: want one OAuth warning (the advisory's copies): {err}")
        c.mixed()
        # A demo that cannot run to its end (exit 77): insufficient evidence, no advisory: no
        # sandbox got copies, so no OAuth warning.
        q = c.repo / "qc.toml"
        q.write_text(q.read_text().replace("; echo neither readable", "; exit 77"))
        c.git("commit", "-qam", "demo stops")
        c.head = c.git("rev-parse", "HEAD")
        out, err, _ = c.qc("acceptance-a", want=2)
        if not has("^INSUFFICIENT EVIDENCE acceptance-a: ", out):
            fail(f"exit 77: want insufficient evidence: {out}")
        if "advisory" in err:
            fail(f"exit 77: an advisory ran: {err}")
        if OAUTH in err:
            fail(f"exit 77: OAuth warning for a run whose sandboxes copied nothing: {err}")
    finally:  # what a run left read-only goes with the scratch
        subprocess.run(["chmod", "-R", "u+w", str(s.root)], capture_output=True, check=False)  # noqa: S607
    say(
        "qc-creds: ok (a declared demo's sandbox holds no auth.json or models.json: its proof "
        "says so, its record shows both unreadable, no secret stored; the advisory classify run "
        "finds both per-run copies and reaches the model; a criterion with neither insufficient "
        "evidence, nothing run for it; box files "
        "unchanged; the OAuth warning once for a run with copies, none for a run whose only "
        "sandbox, a demo's, copied nothing)"
    )


def refused(b: Box) -> None:
    """tests/qc.sh's refusals: a dirty tree; reports never overwrite; the pre-run proof printed."""
    (b.repo / "dirty").write_text("x\n")
    b.run(65, "mixed", STATUS, *A)  # dirty worktree
    (b.repo / "dirty").unlink()
    before = b.git("rev-parse", "HEAD")
    for _ in range(2):
        b.run(1, "mixed", STATUS, "5", "acceptance-a", "acceptance-b")
    b.run(0, "mixed", STATUS, *A)
    if len(list((b.t / "reports").glob(f"{before}-*.json"))) != 3:
        fail("three runs at one head must leave three reports")
    proved(b)


def proved(b: Box) -> None:
    """The pre-run proof printed: Herdr unreachable, the worktree an overlay, no persistent
    writable path, no vendored-skill cache on the box and none bound."""
    if "qc sandbox: ok   live Herdr unreachable" not in b.out:
        fail(f"no pre-run proof printed: {b.out}")
    ov = f"qc sandbox: ok   worktree {b.repo} is an overlay"
    if not (ov in b.out and "qc sandbox: ok   writable persistent paths: none" in b.out):
        fail(f"no overlay / persistent-writable proof: {b.out}")
    if "qc sandbox: ok   vendored-skill cache: none on the box, nothing bound" not in b.out:
        fail(f"absent cache: want no bind, no failure: {b.out}")


def nested(b: Box) -> None:
    """A qc sandbox nested in a demo's (outer /proc submounts covered by its own /proc) passes
    its proof."""
    b.run(0, "nested", STATUS, *A)
    j = b.demo_out()
    if has("ESCAPE|MISSING", j):
        fail(f"nested qc: {j}")
    if "NESTED exit 0" not in j:
        fail(f"nested qc: want the inner demo to run and pass (exit 0): {j}")


def recipe_args(b: Box) -> None:
    """The qc recipes pass arguments as data, never as shell source."""
    for jf in (
        ROOT / "justfile",
        ROOT / "templates/python/justfile",
        ROOT / "templates/typescript/justfile",
    ):
        rc, o = b.bounded(
            [
                "just",
                "--justfile",
                str(jf),
                "--working-directory",
                str(b.repo),
                "qc",
                STATUS,
                "5",
                "acceptance-a$(touch pwned)",
                "x;touch pwned2",
            ]
        )
        b.hung(rc, f"{jf} qc", o)
        made = [p for p in (b.repo / "pwned", b.repo / "pwned2", ROOT / "pwned") if p.exists()]
        if rc == 0 or made:
            fail(f"{jf} qc ran its arguments as shell (exit {rc}): {o}")
        if "not in docs/specs/demo.status.json: acceptance-a$(touch pwned) x;touch pwned2" not in o:
            fail(f"{jf} qc mangled its arguments: {o}")


def escapes(s: Scratch) -> None:
    """tests/qc-escapes.sh."""
    with Box(s) as b:
        # A failed proof check aborts before the judge: here raw herdr still reaches a live
        # session (the testkit herdr's FAKE_HERDR_LEAK).
        b.run(66, "escape", STATUS, *A, env={"FAKE_HERDR_LEAK": "1"})
        if "FAIL live Herdr unreachable" not in b.out:
            fail(f"leaking Herdr not caught by the proof: {b.out}")
        if b.started():
            fail("judge started after a failed proof")
        # The rule remote#acceptance-linear-key-qc: a Linear key re-entering the judge's env (here a
        # BASH_ENV that exports it again after the scrub) fails the proof, so the judge never
        # starts; the plain run below proves it absent.
        leak = s.bin / "leak.env"
        leak.write_text("export LINEAR_API_KEY=SECRET-linear-leak\n")
        b.run(66, "escape", STATUS, *A, env={"BASH_ENV": str(leak)})
        if "FAIL no tracker credential: LINEAR_API_KEY set 1 times" not in b.out:
            fail(f"leaking Linear key not caught by the proof: {b.out}")
        if b.started():
            fail("judge started with a Linear key in its env")
        # A mask over another repo that cannot be set up (here a path to bind back on it is
        # missing) aborts before the judge.
        miss = f"{b.home}/src/sib/missing"
        b.run(66, "escape", STATUS, *A, env={"OCTO_FEATHER_QC_RO_BINDS": miss})
        if f"qc sandbox: FAIL bind back {miss} on the mask over {b.home}/src/sib" not in b.out:
            fail(f"a failed repo mask not named: {b.out}")
        if b.started():
            fail("judge started after a failed repo mask")
        every_escape(b)
    say(
        "qc-escapes: ok (proof abort, sandbox escapes, other repos masked (listing recorded and "
        "refused; a failed mask aborts), cleanup count, live state untouched; offline, runs "
        "bounded)"
    )


def every_escape(b: Box) -> None:
    """Every escape fails; leftovers killed, agents counted, credential copies gone, live
    records untouched."""
    b.run(0, "escape", STATUS, *A)
    j = b.demo_out()
    if has("ESCAPE|MISSING|LINEAR KEY", j):
        fail(f"sandbox escape: {j}")
    o, h = b.out, str(b.home)
    if "qc sandbox: ok   no tracker credential: LINEAR_API_KEY set 0 times" not in o:
        fail(f"no Linear key proof: {o}")
    if (
        "qc sandbox: ok   parent route unset: 0 of OCTO_FEATHER_PARENT/SESSION_ID/ROLE/SPEND_SPACE,"
        not in o
    ):
        fail(f"no route proof naming the spend space: {o}")
    rx = (
        rf"qc sandbox: ok   other repos hidden: 1 git repos under {re.escape(h)} .*: src/sib; "
        rf"visible: kit under test {re.escape(str(ROOT))}, worktree {re.escape(str(b.repo))}$"
    )
    if not has(rx, o):
        fail(f"no other-repos proof naming the mask and what stays visible: {o}")
    att = cast("list[dict[str, object]]", b.jr("attempts"))
    want = {"kind": "repo", "attempt": True, "refused": True, "what": f"open {h}/src/sib"}
    if not any(want.items() <= a.items() for a in att):
        fail(f"the listing of another repo not recorded and refused: {b.jr()}")
    cleaned(b)


def cleaned(b: Box) -> None:
    """Leftovers killed and counted, agents counted, nothing survives: no process, no HOME or
    /tmp write, no live record, no sandbox Herdr session in the real config dir."""
    o = b.out
    if "cleanup: agents started 1 (headless pi 1, Herdr panes 0)" not in o:
        fail(f"no agent count: {o}")
    if b.jr("left_after_kill") != 0:
        fail(f"cleanup record: {b.jr()}")
    killed = repr(b.jr("killed"))
    for p in ("sleep 3012", "sleep 302921"):
        if p not in killed:
            fail(f"leftover '{p}' not killed and counted: {b.jr()}")
    if b.left(rf"sleep (3012|302921){b.tok}") or b.servers_left():
        fail("sandbox processes survived the run")
    if (b.home / "qc-saved").exists():
        fail("judge wrote into HOME")
    if list(Path("/tmp").glob("qc-escape-*")):  # noqa: S108 (the judge's /tmp writes, seen from here)
        fail("judge's /tmp writes survived")
    lv = b.live
    hist = (lv / "lanes/archive/gh1.toml").read_text() == "ARCHIVED\n"
    one = len((lv / "director.handoffs.jsonl").read_text().splitlines()) == 1
    if (lv / "lanes/escaped").exists() or not hist or not one:
        fail("judge wrote live state")
    if (b.home / ".config/herdr/sessions").exists():
        fail("sandbox Herdr session left in the real config dir")


def live_session(b: Box) -> None:
    """A real Herdr server, session qclive, a workspace QCLIVE in it (QC_TEST_HERDR=real)."""
    live = subprocess.Popen(
        [b.real, "--session", "qclive", "server"],
        env=b.s.env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    b.pids["qclive"] = live.pid
    for _ in range(50):
        ls = [b.real, "--session", "qclive", "workspace", "list"]
        if subprocess.run(ls, env=b.s.env, capture_output=True, check=False).returncode == 0:
            break
        time.sleep(0.2)
    mk = [b.real, "--session", "qclive", "workspace", "create", "--label", "QCLIVE"]
    mk += ["--cwd", str(b.t), "--no-focus"]
    if subprocess.run(mk, env=b.s.env, capture_output=True, check=False).returncode:
        fail("real herdr: live test session did not start")


def pane(b: Box) -> None:
    """A pane the judge spawns through the sandbox herdr runs in the judge's PID namespace (the
    sandbox server started inside it), sees no live Herdr socket and no creds, and dies with the
    run: the testkit herdr; the box's real herdr only with QC_TEST_HERDR=real, under a real "live"
    Herdr session in the throwaway HOME."""
    path = None
    if b.mode == "real":  # a real "live" Herdr session under the throwaway HOME
        path = b.base
        live_session(b)
    b.run(0, "pane", STATUS, *A, env={"PATH": path} if path else None)
    j, m = b.demo_out(), b.mode
    if has("ESCAPE|MISSING", j):
        fail(f"sandbox pane escape ({m} herdr): {j}")
    if "PANE done" not in j:
        fail(f"pane never ran ({m} herdr): {j}")

    def ns(who: str) -> str:
        return next((x.split(" ")[2] for x in j.splitlines() if x.startswith(f"{who} pidns ")), "")

    if not (ns("judge") == ns("pane") != str(Path("/proc/self/ns/pid").readlink())):
        fail(f"pane not in the judge's PID namespace ({m} herdr): {j}")
    if b.jr("herdr_panes") != 1:
        fail(f"pane not counted ({m} herdr): {b.jr()}")
    time.sleep(0.3)
    if b.left(f"sleep 303031{b.tok}"):
        fail(f"judge's pane survived the run ({m} herdr)")
    if b.mode == "real":
        live_kept(b)
    if (b.repo / "scratch").exists():
        fail("pane run's scratch survived")


def live_kept(b: Box) -> None:
    """The live Herdr session unhurt, the only one left in the config dir."""
    ls = [b.real, "--session", "qclive", "workspace", "list"]
    if subprocess.run(ls, env=b.s.env, capture_output=True, check=False).returncode:
        fail("the run hurt the live Herdr session")
    left = sorted(p.name for p in (b.home / ".config/herdr/sessions").iterdir())
    if left != ["qclive"]:
        fail(f"sandbox session left: {left}")


def qc(s: Scratch) -> None:
    """tests/qc.sh."""
    with Box(s) as b:
        refused(b)
        recipe_args(b)
    say(
        "qc: ok (dirty, unique reports, the pre-run proof, recipe args as data; offline, runs "
        "bounded)"
    )


def namespace(s: Scratch) -> None:
    """tests/qc-namespace.sh."""
    with Box(s) as b:
        nested(b)
        pane(b)
        m = b.mode
    say(
        f"qc-namespace: ok (nested sandbox, judge pane in the sandbox ({m} herdr); offline, "
        "runs bounded)"
    )


if __name__ == "__main__":
    if sys.argv[1:2] != ["creds"]:
        offline()
    elif (
        sys.platform == "darwin"
    ):  # creds runs no offline(): its own skip, as tests/qc-creds.sh had
        say("qc-creds: skipped, not on macOS (just qc needs Linux; CI runs it)")
        sys.exit(0)
    main(qc, namespace, copies, status, uv_cache, mise, oauth, vendored, escapes, creds)
