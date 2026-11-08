"""qc's advisory model judgment (quality spec #qc-judgment, #qc-results, #acceptance-qc-advisory;
judgment spec #question-criterion-evidence, #rule-advisory), through octo-feather-qc (what `just
qc` runs) with the fake herdr and the stub classifier pi (tests/fixtures/classify-stub/pi) at
the model boundary, no model: a scratch target declares a passing and a failing demo. Each
recorded criterion gets the criterion-evidence question through the one classify path, its state
the criterion's text, the demo's command and output; the answer and confidence show beside the
result, labelled an advisory model judgment, and in the report's results. Whatever the model
says or when it fails, the verdicts, exit status and status commit are the same. One qc run per
scenario (the sandboxed classify is the behaviour under test); the target is prepared once per
gate run."""

from __future__ import annotations

import json
import os
import re
import shutil
import time
from pathlib import Path

from testkit import Scratch, main
from testkit.qc import MODEL, RID, qc, target

QC_TOML = """format = 1
[entry]
command = "true"
[services]
[fixture]
[values]
[demo."demo#acceptance-a"]
command = "echo a checks pass"
covers = ["src/a"]
tests = ["tests/a.sh"]
[demo."demo#acceptance-b"]
command = "echo b checks fail >&2; exit 3"
covers = ["src/b"]
tests = ["tests/b.sh"]
"""
IDS = ("acceptance-a", "acceptance-b")
SAID = (
    "  advisory model judgment (no gate reads it): {}, confidence {} "
    "(criterion-evidence by {}; uncalibrated)"
)
NONE = (
    "  advisory model judgment unavailable (criterion-evidence by {}): {}; "
    "the result stands as decided"
)
LACKS_A = 'stub: state lacks "\\nOutput:\\na checks pass"'
B_STATE = (
    "Criterion demo#acceptance-b: Given a user, When acceptance-b runs, then it prints ok.\n"
    "Command: echo b checks fail >&2; exit 3\nOutput:\nb checks fail"
)
LIMIT_S = 90  # a refused pi: the run ends well before the classify timeout (#493 AC1, #495)


def build(p: Scratch) -> None:
    target(p, {"qc.toml": QC_TOML})


class Run:
    """One qc run on IDS (both by default) at the target's head: PASS acceptance-a and FAIL
    acceptance-b from the demos' checks, the exit and status commit they give, whatever the advisory
    said: a built and committed when judged, else the head unchanged."""

    def __init__(
        self, s: Scratch, ids: tuple[str, ...] = IDS, path: str | None = None, **stub: str
    ) -> None:
        s.prepare("qc-advisory", build)
        r = s.root / "repo"
        head = s.git(r, "rev-parse", "HEAD")
        env = {**stub, **({"PATH": path} if path else {})}
        t = time.monotonic()
        ran = qc(s, r, "9", *ids, want=1 if IDS[1] in ids else 0, env=env)
        self.seconds = time.monotonic() - t
        self.out, self.err = ran.out, ran.err
        self.lines = self.out.splitlines()
        for v, i, cmd in (
            ("PASS", IDS[0], "echo a checks pass"),
            ("FAIL", IDS[1], "echo b checks fail >&2; exit 3"),
        ):
            if i in ids:
                n = self.lines.index(f"{v} {i}: $ {cmd}")
                rec = f"  evidence complete; decision demo checks; record {RID}"
                assert any(re.fullmatch(rec, x) for x in self.lines[n + 1 : n + 4]), self.out
        if IDS[0] in ids:
            subject = s.git(r, "log", "-1", "--format=%s")
            assert subject == f"qc: built acceptance-a (judged {head[:12]})", subject
        else:
            assert s.git(r, "rev-parse", "HEAD") == head, "a run building nothing committed"
        rep = json.loads(Path(self.lines[-1].rpartition("; report ")[2]).read_text())
        self.results = {x["id"]: x for x in rep["results"]}

    def adv(self, cid: str) -> str:
        """The advisory line right under CID's record line."""
        n = next(k for k, x in enumerate(self.lines) if re.match(rf"[A-Z]* {cid}: ", x))
        rec = next(
            k
            for k in range(n + 1, n + 5)
            if re.fullmatch(
                rf"  evidence complete; decision demo checks; record {RID}", self.lines[k]
            )
        )
        return self.lines[rec + 1]

    def advisory(self, cid: str) -> dict[str, object]:
        """CID's advisory in the report's results, labelled a model judgment by the kit's model."""
        a = self.results[cid]["advisory"]
        assert a["judgment"].startswith("model judgment"), a
        assert "advisory: no gate reads it" in a["judgment"], a
        assert (a["question"], a["model"]) == ("criterion-evidence", MODEL), a
        return a


