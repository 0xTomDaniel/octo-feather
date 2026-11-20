"""The `just install-check` test's sections, one scenario each (#508, #996): each
tests/install-check*.sh gate item runs one as this file's command, so the items keep their ids
(tests/user-mise-ic*.sh pick them by -k), and each item's header lists the facts its scenario
proves. The box they run on, its stand-ins and its PATH: testkit/install_check.py. A failed fact
fails naming it, with the run's output."""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
from pathlib import Path

from testkit import FIXTURES, HERE, ROOT, Scratch, asked, main
from testkit.install_check import PI_STUB, Box, Out, argv, field

LINEAR = str(HERE / "linear")  # the testkit's Linear stand-in, over a tape
KIT = re.escape(str(ROOT))
KIT_FIX = "octo-feather-lane post-merge step 3 fast-forwards it"
ON_MAIN = "live install clones stay on main (work in a git worktree)"
AB_INSTALL = (
    "npm install -g agent-browser@0.40.0 "
    "(then agent-browser doctor --offline; no Chrome found: agent-browser install)"
)


def say(line: str) -> None:
    sys.stdout.write(line + "\n")


def tracker(s: Scratch) -> None:
    """tests/install-check.sh: the tracker CLI, pi, the gate's Python and the box python3."""
    b, t = Box(s), s.root
    out = b.check(1, b.lin_target / "sub")
    assert out.find(r"^tracker linear "), f"Linear target: no tracker line: {out.text}"
    why = f"linear hidden from a dir it shares with mise: mise gone too: {out.text}"
    assert out.has(f"mise   version {b.mpin} ok (mise-version)"), why
    why = "Linear target without linear: not listed missing with v3.1.0 and the install path"
    assert out.find(r"^linear MISSING \(want v3\.1\.0\).*releases/tag/v3\.1\.0"), (
        f"{why}: {out.text}"
    )
    assert "npx @schpet/linear-cli" in out.text, f"{why}: {out.text}"

    def tape(name: str) -> str:  # a FAKE_LINEAR dir
        d = t / "fl" / name
        d.mkdir(parents=True)
        shutil.copy(FIXTURES / "linear-install-check" / name / "tape.json", d)
        return str(d)

    out = b.check(0, t, LINEAR, b.lin_target, FAKE_LINEAR=tape("pin"))
    why = f"Linear target, linear at the pin: not ok: {out.text}"
    assert out.find(r"^linear ok  .*/linear \(v3\.1\.0\)$"), why
    out = b.check(1, b.lin_target, LINEAR, FAKE_LINEAR=tape("old"))
    rx = r"^linear WRONG VERSION .* reports 3\.0\.0, want v3\.1\.0; .*npx @schpet/linear-cli"
    assert out.find(rx), f"Linear target, linear 3.0.0: {out.text}"
    out = b.check(0, b.gh_target)
    assert out.find(r"^tracker github-issues "), f"GitHub target checked linear: {out.text}"
    assert not re.search("linear", out.text, re.IGNORECASE), (
        f"GitHub target checked linear: {out.text}"
    )
    assert out.has(f"pi     version {b.pin} ok (pi-version)"), (
        f"pi at the pin: no ok version line: {out.text}"
    )
    why = f"gate Python at the pin and box python3: no ok lines: {out.text}"
    rx = rf"python gate {re.escape(b.ppin)} ok  /.* \(venv, pidfd_open; \.python-version\)"
    assert out.full(rx), why
    rx = r"python3 version 3\.[0-9]+\.[0-9]+ ok  /.*/python3 \(3\.11 or later, the kit scripts\)"
    assert out.full(rx), why
    gate_python(b)
    # A box python3 older than 3.11 first on PATH (it answers --version; the recipe's other python3
    # calls run the real one).
    o = t / "py310"
    o.mkdir()
    old = '[ "$1" = --version ] && { echo "Python 3.10.12"; exit 0; }'
    b.stub("python3", f'{old}\nexec "{b.real_py3}" "$@"', o)
    out = b.check(1, b.gh_target, pre=o)
    shutil.rmtree(o)
    assert out.has(
        f"python3 WRONG VERSION {o}/python3 reports 3.10.12, want 3.11 or later (the kit scripts "
        "read TOML with tomllib); install Python 3.11 or later as the box python3 (Debian 12, "
        "Ubuntu 24.04: apt install python3), first on PATH"
    ), f"box python3 3.10: no WRONG VERSION line naming 3.11 and the fix: {out.text}"
    out = b.check(1, b.gh_target, PI_STUB_VERSION="0.0.1")
    assert out.has(
        f"pi     WRONG VERSION {b.bin}/pi reports 0.0.1, want {b.pin} (pi-version); "
        f"npm install -g --ignore-scripts @earendil-works/pi-coding-agent@{b.pin}"
    ), f"pi 0.0.1: no WRONG VERSION line naming the pin and the install command: {out.text}"
    assert not out.find(r"(?i)^browser"), (
        f"GitHub target without qc.toml [browser] has a browser line: {out.text}"
    )
    b.nomodel()
    say(
        "install-check: ok (Linear target: linear missing names v3.1.0 and the install path, "
        "exit 1; at the pin ok; another release named; linear hidden alone, mise in its dir ok; "
        f"GitHub target never checks linear nor a browser; gate Python {b.ppin} ok, not installed "
        "MISSING naming uv python install --no-bin and just check refusing, exit 1; box python3 "
        f"ok, 3.10 WRONG VERSION, exit 1; pi {b.pin} (pi-version) ok, pi 0.0.1 WRONG VERSION "
        "naming the pin and npm install, exit 1; no model call)"
    )


