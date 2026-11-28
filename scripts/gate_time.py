#!/usr/bin/env python3
"""gate_time: the gate time's lines and readers, and the head's failed and pending checks. Moved
from scripts/merge_ask.py, which imports them, for the lane's commands that use them (ticket
#1335, evidence/gh1274-split/split.py helpers); standard library only (AGENTS.md Rules, kit
scripts)."""

__all__ = [  # what merge_ask.py and the lane's command groups import from here
    "BUDGET",
    "TREND",
    "bad_checks",
    "budget_lines",
    "budget_parse",
    "numbered_jsonl",
    "passed_full",
    "stamp",
]

import json
import statistics
from pathlib import Path
from typing import TYPE_CHECKING, cast

import tomllib
from tracker_calls import utc

if TYPE_CHECKING:
    import datetime as dt


TREND = "check-runs.jsonl"  # the state dir's gate run ledger, the gate time's trend (#1335)


# --- the gate time's lines, shared with octo-feather-lane's report (moved whole, #1150) ---

BUDGET = (
    "gate-budget.toml"  # the repo root's gate-time budget, kept by the factory (form: budget_text)
)
BUDGET_TREND = 5  # trend runs shown when the repo has no budget file to set trend_runs
SLOWEST = 5  # slowest items shown


Budget = dict[str, float]  # budget_seconds, growth_share, trend_runs (an int)
Run = dict[str, object]  # one check-runs.jsonl line


def numbered_jsonl(path: Path) -> tuple[list[tuple[int, Run]], list[int]] | None:
    """A JSON lines file's object lines with their numbers, and the numbers of the lines that are
    not one; None with no file."""
    if not path.exists():
        return None
    rows: list[tuple[int, Run]] = []
    bad: list[int] = []
    for i, ln in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not ln.strip():
            continue
        try:
            d: object = json.loads(ln)
        except ValueError:
            d = None
        if isinstance(d, dict):
            rows.append((i, cast("Run", d)))
        else:
            bad.append(i)
    return rows, bad


def budget_parse(text: str | None) -> tuple[Budget | None, str]:
    """gate-budget.toml's three numbers, or None and why: absent (text None) or invalid.
    budget_seconds: the full gate's wall-time budget; growth_share: the share of growth over the
    trend's median that is flagged; trend_runs: how many passed full runs before the latest make
    the trend. Stdlib tomllib: the kit's scripts stay stdlib-only (AGENTS.md)."""
    if text is None:
        return None, f"{BUDGET}: none"
    try:
        d: dict[str, object] = tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        return None, f"{BUDGET}: {e}"
    least = {"budget_seconds": 0.0, "growth_share": 0.0, "trend_runs": 1.0}
    ok: Budget = {}
    for k, low in least.items():
        v = d.get(k)
        if (
            isinstance(v, (int, float))
            and not isinstance(v, bool)
            and (v > low if k == "budget_seconds" else v >= low)
            and (k != "trend_runs" or isinstance(v, int))
        ):
            ok[k] = v
    bad = [f"{k} {d.get(k)!r} is not a number of the right range" for k in least if k not in ok]
    # the per-test CPU budget, optional: the gate's own (tests/gate/conftest.py) reads it
    cpu = d.get("test_cpu_seconds")
    if cpu is not None and (isinstance(cpu, bool) or not isinstance(cpu, (int, float)) or cpu <= 0):
        bad.append(f"test_cpu_seconds {cpu!r} is not a number of the right range")
    # octo-feather-slot reads and checks them
    slots = {
        "heavy_items",
        "heavy_slots",
        "eval_slots",
        "slot_grace_seconds",
        "slot_bound_seconds",
        "fast_workers",  # the fast tier's cap: tests/gate/heavy_slot.py reads it
        "fast_runs",  # fast-tier runs at once on the box: tests/gate/heavy_slot.py reads it
    }
    bad += [f"unknown key {k}" for k in sorted(set(d) - set(least) - {"test_cpu_seconds"} - slots)]
    return (None, f"{BUDGET}: " + "; ".join(bad)) if bad else (ok, "")


def total(d: Run) -> float:
    t = d.get("total_s")
    return float(t) if isinstance(t, (int, float)) else 0.0


def passed_full(rows: list[tuple[int, Run]], heads: set[str]) -> list[Run]:
    """check-runs.jsonl lines of passed full gate runs (tier full, exit 0, the runner's own
    fields) on HEADS, oldest first."""
    runs = [
        d
        for _, d in rows
        if d.get("tier") == "full"
        and d.get("exit") == 0
        and d.get("head") in heads
        and utc(d.get("start")) is not None
        and isinstance(d.get("total_s"), (int, float))
    ]
    # UTC instants of one form: text order is time order
    return sorted(runs, key=lambda d: str(d.get("start")))


