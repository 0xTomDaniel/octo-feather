#!/usr/bin/env python3
"""Fake `pi` as the qc judge (the testkit's stand-in for Pi, which the kit does not own): no model.

Run by octo-feather-qc's agent fallback in its sandbox, its brief the last argument. It prints
which gh it was given, the brief's lines (each prefixed BRIEF), then the answers of three reads
(R1 issue view, R2 pr view --json, R3 api GET) and two writes (W1 issue comment, W2 api -X POST)
through that gh, each prefixed; with a snapshot ($OCTO_FEATHER_GHSNAP) it tries to write it,
printing ESCAPE for each write that lands. Then its report: acceptance-a passed at the brief's
head. `--version` exits 0; FAKE_PI_HANG=N sleeps N seconds instead (a judge that never ends).
FAKE_QC=MODE answers as tests/lib/qc.sh's fake judge does in the qc sandbox test instead (qc_mode
below: each mode what that judge tries, then its report).
"""

import contextlib
import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def say(line: str) -> None:
    sys.stdout.write(line + "\n")


def lands(p: Path) -> bool:
    """Whether a write to P lands."""
    try:
        p.write_text("hacked\n")
    except OSError:
        return False
    return True


def answer(h: str, *crit: dict[str, str], pre: str = "") -> None:
    """A qc judge's report on head H: CRIT, after PRE."""
    say(pre + "```json\n" + json.dumps({"head": h, "criteria": list(crit)}) + "\n```")


def ok(h: str) -> None:
    a = {"id": "acceptance-a", "verdict": "pass", "command": "app a --json", "output": "ok"}
    answer(h, a | {"why": "shown"})


def mkscratch() -> Path:
    d = Path("scratch")
    d.mkdir(exist_ok=True)
    return d


PI = Path.home() / ".pi" / "agent"


def m_dup(h: str, _: list[str]) -> None:
    answer(
        h,
        {"id": "acceptance-a", "verdict": "pass", "command": "a", "output": "ok"},
        {"id": "acceptance-a", "verdict": "fail", "command": "a", "output": "no"},
        {"id": "acceptance-b", "verdict": "pass", "command": "b", "output": "ok"},
    )


def m_head(_h: str, _: list[str]) -> None:
    ok("0" * 40)


def m_mixed(h: str, argv: list[str]) -> None:
    """One judge per criterion: the one the brief names answered."""
    if "- acceptance-b:" in " ".join(argv):
        b = {"id": "acceptance-b", "verdict": "fail", "command": "app b --json", "output": "error"}
        answer(h, b | {"why": "no b"}, pre="done\n")
    else:
        a = {"id": "acceptance-a", "verdict": "pass", "command": "app a --json"}
        answer(h, a | {"output": '{"ok": true}', "why": "shown"}, pre="done\n")


def m_garbage(_h: str, _: list[str]) -> None:
    say("I think it works.")


def m_argv(h: str, argv: list[str]) -> None:
    say("ARGV " + json.dumps(argv))
    ok(h)


def m_hang(_h: str, _: list[str]) -> None:
    """A judge that never ends: it holds a shared flock on FAKE_QC_LOCK across its exec (the
    scenario's proof it ended: testkit.qc.let_go), says ready on the FAKE_QC_READY pipe, then
    sleeps."""
    if lock := os.environ.get("FAKE_QC_LOCK"):
        fd = os.open(lock, os.O_RDONLY)
        fcntl.flock(fd, fcntl.LOCK_SH)
        os.set_inheritable(fd, True)  # noqa: FBT003  # positional only
    if fifo := os.environ.get("FAKE_QC_READY"):
        with Path(fifo).open("w") as f:
            f.write("judge ready\n")
    os.execvp("sleep", ["sleep", "3600"])  # noqa: S606, S607


def m_writes(_h: str, _: list[str]) -> None:
    Path("judge-was-here").write_text("hacked\n")
    (mkscratch() / "fine").write_text("ignored\n")
    say('```json\n{"criteria": []}\n```')


