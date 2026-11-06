"""The scenarios of tests/gate/kit/test_spec_status.py (its items), this file their command
(testkit.main): scripts/octo-feather-spec-status, run directly in throwaway git repos whose
accepted_commit is real (the fixture repos, prepared once per gate run).

- `links`: one good and one bad fixture (tests/fixtures/spec-status/), init and built on a copy;
  evidence links (quality #qc-results, #acceptance-built-links): built names its record, the
  commit it was captured at and its demo's tests; check accepts that shape and a legacy built row,
  and refuses a partial or malformed link and a planned criterion with one; staleness (#qc-stale,
  #acceptance-evidence-stale): `show` names each built criterion current or stale (covered path,
  test file edited or gone, criterion text; a fallback-built one by its text only).
- `guard`: the call log and the guard on a spec changed since its accepted commit
  (issue-lifecycle #gates-spec-calls): an unlogged, a denied-only, a removed and an added
  criterion with the wrong kind each fail, all reported by one check run; logged with the right
  kinds they pass; each log rule fails naming file, line and fix, every bad line of one log on one
  run (the checker names each line); #acceptance-call-evidence; a Linear lane key passes; a
  missing accepted_commit is named; #acceptance-call-guard structure: a moved or reordered
  criterion needs a call naming its sections.
- `calls` (#acceptance-call-listed, -added, -weakens, -many, -denied): the lane's calls since its
  base, grouped weakens, adds, clarifies as #gates-call-loudness orders them; a call already at the
  base is not the lane's, even once denied; a fourth call prints the more-than-three line; the
  default base is the merge base with origin/main, none an error naming the fix.
"""

from __future__ import annotations

import json
import re
import shutil
from typing import TYPE_CHECKING

from testkit import FIXTURES, Scratch, kit, main

if TYPE_CHECKING:
    from pathlib import Path

TAG = "spec-status test"
S = kit("octo-feather-spec-status")
F = FIXTURES / "spec-status"
NOCONF = {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}
A_OK = "then it prints ok.</span></p>"


def repo(p: Scratch, name: str, fixture: str) -> Path:
    """A git repo holding FIXTURE's files in docs/specs, committed; accepted_commit names that
    commit."""
    r = p.root / name
    d = r / "docs" / "specs"
    d.mkdir(parents=True)
    for f in (F / fixture).iterdir():
        shutil.copy2(f, d / f.name)
    p.git(r, "init", "-q")
    p.git(r, "add", "-A")
    p.git(r, "commit", "-qm", "accepted")
    sha = p.git(r, "rev-parse", "--short", "HEAD")
    for st in d.glob("*.status.json"):
        st.write_text(st.read_text().replace("0123abc", sha))
    p.git(r, "commit", "-qam", "status")
    return r


def crit(cid: str) -> str:
    return (
        f'<p data-acceptance-criterion data-anchor="{cid}">Given a user, When {cid} runs, '
        "then it prints ok.</p>\n"
    )


def mspec(required: list[str], optional: list[str]) -> str:
    return (
        '<!doctype html>\n<html><body><article data-spec-contract="shaped-sections-v1">\n'
        '<section data-anchor="acceptance-required"><h2>Required</h2>\n'
        + "".join(map(crit, required))
        + '</section>\n<section data-anchor="acceptance-optional"><h2>Optional</h2>\n'
        + "".join(map(crit, optional))
        + "</section>\n</article></body></html>\n"
    )


def call(kind: str, anchors: list[str], criteria: list[str], **over: object) -> dict[str, object]:
    c: dict[str, object] = {
        "at": "2026-10-21T10:00:00Z",
        "lane": "gh62",
        "role": "supervisor",
        "kind": kind,
        "anchors": anchors,
        "criteria": criteria,
        "what": "w",
        "why": "y",
        "passes_as_written": False,
        "evidence": "e",
    }
    c.update(over)
    return c


def line(c: dict[str, object] | str) -> str:
    return (c if isinstance(c, str) else json.dumps(c)) + "\n"


