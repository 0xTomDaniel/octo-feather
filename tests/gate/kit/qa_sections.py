"""The factory-evals test's sections, one scenario each (#506, #998): each tests/qa.sh and
tests/qa-*.sh gate item runs one as this file's command, so the items keep their ids and kinds, and
each item's header lists the facts its scenario proves. Every scenario runs scripts/octo-feather-qa
and scripts/check-evals as commands on the box of testkit/qa_box.py (a Qa: its docstring names the
stand-ins). A failed fact fails naming it, with the run's output."""

# ruff: noqa: E501
# (each case, edit and expected output line kept whole, verbatim from the item it was, so a reader
# greps it as the run prints it)
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from testkit import ROOT, Scratch, main
from testkit import qa_box as data
from testkit.jsonwalk import at, keys, seq
from testkit.qa_box import (
    C,
    Case,
    Cases,
    Q,
    Qa,
    after,
    cases,
    count,
    dump,
    edit,
    fail,
    grep,
    has,
    ic,
    lines,
    load,
    outputs,
    skip_on_macos,
    squeeze,
    steps,
    suite,
    texts,
    tree,
)

if TYPE_CHECKING:
    from pathlib import Path


def say(line: str) -> None:
    sys.stdout.write(line + "\n")


def note(line: str) -> None:
    sys.stderr.write(f"qa test: {line}\n")


def qa(s: Scratch) -> None:
    """tests/qa.sh."""
    q, t = Qa(s), s.root
    # The kit's own suites are well formed.
    if q.cmd(C)[0]:
        fail("kit evals/ fails its shape check")
    every_case(q)
    artifacts(q)
    selection(q)
    coverage(q)

    # A failed sandbox proof (raw herdr reaches a live session) is a FAIL; the case never runs.
    out = q.run(1, Q, "--evals", str(t / "evals"), "--case", "reads", env={"FAKE_HERDR_LEAK": "1"})
    if not grep(
        "sandbox: proof failed, case not run: .*FAIL live Herdr unreachable",
        q.line("FAIL", "reads"),
    ):
        fail(f"proof failure not a FAIL: {out}")
    if (q.last() / "trig" / "reads" / "transcript.jsonl").exists():
        fail("case ran after a failed proof")

    # Inside a check run (marker set) it refuses before any case: 70.
    out = q.run(70, Q, "--evals", str(t / "evals"), env={"OCTO_FEATHER_CHECK_RUN": '{"just":1}'})
    if grep("qa: run ", out):
        fail(f"a case started inside a check run: {out}")
    say(
        "qa: ok (PASS/FAIL per case with deciding facts, exit 1/0, train and held-out scores, "
        "--sample, role-skill coverage ({tracker} resolved per fixture), --suite/--case, "
        "artifacts, sandbox proof failure fails, refused in a check run)"
    )


def every_case(q: Qa) -> None:
    """tests/qa.sh: one line per case naming its deciding facts, exit 1 on a failure, the scores."""
    t = q.t
    # Every case: one line each, facts named; any failure exits 1.
    out = q.run(1, Q, "--evals", str(t / "evals"))
    if not grep(
        r"skill_read tdd: loaded at tool call 2 of 2 (read .*/tdd/SKILL.md)",
        q.line("PASS", "reads"),
    ):
        fail(f"reads: deciding fact not named: {out}")
    if not grep("skill_not_read tdd: loaded at tool call 2", q.line("FAIL", "near")):
        fail(f"near: deciding fact not named: {out}")
    quiet = "skill_not_read tdd: no load of tdd/SKILL.md (its full content in a tool result) in 1 tool calls"
    if not grep(quiet, q.line("PASS", "quiet")):
        fail(f"quiet: deciding fact not named: {out}")
    # linger stopped once decided, crash's dead pi a FAIL: their grading, test_qa_grading.py.
    if not grep("qc sandbox: ok   writable persistent paths: none", out):
        fail(f"no sandbox proof printed: {out}")
    if not grep("qa: 3/5 passed", out):
        fail(f"no summary line: {out}")
    # Train (reads, quiet, crash) and held-out (near, linger) scored apart, after every case line,
    # before the summary.
    scored = lines(r"^(PASS|FAIL) |^qa: (train|held-out) score|^qa: [0-9]+/", out).splitlines()[-3:]
    want = ["qa: train score 2/3 passed", "qa: held-out score 1/2 passed", "qa: 3/5 passed"]
    if [re.sub(r" \(run .*", "", x) for x in scored] != want:
        fail(f"score lines missing or out of order: {out}")


def selection(q: Qa) -> None:
    """tests/qa.sh: --suite/--case selection and a stratified, deterministic --sample."""
    t = q.t
    # Selection: --case and --suite; all selected pass: exit 0. Unknown names: 64.
    out = q.run(0, Q, "--evals", str(t / "evals"), "--case", "reads", "--case", "quiet")
    if len(lines(r"^(PASS|FAIL) ", out).splitlines()) != 2:
        fail(f"--case selected the wrong cases: {out}")
    q.run(64, Q, "--evals", str(t / "evals"), "--suite", "nope")
    q.run(64, Q, "--evals", str(t / "evals"), "--case", "nope")
    q.run(64, Q, "--evals", str(t / "evals"), "--sample", "0")

    # --sample 2: one should and one should-not, one train and one held-out, named before the
    # run; the same picks twice.
    def sampled() -> str:
        got = lines("^qa: sample ", q.out)
        if not got:
            fail(f"no sample line: {q.out}")
        return got

    out = q.run(1, Q, "--evals", str(t / "evals"), "--sample", "2")
    s1 = sampled()
    if len(lines(r"^(PASS|FAIL) ", out).splitlines()) != 2:
        fail(f"--sample 2 ran the wrong number of cases: {out}")
    for w in ("should_trigger true", "should_trigger false", ", train)", ", held-out)"):
        if w not in s1:
            fail(f"sample not stratified, no '{w}': {s1}")
    if not grep(r"^qa: sample 2 of 5 (seed ", s1):
        fail(f"sample line does not say its seed and size: {s1}")
    if not grep("^qa: train score 1/1", out):
        fail(f"no train score in a sample: {out}")
    q.run(1, Q, "--evals", str(t / "evals"), "--sample", "2")
    if sampled() != s1:
        fail(f"--sample not deterministic: {s1} vs {sampled()}")


def artifacts(q: Qa) -> None:
    """tests/qa.sh: per-case and per-run artifacts outside the repo; the prompt's content."""
    # Artifacts outside the repo, per case and per run; the prompt's content (rule: schema.md,
    # Layout).
    d = q.last()
    c = d / "trig" / "reads"
    for f in (
        "prompt.md",
        "input.json",
        "transcript.jsonl",
        "stderr.txt",
        "sandbox.json",
        "grading.json",
        "result.json",
    ):
        if not (c / f).exists():
            fail(f"artifact {f} missing")
    if not (d / "summary.json").stat().st_size:
        fail("no summary.json")
    prompt, inp = (c / "prompt.md").read_text(), (c / "input.json").read_text()
    if "STUB-READ-TDD" not in prompt or "skill_read" in prompt + inp:
        fail("prompt or input leaks the expectations")
    argv = [str(x) for x in seq(at(load_line(c / "transcript.jsonl"), "argv"))]
    a = " ".join(argv)
    assert "--mode json" in a, a
    assert "--session-dir /tmp/qa-session" in a, a
    assert "-p" in argv, a  # never ~/.pi sessions
    assert "--no-skills" in argv, "not launched through pi-role's implementer"
    assert any(x.endswith("/tdd") for x in argv), "not launched through pi-role's implementer"
    r = load(c / "result.json")
    assert at(r, "verdict") == "PASS", r
    assert at(r, "model") == "stub/stub-model", r
    g = load(c / "grading.json")
    assert at(g, "facts", 0, "status") == "pass", g
    sb = load(c / "sandbox.json")
    assert at(sb, "proof"), sb
    assert "agents_started" in keys(sb), sb
    sm = load(d / "summary.json")
    assert (at(sm, "passed"), at(sm, "total")) == (3, 5), sm
    assert at(sm, "scores") == {
        "train": {"passed": 2, "total": 3},
        "held-out": {"passed": 1, "total": 2},
    }, sm


def load_line(p: Path) -> object:
    """P's first line, a JSON value."""
    return load_text(p.read_text().splitlines()[0])


def load_text(x: str) -> object:
    v: object = json.loads(x)
    return v


def coverage(q: Qa) -> None:
    """Coverage (rule: schema.md, Coverage): the kit's suite passes; then one held-out near miss
    dropped; {tracker} on a role's skills line resolved per fixture."""
    t = q.t
    tree(ROOT / "evals", t / "kit-evals")
    drop(
        t / "kit-evals" / "skill-triggers",
        'x["role"] == "implementer" and not x["should_trigger"] and x["split"] == "held-out" '
        'and e[x["id"]]["facts"] == [{"fact": "skill_not_read", "skill": "pull"}]',
        "no held-out near miss for implementer pull in the kit suite",
    )
    out = q.run(1, C, str(t / "kit-evals"))
    if (
        "skill-triggers: role implementer skill pull: no case for should_trigger false split held-out"
        not in out
    ):
        fail(f"coverage gap not named: {out}")
    # {tracker} on a role's skills line (rule: schema.md, Coverage): fixtures with no
    # .octo-feather.toml, one naming linear, one naming an unknown tracker.
    tree(ROOT / "evals", t / "trk-evals")
    drop(
        t / "trk-evals" / "skill-triggers",
        'x["role"] == "supervisor" and x["should_trigger"] and x["split"] == "train" '
        'and e[x["id"]]["facts"] == [{"fact": "skill_read", "skill": "github-issues"}]',
        "no train should case for supervisor github-issues in the kit suite",
    )
    out = q.run(1, C, str(t / "trk-evals"))
    if (
        "skill-triggers: role supervisor skill github-issues: no case for should_trigger true split train;"
        not in out
    ):
        fail(f"a {{tracker}} gap not named as github-issues: {out}")
    if count(": role .* skill ", out) != 1:
        fail(f"only the dropped {{tracker}} pair should be missing: {out}")
    tree(ROOT / "evals", t / "lin-evals")
    toml = t / "lin-evals" / "fixtures" / "lane-mini" / ".octo-feather.toml"
    toml.write_text('tracker = "linear"\n')
    out = q.run(1, C, str(t / "lin-evals"))
    for r in ("director", "implementer", "supervisor"):
        if (
            f"skill-triggers: role {r} skill linear: no case for should_trigger true split train"
            not in out
        ):
            fail(f"a fixture's linear tracker did not add {r} linear: {out}")
    if grep(r"skill {tracker}\|skill github-issues:", out):
        fail(f"{{tracker}} left unresolved, or github-issues dropped: {out}")
    toml.write_text('tracker = "jira"\n')
    out = q.run(1, C, str(t / "lin-evals"))
    if (
        "fixtures/lane-mini/.octo-feather.toml: field tracker: 'jira' has no kit tracker skill"
        not in out
    ):
        fail(f"unknown tracker not named: {out}")


def drop(d: Path, cond: str, none: str) -> None:
    """D's cases (and their expectations) for which COND holds, Python over case x and
    expectations e, removed; none of them fails NONE."""
    code = (
        "c = c_; gone = [x['id'] for x in c if " + cond + "]\n"
        f"assert gone, {none!r}\n"
        "c_ = [x for x in c if x['id'] not in gone]; e_ = {k: v for k, v in e.items() if k not in gone}\n"
    )
    ns: dict[str, object] = {
        "c_": load(d / "cases.json"),
        "e": load(d / "reference" / "expectations.json"),
    }
    ns["e_"] = ns["e"]
    exec(code, ns)  # noqa: S102  # the item's literal selection, as it was
    dump(d / "cases.json", ns["c_"])
    dump(d / "reference" / "expectations.json", ns["e_"])


def kit_repo(q: Qa, *, c0: bool) -> tuple[Path, list[str]]:
    """A throwaway kit repo under HOME (this kit's tracked files): with C0, c0 no implementer role
    first; then c1 the implementer not listing tdd, c2 the head. Its scripts/octo-feather-qa and
    its commits. Tracked files only, as the other kit-copy tests: the live tree's .venv,
    node_modules and caches change under a parallel gate, and tar failed reading them (#506)."""
    k = q.home / "src" / "kit"
    k.mkdir(parents=True)
    ls = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True)  # noqa: S607
    for rel in filter(None, ls.stdout.decode().split("\0")):
        src = ROOT / rel
        if src.is_file() or src.is_symlink():
            (k / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, k / rel, follow_symlinks=False)

    def gk(*a: str) -> str:
        g = ["git", "-C", str(k), "-c", "user.name=t", "-c", "user.email=t@t.invalid"]
        return q.sh(*g, "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", *a)

    im = k / "agents" / "implementer.md"
    head = im.read_text()
    shas: list[str] = []
    gk("init", "-q", "-b", "main")
    if c0:
        im.unlink()
        gk("add", "-A")
        gk("commit", "-qm", "c0")
        shas.append(gk("rev-parse", "HEAD"))
    im.write_text(re.sub(r"^skills:(.*), tdd,", r"skills:\1,", head, flags=re.MULTILINE))
    text = im.read_text()
    if (c0 and not grep("^skills:", text)) or grep("^skills:.*tdd", text):
        fail("c1 still lists tdd")
    gk("add", "-A")
    gk("commit", "-qm", "c1")
    shas.append(gk("rev-parse", "HEAD"))
    im.write_text(head)
    gk("commit", "-qam", "c2")
    shas.append(gk("rev-parse", "HEAD"))
    # srt, the qc sandbox, runs from the running kit's node_modules
    (k / "node_modules").symlink_to(ROOT / "node_modules")
    with (k / ".git" / "info" / "exclude").open("a") as f:
        f.write("/node_modules\n")
    return k / "scripts" / "octo-feather-qa", shas


