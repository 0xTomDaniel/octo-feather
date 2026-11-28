#!/usr/bin/env python3
"""`octo-feather-lane digest`, the merge digest of a UTC day or of every due day (issue-lifecycle
spec #gates-digest, #acceptance-merge-digest; issues 1339, 1340): what it reads and prints, HELP
below, the chunk the hub shows in `octo-feather-lane --help`; and `octo-feather-lane veto`
(issue 1341), HELP's last entry. The hub imports this module only when `digest` or `veto` runs
or its help prints, or when `merge` or `start` runs the due check (#1274 comment 7232729794).

Interface:

    digest(args, state, err) -> str
        The digest ARGS ask for (`[DAY] [--repo O/R]`, HELP): DAY's, else every due day's, then
        its sha256 prefix line; STATE the state dir (the hub's $(octo-feather-state)), its
        post-merge records and director log read there; ERR (the caller's refusal class) raised
        naming the fix on bad arguments, a gh failure or an unreadable record or log line.
    sent(args, sha, state, err) -> str
        `digest [DAY] [--repo O/R] --sent SHA`: the same digest remade, refused unless its sha256
        starts with SHA, then one director-log `digest` line appended (HELP); the line printed.
        The caller refuses first anywhere but the director's pane.
    due(state, repo, err) -> Due | None
        The due check both edges call (`merge`, `start`): the due days of REPO (None: every
        record's), as HELP says, None when none; no gh call. Due.line the director's line,
        Due.key its tell key, Due.told whether a post-merge record's told holds that key.
    veto(args, said, state, err) -> str
        `veto PR [--repo O/R] --said WORDS` (issue 1341): the owner's veto of a merge a sent
        digest listed filed as a repair lane's parent issue, one director-log `veto` line
        appended, the lane start's brief written under STATE; what it printed (HELP). The
        caller refuses first anywhere but the director's pane.

Standard library only (AGENTS.md: the kit's scripts); how a command finds this module:
scripts/correction_lanes.py's docstring.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import shlex
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, TypedDict, cast

import post_merge
import tomllib  # stdlib since 3.11; ruff, at the 3.10 floor, sorts it as third-party
from correction_lanes import DIRECTOR_LOG
from handoff_log import encode, read_log
from kit_env import kit_python
from merge_ask import VALIDATE
from tracker_calls import KIT, gh, tracker

if TYPE_CHECKING:
    from pathlib import Path

HELP = """\
  octo-feather-lane digest [DAY] [--repo O/R] [--sent SHA12]
                                   the merge digest of UTC day DAY (YYYY-MM-DD), or of every
                                   due day; --sent records it sent

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
and the merge ask check is never rerun for it. It reads only those two gh answers per day and the
records, each gh answer validated against its schema (schemas/gh-repo-default-branch.schema.json,
schemas/gh-pr-merged.schema.json) before it is read. After the text, a blank line and `sha256
<its first 12 hex>`, the sha256 of the text above it (UTF-8). Exit 0; 1 refused (bad arguments,
gh failing or answering outside its schema, a record or director-log line unreadable), naming the
fix or the field rejected.

With no DAY (issue 1340) it prints every due day's digest, oldest first, one blank line apart,
then the one sha256 line; none due, `No merge digest due (...)` and no sha256. A due day is a
past UTC day (today never is) on which a post-merge record's step 1 (merged) was recorded ok, and
which no sent `digest` line of the director log ($(octo-feather-state)/director.handoffs.jsonl)
names, counted from the oldest day a sent line names, or with none at all from the first day a
record carries an ask, never all history. With --repo, only records whose lane record
(lanes/<lane>.toml, or lanes/archive/) names that `repository` or none, and sent lines of that
repo or null. No gh call: `merge` and `start` run this due check (one function, `due`). Known
limit: a record's day is when step 1 recorded the merge, seconds after GitHub's mergedAt, so a
merge in the last seconds of a day counts on the next; and a lane's record is replaced by its
next merge.