def does_not_show(s: Scratch) -> None:
    """The model, induced, says the passing demo's evidence does not show its criterion: it still
    passes. The classifier refuses a state without a's output, so b's answer is unavailable."""
    q = Run(s, STUB_ANSWER="does-not-show", STUB_WANT="\nOutput:\na checks pass")
    asked = (
        f"qc: advisory criterion-evidence question to {MODEL} for 2 recorded criteria "
        "(no gate reads it)"
    )
    assert asked in q.err, q.err
    assert q.adv(IDS[0]) == SAID.format("does-not-show", "0.910", MODEL), q.out
    assert q.adv(IDS[1]) == NONE.format(MODEL, LACKS_A), q.out
    a = q.advisory(IDS[0])
    assert (a["answer"], a["confidence"]) == ("does-not-show", 0.91), a
    assert q.advisory(IDS[1])["unavailable"] == LACKS_A


def shows(s: Scratch) -> None:
    """The failing demo, the model says shows: still a failure. Its state is exactly the
    criterion's text, command and output."""
    q = Run(s, IDS[1:], STUB_ANSWER="shows", STUB_CONFIDENCE="0.77", STUB_WANT=B_STATE)
    assert q.adv(IDS[1]) == SAID.format("shows", "0.770", MODEL), q.out
    a = q.advisory(IDS[1])
    assert (a["answer"], a["confidence"]) == ("shows", 0.77), a


def unavailable(s: Scratch) -> None:
    """The classifier fails on every call: both show unavailable, the results as decided."""
    q = Run(s)
    for i in IDS:
        assert q.adv(i) == NONE.format(MODEL, "stub: provider error"), q.out
        assert q.advisory(i)["unavailable"] == "stub: provider error"


def node_shim(s: Scratch) -> None:
    """From a bare pane (#465): the node first on PATH is mise's shim (a link to mise named node).
    In qc's advice run (a scratch dir pinning no node; the sandbox turns the shims' system fallback
    off) it resolves no version; the answer still comes."""
    shim = s.root / "shim"
    shim.mkdir()
    mise = shutil.which("mise", path=s.env["PATH"])
    assert mise, "no mise on PATH"
    (shim / "node").symlink_to(mise)
    q = Run(s, IDS[:1], f"{shim}{os.pathsep}{s.env['PATH']}", STUB_ANSWER="does-not-show")
    assert q.adv(IDS[0]) == SAID.format("does-not-show", "0.910", MODEL), q.out


def no_pi(s: Scratch, how: str) -> None:
    """No pi on the box (nopi), or a pi on PATH that only leads back to the sandbox's pi shim, one
    running the bare name pi (loop), #493 AC1: the shim refuses both
    (scripts/octo-feather-qc-sandbox, its pi shim): each advisory unavailable naming pi's exit 127,
    the run ending before LIMIT_S. PATH with every pi gone: each dir holding one mirrored minus
    it."""
    assert shutil.which("pi", path=s.env["PATH"]) == str(s.bin / "pi"), (
        "the first pi on PATH is not the stub"
    )
    (s.bin / "pi").unlink()
    dirs: list[str] = []
    for n, d in enumerate(map(Path, filter(None, s.env["PATH"].split(os.pathsep)))):
        if not (d / "pi").is_symlink() and not (d / "pi").exists():
            dirs.append(str(d))
            continue
        m = s.root / f"nopi.{n}"
        m.mkdir()
        for f in sorted(d.iterdir()) if d.is_dir() else []:
            if f.name != "pi":
                (m / f.name).symlink_to(f)
        dirs.append(str(m))
    path = os.pathsep.join(dirs)
    assert shutil.which("pi", path=path) is None, "pi hidden, yet PATH holds one"
    if how == "loop":
        loop = s.root / "loop"
        loop.mkdir()
        (loop / "pi").write_text('#!/bin/sh\nexec pi "$@"\n')
        (loop / "pi").chmod(0o755)
        path = f"{loop}{os.pathsep}{path}"
    q = Run(s, IDS, path)
    assert q.seconds < LIMIT_S, f"{how}: qc took {q.seconds:.0f} s (limit {LIMIT_S})"
    refused = (
        rf"  advisory model judgment unavailable \(criterion-evidence by {re.escape(MODEL)}\): "
        r".*pi exit 127.*; the result stands as decided"
    )
    for i in IDS:
        assert re.fullmatch(refused, q.adv(i)), (
            f"{how}: {i}: no advisory unavailable naming pi exit 127: {q.out}"
        )