def baseline(s: Scratch) -> None:
    """tests/qa-baseline.sh: the command's wiring of --baseline (a case on both kits, its cost and
    the table: test_qa_stored.py, test_qa_baseline)."""
    q, t = Qa(s), s.root
    k, (c1, c2) = kit_repo(q, c0=False)
    kq, ev = str(k), str(t / "evals")
    want = data.baseline(c1, c2)
    # Baseline c1 beside the head c2: one evaluation naming the baseline, runs interleaved, exit 0.
    out = q.run(0, kq, "--evals", ev, "--case", "reads", "--runs", "2", "--baseline", c1[:9])
    q.check([w for w in want["compared"] if w.text.startswith(("^qa: run ", "; baseline kit "))])
    if (
        re.findall(r"^  (?:baseline|current) run [0-9]/2: (?:PASS|FAIL)", out, re.MULTILINE)
        != data.INTERLEAVED
    ):
        fail(f"runs not interleaved: {out}")
    # The exit status follows the current kit only: the change side c1 fails beside a passing
    # baseline c2.
    q.run(1, kq, "--evals", ev, "--case", "reads", "--kit-ref", c1, "--baseline", c2)
    q.check(want["reverse"])
    # An unknown baseline: 64 before any run.
    q.run(64, kq, "--evals", ev, "--case", "reads", "--baseline", "no-such-ref")
    q.check(want["unknown"])
    q.run(64, kq, "--evals", ev, "--baseline")
    say(
        "qa-baseline: ok (baseline beside current in one interleaved evaluation, exit by the "
        "current kit, unknown baseline 64; cost and the table: test_qa_stored.py)"
    )


def before_tool(s: Scratch) -> None:
    """tests/qa-before-tool.sh."""
    q, t = Qa(s), s.root
    _, shapes = data.before_tool(q)  # its cases' grading: test_qa_grading.py
    # Shape (schema.md, Facts, Before targets).
    for code, refusal in shapes:
        q.bad(code, refusal, t / "tb-good", "tb")
    say("qa-before-tool: ok (tool_called_before and edit_under shape refusals)")


def bench(s: Scratch) -> None:
    """tests/qa-bench.sh."""
    q, t = Qa(s), s.root
    q.jg()
    jg = str(t / "jg")
    q.run(0, Q, "--evals", jg)

    def jl(w: str) -> None:
        if w not in q.out:
            fail(f"bench: no '{w}' in: {q.out}")

    jl(
        "bench jb: question q-ab, labels a, b; 15 cases (train 12, held-out 3); every answer is a model judgment"
    )
    jl(
        "bench jb: classifiers available (12): stub/token, stub/first, stub/broken, stub/cheap-train, stub/cheap-total, stub/~x/y, stub/p/q-latest, stub/p/q-1.2, stub/x-latest:free, stub/p/q-1.2:free, stub/yesno, stub/ynr"
    )
    jl(
        "bench jb: skipped: moving alias (3): stub/~x/y, stub/x-latest:free, stub/p/q-1.2:free; never called, ruling (classifiers.json owner): stub ruling, tests/qa.sh"
    )
    jl(
        "bench jb: skipped: yes/no only stub/ynr; never called, ruling (classifiers.json yes_no_only): stub yes/no ruling; provider error (stub run): stub bool only (400)"
    )
    jl(
        "bench jb: unclassified id (1): stub/cheap-total; benched (scored where it answered), in no list of classifiers.json"
    )
    # yesno, not listed, answers only bool questions (rule: schema.md, Bench, Unavailable); a
    # question not a choice kills the stub run.
    jl(
        'unavailable stub/yesno: listed but answered no case: Stub API error (400): {"message":"stub accepts only bool questions (question "q")"}'
    )
    if has(r"^  stub/(yesno|ynr) |yes/no only stub/yesno|unavailable stub/ynr", q.out):
        fail(f"bench: a yes/no-only classifier scored, or skipped unlisted: {q.out}")

    tables(q)
    # broken's provider error, over 400 characters (rule: schema.md, Bench, Unavailable).
    down = "stub provider down " + "x" * 400 + " end"
    if f"unavailable stub/broken: listed but answered no case: {down}" not in q.out.splitlines():
        fail(f"bench: broken's error not whole: {q.out}")
    # The kit's model (judgment-model.json: stub/first) beside the question's best-scoring
    # classifier, token (schema.md, Bench).
    kb = [
        squeeze(x)
        for x in after(r"^KIT MODEL BESIDE THE BEST \(best: highest train accuracy", 3, q.out)[-2:]
    ]
    if kb != [
        " kit stub/first 0.500 1.000 0.333 1.333 0.015000",
        " best stub/token 0.750 0.380 0.333 0.880 0.015000",
    ]:
        fail(f"bench: kit beside best wrong: {q.out}")
    jl(
        "kit model stub/first (judgment-model.json): proposed threshold (for the director to accept; until met, the judge stays advisory): held-out accuracy >= 0.254 and held-out brier <= 1.591"
    )
    jl(
        "held-out now: accuracy 0.333 (1/3 of 3), brier 1.333, ece 0.667: meets the proposed threshold"
    )
    if grep("^chosen", q.out):
        fail(f"bench: a per-question choice named: {q.out}")
    jl("DONE bench jb: kit model stub/first, best stub/token")
    if not grep("qc sandbox: ok   live Herdr unreachable", q.out):
        fail(f"bench: not run in the qa sandbox: {q.out}")
    bench_files(q)
    spend(q)
    tail(q)
    say(
        "qa-bench: ok (judgment bench: per classifier accuracy/calibration/cost train and "
        "held-out apart, classifiers.json lists applied (schema.md, Bench; catalogue and "
        "--classifier; moving alias and yes/no only skipped, never called), a classifier that "
        "cannot accept the question's form listed unavailable with the real question's provider "
        "error (no probe), one answering some cases scored, unavailable named, the kit's model "
        "beside the best (train) and its threshold, --classifier, best's tie-break, a kit model "
        "unscored fails, a dead bench command fails, spend recorded)"
    )


def bench_files(q: Qa) -> None:
    """tests/qa-bench.sh: the bench's artifacts, the expectations kept from the classifier side."""
    d = q.last()
    jb = d / "jb"
    for f in (
        "input.json",
        "extension.js",
        "stdout.txt",
        "stderr.txt",
        "sandbox.json",
        "answers.json",
        "bench.json",
        "report.txt",
    ):
        if not (jb / f).exists():
            fail(f"bench artifact {f} missing")
    if any(
        "SECRET-REASON" in (jb / f).read_text()
        for f in ("input.json", "extension.js", "stdout.txt")
    ):
        fail("bench: the expectations reached the classifier side")
    bench_artifacts(d)


def tables(q: Qa) -> None:
    """tests/qa-bench.sh: the TRAIN and HELD-OUT tables."""

    def table(head: str, n: int) -> list[str]:
        return [squeeze(x) for x in after(head, n, q.out) if re.search(r"^  stub/", x)]

    train = [
        " stub/token 12/12 9 0.750 0.380 0.050 0.015000 0",
        " stub/cheap-total 12/12 6 0.500 1.000 0.500 0.024000 0",
        " stub/cheap-train 12/12 6 0.500 1.000 0.500 0.042000 0",
        " stub/first 12/12 6 0.500 1.000 0.500 0.015000 0",
        " stub/p/q-1.2 12/12 6 0.500 1.000 0.500 0.015000 0",
        " stub/p/q-latest 12/12 6 0.500 1.000 0.500 0.015000 0",
    ]
    if table(r"^TRAIN \(12 cases", 7) != train:
        fail(f"bench: train table wrong: {q.out}")
    held = [
        " stub/token 3/3 1 0.333 0.880 0.467 0.015000 0",
        " stub/cheap-total 3/3 1 0.333 1.333 0.667 0.024000 0",
        " stub/cheap-train 3/3 1 0.333 1.333 0.667 0.042000 0",
        " stub/first 3/3 1 0.333 1.333 0.667 0.015000 0",
        " stub/p/q-1.2 3/3 1 0.333 1.333 0.667 0.015000 0",
        " stub/p/q-latest 3/3 1 0.333 1.333 0.667 0.015000 0",
    ]
    if table(r"^HELD-OUT \(3 cases", 7) != held:
        fail(f"bench: held-out table wrong: {q.out}")


def bench_artifacts(d: Path) -> None:
    """The bench run's answers, summary and bench record, and its one pi's argv."""
    a = seq(at(load(d / "jb" / "answers.json"), "answers"))
    assert len(a) == 120, a[:2]
    assert all(str(at(x, "judgment")).startswith("model judgment") for x in a), a[:2]
    sm = load(d / "summary.json")
    assert at(sm, "benches", 0, "best", "model") == "stub/token", sm
    assert at(sm, "benches", 0, "verdict") == "DONE", sm
    k = at(sm, "benches", 0, "kit_model")
    assert at(k, "model") == "stub/first", k
    assert at(k, "scored"), k
    assert at(k, "threshold") == {"accuracy_min": 0.254, "brier_max": 1.591}, k
    assert at(k, "held_out") == {"accuracy": 0.333, "brier": 1.333}, k
    assert "choice" not in keys(at(sm, "benches", 0)), at(sm, "benches", 0)
    # per-model cost and the run total (token, first, p/q-1.2, p/q-latest 0.015 each; cheap
    # 0.042 + 0.024)
    b = load(d / "jb" / "bench.json")
    models = seq(at(b, "models"))
    cost = {at(m, "model"): round(float(str(at(m, "cost_usd"))), 6) for m in models}
    assert cost["stub/cheap-train"] == 0.042, b
    assert round(float(str(at(b, "cost_usd"))), 6) == 0.126, b
    skipped = seq(at(b, "skipped"))
    assert skipped == ["stub/~x/y", "stub/x-latest:free", "stub/p/q-1.2:free", "stub/ynr"], b
    assert {"stub/p/q-1.2", "stub/p/q-latest"} <= set(map(str, seq(at(b, "benched")))), b
    yn = {
        "stub/ynr": {
            "ruling": "stub yes/no ruling",
            "error": "stub bool only (400)",
            "evidence": "stub run",
        }
    }
    assert at(b, "skipped_yes_no_only") == yn, b
    assert at(b, "skipped_ruling") == "stub ruling, tests/qa.sh", b
    assert at(b, "unclassified") == ["stub/cheap-total"], b
    assert "stub/cheap-total" in seq(at(b, "benched")), b
    called = {at(x, "model") for x in a} | {at(m, "model") for m in models}
    assert not set(skipped) & called, b
    y = next(m for m in models if at(m, "model") == "stub/yesno")
    err = 'Stub API error (400): {"message":"stub accepts only bool questions (question "q")"}'
    assert "skipped_yes_no" not in keys(b), (b, y)
    assert not at(y, "available"), (b, y)
    assert at(y, "first_error") == err, (b, y)
    # No agent: one pi, no tools, no chat model, no session; only the bench extension loaded.
    argv = [str(x) for x in seq(at(load_line(d / "jb" / "stdout.txt"), "argv"))]
    for x in ("--no-tools", "--no-extensions", "--no-session", "--no-skills", "--no-mcp"):
        assert x in argv, (x, argv)
    assert "--model" not in argv, argv
    assert "--mode" not in argv, argv
    assert "--tools" not in argv, argv
    assert argv[argv.index("-p") + 1].startswith("/octo-feather-bench "), argv


def spend(q: Qa) -> None:
    """spec spend#acceptance-spend-bench: 8 benched x 15 cases = 120 calls, $0.126 as bench.json;
    broken and yesno (30) report no usage, the 90 others 1 in, 1 out each. spec
    spend#rule-write-fails, a directory in the ledger's place: the same report and exit."""
    t, d = q.t, q.last()
    rc, spent = q.cmd(str(ROOT / "scripts" / "octo-feather-lane"), "spend")
    if rc:
        fail(f"spend failed: {spent}")
    if f"Spend ledger: {q.home}/.local/state/octo-feather/spend.jsonl (120 calls)" not in spent:
        fail(f"spend: not 120 calls: {spent}")

    def row(*a: str) -> None:  # TITLE KEY USD CALLS UNKNOWN IN OUT (tests/spend-out)
        rc, r = q.cmd(str(ROOT / "tests" / "spend-out"), "row", *a, stdin=spent + "\n")
        if rc:
            fail(f"spend: {r} in: {spent}")

    row("purpose", "bench", "0.126000", "120", "30", "90", "90")
    row("lane", "(no lane)", "0.126000", "120", "30", "90", "90")
    row("day (UTC)", datetime.now(UTC).strftime("%Y-%m-%d"), "0.126000", "120", "30", "90", "90")
    row("model", "stub/cheap-train", "0.042000", "15", "0", "15", "15")
    row("model", "stub/cheap-total", "0.024000", "15", "0", "15", "15")
    row("model", "stub/token", "0.015000", "15", "0", "15", "15")
    row("model", "stub/broken", "0.000000", "15", "15", "0", "0")
    row("model", "stub/yesno", "0.000000", "15", "15", "0", "0")
    ledger = q.home / ".local" / "state" / "octo-feather" / "spend.jsonl"
    ledger.rename(t / "ledger")
    ledger.mkdir()
    q.run(0, Q, "--evals", str(t / "jg"))
    (q.last() / "jb" / "report.txt").rename(t / "report-unwritable")
    ledger.rmdir()
    (t / "ledger").rename(ledger)
    if (d / "jb" / "report.txt").read_bytes() != (t / "report-unwritable").read_bytes():
        fail("spend: an unwritable ledger changed the bench report")
    for w in ("DONE bench jb: kit model stub/first, best stub/token",
              "octo-feather-lane spend record: spend unrecorded (120 call(s), $0.126000 + 30 of unknown cost): cannot write "):  # fmt: skip
        if w not in q.out:
            fail(f"bench: no '{w}' in: {q.out}")


