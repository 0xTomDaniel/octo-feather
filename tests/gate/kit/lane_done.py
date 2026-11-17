"""The scenarios of tests/gate/kit/test_lane_done.py (its items), this file their command
(testkit.main): scripts/octo-feather-lane done, the supervisor's lane close (spec issue-lifecycle
#gates-pr-line, #acceptance-merge-linear, #acceptance-merge-approved-head,
#acceptance-no-github-issue), offline. A Linear target's close, against the kit's offline fake
linear (the linear skill's scripts/linear) with the testkit's gh first on PATH, moves the parent
and every ticket to done through the tracker skill's issue-done, leaves a Canceled ticket Canceled,
and runs no gh at all (no GitHub issue filed or closed); a GitHub target's close, the testkit's gh
answering only real gh's recorded answers (testkit/recordings/lane-done.json), closes every
sub-issue and then the parent through issue-done, and files nothing. A ticket the tracker cannot
move fails naming it, after the others were tried, the parent last."""

from __future__ import annotations

import json
import os
from pathlib import Path

from testkit import ROOT, Ran, Scratch, kit, main

LINEAR = ROOT / ".agents" / "skills" / "linear" / "scripts"
# gh 2.102.0 on 0xTomDaniel/octo-feather, 2026-11-17 (each recording's source): one real
# `octo-feather-lane done 944` on scratch issues, open parent #944 with open sub-issue #945 and
# already-closed #938, which closed #945 and #944.
TAPE = Path(__file__).parent / "testkit" / "recordings" / "lane-done.json"
STORE: dict[str, object] = {
    "workspace": "acme",
    "issues": {
        k: {"title": title, "description": desc, "state": state, "parent": parent, "blocked_by": []}
        for k, title, desc, state, parent in (
            ("ENG-123", "Lane", "p", "In Progress", None),
            ("ENG-124", "T1", "t", "Todo", "ENG-123"),
            ("ENG-125", "T2", "t", "Canceled", "ENG-123"),
            ("ENG-126", "T3", "t", "Done", "ENG-123"),
            ("ENG-200", "Other", "o", "Todo", None),
        )
    },
}


def done(s: Scratch, repo: str, *args: str, want: int = 0) -> Ran:
    return s.run([kit("octo-feather-lane"), "done", *args], want=want, cwd=s.root / repo)


def linear(s: Scratch) -> None:
    """issue-lifecycle#acceptance-merge-linear, #acceptance-no-github-issue: a Linear target's
    close moves ENG-123 and its tickets to Done (ENG-125 stays Canceled, another lane's ENG-200
    untouched), no gh run; a rerun leaves done tickets as they are; an unknown parent is named; a
    team with no completed state: every move fails, each named, the parent tried last; no parent
    is a usage error."""
    store = s.root / "linear.json"
    store.write_text(json.dumps(STORE))
    s.env |= {
        "OCTO_FEATHER_LINEAR_STORE": str(store),
        "PATH": f"{s.bin}{os.pathsep}{LINEAR}{os.pathsep}{s.env['PATH']}",
    }
    s.git(s.root, "init", "-q", "-b", "main", "lin")
    (s.root / "lin" / ".octo-feather.toml").write_text('tracker = "linear"\n')

    def state(k: str) -> str:
        return str(json.loads(store.read_text())["issues"][k]["state"])

    r = done(s, "lin", "eng-123")
    moved = "ENG-124: done\nENG-125: done\nENG-126: done\nENG-123: done\n"
    assert r.out == moved + "ENG-123: parent and 3 tickets done", f"linear done output: {r.out}"
    for k in ("ENG-123", "ENG-124", "ENG-126"):
        assert state(k) == "Done", f"{k} is {state(k)}, not Done"
    assert state("ENG-125") == "Canceled", f"canceled ENG-125 moved to {state('ENG-125')}"
    assert state("ENG-200") == "Todo", f"another lane's ENG-200 moved to {state('ENG-200')}"
    assert not s.gh.log(), (
        f"a Linear lane's close ran gh (no GitHub issue may be filed or closed): {s.gh.log()}"
    )
    done(s, "lin", "ENG-123")  # a rerun leaves done tickets as they are
    assert (state("ENG-125"), state("ENG-123")) == ("Canceled", "Done"), "rerun changed states"
    r = done(s, "lin", "ENG-999", want=1)
    assert "tracker script linear/issue-view ENG-999 failed" in r.err, f"unknown parent: {r.err}"
    d = json.loads(store.read_text())
    d["states"] = [{"name": "Todo", "type": "unstarted"}, {"name": "Canceled", "type": "canceled"}]
    for k in ("ENG-124", "ENG-123", "ENG-126"):
        d["issues"][k]["state"] = "Todo"
    store.write_text(json.dumps(d))
    r = done(s, "lin", "ENG-123", want=1)
    failed = (
        r.out == "ENG-125: done"
        and "ENG-123: 3 of 4 not done" in r.err
        and any(
            x.startswith("  - ENG-124: ") and "Unknown workflow state" in x
            for x in r.err.split("\n")
        )
        and "  - ENG-123: " in r.err
        and "rerun `octo-feather-lane done ENG-123`" in r.err
    )
    assert failed, f"failed moves: {r.out} {r.err}"
    r = done(s, "lin", want=1)
    assert "usage: octo-feather-lane done PARENT" in r.err, f"usage: {r.err}"


def github(s: Scratch) -> None:
    """A GitHub target (no .octo-feather.toml): open parent 944 with open sub-issue 945 and
    already-closed 938: 938, 945, then 944 closed through issue-done; gh asked only issue view and
    issue close. An unrecorded parent: testkit/gh.py's replay owns the refusal."""
    s.git(s.root, "init", "-q", "-b", "main", "gh")
    s.gh.store("tape.json", json.loads(TAPE.read_text()))
    r = done(s, "gh", "944")
    want = "938: done\n945: done\n944: done\n944: parent and 2 tickets done"
    assert r.out == want, f"github done output: {r.out}"
    log = s.gh.log()
    closes = [x for x in log if x.startswith("issue close")]
    assert closes == ["issue close 938", "issue close 945", "issue close 944"], (
        f"github closes: {log}"
    )
    assert all(x.startswith(("issue view ", "issue close ")) for x in log), (
        f"github close ran another gh command: {log}"
    )
    r = done(s, "gh", "9", want=1)
    unrecorded = "fake gh: no recording for call 1 of 'issue view 9 --json "
    assert "tracker script github-issues/issue-view 9 failed" in r.err, f"unrecorded: {r.err}"
    assert unrecorded in r.err, f"unrecorded: {r.err}"


if __name__ == "__main__":
    main(linear, github)