def m_opaque(h: str, _: list[str]) -> None:
    """A tracked dir replaced: opaque in the upper."""
    shutil.rmtree("docs")
    Path("docs/specs").mkdir(parents=True)
    Path("docs/specs/other.html").write_text("x\n")
    ok(h)


def m_tracked(h: str, _: list[str]) -> None:
    with Path(".gitignore").open("a") as f:
        f.write("hacked\n")
    Path("docs/specs/demo.spec.html").unlink()
    ok(h)


def m_copycreds(h: str, _: list[str]) -> None:
    shutil.copy2(PI / "auth.json", mkscratch() / "a")
    shutil.copy2(PI / "models.json", ".git/m")
    ok(h)


def m_bigcopy(h: str, _: list[str]) -> None:
    big = mkscratch() / "big"
    shutil.copy(PI / "auth.json", big)
    os.truncate(big, 67108865)
    ok(h)


def refreshed(v: str) -> None:
    """auth.json refreshed to V, by rename or else in place."""
    text = f'{{"k": "SECRET-pi-auth-{v}-987654", "exp": 2}}\n'
    try:
        (PI / "auth.json.new").write_text(text)
        (PI / "auth.json.new").replace(PI / "auth.json")
    except OSError:
        (PI / "auth.json").write_text(text)


def m_refresh(h: str, _: list[str]) -> None:
    """auth A becomes B, B kept, B becomes C (a refresh between two copies), a stash into HOME."""
    d = mkscratch()
    refreshed("B")
    shutil.copy(PI / "auth.json", d / "oldauth")
    shutil.copy(PI / "auth.json", ".git/oldauth")
    with contextlib.suppress(OSError):
        shutil.copy(PI / "auth.json", Path.home() / "oldauth")
    refreshed("REFRESHED")
    ok(h)


def m_rewrite(h: str, _: list[str]) -> None:
    """Both Pi files rewritten in place; the judge sees its own writes."""
    (PI / "auth.json").write_text('{"k": "SECRET-pi-auth-JUDGE-987654", "exp": 3}\n')
    models = '{"providers": {"p": {"apiKey": "SECRET-pi-models-JUDGE-987654"}}}\n'
    (PI / "models.json").write_text(models)
    if all("JUDGE" in (PI / f).read_text() for f in ("auth.json", "models.json")):
        ok(h)
    else:
        say("copies not writable")


def m_token(h: str, _: list[str]) -> None:
    """Only extracted values, as jq -r would print them: no whole-file match."""
    k = json.loads((PI / "auth.json").read_text())["k"]
    (mkscratch() / "tok").write_text(f"x {k} y\n")
    key = json.loads((PI / "models.json").read_text())["providers"]["p"]["apiKey"]
    Path(".git/tok2").write_text(key + "\n")
    ok(h)


def shell(script: str, *args: str) -> str:
    """The judge's shell step: SCRIPT (a file beside this one) run by bash with ARGS."""
    here = Path(__file__).resolve().parent
    p = subprocess.run(
        ["bash", str(here / script), *args],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    )
    return (p.stdout + p.stderr).rstrip("\n")


def m_pane(h: str, _: list[str]) -> None:
    """A pane spawned through the sandbox herdr (judge-pane.sh) reports what it sees and tries to
    outlive the run, holding a shared flock on $HOME/pane.lock while it lives (the scenario's proof
    it died with the run: testkit.qc.let_go)."""
    say(shell("judge-pane.sh"))
    ok(h)


def m_nested(h: str, _: list[str]) -> None:
    """A sandboxed qc inside the judge's (judge-nested.sh) gets past its proof; this pi's own dir
    first on its PATH."""
    say(shell("judge-nested.sh", str(Path(sys.argv[0]).parent)))
    ok(h)


