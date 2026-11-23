"""Issues named to octo-feather-qc-ghsnap beside its window (#1225; issue-lifecycle
#acceptance-correction-replay-shown): `octo-feather-qc-ghsnap REPO DIR [ISSUE...]`. GitHub is the
testkit's fake gh, holding issue #1, older than the window (the 200 most recently updated issues
and PRs: 200 newer PRs here), and #1's notes as GitHub answers the github-issues issue-view --notes
query (shape: testkit/recordings/lane-skills.json, as tests/gate/kit/lane_tickets.py builds it).
Snapshotted with no number named, #1 is a list row only and the offline gh refuses its notes;
named, the offline gh (.agents/skills/github-pr/scripts/gh), read with no network (`unshare -cn`:
a real namespace, so end-to-end, quality spec #test-kinds), answers `gh issue view 1 --json` and
issue-view 1 --notes as the fake GitHub does, every other file of the snapshot unchanged. A named
number GitHub does not have is named in the summary line and meta.json's absent, never dropped."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from testkit import ROOT, Scratch, kit, main

if TYPE_CHECKING:
    from pathlib import Path

OFFLINE_GH = ROOT / ".agents" / "skills" / "github-pr" / "scripts" / "gh"
VIEW = str(ROOT / ".agents" / "skills" / "github-issues" / "scripts" / "issue-view")
NOTES = ROOT / ".agents" / "skills" / "github-issues" / "scripts" / "notes.graphql"
# Every field the snapshot's full issue view asks (as octo-feather-qc-ghsnap's IF), read back here
# through the offline gh as `gh issue view --json` asks it.
FIELDS = (
    "assignees,author,blockedBy,blocking,body,closed,closedAt,closedByPullRequestsReferences,"
    "comments,createdAt,id,labels,milestone,number,parent,state,stateReason,subIssues,"
    "subIssuesSummary,title,updatedAt,url"
)
OLD: dict[str, object] = {
    "number": 1,
    "title": "The parent, filed long ago",
    "state": "CLOSED",
    "createdAt": "2025-01-01T00:00:00Z",
    "updatedAt": "2025-01-02T00:00:00Z",
    "author": {"login": "a"},
    "labels": [],
    "body": "The old parent's body.",
    "comments": [
        {"author": {"login": "b"}, "body": "a late note", "createdAt": "2025-01-02T00:00:00Z"}
    ],
    "url": "https://github.com/o/r/issues/1",
    "subIssues": {"nodes": [], "totalCount": 0},
    "blockedBy": {"nodes": []},
}


def github(s: Scratch) -> None:
    """The fake GitHub o/r: #1 (OLD) and 200 merged PRs updated after it, #1's notes answer."""
    s.gh.store("repo.json", {"nameWithOwner": "o/r", "name": "r", "owner": {"login": "o"}})
    s.gh.store("issue/1.json", OLD)
    for n in range(2, 202):
        day = f"2026-11-{n % 20 + 1:02d}T00:00:00Z"
        pr: dict[str, object] = {"number": n, "title": f"p{n}", "state": "MERGED", "updatedAt": day}
        pr |= {"author": {"login": "a"}, "body": "", "comments": []}
        s.gh.store(f"pr/{n}.json", pr)
        s.gh.store(f"pr/{n}.diff", "")
    issue: dict[str, object] = {
        "url": OLD["url"],
        "createdAt": OLD["createdAt"],
        "lastEditedAt": "2025-01-02T00:00:00Z",
        "body": OLD["body"],
        "comments": {
            "pageInfo": {"hasNextPage": False},
            "nodes": [
                {
                    "url": f"{OLD['url']}#issuecomment-5",
                    "createdAt": "2025-01-02T00:00:00Z",
                    "lastEditedAt": None,
                    "body": "a late note",
                }
            ],
        },
    }
    query = NOTES.read_text().rstrip("\n")
    s.gh.store(
        "recorded.json",
        [
            {
                "request": f"api graphql -F n=1 -f owner=o -f name=r -f query={query}",
                "out": json.dumps(
                    {"data": {"repository": {"issue": issue}}}, separators=(",", ":")
                ),
                "err": "",
                "exit": 0,
                "source": "built (shape: testkit/recordings/lane-skills.json)",
            }
        ],
    )


def files(d: Path) -> dict[str, str]:
    """Snapshot D's files and their text, but meta.json and fetched_at (the fetch's own time)."""
    skip = {"meta.json", "fetched_at"}
    return {
        str(p.relative_to(d)): p.read_text()
        for p in d.rglob("*")
        if p.is_file() and p.name not in skip
    }


def named_issue(s: Scratch) -> None:
    github(s)
    off = s.root / "off"
    off.mkdir()
    (off / "gh").symlink_to(OFFLINE_GH)

    def offline(snap: Path, *cmd: str, want: int = 0) -> str:
        env = {
            "PATH": f"{off}:{s.env['PATH']}",
            "OCTO_FEATHER_GHSNAP": str(snap),
            "OCTO_FEATHER_GHSNAP_MISS": str(s.root / "miss.log"),
        }
        r = s.run(["unshare", "-cn", *cmd], want=want, env=env)
        return r.out + r.err

    plain, named = s.root / "plain", s.root / "named"
    line = s.run([kit("octo-feather-qc-ghsnap"), "o/r", str(plain)]).out
    assert "list-only: #1" in line, line  # #1 is older than the window
    assert "named" not in line, line
    refused = offline(plain, VIEW, "1", "--notes", want=1)
    assert "#1 notes" in refused, refused
    assert "not in read-only snapshot" in refused, refused

    line = s.run([kit("octo-feather-qc-ghsnap"), "o/r", str(named), "1", "9999"]).out
    assert "list-only:" not in line, line
    assert "named, not on GitHub: #9999" in line, line
    meta = json.loads((named / "meta.json").read_text())
    assert meta["capped"] == [], meta
    assert "issue #9999" in meta["absent"], meta
    live = json.loads(s.run(["gh", "issue", "view", "1", "--json", FIELDS]).out)
    got = json.loads(offline(named, "gh", "issue", "view", "1", "--json", FIELDS))
    assert got == live, f"{got} != {live}"
    (s.gh.dir / "log").write_text(
        ""
    )  # the fake GitHub's notes answer replays afresh for issue-view
    live = json.loads(s.run([VIEW, "1", "--notes"]).out)
    got = json.loads(offline(named, VIEW, "1", "--notes"))
    assert got == live, f"{got} != {live}"
    assert got["notes"][-1]["body"] == "a late note", got
    assert "not in snapshot" in offline(
        named, "gh", "issue", "view", "9999", "--json", "title", want=1
    )
    before, after = files(plain), files(named)
    assert {k: after.get(k) for k in before} == before, "a named issue changed the window's files"
    new = {
        "issue/1.json",
        "issue/1.notes.json",
        "notes.graphql",
    }  # the query: the window has no issue
    assert set(after) - set(before) == new, set(after) - set(before)


if __name__ == "__main__":
    main(named_issue)
