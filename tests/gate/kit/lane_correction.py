"""The scenarios of tests/gate/kit/test_lane_correction.py (its items), this file their command
(testkit.main): the correction lanes the reflection files (spec comms #reflection-correction,
#acceptance-reflect-files-correction; issue-lifecycle #lanes-correction,
#acceptance-reflection-missed-lane, #acceptance-writer-route-lane): scripts/octo-feather-lane
archive and reflect --director run as commands, the real scripts/pi-role starting
agents/reflector.md under the testkit's Pi stand-in (testkit/pi_agent.py, print mode: the reply
each case records), and the testkit's fake gh under the real github-issues scripts; nothing
reaches GitHub. Each case against the rule as issue-lifecycle #lanes-correction owns it (what
counts, when a class is due, refiling, reflection-missed, owner-caught), and comms
#reflection-correction (where it files, what it quotes)."""

from __future__ import annotations

import json
import re

from testkit import Scratch, kit, main, reflector
from testkit.gh_recordings import recording_run

KIT_REPO = "0xTomDaniel/octo-feather"


def cr(at: str, cls: str, summary: str) -> str:
    """A blocking code-review finding line."""
    d = {"at": at, "kind": "finding", "source": "code-review", "class": cls, "blocking": True}
    return json.dumps(d | {"summary": summary}, separators=(",", ":"))


LIST = (
    'issue list --repo {} --state all --limit 1000 --search "correction-lane" in:title --json '
    "number,title,state,closedAt"
)
# The number GitHub gives the next issue of each repo (its own sequence, per repo).
FIRST = {"o/t": 901, KIT_REPO: 704}


def create_request(repo: str, title: str) -> str:
    return f"GH_REPO={repo} issue create --title {title} --body-file -"