`merge` (above), once merged and its ask recorded, tells the director when any day is due, once
per newest due day (post-merge's tell, key `digest <day>`, skipped when any record's told holds
it): `merge digest due for <days>: octo-feather-lane digest [--repo O/R], send its text to the
owner, then octo-feather-lane digest [--repo O/R] --sent <sha12>` (--repo the lane record's
`repository`); a check that fails is named on stderr, exit 1, and the routine still runs.
`start` prints the same line first (no --repo), before its steps, whatever it does after.

`--sent SHA12` (12 to 64 hex) runs only in the director's pane, by `relay`'s check (below),
else refuses, `only the director records a digest sent`, nothing recorded and no gh call. It
remakes the digest for the same DAY or due days and refuses unless its sha256 starts with SHA12,
naming both, nothing recorded; then appends one director-log line {"at", "kind": "digest",
"repo" (the --repo given, else null), "days": [...], "prs": [...], "sha256", "sent": true}.
The director runs it after sending the owner the text `digest` printed. Check class:
declaration (docs/adr/0008 rung 2): the line rests on the director's word that it sent that
text; a stopgap until the owner's own record (#1262).

  octo-feather-lane veto PR --said WORDS [--repo O/R]
                                   the owner's veto of a merge a sent digest listed: files the
                                   repair lane's parent issue and prints its lane start

