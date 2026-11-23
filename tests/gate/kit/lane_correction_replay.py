"""The scenarios of tests/gate/kit/test_lane_correction_replay.py (its items), this file their
command (testkit.main): a correction lane's merge ask carries a `## Replay` table and
`octo-feather-lane merge-ask` reruns every row itself, each in its own qc sandbox over one
offline GitHub snapshot (issue-lifecycle #lanes-correction, #acceptance-correction-replay-missing,
#acceptance-correction-replay-shown; #1226). End to end (quality spec #test-kinds): the real qc
sandbox (srt, user namespaces), the real octo-feather-qc-ghsnap over the testkit's fake gh, which
stands in for GitHub outside the sandbox; the box's mise installs as its mise check finds them.

The recorded case, PR #1216 (lane gh1121) as tests/gate/kit/lane_verdict_rounds.py builds it
offline (Lane: the scratch repo at head 2dc6f718, the fake gh), its rounds 2 and 3 posted, so the
verdict comment lists round 2's two Check lines on scripts/octo-feather-lane; its origin
github.com/0xTomDaniel/octo-feather, the repository GitHub (the fake gh) holds. Its parent #1121
and every ticket a row's seam check reads come from GitHub as recorded
(testkit/recordings/correction-replay-1216.json, the github-issues issue-view of each), the same
issues stored as GitHub's for the snapshot: #1121's title carries
`[correction-lane unlisted-test-seam]`, its body and comments quote 13 finding lines. The state
dir's archived lanes are the box's own (tests/fixtures/correction-replay/lanes/archive: each
record verbatim, each hand-off log cut to its finding lines and its last line): gh1074 archived
after #1216's first commit (0347bcd5, 2026-11-21T11:13:39Z), gh1085 holding a finding of the
class, gh706 the sixth newest; the clean sample is gh1197, gh1192, gh905, gh1146 and gh1132. Each
row replays the seam check #1216 changed (`seam TICKET ID SEAM --before REV`, as 2dc6f718 has it)
on the ticket and test commit its finding names; four findings name no test commit or no seam:
not replayable. Run on GitHub (2026-11-22) the rows gave what ROWS claims: nine findings caught,
clean gh1192 refused (#1193 holds no Seam record).

The trigger case: #1121 marked but quoting no finding line (built, as the notes query answers:
testkit/recordings/lane-skills.json's shape), no archived lane: one `trigger` row, no clean one;
masked adds a Pi session to the box, which every row's sandbox masks (#1241).

The recorded #1233 case (#1241; Recorded1233): #1228's 17 send-back items, 10 finding ids, each
row declared not replayable (the skills check needs the worker's Pi session and the caller's
Herdr pane, neither of which the sandbox serves); the replay done outside merge-ask is lane
gh1228's, /home/exedev/scratch/gh1228-replay/TABLE.md section 1.
"""

from __future__ import annotations

import json
import re
import shutil
from typing import TYPE_CHECKING, Any, TypedDict, cast

import jsonschema
from lane_verdict_rounds import PR, R2, R3, G, L, Lane
from testkit import FIXTURES, HERE, ROOT, Ran, Scratch, fixture, main
from testkit.qc_box import mise_dir

if TYPE_CHECKING:
    from collections.abc import Mapping

REPO = "0xTomDaniel/octo-feather"
SEAM = "scripts/octo-feather-lane seam"
NOTES = ROOT / ".agents" / "skills" / "github-issues" / "scripts" / "notes.graphql"
TRIGGER = "[correction-lane unlisted-test-seam] repeated finding class: unlisted-test-seam"

