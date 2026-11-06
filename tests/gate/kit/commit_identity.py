"""The factory commit identity (#665, owner ruling #587): one setting on the box, the [identity]
table of the box onboarding file (scripts/pi-role --help, Commit identity), applied by every role
launch; a launch of a role that would commit, with it unset, refuses naming the setting and how to
set it. Driven through the commands: `pi-role --set-identity` writes it in the scratch HOME's state
dir; a headless `pi-role agents/implementer.md -p` starts a stand-in pi that commits in a scratch
repo with no user config (no model call); herdr-spawn (the pane launch) with the fake herdr of
tests/fixtures/herdr-spawn records the tab's env; `just install-check` reports the setting."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from typing import TYPE_CHECKING

from testkit import ROOT, Scratch, kit, main

if TYPE_CHECKING:
    from pathlib import Path

NAME, EMAIL = "Ada Lovelace", "ada@example.com"
IDENT = f"{NAME} <{EMAIL}>"
# git reads no user config but the scratch repo's (none): no system file, the scratch HOME's global.
NO_CONFIG = {"GIT_CONFIG_NOSYSTEM": "1"}
# The stand-in pi (Pi, which the kit does not own): launched as a role (pi-role's
# --octo-feather-role), one commit in its working directory, as a role's bash call to git would
# make it; any other call (install-check's `pi --version`, run from the kit dir) does nothing,
# so no commit ever lands outside the scratch repo.
PI = (
    "#!/bin/sh\n"
    'case " $* " in *" --octo-feather-role "*) ;; *) exit 0 ;; esac\n'
    "exec git -c commit.gpgsign=false commit -q --allow-empty -m role-commit\n"
)


def world(s: Scratch) -> Path:
    """A scratch repo with no user config, and the stand-in pi first on PATH."""
    pib = s.root / "pibin"
    pib.mkdir()
    (pib / "pi").write_text(PI)
    (pib / "pi").chmod(0o755)
    s.env["PATH"] = f"{pib}{os.pathsep}{s.env['PATH']}"
    s.env |= NO_CONFIG
    for k in (
        "EMAIL",
        *(f"GIT_{w}_{f}" for w in ("AUTHOR", "COMMITTER") for f in ("NAME", "EMAIL")),
    ):
        s.env.pop(k, None)
    repo = s.root / "repo"
    repo.mkdir()
    s.run(["git", "init", "-q", str(repo)])
    return repo


def onboarding(s: Scratch) -> Path:
    return s.home / ".local" / "state" / "octo-feather" / "onboarding.toml"


def spawn(s: Scratch, cwd: Path, *, want: int) -> Path:
    """herdr-spawn of an implementer pane at CWD with the fake herdr; the fake's state dir."""
    d = s.root / "herdr"
    hb = s.root / "herdrbin"
    for x in (d, hb):
        x.mkdir(exist_ok=True)
    for f in (ROOT / "tests" / "fixtures" / "herdr-spawn").iterdir():
        shutil.copy(f, hb / f.name)
    env = {
        "FAKE_HERDR_DIR": str(d),
        "PATH": f"{hb}{os.pathsep}{s.env['PATH']}",
        "HERDR_PANE_ID": "w9:p0",
    }
    spawner = str(ROOT / ".agents" / "skills" / "herdr-comms" / "assets" / "herdr-spawn")
    s.run(
        [spawner, "--workspace", "w9", "--name", "t1", "--role", "implementer", "--cwd", str(cwd)],
        want=want,
        env=env,
    )
    return d


def install_check(s: Scratch) -> list[str]:
    """`just install-check` of the kit, its stdout lines; its exit is the box's (its other lines
    judge this box's tools), so not asserted."""
    cmd = ["just", "--justfile", str(ROOT / "justfile"), "install-check", str(ROOT)]
    path = os.pathsep.join(d for d in s.env["PATH"].split(os.pathsep) if d != str(s.root / "pibin"))
    env = {**s.env, "PATH": path}  # the box's own pi, never the stand-in, which commits
    p = subprocess.run(cmd, cwd=s.root, env=env, capture_output=True, text=True, check=False)
    assert "Traceback" not in p.stderr, p.stderr
    return p.stdout.splitlines()


def applied(s: Scratch) -> None:
    """Set once with pi-role --set-identity (beside the onboarding file's [consent] table, kept):
    a headless implementer launch's commit, in a repo with no user config, carries it as author
    and committer; a pane launch's tab env holds it; install-check reports it ok."""
    repo = world(s)
    ob = onboarding(s)
    ob.parent.mkdir(parents=True)
    ob.write_text("[consent]\npush = false\n")
    s.identity(NAME, EMAIL)
    assert "[consent]\npush = false\n" in ob.read_text(), ob.read_text()
    s.run([kit("pi-role"), str(ROOT / "agents" / "implementer.md"), "-p", "x"], cwd=repo)
    got = s.run(["git", "-C", str(repo), "log", "-1", "--format=%an <%ae>|%cn <%ce>"]).out
    assert got == f"{IDENT}|{IDENT}", got
    tab = (spawn(s, repo, want=0) / "tab-env").read_text().splitlines()
    for k in ("AUTHOR", "COMMITTER"):
        assert f"GIT_{k}_NAME={NAME}" in tab, tab
        assert f"GIT_{k}_EMAIL={EMAIL}" in tab, tab
    line = rf"identity ok  {re.escape(IDENT)} \(\[identity\] in {re.escape(str(ob))}, .*"
    assert any(re.fullmatch(line, x) for x in install_check(s)), "\n".join(install_check(s))


def unset(s: Scratch) -> None:
    """No setting: a headless implementer launch and a pane launch refuse, naming the setting, the
    onboarding file and the command that sets it; no pi starts, no tab opens, no commit is made;
    install-check reports it missing with the same fix."""
    repo = world(s)
    ob = re.escape(str(onboarding(s)))
    setting = rf"\[identity\] name and email in the box onboarding file {ob}"
    how = rf"{re.escape(kit('pi-role'))} --set-identity \"Your Name\" you@example.com"
    ran = s.run(
        [kit("pi-role"), str(ROOT / "agents" / "implementer.md"), "-p", "x"], want=1, cwd=repo
    )
    assert re.search(rf"implementer not started: it would commit.*{setting}.*{how}", ran.err), (
        ran.err
    )
    assert s.run(["git", "-C", str(repo), "rev-list", "--all"]).out == "", "a commit was made"
    d = spawn(s, repo, want=65)
    assert not (d / "argv").exists() or "tab create" not in (d / "argv").read_text(), "a tab opened"
    line = rf"identity MISSING \(no file {ob}\): .*{setting}.*{how}.*"
    assert any(re.fullmatch(line, x) for x in install_check(s)), "\n".join(install_check(s))


def read_only(s: Scratch) -> None:
    """No setting: the launch of a role whose contract never commits (the code reviewer) is not
    refused, and applies no identity: its launch env (`pi-role --print-env`) is empty."""
    repo = world(s)
    ran = s.run(
        [kit("pi-role"), "--print-env", str(ROOT / "agents" / "code-reviewer.md")], cwd=repo
    )
    assert ran.out == "", ran.out


if __name__ == "__main__":
    main(applied, unset, read_only)
