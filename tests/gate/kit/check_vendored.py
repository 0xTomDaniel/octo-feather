"""The scenarios of tests/gate/kit/test_check_vendored.py (its items), this file their command
(testkit.main): scripts/check-vendored, the gate behind `just check-vendored` and the fetch
behind `just vendored-fetch`, run directly (--repo: a copy of the kit's Skillfile, lock, patches
and skill folders, a git repo, prepared once per gate run) against the warm cache `just
vendored-fetch` makes (CI runs it before the gate; none fails naming it), read in place, never
written: a scenario that changes a cache builds its own beside it.

- The gate passes with no network namespace (it never needs to dial out), and reads the
  committed folder (the run stages every change, as a commit records it): a drifted, extra or
  missing vendored file, a committed mode change (on the disk or in the index only), a patch
  that no longer matches, a committed stray, a file, folder or skill-folder symlink fails naming
  skill and file; an untracked file and what git cannot hold (a FIFO, an empty folder) pass
  (#143, #121 D16). One run carries every finding a state can hold at once (`findings`).
- A poisoned cache (a tampered upstream blob matching a tampered vendored file) fails naming the
  skill; a missing cache fails naming `just vendored-fetch`.
- --extract spec-chat DEST writes the fetch-only Spec Chat pin offline, exec bits kept; uncached,
  it fails naming `just vendored-fetch` (#96).
- A fetch GitHub refuses for credentials (a private pin; testkit/git_refused.py) names gh auth
  login && gh auth setup-git, never the network (#463).
- A fetch through a stalled proxy, silent or dripping headers, times out within its bound naming
  the fix, for the pin's git fetch and the skillfile download alike (own network namespace, only
  loopback up: never the real network).
The namespace proofs need Linux user namespaces (and `ip` for the proxy): where they do not work
the scenario names the skip, as the gate's other items run everywhere.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import zlib
from pathlib import Path

from testkit import HERE, ROOT, Ran, Scratch, kit, main

CACHE = (
    Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "octo-feather" / "skillfile"
)
PIN = "49dd158d1076134a641b33efb035946536778336"
MP = "mattpocock/skills"
TAG = "check-vendored test"
OK = "vendored: ok"
FETCH = "run `just vendored-fetch`"
NS = ["unshare", "-Un", "--map-current-user"]
SKILLS = ".agents/skills"


def build(p: Scratch) -> None:
    """repo: the kit's Skillfile, lock, patches and skill folders, one commit."""
    r = p.root / "repo"
    (r / ".skillfile").mkdir(parents=True)
    for f in ("Skillfile", "Skillfile.lock"):
        shutil.copy2(ROOT / f, r / f)
    shutil.copytree(ROOT / ".skillfile" / "patches", r / ".skillfile" / "patches", symlinks=True)
    shutil.copytree(ROOT / SKILLS, r / SKILLS, symlinks=True)
    p.git(r, "init", "-q")
    p.git(r, "add", "-A")
    p.git(r, "commit", "-qm", "base")


def warm() -> None:
    for d in ("git", "bin"):
        assert (CACHE / d).is_dir(), f"{TAG}: no warm cache at {CACHE}; run `just vendored-fetch`"


def repo(s: Scratch) -> Path:
    warm()
    s.prepare("check-vendored", build)
    return s.root / "repo"


def skipped(what: str) -> None:
    """The Linux-only proof WHAT named as skipped, on stdout."""
    sys.stdout.write(f"{TAG}: skipped, Linux-only proof: {what}\n")


def works(cmd: list[str]) -> bool:
    return subprocess.run(cmd, capture_output=True, check=False).returncode == 0


def ns() -> list[str]:
    """The offline-namespace prefix where `unshare -Un` works, else none (the skip named)."""
    if works([*NS, "true"]):
        return NS
    skipped("offline-namespace gate runs (unshare -Un unavailable)")
    return []


