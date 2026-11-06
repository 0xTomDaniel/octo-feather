"""The scenarios of tests/gate/kit/test_qc_carry.py (its items), this file their command
(testkit.main): qc carry (quality spec #qc-carry, #acceptance-qc-carry) through octo-feather-qc
(what `just qc` runs), the status file and the qc report, with the testkit's fake herdr and the
stub judge tests/fixtures/qc-judge/pi (no model). A scratch target on a lane branch: its earlier
head h0 passes demos a, b, c, the agent fallback f (an entry with covers, no demo), the tagged
tests g and h (h with no covered path; both from h0's claims gate, `just check`), fails e and
gets insufficient evidence on i. Each later head is a merge of main changing one thing; what qc
on it carries or judges again: quality spec #qc-carry, each scenario below.

The target judged at h0 (`build_h0`), and then at h1, a merge of main changing src/b, which only b
covers (`build_h1`), are each prepared once per gate run (testkit Scratch.prepare); every later
scenario merges one more change into h1 (a carried a's second hop) and judges it."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from testkit import FIXTURES, ROOT, Ran, Scratch, kit, main, tool_homes
from testkit.qc import LIMIT_S

STATUS = "docs/specs/carry.status.json"
SPEC = "docs/specs/carry.spec.html"
IDS = ("a", "b", "c", "e", "f", "g", "h", "i")
CLAIMS = "carry#acceptance-g carry#acceptance-h"
# Unset in every scenario, as the old test unset them: a Herdr pane's session, a qc report dir, the
# stub judge's modes, the gate's claims (each gate run below sets its own).
UNSET = (
    "HERDR_SESSION",
    "HERDR_SOCKET_PATH",
    "HERDR_BIN_PATH",
    "HERDR_ENV",
    "OCTO_FEATHER_QC_DIR",
    "FAKE_QC_JUDGE",
    "FAKE_QC_FAIL",
    "OCTO_FEATHER_QC_CLAIMS",
)
JUSTFILE = """set positional-arguments
export GATE_RECIPES := "check-ok"
export OCTO_FEATHER_CHECK_RUN := `check-gate-free --run`
check: check-tests
check-ok:
    @true
check-tests *args:
    uv run --project "$KIT" --locked --offline --no-sync pytest "$@"
