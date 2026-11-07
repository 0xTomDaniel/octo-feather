"""The scenarios of tests/gate/kit/test_integrate.py (its items), this file their command
(testkit.main): scripts/octo-feather-integrate, run directly, in throwaway repos (its lane
worktrees beside them).
  lanes       merge a branch and cherry-pick a commit; a conflict and a red gate roll back; a
              missing lane exits 66; the lane is gh<N> or <prefix>/gh<N> only (not gh<N>-x, gh<N>0,
              gh<N>-demo); a GitHub target refuses a Linear key. Then hygiene and linear:
  hygiene     review state and factory recipes never land on the lane (as just reads them: @qc, a
              defaulted parameter, an import; an unreadable justfile refused); a lane qc recipe's
              parameters edited and an alias-only hand-in integrate; a spec alone integrates
  linear      a Linear target: ENG-123 lands on branch eng-123 only (never eng-1230 or
              eng-123-x); a number is refused; an unknown tracker refused before any worktree is
              touched
  tiers       (issue-lifecycle #lanes-checkpoints) a repo with a fast recipe and a shared-machinery
              list: the pilot runs the full gate and records the pass (#acceptance-pilot-full); an
              unlisted change runs only the fast tier, provisional, no pass recorded
              (#acceptance-integrate-fast); two full passes on an unchanged configuration record
              one configuration identity; a listed rename runs the full gate, red rolls back naming
              it (#acceptance-integrate-checkpoint)
  brownfield  a repo the kit did not create, only its own `just check`: every integration runs it
              in full and records the pass; the repo gains no recipe (#acceptance-brownfield-full)
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from testkit import Ran, Scratch, kit, main

if TYPE_CHECKING:
    from pathlib import Path

TAG = "integrate test"
IDENT = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@t",
}


class Repo:
    """A repo at S/NAME holding FILES, one commit on main; its lane worktrees beside it."""

    def __init__(self, s: Scratch, name: str, files: dict[str, str]) -> None:
        self.s, self.dir = s, s.root / name
        s.env |= IDENT
        s.git(s.root, "-c", "init.defaultBranch=main", "init", "-q", name)
        for rel, text in files.items():
            (self.dir / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.dir / rel).write_text(text)
        self.g("add", "-A")
        self.g("commit", "-qm", "base")

    def g(self, *args: str, cwd: Path | None = None) -> str:
        return self.s.git(cwd or self.dir, *args)

    def at(self, name: str) -> Path:
        return self.s.root / name

    def tree(self, branch: str, name: str | None = None, base: str = "main") -> Path:
        """A worktree of a new BRANCH beside the repo, at S/NAME (default BRANCH)."""
        d = self.at(name or branch)
        self.g("worktree", "add", "-q", "-b", branch, str(d), base)
        return d

    def work(self, branch: str, files: dict[str, str], base: str = "main") -> Path:
        """BRANCH off BASE with FILES written and committed (message BRANCH)."""
        d = self.tree(branch, base=base)
        for rel, text in files.items():
            (d / rel).parent.mkdir(parents=True, exist_ok=True)
            (d / rel).write_text(text)
        self.g("add", "-A", cwd=d)
        self.g("commit", "-qm", branch, cwd=d)
        return d

    def head(self, d: Path) -> str:
        return self.g("rev-parse", "HEAD", cwd=d)

    def run(self, want: int, *args: str) -> str:
        """octo-feather-integrate ARGS from the repo, exiting WANT; its stdout and stderr."""
        r: Ran = self.s.run([kit("octo-feather-integrate"), *args], want=want, cwd=self.dir)
        return f"{r.out}\n{r.err}"


def lanes(s: Scratch) -> None:
    r = Repo(s, "repo", {"justfile": "check:\n    test ! -e red\n", "f": "a\n"})
    lane = r.tree("gh7", "lane")
    gh7x = r.tree("gh7-x", "gh7x")  # worker branch beside lane gh7: not a lane
    gh70 = r.tree("gh70")  # lane gh70: not lane gh7
    w1 = r.work("w1", {"b": "b\n"})
    c2 = r.head(r.work("w2", {"c": "c\n"}))
    r.run(0, "7", "w1", c2)  # merge a branch, cherry-pick a commit
    assert (lane / "b").exists(), f"{TAG}: lane missing worker file b"
    assert (lane / "c").exists(), f"{TAG}: lane missing worker file c"
    head = r.head(lane)
    (w1 / "f").write_text("x\n")
    r.g("commit", "-qam", "w1f", cwd=w1)
    r.work("w3", {"f": "y\n"})
    r.run(0, "7", "w1")
    before = r.head(lane)
    r.run(1, "7", "w3")  # conflict on f
    assert r.head(lane) == before, f"{TAG}: conflict did not restore the head"
    assert r.g("status", "--porcelain", cwd=lane) == "", f"{TAG}: lane left dirty after conflict"
    r.work("w4", {"red": "r\n"})
    before = r.head(lane)
    r.run(2, "7", "w4")  # red gate rolls back
    assert r.head(lane) == before != head, f"{TAG}: red gate did not roll back"
    r.run(66, "8", "w1")  # no lane for gh8
    assert r.head(gh70) == r.head(gh7x), f"{TAG}: gh70 touched as lane gh7"
    r.g("worktree", "remove", str(lane))
    r.g("worktree", "remove", str(gh7x))
    r.run(66, "7", "w1")  # gh70 alone is not lane gh7
    suf = r.tree("gh7-demo", "suf")
    r.run(66, "7", "w1")  # gh7-demo alone is not lane gh7
    r.g("worktree", "remove", str(suf))
    pre = r.tree("octo-feather/gh7", "pre")
    out = r.run(0, "7", "w1")  # namespaced lane octo-feather/gh7 integrates
    assert "branch=octo-feather/gh7 " in out, f"{TAG}: prefixed lane not integrated: {out}"
    assert (pre / "b").exists(), f"{TAG}: prefixed lane lacks b: {out}"
    hygiene(r, pre)
    out = r.run(64, "ENG-7", "w1")
    assert "not a GitHub issue number" in out, f"{TAG}: ENG-7 in a GitHub target: {out}"
    linear(s)


def hygiene(r: Repo, pre: Path) -> None:
    """Hand-in hygiene (pilot 1, 2026-10-20): review state and factory recipes never land on the
    lane PRE."""
    s = r.s
    s.run([kit("octo-feather-exclude"), "."], cwd=r.dir)
    review = "docs/specs/a.spec.html.review/versions/1.html"
    (r.dir / review).parent.mkdir(parents=True)
    (r.dir / review).write_text("v\n")
    assert r.g("status", "--porcelain") == "", f"{TAG}: excluded review state shows in git status"
    w5 = r.tree("w5")
    (w5 / review).parent.mkdir(parents=True)
    (w5 / review).write_text("v\n")
    (w5 / "docs/specs/a.spec.html").write_text("s\n")
    r.g("add", "docs/specs/a.spec.html", cwd=w5)
    r.g("add", "-f", "docs/specs/a.spec.html.review", cwd=w5)
    r.g("commit", "-qm", "review-state", cwd=w5)
    before = r.head(pre)

    def refused(branch: str, said: str) -> None:
        out = r.run(3, "7", branch)
        assert said in out, f"{TAG}: {branch} not refused for {said}: {out}"
        assert r.head(pre) == before, f"{TAG}: {branch}: the lane moved: {out}"

    refused("w5", "review state")
    jf = (r.dir / "justfile").read_text()
    r.work(
        "w6",
        {
            "justfile": jf
            + "\nintegrate issue +refs:\n    octo-feather-integrate {{issue}} {{refs}}\n"
        },
    )
    refused("w6", "factory recipes")
    # #121 D12: a quiet recipe, a defaulted parameter, an import, an unreadable justfile.
    r.work("w8", {"justfile": jf + "\n@qc:\n    true\n"})
    refused("w8", "factory recipes to the justfile (qc)")
    r.work("w9", {"justfile": jf + '\nqc status="x":\n    true\n'})
    refused("w9", "factory recipes to the justfile (qc)")
    r.work("w10", {"ci.just": "integrate N:\n    true\n", "justfile": jf + "\nimport 'ci.just'\n"})
    refused("w10", "factory recipes to the justfile (integrate)")
    r.work("w11", {"justfile": jf + "\nfoo:\n\ttrue\n  x\n"})
    refused("w11", "justfile does not parse")
    # #121 D13: a lane qc recipe's parameters edited.
    (pre / "justfile").write_text(jf + "\nqc STATUS:\n    true\n")
    r.g("commit", "-qam", "lane-qc", cwd=pre)
    lane_jf = (pre / "justfile").read_text()
    r.work("w12", {"justfile": lane_jf.replace("qc STATUS:", "qc STATUS PR:")}, "octo-feather/gh7")
    out = r.run(0, "7", "w12")
    assert "\nqc STATUS PR:\n" in (pre / "justfile").read_text(), f"{TAG}: qc edit lost: {out}"
    # PR #140 review finding 3 (owner: docs/adr/0017): an alias-only hand-in.
    jf13 = (pre / "justfile").read_text() + "\nalias integrate := check\n"
    r.work("w13", {"justfile": jf13}, "octo-feather/gh7")
    out = r.run(0, "7", "w13")
    lines = (pre / "justfile").read_text().splitlines()
    assert "alias integrate := check" in lines, f"{TAG}: alias-only hand-in not integrated: {out}"
    r.work("w7", {"docs/specs/a.spec.html": "s\n"})
    r.run(0, "7", "w7")  # a spec alone stays tracked and integrates


def linear(s: Scratch) -> None:  # lanes' last part
    """Linear target (roles spec #lane-key)."""
    r = Repo(
        s,
        "lin",
        {
            "justfile": "check:\n    true\n",
            ".octo-feather.toml": 'tracker = "linear"\n',
            "f": "a\n",
        },
    )
    l1230 = r.tree("eng-1230", "l1230")
    l123x = r.tree("eng-123-x", "l123x")
    r.work("lw", {"l": "l\n"})
    r.run(66, "ENG-123", "lw")  # eng-1230 and eng-123-x are not lane eng-123
    l123 = r.tree("eng-123", "l123")
    out = r.run(0, "ENG-123", "lw")
    assert "branch=eng-123 " in out, f"{TAG}: Linear lane eng-123 not integrated: {out}"
    assert (l123 / "l").exists(), f"{TAG}: eng-123 lacks l: {out}"
    assert not (l1230 / "l").exists(), f"{TAG}: eng-1230 got l: {out}"
    assert not (l123x / "l").exists(), f"{TAG}: eng-123-x got l: {out}"
    out = r.run(64, "12", "lw")
    assert "not a Linear issue key" in out, f"{TAG}: 12 in a Linear target: {out}"
    (r.dir / ".octo-feather.toml").write_text('tracker = "jira"\n')
    r.g("commit", "-qam", "jira")
    head = r.head(l123)
    out = r.run(64, "ENG-123", "lw")
    assert "unknown tracker 'jira'" in out, f"{TAG}: jira target: {out}"
    assert r.head(l123) == head, f"{TAG}: jira target: the lane moved"


def tiers(s: Scratch) -> None:
    """Gate tiers (issue-lifecycle #lanes-checkpoints): the full gate reds on machinery/b, the
    fast tier never reds."""
    jf = "check:\n    @echo gate=full\n    test ! -e machinery/b\nfast:\n    @echo gate=fast\n"
    files = {"justfile": jf, "shared-machinery.txt": "# listed\nmachinery\n", "machinery/a": "a\n"}
    r = Repo(s, "tiers", files | {"f": "a\n"})
    t9 = r.tree("gh9", "t9")
    gate = kit("octo-feather-gate")

    def passed(rev: str = "HEAD", want: int = 0) -> str:
        return s.run([gate, "passed", rev], want=want, cwd=t9).out

    # Pilot (issue-lifecycle #acceptance-pilot-full): the lane's first integration runs the full
    # gate and records the pass.
    r.work("t1", {"one": "1\n"}, "gh9")
    out = r.run(0, "9", "t1")
    assert "gate=full" in out, f"{TAG}: pilot did not run the full gate: {out}"
    assert "gate=fast" not in out, f"{TAG}: pilot ran the fast tier: {out}"
    assert "tier: full (pilot" in out, f"{TAG}: pilot not named: {out}"
    h1 = r.head(t9)
    rec = passed()
    assert f'"head": "{h1}"' in rec, f"{TAG}: pilot pass not recorded for {h1}: {rec}"
    assert '"clean": true' in rec, f"{TAG}: pilot pass not clean: {rec}"
    # Fast (issue-lifecycle #acceptance-integrate-fast): past it, a branch touching no listed path
    # runs only the fast tier.
    r.work("t2", {"two": "2\n"}, "gh9")
    out = r.run(0, "9", "t2")
    assert "gate=fast" in out, f"{TAG}: unlisted change not fast: {out}"
    assert "gate=full" not in out, f"{TAG}: unlisted change ran the full gate: {out}"
    assert "provisional" in out, f"{TAG}: unlisted change not provisional: {out}"
    passed(want=1)  # a fast-only head has no full pass recorded
    # Two full passes on heads whose gate configuration did not change (justfile only: no
    # Justfile, .justfile or lock files) record one configuration identity.
    r.work("t4", {"four": "4\n"}, "gh9")
    r.run(0, "9", "--full", "t4")
    one, now = json.loads(passed(h1))["gate_config"], json.loads(passed())["gate_config"]
    assert one == now, f"{TAG}: unchanged configuration, two identities: {one} {now}"
    assert now, f"{TAG}: no configuration identity: {now}"
    # Checkpoint (issue-lifecycle #acceptance-integrate-checkpoint): renaming a listed file runs
    # the full gate; red rolls back, naming it.
    t3 = r.tree("t3", base="gh9")
    r.g("mv", "machinery/a", "machinery/b", cwd=t3)
    r.g("commit", "-qm", "t3", cwd=t3)
    before = r.head(t9)
    out = r.run(2, "9", "t3")
    for want in ("gate=full", "machinery/a", "machinery/b"):
        assert want in out, f"{TAG}: listed rename lacks {want}: {out}"
    assert r.head(t9) == before, f"{TAG}: listed rename red did not roll back: {out}"


def brownfield(s: Scratch) -> None:
    """issue-lifecycle#acceptance-brownfield-full: a repo the kit did not create, only its own
    `just check` (no fast recipe): every integration, past the pilot too, runs that gate in full
    and records the pass; the repo gains no recipe."""
    r = Repo(s, "brown", {"justfile": "check:\n    @echo own-gate\n", "f": "a\n"})
    recipes = s.run(["just", "--summary"], cwd=r.dir).out
    b11 = r.tree("gh11", "b11")
    for n in (1, 2, 3):
        r.work(f"b{n}", {f"n{n}": f"{n}\n"}, "gh11")
        out = r.run(0, "11", f"b{n}")
        full = "no fast recipe in this repo: its one gate is the full tier"
        assert "tier: full (" in out, f"{TAG}: brownfield {n} not full: {out}"
        assert full in out, f"{TAG}: brownfield {n} not named full: {out}"
        assert "own-gate" in out, f"{TAG}: brownfield {n} did not run its own gate: {out}"
        assert "tier=full" in out, f"{TAG}: brownfield {n}: no tier=full: {out}"
        assert "provisional" not in out, f"{TAG}: brownfield {n} provisional: {out}"
        s.run([kit("octo-feather-gate"), "passed"], cwd=b11)
        got = s.run(["just", "--summary"], cwd=b11).out
        assert got == recipes, f"{TAG}: brownfield repo gained a recipe: {got}"


if __name__ == "__main__":
    main(lanes, tiers, brownfield)