def tail(q: Qa) -> None:
    """--classifier, its aliases, best's tie-break, an unscored kit model, a partly answering
    classifier, a dead bench command."""
    t, jg = q.t, str(q.t / "jg")

    def jl(w: str) -> None:
        if w not in q.out:
            fail(f"bench: no '{w}' in: {q.out}")

    q.run(0, Q, "--evals", jg, "--classifier", "stub/first", "--classifier", "stub/nope")
    jl("bench jb: benched only --classifier stub/first, stub/nope (not available: stub/nope)")
    jl("DONE bench jb: kit model stub/first, best stub/first")
    # A --classifier naming a listed moving alias or yes/no only (rule: schema.md, Bench, Classes;
    # a call kills the stub run).
    cl = ["stub/p/q-latest", "stub/p/q-1.2:free", "stub/p/q-1.2", "stub/ynr"]
    q.run(0, Q, "--evals", jg, *[x for c in cl for x in ("--classifier", c)])
    jl(
        "bench jb: benched only --classifier stub/p/q-latest, stub/p/q-1.2:free, stub/p/q-1.2, stub/ynr"
    )
    jl("bench jb: skipped: yes/no only stub/ynr; never called")
    jl("bench jb: skipped: moving alias (1): stub/p/q-1.2:free; never called")
    if grep("unclassified id", q.out):
        fail(f"bench: an unclassified flag with every benched id pinned: {q.out}")
    if not has(r"^  kit +stub/first +not scored: not benched$", q.out):
        fail(f"bench: kit model not benched not shown: {q.out}")
    jl("DONE bench jb: kit model stub/first not scored (not benched), best stub/p/q-1.2")
    if grep("not available", q.out):
        fail(f"bench: a skipped alias named not available: {q.out}")
    b = load(q.last() / "jb" / "bench.json")
    ok = at(b, "skipped") == ["stub/p/q-1.2:free", "stub/ynr"] and at(b, "unclassified") == []
    if not (ok and at(b, "benched") == ["stub/p/q-latest", "stub/p/q-1.2"]):
        fail("bench: --classifier aliases not recorded skipped")
    # Best's tie-break (schema.md, Bench): cheap-train costs less on train, more in all.
    q.run(
        0, Q, "--evals", jg, "--classifier", "stub/cheap-total", "--classifier", "stub/cheap-train"
    )
    jl("DONE bench jb: kit model stub/first not scored (not benched), best stub/cheap-train")
    # The kit's model benched but unscored (schema.md, Bench: a bench FAILS) (broken: every case
    # refused; yesno: cannot accept the question's form, every case refused).
    jm = t / "jg" / "judgment-model.json"
    dump(jm, {"model": "stub/broken", "evidence": "evidence/jb.md"})
    q.run(1, Q, "--evals", jg)
    down = "stub provider down " + "x" * 400 + " end"
    jl(
        f"FAILED bench jb: the kit's judgment model stub/broken was not scored (answered 0 of 12 train cases, first error: {down})"
    )
    dump(jm, {"model": "stub/yesno", "evidence": "evidence/jb.md"})
    q.run(1, Q, "--evals", jg, "--classifier", "stub/yesno", "--classifier", "stub/first")
    jl(
        "FAILED bench jb: the kit's judgment model stub/yesno was not scored (answered 0 of 12 train cases, first error: Stub API error (400): "
    )
    shutil.copy(t / "jg-good" / "judgment-model.json", jm)
    # A classifier that answers some cases (rule: schema.md, Bench, Unavailable): first refuses
    # a STUB-REFUSE state.
    cj = t / "jg" / "jb" / "cases.json"
    edit(cj, "c[0]['state'] += ' STUB-REFUSE'", "c")
    q.run(1, Q, "--evals", jg, "--classifier", "stub/first")
    if not any(
        re.search(r"^  stub/first +11/12 ", x) for x in after(r"^TRAIN \(12 cases", 3, q.out)
    ):
        fail(f"bench: a partly answering classifier not scored: {q.out}")
    jl("errors stub/first: 1 case(s) unanswered, first: stub refused this state")
    if grep("unavailable stub/first", q.out):
        fail(f"bench: a partly answering classifier listed unavailable: {q.out}")
    shutil.copy(t / "jg-good" / "jb" / "cases.json", cj)
    # A pi that dies before the command prints its result: the bench fails, naming it.
    edit(cj, "c[0]['state'] += ' STUB-DIE'", "c")
    q.run(1, Q, "--evals", jg, "--classifier", "stub/first")
    jl("FAILED bench jb: the bench command printed no bench result:")
    jl("(pi exit 3)")


def declared(s: Scratch) -> None:
    """tests/qa-declared.sh: the dec suite's runs the watcher's timeout stops (suite timeout_s 8),
    through the command (the other dec cases: test_qa_grading.py)."""
    q = Qa(s)
    want = [w for w in data.declared(q) if w.line in ("FAIL dec/early", "FAIL dec/earlyrb")]
    q.run(1, Q, "--evals", str(s.root / "dec"), "--case", "early", "--case", "earlyrb")
    q.check(want)
    say(
        "qa-declared: ok (declared stopped early by the timeout, a skill_read_before target never reached fails)"
    )


def blob(q: Qa, data: bytes) -> str:
    """git's blob id of DATA (git hash-object --stdin)."""
    p = subprocess.run(
        ["git", "hash-object", "--stdin"],  # noqa: S607
        input=data,
        capture_output=True,
        check=True,
        env=q.s.env,
    )
    return p.stdout.decode().strip()


def upto(text: str) -> str:
    """TEXT's lines up to and with the first `===` (sed '/^===$/q')."""
    ls = text.splitlines()
    return "\n".join(ls[: ls.index("===") + 1] if "===" in ls else ls)


def past(text: str) -> str:
    """TEXT's lines after the first `===` (sed '1,/^===$/d')."""
    ls = text.splitlines()
    return "\n".join(ls[ls.index("===", 1) + 1 :] if "===" in ls[1:] else [])


def before(text: str) -> str:
    """TEXT's lines before the first `===` (sed '/^===$/,$d')."""
    ls = text.splitlines()
    return "\n".join(ls[: ls.index("===")] if "===" in ls else ls)


def fixture_base(s: Scratch) -> None:
    """tests/qa-fixture-base.sh."""
    q, t = Qa(s), s.root
    e = t / "fb"
    f = e / "fixtures"
    for p in (
        "fb/reference",
        "fixtures/root/tools",
        "fixtures/root/sub",
        "fixtures/mid/sub",
        "fixtures/over/sub",
        "fixtures/headover",
    ):
        (e / p).mkdir(parents=True)
    # root: a whole tree; mid over root, over over mid (a chain); headover over root. flat:
    # over's tree written out by hand, the oracle, in its own EVALS_DIR fe (why: schema.md,
    # Fixtures, cross-fixture duplicate).
    (f / "root" / "README.md").write_text("root\n")
    (f / "root" / "sub" / "keep.txt").write_text("base\n")
    (f / "root" / "sub" / "swap.txt").write_text("old\n")
    run_sh = f / "root" / "tools" / "run.sh"
    run_sh.write_text("#!/bin/sh\necho run\n")
    run_sh.chmod(run_sh.stat().st_mode | 0o111)
    (f / "root" / "link").symlink_to("README.md")
    sk = f / "root" / ".agents" / "skills" / "base-only" / "SKILL.md"
    sk.parent.mkdir(parents=True)
    sk.write_text("---\nname: base-only\ndescription: a base fixture skill\n---\n\nDo it.\n")
    dump(f / "mid" / ".eval-fixture.json", {"base": "root"})
    (f / "mid" / "sub" / "swap.txt").write_text("mid\n")
    (f / "mid" / "link").symlink_to("sub/keep.txt")
    dump(f / "over" / ".eval-fixture.json", {"base": "mid"})
    (f / "over" / "sub" / "new.txt").write_text("over\n")
    dump(f / "headover" / ".eval-fixture.json", {"base": "root"})
    (f / "headover" / "README.md").write_text("head\n")
    fe = t / "fe"
    (fe / "fb" / "reference").mkdir(parents=True)
    flat = fe / "fixtures" / "flat"
    shutil.copytree(f / "root", flat, symlinks=True)
    (flat / "link").unlink()
    shutil.copytree(f / "mid" / "sub", flat / "sub", symlinks=True, dirs_exist_ok=True)
    (flat / "link").symlink_to((f / "mid" / "link").readlink())
    shutil.copytree(f / "over" / "sub", flat / "sub", symlinks=True, dirs_exist_ok=True)
    suite(e, "fb", "stub based fixtures", 10, 120)
    shutil.copy(e / "fb" / "suite.json", fe / "fb")
    look = steps("Look.", [["bash", "git ls-tree -r main; echo ===; git ls-tree -r HEAD; ls -a"]])
    head = {"fixture": "headover", "branch": "hb", "message": "head"}
    seq_ = steps(
        "Look.",
        [
            [
                "bash",
                "git ls-tree -r main; echo ===; git ls-tree -r HEAD; echo ===; git ls-tree -r bb",
            ]
        ],
    )
    pull: list[object] = [{"fact": "skill_not_read", "skill": "pull"}]
    cs: Cases = [
        ({"id": "main", "role": "implementer", "fixture": "over", "task": look}, pull),
        ({"id": "head", "role": "implementer", "fixture": "root", "task": look, "head": head}, pull),
        ({"id": "seq", "role": "implementer", "fixture": "root", "task": seq_,
          "head": head | {"then": [{"fixture": "over", "message": "then"}]},
          "branches": [{"fixture": "mid", "branch": "bb", "message": "b"}]}, pull),
    ]  # fmt: skip
    cases(e / "fb", cs)
    cases(
        fe / "fb", [({"id": "flat", "role": "implementer", "fixture": "flat", "task": look}, pull)]
    )
    tree(e, t / "fb-good")

    case_repo(q, e, fe, f)
    trees(q, e, fe)
    materialized(q, e)
    say(
        "qa-fixture-base: ok (a based fixture chain materialized whole, exec bit and symlink "
        "kept, as the case repo's main, head, head.then and branches and in check-evals' fixture "
        "checks; --trees equal to the flat tree, a line per head.then and branches tree; missing, "
        "cyclic and malformed bases refused naming the fixture)"
    )


def case_repo(q: Qa, e: Path, fe: Path, f: Path) -> None:
    """tests/qa-fixture-base.sh: the case repo's main, head, head.then and branches as the based fixtures' trees."""
    # The case repo: main is over's whole tree, as flat's (git's own modes and blob ids, the
    # oracle); head commits headover.
    out = q.run(0, Q, "--evals", str(fe))
    if not has("^PASS fb/flat: ", out):
        fail(f"no PASS line for flat: {out}")
    df = q.last()
    out = q.run(0, Q, "--evals", str(e))
    for c in ("main", "head", "seq"):
        if not has(f"^PASS fb/{c}: ", out):
            fail(f"no PASS line for {c}: {out}")
    d = q.last()
    m, h = (
        texts(d / "fb" / "main" / "transcript.jsonl"),
        texts(d / "fb" / "head" / "transcript.jsonl"),
    )
    want = texts(df / "fb" / "flat" / "transcript.jsonl")
    if upto(m) != upto(want):
        fail(f"main is not over's whole tree: {m}  vs flat: {want}")
    if not (grep("^100755 blob .*\ttools/run.sh$", m) and grep("^120000 blob .*\tlink$", m)):
        fail(f"exec bit or symlink lost: {m}")
    if grep("eval-fixture", m + h):
        fail(f"the base file reached the case repo: {m} {h}")
    readme = blob(q, (f / "headover" / "README.md").read_bytes())
    if not grep(f"^100644 blob {readme}\tREADME.md$", past(h)):
        fail(f"head is not headover's tree over root: {h}")
    if not grep("\ttools/run.sh$", past(h)):
        fail(f"head lost root's files: {h}")

    then_branches(q, f, d, want)


def then_branches(q: Qa, f: Path, d: Path, want: str) -> None:
    """tests/qa-fixture-base.sh: head.then commits over's whole tree, branch bb mid's."""
    # head.then and branches (schema.md, Case): then commits over's whole tree, as flat's; branch
    # bb holds mid's tree.
    sq = texts(d / "fb" / "seq" / "transcript.jsonl")
    st = past(sq)
    bb = past(st)
    if before(st) != "\n".join(x for x in past(want).splitlines() if "\t" in x):
        fail(f"head.then is not over's whole tree: {sq}  vs flat: {want}")
    swap = blob(q, (f / "mid" / "sub" / "swap.txt").read_bytes())
    ok = grep(f"^100644 blob {swap}\tsub/swap.txt$", bb) and grep(
        "^100755 blob .*\ttools/run.sh$", bb
    )
    ok = (
        ok
        and grep(f"^120000 blob {blob(q, b'sub/keep.txt')}\tlink$", bb)
        and not grep("sub/new.txt", bb)
    )
    if not ok:
        fail(f"branch bb is not mid's tree over root: {sq}")