def build(p: Scratch) -> None:
    repo(p, "good", "good")
    repo(p, "bad", "bad")
    repo(p, "guard", "good")
    m = p.root / "move"
    md = m / "docs" / "specs"
    md.mkdir(parents=True)
    (md / "demo.spec.html").write_text(mspec(["acceptance-a", "acceptance-b"], []))
    p.git(m, "init", "-q")
    p.git(m, "add", "-A")
    p.git(m, "commit", "-qm", "accepted")
    sha = p.git(m, "rev-parse", "--short", "HEAD")
    (md / "demo.status.json").write_text(
        json.dumps(
            {
                "spec": "demo.spec.html",
                "accepted_commit": sha,
                "criteria": {
                    "acceptance-a": {"status": "planned", "pr": None},
                    "acceptance-b": {"status": "planned", "pr": None},
                },
            }
        )
        + "\n"
    )
    p.git(m, "add", "-A")
    p.git(m, "commit", "-qm", "status")
    c = repo(p, "calls", "good")
    lcall_ = lcall("clarifies", "old-call", "gh50")
    (c / "docs/specs/demo.calls.jsonl").write_text(line(lcall_))
    p.git(c, "add", "-A")
    p.git(c, "commit", "-qm", "earlier lane")


def lcall(kind: str, what: str, lane: str, **over: object) -> dict[str, object]:
    return call(
        kind,
        ["acceptance-a"],
        ["acceptance-a"],
        lane=lane,
        what=what,
        why=f"why-{what}",
        evidence=f"ev-{what}",
        **over,
    )


def world(s: Scratch) -> None:
    s.prepare("spec-status", build)
    s.env |= NOCONF


def has(out: str, *wants: str) -> None:
    for w in wants:
        assert w in out, f"{TAG}: did not report: {w}\n{out}"


def run(s: Scratch, want: int, *cmd: str, cwd: Path | None = None) -> str:
    r = s.run([S, *cmd], want=want, cwd=cwd)
    return f"{r.out}\n{r.err}"


