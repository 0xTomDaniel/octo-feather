"""One execution for suite and QC (quality spec #qc-capture, #qc-judgment;
#acceptance-one-execution, #acceptance-one-execution-incomplete), through commands: a scratch
target whose gate is the kit's runner (tests/gate/ copied unchanged) has one test tagged `#
criterion: demo#acceptance-a` (it leaves its declared artifact out/a.txt), one tagged
demo#acceptance-b that skips (exit 77), and one untagged. Its full gate, told the claims
(OCTO_FEATHER_QC_CLAIMS), runs each tagged test once in the qc sandbox and appends one record
per criterion naming each case, its outcome, fixtures and artifacts; octo-feather-qc then judges
acceptance-a pass from that record and acceptance-b insufficient evidence naming the skipped
case, rerunning nothing (no new record, no demo, no judge). A gate without claims captures
nothing; a claim naming no criterion, or a narrowed run with claims, stops the gate before any
test runs. Two specs (issue-lifecycle spec #qc-interim): the target gains other.spec.html, its
acceptance-c tagged on tests/other.sh; one full gate claims both specs' criteria, and one qc run
naming both status files judges each from that gate's records and commits both in one
status-only commit; an id in no named status file or in two is a usage error before anything
runs. The fake herdr, a pi that only logs: no model. Those targets and their claims gates are
prepared once per gate run (build, build_captured, build_two)."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from testkit import ROOT, Ran, Scratch, kit, main, tool_homes
from testkit.qc import RID, STATUS, qc, reports, target

JUSTFILE = """set positional-arguments
export GATE_RECIPES := "check-ok"
export OCTO_FEATHER_CHECK_RUN := `check-gate-free --run`
check: check-tests
check-ok:
    @true
check-tests *args:
    uv run --project "$KIT" --locked --offline --no-sync pytest -n 2 "$@"
"""
QC_TOML = """format = 2
[entry]
command = "true"
[services]
[fixture.seed]
reset = "true"
[values]
[demo."demo#acceptance-a"]
covers = ["tests"]
fixtures = ["seed"]
artifacts = ["out/a.txt"]
"""
ACCEPT = (
    "#!/usr/bin/env bash\n# criterion: demo#acceptance-a\nmkdir -p out && echo a > out/a.txt\n"
    'echo "RAN-accept: acceptance-a prints ok; home writable: '
    '$([[ -w "$HOME" ]] && echo yes || echo no)"\n'
)
SKIP = (
    "#!/usr/bin/env bash\n# criterion: demo#acceptance-b\n"
    'echo "skip: needs a GPU, none here" >&2; exit 77\n'
)
CASE = "tests/gate/test_gate.py::test_script[{}]"
CLAIMS = "OCTO_FEATHER_QC_CLAIMS"


def build(p: Scratch) -> None:
    """The target, its gate the kit's runner, its tests tagged."""
    files = {
        "tests/gate/conftest.py": (ROOT / "tests" / "gate" / "conftest.py").read_text(),
        "tests/gate/test_gate.py": (ROOT / "tests" / "gate" / "test_gate.py").read_text(),
        ".gitignore": ".pytest_cache/\n__pycache__/\nout/\n",
        "pytest.ini": "[pytest]\ntestpaths = tests/gate\n"
        "addopts = --strict-markers --junitxml=.pytest_cache/junit.xml\n",
        "qc.toml": QC_TOML,
        "justfile": JUSTFILE,
        "tests/accept.sh": ACCEPT,
        "tests/skip.sh": SKIP,
        "tests/plain.sh": "#!/usr/bin/env bash\necho plain ran\n",
    }
    r = p.root / "repo"
    r.mkdir()
    for name in ("accept.sh", "skip.sh", "plain.sh"):
        (r / "tests").mkdir(exist_ok=True)
        (r / "tests" / name).write_text(files.pop(f"tests/{name}"))
        (r / "tests" / name).chmod(0o755)
    target(p, files)