# The recordings and fixtures read here, each validated once by the kit's pinned jsonschema
# (quality spec #edge-validation-kit), then typed: the fields read, each required with its type.
TEXT = {"type": "string"}
RECORDING = {  # testkit/recordings/*.json, as testkit/gh.py replays them
    "type": "array",
    "items": {
        "type": "object",
        "required": ["request", "out", "err", "exit", "source"],
        "additionalProperties": False,
        "properties": {
            "request": TEXT,
            "out": TEXT,
            "err": TEXT,
            "exit": {"type": "integer"},
            "source": TEXT,
        },
    },
}
ISSUE = {  # gh issue view N --json ...'s answer, the fields read
    "type": "object",
    "required": ["number", "title", "body"],
    "properties": {"number": {"type": "integer"}, "title": TEXT, "body": TEXT},
}
COMMENTS = {  # the notes query's answer (notes.graphql), the path written to
    "type": "object",
    "required": ["data"],
    "properties": {
        "data": {
            "type": "object",
            "required": ["repository"],
            "properties": {
                "repository": {
                    "type": "object",
                    "required": ["issue"],
                    "properties": {
                        "issue": {
                            "type": "object",
                            "required": ["comments"],
                            "properties": {
                                "comments": {
                                    "type": "object",
                                    "required": ["nodes"],
                                    "properties": {"nodes": {"type": "array"}},
                                }
                            },
                        }
                    },
                }
            },
        }
    },
}
FINDING_ITEM = {  # tests/fixtures/correction-replay-1233/findings.jsonl, one line
    "type": "object",
    "required": ["lane", "line"],
    "properties": {
        "lane": TEXT,
        "line": {
            "type": "object",
            "required": ["at", "source", "summary", "ticket", "skill"],
            "properties": dict.fromkeys(("at", "source", "summary", "ticket", "skill"), TEXT),
        },
    },
}


class Recording(TypedDict):
    request: str
    out: str
    err: str
    exit: int
    source: str


class Issue(TypedDict):
    number: int
    title: str
    body: str


class Line(TypedDict):
    at: str
    source: str
    summary: str
    ticket: str
    skill: str


class Item(TypedDict):
    lane: str
    line: Line


def valid(text: str, schema: Mapping[str, object], what: str) -> object:
    """TEXT's JSON once SCHEMA holds for it; else fails naming WHAT and the failing field."""
    doc: object = json.loads(text)
    try:
        jsonschema.validate(doc, schema)
    except jsonschema.ValidationError as e:
        at = ".".join(map(str, e.absolute_path)) or "the document"
        msg = f"{what}: {at}: {e.message}"
        raise AssertionError(msg) from e
    return doc


def tape(name: str) -> list[Recording]:
    """testkit/recordings/NAME.json, validated."""
    p = HERE / "recordings" / f"{name}.json"
    return cast("list[Recording]", valid(p.read_text(), RECORDING, str(p)))


