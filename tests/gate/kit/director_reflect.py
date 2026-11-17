"""The scenarios of tests/gate/kit/test_director_reflect.py (its items), this file their command
(testkit.main): the director reflection (spec comms #reflection-director, #reflection-writer-route,
#acceptance-reflect-director, #acceptance-reflect-writer-route, #acceptance-reflect-missed,
#acceptance-reflect-daily) through `octo-feather-lane reflect --director [--due]` and `archive`,
`octo-feather-start --issue` and the public `verify-octo-feather run director-reflection`, in
testkit.reflector's world; what the reflector was shown read by testkit.shown, a case's act at
the model's turn by testkit.turn.

The world (Director): three lanes, one code-review class in each: gh1 archived after a lane
reflection that found no gap, gh2 archived, gh3 open with a qc finding of another class too; the
director log: a line, its last director reflection two days ago, an owner-caught finding, 411
history lines, then a line past Linux's single-argument limit, multibyte."""

from __future__ import annotations

import datetime as dt
import json
import os
import signal
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, TypeVar

from testkit import (
    MODEL_DOWN,
    QUESTIONS,
    ROOT,
    Scratch,
    Shown,
    appended,
    get,
    kit,
    main,
    reflector,
    reply,
    shown,
    tree,
    turn,
)

if TYPE_CHECKING:
    from collections.abc import Callable

T = TypeVar("T")
L = kit("octo-feather-lane")
HOLD = 60  # s: a hang guard on a held reflector, never a proof


