"""The scenario of tests/gate/kit/test_lane_merge_ask_hunks.py (its item), this file its command
(testkit.main): `octo-feather-lane merge-ask` keeps a lane's verdicts across a clean merge of
main that changed another part of a lane file (spec issue-lifecycle #lanes-one-head,
#acceptance-one-head-hunks), no network. The lane is lane_merge_ask.py's (a real git repo, PR #7
in the fake gh): its judged head J changed app.py's line 1, with clear qc rows and a clear review
verdict on J and J's full gate pass recorded, then qc's status commit H. Main then changes
app.py's line 20; the lane merges it with no conflict as R, the PR head. merge-ask passes at R on
J's verdicts with no new judge run, its Judged proof naming J, R and the lane's hunks unchanged.
The rule's own cases (the lane's own hunks changed): test_merge_ask.py, in-process."""

from __future__ import annotations

import re

from lane_merge_ask import Lane, pr_head, section
from testkit import Scratch, main


def one_head_hunks(s: Scratch) -> None:
    """issue-lifecycle#acceptance-one-head-hunks: the clean merge of main keeps both verdicts."""
    ln = Lane(s)
    j, h = ln.j, ln.h

    def twenty() -> None:  # main changes another part of the lane's file
        ln.line(20, "twenty")
        ln.commit("main: twenty")

    m = ln.on(ln.b, twenty)
    ln.main(m)
    r = ln.merge(h, m)
    assert ln.git("show", "-s", "--format=%P", r).split() == [h, m], "R is not a merge of main"
    assert ln.git("show", f"{r}:app.py").splitlines()[::19] == ["one", "twenty"], "not both edits"
    n = ln.writes()
    judged = re.escape(f"{j[:12]} to {r[:12]}: qc status commits {h[:12]} change only ")
    proof = (
        rf"{judged}\S+; clean merge of main {r[:12]}: lane hunks identical \(1 file, sha256 "
        r"[0-9a-f]{12}\)"
    )
    # the check names its proof line for the section to quote
    got = ln.bad(
        rf"add the check's proof line `Judged: ({proof})`",
        pr_head(r, "Merge main"),
        regex=True,
        head=r[:12],
    )
    line = re.search(rf"`Judged: ({proof})`", got.err)
    assert line, got.err
    ln.setpr(pr_head(r, "Merge main"), head=r[:12], judged=line[1])
    out = ln.ask().out
    lines = section(out)
    assert f"Head: {r[:12]}" in lines, out
    assert f"Judged: {line[1]}" in lines, out
    assert f"Review verdict: {ln.url}" in lines, out
    assert f"| demo#acceptance-a | pass | judged {j[:7]} | qc report a1b2.json, cmd ok |" in lines
    assert ln.writes() == n, "merge-ask wrote: a judge ran again"


if __name__ == "__main__":
    main(one_head_hunks)