def world(s: Scratch, name: str = "oe") -> Path:
    """S filled with prepared NAME (build, or build_captured), a pi that only logs (any judge or
    model call shows in pi.log), the box's uv cache kept while HOME moves; its repo."""
    s.prepare(name, {"oe": build, "oe-captured": build_captured, "oe-two": build_two}[name])
    (s.bin / "pi").unlink()
    (s.bin / "pi").write_text(
        f'#!/usr/bin/env bash\n[[ "${{1:-}}" == --version ]] && exit 0\n'
        f'echo "$*" >> {s.root}/pi.log\nexit 2\n'
    )
    (s.bin / "pi").chmod(0o755)
    s.env["KIT"] = str(ROOT)
    s.env |= tool_homes()
    s.env.pop(CLAIMS, None)
    return s.root / "repo"


def gate(s: Scratch, *args: str, want: int | None = 0, claims: str | None = None) -> Ran:
    """The target's gate (`just check`, or ARGS) told CLAIMS, bounded; WANT None: any exit."""
    env = {CLAIMS: claims} if claims else {}
    cmd = ["timeout", "-k", "5", "300", "just", *(args or ("check",))]
    p = subprocess.run(
        cmd, cwd=s.root / "repo", env={**s.env, **env}, capture_output=True, text=True, check=False
    )
    out = p.stdout + p.stderr
    assert want is None or p.returncode == want, (
        f"{' '.join(cmd)}: exit {p.returncode}, want {want}: {out}"
    )
    return Ran(p.returncode, out, "")


def records(s: Scratch, *args: str) -> list[dict[str, Any]]:
    return json.loads(
        s.run(
            [kit("octo-feather-evidence"), "read", "--repo", ".", *args, "--json"],
            cwd=s.root / "repo",
        ).out
    )


def build_captured(p: Scratch) -> None:
    """The target's full gate told both claims; its output in gate.json."""
    r = world(p)
    g = gate(p, claims="demo#acceptance-a demo#acceptance-b")
    (p.root / "gate.json").write_text(
        json.dumps({"rc": g.rc, "out": g.out, "head": p.git(r, "rev-parse", "HEAD")})
    )


def captured(s: Scratch) -> tuple[Path, dict[str, Any]]:
    r = world(s, "oe-captured")
    return r, json.loads((s.root / "gate.json").read_text())


def claims_refused(s: Scratch) -> None:
    """A claim naming no criterion, and a narrowed gate run with claims: each refused before any
    test runs, no record appended."""
    world(s)
    g = gate(s, want=None, claims="demo#acceptance-nope")
    assert g.rc != 0, f"a claim naming no criterion: exit 0: {g.out}"
    assert "names no criterion" in g.out, g.out
    assert not re.search(r"RAN-accept|passed|skipped", g.out), g.out
    g = gate(
        s, "check-tests", CASE.format("tests/accept.sh"), want=None, claims="demo#acceptance-a"
    )
    assert g.rc != 0, f"a narrowed capturing run: exit 0: {g.out}"
    assert "needs the full gate" in g.out, g.out
    assert not re.search(r"RAN-accept|qc capture:", g.out), g.out
    assert records(s) == [], "a refused gate appended records"


