"""tests/user-mise.sh's fixture user and #493's assertions, a command it runs in a namespace (#495).

`check.py setup`: the fixture user's files: fake global installs (a python of another minor than
.python-version, erlang, rust with its cargo and some-cli in ~/.cargo/bin), their version links,
the global ~/.config/mise/config.toml, pnpm's store named, the kit clone's uncommitted
files committed, mise's shims.
`check.py assert`: #493's fixture assertions (1)-(5), one ok or FAIL line each; exit 1 on any FAIL.

Every command runs as the fixture user through tests/user-mise.sh's wrapper $USER_MISE_T/user, the
one place the user's environment is set. Inputs (env): USER_MISE_T (the scratch dir), USER_MISE_HOME
(the fixture HOME's path), USER_MISE_GATE_PY (the gate's Python, which the fake python3 runs).
"""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import cast

T = Path(os.environ["USER_MISE_T"])
H = Path(os.environ["USER_MISE_HOME"])
D = H / ".local/share/mise"
K = H / "src/octo-feather"
USER = str(T / "user")
UP = f"{D}/shims:{H}/.local/bin:/usr/local/bin:/usr/bin:/bin"
GLOBAL = ("python", "erlang", "rust")
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "init.defaultBranch=main"]
COMMITTER = (
    "GIT_AUTHOR_NAME=t",
    "GIT_AUTHOR_EMAIL=t@t",
    "GIT_COMMITTER_NAME=t",
    "GIT_COMMITTER_EMAIL=t@t",
)
FAILED: list[str] = []


def say(line: str, *, err: bool = False) -> None:
    (sys.stderr if err else sys.stdout).write(line + "\n")
    (sys.stderr if err else sys.stdout).flush()


def die(msg: str) -> None:
    say(f"user-mise: {msg}", err=True)
    sys.exit(1)


def pyv() -> str:
    """The global python's version: a minor other than .python-version's."""
    minor = int((K / ".python-version").read_text().strip().split(".")[1])
    return f"3.{13 if minor == 11 else 11}.9"


def user(
    cmd: list[str], cwd: Path = T, env: tuple[str, ...] = (), *, merge: bool = True
) -> tuple[int, str, str]:
    """CMD as the fixture user, ENV (K=V) on top of the user's environment: exit, stdout, stderr
    (stderr in stdout when MERGE)."""
    r = subprocess.run(
        [USER, "env", *env, *cmd],
        cwd=cwd,
        text=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT if merge else subprocess.PIPE,
        check=False,
    )
    return r.returncode, r.stdout or "", r.stderr or ""


def git(*args: str) -> str:
    return subprocess.run([*GIT, *args], capture_output=True, text=True, check=True).stdout.strip()


def setup() -> None:
    v = pyv()
    py = D / "installs/python" / v / "bin"
    erl = D / "installs/erlang/27.3/bin"
    for d in (py, erl, D / "installs/rust/1.80.0", H / ".cargo/bin", H / ".rustup"):
        d.mkdir(parents=True, exist_ok=True)
    (py / "python3").write_text(f'#!/bin/sh\nexec {os.environ["USER_MISE_GATE_PY"]} "$@"\n')
    (py / "python").symlink_to("python3")
    (erl / "erl").write_text("#!/bin/sh\necho erl\n")
    (D / "installs/rust/1.80.0/.installed").touch()
    for x in ("cargo", "some-cli"):
        (H / ".cargo/bin" / x).write_text(f"#!/bin/sh\necho {x}\n")
    for f in (py / "python3", erl / "erl", H / ".cargo/bin/cargo", H / ".cargo/bin/some-cli"):
        f.chmod(0o755)
    # The version links mise keeps beside an install (it adds them on its first run after one:
    # the user's are in place).
    for tool, ver in (("python", v), ("erlang", "27.3"), ("rust", "1.80.0")):
        parts = ver.split(".")
        for link in (".".join(parts[:-1]), parts[0], "latest"):
            p = D / "installs" / tool / link
            if not p.exists():
                p.symlink_to(f"./{ver}")
    (H / ".config/mise/config.toml").write_text(
        f'[tools]\npython = "{v}"\nerlang = "27.3"\nrust = "1.80.0"\n'
    )
    # pnpm's store, the box's (bound in), named: a project on another mount than the store (the
    # fixture's TMPDIR, its HOME being binds) would otherwise get a store of its own at that mount's
    # root, empty offline (on the box, HOME and /tmp share one mount).
    (H / ".config/pnpm").mkdir(parents=True, exist_ok=True)
    (H / ".config/pnpm/rc").write_text(f"store-dir={H}/.local/share/pnpm/store\n")
    # The kit clone with this checkout's files over it: one commit for what is not committed yet.
    git("-C", str(K), "add", "-A")
    if subprocess.run([*GIT, "-C", str(K), "diff", "--cached", "--quiet"], check=False).returncode:
        git("-C", str(K), "commit", "-q", "-m", "the checkout's uncommitted files")
    if user(["mise", "reshim"])[0]:
        die("mise reshim in the user's HOME failed")


