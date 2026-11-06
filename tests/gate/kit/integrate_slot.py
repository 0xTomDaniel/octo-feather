"""`just integrate` tells a heavy-slot refusal from a red gate (#668; owner #660, no silent
failures; director finding refusal-reported-as-red), through octo-feather-integrate in a scratch
target whose lane gh7's gate (`just check`) runs the kit's gate plugin over its 31-item suite, as
an implementer of gh7 with a scratch box state dir.

refused: without gh7's heavy grant the gate is refused before any item runs: integrate prints
`refused: no heavy slot, nothing ran` with the slot's refusal, never a `red:` line, resets the lane
and exits 75. red: with the grant, a worker adding a failing test makes the gate run red: `red:`,
exit 2, the lane reset as before."""

from __future__ import annotations

import sys

from testkit import ROOT, Scratch, kit, main

AGENT = {
    "OCTO_FEATHER_ROLE": "implementer",
    "HERDR_PANE_ID": "w9:p3",
    "OCTO_FEATHER_PARENT": "w9:p1",
    "HERDR_WORKSPACE_ID": "w9",
}
DIRECTOR = {"OCTO_FEATHER_ROLE": "director", "HERDR_PANE_ID": "w1:p1"}
PANE = (*AGENT, "HERDR_SESSION", "OCTO_FEATHER_SPEND_SPACE")
REFUSED = 75
JUSTFILE = f"""check:
    PYTHONPATH={ROOT} {sys.executable} -m pytest -q -p tests.gate.heavy_slot suite
"""
MANY = "import pytest\n@pytest.mark.parametrize('n', range(31))\ndef test_n(n): pass\n"
SLOT_REFUSAL = (
    "octo-feather-slot: refused, nothing ran: this heavy run selects 31 items, over heavy_items 30"
    " (gate-budget.toml), and lane gh7 holds no heavy grant; current holder: none; ask the "
    "director: octo-feather-slot grant gh7 --kind heavy"
)


def world(s: Scratch) -> tuple[str, str]:
    """S's box (lane gh7's record, scratch state) and target: main with the gate and its suite, the
    lane worktree gh7, worker branch w1 (one more file) and w2 (a failing test). Returns the repo
    and the lane worktree paths."""
    lanes = s.root / "state" / "octo-feather" / "lanes"
    lanes.mkdir(parents=True)
    (lanes / "gh7.toml").write_text('supervisor = "w9:p1"\n')
    s.env = {k: v for k, v in s.env.items() if k not in PANE}
    s.env |= {"XDG_STATE_HOME": str(s.root / "state")}
    r, lane = s.root / "repo", s.root / "lane"
    (r / "suite").mkdir(parents=True)
    (r / "justfile").write_text(JUSTFILE)
    (r / "suite" / "pytest.ini").write_text("[pytest]\naddopts = -p no:cacheprovider\n")
    (r / "suite" / "test_many.py").write_text(MANY)
    s.git(r, "init", "-q", "-b", "main")
    s.git(r, "add", "-A")
    s.git(r, "commit", "-qm", "base")
    s.git(r, "worktree", "add", "-q", "-b", "gh7", str(lane))
    red = "def test_red(): assert 0\n"
    for w, f, text in (("w1", "b", "b\n"), ("w2", "suite/test_red.py", red)):
        s.git(r, "worktree", "add", "-q", "-b", w, str(s.root / w))
        (s.root / w / f).write_text(text)
        s.git(s.root / w, "add", "-A")
        s.git(s.root / w, "commit", "-qm", w)
    return str(r), str(lane)


def integrate(s: Scratch, repo: str, ref: str, want: int) -> str:
    env = {
        **AGENT,
        **{
            f"GIT_{w}_{k}": v
            for w in ("AUTHOR", "COMMITTER")
            for k, v in (("NAME", "t"), ("EMAIL", "t@example.com"))
        },
    }
    ran = s.run([kit("octo-feather-integrate"), "--full", "7", ref], cwd=repo, want=want, env=env)
    return ran.out + "\n" + ran.err


def refused(s: Scratch) -> None:
    repo, lane = world(s)
    start = s.git(s.root / "lane", "rev-parse", "HEAD")
    out = integrate(s, repo, "w1", REFUSED)
    want = "refused: no heavy slot, nothing ran: just check, the full tier "
    lines = [ln for ln in out.splitlines() if ln.startswith(want)]
    assert lines, out
    assert lines[0].endswith(SLOT_REFUSAL), out
    assert "red:" not in out, out
    assert s.git(s.root / "lane", "rev-parse", "HEAD") == start, f"{lane} not reset"


def red(s: Scratch) -> None:
    repo, lane = world(s)
    s.run([kit("octo-feather-slot"), "grant", "gh7", "--kind", "heavy"], env=DIRECTOR)
    start = s.git(s.root / "lane", "rev-parse", "HEAD")
    out = integrate(s, repo, "w2", 2)
    assert "red: just check, the full tier " in out, out
    assert "refused:" not in out, out
    assert "heavy slot: held: the heavy slot for lane gh7" in out, out
    assert s.git(s.root / "lane", "rev-parse", "HEAD") == start, f"{lane} not reset"


if __name__ == "__main__":
    main(refused, red)