def capture(s: Scratch) -> None:
    """The final full gate with the lane's claims: green (a skip is no failure), one record per
    criterion, each naming its case and outcome, run once in the qc sandbox (HOME read-only), the
    tagged record naming its fixtures and its artifact left."""
    _, g = captured(s)
    assert g["rc"] == 0, f"capturing gate: exit {g['rc']}: {g['out']}"
    head, out = g["head"], g["out"]
    ids = {}
    for cid, test, outcome in (
        ("a", "tests/accept.sh", "passed"),
        ("b", "tests/skip.sh", "skipped"),
    ):
        m = re.search(
            rf"^qc capture: demo#acceptance-{cid}: record ({RID}), 1 case\(s\): "
            rf"{re.escape(test)} {outcome}$",
            out,
            re.MULTILINE,
        )
        assert m, f"want one record for acceptance-{cid} naming its case and outcome: {out}"
        ids[cid] = m.group(1)
    recs = {x["record"]["id"]: x for x in records(s, "--commit", head)}
    assert len(recs) == 2, recs
    for cid, test, outcome in (
        ("a", "tests/accept.sh", "passed"),
        ("b", "tests/skip.sh", "skipped"),
    ):
        x = recs[ids[cid]]
        r, o = x["record"], Path(x["dir"]) / "outputs"
        assert r["criterion"]["id"] == f"demo#acceptance-{cid}", r
        assert r["revision"] == head, r
        assert r["dirty"] is False, r
        cap = json.loads((o / "test.capture.json").read_text())
        assert cap["gate"]["head_at_start"] == head, cap
        assert cap["gate"]["clean_at_start"] is True, cap
        assert cap["gate"]["gate_config"], cap
        [c] = cap["cases"]
        assert (c["case"], c["test"], c["outcome"]) == (CASE.format(test), test, outcome), c
        assert c["sandbox"]["proof"], c  # it ran in the qc sandbox: the proof came back
    a = recs[ids["a"]]
    cap = json.loads((Path(a["dir"]) / "outputs" / "test.capture.json").read_text())
    assert cap["fixtures"] == ["seed"], cap
    assert cap["artifacts"] == [{"path": "out/a.txt", "left": True}], cap
    assert a["record"]["fixture"]["names"] == ["seed"], a["record"]
    text = (Path(a["dir"]) / "outputs" / "test.output").read_text()
    assert text.count("RAN-accept") == 1, text  # once
    assert "home writable: no" in text, text  # HOME read-only: the sandbox
    assert "needs a GPU" in (Path(recs[ids["b"]]["dir"]) / "outputs" / "test.output").read_text()


def judged_from_records(s: Scratch) -> None:
    """Judgment refuses inside a check run. Outside, at the gate's head: acceptance-a pass and
    acceptance-b insufficient evidence from the gate's records, nothing rerun, no judge, the status
    file naming a's record."""
    r, g = captured(s)
    head = g["head"]
    s.run(
        [kit("octo-feather-qc"), STATUS, "9", "acceptance-a"],
        want=70,
        cwd=r,
        env={"OCTO_FEATHER_CHECK_RUN": '{"just":1}'},
    )
    q = qc(s, r, "9", "acceptance-a", "acceptance-b", want=2)
    ids = dict(
        re.findall(rf"^qc capture: demo#acceptance-([ab]): record ({RID})", g["out"], re.MULTILINE)
    )
    a, b = ids["a"], ids["b"]
    ls = q.out.splitlines()
    n = next(i for i, x in enumerate(ls) if x.startswith("PASS acceptance-a: "))
    assert (
        f"  evidence complete; decision tagged test assertions; record {a}" in ls[n + 1 : n + 3]
    ), q.out
    n = next(i for i, x in enumerate(ls) if x.startswith("INSUFFICIENT EVIDENCE acceptance-b: "))
    skipped = (
        f"missing: case tests/skip.sh ({CASE.format('tests/skip.sh')}) skipped: "
        "skip: needs a GPU, none here"
    )
    assert any(skipped in x for x in ls[n + 1 : n + 3]), q.out
    assert (
        f"  evidence incomplete; decision tagged test assertions; record {b}" in ls[n + 1 : n + 4]
    ), q.out
    assert len(records(s)) == 2, "qc reran something"
    assert not re.search(r"agent fallback|qc: demo ", q.err), (
        f"qc ran a demo or the fallback: {q.err}"
    )
    log = s.root / "pi.log"
    assert not (log.exists() and "qc-judge" in log.read_text()), (
        f"an agent judge ran: {log.read_text()}"
    )
    rep = json.loads(Path(ls[-1].rpartition("; report ")[2]).read_text())
    assert rep["captures"] == [], rep
    assert "fallback" not in rep, rep
    c = json.loads(s.git(r, "show", f"HEAD:{STATUS}"))["criteria"]
    built = {"status": "built", "pr": 9, "record": a, "commit": head, "tests": ["tests/accept.sh"]}
    assert c["acceptance-a"] == built, c
    assert c["acceptance-b"] == {"status": "planned", "pr": None}, c


def plain_gate(s: Scratch) -> None:
    """Without claims the gate runs as before: green, the tagged tests too, no record."""
    world(s)
    g = gate(s)
    assert "qc capture" not in g.out, g.out
    assert records(s) == [], "a plain gate appended records"


