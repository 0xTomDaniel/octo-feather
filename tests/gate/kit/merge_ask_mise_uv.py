"""The scenario of tests/gate/kit/test_merge_ask_mise_uv.py, this file its command (testkit.main):
a kit script that re-execs into the kit's locked environment starts uv in the kit, so a target
pinning no uv works where uv comes only from mise (owner ruling 2026-11-26, #1325; #1330).

`octo-feather-lane merge-ask 1321` runs as a command in a scratch target repo (git init, no
mise.toml, no uv pin anywhere above it), its PATH holding uv only as mise's real shim (the dir
`mise doctor --json` names; the shim is mise itself under uv's name), every other uv on PATH
masked; mise's installs and uv's caches the caller's (testkit.tool_homes), so nothing is fetched.
GitHub answers only real gh's, unmodified (testkit/recordings/merge-ask-mise-uv.json: PR #1321,
the open PRs on main, issue #1317, each as gh 2.102.0 gave it to merge-ask). Its merge order and
its replay must read: each open PR of the recorded list is named under Merge order, no `not read:
open pull requests` line, no `cannot read correction lane facts`, and no mise `No version is set
for shim` anywhere.

On a machine without mise, or whose mise has not installed the kit's uv pin (mise.toml), the
scenario fails at its start naming what is missing and the command that installs it; it never
skips: the CI runner (jdx/mise-action) and the box both have them.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import cast

import tomllib
from testkit import ROOT, Scratch, kit, main, tool_homes
from testkit.qc_box import mise_dir

TAPE = Path(__file__).parent / "testkit" / "recordings" / "merge-ask-mise-uv.json"
REPO = "0xTomDaniel/octo-feather"
PR = 1321
SHIM_ERROR = "No version is set for shim"


def mise_uv() -> Path:
    """mise's shims dir, once mise and its install of the kit's uv pin are found; else fails
    naming the missing one."""
    pin = tomllib.loads((ROOT / "mise.toml").read_text())["tools"]["uv"]
    install = f"{kit('octo-feather-mise-install')} {ROOT}"
    mise = shutil.which("mise")
    assert mise, f"no mise on PATH: this case runs uv as mise's shim; install mise, then: {install}"
    p = subprocess.run([mise, "which", "uv"], cwd=ROOT, capture_output=True, text=True, check=False)
    assert p.returncode == 0, (
        f"mise has no uv@{pin} (mise.toml) installed: run {install}\n{p.stderr}"
    )
    shims = Path(mise_dir("shims"))
    assert (shims / "uv").exists(), f"no uv shim in mise's shims dir {shims}: run mise reshim"
    return shims


def read_with_mise_uv(s: Scratch) -> None:
    shims = mise_uv()
    s.without("uv")
    first, *rest = s.env["PATH"].split(":")
    s.env |= {"PATH": ":".join([first, str(shims), *rest]), **tool_homes()}
    target = s.root / "target"
    target.mkdir()
    s.git(target, "init", "-q")
    tape = cast("list[dict[str, object]]", json.loads(TAPE.read_text()))
    s.gh.store("tape.json", tape)
    lst = next(r for r in tape if str(r["request"]).startswith("pr list "))
    rows = cast("list[dict[str, object]]", json.loads(str(lst["out"])))
    status = str(ROOT / "docs" / "specs" / "comms.status.json")
    ran = s.run(
        [kit("octo-feather-lane"), "merge-ask", str(PR), "--repo", REPO, "--status", status],
        want=1,  # the PR's commits are not in the target: incomplete, as from any non-lane dir
        cwd=target,
    )
    said = f"{ran.out}\n{ran.err}"
    assert SHIM_ERROR not in said, f"mise's shim found no uv: {said}"
    assert "not read: open pull requests" not in said, f"merge order unread: {said}"
    order = said.split("Merge order", 1)[1].split("merge-ask: PR", 1)[0]
    for n in (int(str(r["number"])) for r in rows if r["number"] != PR):
        assert f"PR #{n} " in order, f"open PR #{n} not in the merge order: {said}"
    assert "cannot read correction lane facts" not in said, f"replay unread: {said}"
    assert any(x.startswith("issue view 1317 ") for x in s.gh.log()), "the replay never read #1317"


if __name__ == "__main__":
    main(read_with_mise_uv)
