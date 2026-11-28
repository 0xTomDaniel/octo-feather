"""The scenarios of tests/gate/kit/test_lane_veto.py (its items), this file their command
(testkit.main): `octo-feather-lane veto` (what it does: `octo-feather-lane --help`, veto;
issue-lifecycle #gates-digest, #gates-call-decision, #acceptance-merge-digest-veto; issue 1341),
offline, gh answering only real gh's recorded answers.

The real case: tests/gate/kit/lane_digest.py's world and its recordings (lane gh49's merge of
realcase PR #51 on 2026-11-28, lane gh50's of PR #52, tier 2 with one clarifies call, the next
day; the digest of 2026-11-28 made and recorded sent from the director's pane), then the veto's
own recording, lane-veto-1341.json (lane gh1337, #1341, the ticket's demo): from that same scratch
world, real gh on PATH, the director ran `veto 48` (realcase PR #48, closed unmerged) and `veto 52`
before the digest was sent, then, once sent, `veto 52 --said "gh1337 demo veto" --repo <it>`,
which filed the repair issue in the realcase through the github-issues skill's issue-create;
every gh call recorded, unmodified.

  veto_refused   from the director's pane, before any digest is sent: `veto 48` refused, `PR
           #48 is not merged (CLOSED)`; `veto 52` refused, no sent merge digest lists it; from
           lane gh50's supervisor's pane, `veto 52` refused, `only the director records a veto`,
           no gh call. gh asked only the recorded `pr view` of each, no issue filed, and the
           director log unchanged.
  veto_files_repair  the digest of 2026-11-28 sent, `veto 52 --said "gh1337 demo veto" --repo
           <realcase>` from the director's pane: gh asked the recorded `pr view 52` and one
           `issue create` (GH_REPO the realcase, no --parent), titled `Veto: revert or repair PR
           #52 <its title>`, its body naming the PR's url, its merge commit and merged time, the
           owner's words, the recorded tier block and the clarifies call as the merged main's
           call log holds it, DENIED by this veto with the `denied` field the repair lane sets,
           and the work: revert or repair the merge. The director log's last line {"at", "kind":
           "veto", "repo", "pr": 52, "merge", "issue", "said"}; the last line printed the lane
           start for the issue, its brief the body. `veto 52` again: refused naming that issue,
           no gh call, nothing recorded.
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

from lane_digest import (
    CALLS,
    DAY,
    DIGEST,
    DIRECTOR,
    NEXT_DAY,
    PR_B,
    TAPE_B,
    TAPE_DAY,
    merge_a,
    merge_b,
    merge_commit,
    merged_at,
    shown,
    world,
)
from testkit import Scratch, clock, kit, main
from testkit.realcase import REALCASE, RealCase, recordings

if TYPE_CHECKING:
    from testkit import Ran

TAPE_VETO = "lane-veto-1341"
SAID = "gh1337 demo veto"
VIEW = "pr view {} --json state,title,url,mergedAt,mergeCommit -R " + REALCASE


def merged(s: Scratch, *tapes: str) -> RealCase:
    """The world after both merges, the second the next day, gh answering from TAPES after."""
    w = world(s, DIGEST.tape, TAPE_B, *tapes)
    clock(s, merged_at(DIGEST.pr))
    merge_a(s, w)
    clock(s, NEXT_DAY)
    merge_b(s, w)
    return w


def director(s: Scratch, w: RealCase, *args: str, want: int = 0) -> Ran:
    """`octo-feather-lane ARGS` from the director's checkout in its pane."""
    r = s.run([kit("octo-feather-lane"), *args], want=want, cwd=w.checkout, env=DIRECTOR)
    return shown(r, list(args))


def log_text(w: RealCase) -> str:
    p = w.top / "director.handoffs.jsonl"
    return p.read_text() if p.exists() else ""


