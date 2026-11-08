"""The scenarios of tests/gate/kit/test_director_reflect.py (its items), this file their command
(testkit.main): the director reflection (spec comms #reflection-director, #reflection-writer-route,
#acceptance-reflect-director, #acceptance-reflect-writer-route, #acceptance-reflect-missed,
#acceptance-reflect-daily): scripts/octo-feather-lane reflect --director and archive, and
scripts/octo-feather-start, run as commands; the real scripts/pi-role starts agents/reflector.md,
the testkit's Pi stand-in first on PATH for the model (print mode: it records the director brief
and prints the reply the case records, testkit.reflector), the testkit's herdr (its agents world
for a start, else no server), its gh the tracker. The brief carries the director log's lines since
the last director reflection, every lane log (archived included) with its lane reflections, and
the finding class counts by source and frequency; the director log gains the finding and
reflection lines of spec comms #reflection-output; archive runs it after the lane reflection and
refuses, every file in place, when it cannot run; a start runs it in the background when the last
one is two days old, and not when it is fresh."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import signal
import subprocess

from testkit import ROOT, Ran, Scratch, kit, main, reflector


def ago(hours: float) -> str:
    return (dt.datetime.now(dt.UTC) - dt.timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")


def cr(at: str, source: str, cls: str) -> str:
    d = {
        "at": at,
        "kind": "finding",
        "source": source,
        "class": cls,
        "blocking": True,
        "summary": "s",
    }
    return json.dumps(d, separators=(",", ":")) + "\n"


class Director:
    """Three lanes, one code-review class in each: gh1 archived after a lane reflection that found
    no gap, gh2 archived, gh3 open; gh3's review found the gap later, and a qc finding of another
    class; the director log's last reflection two days ago."""

    def __init__(self, s: Scratch) -> None:
        self.s = s
        for k in ("HERDR_PANE_ID", "PI_SESSION_FILE", "OCTO_FEATHER_REFLECT_ARGS"):
            s.env.pop(k, None)
        s.env |= {"XDG_STATE_HOME": str(s.root / "state"), "HERDR_SESSION": ""}
        s.identity()
        reflector(s)
        # the kit's tracker, where a director reflection-missed finding files: its recorded search
        # answer (none open) and its answer to the new issue
        kit_repo = "0xTomDaniel/octo-feather"
        search = (
            f"issue list --repo {kit_repo} --state all --limit 1000 --search "
            '"correction-lane" in:title --json number,title,state,closedAt'
        )
        self.search = search
        s.gh.tape({search: ["[]\n"]})
        self.state = s.root / "state" / "octo-feather"
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
        self.record("gh3")
        (self.lanes / "gh3.handoffs.jsonl").write_text(
            cr("2026-10-22T00:00:00Z", "code-review", "duplicated-rule")
            + cr("2026-10-22T00:01:00Z", "qc", "bad-fixture")
        )
        self.old = ago(48)
        self.dlog.write_text(
            '{"at":"2026-10-19T00:00:00Z","kind":"note","text":"before-last-reflection"}\n'
            f'{{"at":"{self.old}","kind":"reflection","findings":0,"questions":["owner-asked"]}}\n'
            '{"at":"2026-10-27T00:00:00Z","kind":"finding","class":"owner-caught-stranded-worker",'
            '"issue":3,"summary":"owner found implementer-gh3 stranded at a prompt"}\n'
        )

    def record(self, name: str) -> None:
        (self.lanes / f"{name}.toml").write_text(
            f'issue = "{name}"\nsupervisor = "w9:p2"\ngoal = "scratch"\n'
        )

    def lane(self, *args: str, want: int = 0, **env: str) -> Ran:
        return self.s.run([kit("octo-feather-lane"), *args], want=want, env=env)

    def brief(self) -> str:
        """The director reflector's last argv (the stand-in's record), one argument a line."""
        return (self.s.root / "argv.director").read_text().replace("\0", "\n")

    def reflections(self) -> int:
        return sum(
            json.loads(x).get("kind") == "reflection" for x in self.dlog.read_text().splitlines()
        )