def cache(s: Scratch, name: str, *, bin_: bool = True, git: bool = False) -> Path:
    """An XDG_CACHE_HOME of S holding a skillfile cache: the warm cache's binary (a link) when
    BIN_, its git objects (links per repo) when GIT."""
    c = s.root / name
    d = c / "octo-feather" / "skillfile"
    d.mkdir(parents=True)
    if bin_:
        (d / "bin").symlink_to(CACHE / "bin")
    if git:
        for g in (CACHE / "git").glob("*/*/*.git"):
            (d / g.relative_to(CACHE).parent).mkdir(parents=True, exist_ok=True)
            (d / g.relative_to(CACHE)).symlink_to(g)
    return c


def gate(
    s: Scratch,
    r: Path,
    want: int,
    *,
    xdg: Path = CACHE.parents[1],
    pre: list[str] | None = None,
) -> str:
    """check-vendored on R as its git index holds it, exit WANT; stdout and stderr."""
    got = s.run(
        [*(pre or []), kit("check-vendored"), "--repo", str(r)],
        want=want,
        env={"XDG_CACHE_HOME": str(xdg)},
    )
    return said(got)


def said(r: Ran) -> str:
    return f"{r.out}\n{r.err}"


def has(out: str, *wants: str) -> None:
    for w in wants:
        assert w in out, f"{TAG}: output lacks {w!r}: {out}"


def edit(p: Path, old: str, new: str) -> None:
    t = p.read_text()
    assert old in t, f"{TAG}: {p} lacks {old!r}"
    p.write_text(t.replace(old, new, 1))


def findings(s: Scratch) -> None:
    """The gate on a copy: clean (with an untracked stray, a FIFO and an empty folder) passes
    offline; every drift fails naming skill and file, each on one shared run; the pinned Spec
    Chat extracted offline."""
    r = repo(s)
    sk = r / SKILLS
    pre = ns()
    # Clean, no network at all, plus what never counts: an untracked stray (staging skipped, #143),
    # a FIFO and an empty folder git cannot commit.
    (sk / "tdd" / "STRAY.md").write_text("x\n")
    os.mkfifo(sk / "tdd" / "PIPE")
    (sk / "tdd" / "empty" / "deeper").mkdir(parents=True)
    s.git(r, "add", "-A")
    s.git(r, "rm", "-q", "--cached", f"{SKILLS}/tdd/STRAY.md")
    has(gate(s, r, 0, pre=pre), OK)
    (sk / "tdd" / "PIPE").unlink()
    shutil.rmtree(sk / "tdd" / "empty")
    # Pinned Spec Chat, written out with no network: its files, exec bits kept.
    dest = s.root / "sc"
    x = s.run(
        [*pre, kit("check-vendored"), "--repo", str(r), "--extract", "spec-chat", str(dest)],
        env={"XDG_CACHE_HOME": str(CACHE.parents[1])},
    )
    assert x.out == f"{dest}/skill", f"{TAG}: --extract spec-chat: {said(x)}"
    assert os.access(dest / "skill" / "review-spec" / "scripts" / "review-host.py", os.X_OK), said(
        x
    )
    assert (dest / "skill" / "review-spec" / "assets" / "review-serve.py").is_file(), said(x)
    # Every finding one state can hold, committed (staged): a drifted line in a patched file, an
    # extra file, a missing upstream file, a patch no longer matching its file, the stray now
    # staged, a folder symlink, a file symlink, a file replaced by a symlink, a mode changed in
    # the index only (#143, #121 D16).
    edit(sk / "tdd" / "SKILL.md", "\n\n", "\ndrift\n")
    (sk / "sharpen" / "EXTRA.md").write_text("x\n")
    shutil.move(sk / "tdd" / "mocking.md", s.root / "mocking.md")
    edit(
        r / ".skillfile/patches/skills/sharpen/SKILL.md.patch",
        "\n-disable-model",
        "\n disable-model",
    )
    (sk / "tdd" / "EXTRA").symlink_to("../grilling")
    (sk / "tdd" / "LINK.md").symlink_to("SKILL.md")
    shutil.move(sk / "tdd" / "tests.md", s.root / "tests.md")
    (sk / "tdd" / "tests.md").symlink_to(s.root / "tests.md")
    s.git(r, "add", "-A")
    s.git(r, "update-index", "--chmod=+x", f"{SKILLS}/grilling/SKILL.md")
    out = gate(s, r, 1)
    has(
        out,
        f"check-vendored: tdd: {SKILLS}/tdd/SKILL.md differs from upstream {MP}@49dd158",
        f"check-vendored: sharpen: {SKILLS}/sharpen/EXTRA.md is not in upstream",
        f"check-vendored: tdd: {SKILLS}/tdd/mocking.md is missing",
        f"check-vendored: sharpen: {SKILLS}/sharpen/SKILL.md differs",
        f"check-vendored: tdd: {SKILLS}/tdd/STRAY.md is not in upstream",
        f"check-vendored: tdd: {SKILLS}/tdd/EXTRA is a symlink (to ../grilling)",
        f"check-vendored: tdd: {SKILLS}/tdd/LINK.md is a symlink (to SKILL.md)",
        f"check-vendored: tdd: {SKILLS}/tdd/tests.md is a symlink",
        f"check-vendored: grilling: {SKILLS}/grilling/SKILL.md has git mode 100755",
        "check-vendored: 10 vendored file(s) drift from pin plus patch",
    )
    # Back to the commit, then what one file cannot hold beside the above: a mode change on the
    # disk (chmod +x), and the skill folder itself a symlink.
    s.git(r, "reset", "-q", "--hard")
    s.git(r, "clean", "-qfd")
    (sk / "tdd" / "SKILL.md").chmod(0o755)
    shutil.move(sk / "sharpen", s.root / "sharpen")
    (sk / "sharpen").symlink_to(s.root / "sharpen")
    s.git(r, "add", "-A")
    out = gate(s, r, 1)
    has(
        out,
        f"check-vendored: tdd: {SKILLS}/tdd/SKILL.md has git mode 100755, upstream {MP}@49dd158",
        f"check-vendored: sharpen: {SKILLS}/sharpen is a symlink",
        "check-vendored: 3 vendored file(s) drift from pin plus patch",
    )


