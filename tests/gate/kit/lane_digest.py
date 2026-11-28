"""The scenarios of tests/gate/kit/test_lane_digest.py (its items), this file their command
(testkit.main): `octo-feather-lane merge` and `octo-feather-lane digest` (what each does:
`octo-feather-lane --help`, merge, digest; issue-lifecycle #gates-digest,
#acceptance-merge-digest; issue 1339), offline, gh answering only real gh's recorded answers.

The real case (testkit.realcase DIGEST, lane gh1337's recording, #1339): on
0xTomDaniel/octo-feather-realcase, on 2026-11-28, from a scratch world as RealCase builds, lane
gh49 (parent issue 49) merged PR #51 (one file, tier 1) and then lane gh50 (issue 50) merged PR
#52 (one file and one call of kind clarifies appended to docs/specs/gh1337-demo.calls.jsonl,
tier 2), each through `octo-feather-lane merge` as its own supervisor; then PR #53 was merged
with plain `gh pr merge`, outside the merge command; then `digest 2026-11-28 --repo <it>` ran.
Every gh call recorded, unmodified: lane-merge-digest-51.json, lane-merge-digest-52.json,
lane-digest-1339.json; the git objects realcase-gh1337.bundle. GitHub's main moved at each real
merge; the fake gh's merge moves no git, so origin.git's main is set where GitHub's stood (the
merge commit the tape's step 1 read names) before each merge, the director's checkout having
fetched it last before the first (its origin/main the first merge's parent), as in the run.
"""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING

from testkit import Scratch, kit, main
from testkit.realcase import REALCASE, Case, RealCase, merged_view, recorded, recordings

if TYPE_CHECKING:
    from testkit import Ran

DIGEST = Case("realcase-gh1337", "lane-merge-digest-51", 51, "gh49", "gh50")
TAPE_B, TAPE_DAY, PR_B = "lane-merge-digest-52", "lane-digest-1339", 52
DAY = "2026-11-28"
CALLS = "docs/specs/gh1337-demo.calls.jsonl"
LIST = (
    f"pr list --state merged --base main --search merged:2026-11-27..2026-11-29 --limit 1000 "
    f"--json number,title,url,mergedAt,mergeCommit,headRefOid -R {REALCASE}"
)


def merge_commit(tape: str, pr: int) -> str:
    """The merge commit step 1's recorded read of merged PR names."""
    return json.loads(recorded(tape, merged_view(pr)))["mergeCommit"]["oid"]


def head(tape: str, pr: int) -> str:
    """The head the merge guard's recorded first read of PR names."""
    return json.loads(recorded(tape, f"pr view {pr} --json state,headRefOid -R {REALCASE}"))[
        "headRefOid"
    ]


def digest_lists_the_day(s: Scratch) -> None:
    """issue-lifecycle#acceptance-merge-digest on the real case (the module docstring; the
    ticket's demo, its commands and output printed): lane gh49's `merge 51` and lane gh50's
    `merge 52`, each from the director's checkout as its own supervisor, ask gh exactly the
    recorded runs' calls (the merge adds no gh call to record its ask) and exit 0. Then
    `digest 2026-11-28 --repo <realcase>` asks gh only the recorded digest's two reads (the
    default branch, the merged PRs of the search window), no merge ask check rerun for any PR,
    and prints #51 (tier 1), #52 (tier 2, its one clarifying call as the bundle's merged main
    holds it) and #53 (merged outside the merge command, no recorded ask) in merge order, each
    in the form `octo-feather-lane --help`, digest, gives. Exit 0."""
    w = RealCase(s, DIGEST.tape, TAPE_B, TAPE_DAY, case=DIGEST)
    with (w.lanes / f"{DIGEST.other}.toml").open("a") as f:
        f.write(f"pr = {PR_B}\n")  # lane gh50's PR, as its supervisor recorded it
    m1, m2 = merge_commit(DIGEST.tape, DIGEST.pr), merge_commit(TAPE_B, PR_B)
    s.git(w.checkout, "update-ref", "refs/remotes/origin/main", f"{m1}^1")
    s.git(w.origin, "update-ref", "refs/heads/main", m1)
    w.lane("merge", str(DIGEST.pr), head(DIGEST.tape, DIGEST.pr)[:12], "--repo", REALCASE)
    s.git(w.origin, "update-ref", "refs/heads/main", m2)
    b = {"HERDR_PANE_ID": "zt2:p1", "HERDR_WORKSPACE_ID": "zt2"}  # lane gh50's supervisor
    lane_b = ["merge", str(PR_B), head(TAPE_B, PR_B)[:12], "--repo", REALCASE]
    shown(s.run([kit("octo-feather-lane"), *lane_b], cwd=w.checkout, env=b), lane_b)
    merges = [str(x["request"]) for t in (DIGEST.tape, TAPE_B) for x in recordings(t)]
    assert s.gh.log() == merges, f"gh calls, want the recorded merges': {s.gh.log()}"

    r = w.lane("digest", DAY, "--repo", REALCASE)
    day = [str(x["request"]) for x in recordings(TAPE_DAY)]
    assert s.gh.log() == merges + day, f"the digest's gh calls: {s.gh.log()[len(merges) :]}"
    prs = {p["number"]: p for p in json.loads(recorded(TAPE_DAY, LIST))}
    assert sorted(prs) == [51, 52, 53], sorted(prs)

    def one(n: int, what: str) -> str:
        p = prs[n]
        return f"#{n} {p['title']} ({what}, merged {p['mergedAt'][11:16]}Z) {p['url']}"

    call = json.loads(s.git(w.checkout, "show", f"{m2}:{CALLS}"))
    p53 = prs[53]
    want = [
        f"Merge digest {DAY} ({REALCASE}, merged in [{DAY} 00:00Z, 2026-11-29 00:00Z)): 3 merged",
        "",
        one(51, "tier 1"),
        "",
        one(52, "tier 2"),
        f"  merged {prs[52]['mergedAt']}, head {head(TAPE_B, PR_B)}, merge {m2}",
        "  Tier: 2",
        f"  - spec call gh1337-demo {call['at']} clarifies {', '.join(call['anchors'])}",
        "  Waits for: nobody",
        "  allowed: by its tier, waiting for nobody",
        f"  spec call gh1337-demo clarifies at {call['at']} (lane {call['lane']})",
        f"    anchors: {', '.join(call['anchors'])}",
        f"    criteria: {', '.join(call['criteria'])}",
        f"    what: {call['what']}",
        f"    why: {call['why']}",
        f"    evidence: {call['evidence']}",
        f"    role: {call['role']}",
        "    ruling: none",
        "",
        (
            f"#53 {p53['title']} (tier not recorded: no merge record) {p53['url']}, merge "
            f"{p53['mergeCommit']['oid']}"
        ),
    ]
    assert r.out.split("\n") == want, r.out


def shown(r: Ran, args: list[str]) -> Ran:
    """R printed as RealCase.lane prints its command (the demo's)."""
    sys.stdout.write(
        f"$ octo-feather-lane {' '.join(args)}  # exit {r.rc}\n{r.out}\n{r.err}".rstrip() + "\n"
    )
    return r


if __name__ == "__main__":
    main(digest_lists_the_day)
