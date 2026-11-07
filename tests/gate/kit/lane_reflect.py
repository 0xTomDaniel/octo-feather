"""The scenarios of tests/gate/kit/test_lane_reflect.py (its items), this file their command
(testkit.main): the lane reflection at archive (spec comms #acceptance-reflect-lane,
#acceptance-reflect-before-archive, #reflection-output): scripts/octo-feather-lane archive and
reflect run as commands, the real scripts/pi-role starting agents/reflector.md, the testkit's Pi
stand-in first on PATH for the model (print mode: it records its argv and prints the reply the
case records, testkit.reflector), the testkit's herdr finding no server, its gh the tracker. The
archived hand-off log holds the lane's lines unchanged, then the finding and reflection lines of
spec comms #reflection-output; the brief names the director log's lines about the lane, the
factory report's lane lines and the transcripts; a reflector that cannot run, or replies outside
the form, refuses the archive naming the failed reflection with every file left in place."""

from __future__ import annotations

import hashlib
import json

from testkit import LANE_QUESTIONS, ROOT, Ran, Scratch, kit, main, reflector

SESSION = "0b5e7a1c-0000-4000-8000-00000000c0de"
QUESTIONS = [
    "caught-by-hand",
    "slow-or-from-memory",
    "undetected-rule",
    "check-misfired",
    "mechanical-step",
    "writer-mistake",
    "reflection-missed",
]


class Lanes:
    """A scratch state: a merged lane's record and log (a review finding, a worker spawn with its
    session transcript), the director log's stranded-worker catch about it and another lane's
    line."""

    def __init__(self, s: Scratch) -> None:
        self.s = s
        for k in ("HERDR_PANE_ID", "PI_SESSION_FILE", "OCTO_FEATHER_REFLECT_ARGS"):
            s.env.pop(k, None)
        s.env |= {"XDG_STATE_HOME": str(s.root / "state"), "HERDR_SESSION": ""}
        reflector(s)
        self.lanes = s.root / "state" / "octo-feather" / "lanes"
        self.lanes.mkdir(parents=True)
        d = s.home / ".pi" / "agent" / "sessions" / "--w--"
        d.mkdir(parents=True)
        self.tr = d / f"2026-10-28T00-00-00-000Z_{SESSION}.jsonl"
        self.tr.write_text("{}\n")
        (self.lanes.parent / "director.handoffs.jsonl").write_text(
            '{"at":"2026-10-28T00:20:00Z","kind":"note","issue":900,"text":"read pane w9:p3: '
            'implementer-gh900 stranded at a trust prompt"}\n'
            '{"at":"2026-10-28T00:21:00Z","kind":"note","issue":7,"text":"unrelated lane"}\n'
        )

    def seed(self, name: str) -> None:
        (self.lanes / f"{name}.toml").write_text(
            f'issue = "gh{name[2:]}"\nsupervisor = "w9:p2"\ngoal = "scratch"\n'
        )
        (self.lanes / f"{name}.handoffs.jsonl").write_text(
            '{"at":"2026-10-28T00:00:00Z","kind":"spawn","name":"implementer-gh900","pane":"w9:p3",'
            f'"role":"implementer","session":"{SESSION}"}}\n'
            '{"at":"2026-10-28T00:10:00Z","kind":"finding","source":"code-review","class":'
            '"duplicated-rule","blocking":true,"summary":"restated rule"}\n'
        )

    def lane(self, *args: str, want: int = 0, **env: str) -> Ran:
        return self.s.run([kit("octo-feather-lane"), *args], want=want, env=env)

    def argv(self) -> list[str]:
        """The lane reflector's last argv (the stand-in's record)."""
        return (self.s.root / "argv.lane").read_text().split("\0")