def gate_python(b: Box) -> None:
    """The gate's Python not installed (no managed install, the box's own Pythons not taken):
    named with the fix, exit 1; `just check` in a copy of the kit refuses before any item, naming
    it."""
    t = b.t
    fix = (
        f"uv python install --no-bin {b.ppin} (--no-bin: no python3.X link in ~/.local/bin, which "
        "would change"
    )
    nopy = {"UV_PYTHON_INSTALL_DIR": str(t / "nopy"), "UV_PYTHON_PREFERENCE": "only-managed"}
    out = b.check(
        1, b.gh_target, UV_PYTHON_INSTALL_DIR=str(t / "nopy"), UV_PYTHON_PREFERENCE="only-managed"
    )
    assert f"python gate {b.ppin} MISSING (.python-version); {fix}" in out.text, (
        f"gate Python not installed: no MISSING line naming the fix: {out.text}"
    )
    b.kit_copy(t / "kit")
    env = {**os.environ, "MISE_DATA_DIR": b.s.env["MISE_DATA_DIR"], **nopy}
    p = b.run(None, ["just", "check"], t / "kit", env, "just check without the gate's Python")
    want = (
        f"check-tests: the gate's Python {b.ppin} (.python-version) is not installed; install it "
        f"once, with network: {fix}"
    )
    why = (
        f"just check without the gate's Python: not refused naming the fix (exit {p.rc}): {p.text}"
    )
    assert p.rc != 0, why
    assert want in p.text, why


def box(s: Scratch) -> None:
    """tests/install-check-box.sh: the box facts (#461) and the missing official tools."""
    b, t, home = Box(s), s.root, s.home
    gh = b.gh_target
    # Every probe at a good value, each line ok and the manual sharing step printed, exit 0.
    out = b.check(0, gh)
    for x in (
        "kernel 6.12.0 ok (6.6 or later, the qc sandbox)",
        "userns ok (unshare -rm true, the qc sandbox)",
        f"state  ok  {t}/state/octo-feather (octo-feather-state)",
        f"kit    ok  {b.kitinst} on main (OCTO_FEATHER_KIT_INSTALL)",
        f"agent-browser browser ok  {b.okchrome} (outside {home}/.cache)",
        f"ffmpeg ok  {b.bin}/ffmpeg (optional: agent-browser video recording)",
    ):
        assert out.has(x), f"box facts at good values: not every ok line: {out.text}"
    assert out.full(
        r"sharing MANUAL exe\.dev Private sharing cannot be checked from inside the box; on the "
        r"exe\.dev VM that hosts reviews, from your own machine: ssh exe\.dev share set-private "
        r"\S+ \(never share set-public: a public share has no login\)"
    ), f"no manual sharing step: {out.text}"
    # ripgrep is a required srt dependency: the stubs' PATH decides its presence, never the host's.
    rg = "rg ok (srt, the qc sandbox, needs it)"
    assert out.has(rg), f"rg present: no ok line: {out.text}"
    (b.bin / "rg").rename(t / "rg")
    out = b.check(1, gh)
    assert out.has("rg MISSING (srt, the qc sandbox, needs it); sudo apt install ripgrep"), (
        f"rg absent: no MISSING line with package fix: {out.text}"
    )
    (t / "rg").rename(b.bin / "rg")
    out = b.check(0, gh)
    assert out.has(rg), f"rg restored: no ok line: {out.text}"
    # A kernel older than 6.6: TOO OLD naming the upgrade, exit 1.
    b.kernel("6.1.0")
    out = b.check(1, gh)
    b.kernel("6.12.0")
    assert out.full(
        r"kernel 6\.1\.0 TOO OLD, want 6\.6 or later \(the qc sandbox overlay needs tmpfs user "
        r"xattrs: scripts/octo-feather-qc-sandbox\); boot a 6\.6 or later kernel, then reboot "
        r"\(Debian 12: .*sudo apt install -t bookworm-backports "
        r"linux-image-\$\(dpkg --print-architecture\); Ubuntu 22\.04: sudo apt install "
        r"linux-generic-hwe-22\.04\)"
    ), f"kernel 6.1.0: no TOO OLD line naming the upgrade: {out.text}"
    # unshare -rm refused: FAILED naming its error and a fix (the sysctl that turns them off here,
    # or the container), exit 1.
    (t / "userns-off").touch()
    out = b.check(1, gh)
    (t / "userns-off").unlink()
    assert out.full(
        r"userns FAILED unshare -rm true: unshare: write failed /proc/self/uid_map: Operation not "
        r"permitted \(the qc sandbox runs its judge in unprivileged user namespaces, #404\); "
        r'(allow them: printf ".*" \| sudo tee /etc/sysctl\.d/60-octo-feather-userns\.conf && '
        r"sudo sysctl --system|no sysctl here turns them off .*)"
    ), f"user namespaces refused: no FAILED line naming the error and the fix: {out.text}"
    # The state folder without lanes/: MISSING naming mkdir -p, exit 1.
    lanes = t / "state/octo-feather/lanes"
    lanes.rmdir()
    out = b.check(1, gh)
    lanes.mkdir()
    assert out.has(
        f"state  MISSING {lanes} (the session state folder, octo-feather-state); mkdir -p {lanes}"
    ), f"state folder without lanes/: no MISSING line naming mkdir -p: {out.text}"
    kit_install(b)
    kit_live(b)
    tools(b)
    b.nomodel()
    say(
        "install-check-box: ok (box facts: kernel, userns, state, kit install (a clone or a "
        "detached worktree at main, OCTO_FEATHER_KIT_INSTALL set or not), agent-browser Chrome, "
        "ffmpeg each ok and each gap named with its fix, the sharing step printed; herdr, gh, jq, "
        "git MISSING with their install; no model call)"
    )