def want(what: str, ok: object, detail: str = "") -> None:
    """One assertion: an ok line, or a FAIL line with the tail of DETAIL."""
    if ok:
        say(f"user-mise: ok   {what}")
        return
    FAILED.append(what)
    say(f"user-mise: FAIL {what}", err=True)
    for line in detail.splitlines()[-40:]:
        say(f"    {line}", err=True)


def snap() -> list[str]:
    """The user's mise config, installs and shims, and ~/.cargo: each entry's type, size, mode,
    link target, a file's and link's mtime (a dir's own is left out: mise's reshim on every install
    bumps the shims dir's with every shim unchanged), and the sha256 of every regular file but the
    box's bound kit installs."""
    hashed = [H / ".config/mise", D / "shims", H / ".cargo", *(D / "installs" / g for g in GLOBAL)]
    out: set[str] = set()
    for top in (H / ".config/mise", D / "installs", D / "shims", H / ".cargo"):
        for p in [top, *top.rglob("*")]:
            st = p.lstat()
            line = f"{p} {stat.S_IFMT(st.st_mode)} {st.st_size} {stat.S_IMODE(st.st_mode):o}"
            if not stat.S_ISDIR(st.st_mode):
                line += f" {st.st_mtime_ns}"
            if stat.S_ISLNK(st.st_mode):
                line += f" -> {p.readlink()}"
            elif stat.S_ISREG(st.st_mode) and any(p.is_relative_to(h) for h in hashed):
                line += f" {hashlib.sha256(p.read_bytes()).hexdigest()}"
            out.add(line)
    return sorted(out)


def field(obj: object, *keys: str) -> object:
    """OBJ[KEYS[0]][KEYS[1]]... of parsed JSON, None where a level is no object or lacks the key."""
    for k in keys:
        if not isinstance(obj, dict):
            return None
        obj = cast("dict[str, object]", obj).get(k)
    return obj


def doctor(*env: str) -> tuple[int, object]:
    rc, out, _ = user(["mise", "doctor", "--json"], env=env, merge=False)
    try:
        data: object = json.loads(out)
    except ValueError:
        data = None
    return rc, data


def doctor_view(d: object) -> list[object]:
    return [field(d, "dirs"), field(d, "errors"), field(d, "warnings")]


def state_entries() -> int:
    """Entries one level inside each dir of the user's mise state dir (tracked-configs...)."""
    s = H / ".local/state/mise"
    return sum(len(list(c.iterdir())) for c in s.iterdir() if c.is_dir()) if s.is_dir() else 0