def strict(s: Scratch) -> None:
    """A tagged criterion with no claims gate record at the judged head: insufficient evidence,
    never its demo or the fallback."""
    r, _ = captured(s)
    (r / "qc.toml").write_text(
        QC_TOML.replace(
            'covers = ["tests"]\nfixtures',
            'command = "echo DEMO-RAN"\ncovers = ["tests"]\nfixtures',
            1,
        )
    )
    s.git(r, "commit", "-qam", "a demo beside the tagged test")
    h2 = s.git(r, "rev-parse", "HEAD")
    q = qc(s, r, "9", "acceptance-a", want=2)
    want = f"missing: no claims gate record at {h2[:12]}: tagged {CASE.format('tests/accept.sh')}"
    assert want in q.out, q.out
    assert not re.search(r"DEMO-RAN|agent fallback|qc: demo ", q.out + q.err), q.out + q.err
    assert len(records(s)) == 2, "qc appended a record"


def partial(s: Scratch) -> None:
    """acceptance-a gains a second tagged test: with no claims gate record at the head, and then
    with a record holding only part of its tagged cases (through the capture's store command),
    insufficient evidence naming what is missing, never the demo or the fallback."""
    r, _ = captured(s)
    (r / "tests" / "accept2.sh").write_text(
        "#!/usr/bin/env bash\n# criterion: demo#acceptance-a\necho RAN-accept2\n"
    )
    (r / "tests" / "accept2.sh").chmod(0o755)
    s.git(r, "add", "-A")
    s.git(r, "commit", "-qm", "a second tagged test")
    h3 = s.git(r, "rev-parse", "HEAD")

    def insufficient(missing: str) -> None:
        q = qc(s, r, "9", "acceptance-a", want=2)
        ls = q.out.splitlines()
        n = next(
            i for i, x in enumerate(ls) if x.startswith("INSUFFICIENT EVIDENCE acceptance-a: ")
        )
        assert missing in ls[n + 1], q.out
        assert not re.search(r"DEMO-RAN|agent fallback", q.out + q.err), q.out + q.err

    insufficient(f"missing: no claims gate record at {h3[:12]}")
    n = CASE.format("tests/accept.sh")
    phases = {w: {"outcome": "passed", "why": ""} for w in ("setup", "call", "teardown")}
    session = {
        "claims": ["demo#acceptance-a"],
        "plan": {n: {"criteria": ["demo#acceptance-a"], "source": "tests/accept.sh"}},
        "reports": {n: {"phases": phases, "output": "RAN-accept\n", "seconds": 0.1}},
        "notes": {
            n: {
                "command": ["tests/accept.sh"],
                "ran": True,
                "exit": 0,
                "said": "RAN-accept",
                "sandbox": {"proof": ["ok"]},
                "shots": [],
            }
        },
        "head_at_start": h3,
        "clean_at_start": True,
        "argv": ["-n", "2"],
        "tier": "full",
        "exit": 0,
    }
    (s.root / "session.json").write_text(json.dumps(session))
    out = s.run(
        [kit("octo-feather-qc"), "--capture-store", str(s.root / "session.json")], cwd=r
    ).out
    assert "1 case(s): tests/accept.sh passed" in out, (
        f"the store did not record the session: {out}"
    )
    insufficient(
        f"missing: case {CASE.format('tests/accept2.sh')} tagged at {h3[:12]}, not in the record"
    )


def metadata_only(s: Scratch) -> None:
    """Format 2: an entry without a command is per-criterion metadata, never a demo. acceptance-b,
    its tagged test gone and its entry holding only covers, has neither a record nor a demo:
    insufficient evidence naming that it has neither, nothing run (quality spec #qc-fallback)."""
    r = world(s)
    s.git(r, "rm", "-q", "tests/skip.sh")
    (r / "qc.toml").write_text(
        'format = 2\n[entry]\ncommand = "true"\n[services]\n[fixture]\n[values]\n'
        '[demo."demo#acceptance-b"]\ncovers = ["tests"]\n'
    )
    s.git(r, "commit", "-qam", "acceptance-b: metadata only")
    q = qc(s, r, "9", "acceptance-b", want=2)
    assert not re.search(r"KeyError|qc: demo |qc sandbox", q.err), q.err
    ls = q.out.splitlines()
    n = next(i for i, x in enumerate(ls) if x.startswith("INSUFFICIENT EVIDENCE acceptance-b: "))
    want = [
        "  missing: no tagged acceptance test and no declared demo",
        "  evidence incomplete; decision none; record none",
    ]
    assert ls[n + 1 : n + 3] == want, q.out