def cache_faults(s: Scratch) -> None:
    """A poisoned cache, a missing one (gate and --extract), a fetch refused for credentials."""
    r = repo(s)
    pre = ns()
    # Poisoned: grilling's upstream blob rewritten to match an edited vendored file.
    c = cache(s, "c-poisoned", git=True)
    g = c / "octo-feather/skillfile/git" / MP / f"{PIN}.git"
    g.unlink()
    shutil.copytree(CACHE / "git" / MP / f"{PIN}.git", g)
    packs = list((g / "objects" / "pack").glob("*.pack"))
    for p in packs:
        held = s.root / p.name
        shutil.move(p, held)
        p.with_suffix(".idx").unlink()
        with held.open("rb") as fh:
            subprocess.run(
                ["git", "--git-dir", str(g), "unpack-objects", "-q"],  # noqa: S607
                stdin=fh,
                check=True,
            )
    oid = s.run(
        ["git", "--git-dir", str(g), "rev-parse", f"{PIN}:skills/productivity/grilling/SKILL.md"]
    ).out
    vend = r / SKILLS / "grilling" / "SKILL.md"
    vend.write_text(vend.read_text() + "poisoned line\n")
    loose = g / "objects" / oid[:2] / oid[2:]
    loose.chmod(0o644)
    body = vend.read_bytes()
    loose.write_bytes(zlib.compress(b"blob %d\0" % len(body) + body))
    s.git(r, "add", "-A")
    out = gate(s, r, 1, xdg=c)
    has(
        out,
        f"check-vendored: grilling: cached upstream {MP}@{PIN} skills/productivity/grilling "
        "fails authentication",
        "just vendored-fetch",
    )
    # Missing cache: fails fast naming the fetch step, never a skip; --extract too.
    c = cache(s, "c-missing")
    has(gate(s, ROOT, 1, xdg=c, pre=pre), "is not cached at", FETCH)
    x = s.run(
        [kit("check-vendored"), "--repo", str(ROOT), "--extract", "spec-chat", str(s.root / "sc2")],
        want=1,
        env={"XDG_CACHE_HOME": str(c)},
    )
    has(said(x), "extract: spec-chat: 0xTomDaniel/spec-chat@", FETCH)
    # GitHub asks for credentials (#463): named with the sign-in fix, never "check network".
    (s.bin / "git").symlink_to(HERE / "git_refused.py")
    try:
        f = s.run(
            [kit("check-vendored"), "--repo", str(ROOT), "--fetch"],
            want=1,
            env={"XDG_CACHE_HOME": str(cache(s, "c-auth"))},
        )
    finally:
        (s.bin / "git").unlink()
    has(
        said(f),
        "could not read Username",
        "GitHub wants credentials (a private pin): sign in and let git use gh: gh auth login && "
        "gh auth setup-git, then rerun `just vendored-fetch`",
    )
    assert "check network" not in said(f), (
        f"{TAG}: credential refusal blamed on the network: {said(f)}"
    )