def preconditions() -> object:
    b = min(p.name for p in (D / "installs").iterdir() if p.name not in GLOBAL)
    rc, out, _ = user(["touch", str(D / "installs" / b / ".user-mise-write")])
    want(
        "a write into the box's bound kit tool installs fails (read-only)",
        rc != 0 and "Read-only file system" in out,
        out,
    )
    rc, d0 = doctor()
    want("mise doctor --json under the user's HOME exits 0", rc == 0, json.dumps(d0))
    (T / "moved").mkdir(exist_ok=True)
    pinned = (
        f"MISE_DATA_DIR={D}",
        f"MISE_CACHE_DIR={H}/.cache/mise",
        f"MISE_CONFIG_DIR={H}/.config/mise",
    )
    rc, dm = doctor(f"HOME={T}/moved", *pinned)
    got = [field(dm, "dirs", k) for k in ("data", "cache", "config")]
    errs = field(dm, "errors")
    first = "none"
    if isinstance(errs, list) and errs:
        first = str(cast("list[object]", errs)[0]).replace("\n", " ")
    want(
        f"mise doctor --json under a moved HOME exits 1 (stale shims: {first}) and still prints"
        " dirs",
        rc == 1 and got == [str(D), f"{H}/.cache/mise", f"{H}/.config/mise"],
        f"rc {rc}: {json.dumps(dm)}",
    )
    v, pin = pyv(), (K / ".python-version").read_text().strip()
    rc, out, _ = user(
        ["sh", "-c", "command -v python3; mise which python3; mise ls --json python"], cwd=K
    )
    want(
        f"python3 first on PATH is mise's shim of the global python {v} (.python-version: {pin})",
        rc == 0
        and out.splitlines()[:2] == [f"{D}/shims/python3", f"{D}/installs/python/{v}/bin/python3"],
        out,
    )
    lock = (K / "mise.lock").read_text()
    locked = re.search(r"^\[\[tools\.(erlang|python|rust)\]\]", lock, re.MULTILINE)
    rc, out, _ = user(["mise", "ls", "--installed", "erlang"], cwd=K)
    want(
        "the global tools are installed and absent from the kit's mise.lock",
        not locked and "27.3" in out,
        user(["mise", "ls"], cwd=K)[1],
    )
    return d0


def target(d: Path, mise_toml: str = "") -> None:
    """A scratch target repo under the user's HOME with the demo spec's status file."""
    (d / "docs/specs").mkdir(parents=True)
    spec = K / "tests/fixtures/spec-status/good/demo.spec.html"
    (d / "docs/specs/demo.spec.html").write_bytes(spec.read_bytes())
    git("-C", str(d), "init", "-q", ".")
    git("-C", str(d), "add", "-A")
    git("-C", str(d), "commit", "-qm", "accepted")
    head = git("-C", str(d), "rev-parse", "--short", "HEAD")
    init = ["octo-feather-spec-status", "init", "docs/specs/demo.spec.html", head]
    rc, out, _ = user(init, cwd=d, env=(f"PATH={K}/scripts:{UP}",))
    if rc:
        die(f"octo-feather-spec-status init in {d}: {out}")
    if mise_toml:
        (d / "mise.toml").write_text(mise_toml)
    (d / ".gitignore").write_text("scratch/\n")
    git("-C", str(d), "add", "-A")
    git("-C", str(d), "commit", "-qm", "spec")


def qc(d: Path, first: str = "", *env: str) -> tuple[int, str]:
    """octo-feather-qc on the target in D, HOME moved as the gate's tests move it (tests/qc.sh),
    FIRST dirs before the fake herdr ($USER_MISE_T/fake) and the stub judge ($USER_MISE_T/judge)."""
    cmd = ["timeout", "-k", "5", "180", "octo-feather-qc", "docs/specs/demo.status.json", "5"]
    qenv = (
        f"HOME={T}/qchome",
        f"PATH={first}{T}/fake:{K}/scripts:{UP}",
        f"OCTO_FEATHER_QC_PATH={T}/judge",
        f"OCTO_FEATHER_QC_DIR={T}/reports",
        *COMMITTER,
        *env,
    )
    rc, out, _ = user([*cmd, "acceptance-a", "--no-github"], cwd=d, env=qenv)
    return rc, out


def own_tools_only(rc: int, out: str) -> bool:
    """The proof passed and its mise line names the kit's own tools, never a global one the
    parent walk finds (#493 AC3)."""
    ml = next((ln for ln in out.splitlines() if ln.startswith("qc sandbox: ok   mise offline")), "")
    kit = re.search(re.escape(f"{K}: ") + ".*node@", ml)
    return rc == 0 and kit is not None and not re.search(r"(erlang|python|rust)@", ml)


def judge_stdout() -> str:
    """The stub judge's stdout in the newest qc report."""
    try:
        f = max((T / "reports").glob("*.json"), key=lambda p: p.stat().st_mtime)
        report: object = json.loads(f.read_text())
    except (ValueError, OSError):
        return "no report"
    out = field(report, "fallback", "acceptance-a", "stdout")
    return out if isinstance(out, str) else "no judge stdout"


