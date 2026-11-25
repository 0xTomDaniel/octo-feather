"""A gate run leaves the caller's mise state and its repo's git config as it found them (#664,
#584, #587; owner ruling 2026-11-05), judged only on what this run left, attributed exactly:
`just test` in a git copy of the kit, its caller's mise state dir a scratch one, with one seeded
item. Without a seed the run passes naming what it found unchanged. It fails naming the change,
though the item itself passes, when the item leaves in the caller's state a link into the run's
own TMPDIR (check-tests gives it one), live or dangling, or sets a key in the copy's .git/config
(the repo's git common dir config). What another agent on the box may do meanwhile passes, named
as not this run's: a link elsewhere, live or dangling, added, removed or replaced (concurrent:
through untouched save and check); a branch.<name>.* key (push -u, a worktree's branch)."""

from __future__ import annotations

import re
import subprocess
from typing import TYPE_CHECKING

from testkit import ROOT, Ran, Scratch, kit, main, pnpm_store, tool_homes, tracked

if TYPE_CHECKING:
    from pathlib import Path

ITEM = "tests/gate/test_gate.py::test_script[tests/zz-seed.sh]"
# The seeded item: as each word of SEED says, a link into the caller's mise state (SEED_STATE:
# the item sees only the gate's own per-run state dir, so the caller's is handed to it): one that
# dangles outside the run, one into a dir under its TMPDIR it leaves, or one it removes, one to
# SEED_LIVE (a path made before the run); a key in its repo's git config, user.name or a branch's
# remote; else nothing. It passes either way.
SEED = """#!/usr/bin/env bash
set -euo pipefail
tc="${SEED_STATE:-}/tracked-configs"
for seed in ${SEED:-}; do case "$seed" in
  link) ln -s /nowhere/seeded/mise.toml "$tc/seeded" ;;
  ours) d="$(mktemp -d)"; touch "$d/mise.toml"; ln -s "$d/mise.toml" "$tc/ours" ;;
  gone) d="$(mktemp -d)"; ln -s "$d/mise.toml" "$tc/gone"; rmdir "$d" ;;
  live) ln -s "$SEED_LIVE" "$tc/live" ;;
  config) git config --local user.name seeded ;;
  branch) git config --local branch.x.remote origin ;;
esac; done
"""
# The kit gate's own settings and venv, never the copy's run's.
GATE = (
    "GATE_NESTED",
    "GATE_RECIPES",
    "GATE_WORKERS",
    "GATE_RUN_DIR",
    "GATE_ITEM",
    "HERDR_SESSION",
    "VIRTUAL_ENV",
)


def kit_copy(s: Scratch) -> Path:
    """The kit's tracked files (testkit tracked) in a git repo of their own, with the seeded item,
    and no JavaScript packages (tests/lib/no-packages.py): the seeded item needs none, so each
    nested `just test`'s pnpm install has nothing to install (#1180, #1290)."""
    k = s.root / "kit"
    tracked(k)
    s.run([str(ROOT / "tests" / "lib" / "no-packages.py"), str(k)])
    (k / "tests" / "zz-seed.sh").write_text(SEED)
    (k / "tests" / "zz-seed.sh").chmod(0o755)
    s.git(k, "init", "-q", "-b", "main")
    s.git(k, "add", "-A")
    s.git(k, "commit", "-qm", "copy")
    return k


def homes() -> dict[str, str]:
    """The tools' homes a nested gate runs with (tool_homes, pnpm_store), asked once per scenario:
    each ask runs uv, or pnpm outside a gate run (pnpm_store), ~0.3 s CPU a run (#1180)."""
    return tool_homes() | {"npm_config_store_dir": pnpm_store()}