def kit_install(b: Box) -> None:
    """The kit install: detached on main ok; on another branch NOT ON MAIN naming git switch
    main; a worktree (the box's layout: the main checkout first in git worktree list, the install
    a detached worktree beside it, #422) detached at main ok, on a branch NOT ON MAIN naming
    switch --detach origin/main; a folder that is no clone named with the fix; exit 1."""
    t, gh, k = b.t, b.gh_target, str(b.kitinst)
    b.git("-C", k, "checkout", "-q", "--detach")
    out = b.check(0, gh)
    assert out.has(f"kit    ok  {k} on main (OCTO_FEATHER_KIT_INSTALL)"), (
        f"kit install detached on main: not ok: {out.text}"
    )
    b.git("-C", k, "checkout", "-q", "-b", "feat")
    out = b.check(1, gh)
    assert out.has(
        f"kit    NOT ON MAIN {k} is on branch feat (OCTO_FEATHER_KIT_INSTALL; {KIT_FIX}); "
        f"{ON_MAIN}: git -C {k} switch main"
    ), f"kit install on a branch: no NOT ON MAIN line naming git switch main: {out.text}"
    wt = t / "kitwt"
    b.git("-C", k, "checkout", "-q", "main")
    b.git("-C", k, "worktree", "add", "-q", "--detach", str(wt), "main")
    out = b.check(0, gh, OCTO_FEATHER_KIT_INSTALL=str(wt))
    assert out.has(f"kit    ok  {wt} on main (OCTO_FEATHER_KIT_INSTALL)"), (
        f"kit install a detached worktree at main: not ok: {out.text}"
    )
    b.git("-C", str(wt), "switch", "-q", "-c", "wt")
    out = b.check(1, gh, OCTO_FEATHER_KIT_INSTALL=str(wt))
    assert out.has(
        f"kit    NOT ON MAIN {wt} is on branch wt (OCTO_FEATHER_KIT_INSTALL; {KIT_FIX}); "
        f"{ON_MAIN}: git -C {wt} switch --detach origin/main"
    ), (
        "kit install a worktree on a branch: no NOT ON MAIN line naming switch --detach "
        f"origin/main: {out.text}"
    )
    (t / "noclone").mkdir()
    out = b.check(1, gh, OCTO_FEATHER_KIT_INSTALL=str(t / "noclone"))
    # a kit copy with no origin (tests/user-mise.sh): the placeholder
    url = b.run(
        None, ["git", "-C", str(ROOT), "config", "--get", "remote.origin.url"], t, b.s.env, ""
    )
    assert out.has(
        f"kit    NOT A CLONE {t}/noclone (OCTO_FEATHER_KIT_INSTALL; {KIT_FIX}); git clone "
        f"{url.text if url.rc == 0 else '<kit url>'} {t}/noclone, or set "
        "OCTO_FEATHER_KIT_INSTALL to the install clone"
    ), f"kit install not a clone: no NOT A CLONE line naming git clone: {out.text}"


def kit_live(b: Box) -> None:
    """OCTO_FEATHER_KIT_INSTALL unset: the install is the kit dir the recipe runs from, as
    octo-feather-lane's kit_install() says (post-merge step 3 runs install-check there): a kit
    copy laid out as the box's (a clone's main checkout first, the install a detached worktree at
    main, its tools the kit's node_modules) is ok there; with a commit off main, NOT ON MAIN,
    exit 1."""
    t, kit, live_dir = b.t, str(b.t / "kit"), b.t / "kitlive"
    b.kit_copy(t / "kit")
    b.git("-C", kit, "init", "-q")
    b.git("-C", kit, "add", "-A")
    b.git("-C", kit, "commit", "-q", "-m", "kit")
    b.git("clone", "-q", "--bare", kit, str(t / "kit-o.git"))
    b.git("clone", "-q", str(t / "kit-o.git"), str(t / "kitmain"))
    b.git("-C", str(t / "kitmain"), "worktree", "add", "-q", "--detach", str(live_dir), "main")
    (live_dir / "node_modules").symlink_to(ROOT / "node_modules")

    def live(want: int) -> Out:
        """install-check from the kit install's own justfile, OCTO_FEATHER_KIT_INSTALL unset."""
        env = b.env(b.path())
        del env["OCTO_FEATHER_KIT_INSTALL"]
        cmd = ["just", "-f", str(live_dir / "justfile"), "install-check"]
        what = "kit install a detached worktree, OCTO_FEATHER_KIT_INSTALL unset"
        return b.run(want, cmd, b.gh_target, env, what)

    out = live(0)
    assert out.has(f"kit    ok  {live_dir} on main (the kit dir)"), (
        f"the box's layout, OCTO_FEATHER_KIT_INSTALL unset: kit line not ok: {out.text}"
    )
    b.git("-C", str(live_dir), "commit", "-q", "--allow-empty", "-m", "off")
    out = live(1)
    assert out.has(
        f"kit    NOT ON MAIN {live_dir} is on a detached HEAD off main (the kit dir; {KIT_FIX}); "
        f"{ON_MAIN}: git -C {live_dir} switch --detach origin/main"
    ), f"the box's layout, a commit off main: no NOT ON MAIN line: {out.text}"


