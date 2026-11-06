"""The kit justfile stays offline and never installs on its own (#667, #505; owner ruling #493):
evaluated (`just --evaluate`, every assignment and backtick, as any recipe run starts) with
MISE_DATA_DIR an empty dir, in a network namespace of its own (`unshare -rn`, no route out), and
the caller's mise shims first on PATH (`mise activate --shims`: a shim is mise itself under the
tool's name), it leaves the data dir empty, tries no download, and names each missing tool and
octo-feather-mise-install on stderr. Linux only: unshare."""

from __future__ import annotations

import re
import shutil
import subprocess

import tomllib
from testkit import ROOT, Scratch, asked, main


def empty_data_dir(s: Scratch) -> None:
    mise, unshare = shutil.which("mise"), shutil.which("unshare")
    assert mise, "no mise: this case needs it"
    assert unshare, "no unshare: this case needs it"
    just = asked("mise", "which", "just")  # the real just, not a shim, so mise acts only inside
    (s.bin / "just").symlink_to(mise)
    dirs = {f"MISE_{d}_DIR": s.root / f"mise-{d.lower()}" for d in ("DATA", "CACHE", "STATE")}
    dirs["MISE_CONFIG_DIR"] = s.root / "mise-config"
    for d in dirs.values():
        d.mkdir()
    env = s.env | {k: str(v) for k, v in dirs.items()}
    p = subprocess.run(
        [unshare, "-rn", just, "--evaluate"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    said = f"just --evaluate: exit {p.returncode}\n{p.stderr}"
    data = dirs["MISE_DATA_DIR"]
    wrote = [x.name for x in data.iterdir()]
    assert not wrote, f"mise wrote into MISE_DATA_DIR: {wrote}\n{said}"
    assert "error sending request" not in p.stderr, f"a network attempt: {said}"
    assert "installing" not in p.stderr, f"an install attempt: {said}"
    fix = re.escape(f"run: {ROOT / 'scripts' / 'octo-feather-mise-install'} {ROOT}")
    pin = tomllib.loads((ROOT / "mise.toml").read_text())["tools"]["just"]
    tools = rf"(.* )?just@{re.escape(pin)}( .*)?"
    line = rf"just: not installed: {tools} \(mise\.toml, mise\.lock\); {fix}"
    assert any(re.fullmatch(line, x) for x in p.stderr.splitlines()), said
    assert "Traceback" not in p.stderr, said


if __name__ == "__main__":
    main(empty_data_dir)
