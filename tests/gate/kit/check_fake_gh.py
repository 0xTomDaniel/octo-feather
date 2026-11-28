"""The freeze on the fake gh's store (owner-fakes-ratchet, #1252; ticket #1263), as scenarios
(testkit.main), at its seam, the command `scripts/check-fake-gh` (rule: `check-fake-gh`).

Each scenario runs the check of a scratch git copy of the kit's tests (the kit's tests/gate/kit
Python files, its tests/*.sh, the baseline, and the two scripts the check runs: check-fake-gh and
octo-feather-gate), committed on main with two frozen items added: test_frozen.py's
test_frozen_stores and test_frozen_reads, whose scenarios (frozen.py) store into the fake gh, and
their baseline lines. HEAD is a lane branch off it, so the merge base with the default branch
(main, a local branch: no origin) is that commit. What the check refuses, and why a rename is
refused: its header.
"""

from __future__ import annotations

import re
import shutil
from typing import TYPE_CHECKING

from testkit import ROOT, Scratch, main

if TYPE_CHECKING:
    from pathlib import Path

KIT = "tests/gate/kit"
BASELINE = f"{KIT}/testkit/gh-store-users.txt"
FROZEN = '''"""Scenarios the scratch kit lists as store users."""

from testkit import Scratch, main


def stores(s: Scratch) -> None:
    s.gh.put(1, {"number": 1})


def reads(s: Scratch) -> None:
    s.gh.store("issue/1.json", {"number": 1})


if __name__ == "__main__":
    main(stores, reads)
'''
TAPED = '''"""Scenarios the scratch kit lists as store users."""

from testkit import Scratch, main


def stores(s: Scratch) -> None:
    s.gh.put(1, {"number": 1})


def reads(s: Scratch) -> None:
    s.gh.store("tape.json", [])
    assert s.gh.log() == []


if __name__ == "__main__":
    main(stores, reads)
'''
TEST_FROZEN = """from frozen import reads, stores


def test_frozen_stores(case):
    case(stores)


def test_frozen_reads(case):
    case(reads)
"""
MAIN = "refs/heads/main"
PUT_LINE = 's.gh.put(1, {"number": 1})'
READ_LINE = 's.gh.store("issue/1.json", {"number": 1})'
STORES = f"{KIT}/test_frozen.py::test_frozen_stores"
READS = f"{KIT}/test_frozen.py::test_frozen_reads"
FIX = "check-fake-gh (synthetic-recording, #1252): a test may not drive the hand-written fake gh's"


def lines(text: str) -> list[str]:
    return [x for x in text.splitlines() if x and not x.startswith("#")]


def write_baseline(k: Path, add: tuple[str, ...] = (), drop: tuple[str, ...] = ()) -> None:
    p = k / BASELINE
    text = p.read_text()
    head = [x for x in text.splitlines() if x.startswith("#")]
    body = sorted((set(lines(text)) | set(add)) - set(drop))
    p.write_text("\n".join(head + body) + "\n")


def build(s: Scratch) -> None:
    k = s.root / "k"
    (k / "scripts").mkdir(parents=True)
    for name in ("check-fake-gh", "octo-feather-gate"):
        shutil.copy2(ROOT / "scripts" / name, k / "scripts" / name)
    (k / KIT / "testkit").mkdir(parents=True)
    for p in [*(ROOT / KIT).glob("*.py"), *(ROOT / KIT / "testkit").glob("*.py"), ROOT / BASELINE]:
        shutil.copy2(p, k / p.relative_to(ROOT))
    for p in (ROOT / "tests").glob("*.sh"):
        shutil.copy2(p, k / "tests" / p.name)
    (k / KIT / "frozen.py").write_text(FROZEN)
    (k / KIT / "test_frozen.py").write_text(TEST_FROZEN)
    write_baseline(k, add=(STORES, READS))
    s.git(k, "init", "-q", "-b", "main")
    s.git(k, "add", "-A")
    s.git(k, "commit", "-q", "-m", "base")
    s.git(k, "checkout", "-q", "-b", "lane")


def kit_copy(s: Scratch) -> tuple[Path, str]:
    """The prepared copy, and its base commit's 12-character id."""
    s.prepare("check-fake-gh", build)
    k = s.root / "k"
    return k, s.git(k, "rev-parse", "main")[:12]


def check(s: Scratch, k: Path, want: int) -> list[str]:
    r = s.run([str(k / "scripts" / "check-fake-gh")], want=want, cwd=k)
    if want:
        assert r.err.startswith(FIX), r.err
    return r.out.splitlines()


def passes(s: Scratch) -> None:
    """The kit copy as committed: exit 0, the users counted against the baseline, every line in
    the baseline at the merge base; frozen.py's two items among them."""
    k, base = kit_copy(s)
    n = len(lines((k / BASELINE).read_text()))
    assert n > 2, n
    assert check(s, k, 0) == [
        f"only-down: every line in the baseline at {base}, the merge base with refs/heads/main",
        f"check-fake-gh: ok: {n} store users, as {BASELINE} lists ({n} lines)",
    ]