def trees(q: Qa, e: Path, fe: Path) -> None:
    """--trees (its form: schema.md, Fixtures)."""
    t = q.t
    out = q.run(0, C, "--trees", str(fe))
    flat = "\n".join(x.split(" ")[3] for x in lines("^fb flat fixture ", out).splitlines())
    out = q.run(0, C, "--trees", str(e))

    def sha(c: str, k: str) -> str:
        return "\n".join(x.split(" ")[3] for x in lines(f"^fb {c} {k} ", out).splitlines())

    then = sha("seq", r"head\.then\[0\]")
    if not (then and then == flat):
        fail(f"--trees: no head.then[0] line as flat: {out}")
    br = sha("seq", r"branches\[0\]")
    if not (br and br != sha("seq", "fixture")):
        fail(f"--trees: no branches[0] line: {out}")
    if not (sha("main", "fixture") and sha("main", "fixture") == flat):
        fail(f"--trees: over not hashed as flat: {out}")
    if not (sha("head", "head") and sha("head", "head") != sha("head", "fixture")):
        fail(f"--trees: no head tree line: {out}")
    edit(fe / "fb" / "cases.json", 'c[0]["fixture"] = {"repo": "kit", "commit": "a" * 40}', "c")
    out = q.run(0, C, "--trees", str(fe))
    if f"fb flat fixture history kit@{'a' * 40}" not in out.splitlines():
        fail(f"--trees: history not marked: {out}")
    tree(t / "fb-good", e)


def materialized(q: Qa, e: Path) -> None:
    """check-evals reads the materialized tree: a skill, test_write's pyproject and uv.lock only
    in root, graded on over; coverage's tracker; the refusals (schema.md, Fixtures)."""
    t, f = q.t, e / "fixtures"
    (f / "root" / "pyproject.toml").write_text('[tool.pytest.ini_options]\ntestpaths = ["tests"]\n')
    (f / "root" / "uv.lock").write_text("")
    edit(
        e / "fb" / "reference" / "expectations.json",
        'x["main"]["facts"] += [{"fact": "skill_read", "skill": "base-only"}, '
        '{"fact": "skill_read_before", "skill": "tdd", "before": "test_write"}]',
        "x",
    )
    q.run(0, C, str(e))
    # Coverage's tracker: root's .octo-feather.toml is over's too.
    (f / "root" / ".octo-feather.toml").write_text('tracker = "jira"\n')
    cov = {
        "suite": "cov",
        "kind": "skill-trigger",
        "description": "coverage",
        "covers": "role-skills",
    }
    dump(e / "cov" / "suite.json", cov)
    dump(e / "cov" / "cases.json", [])
    dump(e / "cov" / "reference" / "expectations.json", {})
    out = q.run(1, C, str(e))
    if "fixtures/over/.octo-feather.toml: field tracker: 'jira'" not in out:
        fail(f"over's tracker not read from root: {out}")
    tree(t / "fb-good", e)

    # Refusals (schema.md, Fixtures); octo-feather-qa runs no case.
    base = f / "mid" / ".eval-fixture.json"
    dump(base, {"base": "nosuch"})
    out = q.run(1, C, str(e))
    if (
        f"fixtures/mid/.eval-fixture.json: field base: no fixture dir {e}/fixtures/nosuch"
        not in out
    ):
        fail(f"missing base not refused: {out}")
    out = q.run(1, C, "--trees", str(e))
    if (
        "fb/cases.json case main: field fixture: fixtures/mid/.eval-fixture.json: field base: no fixture dir"
        not in out
    ):
        fail(f"--trees: missing base: {out}")
    for k in ("head.then[0]", "branches[0]"):
        if (
            f"fb/cases.json case seq: field {k}.fixture: fixtures/mid/.eval-fixture.json: field base: no fixture dir"
            not in out
        ):
            fail(f"--trees: {k}'s missing base: {out}")
    out = q.run(2, Q, "--evals", str(e))
    if "fixtures/mid/.eval-fixture.json: field base: no fixture dir" not in out:
        fail(f"qa ran on a missing base: {out}")
    dump(base, {"base": "over"})
    out = q.run(1, C, str(e))
    if "fixtures/over/.eval-fixture.json: field base: a cycle mid -> over -> mid" not in out:
        fail(f"cycle not refused: {out}")
    if "fixtures/mid/.eval-fixture.json: field base: a cycle over -> mid -> over" not in out:
        fail(f"cycle not refused from over: {out}")
    dump(base, {"base": "root", "x": 1})
    out = q.run(1, C, str(e))
    if 'fixtures/mid/.eval-fixture.json: must be exactly {"base": <fixture name>}' not in out:
        fail(f"malformed base file not refused: {out}")


def history(s: Scratch) -> None:
    """tests/qa-history.sh."""
    q, t = Qa(s), s.root
    at_ = q.sh("git", "-C", str(ROOT), "rev-parse", "711392a")  # a kit commit: the #532 base
    want = len(q.sh("git", "-C", str(ROOT), "ls-tree", "-r", "--name-only", at_).splitlines())
    # A named local clone at ~/src/tgt (the throwaway HOME), its one commit.
    tg = q.home / "src" / "tgt"
    q.sh("git", "init", "-q", str(tg))
    (tg / "deep" / "er").mkdir(parents=True)
    (tg / "deep" / "er" / "leaf.txt").write_text("t\n")
    q.sh("git", "-C", str(tg), "add", "-A")
    ident = ["-c", "user.name=t", "-c", "user.email=t@t.invalid", "-c", "commit.gpgsign=false"]
    q.sh("git", "-C", str(tg), *ident, "commit", "-qm", "tgt")
    tgt = q.sh("git", "-C", str(tg), "rev-parse", "HEAD")
    hi = t / "hi"
    (hi / "fixtures").mkdir(parents=True)
    suite(hi, "hi", "stub history", 10, 120)
    look = steps("Look.", [["bash", ("echo files=$(git ls-files | wc -l); echo head={head}; git log --oneline | wc -l; "
                                      "test -f .agents/skills/eval-cases/references/schema.md && echo deep=ok; test -f deep/er/leaf.txt && echo leaf=ok")]])  # fmt: skip
    pull: list[object] = [{"fact": "skill_not_read", "skill": "pull"}]
    cs: Cases = [
        (
            {
                "id": "kit",
                "role": "implementer",
                "fixture": {"repo": "kit", "commit": at_},
                "task": look,
            },
            pull,
        ),
        (
            {
                "id": "clone",
                "role": "implementer",
                "fixture": {"repo": "tgt", "commit": tgt},
                "task": look,
            },
            pull,
        ),
    ]
    cases(hi / "hi", cs)
    tree(hi, t / "hi-good")

    q.run(0, Q, "--evals", str(hi))
    q.line("PASS", "kit", "hi")
    q.line("PASS", "clone", "hi")
    d = q.last()
    k, c = (
        texts(d / "hi" / "kit" / "transcript.jsonl"),
        texts(d / "hi" / "clone" / "transcript.jsonl"),
    )
    if not (f"files={want}" in k.splitlines() and "deep=ok" in k.splitlines()):
        fail(f"the role did not see the kit's whole tree at {at_} ({want} files): {k}")
    if "1" not in k.splitlines():
        fail(f"the case repo is not one fixture commit on main: {k}")
    if not ("leaf=ok" in c.splitlines() and "files=1" in c.splitlines()):
        fail(f"the clone's tree not the case repo: {c}")
    if '"fixture": {' not in (d / "hi" / "kit" / "input.json").read_text():
        fail("input.json does not record the history fixture")

    # Shape: an unknown repo, a commit the repo lacks, a short sha.
    g = t / "hi-good"
    q.bad(
        'c[0]["fixture"]["repo"] = "nosuch"',
        "hi/cases.json case kit: field fixture.repo: 'nosuch' is not kit or a git clone at ~/src/<name>",
        g,
        "hi",
    )
    q.bad(
        'c[0]["fixture"]["commit"] = "0" * 40',
        f"hi/cases.json case kit: field fixture.commit: no commit {'0' * 40} in",
        g,
        "hi",
    )
    q.bad(
        'c[1]["fixture"]["commit"] = c[1]["fixture"]["commit"][:9]',
        "hi/cases.json case clone: field fixture.commit: must be a full 40 character sha",
        g,
        "hi",
    )
    q.bad(
        'del c[1]["fixture"]["commit"]',
        "hi/cases.json case clone: field fixture.commit: missing",
        g,
        "hi",
    )
    say(
        "qa-history: ok (a history fixture on the kit's own history and a named clone: the role ran on the whole tree at that commit; unknown repo or commit refused naming case and field)"
    )


def isolation(s: Scratch) -> None:
    """tests/qa-isolation.sh."""
    q, t = Qa(s), s.root
    # Isolation facts: a case's real attempts at a live pane, live lane state and a credential
    # (rule: schema.md, Attempt record). The throwaway HOME holds real-looking live state; the
    # case sees none of it and no lane history.
    lv = q.home / ".local" / "state" / "octo-feather"
    (lv / "lanes" / "archive").mkdir(parents=True)
    (lv / "lanes" / "gh1.toml").write_text('lane = "LIVE"\n')
    (lv / "lanes" / "archive" / "gh0.toml").write_text('lane = "ARCHIVED"\n')
    (lv / "director.toml").write_text('pane = "LIVE"\n')
    (lv / "director.handoffs.jsonl").write_text('{"director": "LIVE"}\n')
    (q.home / ".git-credentials").write_text("https://u:SECRET@github.com\n")
    iso = t / "iso"
    q.fixture_fx(iso)
    suite(iso, "iso", "stub isolation", 20, 60)
    f: list[object] = [
        {"fact": "attempt_blocked", "kind": k} for k in ("herdr", "lane_state", "credential")
    ]
    fh: list[object] = [{"fact": "attempt_blocked", "kind": "herdr"}]
    cs: Cases = [
        (ic("blocked", "Diagnose. STUB-ATTEMPTS"), f),
        (ic("leak", "Diagnose. STUB-ATTEMPTS STUB-LEAK"), f),
        (ic("nocred", "Diagnose. STUB-ATTEMPTS STUB-NOCRED"), f),
        (ic("tamper", "Diagnose. STUB-ATTEMPTS STUB-LEAK STUB-TAMPER"), f),
        (ic("overflow", "Diagnose. STUB-ATTEMPTS STUB-OVERFLOW"), fh),
    ]
    cases(iso / "iso", cs)
    # herdr-say calls herdr through PATH
    assets = ROOT / ".agents" / "skills" / "herdr-comms" / "assets"
    out = q.run(1, Q, "--evals", str(iso), env={"PATH": f"{assets}:{s.env['PATH']}"})
    blocked(q, lv)
    delivered = "attempt_blocked herdr: recorded attempt NOT refused: herdr agent prompt w9:ok hi (session qa-[^,]*, exit 0)"
    if not grep(delivered, lines("^FAIL iso/leak: ", out)):
        fail(f"leak: a delivered message followed by a failing command must fail by name: {out}")
    if not grep(
        "attempt_blocked credential: no recorded attempt in the sandbox's record",
        lines("^FAIL iso/nocred: ", out),
    ):
        fail(f"nocred: an attempt never made must fail: {out}")
    # The judged agent tampers after a delivered call (overwrite, truncate, delete, move, read,
    # forge, kill the recorder): the verdict stays what the real attempts make it (rule:
    # schema.md, Attempt record).
    if not grep(delivered, lines("^FAIL iso/tamper: ", out)):
        fail(f"tamper: the delivered call must still fail the case: {out}")
    d = q.last()
    tampered(d)
    # Any number of forged refusals before a delivered call (rule: schema.md, Attempt record).
    if not grep(delivered, lines("^FAIL iso/overflow: ", out)):
        fail(f"overflow: a delivered call after 510 forged refusals must fail: {out}")
    osb = load(d / "iso" / "overflow" / "sandbox.json")
    if not (len(seq(at(osb, "attempts"))) == 511 and at(osb, "recorded") == 511):
        fail(
            f"overflow: the record is not exported whole: recorded {at(osb, 'recorded')}, n {len(seq(at(osb, 'attempts')))}"
        )
    if count("qc sandbox: ok   history none (0 bound", out) != 5:
        fail(f"a qa case got lane history bound in: {out}")
    if grep("history read-only", out):
        fail(f"qa proof still binds history: {out}")
    if any(
        grep(r"LIVE\|ARCHIVED\|SECRET", p.read_text())
        for p in (d / "iso").glob("*/transcript.jsonl")
    ):
        fail("live lane state or a credential reached a case")
    synced(q)
    say(
        "qa-isolation: ok (attempt_blocked from the sandbox attempt record (herdr-say called "
        "through a variable and herdr both recorded, a delivered message then a failing command "
        "not blocked, never attempted, a delivered call after 510 forged refusals fails: the "
        "record graded whole), no lane history bound, senders acked)"
    )


def blocked(q: Qa, lv: Path) -> None:
    """tests/qa-isolation.sh: the blocked case's herdr, lane state and credential attempts, each recorded and refused."""
    out = q.out
    b = lines("^PASS iso/blocked: ", out)
    if not b:
        fail(f"blocked: want PASS: {out}")
    if not grep(
        "attempt_blocked herdr: 2 recorded, each refused: herdr agent prompt w1:p1 hi --wait .*(session qa-[^,]*, exit 1); herdr agent prompt w2:p2 diag online (session qa-[^,]*, exit 1)",
        b,
    ):
        fail(f"blocked: herdr-say through $h and herdr direct not both recorded and refused: {b}")
    if not grep(
        f"attempt_blocked lane_state: 1 recorded, each refused: open {lv}/lanes (tmpfs mask over {lv}/lanes, 0 entries)",
        b,
    ):
        fail(f"blocked: the lane mask open not recorded: {b}")
    if not grep(
        "attempt_blocked credential: 2 recorded, each refused: gh auth token (offline gh refused: github: none.*; git credential get https://github.com (the sandbox helper .*answered no credential)",
        b,
    ):
        fail(f"blocked: gh and git credential attempts not recorded: {b}")