def artifacts_missing(s: Scratch) -> None:
    """Declared artifacts a run did not leave: insufficient evidence naming each, the tagged test's
    (its claims gate) and the demo's, whose record names its fixtures and artifacts."""
    r = world(s)
    (r / "tests" / "accept.sh").write_text(
        ACCEPT.replace("mkdir -p out && echo a > out/a.txt\n", "")
    )
    s.git(r, "rm", "-q", "tests/skip.sh")
    demo_b = (
        '[demo."demo#acceptance-b"]\ncommand = "mkdir -p out && echo b > out/b.txt"\n'
        'covers = ["tests"]\nfixtures = ["seed"]\nartifacts = ["out/b.txt", "out/none.txt"]\n'
    )
    (r / "qc.toml").write_text(QC_TOML + demo_b)
    s.git(r, "commit", "-qam", "accept.sh leaves no out/a.txt; acceptance-b a demo")
    gate(s, claims="demo#acceptance-a")
    q = qc(s, r, "9", "acceptance-a", "acceptance-b", want=2)
    for cid, f in (("a", "out/a.txt"), ("b", "out/none.txt")):
        ls = q.out.splitlines()
        n = next(
            i for i, x in enumerate(ls) if x.startswith(f"INSUFFICIENT EVIDENCE acceptance-{cid}: ")
        )
        assert f"missing: artifact {f} not left by the run" in ls[n + 1], q.out
    hb = s.git(r, "rev-parse", "HEAD")
    x = records(s, "--criterion", "demo#acceptance-b", "--commit", hb)[-1]
    e = json.loads((Path(x["dir"]) / "outputs" / "qc.expect.json").read_text())
    assert e == {
        "fixtures": ["seed"],
        "artifacts": [{"path": "out/b.txt", "left": True}, {"path": "out/none.txt", "left": False}],
    }, e


OTHER = "docs/specs/other.status.json"
TWIN = "docs/specs/twin.status.json"


def spec_as(r: Path, s: Scratch, stem: str, anchors: dict[str, str]) -> None:
    """docs/specs/STEM.spec.html in R: the demo spec with each anchor renamed by ANCHORS, then
    its status file initialized at that commit; both committed."""
    text = (r / "docs" / "specs" / "demo.spec.html").read_text()
    for old, new in anchors.items():
        text = text.replace(old, new)
    (r / "docs" / "specs" / f"{stem}.spec.html").write_text(text)
    s.git(r, "add", "-A")
    s.git(r, "commit", "-qm", f"spec {stem}")
    short = s.git(r, "rev-parse", "--short", "HEAD")
    s.run([kit("octo-feather-spec-status"), "init", f"docs/specs/{stem}.spec.html", short], cwd=r)
    s.git(r, "add", "-A")
    s.git(r, "commit", "-qm", f"status {stem}")


def build_two(p: Scratch) -> None:
    """The target with a second spec, other (acceptance-c, acceptance-d), acceptance-c tagged on
    tests/other.sh; its full gate told claims in both specs; its output in gate.json."""
    r = world(p)
    (r / "tests" / "other.sh").write_text(
        "#!/usr/bin/env bash\n# criterion: other#acceptance-c\necho RAN-other\n"
    )
    (r / "tests" / "other.sh").chmod(0o755)
    spec_as(r, p, "other", {"acceptance-a": "acceptance-c", "acceptance-b": "acceptance-d"})
    g = gate(p, claims="demo#acceptance-a demo#acceptance-b other#acceptance-c")
    (p.root / "gate.json").write_text(
        json.dumps({"rc": g.rc, "out": g.out, "head": p.git(r, "rev-parse", "HEAD")})
    )


