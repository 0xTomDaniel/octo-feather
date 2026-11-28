#!/usr/bin/env python3
"""`octo-feather-lane digest`, one UTC day's merge digest (issue-lifecycle spec #gates-digest,
#acceptance-merge-digest; issue 1339): what it reads and prints, HELP below, the chunk the hub
shows in `octo-feather-lane --help`. The hub imports this module only when `digest` runs or its
help prints (#1274 comment 7232729794).

Interface:

    digest(args, state, err) -> str
        The digest ARGS ask for (`[DAY] [--repo O/R]`, HELP), STATE the state dir (the hub's
        $(octo-feather-state)), its post-merge records read there; ERR (the caller's refusal
        class) raised naming the fix on bad arguments, a gh failure or an unreadable record.

Standard library only (AGENTS.md: the kit's scripts); how a command finds this module:
scripts/correction_lanes.py's docstring.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

import post_merge
from tracker_calls import gh

if TYPE_CHECKING:
    from pathlib import Path

HELP = """\
  octo-feather-lane digest [DAY] [--repo O/R]
                                   the merge digest of UTC day DAY (YYYY-MM-DD; default
                                   yesterday's)

`digest` (issue 1339; issue-lifecycle #gates-digest) prints what merged into the repository's
default branch (`gh repo view [O/R] --json defaultBranchRef`) in [DAY 00:00Z, DAY+1 00:00Z) by
GitHub's mergedAt, read with `gh pr list --state merged --base <it> --search
"merged:<DAY-1>..<DAY+1>"`, the day itself kept in Python (a search date is not UTC). Each PR is
matched to the post-merge record ($(octo-feather-state)/post-merge/*.json) whose pr and merge
commit are its own, and shown, in merge order, by the ask `merge` recorded there (merge, above):
a tier 1 in one line, `#<n> <title> (tier 1, merged HH:MMZ) <url>`; a tier 2 in full: that line,
then merged time, head and merge commit, the tier block (`Tier`, each reason, `Waits for`), how
it was allowed, each spec call the lane added in full (spec, kind, at, lane, anchors, criteria,
what, why, evidence, role, ruling, and denied when the owner denied it) and each
behaviour-neutral opt-out (its commit and reason); a tier 3 in one line, `... (tier 3, merged
HH:MMZ): owner approved, merged on the director's relay <at> <url>`. A PR with no recorded ask
(merged before the merge recorded one, outside `merge`, or its record replaced by a later merge
of the lane) prints `#<n> <title> (tier not recorded: <why>) <url>, merge <sha>`: never a tier,
and the merge ask check is never rerun for it. It reads only those two gh answers and the
records. Exit 0; 1 refused (bad arguments, gh failing, a record unreadable), naming the fix.
"""

DAY = re.compile(r"\d{4}-\d{2}-\d{2}")
REPO = re.compile(r"[\w.-]+/[\w.-]+")
FIELDS = "number,title,url,mergedAt,mergeCommit,headRefOid"
LIMIT = 1000  # merged PRs in the three-day search window, gh paginating
ONE = dt.timedelta(days=1)


@dataclass(frozen=True)
class Merged:
    """A PR merged that day, as gh lists it."""

    number: int
    title: str
    url: str
    at: dt.datetime
    merge: str
    head: str


def digest(args: list[str], state: Path, err: type[Exception]) -> str:
    """The digest ARGS ask for (the module docstring)."""
    day, repo = _args(args, err)
    recs = _records(state, err)
    prs = _merged(day, repo, err)
    span = f"merged in [{day} 00:00Z, {day + ONE} 00:00Z)"
    out = [f"Merge digest {day} ({repo or 'this repository'}, {span}): {len(prs)} merged"]
    for p in prs:
        rec = next((r for r in recs if r.pr == p.number and r.merge.lower() == p.merge), None)
        out += ["", *_shown(p, rec)]
    return "\n".join(out)


def _args(args: list[str], err: type[Exception]) -> tuple[dt.date, str | None]:
    got = " ".join(args) or "nothing"
    usage = f"usage: octo-feather-lane digest [DAY] [--repo O/R] (DAY YYYY-MM-DD, UTC; got {got})"
    repo: str | None = None
    if "--repo" in args:
        i = args.index("--repo")
        if i + 1 >= len(args) or not REPO.fullmatch(args[i + 1]):
            raise err(usage)
        repo, args = args[i + 1], args[:i] + args[i + 2 :]
    if len(args) > 1 or (args and not DAY.fullmatch(args[0])):
        raise err(usage)
    try:
        day = dt.date.fromisoformat(args[0]) if args else None
    except ValueError as e:
        msg = f"{usage}: {e}"
        raise err(msg) from e
    return day or dt.datetime.now(dt.timezone.utc).date() - ONE, repo


def _records(state: Path, err: type[Exception]) -> list[post_merge.Record]:
    """Every post-merge record in STATE's records dir."""
    d = post_merge.records(state / "lanes")
    out: list[post_merge.Record] = []
    for p in sorted(d.glob("*.json")) if d.is_dir() else []:
        try:
            rec = post_merge.read(d, p.stem)
        except post_merge.Unreadable as e:
            msg = f"{e}; no digest printed"
            raise err(msg) from e
        if rec is not None:
            out.append(rec)
    return out


def _merged(day: dt.date, repo: str | None, err: type[Exception]) -> list[Merged]:
    """The PRs merged into the default branch on DAY, by GitHub's mergedAt, in merge order."""
    fix = "check gh auth status and the repository, then rerun; no digest printed"
    view = ["repo", "view", *([repo] if repo else []), "--json", "defaultBranchRef"]
    base = str(json.loads(gh(view, fix, err=err))["defaultBranchRef"]["name"])
    search = f"merged:{day - ONE}..{day + ONE}"
    ask = ["pr", "list", "--state", "merged", "--base", base, "--search", search]
    ask += ["--limit", str(LIMIT), "--json", FIELDS, *(["-R", repo] if repo else [])]
    start = dt.datetime(day.year, day.month, day.day, tzinfo=dt.timezone.utc)
    out: list[Merged] = []
    for x in cast("list[dict[str, object]]", json.loads(gh(ask, fix, err=err))):
        at = dt.datetime.fromisoformat(str(x["mergedAt"]).replace("Z", "+00:00"))
        if not start <= at < start + ONE:
            continue
        mc = x.get("mergeCommit")
        merge = str(cast("dict[str, object]", mc).get("oid", "")) if isinstance(mc, dict) else ""
        n, head = cast("int", x["number"]), str(x["headRefOid"]).lower()
        out.append(Merged(n, str(x["title"]), str(x["url"]), at, merge.lower(), head))
    return sorted(out, key=lambda m: (m.at, m.number))


def _shown(p: Merged, rec: post_merge.Record | None) -> list[str]:
    """P's lines by REC's ask (HELP)."""
    if rec is None or rec.ask is None:
        why = "no merge record" if rec is None else "its merge record holds no ask"
        return [f"#{p.number} {p.title} (tier not recorded: {why}) {p.url}, merge {p.merge}"]
    a, hhmm = rec.ask, f"{p.at:%H:%MZ}"
    n = a.tier[0].removeprefix("Tier: ") if a.tier else "?"
    relay = f"on the director's relay {a.relay}"
    how = {"tier": "", "relay": relay, "relay carried": f"{relay}, carried: {a.proof}"}[a.allowed]
    if n == "3":
        return [
            f"#{p.number} {p.title} (tier 3, merged {hhmm}): owner approved, merged {how} {p.url}"
        ]
    line = f"#{p.number} {p.title} (tier {n}, merged {hhmm}{', ' + how if how else ''}) {p.url}"
    if n == "1":
        return [line]
    out = [line, f"  merged {p.at:%Y-%m-%dT%H:%M:%SZ}, head {p.head}, merge {p.merge}"]
    out += [f"  {t}" for t in a.tier]
    out.append(f"  allowed: {how or 'by its tier, waiting for nobody'}")
    for c in a.calls:
        out += _call(c)
    out += [f"  opt-out {o.commit}: {o.reason}" for o in a.optouts]
    return out


def _call(c: post_merge.CallLine) -> list[str]:
    """A spec call in full, from its call-log line."""
    d = cast("dict[str, object]", json.loads(c.line))

    def f(k: str) -> str:
        v = d.get(k)
        return (
            ", ".join(map(str, cast("list[object]", v)))
            if isinstance(v, list)
            else str(v or "none")
        )

    out = [f"  spec call {c.spec} {f('kind')} at {f('at')} (lane {f('lane')})"]
    fields = ("anchors", "criteria", "what", "why", "evidence", "role", "ruling")
    out += [f"    {k}: {f(k)}" for k in fields]
    denied = d.get("denied")
    if isinstance(denied, dict) and denied:
        out.append(f"    denied: {json.dumps(denied, ensure_ascii=False)}")
    return out