def veto_refused(s: Scratch) -> None:
    """issue-lifecycle#acceptance-merge-digest-veto, the refusals (the module docstring)."""
    w = merged(s, TAPE_VETO)
    before, calls = log_text(w), len(s.gh.log())
    veto = ["veto", str(PR_B), "--said", SAID, "--repo", REALCASE]
    r = director(s, w, "veto", "48", "--said", SAID, "--repo", REALCASE, want=1)
    assert "PR #48 is not merged (CLOSED)" in r.err, r.err
    r = director(s, w, *veto, want=1)
    assert f"no sent merge digest of {REALCASE} lists PR #{PR_B}" in r.err, r.err
    assert s.gh.log()[calls:] == [VIEW.format(48), VIEW.format(PR_B)], s.gh.log()[calls:]
    r = w.lane(*veto, want=1)
    assert "only the director records a veto" in r.err, r.err
    assert "nothing filed" in r.err, r.err
    assert len(s.gh.log()) == calls + 2, s.gh.log()[calls:]
    assert log_text(w) == before, log_text(w)[len(before) :]
    assert not (w.top / "veto").exists()


def veto_files_repair(s: Scratch) -> None:
    """issue-lifecycle#acceptance-merge-digest-veto, the repair issue filed (the module
    docstring)."""
    w = merged(s, TAPE_DAY, TAPE_DAY, TAPE_VETO)
    r = w.lane("digest", DAY, "--repo", REALCASE)
    sha = r.out.rpartition("\n\nsha256 ")[2]
    director(s, w, "digest", DAY, "--repo", REALCASE, "--sent", sha)
    calls = len(s.gh.log())

    ok = director(s, w, "veto", str(PR_B), "--said", SAID, "--repo", REALCASE)
    tape = {str(x["request"]): str(x["out"]) for x in recordings(TAPE_VETO)}
    view = json.loads(tape[VIEW.format(PR_B)])
    m2 = merge_commit(TAPE_B, PR_B)
    asked = s.gh.log()[calls:]
    assert len(asked) == 2, asked
    assert asked[0] == VIEW.format(PR_B), asked
    recorded = next(k for k in tape if " issue create " in k)  # the real veto's request
    assert asked[1] == recorded, asked[1]
    title = f"Veto: revert or repair PR #{PR_B} {view['title']}"
    head, _, raw = recorded.partition(" --body-file ")
    assert head == f"GH_REPO={REALCASE} issue create --title {title}", head
    body = json.loads(raw)
    call = s.git(w.checkout, "show", f"{m2}:{CALLS}").strip()
    for want in (
        f"- PR: {view['url']} ({view['title']})",
        f"- Merge commit: {m2}",
        f"- Merged: {view['mergedAt']}",
        f"- Owner's words (declared by the director, `octo-feather-lane veto`): {SAID}",
        "Tier: 2",
        f"Spec gh1337-demo (gh1337-demo.calls.jsonl), DENIED by this veto:\n\n```json\n{call}\n```",
        f'"note": "vetoed by the owner from the merge digest (PR #{PR_B}): {SAID}"',
        f"Revert or repair merge {m2} of PR #{PR_B}",
    ):
        assert want in body, f"{want!r} not in the body:\n{body}"
    found = re.search(r"/issues/(\d+)$", tape[recorded].strip())
    assert found, tape[recorded]
    key = found.group(1)

    line = json.loads(log_text(w).splitlines()[-1])
    assert line.pop("at").startswith("2026-11-29T"), line
    want = {"kind": "veto", "repo": REALCASE, "pr": PR_B, "merge": m2, "issue": key}
    assert line == want | {"said": SAID}, line
    brief = w.top / "veto" / f"{key}.brief.md"
    header = f"Repair lane for the owner's veto of PR #{PR_B}: its parent issue {key} holds"
    header += " the work."
    assert brief.read_text() == f"{header}\n\n{body}", brief.read_text()
    start = (
        f"octo-feather-lane start {key} --goal 'Veto repair: PR #{PR_B}' --outcome 'merge "
        f"{m2[:12]} of PR #{PR_B}, vetoed by the owner, reverted or repaired, each vetoed spec "
        f"call marked denied' --brief-file {brief}"
    )
    assert ok.out.splitlines()[-1] == start, ok.out
    assert ok.out.startswith(f"filed: issue {key}, {title}"), ok.out

    before, calls = log_text(w), len(s.gh.log())
    again = director(s, w, "veto", str(PR_B), "--said", SAID, "--repo", REALCASE, want=1)
    assert f"PR #{PR_B} is already vetoed: issue {key}" in again.err, again.err
    assert len(s.gh.log()) == calls, s.gh.log()[calls:]
    assert log_text(w) == before, log_text(w)[len(before) :]


if __name__ == "__main__":
    main(veto_refused, veto_files_repair)
