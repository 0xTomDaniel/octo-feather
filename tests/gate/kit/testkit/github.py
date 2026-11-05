#!/usr/bin/env python3
"""Fake GitHub `gh` for repo o/r, its issues only, for scripts/octo-feather-qc-ghsnap to snapshot
(the testkit's stand-in for GitHub where a test serves issues through the offline gh,
.agents/skills/github-pr/scripts/gh). A store, no logic of the kit's: $FAKE_GITHUB is a JSON
object of issue number to `gh issue view --json` fields. As real gh, it answers every --json
field asked, the stored value or null, so a snapshot holds exactly the fields ghsnap asks for.
repo view answers o/r; issue list every issue; pr list and run list nothing; api: sub-issue and
dependency paths 404, branches, labels and timelines empty, any other path the repo. Anything
else exits 2 naming it.
"""

import json
import os
import sys

a = sys.argv[1:]
with open(os.environ["FAKE_GITHUB"]) as f:  # noqa: PTH123
    iss = {int(k): v for k, v in json.load(f).items()}


def out(x: object) -> None:
    sys.stdout.write(json.dumps(x) + "\n")
    sys.exit(0)


def pick(d: dict[str, object]) -> dict[str, object]:
    return {f: d.get(f) for f in a[a.index("--json") + 1].split(",")}


c = a[:2]
if c == ["repo", "view"]:
    out(
        pick(
            {
                "nameWithOwner": "o/r",
                "name": "r",
                "owner": {"login": "o"},
                "defaultBranchRef": {"name": "main"},
            }
        )
    )
if c == ["issue", "list"]:
    out([pick(d) for d in iss.values()])
if c in (["pr", "list"], ["run", "list"]):
    out([])
if c == ["issue", "view"]:
    out(pick(iss[int(a[2])]))
if a[0] == "api":
    p = a[-1]
    if "sub_issues" in p or "dependencies" in p:
        sys.stderr.write("gh: Not Found (HTTP 404)\n")
        sys.exit(1)
    empty: list[object] = [[]]
    out(empty if p.endswith(("/branches", "/labels", "/timeline")) else [{"full_name": "o/r"}])
sys.stderr.write(f"fake github gh: unexpected {a}\n")
sys.exit(2)