"""
CALL = (
    '{"at": "2026-11-05T00:00:00Z", "lane": "gh12", "role": "supervisor", "kind": "clarifies", '
    '"anchors": ["acceptance-c"], "criteria": ["acceptance-c"], "what": "w", "why": "w", '
    '"passes_as_written": false, "evidence": "e"}\n'
)


def spec(c_prints: str) -> str:
    """The carry spec: one criterion per id, c printing C_PRINTS."""

    def crit(i: str, prints: str = "ok") -> str:
        return (
            f'<p data-acceptance-criterion data-anchor="acceptance-{i}"><span '
            f"data-acceptance-scenario>Given a user, When {i} runs,</span> <span "
            f"data-acceptance-outcome>then it prints {prints}.</span></p>\n"
        )

    body = "".join(crit(i, c_prints if i == "c" else "ok") for i in IDS)
    return (
        '<!doctype html><html><body><article data-spec-contract="shaped-sections-v1">\n'
        '<section data-spec-section="acceptance" data-anchor="acceptance" id="acceptance">'
        f"<h2>Acceptance criteria</h2>\n{body}</section></article></body></html>\n"
    )


def demo(i: str, command: str | None) -> str:
    cmd = f"command = {json.dumps(command)}\n" if command is not None else ""
    return f'[demo."carry#acceptance-{i}"]\n{cmd}covers = ["src/{i}"]\n'


QC_TOML = (
    'format = 2\n[entry]\ncommand = "true"\n[services]\n[fixture.seed]\nreset = "true"\n'
    'path = "fixtures/seed"\n[values]\n'
    + demo("a", "echo a ok")
    + demo("b", "echo b ok")
    + demo("c", "echo c ok")
    + demo("e", "echo e broke >&2; exit 3")
    + demo("f", None)
    + demo("g", None)
    + demo("i", "echo needs a GPU, none here >&2; exit 77")
)


def tagged(cid: str, says: str) -> str:
    return f"#!/usr/bin/env bash\n# criterion: carry#acceptance-{cid}\necho {says} ok\n"


class Target:
    """The scratch target in S: its repo on the lane branch, the last qc run's results."""

    def __init__(self, s: Scratch) -> None:
        self.s = s
        self.repo = s.root / "repo"
        for k in UNSET:
            s.env.pop(k, None)
        s.env |= {
            "KIT": str(ROOT),
            "OCTO_FEATHER_QC_PATH": str(FIXTURES / "qc-judge"),  # the stub judge for f
        }

    def git(self, *args: str) -> str:
        return self.s.git(self.repo, *args)

    def head(self) -> str:
        return self.git("rev-parse", "HEAD")

    def write(self, rel: str, text: str, *, mode: int | None = None) -> None:
        p = self.repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        if mode is not None:
            p.chmod(mode)

    def merge(self, msg: str, **files: str) -> str:
        """FILES (rel path: text; a .sh executable) committed on main as MSG, main merged into the
        lane: a new lane head."""
        self.git("checkout", "-q", "main")
        for rel, text in files.items():
            self.write(rel, text, mode=0o755 if rel.endswith(".sh") else None)
        self.git("add", "-A")
        self.git("commit", "-qm", msg)
        self.git("checkout", "-q", "lane")
        self.git("merge", "-q", "--no-edit", "main")
        return self.head()

    def gate(self) -> None:
        """The lane head's claims gate (the target's `just check`, g and h claimed), green."""
        # The box's uv Pythons and cache and mise's installs, kept while HOME moves: the kit's
        # locked pytest, offline.
        env = tool_homes() | {"OCTO_FEATHER_QC_CLAIMS": CLAIMS}
        self.s.run(["timeout", "-k", "5", "300", "just", "check"], cwd=self.repo, env=env)

    def qc(self, want: int, *ids: str, pr: str = "9") -> Run:
        """octo-feather-qc for PR on the lane head, criteria IDS, bounded; it exits WANT."""
        h = self.head()
        cmd = ["timeout", "-k", "5", LIMIT_S, kit("octo-feather-qc"), STATUS, pr]
        r = self.s.run([*cmd, *(f"acceptance-{i}" for i in ids)], want=want, cwd=self.repo)
        return Run.of(r, h)

    def row(self, cid: str) -> tuple[Any, Any, str]:
        """acceptance-CID's status-file row: record, commit, status."""
        c = json.loads((self.repo / STATUS).read_text())["criteria"][f"acceptance-{cid}"]
        return c.get("record"), c.get("commit"), c["status"]


class Run:
    """One qc run: its stdout, stderr, judged head and report (the path its last line names)."""

    def __init__(self, out: str, err: str, head: str, report: dict[str, Any]) -> None:
        self.out, self.err, self.head, self.report = out, err, head, report

    @classmethod
    def of(cls, r: Ran, head: str) -> Run:
        rep = json.loads(Path(r.out.splitlines()[-1].rpartition("; report ")[2]).read_text())
        return cls(r.out, r.err, head, rep)

    def dump(self) -> dict[str, Any]:
        return {"out": self.out, "err": self.err, "head": self.head, "report": self.report}

    @classmethod
    def load(cls, d: dict[str, Any]) -> Run:
        return cls(d["out"], d["err"], d["head"], d["report"])

    def results(self, **want: str) -> None:
        """Each result in the report as WANT: carried@<head>:<record>, or judged:<verdict>."""
        r = {x["id"]: x for x in self.report["results"]}
        for i, how in want.items():
            x = r[f"acceptance-{i}"]
            said = f"{i}: {x}\nreport: {self.report}\n{self.out}"
            if how.startswith("carried@"):
                at, rec = how.removeprefix("carried@").split(":")
                assert x.get("carried") is True, said
                assert (x["verdict"], x["head"], x["record"]) == ("pass", at, rec), said
            else:
                assert not x.get("carried"), said
                assert x["verdict"] == how.removeprefix("judged:"), said
                assert x["head"] == self.head, said

    def said(self, pattern: str) -> None:
        """Stderr names PATTERN (a regex, as grep reads it)."""
        assert re.search(pattern, self.err), (
            f"qc at {self.head[:12]}: want stderr naming '{pattern}': {self.err}"
        )


