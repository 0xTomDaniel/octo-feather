"""The scenarios of tests/gate/kit/test_lane_reflect.py (its items), this file their command
(testkit.main): the lane reflection (spec comms #acceptance-reflect-lane,
#acceptance-reflect-before-archive, #reflection-output) through `octo-feather-lane reflect` and
`archive`, in testkit.reflector's world; what the reflector was shown read by testkit.shown, a
case's act at the model's turn by testkit.turn."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from typing import TYPE_CHECKING

from testkit import (
    DIRECTOR,
    MODEL_DOWN,
    QUESTIONS,
    ROOT,
    Scratch,
    Shown,
    appended,
    director,
    kit,
    main,
    reflection,
    reflector,
    reply,
    shown,
    tree,
    turn,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

SESSION = "0b5e7a1c-0000-4000-8000-00000000c0de"
# Each literal-LF boundary of the supervisor's transcript and its windows' LF line spans.
BOUNDARIES = {
    b"{}\n": ((1, 1),),
    b"{}\n{}": ((1, 2),),
    b"{}\n{}\n": ((1, 2),),
    b'{}\n{"text":"' + b"x" * 70000 + b'"}\n{}\n': ((1, 2), (2, 2), (2, 3)),
}


class Lanes:
    """Lanes on S's reflection world; the director log a stranded-worker catch about gh900 and
    another lane's line; a worker's session under the scratch HOME."""

    def __init__(self, s: Scratch) -> None:
        self.s, self.top = s, reflector(s)
        self.lanes = self.top / "lanes"
        self.lanes.mkdir()
        self.dlog = self.top / "director.handoffs.jsonl"
        self.dlog.write_text(
            '{"at":"2026-10-28T00:20:00Z","kind":"note","issue":900,"text":"read pane w9:p3: '
            'implementer-gh900 stranded at a trust prompt"}\n'
            '{"at":"2026-10-28T00:21:00Z","kind":"note","issue":7,"text":"unrelated lane"}\n'
        )
        self.sessions = s.home / ".pi" / "agent" / "sessions" / "--w--"
        self.sessions.mkdir(parents=True)
        self.tr = self.sessions / f"2026-10-28T00-00-00-000Z_{SESSION}.jsonl"
        self.tr.write_text("{}\n")
        self.own = s.root / "own.jsonl"  # the supervisor's session, run from its pane w9:p2
        self.mine = {"HERDR_PANE_ID": "w9:p2", "PI_SESSION_FILE": str(self.own)}

    def seed(self, name: str) -> None:
        """Lane NAME (supervisor w9:p2): a worker's spawn with its session, a review finding."""
        (self.lanes / f"{name}.toml").write_text(
            f'issue = "{name}"\nsupervisor = "w9:p2"\ngoal = "scratch"\n'
        )
        (self.lanes / f"{name}.handoffs.jsonl").write_text(
            '{"at":"2026-10-28T00:00:00Z","kind":"spawn","name":"implementer-gh900","pane":"w9:p3",'
            f'"role":"implementer","session":"{SESSION}"}}\n'
            '{"at":"2026-10-28T00:10:00Z","kind":"finding","source":"code-review","class":'
            '"duplicated-rule","blocking":true,"summary":"restated rule"}\n'
        )

    def lane(
        self, *args: str, want: int = 0, env: Mapping[str, str] | None = None
    ) -> tuple[str, Shown | None]:
        """`octo-feather-lane ARGS`'s output and what its lane reflector was shown."""
        r = self.s.run([kit("octo-feather-lane"), *args], want=want, env=env)
        return f"{r.out}\n{r.err}", shown(self.s, "lane")

    def log(self, name: str) -> list[str]:
        return (self.lanes / f"{name}.handoffs.jsonl").read_text().splitlines()


def alone(s: Scratch) -> None:
    """`reflect` alone, no gap: the reflection line alone, nothing moved, the supervisor's own
    transcript a source; then windows_rebuilt, oversized, binding on lane gh901."""
    ls = Lanes(s)
    ls.seed("gh901")
    ls.own.write_text("{}\n")
    _, seen = ls.lane("reflect", "gh901", env=ls.mine)
    assert (ls.lanes / "gh901.toml").is_file(), "reflect moved the record"
    found, r = appended(ls.lanes / "gh901.handoffs.jsonl", 2)
    assert (found, r.findings, len(r.questions)) == ([], 0, 7), r
    assert seen, "the lane reflector never ran"
    assert seen.inputs.sources["supervisor w9:p2"].original == str(ls.own), "no own transcript"
    windows_rebuilt(ls)
    oversized(ls)
    binding(ls)