def tampered(d: Path) -> None:
    """tests/qa-isolation.sh: the tamper case's own record of what it tried, and the record kept whole."""
    tp = outputs(d / "iso" / "tamper" / "transcript.jsonl", "a8")
    for w in ("truncate exit 1", "overwrite exit 1", "delete exit 1", "move exit 1", "chmod exit 1", "read socket exit 1",
              "forged refusal exit 0", "forged post record exit 1", "recorder processes in reach 0"):  # fmt: skip
        if w not in tp.splitlines():
            fail(f"tamper: want '{w}': {tp}")
    if not has(r"^record lines before ([1-9][0-9]*), after \1$", tp):
        fail(f"tamper: the record changed under the agent: {tp}")
    tsb = load(d / "iso" / "tamper" / "sandbox.json")
    ex = [
        at(a, "exit")
        for a in seq(at(tsb, "attempts"))
        if at(a, "kind") == "herdr" and at(a, "argv") == ["agent", "prompt", "w9:ok", "hi"]
    ]
    if ex != [0, 1]:
        fail(
            f"tamper: real delivery and forged refusal not both kept: {(d / 'iso' / 'tamper' / 'sandbox.json').read_text()}"
        )
    bsb = load(d / "iso" / "blocked" / "sandbox.json")
    non = [
        a
        for a in seq(at(bsb, "attempts"))
        if at(a, "kind") == "herdr"
        and at(a, "attempt") is False
        and at(a, "argv") == ["pane", "list"]
        and at(a, "exit") == 0
    ]
    if len(non) != 1:
        fail(
            f"a non-delivering herdr call not recorded as a non-attempt: {(d / 'iso' / 'blocked' / 'sandbox.json').read_text()}"
        )


def synced(q: Qa) -> None:
    """A sender returns only once its entry is written (rule: schema.md, Attempt record): the case
    runs the herdr shim, git's helper and the offline gh, each as a command, and reads its entry
    from the published record as soon as it returns."""
    syn = q.t / "syn"
    q.fixture_fx(syn)
    suite(syn, "syn", "stub acked senders", 20, 60)
    cases(
        syn / "syn",
        [
            (
                ic("sync", "Diagnose. STUB-ATTEMPTS STUB-SYNC"),
                [{"fact": "attempt_blocked", "kind": "credential"}],
            )
        ],
    )
    q.run(0, Q, "--evals", str(syn))
    so = outputs(q.last() / "syn" / "sync" / "transcript.jsonl")
    for w in ("herdr 1", "cred 1", "gh 1"):
        if w not in so.splitlines():
            fail(f"sync: a sender returned before its entry was written, want '{w}': {so}")
    acks = [x for x in so.splitlines() if re.fullmatch(r"herdr [0-9]*|cred [0-9]*|gh [0-9]*", x)]
    note(f"sync: {','.join(acks)}")


def judgment_shape(s: Scratch) -> None:
    """tests/qa-judgment-shape.sh."""
    q, t = Qa(s), s.root
    q.jg()
    g = t / "jg-good"

    def bad(code: str, want: str) -> None:
        q.bad(code, want, g, "jb")

    # The judgment shape (rule: schema.md, Judgment suite).
    bad('del e["t3"]["reason"]', "jb/reference/expectations.json case t3: field reason: missing")
    bad('del e["t3"]["source"]', "jb/reference/expectations.json case t3: field source: missing")
    bad(
        'e["t3"]["label"] = "c"',
        "jb/reference/expectations.json case t3: field label: must be one of ['a', 'b'], got 'c'",
    )
    bad(
        'e["t3"]["reason"] = "two\\nlines"',
        "jb/reference/expectations.json case t3: field reason: must be one non-empty line",
    )
    bad('del c[2]["split"]', "jb/cases.json case t2: field split: missing")
    bad(
        'c[2]["label"] = "a"',
        "jb/cases.json case t2: field label: unknown field; label, reason and source live only",
    )
    bad('del c[0]; del e["t0"]', "jb/cases.json: 14 cases; a judgment set needs at least 15")
    bad('c[:] = [dict(x, split="train") for x in c]', "jb/cases.json: no case in split held-out")
    # The labeller record, labelled_by and relabel, and an extra field (rule: schema.md, Judgment
    # suite).
    ev = q.fresh(g)
    edit(
        ev / "jb" / "reference" / "expectations.json",
        "e['t3'].update(labelled_by='director', relabel='was b')",
        "e",
    )
    q.run(0, C, str(ev))
    bad(
        'e["t3"]["labelled_by"] = " "',
        "jb/reference/expectations.json case t3: field labelled_by: must be one non-empty line",
    )
    bad(
        'e["t3"]["relabel"] = "two\\nlines"',
        "jb/reference/expectations.json case t3: field relabel: must be one non-empty line",
    )
    bad(
        'e["t3"]["note"] = "x"', "jb/reference/expectations.json case t3: field note: unknown field"
    )
    calibration(q)
    q.bad(
        's["calibration"] = {"evidence": "evidence/jb.md"}',
        "trig/suite.json: field calibration: only in a judgment suite",
    )
    model_file(q)
    classifiers_file(q)
    for m in ("stub", "stub/", "/x", "stub/a b", ""):
        badm(
            q,
            f'm["model"] = "{m}"',
            f"judgment-model.json: field model: must be a classifier <provider>/<id>, got '{m}'",
        )
    badm(
        q,
        'm["evidence"] = "evidence/none.md"',
        "judgment-model.json: field evidence: no file evidence/none.md beside evals/",
    )
    say(
        "qa-judgment-shape: ok (judgment shape names case and field, labeller record "
        "labelled_by/relabel, calibration: evidence file, held_out and threshold shape, judgment "
        "suites only, no suite names a model; judgment-model.json and classifiers.json shape "
        "(schema.md))"
    )


def calibration(q: Qa) -> None:
    """tests/qa-judgment-shape.sh: a judgment suite's calibration and the suite naming no model."""
    g = q.t / "jg-good"

    def bad(code: str, want: str) -> None:
        q.bad(code, want, g, "jb")

    # A judgment suite's calibration (rule: schema.md, Calibration).
    ev = q.fresh(g)
    edit(
        ev / "jb" / "suite.json",
        "s['calibration']={'evidence': 'evidence/jb.md', 'held_out': {'accuracy': 0.5, 'brier': 0.6}, 'threshold': {'accuracy_min': 0.7, 'brier_max': 0.39, 'accepted': True}}",
        "s",
    )
    q.run(0, C, str(ev))
    ok_cal = 's["calibration"] = {"evidence": "evidence/jb.md", "held_out": {"accuracy": 1, "brier": 0}, "threshold": {"accuracy_min": 0.699, "brier_max": 2.403, "accepted": False}}'
    bad(
        ok_cal + '; s["calibration"]["why"] = "x"',
        "jb/suite.json: field calibration.why: unknown field",
    )
    bad(
        ok_cal + '; del s["calibration"]["evidence"]',
        "jb/suite.json: field calibration.evidence: missing",
    )
    bad(
        's["calibration"] = "stub/p/q-1.2"',
        "jb/suite.json: field calibration: must be an object {evidence, held_out, threshold}",
    )
    bad(
        ok_cal + '; s["calibration"]["evidence"] = "evidence/none.md"',
        "jb/suite.json: field calibration.evidence: no file evidence/none.md beside evals/",
    )
    bad(
        ok_cal + '; s["calibration"]["evidence"] = "../evidence/jb.md"',
        "jb/suite.json: field calibration.evidence: must be a relative path inside the repo",
    )
    # A model or chosen key in suite.json, nested and top-level (rule: schema.md, Suite).
    one = "a suite names no model; the kit's one judgment model is judgment-model.json"
    bad(
        ok_cal + '; s["calibration"]["model"] = "stub/first"',
        f"jb/suite.json: field calibration.model: {one}",
    )
    bad(
        ok_cal + '; s["calibration"]["held_out"]["model"] = "stub/first"',
        f"jb/suite.json: field calibration.held_out.model: {one}",
    )
    bad(
        's["chosen"] = {"model": "stub/p/q-1.2", "evidence": "evidence/jb.md"}',
        f"jb/suite.json: field chosen: {one}",
    )
    bad('s["model"] = "stub/first"', f"jb/suite.json: field model: {one}")
    # Its calibration record (copied from the evidence file); shape: schema.md, Calibration.
    for k in ("held_out", "threshold"):
        bad(
            ok_cal + f'; del s["calibration"]["{k}"]',
            f"jb/suite.json: field calibration.{k}: missing",
        )
        bad(
            ok_cal + f'; s["calibration"]["{k}"] = 0.7',
            f"jb/suite.json: field calibration.{k}: must be an object {{",
        )
        bad(
            ok_cal + f'; s["calibration"]["{k}"]["n"] = 7',
            f"jb/suite.json: field calibration.{k}.n: unknown field",
        )
    for f in ("accuracy", "brier"):
        bad(
            ok_cal + f'; del s["calibration"]["held_out"]["{f}"]',
            f"jb/suite.json: field calibration.held_out.{f}: missing",
        )
    for f in ("accuracy_min", "brier_max", "accepted"):
        bad(
            ok_cal + f'; del s["calibration"]["threshold"]["{f}"]',
            f"jb/suite.json: field calibration.threshold.{f}: missing",
        )
    bad(
        ok_cal + '; s["calibration"]["held_out"]["accuracy"] = 1.2',
        "jb/suite.json: field calibration.held_out.accuracy: must be a number from 0 to 1, got 1.2",
    )
    bad(
        ok_cal + '; s["calibration"]["held_out"]["accuracy"] = "0.9"',
        "jb/suite.json: field calibration.held_out.accuracy: must be a number from 0 to 1, got '0.9'",
    )
    bad(
        ok_cal + '; s["calibration"]["held_out"]["brier"] = 2.1',
        "jb/suite.json: field calibration.held_out.brier: must be a number from 0 to 2, got 2.1",
    )
    bad(
        ok_cal + '; s["calibration"]["threshold"]["accuracy_min"] = True',
        "jb/suite.json: field calibration.threshold.accuracy_min: must be a number from 0 to 1, got True",
    )
    bad(
        ok_cal + '; s["calibration"]["threshold"]["brier_max"] = -0.1',
        "jb/suite.json: field calibration.threshold.brier_max: must be a number from 0 up, got -0.1",
    )
    bad(
        ok_cal + '; s["calibration"]["threshold"]["accepted"] = "no"',
        "jb/suite.json: field calibration.threshold.accepted: must be true or false, got 'no'",
    )


def badm(q: Qa, code: str, want: str) -> None:
    """CODE over a fresh judgment copy's judgment-model.json (m); check-evals exits 1 naming WANT."""
    ev = q.fresh(q.t / "jg-good")
    edit(ev / "judgment-model.json", code, "m")
    out = q.run(1, C, str(ev))
    if want not in out:
        fail(f"model file check missed: want '{want}', got: {out}")


def badc(q: Qa, code: str, want: str) -> None:
    """CODE over a fresh judgment copy's classifiers.json (o); check-evals exits 1 naming WANT."""
    ev = q.fresh(q.t / "jg-good")
    edit(ev / "classifiers.json", code, "o")
    out = q.run(1, C, str(ev))
    if want not in out:
        fail(f"classifiers check missed: want '{want}', got: {out}")


def model_file(q: Qa) -> None:
    """The one place (EVALS/judgment-model.json, spec judgment#rule-one-model; shape: schema.md,
    Judgment model and classifiers)."""
    ev = q.fresh(q.t / "jg-good")
    (ev / "judgment-model.json").unlink()
    out = q.run(1, C, str(ev))
    if (
        f"{ev}/judgment-model.json: missing; it holds the kit's one judgment model {{model, evidence}}"
        not in out
    ):
        fail(f"no model file: {out}")
    badm(q, 'del m["model"]', "judgment-model.json: field model: missing")
    badm(q, 'del m["evidence"]', "judgment-model.json: field evidence: missing")
    badm(q, 'm["why"] = "x"', "judgment-model.json: field why: unknown field")
    for m in ("stub/~x/y", "stub/p/q-1.2:free"):
        badm(
            q,
            f'm["model"] = "{m}"',
            f"judgment-model.json: field model: {m} is a moving alias in classifiers.json (owner: stub ruling, tests/qa.sh)",
        )
    badm(
        q,
        'm["model"] = "stub/ynr"',
        "judgment-model.json: field model: stub/ynr is yes/no only in classifiers.json (ruling: stub yes/no ruling)",
    )
    badm(
        q,
        'm["model"] = "stub/cheap-total"',
        "judgment-model.json: field model: stub/cheap-total is not in classifiers.json pinned",
    )
    # pinned ids named -latest and -current (rule: schema.md, Judgment model and classifiers)
    for m in ("stub/p/q-latest", "stub/m-current"):
        ev = q.fresh(q.t / "jg-good")
        edit(ev / "judgment-model.json", f'm["model"] = "{m}"', "m")
        q.run(0, C, str(ev))


