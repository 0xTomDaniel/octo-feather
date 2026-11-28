"""`octo-feather-spec-status init` over an existing status file, and `check` after it
(issue-lifecycle #spec-status-file, #acceptance-revision-preserve, -remove, -repeat, -invalid;
#1189), as scenarios (testkit.main). Driven only through the CLI, on one scratch git repo: a spec
accepted with criteria a, b, c (tests/fixtures/spec-status/revision/accepted.spec.html) is
initialized, a built with an evidence link, b built without, a logged call names c; the owner
accepts a revision dropping c and adding d (revised.spec.html). What init does then:
`octo-feather-spec-status` usage, its init paragraph.

Also `planned` (docs/adr/0035; #1320), on the same accepted spec. What planned does: that usage's
planned paragraph."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from testkit import FIXTURES, get, kit, main, obj

if TYPE_CHECKING:
    from testkit import Scratch

S = kit("octo-feather-spec-status")
SPECS = FIXTURES / "spec-status" / "revision"
CALL = {
    "at": "2026-10-21T10:00:00Z",
    "lane": "gh62",
    "role": "supervisor",
    "kind": "clarifies",
    "anchors": ["acceptance-c"],
    "criteria": ["acceptance-c"],
    "what": "w",
    "why": "y",
    "passes_as_written": False,
    "evidence": "e",
}
PLANNED = '{\n      "status": "planned",\n      "pr": null\n    }'
CALLED_C = "demo.calls.jsonl:2: call (lane gh62; anchors acceptance-c): criterion acceptance-c is"


class Repo:
    """The scratch repo: its spec, status file and call log, each git commit's sha."""

    def __init__(self, s: Scratch) -> None:
        self.s, self.root = s, s.root / "repo"
        self.dir = self.root / "docs" / "specs"
        self.dir.mkdir(parents=True)
        self.spec = self.dir / "demo.spec.html"
        self.st = self.dir / "demo.status.json"
        self.log = self.dir / "demo.calls.jsonl"
        s.git(self.root, "init", "-q")

    def commit(self, msg: str) -> str:
        self.s.git(self.root, "add", "-A")
        self.s.git(self.root, "commit", "-q", "-m", msg)
        return self.s.git(self.root, "rev-parse", "HEAD")

    def spec_from(self, name: str, msg: str) -> str:
        self.spec.write_bytes((SPECS / name).read_bytes())
        return self.commit(msg)

    def init(self, commit: str, want: int = 0) -> str:
        return self.s.run([S, "init", str(self.spec), commit], want=want).err

    def built(self, pr: str, cid: str, *link: str) -> None:
        self.s.run([S, "built", str(self.st), pr, cid, *link])

    def status(self) -> dict[str, object]:
        """The status file, failing naming a field that is not there."""
        return dict(obj(json.loads(self.st.read_text()), str(self.st)))

    def criteria(self) -> dict[str, object]:
        return dict(obj(self.status().get("criteria"), f"{self.st} criteria"))

    def with_row(self, cid: str, row: dict[str, object]) -> None:
        """The status file with CID's row replaced by ROW, written as JSON."""
        data = {**self.status(), "criteria": {**self.criteria(), cid: row}}
        self.st.write_text(json.dumps(data, indent=2) + "\n")


def row(text: str, cid: str) -> str:
    """Criterion CID's row as a status file's text holds it, from `"CID": {` to its `}`."""
    start = text.index(f'\n    "{cid}": {{\n') + 1
    return text[start : text.index("\n    }", start) + len("\n    }")]


def refused(r: Repo, commit: str, *said: str) -> None:
    """init exits non-zero naming each SAID, the status file byte-identical."""
    before = r.st.read_bytes()
    err = r.init(commit, want=1)
    for w in said:
        assert w in err, f"init did not name {w!r}: {err}"
    assert r.st.read_bytes() == before, f"init changed {r.st}: {r.st.read_text()}"


def fresh(r: Repo) -> str:
    """No status file yet: every criterion planned, in spec order."""
    c1 = r.spec_from("accepted.spec.html", "accepted")
    r.init(c1)
    rows = ",\n".join(f'    "acceptance-{x}": {PLANNED}' for x in "abc")
    want = (
        f'{{\n  "spec": "demo.spec.html",\n  "accepted_commit": "{c1}",\n'
        f'  "criteria": {{\n{rows}\n  }}\n}}\n'
    )
    assert r.st.read_text() == want, f"fresh init wrote:\n{r.st.read_text()}"
    return c1


def preserve_remove(r: Repo, c1: str) -> str:
    """#acceptance-revision-preserve, -remove: a's and b's rows byte for byte, d planned, c gone."""
    r.built("7", "acceptance-a", "--record", "20261029T100000Z-0a0a0a0a", "--commit", c1,
            "--test", "tests/a.sh", "--test", "tests/a2.sh")  # fmt: skip
    r.built("8", "acceptance-b")
    r.log.write_text(json.dumps(CALL) + "\n")
    r.commit("a and b built; a call names c")
    text = r.st.read_text()
    ra, rb = row(text, "acceptance-a"), row(text, "acceptance-b")
    assert '"record": "20261029T100000Z-0a0a0a0a"' in ra, ra
    assert '"record"' not in rb, rb
    c2 = r.spec_from("revised.spec.html", "revision accepted")
    r.init(c2)
    text = r.st.read_text()
    assert row(text, "acceptance-a") == ra, f"row a not kept byte for byte:\n{text}"
    assert row(text, "acceptance-b") == rb, f"row b not kept byte for byte:\n{text}"
    got = r.criteria()
    assert list(got) == ["acceptance-a", "acceptance-b", "acceptance-d"], text
    assert got["acceptance-d"] == {"status": "planned", "pr": None}, text
    assert get(r.status(), "accepted_commit", str, str(r.st)) == c2, text
    return c2