def windows_rebuilt(ls: Lanes) -> None:
    """Literal-LF boundaries with their spans; astral JSON escaping past 2000 lines ending
    mid-codepoint, in 2 windows."""
    tail = (json.dumps({"text": "🚀" * 3072}, ensure_ascii=False) + "\n" * 2100).encode()
    for raw, spans in [*BOUNDARIES.items(), (tail + b"\xf0\x9f", None)]:
        ls.own.write_bytes(raw)
        _, seen = ls.lane("reflect", "gh901", env=ls.mine)
        got = seen and seen.inputs.sources["supervisor w9:p2"]
        assert got, "the lane reflector never ran"
        assert (got.data, got.size) == (raw, len(raw)), f"not rebuilt: {raw[:12]!r}"
        assert got.sha256 == hashlib.sha256(raw).hexdigest(), "sha256 not the file's"
        assert got.spans == spans if spans else got.windows == 2, (got.spans, got.windows)


def changes(ls: Lanes) -> None:
    """A source appended to during the run: shown to its captured prefix; rewritten, truncated,
    replaced or gone: refused, nothing appended."""
    ls.seed("gh901")
    o = ls.own
    for act in (
        f'echo \'{{"later":"EXCLUDED-APPEND"}}\' >> {o}',
        f"echo '{{\"changed\":true}}' > {o}",
        f": > {o}",
        f"cp {o} {o}.new && mv {o}.new {o}",
        f"rm {o}",
    ):
        o.write_text("{}")  # a partial final line: later bytes still kept out
        before = ls.log("gh901")
        turn(ls.s, "lane", act)
        out, seen = ls.lane("reflect", "gh901", want=0 if ">>" in act else 1, env=ls.mine)
        if ">>" in act:
            assert seen, "the lane reflector never ran"
            assert "EXCLUDED-APPEND" not in seen.inputs.text(), "later append shown"
        else:
            assert "source prefix changed or unavailable" in out, f"{act} not refused: {out}"
            assert ls.log("gh901") == before, f"{act}: the reflection appended"
    turn(ls.s, "lane")


def oversized(ls: Lanes) -> None:
    """An oversized lane log past 400 lines: out of the brief, whole in its windows, each source's
    prefix identity on the reflection line."""
    with (ls.lanes / "gh901.handoffs.jsonl").open("a") as f:
        f.write(json.dumps({"kind": "note", "text": "EARLY-LANE-RECORD"}) + "\n")
        f.writelines(json.dumps({"kind": "note", "text": f"h-{i}"}) + "\n" for i in range(410))
        big = "LARGE-LANE-" + "é reference | " * 20000
        f.write(json.dumps({"kind": "note", "text": big}, ensure_ascii=False) + "\n")
    _, seen = ls.lane("reflect", "gh901")
    assert seen, "the lane reflector never ran"
    assert len(seen.brief.encode()) < 10000, "brief over 10000 bytes"
    assert "LARGE-LANE-" not in seen.brief, "lane evidence in the brief"
    assert seen.inputs.text().count("LARGE-LANE-") == 1, "lane log not shown once"
    assert "EARLY-LANE-RECORD" in seen.inputs.text(), "lane log not whole"
    r = reflection(ls.log("gh901")[-1])
    assert r.inputs.lane == "gh901", r.inputs.lane
    for src in r.inputs.sources.values():
        prefix = open(src.original, "rb").read()[: src.size]  # noqa: PTH123, SIM115
        assert hashlib.sha256(prefix).hexdigest() == src.sha256, f"prefix identity: {src.original}"


def binding(ls: Lanes) -> None:
    """Run from its pane (no native session): its current session wins over a newer one; an id
    not its header's refused; another caller's session file is no director source."""
    did = "0b5e7a1c-0000-4000-8000-00000000d1ec"
    trace = ls.sessions / f"old_{did}.jsonl"
    trace.write_text(json.dumps(DIRECTOR | {"id": did, "fact": "EXACT-DIRECTOR-ONLY"}) + "\n")
    (ls.sessions / "newest_other.jsonl").write_text('{"fact":"WRONG-NEWEST-SESSION"}\n')
    (ls.top / "director.toml").write_text('pane = "director-pane"\n')
    director(ls.s, None, "director-pane")
    here = {"HERDR_PANE_ID": "director-pane", "PI_SESSION_FILE": str(trace)}
    _, seen = ls.lane("reflect", "gh901", env=here | {"PI_SESSION_ID": did})
    text = seen.inputs.text() if seen else ""
    assert "EXACT-DIRECTOR-ONLY" in text, "explicit director source missing"
    assert "WRONG-NEWEST-SESSION" not in text, "guessed the newest session in its dir"
    out, _ = ls.lane("reflect", "gh901", want=1, env=here | {"PI_SESSION_ID": "wrong"})
    assert "header/session identity unavailable or mismatched" in out, out
    director(ls.s)  # Herdr knows w9:p99 alone
    out, _ = ls.lane("reflect", "gh901", want=1, env=here | {"HERDR_PANE_ID": "another-pane"})
    assert "director sourcegap" in out, f"unknown required source not refused: {out}"