FINDINGS = (  # #1121's finding ids (`<lane> <at>`), in the order its body and comments quote them
    "gh840 2026-11-18T04:20:55Z",
    "gh986 2026-11-18T20:23:18Z",
    "gh987 2026-11-18T20:28:30Z",
    "gh1096 2026-11-19T20:46:40Z",
    "gh901 2026-11-19T00:12:26Z",
    "gh901 2026-11-19T21:25:30Z",
    "gh466 2026-11-18T22:42:09Z",
    "gh978 2026-11-18T19:53:00Z",
    "gh1085 2026-11-20T02:27:58Z",
    "gh644 2026-11-20T01:41:30Z",
    "gh1176 2026-11-20T09:10:37Z",
    "gh1186 2026-11-21T04:36:51Z",
    "gh1186 2026-11-21T10:09:24Z",
)
CLEAN = ("gh1197", "gh1192", "gh905", "gh1146", "gh1132")
NONE = "none"
ROWS = (  # finding, case, command, result
    (FINDINGS[0], "#873/#876, herdr-spawn", NONE, "not replayable: names no test commit"),
    (
        FINDINGS[1],
        "d8e59dec, #990",
        f"{SEAM} 990 rule 'check-evals --export' --before d8e59dec",
        "caught",
    ),
    (FINDINGS[2], "#987", NONE, "not replayable: names no test commit"),
    (
        FINDINGS[3],
        "f7562acc, #1097",
        f"{SEAM} 1097 rule 'octo-feather-lane fields' --before f7562acc",
        "caught",
    ),
    (
        FINDINGS[4],
        "c7b3d148, #1013",
        f"{SEAM} 1013 rule tests/results-on-wake.sh --before c7b3d148",
        "caught",
    ),
    (
        FINDINGS[5],
        "f131433b, #1013",
        f"{SEAM} 1013 rule tests/results-on-wake.sh --before f131433b",
        "caught",
    ),
    (FINDINGS[6], "#466/#640", NONE, "not replayable: names no test commit"),
    (FINDINGS[7], "#992", NONE, "not replayable: names no seam"),
    (
        FINDINGS[8],
        "56ef30a8, #1090",
        f"{SEAM} 1090 quality#acceptance-qa-analyst 'eval_grading summarize' --before 56ef30a8",
        "caught",
    ),
    (
        FINDINGS[9],
        "4a4ad833, #1099",
        (
            f"{SEAM} 1099 issue-lifecycle#acceptance-tracer-tickets 'octo-feather-lane tickets' "
            "--before 4a4ad833"
        ),
        "caught",
    ),
    (
        FINDINGS[10],
        "80d6eb57, #1182",
        f"{SEAM} 1182 quality#acceptance-test-cpu-budget 'just test' --before 80d6eb57",
        "caught",
    ),
    (
        FINDINGS[11],
        "646363b8, #1210",
        f"{SEAM} 1210 quality#acceptance-fast-slot-free 'just check' --before 646363b8",
        "caught",
    ),
    (
        FINDINGS[12],
        "646363b8, #1210",
        f"{SEAM} 1210 quality#acceptance-fast-slot-free 'just test' --before 646363b8",
        "caught",
    ),
    (
        "clean gh1197",
        "385b4b03, #1199",
        f"{SEAM} 1199 quality#acceptance-gate-time-targets octo-feather-qa --before 385b4b03",
        "pass",
    ),
    (
        "clean gh1192",
        "032dc73e, #1193",
        f"{SEAM} 1193 quality#acceptance-fast-affected verify-octo-feather --before 032dc73e",
        "caught",
    ),
    (
        "clean gh905",
        "74f0f749, #1155",
        (
            f"{SEAM} 1155 issue-lifecycle#acceptance-lane-start 'octo-feather-lane start' "
            "--before 74f0f749"
        ),
        "pass",
    ),
    (
        "clean gh1146",
        "8f368cc1, #1147",
        f"{SEAM} 1147 issue-lifecycle#acceptance-pr-tracks merge_ask.check --before 8f368cc1",
        "pass",
    ),
    (
        "clean gh1132",
        "cd1cee50, #1140",
        f"{SEAM} 1140 issue-lifecycle#acceptance-stale-agents herdr-spawn --before cd1cee50",
        "pass",
    ),
)


# A Replay section holding what is no row as GitHub renders it: an example table in a fence and
# one in a comment, each naming a finding; then the table: FINDINGS[2]'s row, an escaped pipe in
# its result cell, and clean gh1197's row with two cells of four.
EXAMPLES = f"""
## Replay

```
| finding | case | command | result |
|---|---|---|---|
| {FINDINGS[0]} | #873 | `bash -c true` | pass |
```

<!--
| finding | case | command | result |
|---|---|---|---|
| {FINDINGS[1]} | #990 | `bash -c true` | pass |
-->

| finding | case | command | result |
|---|---|---|---|
| {FINDINGS[2]} | #987 | none | not replayable: names no test commit \\| no seam |
| clean gh1197 | 385b4b03 |
"""


def table(rows: tuple[tuple[str, str, str, str], ...]) -> str:
    """The `## Replay` section holding ROWS."""
    lines = [
        f"| {f} | {c} | {'`' + cmd + '`' if cmd != NONE else NONE} | {r} |" for f, c, cmd, r in rows
    ]
    return "\n## Replay\n\n| finding | case | command | result |\n|---|---|---|---|\n" + "\n".join(
        [*lines, ""]
    )