def check_after(r: Repo) -> None:
    """-remove at check: the call in the log at accepted_commit passes; a copy added since fails."""
    r.commit("status of the revision")
    assert r.s.run([S, "check", str(r.dir)]).out == "spec-status: ok (1 status files)"
    r.log.write_text(r.log.read_text() + json.dumps(CALL) + "\n")
    err = r.s.run([S, "check", str(r.dir)], want=1).err
    assert CALLED_C + " in neither" in err, err
    r.s.git(r.root, "checkout", "-q", "--", "docs/specs")


def repeat(r: Repo, c2: str) -> None:
    """-repeat: a lane builds d with its evidence link; the same init changes no byte."""
    r.built("9", "acceptance-d", "--record", "20261030T100000Z-0d0d0d0d", "--commit", c2,
            "--test", "tests/d.sh")  # fmt: skip
    before = r.st.read_bytes()
    r.init(c2)
    assert r.st.read_bytes() == before, f"repeat init changed the file:\n{r.st.read_text()}"


def invalid(r: Repo, c2: str) -> None:
    """-invalid: a partial evidence link, a bad status, bad JSON; a spec init cannot read or with
    an id twice: refused, nothing written."""
    a = dict(obj(r.criteria()["acceptance-a"], "acceptance-a"))
    good = r.st.read_bytes()
    del a["commit"], a["tests"]
    r.with_row("acceptance-a", a)
    refused(r, c2, "acceptance-a: names record without commit, tests", "nothing written")
    r.st.write_bytes(good)
    r.with_row("acceptance-b", {**obj(r.criteria()["acceptance-b"], "b"), "status": "done"})
    refused(r, c2, "acceptance-b: status must be planned or built, not 'done'")
    r.st.write_text('{"spec": ')
    refused(r, c2, "demo.status.json")
    err = r.s.run([S, "init", str(r.dir / "gone.spec.html"), c2], want=1).err
    assert "gone.spec.html" in err, err
    dup = r.dir / "dup.spec.html"
    dup.write_text(r.spec.read_text().replace("acceptance-d", "acceptance-a"))
    err = r.s.run([S, "init", str(dup), c2], want=1).err
    assert "duplicate criterion id acceptance-a" in err, err
    assert not (r.dir / "gone.status.json").exists()
    assert not (r.dir / "dup.status.json").exists()


def revision(s: Scratch) -> None:
    """Fresh init, the revision's init, check after it, a repeat, then refusals: one repo."""
    r = Repo(s)
    c2 = preserve_remove(r, fresh(r))
    check_after(r)
    repeat(r, c2)
    invalid(r, c2)


def planned(s: Scratch) -> None:
    """a built with a fallback's link (no tests), b built without, c built: `planned` a b drops
    their PRs and links, c's row byte for byte, check passes; then each refusal leaves the file
    as it was."""
    r = Repo(s)
    c1 = r.spec_from("accepted.spec.html", "accepted")
    r.init(c1)
    r.built("7", "acceptance-a", "--record", "20261029T100000Z-0a0a0a0a", "--commit", c1)
    r.built("8", "acceptance-b")
    r.built("9", "acceptance-c")
    r.commit("a, b and c built")
    text = r.st.read_text()
    rc = row(text, "acceptance-c")
    r.s.run([S, "planned", str(r.st), "acceptance-a", "acceptance-b"])
    want = text.replace(row(text, "acceptance-a"), f'    "acceptance-a": {PLANNED}')
    want = want.replace(row(text, "acceptance-b"), f'    "acceptance-b": {PLANNED}')
    assert r.st.read_text() == want, f"planned a b wrote:\n{r.st.read_text()}"
    assert row(want, "acceptance-c") == rc, want
    assert r.s.run([S, "check", str(r.dir)]).out == "spec-status: ok (1 status files)"
    for ids, said in (
        (["acceptance-a"], "acceptance-a is already planned"),
        (["acceptance-c", "acceptance-z"], "no criterion acceptance-z in"),
        (["*"], "no criterion * in"),
    ):
        refused_planned(r, ids, said)
    before = r.st.read_bytes()
    r.s.run([S, "planned", str(r.st)], want=64)
    assert r.st.read_bytes() == before, r.st.read_text()
    r.with_row("acceptance-b", {"status": "planned", "pr": 8})
    refused_planned(r, ["acceptance-c"], "acceptance-b: a planned criterion has pr null")
    r.st.write_text('{"spec": ')
    refused_planned(r, ["acceptance-c"], "demo.status.json")


def refused_planned(r: Repo, ids: list[str], said: str) -> None:
    """planned IDS exits 1 naming SAID and that nothing was written, the status file unchanged."""
    before = r.st.read_bytes()
    err = r.s.run([S, "planned", str(r.st), *ids], want=1).err
    for w in (said, f"planned: nothing written to {r.st}"):
        assert w in err, f"planned {ids} did not name {w!r}: {err}"
    assert r.st.read_bytes() == before, f"planned {ids} changed {r.st}: {r.st.read_text()}"


if __name__ == "__main__":
    main(revision, planned)