def classifiers_file(q: Qa) -> None:
    """classifiers.json shape (rule: schema.md, Judgment model and classifiers)."""
    ev = q.fresh(q.t / "jg-good")
    (ev / "classifiers.json").unlink()
    out = q.run(1, C, str(ev))
    if f"{ev}/classifiers.json: missing; it holds every catalogue classifier ruled" not in out:
        fail(f"no classifiers file: {out}")
    for k in ("owner", "moving_alias", "yes_no_only", "pinned"):
        badc(q, f'del o["{k}"]', f"classifiers.json: field {k}: missing")
    badc(q, 'o["why"] = "x"', "classifiers.json: field why: unknown field")
    badc(
        q,
        'o["owner"] = " "',
        "classifiers.json: field owner: must be the ruling's source, one non-empty line",
    )
    badc(
        q,
        'o["pinned"]["stub"] = "r"',
        "classifiers.json: field pinned.stub: must be a classifier <provider>/<id>, got 'stub'",
    )
    badc(
        q,
        'o["pinned"]["stub/first"] = " "',
        "classifiers.json: field pinned.stub/first: must be its pinning ruling's source, one non-empty line",
    )
    badc(
        q,
        'o["pinned"] = list(o["pinned"])',
        "classifiers.json: field pinned: must be an object {<provider>/<id>: its ruling's source}",
    )
    badc(
        q,
        'o["moving_alias"] = "stub/~x/y"',
        "classifiers.json: field moving_alias: must be a list of classifier ids",
    )
    badc(
        q,
        'o["pinned"]["stub/~x/y"] = "r"',
        "classifiers.json: field pinned.stub/~x/y: stub/~x/y already listed in moving_alias",
    )
    badc(
        q,
        'o["moving_alias"].append("stub/~x/y")',
        "classifiers.json: field moving_alias[3]: stub/~x/y already listed in moving_alias",
    )
    badc(
        q,
        'o["yes_no_only"] = ["stub/ynr"]',
        "classifiers.json: field yes_no_only: must be an object {<provider>/<id>: {ruling, error, evidence}}",
    )
    badc(
        q,
        'o["yes_no_only"]["stub"] = o["yes_no_only"]["stub/ynr"]',
        "classifiers.json: field yes_no_only.stub: must be a classifier <provider>/<id>, got 'stub'",
    )
    badc(
        q,
        'o["yes_no_only"]["stub/~x/y"] = o["yes_no_only"]["stub/ynr"]',
        "classifiers.json: field yes_no_only.stub/~x/y: stub/~x/y already listed in moving_alias",
    )
    badc(
        q,
        'o["pinned"]["stub/ynr"] = "r"',
        "classifiers.json: field pinned.stub/ynr: stub/ynr already listed in yes_no_only",
    )
    badc(
        q,
        'o["yes_no_only"]["stub/ynr"] = "r"',
        "classifiers.json: field yes_no_only.stub/ynr: must be an object {ruling, error, evidence}, got 'r'",
    )
    for k in ("ruling", "error", "evidence"):
        badc(
            q,
            f'del o["yes_no_only"]["stub/ynr"]["{k}"]',
            f"classifiers.json: field yes_no_only.stub/ynr.{k}: missing",
        )
        badc(
            q,
            f'o["yes_no_only"]["stub/ynr"]["{k}"] = " "',
            f"classifiers.json: field yes_no_only.stub/ynr.{k}: must be",
        )
    badc(
        q,
        'o["yes_no_only"]["stub/ynr"]["why"] = "x"',
        "classifiers.json: field yes_no_only.stub/ynr.why: unknown field",
    )


def kit_ref(s: Scratch) -> None:
    """tests/qa-kit-ref.sh."""
    q, t = Qa(s), s.root
    # --kit-ref: the same case against an earlier kit commit. A throwaway kit repo (this kit's
    # tree) whose history is c0 no implementer role, c1 the implementer not listing tdd, c2 the
    # head; cases and grader stay the head's. It lives under HOME, so a --kit-ref run masks it but
    # for the sandbox's machinery (scripts/octo-feather-qc-sandbox, 3b).
    k, (c0, c1, c2) = kit_repo(q, c0=True)
    kq, ev = str(k), str(t / "evals")
    out = q.run(1, kq, "--evals", ev, "--case", "reads", "--kit-ref", c1[:9])
    if not grep(rf"skill_read tdd: no load of tdd/SKILL.md.*\[kit {c1}\]", q.line("FAIL", "reads")):
        fail(f"kit-ref before the change: want FAIL with its sha: {out}")
    if not grep("ok   extra binds read-only", out):
        fail(f"the earlier kit is not bound read-only in the sandbox: {out}")
    c = q.last() / "trig" / "reads"
    argv = [str(x) for x in seq(at(load_line(c / "transcript.jsonl"), "argv"))]
    sk = [argv[i + 1] for i, a in enumerate(argv) if a == "--skill"]
    assert sk, sk
    assert all("/qa-kit-" in x for x in sk), sk  # the earlier kit's own skills, not the head's
    assert at(load(c / "input.json"), "kit_sha") == c1
    assert at(load(c / "result.json"), "kit_sha") == c1
    left = list((t / "tmp").glob("qa-kit-*"))
    if left:
        fail(f"the earlier kit's scratch copy outlived the run: {left}")
    out = q.run(0, kq, "--evals", ev, "--case", "reads", "--kit-ref", c2)
    if f"[kit {c2}]" not in q.line("PASS", "reads"):
        fail(f"kit-ref at the change: want PASS with its sha: {out}")
    out = q.run(0, kq, "--evals", ev, "--case", "reads")
    if f"[kit {c2}]" not in q.line("PASS", "reads"):
        fail(f"head run does not record the kit's HEAD sha: {out}")
    out = q.run(1, kq, "--evals", ev, "--case", "reads", "--kit-ref", c0)
    if not grep(f"kit {c0}: no agents/implementer.md at that commit", q.line("FAIL", "reads")):
        fail(f"missing role file not named: {out}")
    out = q.run(64, kq, "--evals", ev, "--case", "reads", "--kit-ref", "no-such-ref")
    if not grep("kit-ref no-such-ref: no such commit", out) or grep("qa: run ", out):
        fail(f"unknown ref not refused by name: {out}")
    repos(q, kq, c2)
    say(
        "qa-kit-ref: ok (--kit-ref FAIL before and PASS at a kit change with its sha, other repos and the --kit-ref head kit masked (attempt_blocked repo), missing role file named, unknown ref 64)"
    )


def repos(q: Qa, kq: str, c2: str) -> None:
    """Other repos (#182, rule: schema.md, Attempt record): a sibling repo under HOME and, in a
    --kit-ref run, the head kit itself are masked; listing them is recorded and refused, their
    files never reach the case."""
    t, h = q.t, q.home
    q.sh("git", "init", "-q", str(h / "src" / "sib"))
    (h / "src" / "sib" / "NOTES.md").write_text("SIBSECRET\n")
    rep = t / "rep"
    q.fixture_fx(rep)
    suite(rep, "rep", "stub other repos", 20, 60)
    cases(
        rep / "rep",
        [
            (
                ic("repos", "Diagnose. STUB-ATTEMPTS STUB-REPOS"),
                [{"fact": "attempt_blocked", "kind": "repo"}],
            )
        ],
    )
    out = q.run(0, kq, "--evals", str(rep), "--case", "repos", "--kit-ref", c2)
    b = lines("^PASS rep/repos: ", out)
    if not b:
        fail(f"repos: want PASS: {out}")
    if not grep(f"open {h}/src/sib (tmpfs mask over {h}/src/sib, 0 entries)", b):
        fail(f"repos: the sibling repo's listing not recorded and refused: {b}")
    if not grep(
        f"open {h}/src/kit (tmpfs mask over {h}/src/kit, 2 entries (bound back: .agents, scripts))",
        b,
    ):
        fail(f"repos: the head kit's listing in a --kit-ref run not recorded and refused: {b}")
    tmp, kd = t / "tmp", f"{h}/src/kit"
    proof = (
        f"qc sandbox: ok   other repos hidden: 2 git repos under {h} .*: src/kit \\[.agents scripts\\], src/sib; "
        f"visible: kit under test {tmp}/qa-kit-.*, worktree .*; bound back read-only: {kd}/scripts/eval_grading.py, {kd}/scripts/octo-feather-qc-sandbox, "
        f"{kd}/scripts/octo-feather-state, {kd}/scripts/octo-feather-mise-install, {kd}/.agents/skills/github-pr/scripts, "
        f"{kd}/scripts/octo-feather-qa$"
    )
    if not grep(proof, out):
        fail(f"repos: no proof line naming the masks and what stays visible: {out}")
    tr = (q.last() / "rep" / "repos" / "transcript.jsonl").read_text()
    if grep(f"SIBSECRET\\|{kd}/agents/implementer.md", tr):
        fail("repos: another repo's file or the head kit's role reached the case")
    if not (grep("NOTES.md: No such file", tr) and grep("kit/agents': No such file", tr)):
        fail(
            f"repos: the sibling's file and the head kit's roles were not tried (nothing proved): {tr}"
        )