def writer_route(s: Scratch) -> None:
    """acceptance-reflect-writer-route, -missed: reflect --director on its own appends the two
    findings and the reflection line; the brief names the model, the reflect skill, the last
    director reflection, the owner-caught line since it (not a line from before), the class
    counts by source and frequency, each lane log with its lane reflections, the factory report,
    the director's questions (no lane question). --due: the last one ran just now, so a due run
    does nothing."""
    d = Director(s)
    reflector(
        s,
        director=[
            (
                "Finding: class: duplicated-rule | question: writer-route | route: "
                "agents/implementer.md Rules | summary: 3 code-review findings in 3 lanes (gh1, "
                "gh2, gh3); writers restate rules"
            ),
            (
                "Finding: class: reflection-missed | question: director-reflection-missed | "
                "route: reflection/questions.json undetected-rule | summary: gh1 reflection found "
                "no gap; gh3 review found duplicated-rule; reword undetected-rule"
            ),
        ],
    )
    b = len(d.dlog.read_text().splitlines())
    from testkit.gh_recordings import recording_run  # noqa: PLC0415 (only this case)

    expected_request: list[str] = []

    def arm_create() -> None:
        findings = [json.loads(x) for x in d.dlog.read_text().splitlines()[b:]]
        at = next(x["at"] for x in findings if x.get("class") == "reflection-missed")
        title = (
            f"[correction-lane reflection-missed {at} 6aea7eb4] "
            "change the question list: reflection-missed"
        )
        request = f"GH_REPO=0xTomDaniel/octo-feather issue create --title {title} --body-file -"
        expected_request.append(request)
        tape_file = s.gh.dir / "tape.json"
        tape = json.loads(tape_file.read_text())
        tape[request] = ["https://github.com/0xTomDaniel/octo-feather/issues/704\n"]
        tape_file.write_text(json.dumps(tape))

    r = recording_run(
        s, [kit("octo-feather-lane"), "reflect", "--director"], (d.search,), arm_create
    )
    sent = [json.loads(x) for x in (s.gh.dir / "requests.jsonl").read_text().splitlines()]
    assert [x["request"] for x in sent] == [d.search, *expected_request], sent
    assert (
        "gh1 reflection found no gap; gh3 review found duplicated-rule; reword undetected-rule"
        in sent[-1]["body"]
    ), sent
    out = r.out + r.err
    assert "reflection: director, 2 findings, questions owner-asked," in out, (
        f"no reflection summary: {out}"
    )
    f1, f2, refl = (json.loads(x) for x in d.dlog.read_text().splitlines()[b:])
    for f in (f1, f2):
        assert set(f) == {"at", "kind", "source", "class", "question", "route", "summary"}, f
        assert f["source"] == "reflection", f
    want1 = ("duplicated-rule", "writer-route", "agents/implementer.md Rules")
    assert (f1["class"], f1["question"], f1["route"]) == want1, f1
    assert "3 code-review findings in 3 lanes" in f1["summary"], f1
    assert (f2["class"], f2["question"]) == ("reflection-missed", "director-reflection-missed"), f2
    assert (refl["kind"], refl["findings"], len(refl["questions"])) == ("reflection", 2, 9), refl
    brief = d.brief()
    for want in (
        "openai/gpt-6.1-sol",
        str(ROOT / ".agents" / "skills" / "reflect"),
        f"last director reflection ({d.old})",
        "owner-caught-stranded-worker",
        (
            "class duplicated-rule, source code-review: 3 findings in 3 lanes (gh1, gh2, gh3), "
            "last 2026-10-22T00:00:00Z"
        ),
        "class bad-fixture, source qc: 1 finding in 1 lane (gh3)",
        (
            f"gh1: {d.lanes}/archive/gh1.handoffs.jsonl; lane reflections: 2026-10-20T01:00:00Z "
            "0 findings"
        ),
        f"gh3: {d.lanes}/gh3.handoffs.jsonl; lane reflections: none",
        "report at ",
        "- writer-route: Which code-review",
    ):
        assert want in brief, f"director brief lacks {want!r}: {brief}"
    assert "before-last-reflection" not in brief, (
        "brief quoted a line from before the last reflection"
    )
    assert "- caught-by-hand:" not in brief, "director brief asked a lane question"
    (s.root / "argv.director").unlink()
    r = d.lane("reflect", "--director", "--due")
    assert "director reflection: not due, last ran" in r.out + r.err, f"--due: {r.out} {r.err}"
    assert not (s.root / "argv.director").exists(), "--due ran a fresh one"