def secs(x: float) -> str:
    return f"{round(x, 3):g}s"


def budget_lines(  # noqa: PLR0913, PLR0917  the run, its trend, the budget and how it is shown
    last: Run, before: list[Run], budget: Budget | None, why: str, now: object, pad: str
) -> list[str]:
    """The full gate run LAST against BUDGET, with the trend (passed full runs BEFORE it, oldest
    first) and its slowest items; flags OVER BUDGET and GROWN. Display only: no gate reads it
    (issue-lifecycle #lanes-checkpoints)."""
    t = total(last)
    run = (
        f"{pad}full gate: {secs(t)}, head {str(last.get('head'))[:12]}, started "
        f"{stamp(last.get('start'), now)}"
    )
    if budget is None:
        out = [f"{run}: no budget ({why})"]
    else:
        b = float(budget["budget_seconds"])
        out = [
            f"{run}: "
            + (
                f"OVER BUDGET by {secs(t - b)}"
                if t > b
                else f"within budget, {secs(b - t)} to spare"
            )
            + f" (budget {secs(b)})"
        ]
    base = before[-int(budget["trend_runs"] if budget else BUDGET_TREND) :]
    if not base:
        out.append(f"{pad}growth: no passed full run before it to compare")
    else:
        med = statistics.median(total(d) for d in base)
        grow = (t - med) / med if med else 0.0
        g = (
            f"{pad}growth: {grow:+.1%} over the trend's median {secs(med)} (the {len(base)} "
            f"passed full run{'s' * (len(base) > 1)} before it)"
        )
        if budget is None:
            out.append(f"{g}; no set share ({why})")
        else:
            share = float(budget["growth_share"])
            out.append(
                f"{g}; set share {share * 100:g}%: " + ("GROWN" if grow > share else "within")
            )
    out.append(
        f"{pad}trend: "
        + ", ".join(
            f"{secs(total(d))} {str(d.get('head'))[:12]} {d.get('start')}" for d in [*base, last]
        )
        + " (passed full runs, oldest first)"
    )
    raw = last.get("steps")
    steps: list[tuple[float, str]] = []
    for x in cast("list[object]", raw) if isinstance(raw, list) else []:
        st = cast("dict[str, object]", x) if isinstance(x, dict) else {}
        sec = st.get("seconds")
        if isinstance(sec, (int, float)):
            steps.append((float(sec), str(st.get("name"))))
    top = sorted(steps, key=lambda s: (-s[0], s[1]))[:SLOWEST]
    out.append(
        f"{pad}slowest: "
        + (", ".join(f"{name} {secs(sec)}" for sec, name in top) or "no items recorded")
    )
    return out


def stamp(s: object, now: object) -> str:
    t = utc(s)
    if t is None:
        return f"{s!r} (not a UTC instant)" if s not in (None, "") else "(not recorded)"
    n = int((cast("dt.datetime", now) - t).total_seconds())
    sign, n = ("", n) if n >= 0 else ("-", -n)
    d, h, m = n // 86400, n // 3600 % 24, n // 60 % 60
    age = (f"{d}d" if d else "") + (f"{h}h" if d or h else "") + f"{m}m"
    return f"{t:%Y-%m-%dT%H:%M:%SZ} ({sign}{age} ago)"


def bad_checks(rollup: list[dict[str, object]]) -> tuple[list[str], list[str]]:
    """(the failed checks, the pending ones) of ROLLUP (gh pr view statusCheckRollup), each
    `<name> <state>`."""
    failed: list[str] = []
    pending: list[str] = []
    for c in cast("list[dict[str, str]]", rollup):
        name = c.get("name") or c.get("context") or "?"
        if c.get("__typename") == "StatusContext" or ("state" in c and "conclusion" not in c):
            s = (c.get("state") or "").upper()
            (
                pending if s in ("PENDING", "EXPECTED", "") else failed if s != "SUCCESS" else []
            ).append(f"{name} {s.lower() or 'pending'}")
        elif (c.get("status") or "COMPLETED").upper() != "COMPLETED" or not c.get("conclusion"):
            pending.append(f"{name} {(c.get('status') or 'pending').lower()}")
        elif c["conclusion"].upper() not in ("SUCCESS", "NEUTRAL", "SKIPPED"):
            failed.append(f"{name} {c['conclusion'].lower()}")
    return failed, pending
