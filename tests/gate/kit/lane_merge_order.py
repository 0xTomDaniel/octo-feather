"""The scenario of tests/gate/kit/test_lane_merge_order.py, this file its command (testkit.main):
`octo-feather-lane merge-ask` names the other open lane PRs its merge would set back (spec
issue-lifecycle #gates-merge-order, #acceptance-merge-ask-siblings), no network. The lane is
lane_merge_ask.py's (a real git repo, PR #7 in the fake gh), its main moved on to hold a target's
worker role, its launcher and an eval case (qc_eval_verdict.py's), merged into the lane, whose
judged head then changes a skill that role launches. Three other open PRs on main, their heads on
the lane's origin (a bare repo, refs/pull/N/head, as GitHub serves them) and not in the lane
repo: #12 pins a stored run of the role in a qc.toml demo, #13 conflicts with the lane's head,
#14's head is not on origin. The rule's own cases: test_merge_ask_order.py, in-process."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from lane_merge_ask import Lane, section
from qc_eval_verdict import FACTS, PI_ROLE, store
from testkit import Scratch, main

if TYPE_CHECKING:
    from pathlib import Path

RUN = "20260101T000000Z-abc123"
PIN = f"{RUN}/s1/c1"
CASE = {"id": "c1", "role": "worker", "task": "Do it."}
WORLD = {
    "agents/worker.md": "the worker role\n",
    "scripts/pi-role": PI_ROLE,
    ".agents/skills/s/SKILL.md": "the skill\n",
    "evals/s1/cases.json": json.dumps([CASE]),
    "evals/s1/reference/expectations.json": json.dumps({"c1": {"facts": FACTS}}),
}
QC_PIN = (
    '[demo."demo#acceptance-a"]\ncommand = "true"\n'
    f'[demo."demo#acceptance-z"]\ncommand = "scripts/octo-feather-qa --verdict {PIN}"\n'
)
GONE = "ab" * 20  # PR #14's head, on no remote
HEAD = (
    "Merge order (issue-lifecycle #gates-merge-order; shown only: this merge ask passes or "
    "fails the same without it):"
)


def put(root: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text)


def block(text: str) -> list[str]:
    """The merge-order lines of TEXT."""
    lines = text.splitlines()
    i = lines.index(HEAD)
    j = lines.index("", i) if "" in lines[i:] else len(lines)
    return lines[i:j]


def lane(s: Scratch) -> tuple[Lane, str, str, str]:
    """The lane, main moved to M1 (the worker role, its launcher, skill and eval case) and merged
    in, then D changing the skill (its full pass recorded); PR #12 at S12 off M1 pinning a stored
    run made at S12, PR #13 at S13 off B setting app.py's line 1, both on origin only, and PR #14
    at a head origin lacks, all open on main. (lane, D, S12, S13)."""
    ln = Lane(s)

    def world() -> None:
        put(ln.r, WORLD)
        (ln.r / "scripts" / "pi-role").chmod(0o755)
        ln.commit("main: the worker role")

    m1 = ln.on(ln.b, world)
    ln.main(m1)

    def skill() -> None:
        put(ln.r, {".agents/skills/s/SKILL.md": "the skill, reworded\n"})
        ln.commit("feat: skill")
        ln.record()

    d = ln.on(ln.merge(ln.h, m1), skill)
    origin = s.root / "origin.git"
    s.git(s.root, "clone", "-q", "--bare", str(ln.r), str(origin))
    w = s.root / "other"
    s.git(s.root, "clone", "-q", str(origin), str(w))

    def pr(n: int, parent: str, files: dict[str, str]) -> str:
        """PR N's head: FILES committed on PARENT in another clone, pushed to refs/pull/N/head."""
        s.git(w, "checkout", "-q", "--detach", parent)
        put(w, files)
        s.git(w, "commit", "-qam", f"pr {n}")
        s.git(w, "push", "-q", "origin", f"HEAD:refs/pull/{n}/head")
        return s.git(w, "rev-parse", "HEAD")

    s12 = pr(12, m1, {"qc.toml": QC_PIN})
    s13 = pr(13, ln.b, {"app.py": "uno\n" + "".join(f"{i}\n" for i in range(2, 21))})
    ln.git("remote", "add", "origin", str(origin))
    store(s, s12, case=CASE)
    s.env["OCTO_FEATHER_QA_DIR"] = str(s.root / "qa")
    for n, oid in ((12, s12), (13, s13), (14, GONE)):
        pr_n = {"number": n, "baseRefName": "main", "headRefName": f"gh{n}", "headRefOid": oid}
        s.gh.put(n, pr_n | {"state": "OPEN"})
    return ln, d, s12, s13


def states(s: Scratch, state: str) -> None:
    """PRs #12, #13 and #14 in STATE."""
    for n in (12, 13, 14):
        s.gh.put(n, s.gh.pr(n) | {"state": state})


def siblings(s: Scratch) -> None:
    """Passing, the ask prints #12 with its pinned run and the changed skill file, #13 with the
    conflicting file, and #14 not read; with those PRs closed it prints the same section and
    passes alike. Failing on a gap, the same items with and without them."""
    ln, d, _, _ = lane(s)
    edits, lines = ln.at(d, "feat: skill")
    ln.setpr(*edits, **lines)
    with_them = ln.ask()
    order = block(with_them.out)
    stales = f"this merge stales its pinned run {PIN}: .agents/skills/s/SKILL.md changed"
    assert order[:3] == [
        HEAD,
        f"- PR #12 (gh12): {stales}",
        "- PR #13 (gh13): its head conflicts with this head in app.py",
    ], with_them.out
    assert len(order) == 4, with_them.out
    assert order[3].startswith(f"- not read: PR #14 (gh14) head {GONE[:12]}: git fetch "), order
    assert len(ln.git("worktree", "list").splitlines()) == 1, "a scratch worktree was left"

    states(s, "CLOSED")
    without = ln.ask()
    none = "none this merge would stale or conflict with"
    assert block(without.out) == [HEAD, f"- none: 0 other open pull requests on main, {none}"]
    assert section(with_them.out) == section(without.out), f"{with_them.out}\n---\n{without.out}"

    ln.setpr(*edits, **lines, failed="Failed: oops")
    fail_alone = ln.ask(want=1).err
    states(s, "OPEN")
    fail_with = ln.ask(want=1).err
    items = [x for x in fail_with.splitlines() if x.startswith("  - ")]
    assert items, fail_with
    assert items == [x for x in fail_alone.splitlines() if x.startswith("  - ")], fail_with
    assert block(fail_with)[:3] == order[:3], fail_with


if __name__ == "__main__":
    main(siblings)