def new_use(s: Scratch) -> None:
    """A new scenario storing into the fake gh is refused naming its item and the using line; a
    tape-only one beside it (tape.json, then the call log) is no use; its line hand-added is
    refused as absent at the merge base."""
    k, base = kit_copy(s)
    (k / KIT / "fresh.py").write_text(
        TAPED.replace("Scenarios the scratch kit lists", "New scenarios").replace(
            's.gh.put(1, {"number": 1})', 's.gh.store("pr/2.json", {"number": 2})'
        )
    )
    (k / KIT / "test_fresh.py").write_text(TEST_FROZEN.replace("frozen", "fresh"))
    item = f"{KIT}/test_fresh.py::test_fresh_stores"
    assert check(s, k, 1) == [
        f'new use: {item}: {KIT}/fresh.py:7: s.gh.store("pr/2.json", {{"number": 2}})',
        f"only-down: every line in the baseline at {base}, the merge base with refs/heads/main",
    ]
    write_baseline(k, add=(item,))
    assert check(s, k, 1) == [
        f"hand-added: {item}: absent from the baseline at {base}, the merge base with {MAIN}",
        f"only-down: every line in the baseline at {base}, the merge base with refs/heads/main",
    ]


def moved_off(s: Scratch) -> None:
    """A listed item moved off the store (its scenario now tape-only) is refused, its line stale,
    until the line is deleted; then exit 0."""
    k, base = kit_copy(s)
    (k / KIT / "frozen.py").write_text(TAPED)
    assert check(s, k, 1) == [
        f"stale: {READS}: no store use found (or no such item): delete its line",
        f"only-down: every line in the baseline at {base}, the merge base with refs/heads/main",
    ]
    write_baseline(k, drop=(READS,))
    out = check(s, k, 0)
    assert re.fullmatch(r"check-fake-gh: ok: \d+ store users, as .* lists \(\d+ lines\)", out[-1])


def renamed(s: Scratch) -> None:
    """A listed item renamed reads as a new use plus a stale line, refused; its line renamed in
    the baseline too is refused as hand-added (a rename is no carry-over: the check's header)."""
    k, base = kit_copy(s)
    t = k / KIT / "test_frozen.py"
    t.write_text(t.read_text().replace("test_frozen_stores", "test_frozen_keeps"))
    kept = f"{KIT}/test_frozen.py::test_frozen_keeps"
    assert check(s, k, 1) == [
        f'new use: {kept}: {KIT}/frozen.py:7: s.gh.put(1, {{"number": 1}})',
        f"stale: {STORES}: no store use found (or no such item): delete its line",
        f"only-down: every line in the baseline at {base}, the merge base with refs/heads/main",
    ]
    write_baseline(k, add=(kept,), drop=(STORES,))
    assert check(s, k, 1) == [
        f"hand-added: {kept}: absent from the baseline at {base}, the merge base with {MAIN}",
        f"only-down: every line in the baseline at {base}, the merge base with refs/heads/main",
    ]


def no_default(s: Scratch) -> None:
    """No default branch (a gate's copy of the kit may hold none): the check says so and judges
    no line by the merge-base rule, never passing silently."""
    k, _ = kit_copy(s)
    s.git(k, "branch", "-q", "-D", "main")
    n = len(lines((k / BASELINE).read_text()))
    assert check(s, k, 0) == [
        "only-down: none judged: no default branch or no merge base with it",
        f"check-fake-gh: ok: {n} store users, as {BASELINE} lists ({n} lines)",
    ]


def replayed(s: Scratch) -> None:
    """--replay REV (a Replay row): a commit adding a store-using item is refused naming it,
    against the check's own measurement at its parent, with no baseline line read; a commit adding
    a tape-only item passes."""
    k, _ = kit_copy(s)
    (k / KIT / "taped.py").write_text(TAPED)
    (k / KIT / "test_taped.py").write_text(
        TEST_FROZEN.replace("frozen", "taped").replace("    case(stores)\n", "    case(reads)\n")
    )
    s.git(k, "add", "-A")
    s.git(k, "commit", "-q", "-m", "tape-only")
    taped = s.git(k, "rev-parse", "HEAD")[:12]
    (k / KIT / "fresh.py").write_text(FROZEN)
    (k / KIT / "test_fresh.py").write_text(TEST_FROZEN.replace("frozen", "fresh"))
    s.git(k, "add", "-A")
    s.git(k, "commit", "-q", "-m", "store")
    fresh = s.git(k, "rev-parse", "HEAD")[:12]
    cmd = [str(k / "scripts" / "check-fake-gh"), "--replay"]
    n = len(lines((k / BASELINE).read_text()))
    r = s.run([*cmd, taped], cwd=k)
    assert r.out == f"replay {taped}: {n} store users, {n} at its first parent (0 new, 0 gone)"
    r = s.run([*cmd, fresh], want=1, cwd=k)
    assert r.out.splitlines() == [
        f"new use: {KIT}/test_fresh.py::test_fresh_reads: {KIT}/fresh.py:11: {READ_LINE}",
        f"new use: {KIT}/test_fresh.py::test_fresh_stores: {KIT}/fresh.py:7: {PUT_LINE}",
        f"replay {fresh}: {n + 2} store users, {n} at its first parent (2 new, 0 gone)",
    ], r.out
    assert r.err.startswith(FIX), r.err


if __name__ == "__main__":
    main(passes, new_use, moved_off, renamed, no_default, replayed)