def guard(s: Scratch) -> None:
    world(s)
    r = s.root / "guard"
    d = r / "docs" / "specs"
    spec, status, log = d / "demo.spec.html", d / "demo.status.json", d / "demo.calls.jsonl"
    check = ("check", str(d))
    orig_spec, orig_status = spec.read_text(), status.read_text()

    def a_line(ln: str) -> bool:
        return 'data-anchor="acceptance-a"' in ln

    # An anchored paragraph changed since accepted_commit with no call fails, naming spec and
    # anchor.
    spec.write_text(
        "".join(
            ln.replace(A_OK, "then it prints done.</span></p>") if a_line(ln) else ln
            for ln in orig_spec.splitlines(keepends=True)
        )
    )
    has(
        run(s, 1, *check),
        "demo.spec.html: anchor acceptance-a changed since accepted_commit",
        "calls.jsonl",
    )
    # Beside it, acceptance-b removed and acceptance-c added (their parent section changed too).
    spec.write_text(
        spec.read_text()
        .replace('data-anchor="acceptance-b"', 'data-anchor="acceptance-c"')
        .replace("When acceptance-b runs", "When acceptance-c runs")
    )
    st = json.loads(orig_status)
    st["criteria"].pop("acceptance-b")
    st["criteria"]["acceptance-c"] = {"status": "planned", "pr": None}
    status.write_text(json.dumps(st))
    # Wrong calls: a's only call denied, b's and c's of kind clarifies.
    log.write_text(
        line(
            call(
                "clarifies",
                ["acceptance-a"],
                ["acceptance-a"],
                denied={"at": "2026-10-21T11:00:00Z", "note": "no"},
            )
        )
        + line(call("clarifies", ["acceptance-b"], ["acceptance-b"]))
        + line(call("clarifies", ["acceptance-c"], ["acceptance-c"]))
    )
    out = run(s, 1, *check)
    has(
        out,
        "anchor acceptance-a changed",
        "criterion acceptance-b removed since accepted_commit",
        "kind weakens",
        "criterion acceptance-c added since accepted_commit",
        "kind adds",
    )
    # The right calls: clarifies, weakens and adds naming the parent section.
    log.write_text(
        line(call("clarifies", ["acceptance-a"], ["acceptance-a"]))
        + line(call("weakens", ["acceptance-b", "acceptance"], ["acceptance-b"]))
        + line(call("adds", ["acceptance-c", "acceptance"], ["acceptance-c"]))
    )
    run(s, 0, *check)
    # Each log rule fails naming file, line and fix: line 1 a Linear lane key (eng-123 passes
    # like gh62), then one bad line each.
    spec.write_text(orig_spec)
    status.write_text(orig_status)
    g77 = {"lane": "gh77"}
    bad: list[tuple[dict[str, object] | str, str]] = [
        ('{"at": ', "not a JSON object"),
        (
            {
                k: v
                for k, v in call("clarifies", ["acceptance-a"], ["acceptance-a"]).items()
                if k != "why"
            },
            "missing or empty field why",
        ),
        # #acceptance-call-evidence: an empty, missing or blank evidence fails, naming that call.
        (
            call("clarifies", ["acceptance-a"], ["acceptance-a"], evidence="", **g77),
            "call (lane gh77; anchors acceptance-a): missing or empty field evidence",
        ),
        (
            {
                k: v
                for k, v in call("clarifies", ["acceptance-a"], ["acceptance-a"], **g77).items()
                if k != "evidence"
            },
            "call (lane gh77; anchors acceptance-a): missing or empty field evidence",
        ),
        (
            call("clarifies", ["acceptance-a"], ["acceptance-a"], evidence="  \n\t", **g77),
            "call (lane gh77; anchors acceptance-a): missing or empty field evidence",
        ),
        (
            call("clarifies", ["acceptance-a"], ["acceptance-a"], what=" \t"),
            "missing or empty field what",
        ),
        (call("clarifies", [" "], ["acceptance-a"]), "missing or empty field anchors"),
        (
            call("clarifies", ["acceptance-a"], ["acceptance-a"], role="implementer"),
            "role 'implementer'",
        ),
        (
            call("clarifies", ["acceptance-a"], ["acceptance-a"], passes_as_written=True),
            "passes_as_written must be false",
        ),
        (call("tweaks", ["acceptance-a"], ["acceptance-a"]), "kind 'tweaks' is not one of"),
        (
            call("clarifies", ["acceptance-a"], ["acceptance-q"]),
            "criterion acceptance-q is in neither",
        ),
    ]
    bad += [
        (
            call("clarifies", ["acceptance-a"], ["acceptance-a"], lane=ln),
            f"lane '{ln}' is not a lane key",
        )
        for ln in ("ENG-123", "62", "gh62-x", "eng-123-x")
    ]
    log.write_text(
        line(call("clarifies", ["acceptance-a"], ["acceptance-a"], lane="eng-123"))
        + "".join(line(c) for c, _ in bad)
    )
    out = run(s, 1, *check)
    assert "demo.calls.jsonl:1:" not in out, f"{TAG}: a Linear lane key's call refused: {out}"
    for n, (_, want) in enumerate(bad, 2):
        hit = [ln for ln in out.splitlines() if f"demo.calls.jsonl:{n}: " in ln]
        assert any(want in ln and "fix: " in ln for ln in hit), (
            f"{TAG}: line {n} did not report: {want}\n{out}"
        )
    # An accepted_commit missing from the repo is named.
    log.unlink()
    status.write_text(
        re.sub(r'"accepted_commit": "[0-9a-f]+"', '"accepted_commit": "deadbee"', orig_status)
    )
    has(run(s, 1, *check), "accepted_commit deadbee is not in this repo", "fetch full history")
    # #acceptance-call-guard, structure: moving an unchanged criterion between anchored sections,
    # or reordering two anchored siblings, changes the parents, so it needs a call naming them.
    m = s.root / "move" / "docs" / "specs"
    ms, ml = m / "demo.spec.html", m / "demo.calls.jsonl"
    mc = ("check", str(m))
    run(s, 0, *mc)
    ms.write_text(mspec(["acceptance-b"], ["acceptance-a"]))
    out = run(s, 1, *mc)
    has(
        out,
        "anchor acceptance-optional changed since accepted_commit",
        "anchor acceptance-required changed since accepted_commit",
    )
    assert "anchor acceptance-a " not in out, (
        f"{TAG}: unchanged moved criterion reported as changed: {out}"
    )
    ml.write_text(
        line(call("clarifies", ["acceptance-required", "acceptance-optional"], ["acceptance-a"]))
    )
    run(s, 0, *mc)
    ml.unlink()
    ms.write_text(mspec(["acceptance-b", "acceptance-a"], []))
    has(run(s, 1, *mc), "anchor acceptance-required changed since accepted_commit")
    ml.write_text(line(call("clarifies", ["acceptance-required"], ["acceptance-a"])))
    run(s, 0, *mc)