class Correction(Lane):
    """Lane with its verdict rounds 2 and 3 posted (round 2's two Check lines), the archived lanes
    in the state dir unless LANES is False, origin and gh's repository REPO."""

    def __init__(self, s: Scratch, *, lanes: bool = True) -> None:
        super().__init__(s)
        if lanes:
            shutil.copytree(
                FIXTURES / "correction-replay" / "lanes", s.root / "xdg" / "octo-feather" / "lanes"
            )
        # the sandbox's mise check finds the box's installs, as tests/gate/kit/qc_gh.py's box does
        s.env |= {f"MISE_{d.upper()}_DIR": mise_dir(d) for d in ("data", "cache", "config")}
        s.gh.store("repo.json", {"nameWithOwner": REPO})
        s.gh.store(f"api/repos/{REPO}.json", {"nameWithOwner": REPO, "name": "octo-feather"})
        s.gh.store(f"pr/{PR}.diff", "")
        origin = f"https://github.com/{REPO}.git"
        s.run(["git", "-C", str(self.r), "remote", "add", "origin", origin])
        self.pr()
        self.url = self.verdict(R2, "round2", "6eaf8c7b..ffba6ee7").out
        self.verdict(R3, "round3", "ffba6ee7..2dc6f718")

    def recorded(self) -> None:
        """#1121 and the rows' tickets as GitHub answered (each request up to 8 times), each also
        stored as GitHub's issue of REPO, which the snapshot reads (`gh issue view N -R REPO`)."""
        recs = tape("correction-replay-1216")
        self.s.gh.store("recorded.json", recs * 8)
        for rec in recs:
            if m := re.fullmatch(r"issue view (\d+) --json \S+", rec["request"]):
                issue = valid(rec["out"], ISSUE, rec["request"])
                self.s.gh.store(f"repos/{REPO}/issue/{m[1]}.json", issue)

    def trigger(self) -> None:
        """#1121 marked, quoting no finding line: its view, in both stores, and its notes."""
        url = f"https://github.com/{REPO}/issues/1121"
        issue = {"number": 1121, "title": TRIGGER, "body": "Class: unlisted-test-seam\n"}
        issue |= {"state": "OPEN", "url": url, "updatedAt": "2026-11-21T00:00:00Z"}
        self.s.gh.store("issue/1121.json", issue)
        self.s.gh.store(f"repos/{REPO}/issue/1121.json", issue)
        notes: dict[str, object] = {
            "url": url,
            "createdAt": "2026-11-19T21:26:32Z",
            "lastEditedAt": None,
            "body": issue["body"],
            "comments": {"pageInfo": {"hasNextPage": False}, "nodes": []},
        }
        owner, name = REPO.split("/")
        query = NOTES.read_text().rstrip("\n")
        ask = f"api graphql -F n=1121 -f owner={owner} -f name={name} -f query={query}"
        answer = json.dumps({"data": {"repository": {"issue": notes}}}, separators=(",", ":"))
        rec = {"request": ask, "out": answer, "err": "", "exit": 0, "source": "built"}
        self.s.gh.store("recorded.json", [rec] * 8)

    def section(self, more: str = "") -> None:
        """The PR body's merge ask naming the verdict comment, MORE after it."""
        self.keep_body(self.url, more)


def missing(s: Scratch) -> None:
    """issue-lifecycle#acceptance-correction-replay-missing: PR #1216 with its parent unmarked
    passes with no Replay line (a non-correction lane); with #1121 as recorded and no `## Replay`,
    merge-ask refuses naming each of its 13 findings and each lane of the clean sample, and only
    those."""
    ln = Correction(s)
    ln.section()
    r = ln.ask()
    assert "Replay:" not in r.out + r.err, f"a non-correction lane is shown a replay: {r.out}"
    ln.recorded()
    r = ln.ask(want=1)
    assert (
        "  - Replay: no `## Replay` section; #1121 is a correction lane (unlisted-test-seam)"
        in r.err
    ), r.err
    named = [x for x in r.err.splitlines() if x.startswith("  - Replay: no row for ")]
    assert named == [
        *(f"  - Replay: no row for finding `{f}`" for f in FINDINGS),
        *(f"  - Replay: no row for clean lane `clean {lane}`" for lane in CLEAN),
    ], r.err