class Corr:
    """A scratch state and tracker: lanes on target o/t, the reflector's replies recorded. GitHub
    is the testkit gh's recordings, armed before each command (arm): each repo's correction-lane
    issue search answers what that repo holds then (`held`, the scenario's record of it), a new
    issue in it the next number of its own sequence; what the command sent is read back from the
    gh's requests (issues)."""

    def __init__(self, s: Scratch) -> None:
        self.s = s
        for k in ("HERDR_PANE_ID", "PI_SESSION_FILE", "OCTO_FEATHER_REFLECT_ARGS", "GH_REPO"):
            s.env.pop(k, None)
        s.env |= {"XDG_STATE_HOME": str(s.root / "state"), "HERDR_SESSION": ""}
        self.says: dict[str, tuple[str, ...]] = {"lane": (), "director": ()}
        self.lanes = s.root / "state" / "octo-feather" / "lanes"
        self.dlog = self.lanes.parent / "director.handoffs.jsonl"
        (self.lanes / "archive").mkdir(parents=True)
        self.dlog.write_text("")
        self.held: dict[str, list[dict[str, object]]] = {r: [] for r in FIRST}
        self.next = dict(FIRST)
        self.filed: dict[int, dict[str, object]] = {}
        self.seen = 0  # requests read so far
        self.none()

    def reply(self, who: str, *findings: str) -> None:
        """The reflector's reply for WHO (lane, director): FINDINGS, or none (testkit.reflector)."""
        self.says[who] = findings
        reflector(self.s, self.says["lane"], self.says["director"])

    def none(self) -> None:
        self.says = {"lane": (), "director": ()}
        reflector(self.s)

    def lane(self, name: str, *lines: str, archived: bool = False) -> None:
        """An open (or ARCHIVED) lane on target o/t, its log LINES."""
        d = self.lanes / "archive" if archived else self.lanes
        (d / f"{name}.toml").write_text(
            f'issue = "{name}"\nrepository = "o/t"\nsupervisor = "w9:p2"\ngoal = "scratch"\n'
        )
        (d / f"{name}.handoffs.jsonl").write_text("".join(x + "\n" for x in lines))

    def arm(self, creates: tuple[tuple[str, str], ...] = ()) -> None:
        """Exact search and create requests expected in the next command."""
        tapes: dict[str, list[object]] = {}
        for repo, held in self.held.items():
            tapes[LIST.format(repo)] = [json.dumps(held) + "\n"]
        for repo, title in creates:
            tapes[create_request(repo, title)] = [
                f"https://github.com/{repo}/issues/{self.next[repo]}\n"
            ]
        self.s.gh.tape(tapes)

    def lane_cmd(
        self,
        *args: str,
        creates: tuple[tuple[str, str], ...] = (),
        missed: bool = False,
        searches: int = 1,
    ) -> str:
        """octo-feather-lane ARGS; each issue it filed (its create request, answered the repo's
        next number) recorded in `filed` and held by its repo from then on."""
        self.arm(creates)
        if searches != 1:
            tape_file = self.s.gh.dir / "tape.json"
            tape = json.loads(tape_file.read_text())
            tape[LIST.format("o/t")] *= searches
            tape_file.write_text(json.dumps(tape))
        expected_creates = [create_request(repo, title) for repo, title in creates]
        cmd = [kit("octo-feather-lane"), *args]
        if missed:

            def arm_missed() -> None:
                tape = json.loads((self.s.gh.dir / "tape.json").read_text())
                for repo, path, tag in (
                    ("o/t", self.lanes / "gh6.handoffs.jsonl", "fe02d601"),
                    (KIT_REPO, self.dlog, "d91e4c73"),
                ):
                    findings = [json.loads(x) for x in path.read_text().splitlines()]
                    at = next(
                        (d["at"] for d in findings if d.get("class") == "reflection-missed"), None
                    )
                    if at is None:
                        continue
                    title = (
                        f"[correction-lane reflection-missed {at} {tag}] "
                        "change the question list: reflection-missed"
                    )
                    request = create_request(repo, title)
                    if request not in expected_creates:
                        expected_creates.append(request)
                    tape[request] = [f"https://github.com/{repo}/issues/{self.next[repo]}\n"]
                (self.s.gh.dir / "tape.json").write_text(json.dumps(tape))

            tape_file = self.s.gh.dir / "tape.json"
            tape = json.loads(tape_file.read_text())
            tape[LIST.format("o/t")].append(
                json.dumps(self.held["o/t"]) + "\n"
            )  # gh5 and gh6 owners
            tape_file.write_text(json.dumps(tape))
            r = recording_run(self.s, cmd, (LIST.format("o/t"), LIST.format(KIT_REPO)), arm_missed)
        else:
            r = self.s.run(cmd)
        log = (self.s.gh.dir / "requests.jsonl").read_text().splitlines()
        sent = [json.loads(line) for line in log[self.seen :]]
        assert [
            r["request"] for r in sent if " issue create " in r["request"]
        ] == expected_creates, sent
        if missed:
            assert [r["request"] for r in sent] == [
                LIST.format("o/t"),
                LIST.format("o/t"),
                expected_creates[0],
                LIST.format(KIT_REPO),
                expected_creates[1],
            ], sent
        for req in sent:
            m = re.fullmatch(
                r"GH_REPO=(\S+) issue create --title (.*) --body-file -", req["request"]
            )
            if not m:
                continue
            repo, n = m.group(1), self.next[m.group(1)]
            self.next[repo] = n + 1
            d: dict[str, object] = {"number": n, "title": m.group(2), "state": "OPEN"}
            d["closedAt"] = None
            self.held[repo].append(d)
            self.filed[n] = d | {"repo": repo, "body": req["body"]}
        self.seen = len(log)
        return (r.out + ("\n" + r.err if r.err else "")).strip("\n")

    def issues(self) -> dict[int, dict[str, object]]:
        """Every issue filed, by number: its repo, title and body as sent."""
        return self.filed

    def close(self, n: int, at: str) -> None:
        """Issue N closed on GitHub at AT, as its repo's search answers from then on."""
        for held in self.held.values():
            for d in held:
                if d["number"] == n:
                    d |= {"state": "CLOSED", "closedAt": at}


def filed(out: str, n: int, repo: str, cls: str, rest: str = "") -> None:
    want = re.escape(f"correction lane: filed {n} in github-issues {repo} for {cls}") + rest
    assert re.search("^" + want, out, re.MULTILINE), f"not filed {n} {cls}: {out}"


def none_filed(c: Corr, out: str, n: int) -> None:
    assert len(c.issues()) == n, f"filed again: {out} {c.issues()}"
    assert "correction lanes: none filed" in out.split("\n"), f"filed again: {out}"