def tools(b: Box) -> None:
    """agent-browser's Chrome under the cache folder the qc sandbox masks, and none found: each
    named with agent-browser install, exit 1; ffmpeg absent: an OPTIONAL line naming the install,
    the check still passing; herdr, gh, jq and git absent: each MISSING with its official install
    command, exit 1."""
    t, gh, home = b.t, b.gh_target, b.s.home
    abfix = (
        f"agent-browser install (Chrome for Testing into {home}/.agent-browser/browsers, which "
        "agent-browser searches first; drop any AGENT_BROWSER_EXECUTABLE_PATH, or executablePath "
        "in ~/.agent-browser/config.json, naming another)"
    )
    cached = home / ".cache/ms-playwright/chromium-1248/chrome-linux64/chrome"
    b.chrome(cached)
    out = b.check(1, gh)
    assert out.has(
        f"agent-browser browser UNREADABLE IN THE QC SANDBOX {cached} is under {home}/.cache, "
        f"which the sandbox masks; {abfix}"
    ), f"agent-browser Chrome under the cache folder: not refused with the fix: {out.text}"
    b.chrome(None)
    out = b.check(1, gh)
    b.chrome(b.okchrome)
    assert out.has(
        f"agent-browser browser MISSING (agent-browser doctor --offline names no Chrome); {abfix}"
    ), f"agent-browser without Chrome: no MISSING line with the fix: {out.text}"
    (b.bin / "ffmpeg").rename(t / "ffmpeg")
    saved, b.clean = b.clean, b.hide(["ffmpeg"], b.clean)
    out = b.check(0, gh)
    b.clean = saved
    (t / "ffmpeg").rename(b.bin / "ffmpeg")
    assert out.has(
        "ffmpeg OPTIONAL not installed; only agent-browser video recording needs it, the check "
        "passes; to record video: sudo apt install ffmpeg"
    ), f"no ffmpeg: no OPTIONAL line naming the install, or the check failed: {out.text}"
    aside = t / "aside"
    aside.mkdir()
    for n in ("herdr", "gh"):
        (b.bin / n).rename(aside / n)
    saved, b.clean = b.clean, b.hide(["herdr", "gh", "jq", "git"], b.clean)
    out = b.check(1, gh)
    b.clean = saved
    for n in ("herdr", "gh"):
        (aside / n).rename(b.bin / n)
    why = f"herdr, gh, jq, git absent: not each MISSING with its install command: {out.text}"
    assert out.has("herdr  MISSING; curl -fsSL https://herdr.dev/install.sh | sh"), why
    assert out.has("jq     MISSING; sudo apt install jq (Debian, Ubuntu)"), why
    assert out.has("git    MISSING; sudo apt install git (Debian, Ubuntu)"), why
    assert out.find(
        r"^gh     MISSING; \(Debian, Ubuntu: GitHub CLI's apt repository\) "
        r".*https://cli\.github\.com/packages stable main.* && sudo apt install gh -y$"
    ), why


def browser(s: Scratch) -> None:
    """tests/install-check-browser.sh: a target's headless browser, the kit's PATHs,
    agent-browser."""
    b, t, home = Box(s), s.root, s.home
    # Browser target: qc.toml declares the headless browser at a Playwright pin.
    br = t / "browser"
    b.git("init", "-q", str(br))
    (br / "qc.toml").write_text(
        'format = 1\n[entry]\ncommand = "app"\n[services]\n[fixture]\n[values]\n'
        '[browser]\nplaywright = "1.64.1"\n'
    )
    folder = home / ".local/share/octo-feather/ms-playwright/1.64.1"
    out = b.check(1, br)
    assert out.has(
        f"browser MISSING (want Playwright 1.64.1 headless Chromium shell in {folder}); install: "
        f"PLAYWRIGHT_BROWSERS_PATH={folder} npx -y playwright@1.64.1 install --only-shell chromium"
    ), (
        "browser target without the browser: no MISSING line naming the pin, folder and install "
        f"command: {out.text}"
    )
    (folder / "chromium_headless_shell-1248").mkdir(parents=True)
    (folder / "chromium_headless_shell-1248/INSTALLATION_COMPLETE").touch()
    out = b.check(0, br)
    assert out.has(
        f"browser ok  {folder}/chromium_headless_shell-1248 (Playwright 1.64.1; "
        f"PLAYWRIGHT_BROWSERS_PATH={folder})"
    ), f"browser target, fake headless shell at the pin: not ok: {out.text}"
    kit_paths(b)
    d = home / ".cache/d"
    shutil.copytree(home / ".local/share/octo-feather", d / "octo-feather", symlinks=True)
    out = b.check(1, br, XDG_DATA_HOME=str(d))
    assert out.find(
        rf"^browser UNREADABLE IN THE QC SANDBOX {re.escape(str(d))}/octo-feather/ms-playwright/"
        rf"1\.64\.1 is under {re.escape(str(home))}/\.cache"
    ), f"browser folder under the masked cache folder: not refused: {out.text}"
    # agent-browser (spec remote#acceptance-install-agent-browser): the stub at 0.40.0 ok; another
    # release WRONG VERSION; on a box without it, MISSING naming 0.40.0 and the npm install.
    # Without it: each PATH dir holding one is mirrored minus it.
    assert out.has("agent-browser version 0.40.0 ok (agent-browser-version)"), (
        f"agent-browser at the pin: no ok line: {out.text}"
    )
    b.agent_browser("0.39.4")
    out = b.check(1, b.gh_target)
    assert out.has(
        f"agent-browser WRONG VERSION {b.bin}/agent-browser reports 0.39.4, want 0.40.0 "
        f"(agent-browser-version); {AB_INSTALL}"
    ), f"agent-browser 0.39.4: no WRONG VERSION line naming 0.40.0 and the install: {out.text}"
    # mise's shims too: an agent-browser npm put in mise's node has a shim there (#463).
    (b.bin / "agent-browser").unlink()
    saved = b.clean, b.shims
    b.clean, b.shims = b.hide(["agent-browser"], b.clean), b.hide(["agent-browser"], [b.shims])[0]
    out = b.check(1, b.gh_target)
    b.clean, b.shims = saved
    assert out.has(f"agent-browser MISSING (want 0.40.0, agent-browser-version); {AB_INSTALL}"), (
        f"no agent-browser on PATH: not listed MISSING with 0.40.0 and the install: {out.text}"
    )
    b.agent_browser("0.40.0")
    b.nomodel()
    say(
        "install-check-browser: ok (browser target: MISSING names Playwright 1.64.1, the folder "
        "and the install command, exit 1; fake shell at the pin ok; folder under ~/.cache "
        "refused; in the kit a stale node in a system dir before mise's shims a NOTE only, exit "
        "0, one ahead of mise's dirs SHADOWED, shims first ok; agent-browser 0.40.0 ok, 0.39.4 "
        "WRONG VERSION, none MISSING naming 0.40.0 and npm install, exit 1; no model call)"
    )