def read(s: Scratch) -> None:
    """issue-lifecycle#acceptance-correction-replay-missing, the PR body and the parent read as
    their sources give them: the Replay section as GitHub renders it (EXAMPLES), so the refusal
    names every finding and clean lane but FINDINGS[2], whose row holds an escaped pipe, and
    clean gh1197's row by its empty fields; #1121's notes with a null body refused, the field
    named."""
    ln = Correction(s)
    ln.recorded()
    ln.section(EXAMPLES)  # the section read as GitHub renders it
    err = ln.ask(want=1).err.splitlines()
    named = [x for x in err if x.startswith("  - Replay: no row for ")]
    assert named == [
        *(f"  - Replay: no row for finding `{f}`" for f in FINDINGS if f != FINDINGS[2]),
        *(f"  - Replay: no row for clean lane `clean {lane}`" for lane in CLEAN),
    ], err  # a fenced or commented example is no row; the escaped pipe kept its row whole
    rows = [x for x in err if x.startswith("  - Replay: row ")]
    want = (
        "  - Replay: row `clean gh1197`: command, result empty; a row is "
        "`| finding | case | command | result |`"
    )
    assert rows == [want], err
    recs = tape("correction-replay-1216")  # #1121's body as GitHub would never give it: null
    for rec in recs:
        if rec["request"].startswith("api graphql -F n=1121 "):
            answer = cast("dict[str, Any]", valid(rec["out"], COMMENTS, rec["request"]))
            answer["data"]["repository"]["issue"]["body"] = None
            rec["out"] = json.dumps(answer)
    s.gh.store("recorded.json", recs * 8)
    err = ln.ask(want=1).err.splitlines()
    want = (
        "  - Replay: cannot read correction lane facts for #1121 (issue-view 1121 --notes "
        "answered no valid JSON: notes.0.body: None is not of type 'string'); fix it, then rerun"
    )
    assert [x for x in err if x.startswith("  - Replay:")] == [want], err


def shown(s: Scratch) -> None:
    """issue-lifecycle#acceptance-correction-replay-shown: with a row per finding and per clean
    lane, merge-ask reruns each row at the head and passes, printing what the runs showed: nine
    findings caught of 13, four not replayable, clean gh1192 refused of five."""
    ln = Correction(s)
    ln.recorded()
    ln.section(table(ROWS))
    out = ln.ask().out
    want = "\nReplay: caught 9 of 13 (4 not replayable); false refusals 1 of 5 clean\n"
    assert want in out, out
    said = out.split(want, 1)[1].split("\n\n", 1)[0].splitlines()
    for (finding, _, cmd, result), line in zip(ROWS, said, strict=True):
        ran = f"- `{finding}`: {result}, sandboxed run exited {0 if result == 'pass' else 1}"
        assert line.startswith(ran if cmd != NONE else f"- `{finding}`: {result} ("), line


def untrue(s: Scratch) -> None:
    """issue-lifecycle#acceptance-correction-replay-shown: merge-ask refuses a row whose claim
    differs from its own run (three rows given, the rest missing), naming the run's exit and the
    end of its output, and a row whose program is on no verdict Check line, never running it."""
    ln = Correction(s)
    ln.recorded()
    rows = (
        (FINDINGS[1], ROWS[1][1], ROWS[1][2], "missed"),
        ("clean gh1192", ROWS[14][1], ROWS[14][2], "pass"),
        ("clean gh905", "74f0f749", f"bash -c 'touch {s.root}/ran'", "pass"),
    )
    ln.section(table(rows))
    err = ln.ask(want=1).err
    gaps = [x for x in err.splitlines() if x.startswith("  - Replay: row ")]
    assert len(gaps) == len(rows), err  # one per row, each refused
    for who, claim, tail in (
        (FINDINGS[1], "missed", "fix: post `Seam: rule: `check-evals --export`` on 990 with the"),
        (
            "clean gh1192",
            "pass",
            "fix: post `Seam: quality#acceptance-fast-affected: `verify-octo-feather`` on 1193",
        ),
    ):
        head = f"  - Replay: row `{who}` claims {claim} (exit 0); its run at {R3[:12]} exited 1: "
        line = next((x for x in gaps if x.startswith(head)), "")
        assert line, f"{who}: no refusal naming its run: {err}"
        assert tail in line, f"{who}: the run's output tail: {line}"
    want = (
        f"  - Replay: row `clean gh905` runs `bash -c 'touch {s.root}/ran'`, whose program is no "
        "path on a verdict Check line (scripts/octo-feather-lane): replay the lane's own check"
    )
    assert want in gaps, err
    assert not (s.root / "ran").exists(), "a row off the Check lines ran"


