"""`just install-check` warns when the caller's mise would install a shimmed just from the network
(#667, #505; director ruling): with just on the caller's PATH mise's shim (`mise activate
--shims`: a shim is mise itself under the tool's name) and the user's mise config (a scratch
MISE_CONFIG_DIR) leaving auto-install on, mise's default, one WARNING line names the settings, the
effect and the command the user may run, and the exit is the one the same box gets with
auto-install off; with it off (auto_install = false), no such line. The kit never edits the
user's mise config: the scratch config is byte-identical after each run."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import tomllib
from testkit import ROOT, Ran, Scratch, main, tool_homes

# The user's own shell settings the scenario stands for: none (a gate run exports them off).
SHELL = (
    "MISE_OFFLINE",
    "MISE_AUTO_INSTALL",
    "MISE_EXEC_AUTO_INSTALL",
    "MISE_NOT_FOUND_AUTO_INSTALL",
)
WARNING = (
    r"mise   WARNING auto-install on \(auto_install true, not_found_auto_install true, "
    r"exec_auto_install true; mise settings\): just on your PATH is mise's shim (?P<shim>\S+), "
    r"so a just whose pinned version is not installed is installed from the network before any "
    r"justfile is read \(the gate's own mise calls never install, #667\); the check still "
    r"passes; to turn it off: mise settings set auto_install false \(the kit never edits your "
    r"mise config\)"
)


def install_check(s: Scratch, settings: str) -> Ran:
    """`just -f KIT/justfile install-check` in a scratch repo, run as the user runs it: just on
    PATH mise's shim (which puts its install first on PATH for the just it runs), the user's mise
    config SETTINGS with just at the kit's pin; its exit as it is (the box's own gaps decide it)."""
    conf = s.root / "mise-config"
    conf.mkdir(exist_ok=True)
    pin = tomllib.loads((ROOT / "mise.toml").read_text())["tools"]["just"]
    text = f'{settings}[tools]\njust = "{pin}"\n'  # the user's just: the kit's pin, installed
    (conf / "config.toml").write_text(text)
    repo = s.root / "repo"
    if not repo.exists():
        repo.mkdir()
        s.git(repo, "init", "-q")
    # mise's data dir as the user's: its installs (the box's, linked) and its shims dir, where a
    # shim is mise itself under the tool's name; on PATH, so just resolves to the shim.
    homes = tool_homes()
    data = s.root / "mise-data"
    shim = data / "shims" / "just"
    if not data.exists():
        mise = shutil.which("mise")
        assert mise, "no mise: this case needs it"
        shim.parent.mkdir(parents=True)
        shim.symlink_to(mise)
        (data / "installs").symlink_to(Path(homes["MISE_DATA_DIR"]) / "installs")
    env = {k: v for k, v in s.env.items() if k not in SHELL}
    env |= homes | {"MISE_DATA_DIR": str(data), "MISE_CONFIG_DIR": str(conf)}
    env["PATH"] = f"{s.bin}{os.pathsep}{shim.parent}{os.pathsep}{env['PATH']}"
    p = subprocess.run(
        [str(shim), "-f", str(ROOT / "justfile"), "install-check"],  # as PATH finds it
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert (conf / "config.toml").read_text() == text, "install-check edited the mise config"
    assert "Traceback" not in p.stderr, p.stderr
    return Ran(p.returncode, p.stdout, p.stderr)


def on(s: Scratch) -> None:
    ran = install_check(s, "")
    shims = [m for x in ran.out.splitlines() if (m := re.fullmatch(WARNING, x))]
    assert shims, f"no auto-install WARNING line:\n{ran.out}\n{ran.err}"
    assert shims[0]["shim"] == str(s.root / "mise-data" / "shims" / "just"), shims[0]["shim"]
    off = install_check(s, "[settings]\nauto_install = false\n")
    assert ran.rc == off.rc, f"the WARNING changed the exit: {ran.rc}, off {off.rc}"


def off(s: Scratch) -> None:
    ran = install_check(s, "[settings]\nauto_install = false\n")
    assert "WARNING auto-install" not in ran.out, ran.out
    assert "mise   version" in ran.out, f"no mise section:\n{ran.out}\n{ran.err}"


if __name__ == "__main__":
    main(on, off)