def archive_findings(s: Scratch) -> None:
    """At archive, two gaps: two finding lines then the reflection line after the lane's lines;
    the reflector ran as agents/reflector.md on a brief naming its inputs (director line about
    the lane only, spawn transcript, lane log, report line, questions); then director_source."""
    ls = Lanes(s)
    ls.seed("gh900")
    reply(
        s,
        "lane",
        "class: stranded-worker-by-hand | question: caught-by-hand | route: agents/supervisor.md "
        "goal check-in | summary: director found implementer-gh900 stranded by reading pane w9:p3 "
        "(director log); a herdr agent get status check would have caught it first",
        "class: restated-rule | question: writer-mistake | route: .agents/skills/code-review | "
        "summary: review finding duplicated-rule (hand-off log line 2)",
    )
    before = ls.log("gh900")
    out, seen = ls.lane("archive", "gh900")
    arch = ls.lanes / "archive" / "gh900.handoffs.jsonl"
    assert arch.is_file(), f"gh900 not archived: {out}"
    assert not list(ls.lanes.glob("gh900.*")), f"gh900 still listed: {out}"
    assert "reflection: lane gh900, 2 findings" in out, f"no reflection summary: {out}"
    assert arch.read_text().splitlines()[:2] == before, "lane lines changed"
    (f1, f2), r = appended(arch, 2)
    want = ("stranded-worker-by-hand", "caught-by-hand", "agents/supervisor.md goal check-in")
    assert f1[:3] == want, f1
    assert "stranded by reading pane w9:p3" in f1.summary, f1
    assert f2[:2] == ("restated-rule", "writer-mistake"), f2
    assert (f1.blocking, f2.blocking) == (False, False), "a reflection finding blocks"
    assert (r.findings, r.questions) == (2, QUESTIONS["lane"]), r
    assert seen, "the lane reflector never ran"
    skill = str(ROOT / ".agents" / "skills" / "reflect")
    for w in ("openai/gpt-6.1-sol", "high", "read,grep,find,ls,codemode", skill):
        assert w in seen.argv, f"reflector argv lacks {w!r}: {seen.argv}"
    assert "- caught-by-hand: What did anyone" in seen.brief, seen.brief
    m = seen.inputs
    assert "read pane w9:p3: implementer-gh900 stranded" in m.sources["director log"].text()
    assert "unrelated lane" not in m.text(), "brief quoted another lane's director line"
    assert m.sources["spawn implementer-gh900 implementer w9:p3"].original == str(ls.tr)
    assert m.sources["handoff log"].original == str(ls.lanes / "gh900.handoffs.jsonl")
    assert "lane gh900: issue gh900" in m.derived["factory-report"].text(), "no report line"
    reply(s, "lane")
    ls.seed("gh904")
    director_source(ls)