def kit_paths(b: Box) -> None:
    """The PATHs the kit runs its tools from, in the kit itself (post-merge step 3 runs
    install-check there from the director's pane, #422): its recipes' PATH (the justfile puts
    mise's dirs before the first system dir) and a pane's (pi-role's with_mise). (a) A caller PATH
    with a system dir holding stale launchers before mise's shims (a shell started before the
    shims went first): ok and a NOTE line naming the launcher, the kit unaffected, exit 0. (b) A
    stale launcher in a dir the caller puts ahead (the justfile and pi-role keep such dirs
    first): SHADOWED, exit 1. (c) mise's shims first: ok, no NOTE. The stale /usr/local/bin is a
    scratch dir bound over it in a user namespace (unshare -rm, as tests/qc.sh needs), so no box
    dir is touched; the kit's [browser] pin is the fake shell."""
    t = b.t
    sysd = t / "sysbin"
    sysd.mkdir()
    b.stub("node", "echo v18.0.0", sysd)
    assert Path("/usr/local/bin").is_dir(), "no /usr/local/bin to bind the stale launchers over"
    bind = 'mount --bind "$1" /usr/local/bin && shift && exec "$@"'

    def inkit(want: int, path: str) -> Out:
        """install-check in the kit, /usr/local/bin holding only a stale node."""
        cmd = [b.real_unshare, "-rm", "sh", "-c", bind, "sh", str(sysd), "just", "install-check"]
        return b.run(want, cmd, ROOT, b.env(path), f"in the kit (PATH {path})")

    clean, shims = os.pathsep.join(b.clean), b.shims
    out = inkit(0, f"{b.bin}:/usr/local/bin:{shims}:{clean}")
    why = (
        "stale node in a system dir before mise's shims: want node ok and a NOTE line only: "
        f"{out.text}"
    )
    assert out.find(rf"^path   node ok  /\S+/node \({KIT}/mise\.lock\)$"), why
    assert "SHADOWED" not in out.text, why
    assert out.find(
        rf"^path   node NOTE /usr/local/bin/node comes first on your shell PATH, before the pinned "
        rf"{re.escape(shims)}/node \({KIT}/mise\.lock\); the kit is unaffected: its recipes "
        r"\(justfile\) and panes \(pi-role\) put mise first and run /\S+/node; to run the pinned "
        rf"one in this shell too, put {re.escape(shims)} first on PATH$"
    ), why
    o = t / "ahead"
    o.mkdir()
    shutil.copy(sysd / "node", o / "node")
    out = inkit(1, f"{o}:{b.bin}:/usr/local/bin:{shims}:{clean}")
    assert out.has(
        f"path   node SHADOWED {o}/node comes first on PATH, before the pinned {shims}/node "
        f"({ROOT}/mise.lock); remove or rename {o}/node, or put {shims} first on PATH"
    ), f"stale node ahead of mise's dirs on the kit's PATHs: no SHADOWED line: {out.text}"
    shutil.rmtree(o)
    out = inkit(0, f"{b.bin}:{shims}:/usr/local/bin:{clean}")
    why = f"mise's shims first: want ok, no NOTE: {out.text}"
    assert out.find(r"^path   node ok  "), why
    assert not out.find(r"^path   \S+ (NOTE|SHADOWED) "), why