def at_archive(s: Scratch) -> None:
    """acceptance-reflect-director: archiving a merged lane runs the lane, then the director
    reflection: one reflection line more in the director log, its owner-asked finding, the brief
    naming the owner-caught line and the archiving lane's log. The director reflection cannot run
    (its model unreachable): archive refuses naming it, every file as it was."""
    d = Director(s)
    d.record("gh4")
    (d.lanes / "gh4.handoffs.jsonl").write_text(cr("2026-10-28T00:00:00Z", "code-review", "x"))
    with d.dlog.open("a") as f:
        f.write(
            '{"at":"2026-10-28T00:30:00Z","kind":"finding","class":"owner-caught-merge-order",'
            '"summary":"owner asked why the unblocking fix was not merged first"}\n'
        )
    reflector(
        s,
        director=[
            (
                "Finding: class: merge-order-by-hand | question: owner-asked | route: "
                "agents/director.md Merge order | summary: owner asked why the unblocking fix was "
                "not first (director log owner-caught-merge-order); a blocked-by count in "
                "octo-feather-lane report would have caught it first"
            )
        ],
    )
    b = d.reflections()
    r = d.lane("archive", "gh4")
    out = r.out + r.err
    assert (d.lanes / "archive" / "gh4.toml").is_file(), f"gh4 not archived: {out}"
    assert not (d.lanes / "gh4.toml").exists(), f"gh4 not archived: {out}"
    assert "reflection: lane gh4" in out, f"archive did not run both reflections: {out}"
    assert "reflection: director, 1 finding" in out, f"archive did not run both reflections: {out}"
    assert d.reflections() == b + 1, "director log did not gain one reflection line"
    assert '"question": "owner-asked"' in d.dlog.read_text().splitlines()[-2], (
        "no owner-asked finding"
    )
    brief = d.brief()
    assert "owner-caught-merge-order" in brief, "director brief lacks the owner-caught line"
    assert f"gh4: {d.lanes}/gh4.handoffs.jsonl" in brief, (
        "director brief lacks the archiving lane's log"
    )
    d.record("gh5")
    (d.lanes / "gh5.handoffs.jsonl").write_text(cr("2026-10-28T00:00:00Z", "code-review", "x"))
    (s.root / "reply.director.exit").write_text("1")
    (s.root / "reply.director.err").write_text("Error: 503 model openai/gpt-6.1-sol unreachable\n")
    state = s.root / "state"

    def tree() -> list[tuple[str, str]]:
        return sorted(
            (
                str(p.relative_to(state)),
                hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else "d",
            )
            for p in state.rglob("*")
        )

    before = tree()
    r = d.lane("archive", "gh5", want=1)
    out = r.out + r.err
    assert "director reflection failed (reflector exited 1: Error: 503" in out, f"no refusal: {out}"
    assert tree() == before, "refusal changed files"


def at_start(s: Scratch) -> None:
    """acceptance-reflect-daily: a lane start when the last director reflection ran two days ago
    runs one in the background: the start returns while the reflector is held (its readiness
    gate, never a delay), no reflection line yet; once released, the background run (its end seen
    as EOF on a pipe only it still holds) appends one reflection line and prints its report line
    to director-reflection.out. Fresh now: a second start runs none."""
    d = Director(s)
    herdr = s.root / "herdr"
    herdr.mkdir()
    (herdr / "agents.json").write_text("{}")
    for k in [k for k in s.env if k.startswith(("HERDR_", "OCTO_FEATHER_"))]:
        del s.env[k]
    s.env |= {
        "FAKE_HERDR": str(herdr),
        "XDG_CACHE_HOME": str(s.root / "cache"),
        "HERDR_SESSION": "",
    }
    s.git(s.root, "init", "-q", "-b", "main", "target")
    gate = s.root / "reply.director.gate"
    os.mkfifo(gate)
    b = d.reflections()
    out = d.state / "director-reflection.out"

    def start(issue: str) -> int:
        """octo-feather-start --issue ISSUE; the read end of a pipe its background children hold."""
        r, w = os.pipe()
        p = subprocess.run(
            [kit("octo-feather-start"), "--issue", issue, "--cwd", str(s.root / "target")],
            env=s.env,
            cwd=s.root,
            capture_output=True,
            text=True,
            pass_fds=(w,),
            check=False,
            timeout=60,
        )
        os.close(w)
        assert p.returncode == 0, f"start failed: {p.stdout} {p.stderr}"
        return r

    def drained(r: int) -> None:
        """Every holder of the pipe's write end exited (the background reflection done)."""
        signal.alarm(60)  # a run that never ends fails the case, never hangs it
        with os.fdopen(r) as f:
            f.read()
        signal.alarm(0)

    r = start("12")
    assert d.reflections() == b, (
        "start waited on the reflection, or it ran before the reflector returned"
    )
    signal.alarm(60)
    with gate.open("w"):  # the held reflector answers now
        pass
    signal.alarm(0)
    drained(r)
    assert d.reflections() == b + 1, f"start ran no director reflection: {out.read_text()}"
    assert "reflection: director, 0 findings" in out.read_text(), (
        "no output in director-reflection.out"
    )
    gate.unlink()
    (s.root / "argv.director").unlink()
    drained(start("13"))
    assert "director reflection: not due, last ran" in out.read_text(), out.read_text()
    assert not (s.root / "argv.director").exists(), "a fresh reflection ran again"


if __name__ == "__main__":
    main(writer_route, at_archive, at_start)