def calls(s: Scratch) -> None:
    world(s)
    c = s.root / "calls"
    cl = c / "docs/specs/demo.calls.jsonl"
    base = s.git(c, "rev-parse", "HEAD")
    old = json.loads(cl.read_text())
    old["denied"] = {"at": "2026-10-22T09:00:00Z", "note": "old"}
    cl.write_text(
        line(old)
        + line(lcall("clarifies", "what-clar", "gh63"))
        + line(lcall("adds", "what-add", "gh63"))
        + line(
            lcall(
                "weakens",
                "what-weak",
                "gh63",
                denied={"at": "2026-10-22T10:00:00Z", "note": "keep it"},
            )
        )
    )
    out = run(s, 0, "calls", "--since", base, "docs/specs", cwd=c)
    has(
        out,
        "3 calls (1 weakens, 1 adds, 1 clarifies; 1 denied).",
        "weakens DENIED (2026-10-22T10:00:00Z: keep it): docs/specs/demo.spec.html, lane gh63, "
        "role supervisor",
        "   why: why-what-weak",
        "   evidence: ev-what-add",
        "   anchors: acceptance-a",
        "   criteria: acceptance-a",
    )
    assert "old-call" not in out, f"{TAG}: a call at the base was listed: {out}"
    assert "more than three" not in out, (
        f"{TAG}: three calls printed the more-than-three line: {out}"
    )
    lines = out.splitlines()
    at = [
        next((i for i, ln in enumerate(lines) if w in ln), -1)
        for w in (
            "Weakens or removes",
            "what-weak",
            "Adds scope",
            "what-add",
            "Clarifies or adds detail",
            "what-clar",
        )
    ]
    assert -1 not in at, f"{TAG}: calls not all listed: {out}"
    assert at == sorted(at), f"{TAG}: calls not grouped weakens, adds, clarifies: {out}"
    with cl.open("a") as fh:
        fh.write(line(lcall("clarifies", "what-four", "gh63")))
    has(
        run(s, 0, "calls", "--since", base, cwd=c),
        "4 calls",
        "Lane gh63 made 4 calls, more than three: the director tells the owner",
    )
    # Default base: the merge base with origin/main; none is an error naming the fix.
    has(run(s, 1, "calls", cwd=c), "no merge base with origin/main", "--since REF")
    s.git(c, "update-ref", "refs/remotes/origin/main", base)
    has(run(s, 0, "calls", cwd=c), "4 calls")


RA, RB, RC = "20261029T100000Z-0a0a0a0a", "20261029T100000Z-0b0b0b0b", "20261029T100000Z-0c0c0c0c"
QC_TOML = """format = 1
[entry]
command = "true"
[services]
[fixture]
[values]
[demo."demo#acceptance-a"]
command = "true"
covers = ["src/a"]
tests = ["tests/a.sh"]
[demo."demo#acceptance-b"]
command = "true"
covers = ["src/b"]
tests = ["tests/b.py::test_b"]
"""