def contained(s: Scratch) -> None:
    """issue-lifecycle#acceptance-correction-replay-missing and -shown, the trigger case and the
    director's proof 2: with no `## Replay`, merge-ask refuses naming the one `trigger` row. Given
    two rows that write, it passes, each run contained: `octo-feather-lane done 1121` (a tracker
    write) is shown not replayable, the offline gh refusing its close, and GitHub (the fake gh's
    store and call log) shows #1121 open, no write made; a row writing a file in the lane
    worktree and one in $HOME is shown with its discarded write, and neither file exists after."""
    ln = Correction(s, lanes=False)
    ln.trigger()
    ln.section()
    err = ln.ask(want=1).err
    want = "  - Replay: no row for finding `trigger` (the issue lists no finding)"
    assert want in err.splitlines(), err
    before = (s.gh.dir / f"repos/{REPO}/issue/1121.json").read_text()
    writes = 'scripts/octo-feather-lane --help > leak; echo x > "$HOME/leak"; exit 0'
    rows = (
        ("trigger", "#1121", "scripts/octo-feather-lane done 1121", "caught"),
        ("trigger", "#1121", writes, "pass"),
    )
    ln.section(table(rows))
    calls = len(s.gh.log())  # the scenario's own verdict posts before it
    out = ln.ask().out
    want = "\nReplay: caught 0 of 1 (0 not replayable); false refusals 0 of 0 clean\n"
    assert want in out, out
    said = out.split(want, 1)[1].split("\n\n", 1)[0].splitlines()
    assert said[0].startswith("- `trigger`: not replayable: gh issue close 1121"), said
    assert "offline gh refused" in said[0], said
    assert said[1] == "- `trigger`: pass, sandboxed run exited 0; 1 writes discarded: new leak", (
        said
    )
    closes = [x for x in s.gh.log()[calls:] if x.startswith(("issue close", "api -X"))]
    assert closes == [], f"GitHub got a write: {closes}"
    assert (s.gh.dir / f"repos/{REPO}/issue/1121.json").read_text() == before, "#1121 changed"
    assert (s.gh.dir / "issue/1121.json").read_text() == before, "#1121 changed"
    left = [p for p in (ln.r / "leak", s.home / "leak") if p.exists()]
    assert left == [], f"a row's write persists: {left}"


def masked(s: Scratch) -> None:
    """issue-lifecycle#acceptance-correction-replay-shown, a read the sandbox masks (#1241): Pi's
    sessions, which the box holds (one session here), are masked in every row's sandbox, so
    `octo-feather-lane report`, whose skill reach reads them, finds none there and exits 0. Its
    rows, one claiming caught and one pass, are each shown not replayable, naming the masked read
    from the sandbox's attempt record; neither is refused as untrue nor counted as a run."""
    ln = Correction(s, lanes=False)
    ln.trigger()
    s.env.pop("PI_CODING_AGENT_DIR", None)
    box = s.home / ".pi" / "agent" / "sessions" / "--w--"
    box.mkdir(parents=True)
    (box / "2026-11-23T00-00-00-000Z_s1.jsonl").write_text(
        '{"type":"session","timestamp":"2026-11-23T00:00:00.000Z"}\n'
    )
    rows = (
        ("trigger", "#1121", "scripts/octo-feather-lane report", "caught"),
        ("trigger", "#1121", "scripts/octo-feather-lane report", "pass"),
    )
    ln.section(table(rows))
    out = ln.ask().out
    want = "\nReplay: caught 0 of 1 (1 not replayable); false refusals 0 of 0 clean\n"
    assert want in out, out
    said = out.split(want, 1)[1].split("\n\n", 1)[0].splitlines()
    mask = f"open {s.home}/.pi/agent/sessions: tmpfs mask over {s.home}/.pi/agent/sessions"
    assert len(said) == len(rows), said
    for line in said:
        assert line.startswith("- `trigger`: not replayable: "), line
        assert mask in line, line