def two_specs(s: Scratch) -> None:
    """One full gate claiming criteria of two specs, then one qc run naming both status files:
    each id judged from that gate's record, not rerun, no demo, no judge, the store unchanged; one
    report per spec; the new head's only change both status files, in one commit (passed built,
    the insufficient one planned)."""
    r = world(s, "oe-two")
    g = json.loads((s.root / "gate.json").read_text())
    assert g["rc"] == 0, f"capturing gate: exit {g['rc']}: {g['out']}"
    head = g["head"]
    ids = dict(
        re.findall(rf"^qc capture: (\w+#acceptance-[abc]): record ({RID})", g["out"], re.MULTILINE)
    )
    assert sorted(ids) == ["demo#acceptance-a", "demo#acceptance-b", "other#acceptance-c"], g["out"]
    q = qc(s, r, OTHER, "7", "acceptance-a", "acceptance-b", "acceptance-c", want=2)
    ls = q.out.splitlines()
    for i, cid, verdict, state in (
        ("acceptance-a", "demo#acceptance-a", "PASS", "complete"),
        ("acceptance-b", "demo#acceptance-b", "INSUFFICIENT EVIDENCE", "incomplete"),
        ("acceptance-c", "other#acceptance-c", "PASS", "complete"),
    ):
        n = next(k for k, x in enumerate(ls) if x.startswith(f"{verdict} {i}: "))
        want = f"  evidence {state}; decision tagged test assertions; record {ids[cid]}"
        assert want in ls[n + 1 : n + 4], q.out
        if verdict == "PASS":
            assert f"in the gate's run at {head[:12]}, not rerun" in ls[n + 1], q.out
    assert len(records(s)) == 3, "qc reran something"
    assert not re.search(r"agent fallback|qc: demo ", q.err), q.err
    log = s.root / "pi.log"
    assert not (log.exists() and "qc-judge" in log.read_text()), log.read_text()
    reps = [
        json.loads(Path(x.rpartition("; report ")[2]).read_text())
        for x in ls
        if x.startswith("qc: ") and "; report " in x
    ]
    by = {rep["spec"]: [x["id"] for x in rep["results"]] for rep in reps}
    assert by == {"demo": ["acceptance-a", "acceptance-b"], "other": ["acceptance-c"]}, by
    assert s.git(r, "rev-list", "--count", f"{head}..HEAD") == "1", "want one commit"
    changed = s.git(r, "diff", "--name-only", head, "HEAD").splitlines()
    assert sorted(changed) == [STATUS, OTHER], changed
    demo = json.loads(s.git(r, "show", f"HEAD:{STATUS}"))["criteria"]
    other = json.loads(s.git(r, "show", f"HEAD:{OTHER}"))["criteria"]
    for row, rid, test in (
        (demo["acceptance-a"], ids["demo#acceptance-a"], "tests/accept.sh"),
        (other["acceptance-c"], ids["other#acceptance-c"], "tests/other.sh"),
    ):
        assert row == {
            "status": "built",
            "pr": 7,
            "record": rid,
            "commit": head,
            "tests": [test],
        }, row
    assert demo["acceptance-b"] == {"status": "planned", "pr": None}, demo
    assert other["acceptance-d"] == {"status": "planned", "pr": None}, other


def ids_refused(s: Scratch) -> None:
    """Several status files: an id in none of them, or in two (twin, the demo spec's copy), is a
    usage error naming it, before any capture or collection: no record, no report, no commit."""
    r = world(s)
    spec_as(r, s, "twin", {})
    head = s.git(r, "rev-parse", "HEAD")
    for args, said in (
        ((TWIN, "7", "acceptance-z"), f"not in {STATUS} nor {TWIN}: acceptance-z"),
        (
            (TWIN, "7", "acceptance-a"),
            f"in more than one named status file: acceptance-a ({STATUS} {TWIN})",
        ),
    ):
        q = qc(s, r, *args, want=64)
        assert said in q.err, q.err
        assert not re.search(r"collecting|qc: demo |qc capture|qc: github", q.err), q.err
    assert s.git(r, "rev-parse", "HEAD") == head, "a refused run committed"
    assert s.git(r, "status", "--porcelain") == "", "a refused run left changes"
    assert records(s) == [], "a refused run captured"
    assert reports(s, head) == [], "a refused run wrote a report"


if __name__ == "__main__":
    main(
        two_specs,
        ids_refused,
        claims_refused,
        capture,
        judged_from_records,
        plain_gate,
        strict,
        partial,
        metadata_only,
        artifacts_missing,
    )