def mise(s: Scratch) -> None:
    """tests/install-check-mise.sh: mise, a target's mise tools, the PATH rule and just."""
    b, t = Box(s), s.root
    # mise at mise-version everywhere; a repo the kit created (its own mise.toml, here the kit's
    # pins) gets each tool checked at its lock, PATH resolving to mise's; a repo the kit did not
    # create (the GitHub target) gets no tool line.
    mt = t / "created"
    b.git("init", "-q", str(mt))
    for f in ("mise.toml", "mise.lock"):
        shutil.copy(ROOT / f, mt)
    out = b.check(0, mt)
    why = f"created repo at the pins: no ok lines: {out.text}"
    assert out.has(f"mise   version {b.mpin} ok (mise-version)"), why
    assert out.full(rf"mise   shellcheck [0-9.]+ ok \({re.escape(str(mt))}/mise\.lock\)"), why
    # Each pinned tool's first hit on the caller's PATH (#422 item 2): mise's shim ok; a stale node
    # launcher first on PATH: SHADOWED naming it, the pinned shim and the fix, exit 1.
    why = f"created repo: no resolved-path ok lines for node and mise: {out.text}"
    assert out.has(f"path   node ok  {b.shims}/node ({mt}/mise.lock)"), why
    assert out.has(f"path   mise ok  {b.mdir}/mise (mise-version)"), why
    o = t / "stale"
    o.mkdir()
    b.stub("node", "echo v18.0.0", o)
    out = b.check(1, mt, pre=o)
    shutil.rmtree(o)
    assert out.has(
        f"path   node SHADOWED {o}/node comes first on PATH, before the pinned {b.shims}/node "
        f"({mt}/mise.lock); remove or rename {o}/node, or put {b.shims} first on PATH"
    ), (
        "stale node first on PATH: no SHADOWED line naming it, the pinned shim and the fix: "
        f"{out.text}"
    )
    npm_global(b)
    out = b.check(0, b.gh_target)
    why = f"a repo the kit did not create got mise tool lines: {out.text}"
    assert out.has(f"mise   version {b.mpin} ok (mise-version)"), why
    assert not out.find(r"^mise   [^v]"), why
    o = t / "first"  # first on the caller's PATH, which the justfile keeps ahead of its tools
    o.mkdir()
    stale = '[ "$1" = --version ] && { echo "2000.1.1 linux-x64"; exit 0; }'
    b.stub("mise", f'{stale}\nexec "{shutil.which("mise")}" "$@"', o)
    out = b.check(1, b.gh_target, pre=o)
    shutil.rmtree(o)
    pin = re.escape(b.mpin)
    assert out.find(
        rf"^mise   WRONG VERSION {re.escape(str(o))}/mise reports 2000\.1\.1, want {pin} "
        rf"\(mise-version\); install mise {pin}: "
    ), f"mise 2000.1.1: no WRONG VERSION line naming mise-version: {out.text}"
    assert out.has(
        f"path   mise SHADOWED {o}/mise comes first on PATH, before the pinned {b.mdir}/mise "
        f"(mise-version); remove or rename {o}/mise, or put {b.mdir} first on PATH"
    ), (
        "stale mise first on PATH: no SHADOWED line naming it, the pinned mise and the fix: "
        f"{out.text}"
    )
    just_pin(b, mt)
    b.nomodel()
    say(
        "install-check-mise: ok (mise at its pin ok, 2000.1.1 named, exit 1; a created repo's "
        "mise.toml tools ok, MISSING named, exit 1; a repo the kit did not create gets no tool "
        "line; a stale node or mise first on PATH SHADOWED naming the pinned path and the fix, "
        "exit 1; pi and agent-browser in the target's mise node ok by their pins; just checked at "
        "the kit lock in every target (ok, 0.0.1 WRONG VERSION); no model call)"
    )


def npm_global(b: Box) -> None:
    """pi and agent-browser that `npm install -g` put in the target's mise node bin dir (a path:
    version stands in for it, trusted through the environment only): pinned by pi-version and
    agent-browser-version, not mise.lock, so the stubs at those pins first on PATH are ok (#463:
    the scratch-HOME proof's npm-installed pi made this SHADOWED)."""
    t = b.t
    npm = t / "npmglobal"
    b.git("init", "-q", str(npm))
    (t / "node/bin").mkdir(parents=True)
    for n in ("pi", "agent-browser"):
        shutil.copy(b.bin / n, t / "node/bin" / n)
    (npm / "mise.toml").write_text(f'[tools]\nnode = "path:{t}/node"\n')
    out = b.check(0, npm, MISE_TRUSTED_CONFIG_PATHS=str(npm))
    why = (
        "pi and agent-browser in the target's mise node bin dir: not checked by their version "
        f"pins: {out.text}"
    )
    assert out.has(f"path   pi ok  {b.bin}/pi (pi-version)"), why
    assert out.has(f"path   agent-browser ok  {b.bin}/agent-browser (agent-browser-version)"), why


def just_pin(b: Box, mt: Path) -> None:
    """just, which the kit runs in every target, at the kit mise.lock version even in a repo the
    kit did not create: ok there with no mise tool or MISSING line; a just reporting another
    release: WRONG VERSION naming the kit lock and the fix, exit 1. The stub forwards all but
    --version to the real just (the gate guard asks it). In the created repo MT: its own just pin
    installed ok, not installed MISSING naming the install."""
    lock = asked("mise", "-C", str(ROOT), "ls", "--local", "--json")
    jv = field(lock, "mise ls --local --json", "just", 0, "version")
    out = b.check(0, b.gh_target)
    why = f"foreign target, just at the kit version: no ok line, or a mise demand: {out.text}"
    assert out.has(f"just   version {jv} ok (kit mise.lock)"), why
    assert "MISSING" not in out.text, why
    o = b.t / "first"
    o.mkdir()
    b.stub(
        "just",
        f'[ "$1" = --version ] && {{ echo "just 0.0.1"; exit 0; }}\nexec "{b.bin}/just" "$@"',
        o,
    )
    out = b.check(1, b.gh_target, pre=o)
    shutil.rmtree(o)
    assert out.full(
        rf"just   WRONG VERSION {re.escape(str(o))}/just reports 0\.0\.1, want {re.escape(jv)} "
        r"\(kit mise\.lock\); the kit runs it in every target: .*"
    ), f"foreign target, just 0.0.1: no WRONG VERSION line naming the kit lock: {out.text}"
    (mt / "mise.toml").write_text(f'[tools]\njust = "{jv}"\n')
    out = b.check(0, mt)
    assert out.has(f"mise   just {jv} ok ({mt}/mise.lock)"), (
        f"created repo, just at an installed pin: no ok line: {out.text}"
    )
    (mt / "mise.toml").write_text('[tools]\njust = "0.0.1"\n')
    out = b.check(1, mt)
    assert out.has(
        f"mise   just 0.0.1 MISSING ({mt}/mise.lock); {ROOT}/scripts/octo-feather-mise-install {mt}"
    ), f"created repo, just at a pin not installed: no MISSING line naming the install: {out.text}"