def director_source(ls: Lanes) -> None:
    """No director source refuses (sourcegap); --director-source refused for a wrong pane, a
    missing file, a non-session header, another cwd, a conflicting native path or id; the
    record or header changed during the run refused, nothing appended or moved; native id
    binding; a declared older session reaches both archive reflections."""
    s, b, talk = ls.s, tree(ls.top), str(ls.s.root / "director.jsonl")
    director(s, None)
    out, _ = ls.lane("archive", "gh904", want=1)
    assert "sourcegap" in out, f"missing director source not refused: {out}"
    assert tree(ls.top) == b, "sourcegap changed archive state"
    explicit = s.root / "explicit.jsonl"
    for pane, native, text in (
        ("wrong-pane", None, None),
        ("w9:p99", None, ""),  # no such file
        ("w9:p99", None, '{"type":"message","id":"not-session"}\n'),
        ("w9:p99", None, '{"type":"session","id":"wrong-cwd","cwd":"/another/cwd"}\n'),
        ("w9:p99", "path", None),
        ("w9:p99", "id", json.dumps(DIRECTOR | {"id": "wrong-native-id"})),
    ):
        explicit.write_text(json.dumps(DIRECTOR) + "\n" if text is None else text)
        f = s.root / "no-such-source" if text == "" else explicit
        director(s, native)
        out, _ = ls.lane("archive", "gh904", "--director-source", pane, str(f), want=1)
        assert "invalid --director-source" in out, f"{pane} {native} {text} not refused: {out}"
        assert tree(ls.top) == b, f"{pane} {native} {text} changed archive state"
    director(s)
    header = json.dumps(DIRECTOR | {"id": "changed-header"})
    for act, want in (
        (
            f"echo 'pane = \"changed-pane\"' > {ls.top}/director.toml",
            "does not match director.toml",
        ),
        (f"echo '{header}' > {talk}", "director source binding changed"),
    ):
        logs = (ls.log("gh904"), ls.dlog.read_text())
        turn(s, "lane", act)
        out, seen = ls.lane("archive", "gh904", "--director-source", "w9:p99", talk, want=1)
        assert seen, f"{act}: the lane reflector never ran"
        m = seen.inputs
        assert (m.mode, m.pane, m.session) == (
            "explicit-director-handoff",
            "w9:p99",
            DIRECTOR["id"],
        )
        assert m.sources["director record"].data == b'pane = "w9:p99"\n', "record before the act"
        assert want in out, f"{act} not refused: {out}"
        assert (ls.log("gh904"), ls.dlog.read_text()) == logs, f"{act}: reflection appended"
        assert (ls.lanes / "gh904.toml").is_file(), f"{act}: lane moved"
        assert not (ls.lanes / "archive" / "gh904.toml").exists(), f"{act}: lane archived"
        (ls.top / "director.toml").write_text('pane = "w9:p99"\n')
        (s.root / "director.jsonl").write_text(json.dumps(DIRECTOR) + "\n")
    turn(s, "lane")
    director(s, "id")
    ls.lane("reflect", "gh904", "--director-source", "w9:p99", talk)
    declared = s.root / "declared-old.jsonl"
    shutil.copy(talk, declared)
    os.utime(declared, (946684800, 946684800))  # 2000-01-01: a declaration, no currentness proof
    director(s, None)
    ls.lane("archive", "gh904", "--director-source", "w9:p99", str(declared))
    for log in (ls.lanes / "archive" / "gh904.handoffs.jsonl", ls.dlog):
        m = reflection(log.read_text().splitlines()[-1]).inputs
        assert m.mode == "explicit-director-handoff", f"{log}: binding {m.mode}"
        assert str(declared) in [x.original for x in m.sources.values()], f"{log}: source"


def refusals(s: Scratch) -> None:
    """The model unreachable, past its timeout, Pi not launching, or a reply outside the form:
    archive refuses naming the failed reflection, no traceback, the state dir unchanged, the lane
    listed; then changes."""
    ls = Lanes(s)

    def refuse(want: str, env: Mapping[str, str] | None = None) -> None:
        ls.seed("gh902")
        before = tree(ls.top)
        out, _ = ls.lane("archive", "gh902", want=1, env=env)
        assert "lane reflection of gh902 failed" in out, f"not the failed reflection: {out}"
        assert want in out, f"refusal does not say {want!r}: {out}"
        assert "Traceback" not in out, f"traceback: {out}"
        assert tree(ls.top) == before, f"refusal ({want}) changed files"

    turn(s, "lane", MODEL_DOWN)
    refuse("reflector exited 1: Error: 503 model openai/gpt-6.1-sol unreachable")
    turn(s, "lane", "sleep 2")
    refuse("reflector ran past", {"OCTO_FEATHER_REFLECT_TIMEOUT": "0.2"})
    turn(s, "lane")
    path = s.env["PATH"]
    s.without("pi")
    refuse("reflector exited")
    s.env["PATH"] = path
    q = "Questions: " + ", ".join(QUESTIONS["lane"])
    bad = "Finding: class: {} | question: {} | route: r | summary: s"
    replies = s.root / "reply.lane"
    for text, want in (
        ("Looks fine to me.", "0 Questions lines"),
        ("Questions: caught-by-hand\nFindings: none", "want each of"),
        (f"{q}\n" + bad.format("owner-caught-x", "caught-by-hand"), "owner-caught-"),
        (f"{q}\n" + bad.format("x", "nope"), "question 'nope'"),
        (q, "no Finding line and no"),
    ):
        replies.write_text(text + "\n")
        refuse(want)
    reply(s, "lane")
    changes(ls)


if __name__ == "__main__":
    main(alone, archive_findings, refusals)
