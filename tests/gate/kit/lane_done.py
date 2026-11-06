"""The scenarios of tests/gate/kit/test_lane_done.py (its items), this file their command
(testkit.main): scripts/octo-feather-lane done, the supervisor's lane close (spec issue-lifecycle
#gates-pr-line, #acceptance-merge-linear, #acceptance-merge-approved-head,
#acceptance-no-github-issue), offline. A Linear target's close, against the kit's offline fake
linear (the linear skill's scripts/linear) with the testkit's fake gh first on PATH, moves the
parent and every ticket to done through the tracker skill's issue-done, leaves a Canceled ticket
Canceled, and runs no gh at all (no GitHub issue filed or closed); a GitHub target's close,
against the fake gh holding the issues, closes every sub-issue and then the parent through
issue-done, and files nothing. A ticket the tracker cannot move fails naming it, after the others
were tried."""

from __future__ import annotations

import json
import os

from testkit import ROOT, Ran, Scratch, kit, main

LINEAR = ROOT / ".agents" / "skills" / "linear" / "scripts"
STORE: dict[str, object] = {
    "workspace": "acme",
    "issues": {
        k: {"title": title, "description": "t", "state": state, "parent": parent, "blocked_by": []}
        for k, title, state, parent in (
            ("ENG-123", "Lane", "In Progress", None),
            ("ENG-124", "T1", "Todo", "ENG-123"),
            ("ENG-125", "T2", "Canceled", "ENG-123"),
            ("ENG-126", "T3", "Done", "ENG-123"),
            ("ENG-200", "Other", "Todo", None),
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
        "PATH": f"{LINEAR}{os.pathsep}{s.env['PATH']}",
    }
    s.git(s.root, "init", "-q", "-b", "main", "lin")
    (s.root / "lin" / ".octo-feather.toml").write_text('tracker = "linear"\n')

    def state(k: str) -> str:
        return str(json.loads(store.read_text())["issues"][k]["state"])

    r = done(s, "lin", "eng-123")
    moved = "ENG-124: done\nENG-125: done\nENG-126: done\nENG-123: done\n"
    assert r.out == moved + "ENG-123: parent and 3 tickets done", f"linear done output: {r.out}"
    got = {k: state(k) for k in ("ENG-123", "ENG-124", "ENG-125", "ENG-126", "ENG-200")}
    want = {
        "ENG-123": "Done",
        "ENG-124": "Done",
        "ENG-125": "Canceled",
        "ENG-126": "Done",
        "ENG-200": "Todo",
    }
    assert got == want, f"linear states: {got}"
    assert not s.gh.log(), f"a Linear lane's close ran gh: {s.gh.log()}"
    done(s, "lin", "ENG-123")  # a rerun leaves done tickets as they are
    assert (state("ENG-125"), state("ENG-123")) == ("Canceled", "Done"), "rerun changed states"
    r = done(s, "lin", "ENG-999", want=1)
    assert "tracker script linear/issue-view ENG-999 failed" in r.err, f"unknown parent: {r.err}"
    d = json.loads(store.read_text())
    d["states"] = [{"name": "Todo", "type": "unstarted"}, {"name": "Canceled", "type": "canceled"}]
    for k in ("ENG-123", "ENG-124", "ENG-126"):
        d["issues"][k]["state"] = "Todo"
    store.write_text(json.dumps(d))
    r = done(s, "lin", "ENG-123", want=1)
    assert r.out == "ENG-125: done", f"failed moves: {r.out}"
    for w in (
        "ENG-123: 3 of 4 not done",
        "  - ENG-123: ",
        "rerun `octo-feather-lane done ENG-123`",
    ):
        assert w in r.err, f"failed moves: no {w!r} in {r.err}"
    assert any(
        x.startswith("  - ENG-124: ") and "Unknown workflow state" in x for x in r.err.split("\n")
    ), f"failed moves: {r.err}"
    r = done(s, "lin", want=1)
    assert "usage: octo-feather-lane done PARENT" in r.err, f"usage: {r.err}"
    assert not s.gh.log(), f"a Linear lane's close ran gh: {s.gh.log()}"


def github(s: Scratch) -> None:
    """A GitHub target (no .octo-feather.toml): parent 6 with sub-issues 7 and 8 (8 already
    closed), 9 another lane's: 7, 8, then 6 closed through issue-done, 9 left open; gh asked only
    issue view and issue close."""
    s.git(s.root, "init", "-q", "-b", "main", "gh")

    def issue(n: int, state: str, parent: int | None, kids: list[int]) -> None:
        nodes = [{"number": k} for k in kids]
        s.gh.store(
            f"issue/{n}.json",
            {
                "number": n,
                "title": "t",
                "body": "b",
                "state": state,
                "url": "u",
                "parent": {"number": parent} if parent else None,
                "subIssues": {"nodes": nodes, "totalCount": len(nodes)},
                "blockedBy": {"nodes": [], "totalCount": 0},
            },
        )

    issue(6, "OPEN", None, [7, 8])
    issue(7, "OPEN", 6, [])
    issue(8, "CLOSED", 6, [])
    issue(9, "OPEN", None, [])
    r = done(s, "gh", "6")
    assert r.out == "7: done\n8: done\n6: done\n6: parent and 2 tickets done", (
        f"github done output: {r.out}"
    )
    states = [
        json.loads((s.gh.dir / "issue" / f"{n}.json").read_text())["state"] for n in (6, 7, 8, 9)
    ]
    assert states == ["CLOSED", "CLOSED", "CLOSED", "OPEN"], f"github states: {states}"
    log = s.gh.log()
    closes = [x for x in log if x.startswith("issue close")]
    assert closes == ["issue close 7", "issue close 8", "issue close 6"], f"github closes: {log}"
    assert all(x.startswith(("issue view ", "issue close ")) for x in log), (
        f"another gh command: {log}"
    )


if __name__ == "__main__":
    main(linear, github)