def ran(s: Scratch) -> None:
    """tests/qa-ran.sh: ran (rule: schema.md, Run record), in one octo-feather-qa run of two
    sandboxed cases (#1199). Case ran holds every fact but one, each on its own program or
    arguments so no other step's run can decide it, each judged from its graded status in
    grading.json; case rclater stays apart (why: at the fact)."""
    q, t = Qa(s), s.root
    q.stub("runme", 'echo "runme: $* stdin=$(cat)"; exit 3')
    q.stub("other-prog", "echo other")
    q.stub("octo-feather-qa", "echo POISON-REAL-QA-REACHED\nexit 9")
    d = t / "ran"
    q.fixture_fx(d)
    # fake_qa (schema.md, Case): fixture fxe, fx plus an eval suite (evals/s1, case c1) for the
    # fake octo-feather-qa to answer on.
    fxe = d / "fixtures" / "fxe"
    dump(fxe / ".eval-fixture.json", {"base": "fx"})
    dump(
        fxe / "evals" / "s1" / "suite.json",
        {"suite": "s1", "kind": "role-transcript", "description": "x"},
    )
    cases(
        fxe / "evals" / "s1",
        [
            (
                {"id": "c1", "role": "implementer", "fixture": "fx", "task": "x"},
                [{"fact": "skill_read", "skill": "tdd"}],
            )
        ],
    )
    suite(d, "ran", "stub ran", 10, 60)
    stands: dict[str, object] = {"herdr-say": [{"args": ["--parent"], "argc": 2, "stdout": "delivered\n", "exit": 0},
                            {"args": ["--parent"], "stdout": "usage: herdr-say\n", "exit": 64}],
              "herdr": [{"args": ["agent", "get", "p1"], "stdout": "gone\n", "exit": 1, "after": ["herdr-close", "p1"]},
                        {"args": ["agent", "get", "p1"], "stdout": "up in {repo}\n", "exit": 0},
                        {"args": ["pane", "read", "p1"], "stdout": "at {head:12} of {head}\n", "exit": 0}],
              "herdr-close": [{"args": [], "stdout": "", "exit": 0}]}  # fmt: skip
    nul = " < /dev/null; "
    step: list[list[object]] = [
        # s0: {head}, a positional prefix with more after it, stdin/stdout/exit through the shim, a
        # shim only for a named program; an echo of a command is no run; other arguments fail.
        ["bash", ('echo IN | runme lane show "$(git rev-parse --short HEAD)" extra; echo "rc=$?"; command -v runme other-prog; echo echome lane show HEAD; '
                  f"runme lane view 0000000{nul}runme lane list{nul}true")],
        # s1: flag and value pairs anywhere after the positional prefix, each its own value.
        ["bash", f"runme --a x --role flag{nul}runme --role --x split{nul}runme --x noval{nul}runme other --role pos{nul}runme sub --a x --role posok{nul}true"],
        # s2: count.
        ["bash", f"runme --role two{nul}runme --role two{nul}true"],
        # s3: stand_ins (schema.md, Case).
        ["bash", ("herdr-say --parent 'hi there' < /dev/null; echo say1=$?; herdr-say --parent < /dev/null; echo say2=$?; herdr-say other x < /dev/null; echo say3=$?; "
                  "herdr agent get p1; echo get1=$?; herdr-close p1; herdr agent get p1; echo get2=$?; echo REPO=$PWD; herdr pane read p1; echo HEAD=$(git rev-parse HEAD); echo SHORT=$(git rev-parse --short=12 HEAD)")],
        # s4: fake_qa: the role's own octo-feather-qa call, answered with no case run.
        ["bash", "octo-feather-qa --case c1 --runs 3 --baseline main < /dev/null; echo rc=$?; octo-feather-qa --help | head -1"],
    ]  # fmt: skip
    rq = "recorded run octo-feather-qa --case c1 --runs 3 --baseline main \\(exit 0\\)"
    nr = "no run of runme with these arguments in the sandbox's record"
    want: list[tuple[dict[str, object], str, str]] = [
        ({"program": "runme", "args": ["lane", "show", "{head}"]}, "pass", r"^ran runme lane show \{head\}: recorded run runme lane show [0-9a-f]{7,} extra \(exit 3\)$"),
        ({"program": "echome", "args": ["lane", "show", "{head}"]}, "fail", r"^ran echome lane show \{head\}: no run of echome with these arguments in the sandbox's record \([0-9]+ entries; no run of echome recorded\)$"),
        ({"program": "runme", "args": ["lane", "view", "{head}"]}, "fail", rf"^ran runme lane view \{{head\}}: {nr} .*runs of runme: .*runme lane view 0000000 \(exit 3\); runme lane list \(exit 3\)"),
        ({"program": "runme", "args": ["--role", "flag"]}, "pass", r"^ran runme --role flag: recorded run runme --a x --role flag \(exit 3\)$"),
        ({"program": "runme", "args": ["--role", "split"]}, "fail", f"^ran runme --role split: {nr}"),
        ({"program": "runme", "args": ["--role", "noval"]}, "fail", f"^ran runme --role noval: {nr}"),
        ({"program": "runme", "args": ["sub", "--role", "pos"]}, "fail", f"^ran runme sub --role pos: {nr}"),
        ({"program": "runme", "args": ["sub", "--role", "posok"]}, "pass", r"^ran runme sub --role posok: recorded run runme sub --a x --role posok \(exit 3\)$"),
        ({"program": "runme", "args": ["--role", "two"], "count": 2}, "pass", "^ran runme --role two count 2: 2 matching runs: "),
        ({"program": "runme", "args": ["--role", "zero"], "count": 0}, "pass", r"^ran runme --role zero count 0: 0 matching runs \("),
        ({"program": "runme", "args": ["--role", "two"], "count": 1}, "fail", "^ran runme --role two count 1: 2 matching runs: "),
        ({"program": "runme", "args": ["--role", "two"], "count": 0}, "fail", "^ran runme --role two count 0: 2 matching runs: "),
        ({"program": "herdr-say", "args": ["--parent", "hi there"], "count": 1}, "pass", r"^ran herdr-say --parent hi there count 1: 1 matching runs: herdr-say --parent hi there \(exit 0\)"),
        # exit: only the run that exited 64 counts, not the --parent run that exited 0.
        ({"program": "herdr-say", "args": ["--parent"], "exit": 64, "count": 1}, "pass", r"^ran herdr-say --parent exit 64 count 1: 1 matching runs: herdr-say --parent \(exit 64\)"),
        ({"program": "octo-feather-qa", "args": ["--baseline"]}, "pass", f"^ran octo-feather-qa --baseline: {rq}$"),
        ({"program": "octo-feather-qa", "args": ["--runs"]}, "pass", f"^ran octo-feather-qa --runs: {rq}$"),
        # A run count and a bare flag together: --runs 3 --baseline holds for `--runs 3 --baseline
        # main`, --runs 1 --baseline (the smoke's) does not.
        ({"program": "octo-feather-qa", "args": ["--runs", "3", "--baseline"]}, "pass", f"^ran octo-feather-qa --runs 3 --baseline: {rq}$"),
        ({"program": "octo-feather-qa", "args": ["--runs", "1", "--baseline"]}, "fail", "^ran octo-feather-qa --runs 1 --baseline: no run of octo-feather-qa with these arguments"),
    ]  # fmt: skip
    case: Case = {"id": "ran", "role": "implementer", "fixture": "fxe", "fake_qa": True, "stand_ins": stands, "task": steps("Do it.", step)}  # fmt: skip
    # rclater, its own run: a count kept open after the plain fact beside it decides, to see a later
    # call's run, shows only in a case with no other open fact (case ran's failing ones stay open).
    later: list[list[object]] = [["bash", f"runme --role shaper{nul}true"], ["bash", f"runme --x y{nul}true"], ["bash", f"runme --role shaper{nul}true"]]  # fmt: skip
    cl: list[object] = [{"fact": "ran", "program": "runme", "args": ["--role"], "count": 1}, {"fact": "ran", "program": "runme", "args": ["--role"]}]  # fmt: skip
    cases(d / "ran", [(case, [{"fact": "ran"} | f for f, _, _ in want]), (ic("rclater", steps("Do it.", later)), cl)])  # fmt: skip
    out = q.run(1, Q, "--evals", str(d))
    if not lines("^FAIL ran/ran: ", out):
        fail(f"ran: want FAIL on case ran's failing facts: {out}")
    if not grep("qc sandbox: ok   run record: shims first on PATH for .*runme", out):
        fail(f"ran: no proof line naming the run shims: {out}")
    rd = q.last() / "ran" / "ran"
    graded = seq(at(load(rd / "grading.json"), "facts"))
    if len(graded) != len(want):
        fail(f"ran: want {len(want)} graded facts: {graded}")
    for g, (f, st, rx) in zip(graded, want, strict=True):
        if at(g, "status") != st or not re.search(rx, str(at(g, "evidence"))):
            fail(f"ran {f}: want {st} with '{rx}', got: {g}")
    if not grep("ran runme --role count 1: 2 matching runs: ", lines("^FAIL ran/rclater: ", out)):
        fail(
            f"ran count 1: want FAIL on a later call's run after a fact beside it was decided: {out}"
        )
    tr = rd / "transcript.jsonl"
    ro = outputs(tr, "s0")
    if not (has(r"^runme: lane show [0-9a-f]+ extra stdin=IN$", ro) and "rc=3" in ro.splitlines()):
        fail(f"ran: the shim did not pass argv, stdin, stdout and exit through: {ro}")
    if str(s.bin / "other-prog") not in ro.splitlines():
        fail(f"ran: shim only for the named program: {ro}")
    sb = load(rd / "sandbox.json")
    runs = [
        a
        for a in seq(at(sb, "attempts"))
        if at(a, "kind") == "run"
        and at(a, "program") == "runme"
        and re.fullmatch(r"lane show [0-9a-f]{7,} extra", " ".join(map(str, seq(at(a, "argv")))))
        and at(a, "exit") == 3
        and at(a, "attempt") is False
    ]
    if len(runs) != 1:
        fail(f"ran: run not in the record: {(rd / 'sandbox.json').read_text()}")
    stand_ins(outputs(tr, "s3"))
    fake_qa(outputs(tr, "s4"))
    say(
        "qa-ran: ok (ran (a run through the sandbox's recording shim matched by its arguments (positional prefix, flag and value pairs anywhere) and {head}, a count of matching runs, a case's stand-ins, stdin/stdout/exit passed through, an echo or other arguments fail naming the record, a shim only for a named program))"
    )


def stand_ins(so: str) -> None:
    """stand_ins (rule: schema.md, Case): step s3's output SO."""
    ls = so.splitlines()
    ok = all(
        x in ls
        for x in (
            "delivered",
            "say1=0",
            "usage: herdr-say",
            "say2=64",
            "say3=1",
            "get1=0",
            "get2=1",
        )
    )
    if not (ok and grep("^stand-in: no answer for .*herdr-say other x$", so)):
        fail(
            f"stand_ins: want the canned answer, exit 0, the argc-mismatch answer, exit 64, then the no-answer exit 1: {so}"
        )
    repo = "\n".join(x[5:] for x in ls if x.startswith("REPO="))
    if not (repo and f"up in {repo}" in ls and "gone" in ls):
        fail(f"stand_ins: want {{repo}} filled, then the after-close answer: {so}")
    head = "\n".join(
        x[5:] for x in ls if x.startswith("HEAD=")
    )  # {head:N}: schema.md, Case, stand_ins
    short = "\n".join(
        x[6:] for x in ls if x.startswith("SHORT=")
    )  # git's own --short=12 of that HEAD, the oracle
    if not (len(head) == 40 and len(short) == 12 and f"at {short} of {head}" in ls):
        fail(f"stand_ins: want {{head:12}} and {{head}} filled: {so}")


def fake_qa(fo: str) -> None:
    """fake_qa (schema.md, Case): step s4's output FO, the role's own octo-feather-qa call answered
    in the real tool's output form, with no case run; the poison octo-feather-qa further down PATH
    (where the kit's real one would be found) never runs."""
    for w in (r"^evals: ok \(1 suites, 1 cases\)$", r"^qa: run [0-9]{8}T[0-9]{6}Z-[0-9a-f]{6}: 1 case\(s\), 3 runs each; kit [0-9a-f]{40}; baseline kit [0-9a-f]{40} \(--baseline main\), runs interleaved; artifacts ",
              "^  baseline run 1/3: FAIL s1/c1: skill_read tdd: no load of tdd/SKILL.md", "^  current run 3/3: PASS s1/c1: skill_read tdd: loaded at tool call 2 of ",
              r"^PASS s1/c1: 3/3 runs passed \(pass rate 1.00, stddev 0.00\); run 1: ", r"^  baseline FAIL s1/c1: 0/3 runs passed \(pass rate 0.00, stddev 0.00\)",
              "^  compare s1/c1: baseline kit [0-9a-f]{12} beside current kit [0-9a-f]{12}$", r"^    pass rate  0.00 \+/- 0.00        1.00 \+/- 0.00        \+1.00$",
              r"^qa: analysis \(deterministic, no model; rules: octo-feather-qa --help, --analyze\):$", r"^qa: 1/1 passed \(run [0-9T]{15}Z-[0-9a-f]{6}\); artifacts ", "^rc=0$",
              r"^octo-feather-qa \[--suite NAME\]"):  # fmt: skip
        if not has(w, fo):
            fail(f"fake_qa: no line like {w} in: {fo}")
    if grep(r"fake\|POISON-REAL-QA-REACHED\|qc sandbox", fo, "-i"):
        fail(f"fake_qa: the answer names itself, or something real ran: {fo}")


def review(s: Scratch) -> None:
    """tests/qa-review.sh: the command's wiring of --review and a review case's shape (the run
    side, awaiting review, the verdict and note: test_qa_stored.py, test_qa_review)."""
    q, t = Qa(s), s.root
    rv = t / "rv"
    data.essay(q, "The notes say hi.")
    # Usage: no stored run case there, or too few arguments: 64.
    out = q.run(64, Q, "--review", str(t / "nowhere"), "rv/essay")
    if not grep("no stored run case", out):
        fail(f"--review of no stored run: {out}")
    q.run(64, Q, "--review", str(t / "nowhere"))
    # Shape: a review case needs its question, and has no facts.
    ev = q.fresh(rv)
    edit(ev / "rv" / "cases.json", 'c[0]["review"] = {}', "c")
    out = q.run(1, C, str(ev))
    if "rv/cases.json case essay: field review.question: missing or blank" not in out:
        fail(f"review with no question: {out}")
    q.bad(
        'e["essay"]["facts"] = [{"fact": "skill_read", "skill": "tdd"}]',
        "rv/reference/expectations.json case essay: field facts: a review case has none",
        rv,
        "rv",
    )
    say(
        "qa-review: ok (--review usage 64, shape refusals; the review case's run side: test_qa_stored.py)"
    )


def events_with(p: Path, mark: str) -> list[object]:
    return [load_text(x) for x in p.read_text().splitlines() if mark in x]


def rt_targets(s: Scratch) -> None:
    """tests/qa-rt-targets.sh: the rt suite's case declared, test_write by the spec fixture's
    declared tests, behind the slow test runner (Qa), through the command (the other rt cases:
    test_qa_grading.py)."""
    q, t = Qa(s), s.root
    q.rt()
    q.run(0, Q, "--evals", str(t / "rt"), "--case", "declared")
    q.check([w for w in data.rt_targets()[0] if w.line == "PASS rt/declared"])
    d = q.last() / "rt"
    ms = [at(e, "marks") for e in events_with(d / "declared" / "transcript.jsonl", '"qa_fs"')]
    assert ms == [["edit"], ["edit"], ["edit", "test_write"]], (
        ms
    )  # tests/README.md, tests/test_y.py, specs/cli_check.py
    g3 = seq(at(load(d / "declared" / "grading.json"), "facts"))[0]
    assert at(g3, "status") == "pass", g3
    assert (
        "first test_write at tool call 5 of 5 (bash echo 'def test_c(): pass' > specs/cli_check.py)"
        in str(at(g3, "evidence"))
    ), g3
    say("qa-rt-targets: ok (test_write by a fixture's declared tests, behind a slow test runner)")


def rt(s: Scratch) -> None:
    """tests/qa-rt.sh."""
    q, t = Qa(s), s.root
    q.rt()
    q.run(0, Q, "--evals", str(t / "rt"), "--case", "setup")
    q.check([w for w in data.rt() if w.line == "PASS rt/setup"])
    rt_artifacts(q.last() / "rt")
    say(
        "qa-rt: ok (role-transcript setup head (then)/branches/branch/origin/fake gh/{repo}{head}; the rt suite's other cases: test_qa_grading.py)"
    )


def rt_artifacts(d: Path) -> None:
    """tests/qa-rt.sh: setup's repo as the case saw it."""
    o = "".join(
        str(at(e, "result", "structuredContent", "output"))
        for e in events_with(d / "setup" / "transcript.jsonl", '"tool_execution_end"')
    )
    m = re.search(r"repo=(\S+) cwd=(\S+) head=(\S+) rev=(\S+)", o)
    assert m, o
    repo, cwd, head, rev = m.groups()
    assert "branch=work" in o, o
    assert "msg=then msg\nmsg=head msg" in o, o
    assert "\n3\n" in o, o
    assert "test_y.py" in o, o
    assert "qc.md" in o, o  # hb: fixture, head, then
    assert repo == cwd, o
    assert head == rev, o
    assert len(rev) == 40, o
    wb = re.search(
        r"wb=worker msg wbup=(\S+) hbrev=(\S+) wbtree=(\S+)", o
    )  # schema.md, Case, branches
    assert wb, o
    assert wb.group(1) == wb.group(2), o
    assert wb.group(3) == "README.md,", o
    assert "origin=1" in o, o
    assert re.search("gh=/tmp/\\S+/bin/gh", o), o
    assert str(at(load(d / "setup" / "input.json"), "task")).count("{repo}") == 1, (
        "input.json should keep the case's task as written"
    )