`veto` (issue 1341; issue-lifecycle #gates-digest, #gates-call-decision,
#acceptance-merge-digest-veto) runs only in the director's pane, by `relay`'s check, else refuses,
`only the director records a veto`. WORDS are the owner's words or a link to them. In order, each
refusal exit 1, nothing filed or recorded: a PR a director-log `veto` line of the repo (or null)
already names, naming the issue it filed, no gh call; then `gh pr view PR --json
state,title,url,mergedAt,mergeCommit [-R O/R]`, validated against
schemas/gh-pr-vetoed.schema.json: a PR not MERGED; a PR no sent `digest` line of the repo (or
null) lists in its prs. Then it files one top-level issue with the target's tracker skill's
issue-create (never --parent; --repo given, in that repo through GH_REPO), title `Veto: revert or
repair PR #<n> <title>`, its body: the PR's url, merge commit and merged time, the owner's words
(declared), the tier block and how the merge was allowed, as the post-merge record of that PR
and merge commit holds its ask (`tier not recorded: <why>` without one), each spec call that ask
holds quoted in full as its call log's line, marked DENIED by this veto, with the `denied` field
{"at", "note"} the repair lane sets on it in the commit that acts on it (the call log's own way:
#gates-call-decision, scripts/octo-feather-spec-status's docstring; veto writes no call log),
and the work: revert or repair merge <commit>. It appends one director-log line {"at", "kind":
"veto", "repo" (the --repo given, else null), "pr", "merge", "issue" (issue-create's key),
"said"}, writes the lane brief $(octo-feather-state)/veto/<issue>.brief.md (the issue body after
a header naming the issue), and prints `filed: issue <key> ...`, `recorded: veto of PR #<n> ...`,
then, last, the ordinary lane start for that issue, `octo-feather-lane start <key> --goal ...
--outcome ... --brief-file <the brief>`, which the director runs from its checkout of the repo:
veto spawns no agent, and the start's own checks apply. Exit 0; 1 refused, naming the fix. Check
class: declaration (docs/adr/0008 rung 2): the line rests on the director's word that the owner
vetoed; a stopgap until the owner records his own word (#1262).
"""

DAY = re.compile(r"\d{4}-\d{2}-\d{2}")
REPO = re.compile(r"[\w.-]+/[\w.-]+")
FIELDS = "number,title,url,mergedAt,mergeCommit,headRefOid"
LIMIT = 1000  # merged PRs in the three-day search window, gh paginating
ONE = dt.timedelta(days=1)
SHA12 = re.compile(r"[0-9a-f]{12,64}")
# gh's two answers, validated once at the edge (quality spec #acceptance-edge-validated) by the
# kit's locked jsonschema, as merge_ask.py validates its gh pr list (VALIDATE): every field typed,
# no other key; then trusted as the TypedDicts below.
BRANCH = KIT / "schemas" / "gh-repo-default-branch.schema.json"
MERGED = KIT / "schemas" / "gh-pr-merged.schema.json"
VETOED = KIT / "schemas" / "gh-pr-vetoed.schema.json"
PR = re.compile(r"[1-9][0-9]*")


class _Commit(TypedDict):
    oid: str


class _GhMerged(TypedDict):
    number: int
    title: str
    url: str
    mergedAt: str  # gh's field
    mergeCommit: _Commit  # gh's field
    headRefOid: str  # gh's field


class _Ref(TypedDict):
    name: str


class _GhVetoed(TypedDict):
    state: str
    title: str
    url: str
    mergedAt: str | None  # gh's field
    mergeCommit: _Commit | None  # gh's field


class _GhRepo(TypedDict):
    defaultBranchRef: _Ref  # gh's field


@dataclass(frozen=True)
class Merged:
    """A PR merged that day, as gh lists it."""

    number: int
    title: str
    url: str
    at: dt.datetime
    merge: str
    head: str


@dataclass(frozen=True)
class Due:
    """The due days of a repo (None: every record's), and whether a record's told holds Key."""

    days: tuple[dt.date, ...]
    repo: str | None
    told: bool

    @property
    def key(self) -> str:
        return f"digest {self.days[-1]}"

    @property
    def line(self) -> str:
        r = f" --repo {self.repo}" if self.repo else ""
        days = ", ".join(map(str, self.days))
        return (
            f"merge digest due for {days}: octo-feather-lane digest{r}, send its text to the "
            f"owner, then octo-feather-lane digest{r} --sent <sha12>"
        )


def digest(args: list[str], state: Path, err: type[Exception]) -> str:
    """The digest ARGS ask for (the module docstring)."""
    text, _, _, sha = _made(args, state, err)
    return f"{text}\n\nsha256 {sha[:12]}" if sha else text


def sent(args: list[str], sha: str, state: Path, err: type[Exception]) -> str:
    """The digest ARGS ask for recorded sent under SHA (the module docstring)."""
    if not SHA12.fullmatch(sha):
        msg = f"--sent takes the 12 hex `digest` printed after its text (sha256 ...), got {sha!r}"
        raise err(msg)
    _, days, prs, full = _made(args, state, err)
    if not days:
        msg = "no merge digest due: nothing to record sent"
        raise err(msg)
    named = ", ".join(map(str, days))
    if not full.startswith(sha):
        msg = (
            f"--sent {sha} is not the digest of {named} as remade now (sha256 {full[:12]}): "
            "nothing recorded; send the owner the text `digest` prints now, then rerun with "
            "the sha256 it prints"
        )
        raise err(msg)
    repo = _args(args, err)[1]
    at = f"{dt.datetime.now(dt.timezone.utc):%Y-%m-%dT%H:%M:%SZ}"
    line: dict[str, object] = {"at": at, "kind": "digest", "repo": repo}
    line["days"] = [str(d) for d in days]
    line |= {"prs": prs, "sha256": full, "sent": True}
    log = state / DIRECTOR_LOG
    with log.open("a", encoding="utf-8") as f:
        f.write(encode(line) + "\n")
    return f"recorded sent: merge digest of {named}, sha256 {full[:12]}, in {log}"


def due(state: Path, repo: str | None, err: type[Exception]) -> Due | None:
    """The due check (the module docstring)."""
    recs = _records(state, err)
    days = _due_days(state, recs, repo, err)
    if not days:
        return None
    d = Due(tuple(days), repo, told=False)
    return replace(d, told=any(d.key in r.told for r in recs))


def veto(args: list[str], said: str, state: Path, err: type[Exception]) -> str:
    """The owner's veto of PR filed and recorded (the module docstring)."""
    pr, repo = _veto_args(args, said, err)
    log = state / DIRECTOR_LOG
    lines = _log_lines(log, err)
    nothing = "nothing filed or recorded"
    done = next((x for x in lines if _veto_of(x, pr, repo)), None)
    if done is not None:
        msg = f"PR #{pr} is already vetoed: issue {done.get('issue')} ({done.get('at')}); {nothing}"
        raise err(msg)
    fix = f"check PR #{pr} exists in {repo or 'this repository'} and gh auth status; {nothing}"
    view = ["pr", "view", str(pr), "--json", "state,title,url,mergedAt,mergeCommit"]
    got = gh([*view, *(["-R", repo] if repo else [])], fix, err=err)
    p = cast("_GhVetoed", _valid(got, VETOED, "gh pr view", err, nothing))
    merged, commit = p["mergedAt"], p["mergeCommit"]
    if p["state"] != "MERGED" or merged is None or commit is None:
        msg = f"PR #{pr} is not merged ({p['state']}): only a merge can be vetoed; {nothing}"
        raise err(msg)
    sent = [x for x in lines if x.get("kind") == "digest" and x.get("sent") is True]
    if not any(_mine(x, repo) and pr in _prs(x) for x in sent):
        msg = (
            f"no sent merge digest of {repo or 'this repository'} lists PR #{pr}: the owner "
            f"vetoes only a merge a digest he was sent listed; {nothing}"
        )
        raise err(msg)
    m = commit["oid"]
    rec = next((r for r in _records(state, err) if r.pr == pr and r.merge.lower() == m), None)
    title = f"Veto: revert or repair PR #{pr} {p['title']}"
    body = _veto_body(pr, p, m, rec, said)
    env = {"GH_REPO": repo} if repo else None
    made = ["issue-create", "--title", title, "--body-file", "-"]
    out = tracker(*made, err=err, env=env, stdin=body)
    key = out.strip()
    if not key or len(key.split()) != 1:
        msg = f"issue-create printed {out[:200]!r}, no issue key: check the tracker; no line logged"
        raise err(msg)
    at = f"{dt.datetime.now(dt.timezone.utc):%Y-%m-%dT%H:%M:%SZ}"
    line = {"at": at, "kind": "veto", "repo": repo, "pr": pr, "merge": m, "issue": key}
    with log.open("a", encoding="utf-8") as f:
        f.write(encode({**line, "said": said}) + "\n")
    brief = state / "veto" / f"{key}.brief.md"
    brief.parent.mkdir(parents=True, exist_ok=True)
    head = f"Repair lane for the owner's veto of PR #{pr}: its parent issue {key} holds the work."
    brief.write_text(f"{head}\n\n{body}", encoding="utf-8")
    goal = f"Veto repair: PR #{pr}"
    outcome = (
        f"merge {m[:12]} of PR #{pr}, vetoed by the owner, reverted or repaired, each vetoed spec "
        "call marked denied"
    )
    start = ["octo-feather-lane", "start", key, "--goal", goal, "--outcome", outcome]
    where = f" (from your checkout of {repo})" if repo else ""
    return "\n".join(
        [
            f"filed: issue {key}, {title}",
            f"recorded: veto of PR #{pr} (merge {m[:12]}) in {log}",
            f"lane start{where}, brief {brief}:",
            shlex.join([*start, "--brief-file", str(brief)]),
        ]
    )


def _veto_args(args: list[str], said: str, err: type[Exception]) -> tuple[int, str | None]:
    got = " ".join(args) or "nothing"
    usage = f"usage: octo-feather-lane veto PR --said WORDS [--repo O/R] (got {got})"
    repo: str | None = None
    if "--repo" in args:
        i = args.index("--repo")
        if i + 1 >= len(args) or not REPO.fullmatch(args[i + 1]):
            raise err(usage)
        repo, args = args[i + 1], args[:i] + args[i + 2 :]
    if len(args) != 1 or not PR.fullmatch(args[0]) or not said.strip():
        msg = f"{usage}: WORDS the owner's words or a link to them, PR its number"
        raise err(msg)
    return int(args[0]), repo


def _mine(line: dict[str, object], repo: str | None) -> bool:
    """Whether director-log LINE is of REPO (None: of any), or of no repo named."""
    return repo is None or line.get("repo") in (repo, None)


def _prs(line: dict[str, object]) -> list[object]:
    """The prs a sent digest LINE lists; none when it holds no list."""
    v = line.get("prs")
    return cast("list[object]", v) if isinstance(v, list) else []


def _veto_of(line: dict[str, object], pr: int, repo: str | None) -> bool:
    return line.get("kind") == "veto" and line.get("pr") == pr and _mine(line, repo)


def _log_lines(log: Path, err: type[Exception]) -> list[dict[str, object]]:
    try:
        return read_log(log)[0] if log.exists() else []
    except OSError as e:
        msg = f"cannot read the director log {log} ({e}): fix it, then rerun; nothing filed"
        raise err(msg) from e


def _veto_body(pr: int, p: _GhVetoed, merge: str, rec: post_merge.Record | None, said: str) -> str:
    """The repair issue's body (HELP, veto)."""
    out = [
        (
            f"The owner vetoed PR #{pr} from the merge digest (issue-lifecycle #gates-digest). A "
            "veto reverts nothing by itself: this issue is the parent of the lane that reverts "
            "or repairs the merge."
        ),
        "",
        f"- PR: {p['url']} ({p['title']})",
        f"- Merge commit: {merge}",
        f"- Merged: {p['mergedAt']}",
        f"- Owner's words (declared by the director, `octo-feather-lane veto`): {said}",
        "",
        "## Tier, as recorded at merge",
        "",
    ]
    a = rec.ask if rec else None
    if a is None:
        why = "no merge record" if rec is None else "its merge record holds no ask"
        out.append(f"Tier not recorded: {why}.")
    else:
        how = {"tier": "by its tier", "relay": f"on the director's relay {a.relay}"}
        how["relay carried"] = f"on the director's relay {a.relay}, carried: {a.proof}"
        out += ["```", *a.tier, "```", "", f"Allowed: {how[a.allowed]}."]
    out += ["", "## Spec calls denied by this veto", ""]
    calls = a.calls if a else ()
    if not calls:
        out.append(f"None: PR #{pr}'s recorded ask holds no spec call.")
    else:
        note = f"vetoed by the owner from the merge digest (PR #{pr}): {said}"
        denied = json.dumps({"at": "<UTC time of that commit>", "note": note}, ensure_ascii=False)
        out.append(
            f"Each call below, which PR #{pr} added, is DENIED by this veto (issue-lifecycle "
            "#gates-call-decision). The repair lane records the denial in the call log's own "
            "way: in the commit that acts on it, it sets that call's line's `denied` field to "
            f"`{denied}`, the rest of the line unchanged (scripts/octo-feather-spec-status's "
            "docstring)."
        )
        for c in calls:
            out += ["", f"Spec {c.spec} ({c.spec}.calls.jsonl), DENIED by this veto:", ""]
            out += ["```json", c.line, "```"]
    out += [
        "",
        "## The work",
        "",
        (
            f"Revert or repair merge {merge} of PR #{pr}, through an ordinary lane, and set the "
            "`denied` field of each call above."
        ),
    ]
    return "\n".join(out) + "\n"


def _made(
    args: list[str], state: Path, err: type[Exception]
) -> tuple[str, list[dt.date], list[int], str]:
    """The digest ARGS ask for: its text, days, PRs and sha256 ("" when no day is due)."""
    day, repo = _args(args, err)
    recs = _records(state, err)
    days = [day] if day else _due_days(state, recs, repo, err)
    if not days:
        none = f"No merge digest due ({repo or 'this repository'}): no past UTC day with a merge"
        return f"{none} left unsent", [], [], ""
    blocks: list[str] = []
    numbers: list[int] = []
    for d in days:
        prs = _merged(d, repo, err)
        span = f"merged in [{d} 00:00Z, {d + ONE} 00:00Z)"
        out = [f"Merge digest {d} ({repo or 'this repository'}, {span}): {len(prs)} merged"]
        for p in prs:
            rec = next((r for r in recs if r.pr == p.number and r.merge.lower() == p.merge), None)
            out += ["", *_shown(p, rec)]
        blocks.append("\n".join(out))
        numbers += [p.number for p in prs]
    text = "\n\n".join(blocks)
    return text, days, numbers, hashlib.sha256(text.encode("utf-8")).hexdigest()


def _due_days(
    state: Path, recs: list[post_merge.Record], repo: str | None, err: type[Exception]
) -> list[dt.date]:
    """The due days of REPO from RECS and the director log's sent lines (HELP)."""
    lanes = state / "lanes"
    mine = [r for r in recs if repo is None or _lane_repo(lanes, r.lane) in (repo, None)]
    merged = [(r, d) for r in mine if (d := _merged_day(r, state, err))]
    done = _sent_days(state, repo, err)
    first = min((d for r, d in merged if r.ask is not None), default=None)
    floor = min(done) if done else first
    if floor is None:
        return []
    today = dt.datetime.now(dt.timezone.utc).date()
    return sorted({d for _, d in merged if floor <= d < today and d not in done})


def _merged_day(rec: post_merge.Record, state: Path, err: type[Exception]) -> dt.date | None:
    """The UTC day REC's step 1 recorded its merge ok; None when it did not."""
    s = rec.steps[0] if rec.steps else None
    if s is None or (s.number, s.name, s.outcome) != (1, "merged", "ok"):
        return None
    try:
        return dt.datetime.fromisoformat(s.at).astimezone(dt.timezone.utc).date()
    except ValueError as e:
        where = post_merge.records(state / "lanes") / f"{rec.lane}.json"
        msg = f"post-merge record {where}: step 1 at {s.at!r} is no time ({e}): fix it, then rerun"
        raise err(msg) from e


def _sent_days(state: Path, repo: str | None, err: type[Exception]) -> set[dt.date]:
    """The days the director log's sent `digest` lines of REPO (or null) name."""
    log = state / DIRECTOR_LOG
    try:
        lines = read_log(log)[0] if log.exists() else []
    except OSError as e:
        msg = f"cannot read the director log {log} ({e}): fix it, then rerun"
        raise err(msg) from e
    out: set[dt.date] = set()
    for x in lines:
        if x.get("kind") != "digest" or x.get("sent") is not True:
            continue
        days = x.get("days")
        if not isinstance(days, list) or not all(
            isinstance(d, str) and DAY.fullmatch(d) for d in cast("list[object]", days)
        ):
            msg = f"director log {log}: a sent digest line names no days ({encode(x)[:200]})"
            raise err(msg)
        if repo is None or x.get("repo") in (repo, None):
            out |= {dt.date.fromisoformat(d) for d in cast("list[str]", days)}
    return out


def _lane_repo(lanes: Path, lane: str) -> str | None:
    """The `repository` lane LANE's record names (open or archived); None when none does."""
    for p in (lanes / f"{lane}.toml", lanes / "archive" / f"{lane}.toml"):
        try:
            v = tomllib.loads(p.read_text(encoding="utf-8")).get("repository")
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
            continue
        return v if isinstance(v, str) and v else None
    return None


def _args(args: list[str], err: type[Exception]) -> tuple[dt.date | None, str | None]:
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
    return day, repo


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
    got = cast("_GhRepo", _valid(gh(view, fix, err=err), BRANCH, "gh repo view", err))
    base = got["defaultBranchRef"]["name"]
    search = f"merged:{day - ONE}..{day + ONE}"
    ask = ["pr", "list", "--state", "merged", "--base", base, "--search", search]
    ask += ["--limit", str(LIMIT), "--json", FIELDS, *(["-R", repo] if repo else [])]
    start = dt.datetime(day.year, day.month, day.day, tzinfo=dt.timezone.utc)
    out: list[Merged] = []
    for x in cast("list[_GhMerged]", _valid(gh(ask, fix, err=err), MERGED, "gh pr list", err)):
        at = dt.datetime.fromisoformat(x["mergedAt"].replace("Z", "+00:00"))
        if start <= at < start + ONE:
            m = x["mergeCommit"]["oid"]
            out.append(Merged(x["number"], x["title"], x["url"], at, m, x["headRefOid"]))
    return sorted(out, key=lambda m: (m.at, m.number))


def _valid(
    out: str, schema: Path, what: str, err: type[Exception], none: str = "no digest printed"
) -> object:
    """OUT, WHAT's JSON answer, once SCHEMA holds for it; ERR naming the field it rejects and
    NONE, what was not done."""
    try:
        p = kit_python("-c", VALIDATE, str(schema), stdin=out, capture=True)
    except OSError as e:
        msg = f"cannot run uv for the kit's locked jsonschema ({e}); {none}"
        raise err(msg) from e
    if p.returncode:
        said = "; ".join(p.stderr.strip().splitlines())[:300] or f"exit {p.returncode}"
        msg = f"{what}'s answer fails schemas/{schema.name} ({said}): {none}"
        raise err(msg)
    return json.loads(out)


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