# The recorded #1233 case (#1241): PR #1233 (lane gh1228, parent #1228), the change to the skills
# check that #1228's 17 send-back items asked for.
PR_1233 = 1233
HEAD_1233 = "0b665281fec8d1aa37e80ad960a58a2dee687b03"
MAIN_1233 = "30086cb1"  # #1233's base on main (its merge-base)
VERDICT_1233 = "https://github.com/0xTomDaniel/octo-feather/pull/1233#issuecomment-7085862927"
MARKED_1228 = "[correction-lane skill-not-loaded] "
MASKED = "not replayable: Pi sessions are masked in the qc sandbox"
LIVE = "; lane gh1075's hand-off log is live, masked too"
STATUS_1233 = "docs/specs/issue-lifecycle.status.json"
CLEAN_1233 = ("gh1227", "gh1074", "gh905", "gh1146", "gh1132")


class Recorded1233:
    """PR #1233 offline as recorded: the scratch repo R at its head 0b665281 (the kit's own
    commits through git alternates, origin/main at its base 30086cb1, the full gate pass recorded
    there), the PR in the fake gh with its body and its verdict comment verbatim
    (tests/fixtures/correction-replay-1233/pr-body.md, verdict.md: two Check lines on
    scripts/octo-feather-lane), its checks passing; #1228 as GitHub answered issue-view 1228
    --notes (testkit/recordings/correction-replay-1233.json, unmodified) but for what makes it a
    correction lane, which reflect never filed it as: its title marker, and one comment quoting the
    17 send-back items as reflect quotes finding lines (findings.jsonl: each line verbatim from
    its lane's hand-off log, gh1075 live, the rest archived). The 17 items are 10 finding ids:
    a ticket's misses share one write, so one `at`. The state dir's archived lanes
    (lanes/archive: each record verbatim, each log cut to its finding lines and last line) give
    the clean sample gh1227, gh1074, gh905, gh1146, gh1132; gh1121, gh1197 and gh1192 hold the
    class, gh706 is the sixth, gh1228 ended after #1233's first commit."""

    def __init__(self, s: Scratch) -> None:
        self.s, self.r = s, s.root / "repo"
        s.env.pop("HERDR_SESSION", None)
        s.env["XDG_STATE_HOME"] = str(s.root / "xdg")
        s.prepare("correction-replay-1233", Recorded1233.build)
        at = FIXTURES / "correction-replay-1233"
        shutil.copytree(at / "lanes", s.root / "xdg" / "octo-feather" / "lanes")
        s.gh.store("repo.json", {"nameWithOwner": REPO})
        s.gh.store(f"pr/{PR_1233}.diff", "")
        lines = (at / "findings.jsonl").read_text().splitlines()
        self.items = [cast("Item", valid(x, FINDING_ITEM, "findings.jsonl")) for x in lines]
        recs = tape("correction-replay-1233")
        quotes = "".join(
            f"- {i['lane']} {i['line']['at']} {i['line']['source']}: {i['line']['summary']}\n"
            for i in self.items
        )
        note = {
            "url": f"https://github.com/{REPO}/issues/1228#issuecomment-recorded-1241",
            "createdAt": "2026-11-23T00:00:00Z",
            "lastEditedAt": None,
            "body": "Recorded for #1241, not on GitHub: #1228 is not reflect-filed; the 17 "
            "send-back items its comment and REPORT.md section 2 count, quoted as reflect quotes "
            "finding lines:\n\n" + quotes,
        }
        for rec in recs:
            if rec["request"].startswith("issue view"):
                issue = cast("Issue", valid(rec["out"], ISSUE, rec["request"]))
                issue["title"] = MARKED_1228 + issue["title"]
                rec["out"] = json.dumps(issue)
            else:
                # COMMENTS holds the path to the nodes; the rest of GitHub's answer kept as is
                answer = cast("dict[str, Any]", valid(rec["out"], COMMENTS, rec["request"]))
                answer["data"]["repository"]["issue"]["comments"]["nodes"].append(note)
                rec["out"] = json.dumps(answer)
            rec["source"] += "; built for #1241: title marker, the quoting comment"
        s.gh.store("recorded.json", recs * 4)
        self.body = fixture("correction-replay-1233/pr-body.md")
        self.pr: dict[str, object] = {
            "number": PR_1233,
            "baseRefName": "main",
            "headRefName": "gh1228",
            "headRefOid": HEAD_1233,
            "body": self.body,
            "statusCheckRollup": [
                {
                    "__typename": "CheckRun",
                    "name": n,
                    "status": "COMPLETED",
                    "conclusion": "SUCCESS",
                }
                for n in ("scope", "check")
            ],
            "comments": [
                {"url": VERDICT_1233, "body": fixture("correction-replay-1233/verdict.md")}
            ],
        }
        s.gh.put(PR_1233, self.pr)

    @staticmethod
    def build(s: Scratch) -> None:
        r = s.root / "repo"
        r.mkdir()
        common = ["git", "-C", str(ROOT), "rev-parse", "--path-format=absolute", "--git-common-dir"]
        s.run(["git", "init", "-q", "-b", "gh1228", str(r)])
        (r / ".git" / "objects" / "info" / "alternates").write_text(
            s.run(common).out + "/objects\n"
        )
        for k, v in (
            ("user.email", "t@example.com"),
            ("user.name", "t"),
            ("commit.gpgsign", "false"),
        ):
            s.run(["git", "-C", str(r), "config", k, v])
        s.run(["git", "-C", str(r), "remote", "add", "origin", f"https://github.com/{REPO}.git"])
        main_sha = s.run(["git", "-C", str(r), "rev-parse", MAIN_1233]).out
        s.run(["git", "-C", str(r), "update-ref", "refs/remotes/origin/main", main_sha])
        s.run(["git", "-C", str(r), "reset", "-q", "--hard", HEAD_1233])
        s.run([G, "record", "--reason", "lane final head", "--seconds", "1"], cwd=r)

    def rows(self) -> tuple[tuple[str, str, str, str], ...]:
        """One row per send-back item, each declared not replayable, and one per clean lane."""
        items = tuple(
            (
                f"{i['lane']} {i['line']['at']}",
                f"#{i['line']['ticket']} {i['line']['skill']}",
                NONE,
                MASKED + (LIVE if i["lane"] == "gh1075" else ""),
            )
            for i in self.items
        )
        return items + tuple((f"clean {x}", f"lane {x}", NONE, MASKED) for x in CLEAN_1233)

    def ask(self, more: str = "", want: int = 0) -> Ran:
        self.s.gh.put(PR_1233, self.pr | {"body": self.body + more})
        cmd = [L, "merge-ask", str(PR_1233), "--base", "origin/main", "--status", STATUS_1233]
        return self.s.run(cmd, want=want, cwd=self.r)


