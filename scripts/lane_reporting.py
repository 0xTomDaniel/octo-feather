#!/usr/bin/env python3
"""lane_reporting: octo-feather-lane's report and spend. Moved from scripts/octo-feather-lane, the dispatcher (ticket #1333)."""

import dataclasses
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import cast

import merge_ask
from correction_lanes import DIRECTOR_LOG
from handoff_log import read_log
from lane_cli import NAME, Refuse, dtm, gh, lanes_dir, pr_view, reflect_module, state_dir
from merge_ask import BUDGET, budget_lines, budget_parse, numbered_jsonl, passed_full, stamp
from tracker_calls import utc

# --- spend (spec spend, issue #185) ---

SPEND_INT = ("input_tokens", "output_tokens")


def spend_lane(lanes: Path) -> str | None:
    """The lane whose supervisor pane is in the caller's Herdr space (spec spend#rule-lane), else None."""
    space = os.environ.get("HERDR_WORKSPACE_ID") or os.environ.get("OCTO_FEATHER_SPEND_SPACE", "")
    if not space:
        return None
    import tomllib
    for rec in sorted(lanes.glob("*.toml")):
        try:
            sup = tomllib.loads(rec.read_text(encoding="utf-8")).get("supervisor")
        except (OSError, ValueError):
            continue
        if isinstance(sup, str) and sup.split(":", 1)[0] == space:
            return rec.stem
    return None


def spend_line(raw: str, lane: str | None) -> dict:
    """One ledger record from one stdin line; ValueError names what is wrong."""
    import datetime as dt
    o = json.loads(raw)
    if not isinstance(o, dict):
        raise ValueError("not a JSON object")
    for k in ("model", "purpose"):
        if not isinstance(o.get(k), str) or not o[k].strip():
            raise ValueError(f"{k} must be a non-empty string")
    if "/" not in o["model"]:
        raise ValueError("model must be provider/id")
    for k in SPEND_INT:
        if type(o.get(k)) is not int or o[k] < 0:
            raise ValueError(f"{k} must be an integer >= 0")
    cost = o.get("cost_usd")
    if cost is not None and (type(cost) not in (int, float) or cost < 0 or cost != cost):
        raise ValueError("cost_usd must be a number >= 0 or null")
    at = o.get("at")
    if at is None:
        at = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    elif not isinstance(at, str) or spend_time(at) is None:
        raise ValueError("at must be an ISO 8601 time")
    return {"at": at, "lane": lane, "purpose": o["purpose"], "model": o["model"],
            "input_tokens": o["input_tokens"], "output_tokens": o["output_tokens"], "cost_usd": cost}


def spend_time(at: str):
    """AT as an aware UTC datetime (naive counts as UTC), or None."""
    import datetime as dt
    try:
        t = dt.datetime.fromisoformat(at.replace("Z", "+00:00") if at.endswith("Z") else at)
    except ValueError:
        return None
    return (t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)).astimezone(dt.timezone.utc)