def lifecycle(s: Scratch) -> None:
    """acceptance-reflect-files-correction, -writer-route-lane: gh1 (archived) logged one dup-rule,
    gh2's review the second, the director routes it: archive gh2 files 901 in o/t quoting both
    and the route, key printed. Its issue open: a third finding files nothing; closed after the
    class's latest finding: nothing; closed before a newer finding: files 902. acceptance-
    reflection-missed -lane: a lane reflection-missed finding files at once in the target (903),
    a director one in the kit's repo (its own sequence: 704), each naming the question list;
    owner-caught classes twice in the director log file nothing; the director reflection alone,
    no new finding, refiles nothing."""
    c = Corr(s)
    c.lane(
        "gh1", cr("2026-10-20T00:00:00Z", "dup-rule", "gh1 restated the merge rule"), archived=True
    )
    c.lane("gh2", cr("2026-10-21T00:00:00Z", "dup-rule", "gh2 restated the gate rule"))
    route = "Finding: class: dup-rule | question: writer-route | route: agents/implementer.md Rules"
    c.reply("director", route + " | summary: 2 code-review findings in gh1, gh2")
    out = c.lane_cmd(
        "archive",
        "gh2",
        creates=(("o/t", "[correction-lane dup-rule] repeated finding class: dup-rule"),),
    )
    filed(
        out,
        901,
        "o/t",
        "dup-rule",
        re.escape(" (2 findings; route: agents/implementer.md Rules)") + "$",
    )
    assert (c.lanes / "archive" / "gh2.toml").is_file(), f"gh2 not archived: {out}"
    (i,) = c.issues().values()
    assert i["repo"] == "o/t", i
    assert "[correction-lane dup-rule]" in str(i["title"]), i
    for want in (
        "Class: dup-rule",
        "Route: agents/implementer.md Rules",
        "gh1 restated the merge rule",
        "gh2 restated the gate rule",
    ):
        assert want in str(i["body"]), (want, i["body"])
    assert "question list" not in str(i["body"]), i["body"]
    c.lane("gh3", cr("2026-10-22T00:00:00Z", "dup-rule", "gh3 again"))
    c.none()
    none_filed(c, c.lane_cmd("archive", "gh3"), 1)
    c.close(901, "2099-01-01T00:00:00Z")
    c.lane("gh4", cr("2026-10-23T00:00:00Z", "dup-rule", "gh4 again"))
    out = c.lane_cmd("archive", "gh4")
    assert len(c.issues()) == 1, f"closed after the latest finding: filed again: {out}"
    c.close(901, "2026-10-23T12:00:00Z")
    c.lane("gh5", cr("2026-10-24T00:00:00Z", "dup-rule", "gh5 after the close"))
    filed(
        c.lane_cmd(
            "archive",
            "gh5",
            creates=(("o/t", "[correction-lane dup-rule] repeated finding class: dup-rule"),),
        ),
        902,
        "o/t",
        "dup-rule",
    )
    with c.dlog.open("a") as f:
        for at, x in (("2026-10-25T00:00:00Z", "a"), ("2026-10-25T01:00:00Z", "b")):
            f.write(
                f'{{"at":"{at}","kind":"finding","class":"owner-caught-stale-pr","summary":"{x}"}}\n'
            )
    c.lane("gh6")
    c.reply(
        "lane",
        "Finding: class: reflection-missed | question: reflection-missed | route: "
        "reflection/questions.json undetected-rule | summary: gh1 reflection found no gap; gh6 "
        "review found the rule broken; reword undetected-rule",
    )
    c.reply(
        "director",
        "Finding: class: reflection-missed | question: director-reflection-missed | route: "
        "reflection/questions.json owner-asked | summary: owner caught a stale PR after the last "
        "reflection; add a stale-PR question",
    )
    out = c.lane_cmd("archive", "gh6", missed=True)
    filed(out, 903, "o/t", "reflection-missed ")
    filed(out, 704, KIT_REPO, "reflection-missed ")
    by = c.issues()
    assert len(by) == 4, by.keys()
    for n, quote in ((903, "reword undetected-rule"), (704, "add a stale-PR question")):
        assert "[correction-lane reflection-missed " in str(by[n]["title"]), by[n]
        assert "Changes: the question list, reflection/questions.json" in str(by[n]["body"]), by[n]
        assert quote in str(by[n]["body"]), by[n]
    assert not any("owner-caught" in str(i["title"]) for i in by.values()), by
    assert [by[n]["repo"] for n in (901, 902, 903, 704)] == ["o/t", "o/t", "o/t", KIT_REPO], by
    c.none()
    none_filed(c, c.lane_cmd("reflect", "--director", searches=2), 4)