def models(s: Scratch) -> None:
    """tests/install-check-models.sh: the review service, and `just install-check-models`."""
    b, t, home = Box(s), s.root, s.home
    gh = b.gh_target
    # The review service (spec remote#review-service, #review-setup): active and enabled ok;
    # inactive or not installed NOT RUNNING, no systemctl MISSING, each naming Spec Chat's
    # installer with --public <vm>.exe.xyz --service, exit 1.
    review_fix = (
        rf"{re.escape(str(home))}/src/spec-chat/scripts/install-spec-chat --review "
        rf"{KIT}/docs/specs/index\.spec\.html --public \S+\.exe\.xyz --service "
        r"\(remote#review-setup\)"
    )
    out = b.check(0, gh)
    assert out.has(
        "review ok  spec-chat-review.service active, enabled (Spec Chat's review service, "
        "systemd --user)"
    ), f"review service up: no ok line: {out.text}"
    # The model check is its own recipe (spec remote#host-models): one line names it, and no run
    # above called a model.
    assert out.has(
        "models MANUAL not checked here (no model call); at box setup and after a model key "
        "change: just install-check-models"
    ), f"no line naming just install-check-models: {out.text}"
    b.nomodel()
    b.unit("inactive", "")
    out = b.check(1, gh)
    assert out.full(
        r"review NOT RUNNING spec-chat-review\.service is inactive, not installed \(want active, "
        rf"enabled: the systemd user service box setup installs\); {review_fix}"
    ), f"review service not installed: no NOT RUNNING line naming the installer: {out.text}"
    b.unit("failed", "enabled")
    out = b.check(1, gh)
    rx = rf"review NOT RUNNING spec-chat-review\.service is failed, enabled .*; {review_fix}"
    assert out.full(rx), f"review service failed: not named: {out.text}"
    b.unit("active", "enabled")
    (b.bin / "systemctl").rename(t / "systemctl")
    saved, b.clean = b.clean, b.hide(["systemctl"], b.clean)
    out = b.check(1, gh)
    b.clean = saved
    (t / "systemctl").rename(b.bin / "systemctl")
    assert out.full(
        r"review MISSING no systemctl: the review service runs as a systemd user service "
        rf"\(spec-chat-review\.service\); on a systemd box: {review_fix}"
    ), f"no systemctl: no MISSING line naming the installer: {out.text}"
    model_probes(b)
    say(
        "install-check-models: ok (review service ok, NOT RUNNING and no systemctl MISSING naming "
        "the installer; models MANUAL naming just install-check-models, no model call; "
        "install-check-models with a stub pi first on PATH: role models and the judgment model "
        "ok, trailing-junk keys REJECTED (models.json, auth.json), proxy UNREACHABLE, judgment "
        "model not listed FAILED, key never printed)"
    )


ISSUED = "sk-proxy-0123456789abcdefghijklmnopqrstuv"
PROXY, UNREACHABLE = "https://proxy.example/v1", "https://unreachable.example/v1"
RERUN = "then rerun just install-check-models"
JUNK = "(the key there ends in or holds whitespace or terminal characters)"
EXACT = "or its environment, exactly, no trailing characters"
JWHO = "judgment model (evals/judgment-model.json): the advisory judge, judgment benches"


class Proxy:
    """The model proxy the stub pi plays (tests/fixtures/install-check/pi), first on PATH in its
    own dir, Pi's agent dir holding its provider config and stored key."""

    def __init__(self, b: Box) -> None:
        self.b, t = b, b.t
        self.mbin, self.agent = t / "mbin", t / "pi-agent"
        self.mbin.mkdir()
        self.agent.mkdir()
        (self.mbin / "pi").symlink_to(PI_STUB)
        (t / "issued").write_text(ISSUED)
        model = (ROOT / "evals/judgment-model.json").read_text()
        self.judge = field(model, "evals/judgment-model.json", "model")
        self.jprov = self.judge.split("/", 1)[0]
        self.path = f"{self.mbin}{os.pathsep}{os.environ['PATH']}"

    def keys(self, akey: str, obase: str, jkey: str) -> None:
        """Pi's provider config (models.json) and stored key (auth.json)."""
        providers = {
            "anthropic": {"baseUrl": "https://proxy.example/", "apiKey": akey},
            "openai": {"baseUrl": obase, "apiKey": ISSUED},
        }
        (self.agent / "models.json").write_text(json.dumps({"providers": providers}))
        stored = {self.jprov: {"type": "api_key", "key": jkey}}
        (self.agent / "auth.json").write_text(json.dumps(stored))

    def probe(self, want: int, avail: str | None = None) -> Out:
        """The recipe run from the scratch with the stub first on PATH, the classifiers Pi lists
        AVAIL (default the judgment model); the key never printed nor on a command line."""
        b = self.b
        b.calls.write_text("")
        env = b.s.env | {
            "PI_CODING_AGENT_DIR": str(self.agent),
            "PI_STUB_ISSUED": str(b.t / "issued"),
            "PI_STUB_CLASSIFIERS": self.judge if avail is None else avail,
            "PATH": self.path,
        }
        cmd = ["just", "-f", str(ROOT / "justfile"), "install-check-models"]
        out = b.run(want, cmd, b.t, env, "install-check-models")
        logged = b.calls.read_text()
        why = f"a key was printed or passed on a command line: {out.text} {logged}"
        assert ISSUED not in out.text, why
        assert ISSUED not in logged, why
        return out


