"""The scenario of tests/gate/kit/test_lane_merge_order.py, this file its command (testkit.main):
`octo-feather-lane merge-ask` names the other open lane PRs its merge would set back (spec
issue-lifecycle #gates-merge-order, #acceptance-merge-ask-siblings), no network. The lane is
lane_merge_ask.py's (a real git repo, PR #7 in the fake gh), its main moved on to hold a target's
worker role, its launcher and an eval case (qc_eval_verdict.py's), merged into the lane, whose
judged head then changes a skill that role launches. Three other open PRs on main, their heads on
the lane's origin (a bare repo, refs/pull/N/head, as GitHub serves them) and not in the lane
repo: #12 pins a stored run of the role in a qc.toml demo, #13 conflicts with the lane's head,
#14's head is not on origin, #15 pins the same run in a qc.toml octo-feather-contract rejects;
then #16, whose head gh pr list answers as null. The rule's own cases: test_merge_ask_order.py,
in-process."""

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
QC = 'format = 2\n[entry]\ncommand = "true"\n[services]\n[fixture]\n[values]\n'
# main's, the lane's qc.toml made a valid contract (its demo for a only kept)
QC_MAIN = f'{QC}[demo."demo#acceptance-a"]\ncovers = ["app.py"]\ncommand = "true"\n'
QC_PIN = (
    f'{QC_MAIN}[demo."demo#acceptance-z"]\ncovers = ["app.py"]\n'
    f'command = "scripts/octo-feather-qa --verdict {PIN}"\n'
)
# PR #15's: the same pin, its demo lacking the covers the contract requires
QC_BAD = f'{QC}[demo."demo#acceptance-z"]\ncommand = "scripts/octo-feather-qa --verdict {PIN}"\n'
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


def asked(out: str) -> list[str]:
    """OUT's section but its `Waits for:` line, which the merge order moves (--help, merge-ask)."""
    return [x for x in section(out) if not x.startswith("Waits for: ")]


def lane(s: Scratch) -> tuple[Lane, str, str, str]:
    """The lane, main moved to M1 (the worker role, its launcher, skill and eval case) and merged
    in, then D changing the skill (its full pass recorded); PR #12 at S12 off M1 pinning a stored
    run made at S12, PR #13 at S13 off B setting app.py's line 1 (and main's qc.toml), PR #15
    at S15 off M1 with QC_BAD, all on origin only, and PR #14 at a head origin lacks, all open
    on main. (lane, D, S12, S15)."""
    ln = Lane(s)

    def world() -> None:
        put(ln.r, WORLD | {"qc.toml": QC_MAIN})
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
    app = "uno\n" + "".join(f"{i}\n" for i in range(2, 21))
    s13 = pr(13, ln.b, {"app.py": app, "qc.toml": QC_MAIN})  # main's qc.toml alike: no conflict
    s15 = pr(15, m1, {"qc.toml": QC_BAD})
    ln.git("remote", "add", "origin", str(origin))
    store(s, s12, case=CASE)
    s.env["OCTO_FEATHER_QA_DIR"] = str(s.root / "qa")
    for n, oid in ((12, s12), (13, s13), (14, GONE), (15, s15)):
        pr_n = {"number": n, "baseRefName": "main", "headRefName": f"gh{n}", "headRefOid": oid}
        s.gh.put(n, pr_n | {"state": "OPEN"})
    return ln, d, s12, s15


def states(s: Scratch, state: str) -> None:
    """PRs #12 to #15 in STATE."""
    for n in (12, 13, 14, 15):
        s.gh.put(n, s.gh.pr(n) | {"state": state})


def siblings(s: Scratch) -> None:
    """Passing, the ask prints #12 with its pinned run and the changed skill file, #13 with the
    conflicting file, #14 not read and #15 not read with the contract's problem; with #16's head
    unanswered, the open PRs not read; with those PRs closed it prints the same section (the line
    the merge order moves aside: asked) and passes alike. Failing on a gap, the same items with and
    without them."""
    ln, d, _, s15 = lane(s)
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
    assert len(order) == 5, with_them.out
    assert order[3].startswith(f"- not read: PR #14 (gh14) head {GONE[:12]}: git fetch "), order
    assert order[4] == (
        f"- not read: PR #15 (gh15) head {s15[:12]}: qc.toml at {s15[:12]} fails "
        "octo-feather-contract (demo.demo#acceptance-z: missing covers)"
    ), order
    assert len(ln.git("worktree", "list").splitlines()) == 1, "a scratch worktree was left"

    s.gh.put(16, {"number": 16, "baseRefName": "main", "headRefName": "gh16", "state": "OPEN"})
    malformed = ln.ask()
    unread = (
        "- not read: open pull requests on main: gh pr list's answer fails "
        "schemas/gh-pr-list.schema.json (4.headRefOid: None is not of type 'string')"
    )
    assert block(malformed.out) == [HEAD, unread], malformed.out
    assert asked(malformed.out) == asked(with_them.out), malformed.out
    s.gh.put(16, s.gh.pr(16) | {"state": "CLOSED"})

    states(s, "CLOSED")
    without = ln.ask()
    none = "none this merge would stale or conflict with"
    assert block(without.out) == [HEAD, f"- none: 0 other open pull requests on main, {none}"]
    assert asked(with_them.out) == asked(without.out), f"{with_them.out}\n---\n{without.out}"

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