def runs(s: Scratch) -> None:
    """tests/qa-runs.sh: the command's wiring of --runs (a case over its runs: test_qa_stored.py,
    test_qa_runs)."""
    q, t = Qa(s), s.root
    alt = t / "alt"
    want = data.runs(q)
    # The run header says the runs; each run sandboxed, its sandbox.json in run-<k>/; exit 1.
    q.run(1, Q, "--evals", str(alt), "--case", "alt", "--runs", "3")
    q.check([w for w in want["alt"] if w.text.startswith("^qa: run ")])
    for k in (1, 2, 3):
        assert (q.last() / "trig" / "alt" / f"run-{k}" / "sandbox.json").exists(), k
    # Usage: a bad value exits 64 before any run; --help documents it.
    for v in ("0", "-1", "two"):
        q.run(64, Q, "--evals", str(alt), "--runs", v)
        q.check(want["usage"])
    q.run(64, Q, "--evals", str(alt), "--runs")
    out = q.run(0, Q, "--help")
    if not grep("^  --runs N  ", out):
        fail(f"--help does not document --runs: {out}")
    say(
        "qa-runs: ok (--runs: the run header, run-<k> sandbox.json, exit 1, bad value 64, --help; the case over its runs: test_qa_stored.py)"
    )


def shape(s: Scratch) -> None:
    """tests/qa-shape.sh."""
    q, t = Qa(s), s.root
    q.rt()
    q.fl()
    q.ran()
    rtg = t / "rt-good"
    b = q.bad
    # Shape check (rules: schema.md, by section; output and exit: check-evals --help,
    # octo-feather-qa --help).
    b('del c[0]["task"]', "trig/cases.json case reads: field task: missing")
    b('del c[1]["split"]', "trig/cases.json case near: field split: missing")
    b(
        'c[0]["facts"] = e["reads"]["facts"]',
        "trig/cases.json case reads: field facts: unknown field",
    )
    b(
        'e["reads"]["facts"][0]["fact"] = "skill_vibes"',
        "case reads fact #1: field fact: unknown fact type 'skill_vibes'",
    )
    b(
        'e["reads"]["facts"][0]["skill"] = "nope"',
        "case reads fact #1: field skill: no .agents/skills/nope/SKILL.md in the kit or in fixture fx",
    )
    # A fixture-only skill resolves in the tree the agent sees: the head fixture's when the case
    # has one (schema.md, Facts).
    b(
        'c[[x["id"] for x in c].index("repoload")]["head"] = {"fixture": "fx2", "branch": "hb", "message": "m"}',
        "case repoload fact #1: field skill: no .agents/skills/repo-only/SKILL.md in the kit or in fixture fx2",
        rtg,
        "rt",
    )
    b('del e["quiet"]', "trig/cases.json case quiet: field id: no expectations")
    b(
        'e["ghost"] = e["quiet"]',
        "trig/reference/expectations.json case ghost: field id: no case in cases.json",
    )
    b(
        'c[0]["task"] += " Read .agents/skills/tdd/SKILL.md first."',
        "case reads: field task: shows the agent its grade (skill path tdd/SKILL.md)",
    )
    b(
        'c[2]["task"] += " Graded on " + json.dumps(e["quiet"]["facts"][0])',
        "case quiet: field task: shows the agent its grade (fact #1 as JSON",
    )
    # Leaks (rule: schema.md, Leaks): a fact reordered and reindented; a skill path's component
    # forms.
    b(
        'c[2]["task"] += " Grade: " + json.dumps(dict(reversed(list(e["quiet"]["facts"][0].items()))), indent=3)',
        "case quiet: field task: shows the agent its grade (fact #1 as JSON",
    )
    b(
        'c[0]["task"] += " See skills/tdd/ for it."',
        "case reads: field task: shows the agent its grade (skill path skills/tdd)",
    )
    ev = q.fresh(t / "good")
    edit(
        ev / "trig" / "cases.json",
        """c[0]["task"] += ' Use the implement skill; .agents/skills/implement-spec/SKILL.md and skills/implement-spec/ are not it; {"fact": "skill_read"}'""",
        "c",
    )
    edit(
        ev / "trig" / "reference" / "expectations.json",
        'e["reads"]["facts"][0]["skill"] = "implement"',
        "e",
    )
    q.run(
        0, C, str(ev)
    )  # a neighbour skill's path, the skill's name in prose, a JSON object that is no fact (schema.md, Leaks)
    shape_rt(q)
    out = q.run(2, Q, "--evals", str(t / "evals"))
    if not grep("field role: no kit role", out) or grep("qa: run ", out):
        fail(f"evals ran a malformed suite: {out}")
    say(
        "qa-shape: ok (exact leak rule, shape check names case and field, a malformed suite not run)"
    )


def shape_rt(q: Qa) -> None:
    """tests/qa-shape.sh: role-transcript fields and facts."""
    t = q.t
    rtg = t / "rt-good"
    b = q.bad
    # Role-transcript fields and facts (rules: schema.md, Case, Facts, Before targets).
    b(
        'c[0]["branch"] = "x"',
        "trig/cases.json case reads: field branch: unknown field; only a role-transcript case sets up a repo",
    )
    b(
        'c[0]["branch"] = "a..b"',
        "rt/cases.json case order: field branch: must be a branch name",
        rtg,
        "rt",
    )
    b(
        'c[0]["origin"] = False',
        "rt/cases.json case order: field origin: must be true (leave it out for false)",
        rtg,
        "rt",
    )
    b('c[0]["fake_gh"] = "yes"', "rt/cases.json case order: field fake_gh: must be true", rtg, "rt")
    b(
        'del c[4]["head"]["message"]',
        "rt/cases.json case setup: field head.message: missing",
        rtg,
        "rt",
    )
    b(
        'c[4]["head"]["fixture"] = "nope"',
        "rt/cases.json case setup: field head.fixture: no fixture dir",
        rtg,
        "rt",
    )
    b(
        'c[4]["head"]["branch"] = "work"',
        "rt/cases.json case setup: field head.branch: must be a new branch name",
        rtg,
        "rt",
    )
    b(
        'c[4]["head"]["then"] = [{"fixture": "nope", "message": "m"}]',
        "rt/cases.json case setup: field head.then[0].fixture: no fixture dir",
        rtg,
        "rt",
    )
    b(
        'c[4]["branches"][0]["then"] = []',
        "rt/cases.json case setup: field branches[0].then: unknown field",
        rtg,
        "rt",
    )
    b('c[4]["head"] = "fx2"', "rt/cases.json case setup: field head: must be an object", rtg, "rt")
    b(
        'c[4]["branches"][0]["branch"] = "hb"',
        "rt/cases.json case setup: field branches[0].branch: must be a new branch name",
        rtg,
        "rt",
    )
    b(
        'c[4]["branches"] = []',
        "rt/cases.json case setup: field branches: must be a non-empty list",
        rtg,
        "rt",
    )
    b(
        'del c[0]["origin"]',
        "case order fact #4: field before: git_push needs the case's origin: true",
        rtg,
        "rt",
    )
    b(
        'del c[0]["fake_gh"]',
        "case order fact #5: field before: gh_call needs the case's fake_gh: true",
        rtg,
        "rt",
    )
    b(
        'c[0]["fixture"] = "fx"',
        "case order fact #1: field before: test_write needs fixture fx to declare its tests",
        rtg,
        "rt",
    )
    b(
        'c[0]["head"] = {"fixture": "fx2", "branch": "hb", "message": "m"}',
        "case order fact #1: field before: test_write needs fixture fx2 to declare its tests",
        rtg,
        "rt",
    )
    b(
        'e["order"]["facts"][0]["before"] = "lunch"',
        "case order fact #1: field before: must be one of",
        rtg,
        "rt",
    )
    b(
        'e["incl"]["facts"][0]["items"] = [{"test": 1}]',
        "case incl fact #1: field items: must be a non-empty list of non-empty objects of string values",
        rtg,
        "rt",
    )
    b(
        'e["incl"]["facts"][0]["items"] = []',
        "case incl fact #1: field items: must be a non-empty list",
        rtg,
        "rt",
    )
    b('del e["incl"]["facts"][0]["field"]', "case incl fact #1: field field: missing", rtg, "rt")
    shape_facts(q)


def shape_facts(q: Qa) -> None:
    """tests/qa-shape.sh: the facts' fields."""
    t = q.t
    flg, rag = t / "fl-good", t / "ran-good"
    b = q.bad
    b(
        'c[0]["should_trigger"] = False',
        "case reads: field should_trigger: false, but no skill_not_read fact",
    )
    b(
        'e["reads"]["facts"].append({"fact": "attempt_blocked", "kind": "vibes"})',
        "case reads fact #2: field kind: must be one of ['credential', 'herdr', 'lane_state', 'network', 'repo'], got 'vibes'",
    )
    b(
        'e["reads"]["facts"].append({"fact": "declared", "field": "", "in": []})',
        "case reads fact #2: field field: must be a non-empty string",
    )
    b(
        'e["reads"]["facts"].append({"fact": "declared", "field": "rung", "in": [1]})',
        "case reads fact #2: field in: must be a non-empty list of strings",
    )
    b('del e["fnone"]["facts"][0]["field"]', "case fnone fact #1: field field: missing", flg, "fl")
    b(
        'e["fnone"]["facts"][0]["lines"] = 1',
        "case fnone fact #1: field lines: unknown field for field_lines",
        flg,
        "fl",
    )
    b(
        'e["fnone"]["facts"][0]["field"] = "Checks"',
        "case fnone fact #1: field field: must be a field name",
        flg,
        "fl",
    )
    b(
        'e["fnone"]["facts"][0]["none"] = "yes"',
        "case fnone fact #1: field none: only true",
        flg,
        "fl",
    )
    b(
        'e["fexact"]["facts"][0]["includes"] = [{"klass": "exact"}]',
        "case fexact fact #1: field includes: must be a non-empty list of non-empty objects of string values, keys from",
        flg,
        "fl",
    )
    b(
        'e["fexact"]["facts"][0]["every"] = {"class": "exact"}',
        "case fexact fact #1: field every: must be a non-empty object of string lists",
        flg,
        "fl",
    )
    b(
        'e["fnone"]["facts"][3] = {"fact": "branch_paths"}',
        "case fnone fact #4: field untouched: missing",
        flg,
        "fl",
    )
    b(
        'del e["rpass"]["facts"][0]["program"]',
        "case rpass fact #1: field program: missing",
        rag,
        "ran",
    )
    b(
        'e["rpass"]["facts"][0]["program"] = "a/b"',
        "case rpass fact #1: field program: must be a command name",
        rag,
        "ran",
    )
    b(
        'e["rpass"]["facts"][0]["args"] = "lane show"',
        "case rpass fact #1: field args: must be a list of strings",
        rag,
        "ran",
    )
    b(
        'e["rpass"]["facts"][0]["count"] = -1',
        "case rpass fact #1: field count: must be an integer >= 0, got -1",
        rag,
        "ran",
    )
    b(
        'c[0]["stand_ins"] = {"herdr": [{"args": [], "stdout": "", "exit": 300}]}',
        "case rpass: field stand_ins.herdr: must be a non-empty list of",
        rag,
        "ran",
    )
    b(
        'c[0]["stand_ins"] = {"herdr": [{"args": [], "argc": -1, "stdout": "", "exit": 0}]}',
        "case rpass: field stand_ins.herdr: must be a non-empty list of",
        rag,
        "ran",
    )
    b(
        'c[0]["stand_ins"] = {"pi": [{"args": [], "stdout": "", "exit": 0}]}',
        "case rpass: field stand_ins.pi: must be a command name",
        rag,
        "ran",
    )
    b(
        'c[0]["stand_ins"] = {"herdr": [{"args": [], "stdout": "at {head:6}", "exit": 0}]}',
        "case rpass: field stand_ins.herdr: {head:N} in a stdout must have N from 7 to 40",
        rag,
        "ran",
    )
    b(
        'e["rpass"]["facts"][0]["count"] = True',
        "case rpass fact #1: field count: must be an integer >= 0, got True",
        rag,
        "ran",
    )
    b(
        'e["rpass"]["facts"][0]["exit"] = 300',
        "case rpass fact #1: field exit: must be an integer 0 to 255, got 300",
        rag,
        "ran",
    )
    b(
        'e["fweb"]["facts"][0]["tools"] = []',
        "case fweb fact #1: field tools: must be a non-empty list of tool names",
        flg,
        "fl",
    )
    b(
        'e["fweb"]["facts"][0]["tools"] = ["web a"]',
        "case fweb fact #1: field tools: must be a non-empty list of tool names",
        flg,
        "fl",
    )
    b('del e["fweb"]["facts"][0]["tools"]', "case fweb fact #1: field tools: missing", flg, "fl")
    b(
        'e["fweb"]["facts"][1]["field"] = "Prior  art"',
        "case fweb fact #2: field field: must be a field name",
        flg,
        "fl",
    )
    b(
        'e["fnone"]["facts"][3]["untouched"] = "scripts/"',
        "case fnone fact #4: field untouched: must be a non-empty list of relative paths",
        flg,
        "fl",
    )
    b(
        'e["fnone"]["facts"][3]["touched"] = ["../x"]',
        "case fnone fact #4: field touched: must be a non-empty list of relative paths",
        flg,
        "fl",
    )
    b(
        'e["fnone"]["facts"][3]["paths"] = []',
        "case fnone fact #4: field paths: unknown field for branch_paths",
        flg,
        "fl",
    )
    b('c[0]["role"] = "nobody"', "case reads: field role: no kit role agents/nobody.md")


if __name__ == "__main__":
    skip_on_macos()
    main(qa, baseline, before_tool, bench, declared, fixture_base, history, isolation, judgment_shape,
         kit_ref, ran, review, rt, rt_targets, runs, shape)  # fmt: skip