def roles(model: str) -> str:
    """The roles whose role file names MODEL, as install-check-models lists them."""
    files = sorted((ROOT / "agents").glob("*.md"))
    return ", ".join(f.stem for f in files if f"model: {model}" in f.read_text().splitlines())


def model_probes(b: Box) -> None:
    """just install-check-models (spec remote#host-models): the stub pi plays the model proxy; it
    is first on PATH, which the recipe's own pi line proves before any probe case. Each model a
    role file names answers one print-mode call, the judgment model (evals/judgment-model.json)
    one classify call through octo-feather-qa's bench extension: right keys ok; a key with
    trailing terminal characters REJECTED (a role model's in models.json, the judgment model's in
    auth.json); a proxy that does not answer UNREACHABLE; a judgment model Pi does not list
    FAILED; each with its users and the fix, the key never printed nor on a command line."""
    px = Proxy(b)
    assert shutil.which("pi", path=px.path) == str(px.mbin / "pi"), "stub pi is not first on PATH"
    ra, ro = roles("anthropic/claude-opus-5-5"), roles("openai/gpt-6.1-sol")
    why = (
        "the role files no longer name anthropic/claude-opus-5-5 and openai/gpt-6.1-sol, or name "
        f"the judgment model {px.judge}: update this test"
    )
    assert ra, why
    assert ro, why
    assert px.judge, why
    assert not roles(px.judge), why
    px.keys(ISSUED, PROXY, ISSUED)
    out = px.probe(0)
    assert out.has(
        f"models pi {px.mbin}/pi (one short call per role model and the judgment model, no tools; "
        f"Pi reads each key from {px.agent}/models.json, {px.agent}/auth.json or its environment)"
    ), f"install-check-models did not resolve the stub pi first: {out.text}"
    log = b.calls.read_text().splitlines()
    calls = [" ".join(argv(x, "the stub pi's log")) for x in log]
    why = (
        "right keys: not one ok line and one call per role model and the judgment model: "
        f"{out.text} {calls}"
    )
    assert out.has(f"model  anthropic/claude-opus-5-5 ok (roles {ra})"), why
    assert out.has(f"model  openai/gpt-6.1-sol ok (roles {ro})"), why
    assert out.has(f"model  {px.judge} ok ({JWHO})"), why
    assert sum(c.startswith("-p --mode json ") for c in calls) == 2, why
    assert sum(" -p /octo-feather-bench " in c for c in calls) == 1, why
    assert len(calls) == 3, why
    bad_keys(px, ra, ro)


def bad_keys(px: Proxy, ra: str, ro: str) -> None:
    """The gaps install-check-models names, each with its users (role models RA, RO) and fix."""
    judge, agent = px.judge, px.agent
    px.keys(ISSUED + "\x1b[201~", PROXY, ISSUED)
    out = px.probe(1)
    why = f"key with trailing junk: no REJECTED line with roles and fix: {out.text}"
    assert out.has(
        f"model  anthropic/claude-opus-5-5 REJECTED key (401) for roles {ra} {JUNK}; put the key "
        f"the model proxy issued for provider anthropic in {agent}/models.json "
        f"(providers.anthropic.apiKey) {EXACT}, {RERUN}"
    ), why
    assert out.has(f"model  openai/gpt-6.1-sol ok (roles {ro})"), why
    px.keys(ISSUED, PROXY, ISSUED + "\n")
    out = px.probe(1)
    assert out.has(
        f"model  {judge} REJECTED key (401) for {JWHO} {JUNK}; put the key the model proxy issued "
        f"for provider {px.jprov} in {agent}/auth.json ({px.jprov}.key) {EXACT}, {RERUN}"
    ), (
        "judgment model key with a trailing newline: no REJECTED line with its users and fix: "
        f"{out.text}"
    )
    px.keys(ISSUED, UNREACHABLE, ISSUED)
    out = px.probe(1)
    assert out.has(
        f"model  openai/gpt-6.1-sol UNREACHABLE (Connection error.) for roles {ro}; the model "
        f"proxy for provider openai did not answer: check this box reaches {UNREACHABLE} "
        f"({agent}/models.json, providers.openai.baseUrl) and the proxy is up, {RERUN}"
    ), f"proxy not answering: no UNREACHABLE line with roles and fix: {out.text}"
    px.keys(ISSUED, PROXY, ISSUED)
    out = px.probe(1, avail="")
    assert out.has(
        f"model  {judge} FAILED (Pi lists no classifier {judge}: no key for its provider, or not "
        f"in Pi catalog) for {JWHO}; run pi --model {judge} -p ok by hand for the full error Pi "
        f"gives, {RERUN}"
    ), f"judgment model Pi does not list: no FAILED line: {out.text}"


if __name__ == "__main__":
    main(tracker, box, browser, mise, models)