def archive_findings(s: Scratch) -> None:
    """acceptance-reflect-lane: two gaps, each a finding line (spec comms #reflection-output), then
    one reflection line, after the lane's lines unchanged; the reflector ran as
    agents/reflector.md (its model, thinking, tools, reflect skill) on a brief naming its inputs:
    the director log's line about the lane (not another lane's), the spawn's transcript, the
    lane's record and log, the question list."""
    ls = Lanes(s)
    ls.seed("gh900")
    before = (ls.lanes / "gh900.handoffs.jsonl").read_text().splitlines()
    reflector(
        s,
        lane=[
            (
                "Finding: class: stranded-worker-by-hand | question: caught-by-hand | route: "
                "agents/supervisor.md goal check-in | summary: director found implementer-gh900 "
                "stranded by reading pane w9:p3 (director log); a herdr agent get status check at "
                "the goal check-in would have caught it first"
            ),
            (
                "Finding: class: restated-rule | question: writer-mistake | route: "
                ".agents/skills/code-review | summary: review finding duplicated-rule (hand-off "
                "log line 2)"
            ),
        ],
    )
    r = ls.lane("archive", "gh900")
    out = r.out + r.err
    a = ls.lanes / "archive" / "gh900.handoffs.jsonl"
    assert a.is_file(), f"gh900 not archived: {out}"
    assert not (ls.lanes / "gh900.toml").exists(), f"gh900 not archived: {out}"
    assert not (ls.lanes / "gh900.handoffs.jsonl").exists(), f"gh900 not archived: {out}"
    assert "reflection: lane gh900, 2 findings" in out, f"no reflection summary: {out}"
    lines = a.read_text().splitlines()
    assert len(lines) == 5, lines
    assert lines[:2] == before, "lane lines changed"
    f1, f2, refl = (json.loads(x) for x in lines[2:])
    keys = {"at", "kind", "source", "class", "blocking", "question", "route", "summary"}
    for f in (f1, f2):
        assert (f["kind"], f["source"], f["blocking"]) == ("finding", "reflection", False), f
        assert set(f) == keys, f
    want1 = ("stranded-worker-by-hand", "caught-by-hand", "agents/supervisor.md goal check-in")
    assert (f1["class"], f1["question"], f1["route"]) == want1, f1
    assert "stranded by reading pane w9:p3" in f1["summary"], f1
    assert (f2["class"], f2["question"]) == ("restated-rule", "writer-mistake"), f2
    assert (refl["kind"], refl["findings"], refl["questions"]) == ("reflection", 2, QUESTIONS), refl
    argv = "\n".join(ls.argv())
    for want in (
        "openai/gpt-6.1-sol",
        "high",
        "read,grep,find,ls,codemode",
        str(ROOT / ".agents" / "skills" / "reflect"),
        "read pane w9:p3: implementer-gh900 stranded",
        f"spawn implementer-gh900 implementer w9:p3: {ls.tr}",
        "lane gh900: issue gh900",
        str(ls.lanes / "gh900.handoffs.jsonl"),
        "- caught-by-hand: What did anyone",
    ):
        assert want in argv, f"reflector argv lacks {want!r}: {argv}"
    assert "unrelated lane" not in argv, "brief quoted another lane's director line"


def reflect_alone(s: Scratch) -> None:
    """No gap: the reflection line alone, findings 0, its 7 questions; `reflect` alone appends and
    moves nothing; the supervisor's own transcript in the brief when run from its pane."""
    ls = Lanes(s)
    ls.seed("gh901")
    own = s.root / "own.jsonl"
    own.write_text("{}\n")
    ls.lane("reflect", "gh901", HERDR_PANE_ID="w9:p2", PI_SESSION_FILE=str(own))
    assert (ls.lanes / "gh901.toml").is_file(), "reflect moved the record"
    lines = (ls.lanes / "gh901.handoffs.jsonl").read_text().splitlines()
    d = json.loads(lines[-1])
    assert (d["kind"], d["findings"], len(d["questions"])) == ("reflection", 0, 7), lines[-1]
    assert len(lines) == 3, "no-gap reflection appended a finding"
    assert f"supervisor w9:p2: {own}" in "\n".join(ls.argv()), (
        "brief lacks the supervisor's own transcript"
    )


def refusals(s: Scratch) -> None:
    """acceptance-reflect-before-archive: the reflector's model unreachable (pi exits non-zero), or
    a reply outside the form (no Questions line, wrong questions, an owner-caught class, an unknown
    question, no Finding line): archive gh902 refuses, exit 1, naming the failed reflection and
    why; every file left as it was, the lane still listed."""
    ls = Lanes(s)
    state = s.root / "state"

    def tree() -> list[tuple[str, str]]:
        return sorted(
            (
                str(p.relative_to(state)),
                hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else "d",
            )
            for p in state.rglob("*")
        )

    def refuse(want: str) -> None:
        ls.seed("gh902")
        before = tree()
        r = ls.lane("archive", "gh902", want=1)
        out = r.out + r.err
        assert "lane reflection of gh902 failed" in out, (
            f"refusal does not name the failed reflection: {out}"
        )
        assert want in out, f"refusal does not say {want!r}: {out}"
        assert tree() == before, "refusal changed files"
        assert (ls.lanes / "gh902.toml").is_file(), "lanes/ no longer lists gh902"
        assert (ls.lanes / "gh902.handoffs.jsonl").is_file(), "lanes/ no longer lists gh902"

    reply = s.root / "reply.lane"
    (s.root / "reply.lane.exit").write_text("1")
    (s.root / "reply.lane.err").write_text("Error: 503 model openai/gpt-6.1-sol unreachable\n")
    refuse("reflector exited 1: Error: 503 model openai/gpt-6.1-sol unreachable")
    (s.root / "reply.lane.exit").unlink()
    for text, want in (
        ("Looks fine to me.\n", "0 Questions lines"),
        ("Questions: caught-by-hand\nFindings: none\n", "want each of"),
        (
            (
                f"{LANE_QUESTIONS}\nFinding: class: owner-caught-x | question: caught-by-hand | "
                "route: r | summary: s\n"
            ),
            "owner-caught-",
        ),
        (
            f"{LANE_QUESTIONS}\nFinding: class: x | question: nope | route: r | summary: s\n",
            "question 'nope'",
        ),
        (f"{LANE_QUESTIONS}\n", "no Finding line and no"),
    ):
        reply.write_text(text)
        refuse(want)


if __name__ == "__main__":
    main(archive_findings, reflect_alone, refusals)