class Stale:
    """The staleness repo: demo.spec.html, qc.toml declaring both demos, their code and tests."""

    def __init__(self, s: Scratch) -> None:
        self.s = s
        self.e = s.root / "stale"
        self.es = self.e / "docs/specs"
        self.st = self.es / "demo.status.json"

    def commit(self, msg: str) -> str:
        self.s.git(self.e, "commit", "-qam", msg)
        return self.s.git(self.e, "rev-parse", "--short=12", "HEAD")

    def show(self) -> str:
        return run(self.s, 0, "show", cwd=self.e)

    def built(self, cid: str, *link: str) -> None:
        run(self.s, 0, "built", str(self.st), "7", cid, *link)


def crit_line(out: str, cid: str) -> str:
    hit = [ln for ln in out.splitlines() if f"  {cid}: " in ln]
    assert hit, f"{TAG}: show: no line for {cid}: {out}"
    return hit[0]


def on(out: str, cid: str, want: str, what: str) -> None:
    assert want in crit_line(out, cid), f"{TAG}: {what}: {out}"


def fixtures(s: Scratch) -> None:
    """The good and bad fixtures; init and built on a copy."""
    run(s, 0, "check", str(s.root / "good/docs/specs"))
    has(
        run(s, 1, "check", str(s.root / "bad/docs/specs")),
        "missing criterion acceptance-b",
        "extra criterion acceptance-z",
        "duplicate key 'acceptance-a'",
        "duplicate criterion id acceptance-c",
        "status must be planned or built",
        "a built criterion names the PR",
    )
    i = s.root / "init"
    i.mkdir()
    shutil.copy2(F / "good/demo.spec.html", i)
    s.git(i, "init", "-q")
    s.git(i, "add", "-A")
    s.git(i, "commit", "-qm", "spec")
    run(s, 0, "init", str(i / "demo.spec.html"), s.git(i, "rev-parse", "HEAD"))
    run(s, 0, "built", str(i / "demo.status.json"), "7", "acceptance-a")
    run(s, 0, "check", str(i))
    status = (i / "demo.status.json").read_text()
    assert '"pr": 7' in status, f"{TAG}: built did not record the PR"


def linked(x: Stale) -> str:
    """Both criteria built with an evidence link at the capture commit, committed; that commit."""
    s, e = x.s, x.e
    x.es.mkdir(parents=True)
    (e / "src").mkdir()
    (e / "tests").mkdir()
    shutil.copy2(F / "good/demo.spec.html", x.es)
    (e / "qc.toml").write_text(QC_TOML)
    for f in ("src/a", "src/b", "tests/a.sh", "tests/b.py", "README"):
        (e / f).write_text(f"{f} v1\n")
    s.git(e, "init", "-q")
    s.git(e, "add", "-A")
    s.git(e, "commit", "-qm", "accepted")
    cap = s.git(e, "rev-parse", "HEAD")
    run(s, 0, "init", str(x.es / "demo.spec.html"), cap)
    x.built("acceptance-a", "--record", RA, "--commit", cap, "--test", "tests/a.sh")
    x.built("acceptance-b", "--record", RB, "--commit", cap, "--test", "tests/b.py::test_b")
    s.git(e, "add", "-A")
    s.git(e, "commit", "-qm", f"qc: built acceptance-a acceptance-b (judged {cap[:12]})")
    got = json.loads(x.st.read_text())["criteria"]["acceptance-a"]
    want = {"status": "built", "pr": 7, "record": RA, "commit": cap, "tests": ["tests/a.sh"]}
    assert got == want, f"{TAG}: built did not write the evidence link: {x.st.read_text()}"
    run(s, 0, "check", str(x.es))
    return cap