def gate(s: Scratch, k: Path, seed: str, want: int | None, tools: dict[str, str]) -> Ran:
    """`just test ITEM` in K with SEED and the tools' homes TOOLS; its stdout and stderr
    together, as a shell's 2>&1."""
    env = {k: v for k, v in s.env.items() if k not in GATE}
    env |= tools | {
        "MISE_STATE_DIR": str(s.root / "user-mise"),
        "GATE_WORKERS": "0",  # one item: in pytest's own process, no xdist worker to start (#1180)
        "SEED": seed,
        "SEED_STATE": str(s.root / "user-mise"),
        "SEED_LIVE": str(s.root / "live" / "mise.toml"),
    }
    p = subprocess.run(
        ["just", "test", ITEM],  # noqa: S607
        cwd=k,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    said = f"just test (SEED={seed}): exit {p.returncode}, want {want}\n{p.stdout}"
    assert want is None or p.returncode == want, said
    return Ran(p.returncode, p.stdout, "")


FAIL = (
    "check-tests: FAIL the gate changed the caller's mise state or the repo's git config "
    "\\(#664\\):\n"
)


def seeded(s: Scratch) -> None:
    """Clean, then the seeds: the clean run and the seeds another agent could have made pass; the
    seeds this run leaves fail naming each change, and the item itself passed."""
    st = s.root / "user-mise"
    tc = re.escape(str(st / "tracked-configs"))
    (st / "tracked-configs").mkdir(parents=True)
    (st / "trusted-configs").mkdir()
    (st / "tracked-configs" / "kept").symlink_to("/nowhere/kept/mise.toml")
    (s.root / "live").mkdir()
    (s.root / "live" / "mise.toml").write_text("[tools]\n")
    k = kit_copy(s)
    cfg = re.escape(str(k / ".git" / "config"))
    unchanged = (
        rf"check-tests: unchanged by the gate: {tc} \(\d+ entries\), "
        rf"{re.escape(str(st))}/trusted-configs \(0 entries\), {cfg} \(\d+ keys, branch\.\* aside\)"
    )
    tools = homes()
    ok = gate(s, k, "", 0, tools)
    assert re.search(unchanged, ok.out), ok.out
    other = gate(s, k, "live link branch", 0, tools)  # what another agent may do meanwhile
    assert re.search(unchanged, other.out), other.out
    root = re.escape(str(s.root))
    for note in (
        rf"{tc}/live: added -> {root}/live/mise\.toml",
        rf"{tc}/seeded: added -> /nowhere/seeded/mise\.toml",
    ):
        assert re.search(rf"check-tests: not this run's: {note}\n", other.out), other.out
    ours = gate(s, k, "ours gone config", None, tools)  # what this run left
    assert ours.rc != 0, ours.out
    assert "1 passed" in ours.out, ours.out
    gt, mk = r"(/\S+/gate\.\w+)", r"tmp\.\w+"  # the run's own TMPDIR (check-tests), a mktemp -d
    want = (
        rf"  {tc}/gone: added -> {gt}/{mk}/mise\.toml, under this run's TMPDIR \1\n"
        rf"  {tc}/ours: added -> \1/{mk}/mise\.toml, under this run's TMPDIR \1\n"
        rf"  {cfg}: changed \(present\): \+user\.name=seeded\n"
    )
    assert re.search(FAIL + want, ours.out), ours.out
    assert str((st / "tracked-configs" / "kept").readlink()) == "/nowhere/kept/mise.toml"


def concurrent(s: Scratch) -> None:
    """Through `octo-feather-gate untouched save` and `check`, around a run whose TMPDIR is RUN:
    another agent removing one pre-existing link and replacing another meanwhile (a peer lane's
    post-merge prune) passes, each named not this run's (#664 director ruling); a pre-existing
    link into RUN removed, one replaced by a link into RUN, and a git config key set each still
    fail, named."""
    repo = s.root / "repo"
    s.git(repo.parent, "init", "-q", "-b", "main", str(repo))
    st = s.root / "state"
    tc = st / "tracked-configs"
    tc.mkdir(parents=True)
    run = s.root / "tmp" / "gate.run1"
    (run / "x").mkdir(parents=True)
    links = {
        "peer": "/other/lane/mise.toml",
        "swap": "/other/a/mise.toml",
        "mine": f"{run}/x/mise.toml",
        "into": "/other/c/mise.toml",
    }
    for n, t in links.items():
        (tc / n).symlink_to(t)
    box = s.root / "box.json"
    gate = kit("octo-feather-gate")
    save = [gate, "untouched", "save", str(box), "--mise-state", str(st), "--run-tmp", str(run)]
    s.run(save, cwd=repo)
    (tc / "peer").unlink()
    (tc / "swap").unlink()
    (tc / "swap").symlink_to("/other/b/mise.toml")
    ok = s.run([gate, "untouched", "check", str(box)], cwd=repo)
    t = re.escape(str(tc))
    for note in (
        rf"{t}/peer: removed \(was -> /other/lane/mise\.toml\)",
        rf"{t}/swap: changed \(-> /other/a/mise\.toml, now -> /other/b/mise\.toml\)",
    ):
        assert re.search(rf"^check-tests: not this run's: {note}$", ok.err, re.MULTILINE), ok.err
    assert "check-tests: unchanged by the gate: " in ok.err, ok.err
    s.run(save, cwd=repo)
    (tc / "mine").unlink()
    (tc / "into").unlink()
    (tc / "into").symlink_to(f"{run}/y/mise.toml")
    s.git(repo, "config", "--local", "user.name", "leaked")
    bad = s.run([gate, "untouched", "check", str(box)], want=1, cwd=repo)
    r = re.escape(str(run))
    cfg = re.escape(str(repo / ".git" / "config"))
    want = (
        rf"  {t}/into: changed \(-> /other/c/mise\.toml, now -> {r}/y/mise\.toml\), "
        rf"under this run's TMPDIR {r}\n"
        rf"  {t}/mine: removed \(was -> {r}/x/mise\.toml\), under this run's TMPDIR {r}\n"
        rf"  {cfg}: changed \(present\): \+user\.name=leaked\n"
    )
    assert re.search(FAIL + want, bad.err + "\n"), bad.err


if __name__ == "__main__":
    main(seeded, concurrent)