def recorded_1233(s: Scratch) -> None:
    """issue-lifecycle#acceptance-correction-replay-missing and -shown, the recorded #1233 case:
    with no `## Replay` merge-ask refuses naming each of #1228's 10 finding ids (its 17 items)
    and each clean lane; with a row per item, each declaring the read the qc sandbox masks (the
    worker's Pi session; gh1075's live log), and a row per clean lane, it passes printing
    caught 0 of 10, all 10 not replayable, each row with its reason. The replay done outside
    merge-ask, at each finding's time: /home/exedev/scratch/gh1228-replay/TABLE.md section 1."""
    ln = Recorded1233(s)
    err = ln.ask(want=1).err
    ids = list(dict.fromkeys(f"{i['lane']} {i['line']['at']}" for i in ln.items))
    assert len(ln.items) == 17, ln.items
    assert len(ids) == 10, ids
    named = [x for x in err.splitlines() if x.startswith("  - Replay: no row for ")]
    assert named == [
        *(f"  - Replay: no row for finding `{f}`" for f in ids),
        *(f"  - Replay: no row for clean lane `clean {x}`" for x in CLEAN_1233),
    ], err
    rows = ln.rows()
    out = ln.ask(table(rows)).out
    want = "\nReplay: caught 0 of 10 (10 not replayable); false refusals 0 of 0 clean\n"
    assert want in out, out
    said = out.split(want, 1)[1].split("\n\n", 1)[0].splitlines()
    assert said == [f"- `{f}`: {r} (as the row says; not run)" for f, _, _, r in rows], said


if __name__ == "__main__":
    main(missing, read, shown, untrue, contained, masked, recorded_1233)