def sandbox() -> None:
    """(1), (2): the qc sandbox proof, mise's dirs pinned as tests/qc.sh pins them."""
    for d in (T / "reports", T / "qchome"):
        d.mkdir(exist_ok=True)
    tgt, pin = H / "src/target", H / "src/pinned"
    target(tgt)
    target(pin, '[tools]\njust = "0.0.1"\n')
    pinned = (
        f"MISE_DATA_DIR={D}",
        f"MISE_CACHE_DIR={H}/.cache/mise",
        f"MISE_CONFIG_DIR={H}/.config/mise",
    )
    rc, out = qc(tgt, "", *pinned)
    want(
        "(1) the qc sandbox proof passes with doctor exiting 1 under the moved HOME, judging only"
        " the kit's and worktree's own tools (no global erlang, python, rust), the stub judge runs"
        f" (exit {rc})",
        own_tools_only(rc, out),
        out,
    )
    # mise's config dir not pinned: the moved HOME's parent walk from the kit finds the user's
    # global config as a local one.
    rc, out = qc(tgt, "", *pinned[:2])
    want(
        "(1) the same, mise's config dir not pinned (the parent walk finds the global config):"
        f" still no global tool judged (exit {rc})",
        own_tools_only(rc, out),
        out,
    )
    judge = judge_stdout()
    want(
        "(2) a shim of a tool not installed, in the sandbox: fails, installs and writes nothing",
        any(ln.startswith("PROBE ok ") for ln in judge.splitlines()),
        judge + "\n" + out,
    )
    for stub, what in (
        ("nojson", "doctor printing no JSON"),
        ("nodirs", "doctor JSON without dirs"),
    ):
        rc, out = qc(tgt, f"{T}/{stub}:", *pinned)
        named = re.search(r"qc sandbox: FAIL .*mise doctor", out)
        want(f"(2) {what}: exit 66 naming mise doctor (exit {rc})", rc == 66 and named, out)
    rc, out = qc(pin, "", *pinned)
    fix = f"run outside it: {K}/scripts/octo-feather-mise-install {pin})"
    named = re.search(r"qc sandbox: FAIL mise .*NOT installed: .*just@0\.0\.1", out)
    want(
        f"(2) a pinned tool not installed: exit 66 naming it and mise install (exit {rc})",
        rc == 66 and fix in out and named,
        out,
    )


def install_check() -> None:
    """(1), (3), (5): the install-check gate item in the kit copy, the state dir counted around it
    (#493 AC7); install-check from a pane PATH with a venv first."""
    n0 = state_entries()
    rc, out, _ = user(["just", "test", "-k", "install-check"], cwd=K, env=("GATE_WORKERS=1",))
    n1 = state_entries()
    want(
        "(1) HERDR_SESSION=fixture just test -k install-check passes in the kit under the user's"
        f" HOME (exit {rc})",
        rc == 0,
        out,
    )
    say(
        f"user-mise: the fixture user's mise state dir ({H}/.local/state/mise, inside the fixture"
        f" HOME mounted over {H}) entries: {n0} before the install-check item, {n1} after"
    )
    want(
        "(5) the install-check item leaves the user's mise state dir entries as they were"
        f" ({n0}, then {n1})",
        n1 == n0,
        f"{n0} entries before, {n1} after",
    )
    if user(["python3", "-m", "venv", f"{T}/venv"])[0]:
        die("python3 -m venv through the user's python3")
    rc, out, _ = user(["just", "install-check"], cwd=K, env=(f"PATH={T}/venv/bin:{UP}",))
    bins = (D / "installs/python" / pyv() / "bin", D / "installs/erlang/27.3/bin", H / ".cargo/bin")
    names = "|".join(sorted({re.escape(p.name) for d in bins for p in d.iterdir()}))
    shadowed = re.search(rf"^path   ({names}|pip[0-9.]*) SHADOWED", out, re.MULTILINE)
    want(
        "(3) just install-check, a venv first on the pane PATH: no SHADOWED line for a global-only"
        " tool",
        shadowed is None,
        out,
    )


def readme_install() -> None:
    """(4): README's install step, the command as it stands there (install-check's fix lines
    print the same: tests/install-check.sh), in the kit."""
    lines = (K / "README.md").read_text().splitlines()
    step = "scripts/octo-feather-mise-install"
    cmd = next((re.sub(r"   #.*", "", ln) for ln in lines if ln.startswith(step)), "")
    rc, out, _ = user(["sh", "-c", cmd], cwd=K) if cmd else (1, f"README.md has no {step} line", "")
    want(
        f"(4) README's install step ({cmd}) in the kit exits 0 with the user's global tools"
        f" installed (exit {rc})",
        rc == 0,
        out,
    )