def build_h0(p: Scratch) -> None:
    """The target, its lane's earlier head h0 gated (claims g and h) and judged on every id;
    h0's run and its rows of a, c and g in h0.json."""
    t = Target(p)
    r = t.repo
    r.mkdir()
    t.git("init", "-q", "-b", "main")
    for k, v in (("user.email", "t@t"), ("user.name", "t"), ("commit.gpgsign", "false")):
        t.git("config", k, v)
    t.git("commit", "-qm", "accepted", "--allow-empty")
    t.write(SPEC, spec("ok"))
    t.git("add", "-A")
    t.git("commit", "-qm", "spec")
    p.run(
        [kit("octo-feather-spec-status"), "init", SPEC, t.git("rev-parse", "--short", "HEAD")],
        cwd=r,
    )
    for name in ("conftest.py", "test_gate.py"):
        t.write(f"tests/gate/{name}", (ROOT / "tests" / "gate" / name).read_text())
    t.write(".gitignore", ".pytest_cache/\n__pycache__/\n")
    t.write(
        "pytest.ini",
        "[pytest]\ntestpaths = tests/gate\n"
        "addopts = --strict-markers --junitxml=.pytest_cache/junit.xml\n",
    )
    t.write("justfile", JUSTFILE)
    for i in ("g", "h"):
        t.write(f"tests/{i}.sh", tagged(i, i), mode=0o755)
    for i in ("a", "b", "c", "f", "g"):
        t.write(f"src/{i}", f"{i} v1\n")
    t.write("fixtures/seed", "seed v1\n")
    t.write("qc.toml", QC_TOML)
    t.git("add", "-A")
    t.git("commit", "-qm", "target")
    t.git("checkout", "-qb", "lane")
    t.gate()
    run = t.qc(1, *IDS)
    rows = {i: t.row(i)[0] for i in ("a", "c", "g")}
    (p.root / "h0.json").write_text(json.dumps({"run": run.dump(), "rows": rows}))


def build_h1(p: Scratch) -> None:
    """h0, then a merge of main changing src/b (h1) judged on every id; its run in h1.json."""
    p.prepare("qc-carry-h0", build_h0)
    t = Target(p)
    t.merge("main: src/b", **{"src/b": "b v2\n"})
    run = t.qc(1, *IDS)
    rows = {i: list(t.row(i)) for i in ("a", "b")}
    (p.root / "h1.json").write_text(json.dumps({"run": run.dump(), "rows": rows}))


def at_h0(s: Scratch) -> tuple[Target, Run, dict[str, str]]:
    s.prepare("qc-carry-h0", build_h0)
    d = json.loads((s.root / "h0.json").read_text())
    return Target(s), Run.load(d["run"]), d["rows"]


def at_h1(s: Scratch) -> tuple[Target, str, dict[str, str]]:
    """S holding h1: its target, h0 and h0's records of a, c and g."""
    s.prepare("qc-carry-h1", build_h1)
    d = json.loads((s.root / "h0.json").read_text())
    return Target(s), d["run"]["head"], d["rows"]


def first_head(s: Scratch) -> None:
    """The earlier head: every kind of result, each judged at h0."""
    _, run, _ = at_h0(s)
    run.results(
        a="judged:pass",
        b="judged:pass",
        c="judged:pass",
        e="judged:fail",
        f="judged:pass",
        g="judged:pass",
        h="judged:pass",
        i="judged:insufficient evidence",
    )