def m_uvcache(h: str, _: list[str]) -> None:
    """An offline `uv sync` of QC_UVP's lock (its one package only in uv's cache), an import of
    it, then a write into that cache, each said with its result."""
    env = os.environ | {"UV_PROJECT_ENVIRONMENT": "/tmp/uv-venv"}  # noqa: S108 (the run's tmpfs)
    sync = ["uv", "sync", "--project", os.environ["QC_UVP"], "--locked", "--offline", "--quiet"]
    p = subprocess.run(sync, env=env, capture_output=True, text=True, check=False)
    say(p.stdout + p.stderr + f"UVSYNC exit {p.returncode}")
    imp = ["/tmp/uv-venv/bin/python", "-c", "import qcw; print('UVIMPORT', qcw.X)"]  # noqa: S108
    try:
        p = subprocess.run(imp, capture_output=True, text=True, check=False)
        say((p.stdout + p.stderr).rstrip("\n"))
    except OSError as e:
        say(f"UVIMPORT failed: {e}")
    where = ["uv", "--color", "never", "cache", "dir"]
    uc = subprocess.run(where, capture_output=True, text=True, check=False).stdout.strip()
    say(f"UVWRITE exit {0 if lands(Path(uc) / 'judge-wrote') else 1}")
    ok(h)


MODES = {n.removeprefix("m_"): f for n, f in list(globals().items()) if n.startswith("m_")}


def qc_mode(mode: str, argv: list[str]) -> None:
    """The qc judge as tests/lib/qc.sh's fake pi answers under FAKE_QC=MODE: what it tries, then
    its report on the brief's head."""
    if os.environ.get("LINEAR_API_KEY") is not None:
        say("LINEAR KEY IN JUDGE ENV")  # remote#acceptance-linear-key-qc
    m = re.search(r"head ([0-9a-f]{40})", " ".join(argv))
    if mode not in MODES:
        sys.exit(f"judge.py: FAKE_QC={mode}: no such mode, one of {' '.join(MODES)}")
    MODES[mode](m.group(1) if m else "", argv)


a = sys.argv[1:]
if a[:1] == ["--version"]:
    sys.exit(0)
if hang := os.environ.get("FAKE_PI_HANG"):
    if observer := os.environ.get("FAKE_PI_HANG_SOCKET"):
        import socket

        with socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET) as peer:
            peer.settimeout(30)
            peer.connect(observer)
            handle = os.pidfd_open(os.getpid())
            try:
                socket.send_fds(
                    peer,
                    [
                        json.dumps(
                            {"pid": os.getpid(), "token": os.environ["FAKE_PI_HANG_TOKEN"]}
                        ).encode()
                    ],
                    [handle],
                )
            finally:
                os.close(handle)
            if peer.recv(1) != b"!":
                sys.exit("fake judge: owned observer did not acknowledge readiness")
    os.execvp("sleep", ["sleep", hang])  # noqa: S606, S607
if qc := os.environ.get("FAKE_QC"):
    qc_mode(qc, a)
    sys.exit(0)
brief = a[-1] if a else ""
say(f"gh is {shutil.which('gh')}")
for ln in brief.splitlines():
    say(f"BRIEF {ln}")


def gh(tag: str, *args: str) -> None:
    p = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)  # noqa: S607
    say(f"{tag} {' '.join((p.stdout + p.stderr).split())}")


gh("R1", "issue", "view", "1", "--json", "title,state", "-q", '.title + " " + .state')
gh("R2", "pr", "view", "2", "--json", "isDraft,title")
gh("R3", "api", "repos/o/r/issues/1/timeline", "-q", "length")
gh("W1", "issue", "comment", "1", "-b", "hacked")
gh("W2", "api", "-X", "POST", "repos/o/r/issues", "-f", "title=x")
if snap := os.environ.get("OCTO_FEATHER_GHSNAP"):
    subprocess.run(["chmod", "-R", "u+w", snap], capture_output=True, check=False)  # noqa: S607
    for what, p in (
        ("snapshot", Path(snap) / "x"),
        ("snapshot item", Path(snap) / "issue" / "1.json"),
    ):
        if lands(p):
            say(f"ESCAPE {what} writable")
m = re.search(r"head ([0-9a-f]{40})", brief)
h = m.group(1) if m else ""
report = (
    f'{{"head": "{h}", "criteria": [{{"id": "acceptance-a", "verdict": "pass", '
    '"command": "gh issue view 1", "output": "ok", "why": "history only: shown"}]}'
)
say(f"```json\n{report}\n```")