def ago(hours: float) -> str:
    return (dt.datetime.now(dt.UTC) - dt.timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")


def cr(at: str, source: str, cls: str) -> str:
    d = {"at": at, "kind": "finding", "source": source, "class": cls, "blocking": True}
    return json.dumps(d | {"summary": "s"}) + "\n"


def guarded(f: Callable[[], T], what: str) -> T:
    """F's result; F still running after HOLD fails the case naming WHAT (a hang guard)."""

    def hang(*_: object) -> None:
        msg = f"{what}: still waiting after {HOLD}s"
        raise TimeoutError(msg)

    signal.signal(signal.SIGALRM, hang)
    signal.alarm(HOLD)
    try:
        return f()
    finally:
        signal.alarm(0)


class Director:
    """The world of the module docstring."""

    def __init__(self, s: Scratch) -> None:
        self.s, self.state = s, reflector(s)
        self.lanes = self.state / "lanes"
        self.dlog = self.state / "director.handoffs.jsonl"
        (self.lanes / "archive").mkdir(parents=True)
        (self.lanes / "archive" / "gh1.handoffs.jsonl").write_text(
            cr("2026-10-20T00:00:00Z", "code-review", "duplicated-rule")
            + '{"at":"2026-10-20T01:00:00Z","kind":"reflection","findings":0,'
            '"questions":["undetected-rule"]}\n'
        )
        (self.lanes / "archive" / "gh2.handoffs.jsonl").write_text(
            cr("2026-10-21T00:00:00Z", "code-review", "duplicated-rule")
        )
        self.lane(
            "gh3",
            cr("2026-10-22T00:00:00Z", "code-review", "duplicated-rule")
            + cr("2026-10-22T00:01:00Z", "qc", "bad-fixture"),
        )
        self.old = ago(48)
        text = "BEGIN synthetic " + "é transport | " * 20000 + " END synthetic"
        self.large = json.dumps({"kind": "note", "text": text}, ensure_ascii=False)
        history = "".join(
            json.dumps({"kind": "note", "text": f"history-{i}"}) + "\n" for i in range(410)
        )
        self.dlog.write_text(
            '{"at":"2026-10-19T00:00:00Z","kind":"note","text":"before-last-reflection"}\n'
            f'{{"at":"{self.old}","kind":"reflection","findings":0,"questions":["owner-asked"]}}\n'
            '{"at":"2026-10-27T00:00:00Z","kind":"finding","class":"owner-caught-stranded-worker",'
            '"issue":3,"summary":"owner found implementer-gh3 stranded at a prompt"}\n'
            + json.dumps({"kind": "note", "text": "EARLY beyond400 relevant history"})
            + "\n"
            + history
            + self.large
            + "\n"
        )

    def lane(self, name: str, log: str) -> None:
        (self.lanes / f"{name}.toml").write_text(
            f'issue = "{name}"\nsupervisor = "w9:p2"\ngoal = "scratch"\n'
        )
        (self.lanes / f"{name}.handoffs.jsonl").write_text(log)

    def kinds(self) -> list[str]:
        return [
            get(json.loads(x), "kind", str, "director log line")
            for x in self.dlog.read_text().splitlines()
        ]

    def run(self, *args: str, want: int = 0, **env: str) -> tuple[str, Shown | None]:
        """octo-feather-lane ARGS's output and what its director reflector was shown."""
        r = self.s.run([L, *args], want=want, env=env)
        return f"{r.out}\n{r.err}", shown(self.s, "director")


def writer_route(s: Scratch) -> None:
    """reflect --director alone appends two findings and the reflection line (every director
    question); the brief names the last reflection and director questions only, never quoting the
    large line; the argv the model and reflect skill; the director log window holds the lines
    since the last reflection, the large line once and whole; each lane log whole; the class
    counts and the factory report. --due right after does nothing."""
    d = Director(s)
    reply(
        s,
        "director",
        "class: duplicated-rule | question: writer-route | route: agents/implementer.md Rules | "
        "summary: 3 code-review findings in 3 lanes (gh1, gh2, gh3); writers restate rules",
        "class: reflection-missed | question: director-reflection-missed | route: "
        "reflection/questions.json undetected-rule | summary: gh1 reflection found no gap; gh3 "
        "review found duplicated-rule; reword undetected-rule",
    )
    b = len(d.dlog.read_text().splitlines())
    out, got = d.run("reflect", "--director")
    assert "reflection: director, 2 findings, questions owner-asked," in out, out
    (f1, f2), r = appended(d.dlog, b)
    assert f1[:3] == ("duplicated-rule", "writer-route", "agents/implementer.md Rules"), f1
    assert "3 code-review findings in 3 lanes" in f1.summary, f1
    assert f2[:2] == ("reflection-missed", "director-reflection-missed"), f2
    assert (f1.blocking, f2.blocking) == (None, None), "a director finding carries blocking"
    assert (r.findings, r.questions) == (2, QUESTIONS["director"]), r
    assert got, "the director reflector never ran"
    assert len(d.large.encode()) > 131072
    assert len(got.brief.encode()) < 10000, "brief quotes evidence"
    assert d.large not in got.brief, "brief quotes evidence"
    assert f"last director reflection ({d.old})" in got.brief, got.brief
    assert "- writer-route: Which code-review" in got.brief, got.brief
    assert "- caught-by-hand:" not in got.brief, "director brief asked a lane question"
    assert "openai/gpt-6.1-sol" in got.argv, got.argv
    assert str(ROOT / ".agents/skills/reflect") in got.argv, got.argv
    window = got.inputs.sources["director log"].text()
    assert window.count(d.large) == 1, "source evidence changed, truncated or duplicated"
    assert "owner-caught-stranded-worker" in window, "window lacks the owner-caught line"
    assert "EARLY beyond400 relevant history" in window, "window lacks early history"
    assert "before-last-reflection" not in window, "window quoted a line before the last one"
    for lane, path in (("gh1", "archive/gh1"), ("gh2", "archive/gh2"), ("gh3", "gh3")):
        log = d.lanes / f"{path}.handoffs.jsonl"
        assert got.inputs.sources[lane].original == str(log), got.inputs.sources[lane]
        assert got.inputs.sources[lane].text() == log.read_text(), f"{lane} log not whole"
    counts = got.inputs.derived["class-counts"].text().splitlines()
    for want in (
        (
            "class duplicated-rule, source code-review: 3 findings in 3 lanes (gh1, gh2, gh3), "
            "last 2026-10-22T00:00:00Z"
        ),
        "class bad-fixture, source qc: 1 finding in 1 lane (gh3), last 2026-10-22T00:01:00Z",
    ):
        assert want in counts, f"class counts lack {want!r}: {counts}"
    assert "report at " in got.inputs.derived["factory-report"].text(), "no factory report"
    out, got = d.run("reflect", "--director", "--due")
    assert "director reflection: not due, last ran" in out, out
    assert got is None, "--due ran a fresh one"


def at_archive(s: Scratch) -> None:
    """Archive runs the lane, then the director reflection: one reflection line more after its
    owner-asked finding, the manifest holding the owner-caught line and the lane's log. It
    cannot run, archive refuses naming it, the state dir unchanged: the model unreachable, a
    malformed reply, past OCTO_FEATHER_REFLECT_TIMEOUT (reflect --director alone: #846), the
    explicit binding changed while the second model runs (the first reflection undone too)."""
    d = Director(s)
    d.lane("gh4", cr("2026-10-28T00:00:00Z", "code-review", "x"))
    with d.dlog.open("a") as f:
        f.write(
            '{"at":"2026-10-28T00:30:00Z","kind":"finding","class":"owner-caught-merge-order",'
            '"summary":"owner asked why the unblocking fix was not merged first"}\n'
        )
    reply(
        s,
        "director",
        "class: merge-order-by-hand | question: owner-asked | route: agents/director.md Merge "
        "order | summary: owner asked why the unblocking fix was not first (director log "
        "owner-caught-merge-order); a blocked-by count in octo-feather-lane report would have "
        "caught it first",
    )
    b = len(d.dlog.read_text().splitlines())
    out, got = d.run("archive", "gh4")
    assert (d.lanes / "archive" / "gh4.toml").is_file(), out
    assert not (d.lanes / "gh4.toml").exists(), out
    assert "reflection: lane gh4" in out, out
    assert "reflection: director, 1 finding" in out, out
    (f,), _ = appended(d.dlog, b)
    assert f.question == "owner-asked", f
    assert got, "the director reflector never ran"
    assert "owner-caught-merge-order" in got.inputs.sources["director log"].text(), "no owner line"
    assert got.inputs.sources["gh4"].original == str(d.lanes / "gh4.handoffs.jsonl"), "no lane log"
    d.lane("gh5", cr("2026-10-28T00:00:00Z", "code-review", "x"))
    before = tree(d.state)

    def refused(want: str, *args: str, **env: str) -> None:
        out, _ = d.run(*args, want=1, **env)
        assert "director reflection failed" in out, out
        assert want in out, out
        assert "Traceback" not in out, f"traceback: {out}"
        assert tree(d.state) == before, f"refusal changed files ({want})"

    turn(s, "director", MODEL_DOWN)
    refused("director reflection failed (reflector exited 1: Error: 503", "archive", "gh5")
    turn(s, "director")
    (s.root / "reply.director").write_text("Malformed synthetic reply\n")
    refused("0 Questions lines", "archive", "gh5")
    reply(s, "director")
    turn(s, "director", "sleep 2")
    refused("reflector ran past", "reflect", "--director", OCTO_FEATHER_REFLECT_TIMEOUT="0.5")
    record = d.state / "director.toml"
    turn(s, "director", f"echo 'pane = \"changed-after-director-model-start\"' > {record}")
    talk = str(s.root / "director.jsonl")
    out, got = d.run("archive", "gh5", "--director-source", "w9:p99", talk, want=1)
    assert got, "the director reflector never ran"
    assert (got.inputs.mode, got.inputs.pane) == ("explicit-director-handoff", "w9:p99"), got
    assert got.inputs.sources["director record"].data == b'pane = "w9:p99"\n', "record before"
    assert "director reflection failed" in out, out
    assert "invalid --director-source" in out, out
    record.write_text('pane = "w9:p99"\n')  # the case's own change undone, the rest compared
    assert tree(d.state) == before, "second-model refusal failed rollback"


def at_start(s: Scratch) -> None:
    """A lane start two days after the last director reflection runs one in the background: the
    start returns while the reflector is held on a FIFO (no wall clock), no line yet; released,
    the background run (its end: EOF on a pipe only it still holds) appends one reflection line
    and its report line to director-reflection.out. A second start runs none."""
    d = Director(s)
    s.identity()
    for k in [k for k in s.env if k.startswith(("HERDR_", "OCTO_FEATHER_"))]:
        del s.env[k]
    s.env |= {
        "HERDR_SESSION": "",
        "XDG_CACHE_HOME": str(s.root / "cache"),
        "HERDR_SPAWN_READY_RETRIES": "2",
    }
    s.git(s.root, "init", "-q", "-b", "main", "target")
    gate = s.root / "gate"
    os.mkfifo(gate)
    turn(s, "director", f"cat {gate}")
    b = d.kinds().count("reflection")
    out = d.state / "director-reflection.out"

    def start(issue: str) -> int:
        """octo-feather-start --issue ISSUE; the read end of a pipe its background children hold."""
        r, w = os.pipe()
        p = subprocess.run(
            [kit("octo-feather-start"), "--issue", issue, "--cwd", str(s.root / "target")],
            env=s.env, cwd=s.root, capture_output=True, text=True, pass_fds=(w,), check=False,
            timeout=HOLD,
        )  # fmt: skip
        os.close(w)
        assert p.returncode == 0, f"start failed: {p.stdout} {p.stderr}"
        return r

    def ended(r: int) -> None:
        with os.fdopen(r) as f:
            guarded(f.read, "the background reflection")

    r = start("12")
    assert d.kinds().count("reflection") == b, "start waited on the reflection, or it ran unheld"
    os.close(guarded(lambda: os.open(gate, os.O_WRONLY), "the background reflector"))
    ended(r)
    assert d.kinds().count("reflection") == b + 1, f"no director reflection: {out.read_text()}"
    assert "reflection: director, 0 findings" in out.read_text(), out.read_text()
    assert shown(s, "director"), "the director reflector never ran"
    ended(start("13"))
    assert "director reflection: not due, last ran" in out.read_text(), out.read_text()
    assert shown(s, "director") is None, "a fresh reflection ran again"


# Each count variant of the public verify's reflect-live: the reply's count word, its route, and
# whether the drive passes (fallback-only: no finding at all).
VARIANTS = {
    "capital": ("Three", "writer templates", 0),
    "mixed": ("ThReE", "writer templates", 0),
    "lower": ("three", "writer templates", 0),
    "digit": ("3", "writer templates", 0),
    "missing": ("Several", "writer templates", 1),
    "two": ("two", "writer templates", 1),
    "two-digit": ("2", "writer templates", 1),
    "fallback-only": ("", "", 1),
    "review-route": ("Three", "code-review", 1),
}


def verify_counts(s: Scratch, *names: str) -> None:
    """The public verify run director-reflection judges the stand-in's reply for each variant
    NAMES: reflect-live's evidence (the seeded lines, then the findings and one reflection line
    with every director question; fallback-only: the seeded records named, no finding); PASS or
    FAIL reflect-live; refuse-unreachable (unshare'd: another network namespace than this one,
    the model unreachable there) and due-fresh passing every time."""
    reflector(s)
    net = str(Path("/proc/self/ns/net").readlink())
    turn(s, "director", f'[ "$(readlink /proc/self/ns/net)" = "{net}" ] || {{ {MODEL_DOWN}; }}')
    verify = str(ROOT / ".agents/skills/verify-octo-feather/scripts/verify-octo-feather")
    for name in names:
        count, route, want = VARIANTS[name]
        found = (
            [(f"class: duplicated-rule | question: writer-route | route: {route} | summary: "
             f"{count} blocking code-review findings across gh911, gh912 and gh913.")]
            if count else []
        )  # fmt: skip
        reply(s, "director", *found)
        v = s.root / f"verify-{name}"
        env = {
            "VERIFY_OCTO_FEATHER_RUN_DIR": str(v / "run"),
            "VERIFY_OCTO_FEATHER_EVIDENCE_DIR": str(v / "evidence"),
        }
        r = s.run([verify, "run", "director-reflection"], want=want, env=env)
        proof = v / "evidence" / "director-reflection"
        assert (proof / "reflect-live.exit").read_text().strip() == "0", name
        seeded = (proof / "reflect-live.obs.seeded").read_text()
        log = proof / "reflect-live.obs.director-log"
        assert log.read_text().startswith(seeded), f"{name}: seeded lines changed"
        fs, refl = appended(log, len(seeded.splitlines()))
        assert len(fs) == refl.findings == (0 if name == "fallback-only" else 1), (name, fs)
        assert refl.questions == QUESTIONS["director"], (name, refl.questions)
        assert all(f.cls == "duplicated-rule" for f in fs), (name, fs)
        if name == "fallback-only":  # the seeded records and the correction counter: no finding
            stdout = (proof / "reflect-live.stdout").read_text()
            assert "3 findings; route: none given by a reflection" in stdout, stdout
        out = f"{r.out}\n{r.err}"
        assert ("PASS reflect-live:" if want == 0 else "FAIL reflect-live:") in out, out
        assert "PASS refuse-unreachable:" in out, f"{name}: {out}"
        assert "PASS due-fresh:" in out, f"{name}: {out}"


if __name__ == "__main__":
    main(writer_route, at_archive, at_start, verify_counts)