def template_setup(lang: str) -> None:
    """(4), (3) in a target (#500): a repo created from the kit's template LANG (just new-repo)
    under the user's HOME. `just setup` from a pane PATH holding the kit's scripts (pi-role's)
    exits 0; from a PATH without them (a standalone repo) it runs mise install --locked: with the
    user's global tools it fails with mise's exit, naming the kit's install command, and with no
    global config (moved aside, then back) it exits 0; the PATH its justfile gives recipes adds no
    dir of a global-only tool (just run as itself: through its mise shim, mise puts its whole
    toolset, global tools too, on just's own PATH). Offline: uv's cache, pnpm's store."""
    offline = ("UV_OFFLINE=1", "npm_config_offline=true")
    kp = (f"PATH={K}/scripts:{UP}", *offline)
    r = H / f"src/tpl-{lang}"
    new = ["just", "--justfile", f"{K}/justfile", "new-repo", lang, str(r), "--no-spec-chat"]
    rc, out, _ = user(new, cwd=H / "src", env=(*kp, *COMMITTER))
    if rc:
        die(f"just new-repo {lang}: {out}")
    tpl = f"a repo from templates/{lang}"
    mrc = user(["mise", "install", "--locked"], cwd=r)[0]
    rc, out, _ = user(["just", "setup"], cwd=r, env=offline)
    want(
        f"(4) just setup in {tpl}, the kit's scripts not on PATH, global tools: fails with mise's"
        f" exit ({mrc}) naming octo-feather-mise-install (exit {rc})",
        rc != 0
        and rc == mrc
        and "is not in the lockfile" in out
        and "octo-feather-mise-install" in out,
        out,
    )
    cfg, aside = H / ".config/mise/config.toml", T / "global-config.toml"
    shutil.move(cfg, aside)  # across mounts: $USER_MISE_T is not under HOME
    try:
        rc, out, _ = user(["just", "setup"], cwd=r, env=offline)
    finally:
        shutil.move(aside, cfg)
    want(
        f"(4) just setup in {tpl}, the kit's scripts not on PATH, no global mise config: exits 0"
        f" (exit {rc})",
        rc == 0,
        out,
    )
    rc, out, _ = user(["just", "setup"], cwd=r, env=kp)
    want(
        f"(4) just setup in {tpl} exits 0 with the user's global tools installed (exit {rc})",
        rc == 0,
        out,
    )
    rc, out, _ = user(["sh", "-c", '"$(mise which just)" --evaluate PATH'], cwd=r, env=kp)
    glob_dir = re.compile(
        rf"^({re.escape(str(D))}/installs/(python|erlang|rust)|{re.escape(str(H))}/\.cargo)(/|$)"
    )
    want(
        f"(3) the recipe PATH of {tpl} holds no global-only tool's dir",
        rc == 0 and not any(glob_dir.match(p) for p in out.strip().split(":")),
        out,
    )


def main() -> None:
    if sys.argv[1:] == ["setup"]:
        setup()
        return
    if sys.argv[1:] != ["assert"]:
        die("usage: check.py setup|assert")
    d0 = preconditions()
    s0 = snap()
    sandbox()
    install_check()
    readme_install()
    for lang in ("python", "typescript"):
        template_setup(lang)
    s1 = snap()
    diff = "\n".join(list(difflib.unified_diff(s0, s1, lineterm=""))[:20])
    want(
        "(5) the user's mise config, installs and shims byte-identical before and after",
        s1 == s0,
        diff,
    )
    rc, d1 = doctor()
    want(
        f"(5) mise doctor under the user's HOME unchanged (exit {rc})",
        rc == 0 and doctor_view(d1) == doctor_view(d0),
        json.dumps(d1),
    )
    if FAILED:
        die("failed (lines above)")
    say(
        "user-mise: ok (fixture HOME: kit installs bound read-only, global tools absent from the"
        " kit lock, python3 a mise shim, stale shims; every #493 assertion passes)"
    )


if __name__ == "__main__":
    main()