def covered_path(s: Scratch) -> None:
    """A merge of main changes src/b, which only b covers: b judged again; a, c and g carried with
    their head and record, g with no gate run here; the fallback's f, h with no covered path, the
    failed e and the insufficient i judged again. Only b, e and i's demos run; a and b built, a at
    h0, b at h1."""
    _, h0, rec = at_h1(s)
    d = json.loads((s.root / "h1.json").read_text())
    run, rows = Run.load(d["run"]), d["rows"]
    run.results(
        a=f"carried@{h0}:{rec['a']}",
        c=f"carried@{h0}:{rec['c']}",
        g=f"carried@{h0}:{rec['g']}",
        b="judged:pass",
        e="judged:fail",
        f="judged:pass",
        h="judged:insufficient evidence",
        i="judged:insufficient evidence",
    )
    ls = run.out.splitlines()
    n = next(k for k, x in enumerate(ls) if x.startswith("PASS acceptance-a: "))
    assert f"carried: judged at {h0[:12]}, record {rec['a']}" in ls[n + 1], (
        f"carried a not shown with its head and record: {run.out}"
    )
    demos = [x for x in run.err.splitlines() if x.startswith("qc: demo ")]
    assert len(demos) == 3, f"want only b, e and i's demos run: {run.err}"
    assert rows["a"] == [rec["a"], h0, "built"], rows
    assert rows["b"][1:] == [run.head, "built"], rows
    run.said("covered path src/b changed")
    run.said("acceptance-f again: judged by the agent fallback")
    run.said("acceptance-h again: no covered path")


def gate_config(s: Scratch) -> None:
    """The gate configuration (the justfile) moves: g judged again from its new gate record; a
    carried."""
    t, h0, rec = at_h1(s)
    t.merge("main: justfile", justfile=JUSTFILE + "# a comment\n")
    t.gate()
    run = t.qc(0, "a", "g")
    run.results(a=f"carried@{h0}:{rec['a']}", g="judged:pass")
    run.said("acceptance-g again: gate configuration")


def moved_text(s: Scratch) -> None:
    """c's text moves (a clarifying call beside it), and g's named test: both judged again (g with
    no gate record here, so insufficient); a carried."""
    t, h0, rec = at_h1(s)
    t.merge(
        "main: c text, tests/g.sh",
        **{
            SPEC: spec("OK"),
            "docs/specs/carry.calls.jsonl": CALL,
            "tests/g.sh": tagged("g", "g") + "echo g2\n",
        },
    )
    run = t.qc(2, "a", "c", "g")
    run.results(a=f"carried@{h0}:{rec['a']}", c="judged:pass", g="judged:insufficient evidence")
    run.said("acceptance-c again: .*criterion text changed")
    run.said("acceptance-g again: .*test file tests/g.sh changed")


def newly_tagged(s: Scratch) -> None:
    """A test newly tagged with c: c judged again (no gate record here, so insufficient); a
    carried."""
    t, h0, rec = at_h1(s)
    h = t.merge("main: tests/c2.sh", **{"tests/c2.sh": tagged("c", "c2")})
    run = t.qc(2, "a", "c")
    run.results(a=f"carried@{h0}:{rec['a']}", c="judged:insufficient evidence")
    run.said(
        rf"acceptance-c again: newly tagged at {h[:12]}: "
        r"tests/gate/test_gate.py::test_script\[tests/c2.sh\]"
    )


def fixture_moved(s: Scratch) -> None:
    """The fixture a's contract names moves: a judged again."""
    t, _, _ = at_h1(s)
    t.merge("main: fixture", **{"fixtures/seed": "seed v2\n"})
    run = t.qc(0, "a")
    run.results(a="judged:pass")
    run.said("acceptance-a again: fixture")


def contract_moved(s: Scratch) -> None:
    """The contract (qc.toml) moves: a judged again."""
    t, _, _ = at_h1(s)
    t.merge("main: contract", **{"qc.toml": QC_TOML + "# a comment\n"})
    run = t.qc(0, "a")
    run.results(a="judged:pass")
    run.said("acceptance-a again: contract")


def other_lane(s: Scratch) -> None:
    """Another lane (PR 10) naming a, built in PR 9: judged again, never carried from lane 9's
    pass."""
    t, _, _ = at_h1(s)
    t.merge("main: src/b again", **{"src/b": "b v3\n"})
    run = t.qc(0, "a", pr="10")
    run.results(a="judged:pass")
    run.said("acceptance-a again: built in PR #9")


if __name__ == "__main__":
    main(
        first_head,
        covered_path,
        gate_config,
        moved_text,
        newly_tagged,
        fixture_moved,
        contract_moved,
        other_lane,
    )
