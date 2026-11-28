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

The due days (issue 1340): the same recordings replayed, a merge of 2026-11-28 now one of the past.
Time is the one thing moved: testkit.clock sets the commands' now, lane gh49's merge on
2026-11-28 at PR #51's real mergedAt, everything after it on the next day, 2026-11-29 08:00Z.
PR #52, merged by the merge command in the first scenario, is in the second one of the merges
made outside it (its tape replayed only for the last merge). A digest the scenario asks for
again replays the digest's recordings again, as GitHub answers the same reads the same.

  due_from_merge  lane gh49's merge (2026-11-28) tells the director no digest: today is never
           due. Lane gh50's merge the next day tells the director (w9:p99), once, `merge digest
           due for 2026-11-28: octo-feather-lane digest --repo <realcase>, send its text to the
           owner, then octo-feather-lane digest --repo <realcase> --sent <sha12>`, the merge
           printing `director told (w9:p99): <it>`; gh asked only the merges' recorded calls.
  due_until_sent  beside a real kit post-merge record of 2026-11-24 written before records held
           an ask (tests/fixtures/post-merge/gh1224.json, unmodified), lane gh49 merges on
           2026-11-28. Next day: `start` from the director's pane prints the due line for
           2026-11-28 alone, first (its usage refusal after it, no gh call); `digest --repo
           <realcase>` prints the digest of 2026-11-28 alone (2026-11-24 before the first ask,
           2026-11-29 today), then `sha256 <12 hex>`, the sha256 of the text above it, asking
           gh only the digest's two reads. `digest --repo <realcase> --sent <sha12>` from lane
           gh49's supervisor's pane: refused, `only the director records a digest sent`,
           nothing recorded, no gh call; from the director's pane with another sha: refused
           naming both, nothing recorded; with the printed sha: exit 0, the director log's last
           line {"at", "kind": "digest", "repo", "days": ["2026-11-28"], "prs": [51, 52, 53],
           "sha256", "sent": true}. Then `start` prints no due line, `digest` prints `No merge
           digest due` with no gh call, and lane gh50's merge of PR #52 tells the director no
           digest.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from typing import TYPE_CHECKING

from testkit import FIXTURES, Scratch, clock, kit, main
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


NEXT_DAY = "2026-11-29T08:00:00Z"
DIRECTOR = {"HERDR_PANE_ID": "w9:p99", "HERDR_WORKSPACE_ID": "w9"}
B = {"HERDR_PANE_ID": "zt2:p1", "HERDR_WORKSPACE_ID": "zt2"}  # lane gh50's supervisor
DUE = (
    f"merge digest due for {DAY}: octo-feather-lane digest --repo {REALCASE}, send its text to "
    f"the owner, then octo-feather-lane digest --repo {REALCASE} --sent <sha12>"
)


def world(s: Scratch, *tapes: str) -> RealCase:
    """The real case's world (the module docstring), gh answering from TAPES."""
    w = RealCase(s, *tapes, case=DIGEST)
    with (w.lanes / f"{DIGEST.other}.toml").open("a") as f:
        f.write(f"pr = {PR_B}\n")  # lane gh50's PR, as its supervisor recorded it
    return w


def merge_a(s: Scratch, w: RealCase) -> None:
    """Lane gh49's `merge 51` from the director's checkout as its supervisor, main where it
    stood."""
    m1 = merge_commit(DIGEST.tape, DIGEST.pr)
    s.git(w.checkout, "update-ref", "refs/remotes/origin/main", f"{m1}^1")
    s.git(w.origin, "update-ref", "refs/heads/main", m1)
    w.lane("merge", str(DIGEST.pr), head(DIGEST.tape, DIGEST.pr)[:12], "--repo", REALCASE)


def merge_b(s: Scratch, w: RealCase) -> Ran:
    """Lane gh50's `merge 52` from the director's checkout as its supervisor."""
    s.git(w.origin, "update-ref", "refs/heads/main", merge_commit(TAPE_B, PR_B))
    lane_b = ["merge", str(PR_B), head(TAPE_B, PR_B)[:12], "--repo", REALCASE]
    return shown(s.run([kit("octo-feather-lane"), *lane_b], cwd=w.checkout, env=B), lane_b)


def digest_told(w: RealCase) -> list[str]:
    return [x for x in w.told() if "merge digest due" in x]


def merged_at(pr: int) -> str:
    """PR's real mergedAt, as the recorded digest's list of merged PRs names it."""
    return next(p["mergedAt"] for p in json.loads(recorded(TAPE_DAY, LIST)) if p["number"] == pr)


def due_from_merge(s: Scratch) -> None:
    """issue-lifecycle#acceptance-merge-digest, the merge edge (the module docstring)."""
    w = world(s, DIGEST.tape, TAPE_B)
    clock(s, merged_at(51))
    merge_a(s, w)
    assert digest_told(w) == [], w.told()
    clock(s, NEXT_DAY)
    r = merge_b(s, w)
    assert digest_told(w) == [f"w9:p99\t{DUE}"], w.told()
    assert f"director told (w9:p99): {DUE}" in r.out.split("\n"), r.out
    merges = [str(x["request"]) for t in (DIGEST.tape, TAPE_B) for x in recordings(t)]
    assert s.gh.log() == merges, f"gh calls, want the recorded merges': {s.gh.log()}"


def due_until_sent(s: Scratch) -> None:
    """issue-lifecycle#acceptance-merge-digest, the start edge, `digest` with no DAY and
    `digest --sent` (the module docstring)."""
    w = world(s, DIGEST.tape, TAPE_DAY, TAPE_DAY, TAPE_DAY, TAPE_B)
    (w.top / "post-merge").mkdir()
    shutil.copy(FIXTURES / "post-merge" / "gh1224.json", w.top / "post-merge")
    clock(s, merged_at(51))
    merge_a(s, w)
    clock(s, NEXT_DAY)
    log, calls = w.top / "director.handoffs.jsonl", len(s.gh.log())
    kit_origin, kit_clone = s.root / "kit-origin.git", s.root / "kit-install"
    s.run(["git", "init", "-q", "--bare", str(kit_origin)])
    s.run(["git", "clone", "-q", str(kit_origin), str(kit_clone)])
    s.git(kit_clone, "commit", "-q", "--allow-empty", "-m", "kit")
    s.git(kit_clone, "push", "-q", "origin", "HEAD:main")
    s.git(kit_clone, "fetch", "-q", "origin")
    start = {**DIRECTOR, "OCTO_FEATHER_KIT_INSTALL": str(kit_clone)}
    r = shown(s.run([kit("octo-feather-lane"), "start"], want=1, env=start), ["start"])
    due = DUE.replace(f" --repo {REALCASE}", "")
    assert r.out == due, r.out
    assert "usage: octo-feather-lane start" in r.err, r.err
    assert len(s.gh.log()) == calls, s.gh.log()[calls:]

    r = w.lane("digest", "--repo", REALCASE)
    text, _, sha = r.out.rpartition("\n\nsha256 ")
    assert sha == hashlib.sha256(text.encode()).hexdigest()[:12], r.out
    days = [x for x in text.split("\n") if x.startswith("Merge digest ")]
    assert [x.split()[2] for x in days] == [DAY], days
    assert s.gh.log()[calls:] == [str(x["request"]) for x in recordings(TAPE_DAY)], s.gh.log()
    before = log.read_text()

    sent = ["digest", "--repo", REALCASE, "--sent", sha]
    no = w.lane(*sent, want=1)
    assert "only the director records a digest sent" in no.err, no.err
    other = "0" * 12 if sha != "0" * 12 else "1" * 12
    off = shown(s.run([kit("octo-feather-lane"), *sent[:-1], other], want=1, env=DIRECTOR), sent)
    assert f"--sent {other} is not the digest of {DAY}" in off.err, off.err
    assert f"(sha256 {sha})" in off.err, off.err
    assert log.read_text() == before, log.read_text()[len(before) :]
    ok = shown(s.run([kit("octo-feather-lane"), *sent], env=DIRECTOR), sent)
    assert ok.out.startswith(f"recorded sent: merge digest of {DAY}, sha256 {sha}"), ok.out
    line = json.loads(log.read_text().splitlines()[-1])
    assert line.pop("at").startswith("2026-11-29T"), line
    full = hashlib.sha256(text.encode()).hexdigest()
    want = {"kind": "digest", "repo": REALCASE, "days": [DAY], "prs": [51, 52, 53]}
    assert line == want | {"sha256": full, "sent": True}, line

    calls = len(s.gh.log())
    r = shown(s.run([kit("octo-feather-lane"), "start"], want=1, env=start), ["start"])
    assert r.out == "", r.out
    r = w.lane("digest", "--repo", REALCASE)
    assert r.out.startswith("No merge digest due"), r.out
    assert len(s.gh.log()) == calls, s.gh.log()[calls:]
    merge_b(s, w)
    assert digest_told(w) == [], w.told()


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
    w = world(s, DIGEST.tape, TAPE_B, TAPE_DAY)
    m2 = merge_commit(TAPE_B, PR_B)
    merge_a(s, w)
    merge_b(s, w)
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
    text = "\n".join(want)
    assert r.out == f"{text}\n\nsha256 {hashlib.sha256(text.encode()).hexdigest()[:12]}", r.out


def shown(r: Ran, args: list[str]) -> Ran:
    """R printed as RealCase.lane prints its command (the demo's)."""
    sys.stdout.write(
        f"$ octo-feather-lane {' '.join(args)}  # exit {r.rc}\n{r.out}\n{r.err}".rstrip() + "\n"
    )
    return r


if __name__ == "__main__":
    main(digest_lists_the_day, due_from_merge, due_until_sent)