def other_lane(s: Scratch) -> None:
    """Every due subject files, whichever lane's reflection runs: archived gh1 and gh2 hold one
    dup-rule finding each; the archive of unrelated gh3 files the class in gh1/gh2's target
    quoting both, no route given; a further archive files nothing."""
    c = Corr(s)
    c.lane(
        "gh1", cr("2026-10-20T00:00:00Z", "dup-rule", "gh1 restated the merge rule"), archived=True
    )
    c.lane(
        "gh2", cr("2026-10-21T00:00:00Z", "dup-rule", "gh2 restated the gate rule"), archived=True
    )
    c.lane("gh3")
    out = c.lane_cmd(
        "archive",
        "gh3",
        creates=(("o/t", "[correction-lane dup-rule] repeated finding class: dup-rule"),),
    )
    filed(
        out,
        901,
        "o/t",
        "dup-rule",
        re.escape(" (2 findings; route: none given by a reflection)") + "$",
    )
    assert (c.lanes / "archive" / "gh3.toml").is_file(), f"gh3 not archived: {out}"
    (i,) = c.issues().values()
    assert i["repo"] == "o/t", i
    assert "[correction-lane dup-rule]" in str(i["title"]), i
    for want in ("gh1 restated the merge rule", "gh2 restated the gate rule"):
        assert want in str(i["body"]), (want, i["body"])
    c.lane("gh4")
    none_filed(c, c.lane_cmd("archive", "gh4"), 1)


def routed(s: Scratch) -> None:
    """acceptance-writer-route-lane through reflect --director: the class's findings in lanes, the
    director routes it: filed in the lanes' target naming the route."""
    c = Corr(s)
    c.lane(
        "gh1",
        cr("2026-10-20T00:00:00Z", "stale-check", "gh1 check missed a stale doc"),
        archived=True,
    )
    c.lane(
        "gh2",
        cr("2026-10-21T00:00:00Z", "stale-check", "gh2 check missed a stale doc"),
        archived=True,
    )
    c.reply(
        "director",
        "Finding: class: stale-check | question: writer-route | route: agents/code-reviewer.md "
        "Rules | summary: 2 code-review findings in gh1, gh2",
    )
    out = c.lane_cmd(
        "reflect",
        "--director",
        creates=(("o/t", "[correction-lane stale-check] repeated finding class: stale-check"),),
    )
    rest = re.escape(" (2 findings; route: agents/code-reviewer.md Rules)") + "$"
    filed(out, 901, "o/t", "stale-check", rest)
    (i,) = c.issues().values()
    assert i["repo"] == "o/t", i
    assert "Route: agents/code-reviewer.md Rules" in str(i["body"]), i


def counts(s: Scratch) -> None:
    """What counts: two reflection findings of a class in two lanes, two blocking ones in one
    lane, a non-blocking review finding beside a blocking one, or the director log's: none due; a
    blocking product-judge (qc) finding counts: only `judged` filed."""
    c = Corr(s)

    def rf(at: str, cls: str, summary: str) -> str:
        d = {"at": at, "kind": "finding", "source": "reflection", "class": cls, "blocking": False}
        d |= {"question": "undetected-rule", "route": "r", "summary": summary}
        return json.dumps(d, separators=(",", ":"))

    c.lane(
        "gh1",
        rf("2026-10-20T00:00:00Z", "refl-only", "gh1 reflection"),
        cr("2026-10-20T00:00:00Z", "one-lane", "gh1 a"),
        cr("2026-10-20T01:00:00Z", "one-lane", "gh1 b"),
        cr("2026-10-20T02:00:00Z", "judged", "gh1 review"),
        archived=True,
    )
    c.lane(
        "gh2",
        rf("2026-10-21T00:00:00Z", "refl-only", "gh2 reflection"),
        '{"at":"2026-10-21T01:00:00Z","kind":"finding","source":"code-review","class":"one-lane",'
        '"blocking":false,"summary":"gh2 note"}',
        '{"at":"2026-10-21T02:00:00Z","kind":"finding","source":"qc","class":"judged",'
        '"blocking":true,"summary":"gh2 judge"}',
        archived=True,
    )
    c.dlog.write_text(
        '{"at":"2026-10-22T00:00:00Z","kind":"finding","class":"one-lane",'
        '"summary":"director saw it"}\n'
    )
    c.lane("gh3")
    out = c.lane_cmd(
        "archive",
        "gh3",
        creates=(("o/t", "[correction-lane judged] repeated finding class: judged"),),
    )
    filed(out, 901, "o/t", "judged", re.escape(" (2 findings; "))
    assert len(c.issues()) == 1, f"counts: want only judged filed: {out} {c.issues()}"


if __name__ == "__main__":
    main(lifecycle, other_lane, routed, counts)