# Inside `unshare -rn` (only loopback, brought up here): a proxy on loopback that accepts and never
# answers (silent) or drips CONNECT response headers every 0.2 s forever (drip), bound before the
# fetch starts; then check-vendored --fetch through it, its exit this one's.
STALL = """
import socket, subprocess, sys, threading, time
subprocess.run(["ip", "link", "set", "lo", "up"], check=True)
s = socket.socket(); s.bind(("127.0.0.1", 0)); s.listen(16)
held = []
def drip(c):
    try:
        c.recv(65536); c.sendall(b"HTTP/1.1 200 Connection established\\r\\n")
        while True: c.sendall(b"X-Drip: 1\\r\\n"); time.sleep(0.2)
    except OSError: pass
def serve():
    while True:
        c = s.accept()[0]; held.append(c)
        if sys.argv[1] == "drip": threading.Thread(target=drip, args=(c,), daemon=True).start()
threading.Thread(target=serve, daemon=True).start()
p = "http://127.0.0.1:%d" % s.getsockname()[1]
env = {"HTTPS_PROXY": p, "https_proxy": p, "OCTO_FEATHER_FETCH_TIMEOUT": "2"}
sys.exit(subprocess.run(sys.argv[2:], env={**__import__("os").environ, **env}).returncode)
"""


def stalled_fetch(s: Scratch) -> None:
    """Silent and dripping proxies, the pin's git fetch and the skillfile download: each fetch
    gives up within one total bound, naming the fix. The four run at once."""
    if not works(["unshare", "-rn", "sh", "-c", "ip link set lo up"]):
        skipped("stalled and dripping proxy fetch (needs unshare -rn and ip)")
        return
    warm()
    runs: list[tuple[str, str, float, subprocess.Popen[str]]] = []
    for what, bin_ in (("git", True), ("download", False)):
        for mode in ("silent", "drip"):
            c = cache(s, f"c-{what}-{mode}", bin_=bin_)
            cmd = [
                "unshare",
                "-rn",
                "python3",
                "-c",
                STALL,
                mode,
                kit("check-vendored"),
                "--repo",
                str(ROOT),
                "--fetch",
            ]
            p = subprocess.Popen(
                cmd,
                env={**s.env, "XDG_CACHE_HOME": str(c)},
                cwd=s.root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            runs.append((what, mode, time.monotonic(), p))
    for what, mode, t0, p in runs:
        out = p.communicate()[0]
        took = time.monotonic() - t0
        said_ = f"{TAG}: {what} {mode} proxy fetch want exit 1 within 10s"
        said_ += f", got {p.returncode} after {took:.1f}s"
        assert p.returncode == 1, f"{said_}: {out}"
        assert took <= 10, f"{said_}: {out}"
        assert "Traceback" not in out, out
        has(out, "rerun `just vendored-fetch`")
        if what == "git":
            has(out, f"git fetch of {MP}@{PIN} timed out after 2s")
        else:
            has(
                out,
                "downloading skillfile v1.9.2 from "
                "https://github.com/eljulians/skillfile/releases/download/v1.9.2/",
                "timed out after 2s",
            )


if __name__ == "__main__":
    main(findings, cache_faults, stalled_fetch)