def spend_record(args: list[str]) -> int:
    def unrecorded(why: str, recs: list[dict]) -> None:
        known = sum(r["cost_usd"] for r in recs if r["cost_usd"] is not None)
        unknown = sum(r["cost_usd"] is None for r in recs)
        what = f"{len(recs)} call(s), ${known:.6f}" + (f" + {unknown} of unknown cost" if unknown else "") if recs else "the call(s) on stdin"
        print(f"octo-feather-lane spend record: spend unrecorded ({what}): {why}", file=sys.stderr)
    recs: list[dict] = []
    ledger = "the ledger"
    try:
        if args[:1] == ["--lane"] and len(args) == 2 and NAME.fullmatch(args[1]):
            lane = args[1]
        elif not args:
            lane = None
        else:
            unrecorded(f"usage: octo-feather-lane spend record [--lane NAME] (got {' '.join(args)})", [])
            return 0
        ledger = state_dir() / "spend.jsonl"
        if lane is None:
            lane = spend_lane(ledger.parent / "lanes")
        bad = []
        for n, raw in enumerate(sys.stdin.read().splitlines(), 1):
            if not raw.strip():
                continue
            try:
                recs.append(spend_line(raw, lane))
            except ValueError as e:   # JSONDecodeError included
                bad.append(f"line {n}: {e}")
        if bad:
            unrecorded(f"{len(bad)} unreadable stdin line(s) skipped ({'; '.join(bad)})", [])
        if not recs:
            return 0
        data = "".join(json.dumps(r, separators=(",", ":")) + "\n" for r in recs).encode()
        import fcntl
        ledger.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(ledger, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            view = memoryview(data)
            while view:
                view = view[os.write(fd, view):]
        finally:
            os.close(fd)
    except Exception as e:
        unrecorded(f"cannot write {ledger} ({e})", recs)
    return 0


def openrouter_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if key:
        return key
    auth = Path.home() / ".pi" / "agent" / "auth.json"
    try:
        key = json.loads(auth.read_text(encoding="utf-8")).get("openrouter", {}).get("key", "")
    except FileNotFoundError:
        raise Refuse(f"no OpenRouter key: OPENROUTER_API_KEY is unset and {auth} does not exist")
    except (OSError, ValueError, AttributeError) as e:
        raise Refuse(f"cannot read {auth} ({type(e).__name__})")
    if isinstance(key, str) and key.startswith("!"):
        try:
            key = subprocess.run(key[1:], shell=True, capture_output=True, text=True, timeout=30, check=True).stdout
        except (OSError, subprocess.SubprocessError) as e:
            raise Refuse(f"the `!` key command in {auth} failed ({type(e).__name__})")
    if not isinstance(key, str) or not key.strip():
        raise Refuse(f"no OpenRouter key: OPENROUTER_API_KEY is unset and {auth} has no openrouter.key")
    return key.strip()


def openrouter_usage() -> dict:
    """{daily, weekly, monthly} USD from GET /api/v1/key; Refuse with the reason (never the key)."""
    key = openrouter_key()
    url = "https://openrouter.ai/api/v1/key"
    auth = key.replace("\\", "\\\\").replace('"', '\\"')
    try:
        r = subprocess.run(["curl", "-sS", "--max-time", "20", "--config", "-", "-w", "\n%{http_code}", url],
                           input=f'header = "Authorization: Bearer {auth}"\n', capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as e:
        raise Refuse(f"GET {url}: curl failed ({type(e).__name__})")
    if r.returncode != 0:
        why = (r.stderr.strip().splitlines() or [f"curl exit {r.returncode}"])[-1]
        raise Refuse(f"GET {url}: unreachable ({why})")
    text, _, code = r.stdout.rpartition("\n")
    if code != "200":
        raise Refuse(f"GET {url}: HTTP {code}")
    try:
        body = json.loads(text)
    except ValueError as e:
        raise Refuse(f"GET {url}: not JSON ({e})")
    data = body.get("data") if isinstance(body, dict) else None
    out = {}
    for w in ("daily", "weekly", "monthly"):
        v = data.get(f"usage_{w}") if isinstance(data, dict) else None
        if type(v) not in (int, float):
            raise Refuse(f"GET {url}: no numeric data.usage_{w} in the reply")
        out[w] = float(v)
    return out


def cmd_spend(args: list[str]) -> int:
    if args[:1] == ["record"]:
        return spend_record(args[1:])
    if args:
        raise Refuse(f"usage: octo-feather-lane spend | spend record [--lane NAME] (got {' '.join(args)})")
    import datetime as dt
    ledger = state_dir() / "spend.jsonl"
    recs, skipped = [], 0
    try:
        lines = ledger.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        lines = []
    except (OSError, UnicodeDecodeError) as e:
        raise Refuse(f"cannot read the ledger {ledger} ({e}): fix its permissions, then rerun")
    for raw in lines:
        try:
            r = json.loads(raw)
            r["_t"] = spend_time(r["at"])
            if r["_t"] is None or not isinstance(r.get("model"), str):
                raise ValueError
            recs.append(r)
        except (ValueError, TypeError, KeyError):
            skipped += 1

    def money(v: float) -> str:
        return f"-${-v:.6f}" if v < 0 else f"${v:.6f}"

    def table(title: str, key) -> None:
        print(f"\nBy {title}:")
        groups: dict = {}
        for r in recs:
            g = groups.setdefault(key(r), [0.0, 0, 0, 0, 0])
            if r.get("cost_usd") is None:
                g[2] += 1
            else:
                g[0] += float(r["cost_usd"])
            g[1] += 1; g[3] += int(r.get("input_tokens") or 0); g[4] += int(r.get("output_tokens") or 0)
        if not groups:
            print("  (none)")
        for k in sorted(groups, key=str):
            usd, n, unk, i, o = groups[k]
            print(f"  {k:<32} {money(usd):>12}  calls {n:>5}  unknown cost {unk:>4}  tokens in {i} out {o}")

    print(f"Spend ledger: {ledger} ({len(recs)} calls" + (f", {skipped} unreadable lines skipped" if skipped else "") + ")")
    table("day (UTC)", lambda r: r["_t"].date().isoformat())
    table("lane", lambda r: r.get("lane") or "(no lane)")
    table("purpose", lambda r: r.get("purpose") or "(none)")
    table("lane and purpose", lambda r: f"{r.get('lane') or '(no lane)'} {r.get('purpose') or '(none)'}")
    table("model", lambda r: r["model"])

    now = dt.datetime.now(dt.timezone.utc)
    day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    starts = {"daily": ("today", day), "weekly": ("this week", day - dt.timedelta(days=day.weekday())),
              "monthly": ("this month", day.replace(day=1))}
    print("\nOpenRouter reconcile (windows and gap: `octo-feather-lane --help`, spend):")
    try:
        usage = openrouter_usage()
    except Refuse as e:
        usage = None
        print(f"  OpenRouter unavailable: {e}")
    print(f"  {'window':<11} {'openrouter':>12} {'ledger':>12} {'gap':>12}")
    for w, (label, start) in starts.items():
        mine = [r for r in recs if r["model"].startswith("openrouter/") and start <= r["_t"] <= now]
        led = sum(float(r["cost_usd"]) for r in mine if r.get("cost_usd") is not None)
        unk = sum(r.get("cost_usd") is None for r in mine)
        theirs = money(usage[w]) if usage else "n/a"
        gap = money(usage[w] - led) if usage else "n/a"
        print(f"  {label:<11} {theirs:>12} {money(led):>12} {gap:>12}" + (f"  ({unk} ledger calls of unknown cost)" if unk else ""))
    return 0


# --- the factory report (spec comms #factory-report, issue #248) ---

RUNNING = "working"   # the Herdr agent_status of an agent at work


def herdr_agents() -> list[dict]:
    try:
        p = subprocess.run(["herdr", "agent", "list"], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    except FileNotFoundError:
        raise Refuse("herdr not on PATH")
    if p.returncode:
        err = (p.stderr or p.stdout).strip().splitlines()
        raise Refuse(f"herdr agent list failed ({err[-1][:300] if err else f'exit {p.returncode}'})")
    try:
        agents = json.loads(p.stdout)["result"]["agents"]
        if not isinstance(agents, list) or not all(isinstance(a, dict) for a in agents):
            raise TypeError("agents is not a list of objects")
    except (ValueError, KeyError, TypeError) as e:
        raise Refuse(f"herdr agent list printed no agent list ({type(e).__name__}: {e})")
    return agents


def pending_gates(lines: list[dict]) -> list[tuple[str, object]]:
    """Each pending owner gate (spec comms #report-owner-queue), with its asked time."""
    latest: dict[str, dict] = {}
    for d in lines:
        if d.get("kind") == "gate" and isinstance(d.get("gate"), str) and d.get("event") in ("asked", "answered"):
            latest[d["gate"]] = d
    return [(g, d.get("at")) for g, d in latest.items() if d["event"] == "asked"]


def check_results(rollup: list[dict]) -> str:
    counts: dict[str, int] = {}
    for c in rollup:
        if c.get("__typename") == "StatusContext" or "state" in c and "conclusion" not in c:
            r = (c.get("state") or "pending").lower()
        elif (c.get("status") or "COMPLETED").upper() != "COMPLETED" or not c.get("conclusion"):
            r = (c.get("status") or "pending").lower()
        else:
            r = c["conclusion"].lower()
        counts[r] = counts.get(r, 0) + 1
    return ", ".join(f"{n} {r}" for r, n in sorted(counts.items())) or "none"


def owner_caught(state: Path, now, unread: list[str]) -> tuple[str, list[str]]:
    """The director log's owner-caught findings (spec comms #report-owner-caught): the headline, the count for the
    last seven days beside the seven before, and the block by class."""
    import datetime
    log = state / "director.handoffs.jsonl"
    head = f"owner-caught (headline, {log.name}):"
    if not log.exists():
        return f"{head} log none", [f"owner-caught: log {log.name}: none"]
    try:
        lines, bad = read_log(log)
    except (OSError, UnicodeDecodeError) as e:
        unread.append(f"log {log.name}")
        return f"{head} unread", [f"owner-caught: unread: log {log.name}: {e}"]
    seen: dict[str, list] = {}
    week = datetime.timedelta(days=7)
    weeks, undated = [0, 0], 0
    for d in lines:
        c = d.get("class")
        if d.get("kind") == "finding" and isinstance(c, str) and c.startswith("owner-caught-"):
            s = seen.setdefault(c, [0, None])
            s[0] += 1
            t = utc(d.get("at"))
            if s[1] is None or t is not None and ((u := utc(cast("object", s[1]))) is None or t > u):
                s[1] = d.get("at")
            if t is None:
                undated += 1
            elif t > now - week:
                weeks[0] += 1
            elif t > now - 2 * week:
                weeks[1] += 1
    head += f" {weeks[0]} in the last 7 days, {weeks[1]} in the 7 days before" + (
        f"; {undated} with no readable at, not counted" if undated else "")
    out = [f"owner-caught ({log.name}):" if seen else f"owner-caught ({log.name}): none"]
    out += [f"  class {c}: count {n}, last seen {stamp(at, now)}" for c, (n, at) in sorted(seen.items())]
    if bad:
        out.append(f"  log {log.name}: {len(bad)} unparsable line{'s' if len(bad) > 1 else ''} ({', '.join(map(str, bad))})")
    return head, out


def director_reflection(state: Path, now: object, unread: list[str]) -> str:
    """When the director reflection last ran (spec comms #report-reflection)."""
    log = state / DIRECTOR_LOG
    if not log.exists():
        return f"director reflection: never ran ({log.name}: none)"
    try:
        lines = read_log(log)[0]
    except (OSError, UnicodeDecodeError) as e:
        if f"log {log.name}" not in unread:
            unread.append(f"log {log.name}")
        return f"director reflection: unread: log {log.name}: {e}"
    at, _ = reflect_module().since_last_reflection(lines)
    return f"director reflection: never ran ({log.name})" if at is None else f"director reflection: last ran {stamp(at, now)}"


@dataclasses.dataclass
class RoleReach:
    """One role's sessions in the window, per offered skill [read, offered] sessions, per skill not offered its reads."""
    sessions: int = 0
    cells: dict[str, list[int]] = dataclasses.field(default_factory=dict)
    apart: dict[str, int] = dataclasses.field(default_factory=dict)


def skill_reach(now: dtm.datetime, unread: list[str]) -> list[str]:
    """The skill reach block (spec comms #report-skill-reach; its lines and rules: --help, report)."""
    from pi_sessions import session_reach, sessions_dir
    root = sessions_dir()
    since = now - dtm.timedelta(days=7)
    head = "skill reach (Pi sessions active in the last 7 days; per role: skill read/offered, sessions):"
    if not root.is_dir():
        return [f"skill reach: no Pi session (sessions {root}: none)"]
    roles: dict[str, RoleReach] = {}
    bad: list[str] = []
    for f in sorted(root.glob("*/*.jsonl")):
        try:
            if f.stat().st_mtime <= since.timestamp():
                continue   # last written before the window: no activity in it
            got = session_reach(f, since)
        except (OSError, ValueError) as e:
            bad.append(f"  unread: Pi session {f.relative_to(root)}: {e}")
            unread.append(f"Pi session {f.relative_to(root)}")
            continue
        if got is None:
            continue
        r = roles.setdefault(got.role, RoleReach())
        r.sessions += 1
        for s in got.offered:
            r.cells.setdefault(s, [0, 0])[1] += 1
        for s in got.read:
            if s in got.offered:
                r.cells[s][0] += 1
            else:
                r.apart[s] = r.apart.get(s, 0) + 1
    out = [head if roles else f"{head} none"]
    for role, r in sorted(roles.items()):
        n = r.sessions
        line = f"  {role} ({n} session{'s' if n != 1 else ''}): " + (
            ", ".join(f"{s} {rd}/{off}" for s, (rd, off) in sorted(r.cells.items())) or "none offered")
        out.append(line + ("; read, not offered: " + ", ".join(f"{s} {k}" for s, k in sorted(r.apart.items())) if r.apart else ""))
    return out + bad


class ReportSources:
    """The state dir's spend ledger and gate run trend, read once, and each repository's default-branch commits, read once."""
    LEDGER, TREND = "spend.jsonl", "check-runs.jsonl"

    def __init__(self, state: Path, unread: list[str]):
        self.unread, self.main = unread, {}
        self.repo_heads: dict[str, set[str]] = {}   # each open lane's repository: its lanes' PR commits
        self.ledger, self.ledger_why = self.load(state / self.LEDGER)
        self.trend, self.trend_why = self.load(state / self.TREND)
        if self.ledger:   # a cost neither dollars nor null (unknown) makes the line unreadable
            rows, bad = self.ledger
            odd = [i for i, d in rows if d.get("cost_usd", "") is not None and not self.dollars(d.get("cost_usd", ""))]
            self.ledger = [r for r in rows if r[0] not in odd], sorted(bad + odd)

    @staticmethod
    def dollars(c: object) -> bool:
        return isinstance(c, (int, float)) and not isinstance(c, bool)

    def load(self, path: Path):
        try:
            return numbered_jsonl(path), None
        except (OSError, UnicodeDecodeError) as e:
            self.unread.append(path.name)
            return None, str(e)

    def notes(self) -> list[str]:
        return [f"{n}: {len(r[1])} unparsable line{'s' if len(r[1]) > 1 else ''} ({', '.join(map(str, r[1]))})"
                for n, r in ((self.LEDGER, self.ledger), (self.TREND, self.trend)) if r and r[1]]

    def spend(self, name: str) -> str:
        if self.ledger_why:
            return f"  spend: unread: {self.LEDGER}: {self.ledger_why}"
        if self.ledger is None:
            return f"  spend: no spend recorded ({self.LEDGER}: none)"
        costs = [d.get("cost_usd") for _, d in self.ledger[0] if d.get("lane") == name]
        known = [c for c in costs if self.dollars(c)]
        if not costs:
            return f"  spend: none recorded for {name}"
        unknown = len(costs) - len(known)
        return (f"  spend: ${sum(known):.4f} over {len(known)} call{'s' if len(known) != 1 else ''} of known cost, "
                f"{unknown} call{'s' if unknown != 1 else ''} of unknown cost")

    def last_run(self, heads: set[str]) -> dict | None:
        """The latest gate run on HEADS: a full line, or one with no tier (written before the runners recorded one)."""
        runs = [(utc(d.get("start")) is not None, str(utc(d.get("start")) or ""), i, d)
                for i, d in (self.trend or ([], []))[0] if d.get("head") in heads and ("tier" not in d or d["tier"] == "full")]
        return max(runs, key=lambda r: r[:3])[3] if runs else None

    def main_heads(self, repo: object) -> set[str] | str:
        """The default branch's last 100 commits of repo, or why they are unread."""
        if not isinstance(repo, str) or not re.fullmatch(r"[\w.-]+/[\w.-]+", repo):
            return f"unread: the record needs repository owner/name (repository {repo!r})"
        if repo not in self.main:
            try:
                out = json.loads(gh(["api", f"repos/{repo}/commits?per_page=100"], f"check {repo} exists, and gh auth status"))
                self.main[repo] = {c["sha"] for c in out}
            except (Refuse, ValueError, KeyError, TypeError) as e:
                self.unread.append(f"GitHub ({repo} default branch)")
                self.main[repo] = f"unread: GitHub: {e}"
        return self.main[repo]

    def gate(self, pr: object, pr_heads: set[str] | None, repo: object, now) -> list[str]:
        if self.trend_why:
            return [f"  gate time: unread: {self.TREND}: {self.trend_why}"]
        if self.trend is None:
            return [f"  gate time: no gate run recorded ({self.TREND}: none)"]

        def run(who: str, d: dict | None, none: str) -> str:
            if d is None:
                return f"  gate time: {who} none: {none}"
            steps = d.get("steps")
            n = len(steps) if isinstance(steps, list) else steps
            return (f"  gate time: {who} {d.get('total_s')}s exit {d.get('exit')}, {n} steps, head {str(d.get('head'))[:12]}, "
                    f"started {stamp(d.get('start'), now)}")
        if pr is None:
            lane = "  gate time: lane none: no pr"
        elif pr_heads is None:
            lane = f"  gate time: lane unread: GitHub (PR #{pr})"
        else:
            lane = run("lane", self.last_run(pr_heads), f"no full gate run on a commit of PR #{pr}")
        main = self.main_heads(repo)
        if isinstance(main, str):
            return [lane, f"  gate time: main {main}"]
        return [lane, run("main", self.last_run(main), f"no full gate run on a commit of {repo}'s default branch")]

    def budget_text(self, repo: str) -> str | None:
        """gate-budget.toml on repo's default branch (None: no such file); Refuse when GitHub cannot say."""
        try:
            return gh(["api", f"repos/{repo}/contents/{BUDGET}", "-H", "Accept: application/vnd.github.raw"],
                      f"check {repo} exists, and gh auth status")
        except Refuse as e:
            if "HTTP 404" in str(e):
                return None
            raise

    def budgets(self, now: object) -> list[str]:
        """Per open lane's repository, its latest passed full gate run on a commit of its default branch or of
        its lanes' PRs, against its gate-time budget (spec comms #report-field-gate-time)."""
        out: list[str] = []
        trend = self.trend
        for repo in sorted(self.repo_heads):
            head = f"gate budget {repo}:"
            if self.trend_why:
                out.append(f"{head} unread: {self.TREND}: {self.trend_why}"); continue
            if trend is None:
                out.append(f"{head} no gate run recorded ({self.TREND}: none)"); continue
            main = self.main_heads(repo)
            if isinstance(main, str):
                out.append(f"{head} {main}"); continue
            runs = passed_full(trend[0], main | self.repo_heads[repo])
            if not runs:
                out.append(f"{head} no passed full gate run on a commit of {repo}'s default branch or its open lanes' PRs"); continue
            try:
                text = self.budget_text(repo)
                budget, why = budget_parse(text)
                if text is not None and budget is None:
                    self.unread.append(f"{BUDGET} ({repo})")
            except Refuse as e:
                self.unread.append(f"GitHub ({repo} {BUDGET})")
                budget, why = None, f"unread: GitHub: {e}"
            out += [f"{head} the latest passed full gate run against {BUDGET} on {repo}'s default branch",
                    *budget_lines(runs[-1], runs[:-1], budget, why, now, "  ")]
        return out


def report_lane(rec_path: Path, agents: list[dict] | None, herdr_why: str | None, now, unread: list[str], queue: list,
                src: ReportSources) -> list[str]:
    import tomllib
    name = rec_path.stem
    try:
        rec = tomllib.loads(rec_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
        unread.append(f"record {rec_path.name}")
        return [f"lane {name}", f"  unread: record {rec_path.name}: {e}"]
    repo = rec.get("repository")
    if isinstance(repo, str) and re.fullmatch(r"[\w.-]+/[\w.-]+", repo):
        src.repo_heads.setdefault(repo, set())
    out = [f"lane {name}: issue {rec.get('issue', '(no issue)')} {repo or '(no repository)'} {json.dumps(rec.get('goal', ''))}",
           f"  started: {stamp(rec.get('started_at'), now)}"]
    check_waits, pr_heads = [], None
    pr = rec.get("pr")
    if pr is None:
        out.append("  pr: none")
    elif not isinstance(pr, int) or isinstance(pr, bool) or not isinstance(repo, str) or not re.fullmatch(r"[\w.-]+/[\w.-]+", repo):
        unread.append(f"GitHub ({name})")
        out.append(f"  pr: {pr!r} unread: GitHub: the record needs pr a number and repository owner/name (repository {repo!r})")
    else:
        try:
            d = pr_view(pr, "state,isDraft,headRefOid,statusCheckRollup,commits", repo)
            rollup = [c for c in d["statusCheckRollup"] or [] if isinstance(c, dict)]
            head = str(d["headRefOid"])[:12]
            out.append(f"  pr: #{pr} {d['state']} {'draft' if d['isDraft'] else 'ready'} head {head} checks: {check_results(rollup)}")
            check_waits = [f"  waits: check {c} on head {head}" for c in merge_ask.bad_checks(cast("list[dict[str, object]]", rollup))[1]]
            pr_heads = {c["oid"] for c in d["commits"] or [] if isinstance(c, dict) and "oid" in c}
            src.repo_heads[repo] |= pr_heads
        except (Refuse, KeyError, TypeError, AttributeError) as e:
            unread.append(f"GitHub ({name})")
            out.append(f"  pr: #{pr} unread: GitHub: {e}")
    sup = rec.get("supervisor")
    workers = []
    if agents is None:
        out.append(f"  running: unread: Herdr: {herdr_why}")
    elif not isinstance(sup, str) or ":" not in sup:
        out.append(f"  running: the record's supervisor {sup!r} is no pane id")
    else:
        ws = sup.split(":", 1)[0]
        mine = sorted((a for a in agents if a.get("workspace_id") == ws), key=lambda a: str(a.get("pane_id")))
        for a in mine:
            is_sup = a.get("pane_id") == sup
            out.append(f"  running: {a.get('pane_id')} {a.get('name') or '(no name)'} {a.get('agent_status')}" + (" (supervisor)" if is_sup else ""))
            if not is_sup and a.get("agent_status") == RUNNING:
                workers.append(f"  waits: worker {a.get('name') or '(no name)'} {a.get('pane_id')} {RUNNING}")
        if not any(a.get("pane_id") == sup for a in mine):
            out.append(f"  running: supervisor pane {sup} not in herdr agent list")
    out.append(f"  waits: waiting_on {json.dumps(rec.get('waiting_on', ''))}, last hand-off {stamp(rec.get('last_handoff_at'), now)}")
    out += workers
    log, notes = rec_path.with_name(f"{name}.handoffs.jsonl"), []
    rounds = "  review rounds: 0"
    if log.exists():
        try:
            lines, bad = read_log(log)
            rounds = f"  review rounds: {sum(1 for d in lines if d.get('kind') == 'review')}"
            pending = pending_gates(lines)
            out += [f"  waits: owner gate {g} asked {stamp(at, now)}" for g, at in pending]
            queue += [(name, g, at) for g, at in pending]
            if bad:
                notes.append(f"  log {log.name}: {len(bad)} unparsable line{'s' if len(bad) > 1 else ''} ({', '.join(map(str, bad))})")
        except (OSError, UnicodeDecodeError) as e:
            unread.append(f"log {log.name}")
            notes.append(f"  unread: log {log.name}: {e}")
            rounds = f"  review rounds: unread (log {log.name})"
    else:
        notes.append(f"  log {log.name}: none")
    numbers = [rounds, src.spend(name), *src.gate(pr, pr_heads, repo, now)]
    return out + check_waits + numbers + notes


def cmd_report(args: list[str]) -> int:
    import datetime
    if args:
        raise Refuse(f"usage: octo-feather-lane report (takes no arguments; got {' '.join(args)})")
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    lanes = lanes_dir()
    print(f"report at {now:%Y-%m-%dT%H:%M:%SZ} ({lanes})")
    unread: list[str] = []
    headline, caught = owner_caught(lanes.parent, now, unread)
    print(headline)
    try:
        agents, herdr_why = herdr_agents(), None
    except Refuse as e:
        agents, herdr_why = None, str(e)
        unread.append("Herdr")
    try:
        records = sorted(lanes.glob("*.toml"))
    except OSError as e:
        records = []
        unread.append(f"lanes {lanes}")
        print(f"unread: lanes {lanes}: {e}")
    if not records:
        print("no open lane")
    queue: list = []
    src = ReportSources(lanes.parent, unread)
    for r in records:
        print("\n".join(report_lane(r, agents, herdr_why, now, unread, queue, src)))
    for line in src.budgets(now):
        print(line)
    queue.sort(key=lambda q: (utc(q[2]) is None, utc(q[2]) or now, q[0], q[1]))   # oldest first, unparsable times last
    print("owner queue:" if queue else "owner queue: none")
    for name, g, at in queue:
        print(f"  lane {name} gate {g} asked {stamp(at, now)}")
    print("\n".join(caught))
    print(director_reflection(lanes.parent, now, unread))
    print("\n".join(skill_reach(now, unread)))
    for n in src.notes():
        print(n)
    print(f"unread: {', '.join(unread) or 'none'}")
    return 0


# This module's chunks of octo-feather-lane --help, joined in lane_cli.HELP_ORDER by lane_cli.help_doc.
HELP = {
    "spend": """\
  octo-feather-lane spend          the spend ledger's totals, then the OpenRouter reconcile
  octo-feather-lane spend record [--lane NAME]
                                   append the model calls given as JSON lines on stdin to the ledger

`spend` (spec spend) reads the ledger, $(octo-feather-state)/spend.jsonl: append-only JSON lines, one per
model call, {at, lane, purpose, model, input_tokens, output_tokens, cost_usd}. It prints totals by UTC day,
lane, purpose, lane and purpose (each role under its lane) and model: dollars, calls, tokens, and calls with
unknown cost (cost_usd null) counted apart (spec spend#rule-cost). Then the reconcile, per window: OpenRouter's usage for the key, the ledger's dollars
on openrouter/* models over the same window, and the gap = OpenRouter minus ledger (spec spend#rule-gap). The
windows are OpenRouter's key usage windows (GET /api/v1/key usage_daily, usage_weekly, usage_monthly,
openrouter.ai/openapi.json): today = the current UTC day from 00:00Z, this week = the current UTC week starting
Monday 00:00Z, this month = the current UTC calendar month from day 1 00:00Z. The key is OPENROUTER_API_KEY,
else `openrouter.key` in ~/.pi/agent/auth.json (a `!command` key runs the command, as Pi does); it is never
printed: `curl` makes the call, the key on its stdin config, never in argv. No key, or an
unreachable or failing endpoint, prints the reason in the reconcile section; the totals still print, exit 0.
No budget: nothing is blocked (spec spend#rule-no-budget).

`spend record` is the ledger's one writer: each call path appends through it. Each stdin line is a JSON object:
model (provider/id, e.g. openrouter/qwen/qwen3-8b) and purpose (e.g. bench, judge, a role name), strings;
input_tokens and output_tokens, integers >= 0; cost_usd, the provider's reported cost in USD, or null or absent
when unreported; at, optional ISO 8601 time of the call (default now, UTC). The lane is --lane NAME (for callers
that lost the HERDR_* env, e.g. in a sandbox), else the lane record in $(octo-feather-state)/lanes/*.toml whose
`supervisor` pane is in the caller's Herdr space (HERDR_WORKSPACE_ID, e.g. w37 for supervisor "w37:p2", else
OCTO_FEATHER_SPEND_SPACE: scripts/pi-role --help, Headless), else
null: no lane (spec spend#rule-lane). Records only grow (spec spend#rule-append): all lines of one call are
appended in one locked write, so concurrent writers never interleave. It never fails its caller: a line it
cannot read, or a ledger it cannot write, prints one stderr line naming the unrecorded spend, and it exits 0
(spec spend#rule-write-fails).

""",
    "report": """\
  octo-feather-lane report         every open lane of this session, then the owner queue and owner-caught

What `report` reads and shows, that it writes nothing, and how it treats a source it cannot read:
docs/specs/comms.spec.html#factory-report. Its output, `report at <now> (<lanes dir>)`, then the headline (spec comms
#report-owner-caught):

  owner-caught (headline, director.handoffs.jsonl): <N> in the last 7 days, <M> in the 7 days before
                                                 by each finding's at; `; <K> with no readable at, not counted`
                                                 when some have none; `log none` with no log, `unread` when unreadable

then per lane:

  lane <record name>: issue <issue> <repository> "<goal>"
    started: <started_at>                        its age is the lane's wall time
    pr: #N <state> <draft|ready> head <12 hex> checks: <count> <result>, ...   (`pr: none` with no pr)
    running: <pane> <name> <Herdr state>, one line per Herdr agent whose workspace is the supervisor
             pane's prefix; `(supervisor)` marks the supervisor's pane, a supervisor pane not listed is said
    waits: waiting_on "<value>", last hand-off <last_handoff_at>
    waits: worker <name> <pane> working          per agent other than the supervisor in state working
    waits: owner gate <gate> asked <at>
    waits: check <name> <status> on head <12 hex>
    review rounds: <N>                           the hand-off log's `"kind": "review"` lines
    spend: $<dollars> over <N> calls of known cost, <M> calls of unknown cost
                                                 spend.jsonl lines whose lane is the record name
                                                 (cost_usd null: unknown; neither a number nor null:
                                                 unparsable); `none recorded for <lane>`,
                                                 `no spend recorded (spend.jsonl: none)` with no ledger
    gate time: lane <total_s>s exit <exit>, <N> steps, head <12 hex>, started <start>
    gate time: main <total_s>s exit <exit>, <N> steps, head <12 hex>, started <start>
                                                 the check-runs.jsonl line with the latest start whose
                                                 tier is full (a subset run, just fast's, never stands in;
                                                 a line with no tier, written before the runners recorded
                                                 one, counts as today) and whose
                                                 head is a commit of the PR (`gh pr view --json commits`),
                                                 then of the default branch's last 100 commits (one
                                                 `gh api repos/<repository>/commits` per repository);
                                                 `<lane|main> none: <why>` with no such run

After the lanes:

  gate budget <owner/name>: the latest passed full gate run against gate-budget.toml on <owner/name>'s default branch
    full gate: <s>s, head <12 hex>, started <start>: OVER BUDGET by <s>s (budget <s>s)
                                                 or `within budget, <s>s to spare (budget <s>s)`, `no budget (<why>)`
    growth: <+x.y%> over the trend's median <s>s (the <N> passed full runs before it); set share <p>%: GROWN
                                                 or `within`; `no set share (<why>)` with no budget
    trend: <s>s <12 hex> <start>, ... (passed full runs, oldest first)
    slowest: <name> <s>s, ...                    the latest run's 5 slowest items
                                                 one block per open lane's repository (spec comms
                                                 #report-field-gate-time): check-runs.jsonl lines with tier full
                                                 and exit 0 (each runner's trend writer sets tier: the kit's
                                                 tests/gate/conftest.py and its copy templates/python/tests/
                                                 conftest.py for pytest, templates/typescript/tests/trend-
                                                 reporter.ts for Vitest; a line without it is no full run
                                                 here) whose head is a commit of
                                                 the default branch (the same 100) or of its open lanes' PRs;
                                                 the latest is the full gate time, trend_runs before it the
                                                 trend; `gate budget <repo>: no passed full gate run ...` or
                                                 `unread: ...` instead. Shown only: no gate reads it
  owner queue:                                   (`owner queue: none` with none pending)
    lane <record name> gate <gate> asked <at>    oldest first
  owner-caught (director.handoffs.jsonl):        (`: none` with no such finding; `owner-caught: log ...: none` with no log)
    class <class>: count <N>, last seen <at>     by class name
  director reflection: last ran <at>             the director log's latest reflection line (`never ran (<log>)`
                                                 with none; `never ran (<log>: none)` with no log)
  skill reach (Pi sessions active in the last 7 days; per role: skill read/offered, sessions):
    <role> (<N> sessions): <skill> <read>/<offered>, ...; read, not offered: <skill> <sessions>, ...
                                                 spec comms #report-skill-reach, one line per role, by name:
                                                 the Pi session files (PI_CODING_AGENT_DIR, else ~/.pi/agent,
                                                 then sessions/*/*.jsonl) with a line timestamped in the last 7
                                                 days, whenever they started (a file last written before that is
                                                 not opened). Role: the first `# ` heading of the system prompt's
                                                 appended role prompt (`no role` without one). Offered: its
                                                 <available_skills> names, whenever that prompt was written.
                                                 Read: a read or bash call (top level, or one a codemode batch
                                                 dispatched) whose result is timestamped in the last 7 days and
                                                 did not fail (top level: its result's isError not true; in a
                                                 batch: the call's status ok in the result's nestedCalls, as Pi
                                                 records them) and whose own arguments open <folder>/SKILL.md:
                                                 the read tool's path; in bash (shell words; # opens a comment
                                                 only at a word's start, as in bash), a file operand of
                                                 cat, head, tail, sed, less, more, bat or nl, or a < input (not
                                                 sed's script text, an option's value, a > target, a heredoc
                                                 body, sed -i). A codemode batch's source is never read: a batch
                                                 with no nestedCalls record counts no read. A path in text, a
                                                 pattern, a grep, a write or edit is no read (skills: cannot tell), and a computed
                                                 path ($var, ${...}, a glob) is not resolved, so not counted:
                                                 the count may miss reads, never makes one up. A folder an
                                                 offered skill's location names counts as
                                                 that skill (a linked skill by its offered name), any other by
                                                 the folder. A session counts once per skill; a read of a skill
                                                 the session was not offered counts apart. `... none` with no
                                                 session; `skill reach: no Pi session (sessions <dir>: none)`
                                                 with no folder; an unreadable file or one with no session line
                                                 first: `  unread: Pi session <dir>/<file>: <reason>`
  spend.jsonl: <N> unparsable line(s) (<line numbers>)       when it has any; likewise check-runs.jsonl

gate-budget.toml, a repository's gate-time budget at its root (read from its default branch, `gh api
repos/<repository>/contents/gate-budget.toml`; by merge-ask at the PR head), kept by the factory like any repo
policy: TOML, read with the standard library, a file of its own so a budget change changes no gate configuration
(octo-feather-gate config) and no qc contract. Keys: budget_seconds (a number > 0), growth_share (a number >= 0:
GROWN when the run is more than that share over the trend's median), trend_runs (an integer >= 1: that many passed
full runs before the latest make the trend; 5 shown with no file); optional test_cpu_seconds (a number > 0: the
per-test CPU budget the gate's runner reads, tests/gate/conftest.py; not read here); optional heavy_items,
heavy_slots, eval_slots, slot_grace_seconds, slot_bound_seconds (the box's run slots: octo-feather-slot --help;
not read here); optional fast_workers and fast_runs (the fast tier's worker count and how many fast-tier
runs run at once on the box: tests/gate/heavy_slot.py; not read here).
Anything else is `unread: gate-budget.toml (<repo>)`.

Every time prints as its UTC instant and `(<age> ago)` at the report's instant. A source it cannot
read prints as `unread: <source>: <reason>` where its facts would be; a log's unparsable lines are
counted and named by line number. The last line is `unread: none` or `unread: <source>, ...`.
Exit 0; 1 on any argument.

""",
}
