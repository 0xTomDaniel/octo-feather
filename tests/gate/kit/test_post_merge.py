"""The post-merge routine's record, resume and lock, in-process at its interface, `run` and `read`
of scripts/post_merge.py (its module docstring; ticket #1133, seam `post_merge.run` agreed on it
before any test; the rule: issue-lifecycle #gates-main-moved). The steps are this file's own
functions, the routine's input: each logs its call and returns the outcome the test sets. The
command's wiring (octo-feather-lane merge and post-merge over the testkit's stand-ins):
test_lane_merge.py."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pytest
from post_merge import Outcome, Step, Unreadable, read, run

if TYPE_CHECKING:
    from pathlib import Path

M = "f" * 40  # the merge commit step 1 learns


@dataclass
class Pm:
    pr: int = 7
    head: str = "1234567"
    merge: str = ""
    base: str = ""


@dataclass
class Steps:
    """Three steps, `merged` (learns the merge commit and base), `ci` and `tell`, each returning
    its outcome in `want` (ok by default); `called` each step's name as it runs."""

    want: dict[str, Outcome] = field(default_factory=dict)
    called: list[str] = field(default_factory=list)
    shown: list[tuple[int, str, str]] = field(default_factory=list)
    gate: threading.Event | None = None

    def step(self, name: str):  # noqa: ANN201 (a step function as run takes it)
        def body(pm: Pm) -> tuple[Outcome, str]:
            self.called.append(name)
            if name == "merged":
                pm.merge, pm.base = M, "main"
            if self.gate is not None and name == "ci":
                self.gate.wait(10)
            return self.want.get(name, "ok"), f"{name} line"

        return body

    def all(self) -> list[tuple[str, object]]:
        return [(n, self.step(n)) for n in ("merged", "ci", "tell")]

    def show(self, s: Step, how: str) -> None:
        self.shown.append((s.number, s.outcome, how))

    def run(self, d: Path, pm: Pm | None = None) -> list[tuple[int, str, str]]:
        self.called.clear()
        self.shown.clear()
        run("gh7", pm or Pm(), self.all(), self.show, d)  # pyright: ignore[reportArgumentType]
        return list(self.shown)


def outcomes(d: Path) -> list[tuple[int, str, str]]:
    rec = read(d, "gh7")
    assert rec is not None, "no record"
    return [(s.number, s.name, s.outcome) for s in rec.steps]


def test_resume_skips_ok_steps(tmp_path: Path) -> None:
    """A stopped step: the record holds steps 1-2, 2 stopped, step 3 not run. The rerun for the
    same merge (a longer head of it) runs no step recorded ok, shows step 1 recorded, takes the
    merge commit and base from the record, and resumes at step 2; the record then 1-3 ok."""
    st = Steps({"ci": "stopped"})
    assert st.run(tmp_path) == [(1, "ok", "ran"), (2, "stopped", "ran")]
    assert st.called == ["merged", "ci"]
    assert outcomes(tmp_path) == [(1, "merged", "ok"), (2, "ci", "stopped")]
    st.want.clear()
    pm = Pm(head="1234567890ab")
    assert st.run(tmp_path, pm) == [(1, "ok", "recorded"), (2, "ok", "ran"), (3, "ok", "ran")]
    assert st.called == ["ci", "tell"]
    assert (pm.merge, pm.base) == (M, "main")
    assert outcomes(tmp_path) == [(1, "merged", "ok"), (2, "ci", "ok"), (3, "tell", "ok")]
    rec = read(tmp_path, "gh7")
    assert rec is not None
    assert (rec.pr, rec.merge, rec.base, rec.steps[0].line) == (7, M, "main", "merged line")


def test_pending_resumes_and_other_merge_replaces(tmp_path: Path) -> None:
    """A pending last step: a rerun runs only it. A run for another merge (another head, then
    another PR) runs every step and replaces the record."""
    st = Steps({"tell": "pending"})
    st.run(tmp_path)
    assert st.run(tmp_path)[-1] == (3, "pending", "ran")
    assert st.called == ["tell"]
    st.want.clear()
    for pm in (Pm(head="abcdef0"), Pm(pr=8, head="abcdef0")):
        assert [h for _, _, h in st.run(tmp_path, pm)] == ["ran"] * 3
        assert st.called == ["merged", "ci", "tell"]
        rec = read(tmp_path, "gh7")
        assert rec is not None
        assert (rec.pr, rec.head) == (pm.pr, pm.head)


def test_second_run_waits(tmp_path: Path) -> None:
    """Two runs of one lane: the second runs no step while the first holds the lane (blocked in
    its step 2); once the first ends, the second reads its record and runs no step it did."""
    first, second = Steps(gate=threading.Event()), Steps()
    t1 = threading.Thread(target=first.run, args=(tmp_path,))
    t1.start()
    while first.called != ["merged", "ci"]:
        time.sleep(0.01)
    t2 = threading.Thread(target=second.run, args=(tmp_path,))
    t2.start()
    time.sleep(0.5)
    assert second.shown == [], f"second ran while the first held the lane: {second.shown}"
    assert first.gate is not None
    first.gate.set()
    t1.join(10)
    t2.join(10)
    assert second.called == [], second.called
    assert [h for _, _, h in second.shown] == ["recorded"] * 3


def test_unreadable_record(tmp_path: Path) -> None:
    """A record that is no JSON, or JSON that is no record: Unreadable naming the file, from read
    and from run, no step run."""
    st = Steps()
    for text in ("{", '{"lane": "gh7"}'):
        (tmp_path / "gh7.json").write_text(text)
        with pytest.raises(Unreadable, match=r"post-merge record .*gh7\.json"):
            read(tmp_path, "gh7")
        with pytest.raises(Unreadable):
            st.run(tmp_path)
        assert st.called == []
    assert read(tmp_path, "gh8") is None