def staleness(x: Stale, cap: str) -> None:
    """show: current, then stale by a covered path, an edited or gone test file, the text."""
    c = cap[:12]
    out = x.show()
    has(out, f"acceptance-a: built (PR #7), current: record {RA} captured at {c}")
    on(out, "acceptance-b", "current", "acceptance-b not current")
    (x.e / "README").write_text("v2\n")
    x.commit("unrelated change")
    (x.e / "src/a").write_text("v2\n")
    ch = x.commit("change a's code")
    out = x.show()
    has(
        out,
        f"acceptance-a: built (PR #7), STALE: record {RA} captured at {c}; covered path src/a "
        f"changed since {c} by {ch} change a's code",
        "2 built: 1 current, 1 stale, 0 no evidence link",
    )
    on(out, "acceptance-b", ", current: ", "an unrelated change made acceptance-b stale")
    # A named test file edited or gone since capture makes it stale (owner ruling #409).
    (x.e / "tests/a.sh").write_text("v2\n")
    ta = x.commit("edit a's test")
    want = f"; test file tests/a.sh changed since {c} by {ta} edit a's test"
    on(x.show(), "acceptance-a", want, "edited test file not stale")
    x.s.git(x.e, "rm", "-q", "tests/b.py")
    tb = x.commit("drop b's test")
    want = (
        f"STALE: record {RB} captured at {c}; test file tests/b.py (tests/b.py::test_b) gone since "
        f"{c} by {tb} drop b's test"
    )
    on(x.show(), "acceptance-b", want, "gone test not stale")
    x.s.git(x.e, "checkout", "-q", cap, "--", "tests/b.py")
    x.commit("b's test back")
    spec = x.es / "demo.spec.html"
    keep = spec.read_text()
    spec.write_text(
        "".join(
            ln.replace("then it prints ok.", "then it prints done.") if "acceptance-b" in ln else ln
            for ln in keep.splitlines(keepends=True)
        )
    )
    want = f"STALE: record {RB} captured at {c}; criterion text changed since {c}"
    on(x.show(), "acceptance-b", want, "changed text not stale")
    spec.write_text(keep)


def fallback_and_legacy(x: Stale) -> None:
    """A fallback-built criterion (record, no declared demo): only its text makes it stale. A
    legacy built row (status and PR only) passes check and shows as no evidence link."""
    q = x.e / "qc.toml"
    q.write_text(q.read_text().split('[demo."demo#acceptance-b"]')[0])
    x.commit("no demo for b")
    fb = x.s.git(x.e, "rev-parse", "HEAD")
    x.built("acceptance-b", "--record", RC, "--commit", fb)
    x.commit(f"qc: built acceptance-b (judged {fb[:12]})")
    (x.e / "src/b").write_text("v3\n")
    x.commit("change b's code")
    want = f"current: record {RC} captured at {fb[:12]} by the agent fallback"
    on(x.show(), "acceptance-b", want, "fallback-built not current")
    x.built("acceptance-b")
    run(x.s, 0, "check", str(x.es))
    out = x.show()
    on(out, "acceptance-b", "acceptance-b: built (PR #7), no evidence link", "legacy row")
    has(out, "2 built: 0 current, 1 stale, 1 no evidence link")


def refusals(x: Stale, cap: str) -> None:
    """check refuses a partial or malformed link, and a planned criterion with one."""
    legacy = x.st.read_text()
    link: dict[str, object] = {"status": "built", "pr": 7, "record": RA, "commit": cap, "tests": []}
    rows: tuple[tuple[dict[str, object], str], ...] = (
        ({"status": "built", "pr": 7, "record": RA}, "names record without commit, tests"),
        (link | {"record": "r1"}, "record must be an evidence record id"),
        (link | {"commit": "HEAD"}, "commit must be a commit sha"),
        (link | {"tests": "t"}, "tests must be a list"),
        (link | {"status": "planned", "pr": None}, "a planned criterion names no evidence"),
    )
    for row, want in rows:
        d = json.loads(legacy)
        d["criteria"]["acceptance-b"] = row
        x.st.write_text(json.dumps(d))
        has(run(x.s, 1, "check", str(x.es)), f"demo.status.json: acceptance-b: {want}")
    x.st.write_text(legacy)


def links(s: Scratch) -> None:
    world(s)
    fixtures(s)
    x = Stale(s)
    cap = linked(x)
    staleness(x, cap)
    fallback_and_legacy(x)
    refusals(x, cap)


if __name__ == "__main__":
    main(links, guard, calls)