def sprint(s: Scratch) -> None:
    """Explicit authorization leaves real demo outcomes intact without starting a classifier."""
    (s.bin / "pi").unlink()
    (s.bin / "pi").write_text("#!/bin/sh\necho CLASSIFIER_CALLED >&2\nexit 99\n")
    (s.bin / "pi").chmod(0o755)
    q = Run(
        s,
        OCTO_FEATHER_QC_ADVISORY_AUTHORITY="gpt-only-sprint-2026-11-08",
        OCTO_FEATHER_QC_ADVISORY_SCOPE="revision-repair",
    )
    assert "CLASSIFIER_CALLED" not in q.err + q.out
    assert "qc: advisory criterion-evidence question" not in q.err
    for i in IDS:
        a = q.results[i]["advisory"]
        assert a == {
            "status": "NOT RUN",
            "authority": "gpt-only-sprint-2026-11-08",
            "scope": "revision-repair",
            "expiry": "sprint pause after final cleanup",
        }
        assert "advisory NOT RUN" in q.adv(i)


def incomplete_sprint(s: Scratch) -> None:
    """Authorization cannot turn a demo that never completed into a built criterion."""
    s.prepare("qc-advisory", build)
    r = s.root / "repo"
    (r / "qc.toml").write_text(QC_TOML.replace("echo a checks pass", "exit 77"))
    s.git(r, "add", "qc.toml")
    s.git(r, "commit", "-qm", "demo cannot complete")
    head = s.git(r, "rev-parse", "HEAD")
    ran = qc(
        s,
        r,
        "9",
        *IDS[:1],
        want=2,
        env={
            "OCTO_FEATHER_QC_ADVISORY_AUTHORITY": "gpt-only-sprint-2026-11-08",
            "OCTO_FEATHER_QC_ADVISORY_SCOPE": "light-test",
        },
    )
    rep = json.loads(Path(ran.out.splitlines()[-1].rpartition("; report ")[2]).read_text())
    result = rep["results"][0]
    assert result["verdict"] == "insufficient evidence"
    assert result["evidence"] == "incomplete"
    assert result["missing"]
    assert result["advisory"]["status"] == "NOT RUN"
    assert s.git(r, "rev-parse", "HEAD") == head
    assert (
        json.loads((r / "docs/specs/demo.status.json").read_text())["criteria"][IDS[0]]["status"]
        == "planned"
    )


def refused_sprint(s: Scratch, how: str) -> None:
    """Unsupported authorization cannot launch advice or replace fallback judgment."""
    s.prepare("qc-advisory", build)
    r = s.root / "repo"
    env = {
        "OCTO_FEATHER_QC_ADVISORY_AUTHORITY": "gpt-only-sprint-2026-11-08",
        "OCTO_FEATHER_QC_ADVISORY_SCOPE": "sandbox",
    }
    ids = IDS
    if how == "authority":
        env["OCTO_FEATHER_QC_ADVISORY_AUTHORITY"] = "unknown"
    elif how == "scope":
        env["OCTO_FEATHER_QC_ADVISORY_SCOPE"] = "ordinary"
    elif how == "missing":
        del env["OCTO_FEATHER_QC_ADVISORY_SCOPE"]
    else:
        (r / "qc.toml").write_text(QC_TOML.split('[demo."demo#acceptance-b"]', maxsplit=1)[0])
        s.git(r, "add", "qc.toml")
        s.git(r, "commit", "-qm", "criterion b needs fallback")
        ids = IDS[1:]
    head = s.git(r, "rev-parse", "HEAD")
    ran = qc(s, r, "9", *ids, want=64, env=env)
    assert "advisory authorization requires" in ran.err
    assert s.git(r, "rev-parse", "HEAD") == head


if __name__ == "__main__":
    main(
        does_not_show,
        shows,
        unavailable,
        node_shim,
        no_pi,
        sprint,
        refused_sprint,
        incomplete_sprint,
    )
