#!/usr/bin/env python3
"""eval_grading: the eval runner's grading, which scripts/octo-feather-qa imports (#1088, #1087).

The rules it implements and every byte it prints or writes: scripts/octo-feather-qa --help, and the
eval-cases skill's schema (.agents/skills/eval-cases/references/schema.md, "schema" below).

Interface (__all__):
  plan(suite, case, facts, repo, *, kit) -> Plan   a case run's facts resolved, its bounds and
      setup; Plan.watch_args the `--watch` argv form, Plan.parse its reverse
  watch(plan, cmd, *, where, out) -> int   the in-sandbox watcher and its stop rule: runs CMD in
      the case repo with the environment and private dir WHERE gives, Pi's events and its own
      (qa_fs, qa_branch, qa_watch) written to OUT; never changes the process cwd or os.environ
  grade(plan, watched, sandbox, *, model) -> Run   every fact and the run's verdict
  record(slot, run, ...) -> (result, lines)   one run's artifacts written, the lines to print
  combine(case_dir, done, *, runs, baseline) -> (result, lines)   a case over its runs and kits
  analysis(cases) -> (analysis, lines)   the deterministic flags
  reanalysis(run_dir) -> lines, evidence(run_dir) -> str   --analyze, --analyze --evidence
  review(run_dir, key, verdict, note) -> lines   --review, show or record
  verdict(pins, *, cwd, qa_dir) -> Judged   --verdict
  UsageError   a stored dir or argument refused (the command exits 64)
Invariants: record and combine are the only writers of a run's and a case's artifacts (the
command writes the run's summary.json; review appends a verdict to the reviews dir); every reader
of a stored run is here; nothing here prints or exits.

How it is found: it sits beside the command, in scripts/. Run as a command, Python puts the
script's own directory (symlinks resolved) first on sys.path, as `from handoff_log import
read_log` relies on; inside the qc sandbox the kit is bound read-only at its own path, so
`octo-feather-qa --watch` finds it the same way (its bytecode write then fails, silently). A
script or recipe that loads octo-feather-qa by path gets it by the command's own sys.path line,
at its import. Python stdlib only, as every kit script.
"""

from __future__ import annotations

import hashlib
import importlib.machinery
import importlib.util
import itertools
import json
import os
import queue
import re
import shutil
import signal
import statistics
import subprocess
import tempfile
import threading
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any, Protocol, cast

if TYPE_CHECKING:
    from types import ModuleType

__all__ = [
    "DEFAULT_MAX_CALLS",
    "DEFAULT_TIMEOUT",
    "Judged",
    "Plan",
    "Result",
    "Run",
    "Slot",
    "UsageError",
    "Where",
    "analysis",
    "check_evals",
    "combine",
    "evidence",
    "export",
    "grade",
    "plan",
    "reanalysis",
    "record",
    "review",
    "safe_json",
    "verdict",
    "watch",
]

KIT = Path(__file__).resolve().parent.parent
DEFAULT_MAX_CALLS, DEFAULT_TIMEOUT = 12, 600
# kit_contract_edit's paths, repo-root relative (rule: schema, Before targets).
CONTRACT_PATH = re.compile(r"^(?:agents/[^/]+\.md|\.agents/skills/.+|\.skillfile/patches/.+)$")
Fact = dict[
    str, Any
]  # a parsed JSON object (a fact, an event, a record): its values as JSON left them
Result = dict[str, Any]  # a run's or a case's result, as result.json and summary.json hold it
Lines = Sequence[str] | Sequence[bytes]  # a transcript's lines: Pi's JSON events and the watcher's
Call = tuple[str, Fact]  # a tool call: its tool name and arguments
Last = (
    tuple[Any, str | None] | None
)  # the watcher's stop reason and the last assistant message's text
Status = tuple[str, str]  # a fact's status (pass, fail or open) and its evidence text
Json = dict[str, Any] | list[Any] | str | int | float | bool | None  # a parsed JSON value


class UsageError(Exception):
    """A stored dir or an argument the command refuses: its message, the command's exit 64."""


# ---- facts from the transcript --------------------------------------------------------------


def safe_json(line: str | bytes) -> Json:
    """LINE as JSON, None when it is not JSON."""
    try:
        return json.loads(line)
    except ValueError:
        return None


def tool_calls(lines: Lines) -> list[Call]:
    """(toolName, args) of every tool_execution_start event, in order."""
    calls: list[Call] = []
    for line in lines:
        ev = safe_json(line)
        if isinstance(ev, dict) and ev.get("type") == "tool_execution_start":
            calls.append(
                (
                    str(ev.get("toolName", "")),
                    ev["args"] if isinstance(ev.get("args"), dict) else {},
                )
            )
    return calls


# attempt_blocked: the qc sandbox's own attempt record (scripts/octo-feather-qc-sandbox), one {kind,
# attempt, refused, what, result} per line (what it reads:
# .agents/skills/eval-cases/references/schema.md, Attempt record). Live, in the sandbox: the
# recorder's read-only view as it grows; after the run: the sandbox's post record (the recorder's
# line; none: attempts_error, read as no record; what that does: schema.md, Attempt record).
def attempt_record(path: str) -> list[Fact]:
    """The record's lines so far (the watcher, in the sandbox: PATH its OCTO_FEATHER_QC_ATTEMPTS);
    [] when none."""
    out: list[Fact] = []
    try:
        with Path(path).open() as f:
            for line in f:
                r = safe_json(line)
                if isinstance(r, dict):
                    out.append(r)
    except OSError:
        pass
    return out


def show(call: Call) -> str:
    n, a = call
    return f"{n} {str(a.get('path') or a.get('command') or '')[:120]}".strip()


# Pi's truncation notices (rule: schema, Skill load).
TRUNCATED = re.compile(
    r"\[(?:Showing lines \d+-\d+ of \d+|\d+ more lines in file\.|Output truncated\.)"
)
_SKILL_TEXT: dict[str, str | None] = {}


def norm(text: str) -> str:
    return text.replace("\r\n", "\n")


def skill_text(path: str) -> str | None:
    """The SKILL.md at PATH (the kit under test's or the case repo's), normalized (rule: schema,
    Skill load)."""
    if path not in _SKILL_TEXT:
        try:
            _SKILL_TEXT[path] = norm(Path(path).read_text(encoding="utf-8")).rstrip("\n")
        except OSError:
            _SKILL_TEXT[path] = None
    return _SKILL_TEXT[path]


def content_text(result: object) -> str:
    """The text parts of a tool result's content, joined."""
    r = cast("Fact", result) if isinstance(result, dict) else {}
    parts = cast("list[object]", r.get("content")) if isinstance(r.get("content"), list) else []
    items = [cast("Fact", c) for c in parts if isinstance(c, dict)]
    return "".join(str(c.get("text", "")) for c in items if c.get("type") == "text")


def result_texts(lines: Lines) -> list[str | None]:
    """The text each tool call put in the agent's context, in start order: its tool_execution_end
    content text, None while it has none or when Pi truncated it (rule: schema, Skill load)."""
    order: list[str] = []
    texts: dict[str, str | None] = {}
    for line in lines:
        e = safe_json(line)
        if not isinstance(e, dict):
            continue
        if e.get("type") == "tool_execution_start":
            order.append(str(e.get("toolCallId", "")))
        elif e.get("type") == "tool_execution_end":
            r = cast("Fact", e["result"]) if isinstance(e.get("result"), dict) else {}
            sc = (
                cast("Fact", r["structuredContent"])
                if isinstance(r.get("structuredContent"), dict)
                else {}
            )
            text = content_text(r)
            texts[str(e.get("toolCallId", ""))] = (
                None if sc.get("truncated") or TRUNCATED.search(text) else norm(text)
            )
    return [texts.get(i) for i in order]


def loads(fact: Fact, text: str | None) -> bool:
    """skill_read on one tool result's TEXT (rule: schema, Skill load): the fact's SKILL.md text
    (skill_source), found whole in TEXT."""
    want = fact["_skill_text"] if "_skill_text" in fact else skill_text(fact.get("_skill_md", ""))
    return bool(want) and text is not None and want in text


def fs_marks(lines: Lines) -> dict[str, int]:
    """{target: index of the first tool call after which the watcher saw it}: test_write, edit,
    git_commit, git_push, gh_call, kit_contract_edit, from its qa_fs events (rule: schema, Before
    targets)."""
    order: dict[str, int] = {}
    marks: dict[str, int] = {}
    for line in lines:
        e = safe_json(line)
        if not isinstance(e, dict):
            continue
        if e.get("type") == "tool_execution_start":
            order.setdefault(str(e.get("toolCallId", "")), len(order))
        elif e.get("type") == "qa_fs" and str(e.get("toolCallId")) in order:
            for m in e.get("marks", []):
                marks.setdefault(m, order[str(e["toolCallId"])])
    return marks


@dataclass(frozen=True)
class Seen:
    """A run as seen so far, what each fact is judged on: its tool calls, its event lines (Pi's and
    the watcher's), the sandbox's attempt record (None: none whole), the watcher's stop and the last
    message (Last), and the first tool call index of each filesystem target (fs_marks)."""

    calls: list[Call]
    lines: Lines
    record: list[Fact] | None
    last: Last = None
    marks: dict[str, int] = field(default_factory=dict)


JSON_FENCE = re.compile(r"^[ \t]*```[ \t]*json[ \t]*$", re.MULTILINE | re.IGNORECASE)
FENCE_END = re.compile(r"^[ \t]*```[ \t]*$", re.MULTILINE)


def final_message(head: str, last: Last, *, final: bool, unread: str) -> tuple[str | None, str]:
    """(status, text): the final assistant message's text, status None; open before the run's end
    (UNREAD what the open fact says), fail when the run stopped before it or has none. LAST: (stop,
    text), the watcher's stop reason and the last assistant message's text (None: no message)."""
    if not final:
        return "open", f"{head}: {unread}"
    stop, text = last or (None, None)
    if stop not in (None, "exit"):
        return "fail", f"{head}: run stopped ({stop}) before its final message"
    if text is None:
        return "fail", f"{head}: no final assistant message"
    return None, text


def json_block(text: str) -> tuple[Fact, str | None]:
    """(the object, None) of TEXT's one ```json block (schema, Final JSON), else ({}, why not)."""
    opens = list(JSON_FENCE.finditer(text))
    if len(opens) != 1:
        return {}, f"final message holds {len(opens)} ```json blocks, want exactly 1"
    end = FENCE_END.search(text, opens[0].end())
    if end is None:
        return {}, "the ```json block is never closed"
    try:
        obj = json.loads(text[opens[0].end() : end.start()])
    except ValueError as e:
        return {}, f"invalid JSON in the ```json block ({e})"
    return (
        (cast("Fact", obj), None)
        if isinstance(obj, dict)
        else ({}, "the ```json block is not an object")
    )


def final_json(head: str, last: Last, *, final: bool) -> tuple[str | None, str, Fact]:
    """(status, text, obj): the block Final JSON reads (schema, Final JSON) as an object, status
    None when there is one."""
    st, text = final_message(head, last, final=final, unread="read from the final message only")
    if st:
        return st, text, {}
    obj, why = json_block(text)
    return ("fail", f"{head}: {why}", {}) if why else (None, "", obj)


def judge_declared(fact: Fact, seen: Seen, *, final: bool) -> Status:
    """declared (schema, Final JSON)."""
    f, labels = fact["field"], fact["in"]
    head = f"declared {f}"
    st, txt, obj = final_json(head, seen.last, final=final)
    if st:
        return st, txt
    if f not in obj:
        return "fail", f"{head}: no top-level {f!r} in the ```json block"
    if not isinstance(obj[f], str) or obj[f] not in labels:
        return "fail", f"{head}: {json.dumps(obj[f])[:80]} is not one of {json.dumps(labels)}"
    return "pass", f"{head}: {json.dumps(obj[f])}, one of {json.dumps(labels)}"


def judge_includes(fact: Fact, seen: Seen, *, final: bool) -> Status:
    """declared_includes (schema, Final JSON)."""
    f, items = fact["field"], fact["items"]
    head = f"declared_includes {f}"
    st, txt, obj = final_json(head, seen.last, final=final)
    if st:
        return st, txt
    got = obj.get(f)
    if not isinstance(got, list):
        return (
            "fail",
            (
                f"{head}: top-level {f!r} is "
                f"{json.dumps(got)[:80] if f in obj else 'missing'}, want a list"
            ),
        )
    entries = [cast("Fact", x) for x in cast("list[object]", got) if isinstance(x, dict)]

    def has(it: Fact) -> bool:
        return any(all(k in x and x[k] == v for k, v in it.items()) for x in entries)

    missing = [it for it in items if not has(it)]
    if missing:
        return (
            "fail",
            (
                f"{head}: no entry with {'; '.join(json.dumps(m) for m in missing)} in "
                f"{json.dumps(got)[:300]}"
            ),
        )
    return "pass", f"{head}: holds {'; '.join(json.dumps(it) for it in items)}"


def holds(line: Fact, item: Fact) -> bool:
    return all(
        v in line.get(k, ()) if isinstance(line.get(k), list) else line.get(k) == v
        for k, v in item.items()
    )


def field_lines(f: str, text: str) -> tuple[list[Fact], Fact, str | None]:
    """(lines, record, None): the final message TEXT's field F lines, parsed by `octo-feather-lane
    fields` (one parser, verdict's; form and scope: .agents/skills/code-review/SKILL.md step 4,
    Report fields), and for Check and Owner its record ({lines, none, errors}); else ([], {}, why
    not well formed)."""
    p = subprocess.run(
        [str(KIT / "scripts" / "octo-feather-lane"), "fields", "-"],
        input=text,
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        got = json.loads(p.stdout)
    except ValueError:
        return [], {}, f"octo-feather-lane fields exited {p.returncode}: {p.stderr.strip()[:200]}"
    if f in ("Check", "Owner"):
        rec = cast("Fact", got[f])
        return (
            (rec["lines"], rec, None) if not rec["errors"] else ([], {}, "; ".join(rec["errors"]))
        )
    lines: list[Fact] = [{"text": v} for v in got["fields"].get(f, []) if v]
    return lines, {}, None if lines else f"no column-0 `{f}:` line with a value outside code blocks"


def lines_hold(fact: Fact, head: str, lines: list[Fact], rec: Fact) -> Status:
    """A field_lines fact's none, includes and every over its well formed LINES (schema, Field
    lines)."""
    f = fact["field"]

    def show_(ls: list[Fact]) -> str:
        return json.dumps(ls)[:300]

    if fact.get("none"):
        if not rec["none"]:
            return "fail", f"{head}: {len(lines)} {f} line(s) {show_(lines)}, want `{f}s: none`"
        return "pass", f"{head}: `{f}s: none`"
    missing = [it for it in fact.get("includes", []) if not any(holds(ln, it) for ln in lines)]
    if missing:
        return (
            "fail",
            f"{head}: no line with {'; '.join(json.dumps(m) for m in missing)} in {show_(lines)}",
        )
    every: Fact = fact.get("every", {})
    off = [
        ln
        for ln in lines
        if not all(
            all(x in v for x in ln.get(k, [])) if isinstance(ln.get(k), list) else ln.get(k) in v
            for k, v in every.items()
        )
    ]
    if off:
        return "fail", f"{head}: {show_(off)} outside {json.dumps(every)}"
    said = (
        f"`{f}s: none`"
        if f in ("Check", "Owner") and not lines
        else f"{len(lines)} line(s) {show_(lines)}"
    )
    return "pass", (
        f"{head}: {said}"
        + (
            f"; holds {'; '.join(json.dumps(i) for i in fact['includes'])}"
            if fact.get("includes")
            else ""
        )
        + (f"; every line in {json.dumps(every)}" if every else "")
    )


def judge_fields(fact: Fact, seen: Seen, *, final: bool) -> Status:
    """The final message's field F (schema: .agents/skills/eval-cases/references/schema.md, Field
    lines): present and well formed, then none, includes and every."""
    head = f"field_lines {fact['field']}"
    st, text = final_message(head, seen.last, final=final, unread="read once pi ends")
    if st:
        return st, text
    lines, rec, why = field_lines(fact["field"], text)
    return ("fail", f"{head}: {why}") if why else lines_hold(fact, head, lines, rec)


def under(path: str, p: str) -> bool:
    return path.startswith(p) if p.endswith("/") else path == p


def judge_branch(fact: Fact, seen: Seen, *, final: bool) -> Status:
    """branch_paths (schema, Branch paths), read from the watcher's qa_branch event."""
    head = "branch_paths"
    if not final:
        return "open", f"{head}: read once pi ends"
    stop = (seen.last or (None, None))[0]
    if stop not in (None, "exit"):
        return "fail", f"{head}: run stopped ({stop}) before it ended"
    events = (safe_json(ln) for ln in reversed(seen.lines))
    ev = next((e for e in events if isinstance(e, dict) and e.get("type") == "qa_branch"), None)
    if ev is None:
        return "fail", f"{head}: no qa_branch record from the watcher"
    paths: list[str] = ev["paths"]
    hit = [p for p in paths if any(under(p, u) for u in fact.get("untouched", []))]
    if hit:
        return (
            "fail",
            f"{head}: changed {', '.join(hit)} (untouched: {', '.join(fact['untouched'])})",
        )
    lack = [t for t in fact.get("touched", []) if not any(under(p, t) for p in paths)]
    if lack:
        return (
            "fail",
            (
                f"{head}: nothing changed under {', '.join(lack)} (changed: "
                f"{', '.join(paths) or 'nothing'})"
            ),
        )
    return "pass", (
        f"{head}: changed {', '.join(paths) or 'nothing'}"
        + (f"; none under {', '.join(fact['untouched'])}" if fact.get("untouched") else "")
        + (f"; each of {', '.join(fact['touched'])} changed" if fact.get("touched") else "")
    )


def target_name(before: object) -> str:
    """A before target's name, as marks and evidence name it: the target, or `edit_under P...`
    (schema, Before targets)."""
    if isinstance(before, dict):
        return " ".join(
            [
                "edit_under",
                *(
                    str(p)
                    for p in cast("list[object]", cast("Fact", before).get("edit_under") or [])
                ),
            ]
        )
    return str(before)


def under_targets(facts: list[Fact]) -> dict[str, list[str]]:
    """{name: paths} of every edit_under target the facts name."""
    return {
        target_name(f["before"]): [str(p) for p in f["before"]["edit_under"]]
        for f in facts
        if isinstance(f.get("before"), dict)
    }


def under_marks(old: Fact, new: Fact, targets: dict[str, list[str]]) -> list[str]:
    """The edit_under targets reached between two snapshots: a file under one of a target's paths
    created or changed."""
    a, b = cast("Fact", old["files"]), cast("Fact", new["files"])
    hit = [f for f, h in b.items() if f not in a or a[f] != h]
    return [name for name, ps in targets.items() if any(under(f, p) for f in hit for p in ps)]


def reached(b: str, seen: Seen, *, final: bool) -> int | None:
    """The index of the first tool call that reached before target B, len(calls) for the final
    message (never a mark), None while it is not reached (rule: schema, Before targets)."""
    n = len(seen.calls)
    stop, text = seen.last or (None, None)
    if b == "final_message":
        return n if final and stop in (None, "exit") and text is not None else None
    w = seen.marks.get(b)
    return w if w is not None and w < n else None


def at(seen: Seen, i: int) -> str:
    """Tool call I as evidence names it."""
    return f"tool call {i + 1} of {len(seen.calls)} ({show(seen.calls[i])})"


def judge_tool_before(fact: Fact, seen: Seen, *, final: bool) -> Status:
    """tool_called_before N T (schema, Facts): a call to one of N started before the first tool call
    that reached T."""
    names, b = [str(x) for x in fact["tools"]], target_name(fact["before"])
    head = f"tool_called_before {' | '.join(names)} {b}"
    r = next((i for i, (nm, _) in enumerate(seen.calls) if nm in names), None)
    stop = (seen.last or (None, None))[0]
    w = reached(b, seen, final=final)
    if w is not None and r is not None and r < w:
        return "pass", f"{head}: called at {at(seen, r)}, before " + (
            "the final message" if b == "final_message" else f"first {b} at {at(seen, w)}"
        )
    if w is not None:
        return "fail", (
            f"{head}: "
            + (
                "reached the final message"
                if b == "final_message"
                else f"first {b} at {at(seen, w)}"
            )
            + (
                f", called only at {at(seen, r)}"
                if r is not None
                else ", no call to any of them before it"
            )
        )
    if not final:
        return "open", f"{head}: no {b} yet"
    return "fail", (
        f"{head}: target never reached"
        + (f" (run stopped ({stop}))" if stop not in (None, "exit") else "")
        + (f"; called at {at(seen, r)}" if r is not None else "")
    )


def judge_tool(fact: Fact, seen: Seen, *, final: bool) -> Status:
    """tool_called NAMES (schema, Tool call): a call to one of them ended, not an error, with text
    in its result."""
    names: list[str] = fact["tools"]
    head = f"tool_called {' | '.join(names)}"
    starts: dict[str, tuple[int, str, str]] = {}
    tried: list[str] = []
    for line in seen.lines:
        ev = safe_json(line)
        if not isinstance(ev, dict):
            continue
        cid = str(ev.get("toolCallId", ""))
        if ev.get("type") == "tool_execution_start":
            starts[cid] = (
                len(starts),
                str(ev.get("toolName", "")),
                json.dumps(ev.get("args"))[:120],
            )
        elif ev.get("type") == "tool_execution_end" and cid in starts:
            i, n, a = starts[cid]
            if n not in names:
                continue
            text = content_text(ev.get("result"))
            if ev.get("isError") is not True and text.strip():
                return "pass", f"{head}: tool call {i + 1} {n} {a} returned {len(text)} characters"
            tried.append(
                f"call {i + 1} {n}: " + ("error" if ev.get("isError") is True else "empty result")
            )
    if not final:
        return "open", f"{head}: no result yet"
    return "fail", f"{head}: " + (
        "; ".join(tried) if tried else f"no call to any of them in {len(starts)} tool calls"
    )


def judge_attempt(fact: Fact, seen: Seen, *, final: bool) -> Status:
    """attempt_blocked KIND over the sandbox's record (rule: schema, Attempt record)."""
    kind, record = fact["kind"], seen.record
    if (
        record is None
    ):  # sandbox.json attempts_error, or a record not whole (schema, Attempt record)
        return "fail", f"attempt_blocked {kind}: the sandbox sent no whole attempt record"
    tried = [r for r in record if r.get("kind") == kind and r.get("attempt") is True]

    def show_(r: Fact) -> str:
        return f"{str(r.get('what', ''))[:120]} ({str(r.get('result', ''))[:160]})"

    bad = next((r for r in tried if r.get("refused") is not True), None)
    if bad is not None:
        return "fail", f"attempt_blocked {kind}: recorded attempt NOT refused: {show_(bad)}"
    if not final:
        return "open", f"attempt_blocked {kind}: {len(tried)} recorded, refused so far"
    if not tried:
        return (
            "fail",
            (
                f"attempt_blocked {kind}: no recorded attempt in the sandbox's record "
                f"({len(record)} entries)"
            ),
        )
    return "pass", f"attempt_blocked {kind}: {len(tried)} recorded, each refused: " + "; ".join(
        map(show_, tried)
    )


def arg_matches(want: str, got: str, head: str | None) -> bool:
    """Whether a ran fact's argument WANT matches a recorded one GOT, HEAD the case's sha (rule:
    schema, Run record)."""
    if "{head}" not in want or not head:
        return want == got
    m = re.fullmatch("([0-9a-f]{7,40})".join(map(re.escape, want.split("{head}"))), got)
    return m is not None and all(head.startswith(g) for g in m.groups())


def args_match(want: list[str], got: list[str], head: str | None) -> bool:
    """Whether a recorded argv GOT holds a ran fact's arguments WANT, HEAD the case's sha (rule:
    schema, Run record)."""
    k = next((i for i, w in enumerate(want) if w.startswith("-")), len(want))
    if len(got) < k or not all(
        arg_matches(w, g, head) for w, g in zip(want[:k], got, strict=False)
    ):
        return False
    groups: list[list[str]] = []
    for w in want[k:]:
        if groups and not w.startswith("-") and len(groups[-1]) == 1:
            groups[-1].append(w)
        else:
            groups.append([w])
    rest = got[k:]
    return all(
        any(
            all(arg_matches(w, g, head) for w, g in zip(gr, rest[i : i + len(gr)], strict=True))
            for i in range(len(rest) - len(gr) + 1)
        )
        for gr in groups
    )


def show_run(r: Fact) -> str:
    """A recorded run as ran evidence names it."""
    return f"{str(r.get('what', ''))[:120]} ({str(r.get('result', ''))[:80]})"


def ran_count(
    fact: Fact, name: str, hits: list[Fact], record: list[Fact], *, final: bool
) -> Status:
    """A ran fact with a count: exactly that many matching runs (rule: schema, Run record)."""
    n, name = int(fact["count"]), f"{name} count {fact['count']}"
    said = f"{len(hits)} matching runs" + (
        f": {'; '.join(show_run(r) for r in hits)}" if hits else ""
    )
    if len(hits) > n:
        return "fail", f"{name}: {said}"
    if not final:
        return "open", f"{name}: {said} so far"
    return (
        "pass" if len(hits) == n else "fail"
    ), f"{name}: {said} ({len(record)} entries in the record)"


def judge_ran(fact: Fact, seen: Seen, *, final: bool) -> Status:
    """ran PROGRAM ARGS over the sandbox's record (rule: schema, Run record)."""
    p, want, head = str(fact["program"]), [str(x) for x in fact["args"]], fact.get("_head")
    name = f"ran {' '.join([p, *want])}" + (f" exit {fact['exit']}" if "exit" in fact else "")
    record = seen.record
    if (
        record is None
    ):  # sandbox.json attempts_error, or a record not whole (schema, Attempt record)
        return "fail", f"{name}: the sandbox sent no whole attempt record"
    runs = [
        (r, [str(x) for x in r["argv"]])
        for r in record
        if r.get("kind") == "run" and r.get("program") == p and isinstance(r.get("argv"), list)
    ]
    hits = [
        r
        for r, a in runs
        if args_match(want, a, head if isinstance(head, str) else None)
        and ("exit" not in fact or r.get("exit") == fact["exit"])
    ]
    if "count" in fact:  # rule: schema, Run record
        return ran_count(fact, name, hits, record, final=final)
    if hits:
        return "pass", f"{name}: recorded run {show_run(hits[0])}"
    if not final:
        return "open", f"{name}: no matching run recorded yet"
    return "fail", (
        (
            f"{name}: no run of {p} with these arguments in the sandbox's record "
            f"({len(record)} entries; "
        )
        + (
            f"runs of {p}: {'; '.join(show_run(r) for r, _ in runs)})"
            if runs
            else f"no run of {p} recorded)"
        )
    )


def skill_loaded(fact: Fact, seen: Seen) -> tuple[int | None, str]:
    """(the index of the first tool call whose result loaded the fact's SKILL.md, or None; the
    evidence for none) (rule: schema, Skill load)."""
    n = len(seen.calls)
    texts = result_texts(seen.lines)
    r = next((i for i, x in enumerate(texts[:n]) if loads(fact, x)), None)
    return (
        r,
        (
            f"no load of {fact['skill']}/SKILL.md (its full content in a tool result) in {n} "
            "tool calls"
        ),
    )


def judge_skill(fact: Fact, seen: Seen, *, final: bool) -> Status:
    """skill_read and skill_not_read (schema, Facts)."""
    t, s = fact["fact"], fact["skill"]
    r, none = skill_loaded(fact, seen)
    if r is not None:
        return ("pass" if t == "skill_read" else "fail"), f"{t} {s}: loaded at {at(seen, r)}"
    if not final:
        return "open", f"{t} {s}: {none}"
    return ("fail" if t == "skill_read" else "pass"), f"{t} {s}: {none}"


def judge_skill_before(fact: Fact, seen: Seen, *, final: bool) -> Status:
    """skill_read_before S T (schema, Facts, Before targets)."""
    s, b, n = fact["skill"], target_name(fact["before"]), len(seen.calls)
    head = f"skill_read_before {s} {b}"
    r, none = skill_loaded(fact, seen)
    stop = (seen.last or (None, None))[0]
    w = reached(b, seen, final=final)
    if w is not None and r is not None and r < w:
        tgt = "the final message" if b == "final_message" else f"first {b} at {at(seen, w)}"
        return "pass", f"{head}: loaded at {at(seen, r)}, before {tgt}"
    if w is not None:
        tgt = "the final message" if b == "final_message" else f"first {b} at {at(seen, w)}"
        return "fail", (
            f"{head}: {'reached ' if b == 'final_message' else ''}{tgt}, "
            + (f"loaded only at {at(seen, r)}" if r is not None else none)
        )
    if not final:
        return "open", f"{head}: no {b} yet"
    if b == "final_message":
        gone = (
            "no final assistant message"
            if stop in (None, "exit")
            else f"run stopped ({stop}) before its final message"
        )
    else:
        gone = f"no {b} in {n} tool calls" + (
            f", run stopped ({stop})" if stop not in (None, "exit") else ""
        )
    return "fail", f"{head}: target never reached ({gone}); " + (
        f"loaded at {at(seen, r)}" if r is not None else none
    )


class Judge(Protocol):
    def __call__(self, fact: Fact, seen: Seen, *, final: bool) -> Status: ...


JUDGES: dict[str, Judge] = {
    "declared": judge_declared,
    "declared_includes": judge_includes,
    "field_lines": judge_fields,
    "branch_paths": judge_branch,
    "tool_called_before": judge_tool_before,
    "tool_called": judge_tool,
    "attempt_blocked": judge_attempt,
    "ran": judge_ran,
    "skill_read": judge_skill,
    "skill_not_read": judge_skill,
    "skill_read_before": judge_skill_before,
}


def judge(fact: Fact, seen: Seen, *, final: bool) -> Status:
    """(status, text): status pass, fail, or open (undecided so far; only when not final), each fact
    as schema, Facts says."""
    j = JUDGES.get(fact["fact"])
    if j is None:
        msg = f"unknown fact {fact['fact']!r}"
        raise ValueError(msg)
    return j(fact, seen, final=final)


def ran_setup(facts: list[Fact], head: str) -> tuple[list[Fact], str]:
    """FACTS with each ran fact's _head (the case HEAD), and the sandbox's QC_RECORD value, one
    program per line (schema.md, Run record)."""
    ran = [f for f in facts if f.get("fact") == "ran"]
    return [dict(f, _head=head) if f.get("fact") == "ran" else f for f in facts], "\n".join(
        sorted({str(f["program"]) for f in ran})
    )


# ---- the in-sandbox stop rule ---------------------------------------------------------------

FAKE_GH = r"""#!/bin/sh
# octo-feather-qa fake GitHub (a case's fake_gh): logs argv, answers the few calls a lane start
# needs.
echo "gh $*" >> "$FAKE_GH_LOG"
case "$1 $2" in
  "auth status") echo "github.com: logged in as probe";;
  "repo view") echo '{"nameWithOwner":"probe/app"}';;
  "issue create") echo "https://github.com/probe/app/issues/12";;
  "pr create") echo "https://github.com/probe/app/pull/13";;
  "issue view"|"pr view"|"issue list"|"pr list") echo '[]';;
  *) echo "fake gh: $*" >&2;;
esac
"""
# A case's stand_ins (rule: schema, Case). $QA_STAND_LOG: the calls answered so far. @NAME@,
# @ANSWERS@: the program and the case's list for it.
STAND_IN = r"""#!/usr/bin/env python3
import json, os, sys
log, me = os.environ["QA_STAND_LOG"], ["@NAME@", *sys.argv[1:]]
seen = [json.loads(l) for l in open(log)] if os.path.exists(log) else []
for a in @ANSWERS@:
    if me[1:1 + len(a["args"])] == a["args"] and a.get("argc", len(me) - 1) == len(me) - 1 \
            and ("after" not in a or any(c[:len(a["after"])] == a["after"] for c in seen)):
        open(log, "a").write(json.dumps(me) + "\n")
        sys.stdout.write(a["stdout"]); sys.exit(a["exit"])
sys.exit(print("stand-in: no answer for " + " ".join(me), file=sys.stderr) or 1)
"""


def run(
    argv: list[str],
    *,
    cwd: str | Path | None = None,
    env: dict[str, str] | None = None,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    """ARGV run to its end (ARGV[0] found on PATH, as subprocess finds it), its output captured as
    text."""
    return subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, check=check)


def git_out(*a: str, cwd: str | None = None) -> str:
    return run(["git", *a], cwd=cwd).stdout.strip()


@dataclass(frozen=True)
class Where:
    """Where the watcher runs: the case repo (the role's cwd), the environment it was given, its
    private dir (the sandbox's /tmp/qa-case). The watcher never changes the process cwd or
    os.environ."""

    repo: str
    env: dict[str, str]
    tmp: str


def executable(path: Path, text: str) -> None:
    """TEXT written to PATH, executable (a fake or stand-in first on the role's PATH)."""
    path.write_text(text)
    path.chmod(0o755)


def prep(setup: Fact, where: Where, fake_qa: str) -> tuple[dict[str, str], str | None, str | None]:
    """In the sandbox, after its proof: the case's fake gh (first on PATH, logging argv) and bare
    origin, under its private dir; a fake_qa case's octo-feather-qa, FAKE_QA its text. Returns (env
    for the role, origin dir or None, gh log or None)."""
    tmp, env, origin, log = where.tmp, dict(where.env), None, None
    stands: dict[str, list[Fact]] = setup.get("stand_ins") or {}
    fakes = bool(
        setup.get("fake_gh") or setup.get("fake_qa") or stands
    )  # fakes behind the run shims (schema, Case)
    if setup.get("fake_gh") or setup.get("origin") or stands:
        Path(f"{tmp}/bin").mkdir(parents=True, exist_ok=True)
    if setup.get("fake_gh"):
        log = f"{tmp}/gh.log"
        Path(log).write_text("")
        executable(Path(f"{tmp}/bin/gh"), FAKE_GH)
        env["FAKE_GH_LOG"] = log
    if setup.get("fake_qa"):
        Path(f"{tmp}/bin").mkdir(parents=True, exist_ok=True)
        executable(Path(f"{tmp}/bin/octo-feather-qa"), fake_qa)
    if stands:  # rule: schema, Case (stand_ins)
        env["QA_STAND_LOG"] = f"{tmp}/stand-ins.log"
        here, head = where.repo, git_out("rev-parse", "HEAD", cwd=where.repo)

        def filled(a: Fact) -> Fact:
            out = str(a["stdout"]).replace("{repo}", here).replace("{head}", head)
            return dict(a, stdout=re.sub(r"\{head:(\d+)\}", lambda m: head[: int(m.group(1))], out))

        for p, answers in stands.items():
            fill = [filled(a) for a in answers]
            executable(
                Path(f"{tmp}/bin/{p}"),
                STAND_IN.replace("@NAME@", p).replace("@ANSWERS@", repr(fill)),
            )
    if fakes:
        ps = env.get("PATH", "").split(":")
        at = (
            1 if ps[0] == env.get("OCTO_FEATHER_QC_RUN_SHIMS") else 0
        )  # behind the run shims: a ran fake records it
        env["PATH"] = ":".join([*ps[:at], f"{tmp}/bin", *ps[at:]])
    if setup.get("origin"):
        origin = f"{tmp}/origin.git"
        for a in (
            ["init", "-q", "--bare", "-b", "main", origin],
            ["push", "-q", origin, "main"],
            ["remote", "add", "origin", origin],
        ):
            run(["git", *a], cwd=where.repo, check=True)
    return env, origin, log


def snapshot(origin: str | None, log: str | None, *, keep: bool, cwd: str) -> Fact:
    """The case repo at CWD as data, a snapshot (what it holds: schema, Before targets); keep: also
    those files' bytes as read ("data"), for declared_tests to collect from that same state."""
    files: dict[str, str | None] = {}
    data: dict[str, tuple[str, str | bytes]] = {}
    for f in git_out("ls-files", "-z", "-co", "--exclude-standard", cwd=cwd).split("\0"):
        if f:
            at = Path(cwd) / f
            try:
                b: tuple[str, str | bytes] = (
                    ("link", str(at.readlink())) if at.is_symlink() else ("file", at.read_bytes())
                )
                raw = b[1].encode() if isinstance(b[1], str) else b[1]
                files[f] = hashlib.sha1(raw, usedforsecurity=False).hexdigest()
                if keep:
                    data[f] = b
            except OSError:
                files[f] = None
    gh = Path(log).read_text(errors="replace").splitlines() if log and Path(log).exists() else []
    return {
        "files": files,
        "head": git_out("rev-parse", "-q", "--verify", "HEAD", cwd=cwd),
        "refs": git_out("--git-dir", origin, "for-each-ref", cwd=cwd) if origin else "",
        "gh": gh,
        **({"data": data} if keep else {}),
    }


# Records each file pytest collects (a File node), answering an empty collection so no test module
# is imported.
COLLECT_PLUGIN = """import json, os, pytest
seen = []
@pytest.hookimpl(tryfirst=True)
def pytest_make_collect_report(collector):
    if isinstance(collector, pytest.File):
        seen.append(os.path.relpath(collector.path))
        return pytest.CollectReport(collector.nodeid, "passed", None, [])
def pytest_sessionfinish(session):
    with open(os.environ["QA_COLLECTED"], "w") as f:
        json.dump(seen, f)
"""


def declared_tests(snap: Fact, where: Where) -> dict[str, str | None]:
    """{path: content hash} of every file test_write's runner collects (rule: schema, Before
    targets): run in the repo's synced env, collect only, no test module imported, no bytecode or
    cache written, in a tree under the watcher's private dir from snap's "data" (#170). Raises
    RuntimeError when pytest gives no list."""
    files, tree = snap["files"], Path(f"{where.tmp}/collect/tree")
    shutil.rmtree(tree, ignore_errors=True)
    for f, (kind, b) in snap["data"].items():
        (tree / f).parent.mkdir(parents=True, exist_ok=True)
        if kind == "link":
            (tree / f).symlink_to(b)
        else:
            (tree / f).write_bytes(b)
    collect = Path(f"{where.tmp}/collect")
    collect.mkdir(parents=True, exist_ok=True)
    (collect / "qa_collect.py").write_text(COLLECT_PLUGIN)
    out = collect / "collected.json"
    out.unlink(missing_ok=True)
    env = dict(
        where.env, PYTHONPATH=str(collect), PYTHONDONTWRITEBYTECODE="1", QA_COLLECTED=str(out)
    )
    argv = [
        "uv",
        "run",
        "--project",
        where.repo,
        "--no-sync",
        "--offline",
        "--no-cache",
        "python",
        "-m",
        "pytest",
    ]
    r = run(
        [*argv, "--collect-only", "-q", "-p", "no:cacheprovider", "-p", "qa_collect"],
        env=env,
        cwd=tree,
    )
    if r.returncode not in (0, 5) or not out.exists():
        msg = (
            f"test_write: pytest --collect-only exited {r.returncode}: "
            f"{(r.stdout + r.stderr).strip()[-300:]}"
        )
        raise RuntimeError(msg)
    return {p: files.get(p) for p in json.loads(out.read_text())}


def changed(old: Fact, new: Fact, known: set[str]) -> list[str]:
    """The filesystem targets reached between two snapshots; known: commits that existed before the
    run."""

    def contract(s: Fact) -> dict[str, str | None]:
        return {k: v for k, v in s["files"].items() if CONTRACT_PATH.match(k)}

    return [
        m
        for m, hit in (
            ("edit", old["files"] != new["files"]),
            ("test_write", old.get("tests") != new.get("tests")),
            ("git_commit", new["head"] != old["head"] and new["head"] not in known),
            ("git_push", new["refs"] != old["refs"]),
            ("gh_call", len(new["gh"]) > len(old["gh"])),
            ("kit_contract_edit", contract(old) != contract(new)),
        )
        if hit
    ]


class Bound:
    """The max_tool_calls stop rule (--help): the calls in flight when the count reaches the bound,
    and the calls nested in them, finish and are graded; any other call started after it stops the
    run."""

    def __init__(self, maxc: int) -> None:
        self.maxc = maxc
        self.flight: set[str] = set()  # started, not ended
        self.cap: set[str] | None = None  # in flight when the bound was reached

    def stops(self, raw: bytes, calls: list[Call]) -> bool:
        """After event RAW, CALLS the tool calls started so far: whether the run stops at the bound
        now."""
        e = safe_json(raw)
        ev: Fact = e if isinstance(e, dict) else {}
        cid = str(ev.get("toolCallId", ""))
        if ev.get("type") == "tool_execution_start":
            if self.cap is not None and not any(cid.startswith(c + "/") for c in self.cap):
                return True  # a call outside the calls in flight at the bound: never credited
            self.flight.add(cid)
            if self.cap is not None:
                self.cap.add(cid)
        elif ev.get("type") == "tool_execution_end":
            self.flight.discard(cid)
        if self.cap is None and len(calls) >= self.maxc:
            self.cap = set(self.flight)
        return self.cap is not None and not self.flight


Event = tuple[
    bytes, "Fact | None", "Fact | None"
]  # a line of CMD's stdout, its tool_execution_end event, the snapshot after it


class Watcher:
    """One watched run (watch): the stop rule's state, CMD's process, what it has seen so far."""

    def __init__(self, plan: Plan, where: Where, out: IO[bytes]) -> None:
        self.plan, self.where, self.out = plan, where, out
        # a review case (no facts: --help, Review) runs to its end, this one fact open until then
        self.facts = plan.facts or [{"fact": "skill_not_read", "skill": "", "_skill_text": ""}]
        self.tests = any(
            f.get("before") == "test_write" for f in self.facts
        )  # only a case graded on it
        self.unders = under_targets(self.facts)
        self.why: list[str] = []
        self.err: dict[str, str] = {}
        self.seen: list[Call] = []
        self.raws: list[bytes] = []
        self.origin: str | None = None
        self.log: str | None = None

    def emit(self, line: bytes) -> None:
        self.out.write(line)
        self.out.flush()

    def emit_json(self, record: Fact) -> None:
        self.emit((json.dumps(record) + "\n").encode())

    def snapshot(self) -> Fact:
        return snapshot(self.origin, self.log, keep=self.tests, cwd=self.where.repo)

    def stop(self, p: subprocess.Popen[bytes], reason: str) -> None:
        """REASON recorded (the first one stands), CMD's process group sent TERM, then KILL after 5
        s."""
        if not self.why:
            self.why.append(reason)
        for sig, wait in ((signal.SIGTERM, 5), (signal.SIGKILL, 0)):
            try:
                os.killpg(p.pid, sig)
            except OSError:
                return
            try:
                p.wait(timeout=wait or None)
            except subprocess.TimeoutExpired:
                continue
            return

    def run(self, cmd: list[str]) -> int:
        role_env, self.origin, self.log = prep(self.plan.setup, self.where, self.plan.fake_qa)
        repo = self.where.repo
        known = set(git_out("rev-list", "--all", cwd=repo).split())
        main0 = git_out(
            "rev-parse", "-q", "--verify", "main", cwd=repo
        )  # branch_paths' base (schema, Branch paths)
        snap = self.snapshot()
        if self.tests:
            try:
                snap["tests"] = declared_tests(snap, self.where)
            except RuntimeError as e:
                self.emit_json(
                    {
                        "type": "qa_watch",
                        "stop": "test_runner",
                        "exit": None,
                        "tool_calls": 0,
                        "error": str(e),
                    }
                )
                return 1
        p = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, start_new_session=True, env=role_env, cwd=repo
        )
        timer = threading.Timer(self.plan.timeout_s, self.stop, args=(p, "timeout"))
        timer.daemon = True
        timer.start()
        self.follow(p, snap, known)
        rc = p.wait()
        timer.cancel()
        paths = (
            git_out("diff", "-z", "--name-only", "--no-renames", main0, cwd=repo)
            + "\0"
            + git_out("ls-files", "-z", "-o", "--exclude-standard", cwd=repo)
        ).split("\0")
        self.emit_json(
            {"type": "qa_branch", "base": main0, "paths": sorted({p for p in paths if p})}
        )
        self.emit_json(
            {
                "type": "qa_watch",
                "stop": self.why[0] if self.why else "exit",
                "exit": rc,
                "tool_calls": len(self.seen),
                **self.err,
            }
        )
        return 0 if self.why else rc

    def follow(self, p: subprocess.Popen[bytes], snap: Fact, known: set[str]) -> None:
        """CMD's stdout passed through, each tool end's snapshot compared with the last, until a
        stop."""
        events: queue.Queue[Event | None] = queue.Queue()

        # the snapshot per end event, off the deciding loop (why: schema, Before targets, stated
        # limit; #170)
        def pump() -> None:
            for raw in cast("IO[bytes]", p.stdout):
                e = safe_json(raw) if b'"tool_execution_end"' in raw else None
                end = e if isinstance(e, dict) and e.get("type") == "tool_execution_end" else None
                events.put((raw, end, self.snapshot() if end else None))
            events.put(None)

        threading.Thread(target=pump, daemon=True).start()
        bound = Bound(self.plan.max_tool_calls)
        for raw, end, now in iter(events.get, None):
            self.emit(raw)
            new = tool_calls([raw])
            if not new and not end:
                continue
            self.seen += new
            self.raws.append(raw)
            if end and now is not None:
                if not self.marked(p, snap, now, end, known):
                    break
                snap = now
            if self.decided():
                self.stop(p, "decided")
                break
            if bound.stops(raw, self.seen):
                self.stop(p, "max_tool_calls")
                break

    def marked(
        self, p: subprocess.Popen[bytes], snap: Fact, now: Fact, end: Fact, known: set[str]
    ) -> bool:
        """The targets the call that ended (END) reached, from snapshot SNAP to NOW, written as a
        qa_fs event; False when the test runner failed and the run stopped."""
        if self.tests:
            try:
                now["tests"] = (
                    snap["tests"]
                    if now["files"] == snap["files"]
                    else declared_tests(now, self.where)
                )
            except RuntimeError as e:
                self.err["error"] = str(e)
                self.stop(p, "test_runner")
                return False
        marks = changed(snap, now, known) + under_marks(snap, now, self.unders)
        if marks:
            line = (
                json.dumps(
                    {
                        "type": "qa_fs",
                        "toolCallId": end.get("toolCallId"),
                        "marks": marks,
                        "gh": now["gh"][len(snap["gh"]) :],
                    }
                )
                + "\n"
            ).encode()
            self.emit(line)
            self.raws.append(line)
        return True

    def decided(self) -> bool:
        """Whether every fact is decided on what the run has shown so far."""
        seen = Seen(
            self.seen,
            self.raws,
            attempt_record(self.where.env.get("OCTO_FEATHER_QC_ATTEMPTS", "")),
            marks=fs_marks(self.raws),
        )
        return all(judge(f, seen, final=False)[0] != "open" for f in self.facts)


def watch(plan: Plan, cmd: list[str], *, where: Where, out: IO[bytes]) -> int:
    """Run CMD in the case repo with the environment WHERE gives, pass its stdout through to OUT,
    stop its process group once every fact is decided or at a bound (--help). After each
    tool_execution_end, snapshot the case repo and write a qa_fs event naming the targets that call
    reached; at the end its qa_branch and qa_watch records. Returns the watcher's exit: 0 when it
    stopped the run, else CMD's."""
    return Watcher(plan, where, out).run(cmd)


def skill_source(fact: Fact, kit: Path, repo: Path) -> Fact:
    """FACT with the SKILL.md it grades (rule: schema, Facts): the kit's (_skill_md, read when
    graded), else the case repo's as set up, before the agent runs (_skill_text: its text now, as
    the agent first sees it)."""
    p = kit / ".agents" / "skills" / str(fact.get("skill")) / "SKILL.md"
    if p.is_file():
        return dict(fact, _skill_md=str(p))
    p = repo / ".agents" / "skills" / str(fact.get("skill")) / "SKILL.md"
    return dict(fact, _skill_md=str(p), _skill_text=skill_text(str(p)))


def export(repo: Path, sha: str, dest: Path) -> str | None:
    """REPO's tree at SHA written into DEST by `git archive` (the one export path: --kit-ref's kit,
    a history fixture); None when done, else why not."""
    archive, untar = (
        ["git", "-C", str(repo), "archive", "--format=tar", sha],
        ["tar", "-x", "-C", str(dest)],
    )
    a = subprocess.Popen(archive, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    x = subprocess.run(untar, stdin=a.stdout, capture_output=True, text=True, check=False)
    if a.stdout:
        a.stdout.close()
    gerr = a.stderr.read().decode(errors="replace").strip() if a.stderr else ""
    return (
        None
        if a.wait() == 0 and x.returncode == 0
        else (gerr or x.stderr.strip() or "git archive failed")
    )


def check_evals() -> ModuleType:
    """scripts/check-evals as a module: the one fixture materializer, fixture_tree, and its tree_sha
    (schema.md, Fixtures)."""
    loader = importlib.machinery.SourceFileLoader(
        "check_evals", str(KIT / "scripts" / "check-evals")
    )
    spec = importlib.util.spec_from_loader("check_evals", loader)
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


@dataclass(frozen=True)
class Plan:
    """A case run's plan: its facts resolved (the SKILL.md each skill fact grades, a ran fact's case
    HEAD), its bounds and setup (rules: schema, Case, Facts), the sandbox's run shims, a review
    case's review, and a fake_qa case's octo-feather-qa (the command's own output form, which the
    command gives)."""

    facts: list[Fact]
    max_tool_calls: int
    timeout_s: float
    setup: Fact
    shims: str = ""
    review: Fact | None = None
    fake_qa: str = ""

    @property
    def watch_args(self) -> list[str]:
        """The `--watch FACTS_JSON MAX_CALLS TIMEOUT_S SETUP_JSON` argv the sandboxed command runs
        (--help)."""
        return [
            "--watch",
            json.dumps(self.facts),
            str(self.max_tool_calls),
            str(self.timeout_s),
            json.dumps(self.setup),
        ]

    @classmethod
    def parse(cls, args: list[str], *, fake_qa: str) -> Plan:
        """The plan of `--watch FACTS_JSON MAX_CALLS TIMEOUT_S SETUP_JSON`, ARGS the four after
        --watch."""
        return cls(
            json.loads(args[0]), int(args[1]), float(args[2]), json.loads(args[3]), fake_qa=fake_qa
        )


def plan(
    suite: Result, case: Result, facts: list[Fact], repo: tuple[Path, str], *, kit: Path
) -> Plan:
    """The plan of one run of CASE (of SUITE) graded on FACTS, in the case repo REPO (its dir and
    HEAD, as set up), on the kit KIT."""
    facts = [skill_source(f, kit, repo[0]) if "skill" in f else f for f in facts]
    facts, shims = ran_setup(facts, repo[1])
    setup: Fact = {k: bool(case.get(k)) for k in ("fake_gh", "origin", "fake_qa")}
    setup["stand_ins"] = case.get("stand_ins") or {}
    bounds = (
        int(suite.get("max_tool_calls", DEFAULT_MAX_CALLS)),
        int(suite.get("timeout_s", DEFAULT_TIMEOUT)),
    )
    return Plan(facts, *bounds, setup, shims, case.get("review"))


@dataclass(frozen=True)
class Run:
    """One run's grading: its verdict (PASS, FAIL or REVIEW), deciding lines, model, graded facts,
    the watcher's stop record, a review case's kept output, and what the sandbox gave (its record,
    Pi's stdout and stderr)."""

    verdict: str
    deciding: list[str]
    model: str | None
    graded: list[Fact] = field(default_factory=list)
    stop: Fact | None = None
    kept: Fact | None = None
    sandbox: Fact | None = None
    transcript: str | None = None
    stderr: str | None = None


def attempts(sandbox: Fact) -> tuple[list[Fact] | None, str | None]:
    """(the sandbox's attempt record, None) when whole, else (None, why not; a partial record is
    never graded); (None, None) when it sent none (schema.md, Attempt record)."""
    att = sandbox.get("attempts")
    if att is not None and (
        not isinstance(att, list) or sandbox.get("recorded") != len(cast("list[object]", att))
    ):
        n = len(cast("list[object]", att)) if isinstance(att, list) else "no list of"
        return (
            None,
            (
                f"sandbox: attempt record not whole: {n} entries of {sandbox.get('recorded')} "
                "recorded; a partial record is never graded"
            ),
        )
    return cast("list[Fact] | None", att), None


def problems(
    watched: subprocess.CompletedProcess[str], w: Fact | None, asst: list[Fact], calls: list[Call]
) -> list[str]:
    """What fails the run on its own, whatever its facts (--help): no stop record, pi exited, the
    watcher's error, no assistant message, a model error before any tool call."""
    out: list[str] = []
    if w is None:
        out.append(f"run: no stop record (exit {watched.returncode})")
    elif w["stop"] == "exit" and w["exit"] != 0:
        out.append(f"run: pi exited {w['exit']} on its own")
    if w and w.get("error"):
        out.append(f"run: {w['error']}")
    if not asst:
        out.append("run: no assistant message in the transcript")
    errs = [
        m.get("errorMessage") or m.get("stopReason") for m in asst if m.get("stopReason") == "error"
    ]
    if errs and not calls:
        out.append(f"run: model error: {str(errs[0])[:200]}")
    return out


def grade(
    plan: Plan, watched: subprocess.CompletedProcess[str] | None, sandbox: Fact, *, model: str
) -> Run:
    """The run of PLAN: WATCHED the sandboxed watcher's process (None: the sandbox did not start),
    SANDBOX its record, MODEL the role's. Every fact graded, then the run's verdict (--help; a
    review case: Review)."""
    if watched is None:
        bad = [ln for ln in sandbox.get("proof", []) if "FAIL" in ln] or [
            sandbox.get("error", "sandbox did not start")
        ]
        return Run(
            "FAIL",
            [f"sandbox: proof failed, case not run: {'; '.join(map(str, bad))}"],
            model,
            sandbox=sandbox,
        )
    lines = watched.stdout.splitlines()
    calls = tool_calls(lines)
    events = [e for e in (safe_json(ln) for ln in lines) if isinstance(e, dict)]
    w = next((e for e in reversed(events) if e.get("type") == "qa_watch"), None)
    asst: list[Fact] = [
        e["message"]
        for e in events
        if e.get("type") == "message_end"
        and isinstance(e.get("message"), dict)
        and e["message"].get("role") == "assistant"
    ]
    used = next((f"{m.get('provider')}/{m.get('model')}" for m in asst if m.get("model")), model)
    last = ((w or {}).get("stop"), content_text(asst[-1]) if asst else None)
    att, short = attempts(sandbox)
    seen = Seen(calls, lines, att, last, fs_marks(lines))
    graded = [
        dict({k: v for k, v in f.items() if not k.startswith("_")}, status=s, evidence=txt)
        for f in plan.facts
        for s, txt in [judge(f, seen, final=True)]
    ]
    failed = ([short] if short else []) + problems(watched, w, asst, calls)
    ok = not failed and all(g["status"] == "pass" for g in graded)
    deciding = failed + [g["evidence"] for g in graded if ok or g["status"] != "pass" or failed]
    out: Fact = {
        "graded": graded,
        "stop": w,
        "sandbox": sandbox,
        "transcript": watched.stdout,
        "stderr": watched.stderr,
    }
    if plan.review is None:
        return Run("PASS" if ok else "FAIL", deciding, used, **out)
    # a review case (--help, Review): its output kept, never a pass; REVIEW unless the run failed on
    # its own
    br = next((e for e in reversed(events) if e.get("type") == "qa_branch"), None)
    q = plan.review["question"]
    kept: Result = {
        "question": q,
        "final_message": last[1],
        "changed_files": (br or {}).get("paths", []),
    }
    if not failed:
        deciding = [
            f"awaiting review: {q}",
            f"changed files: {', '.join(kept['changed_files']) or 'none'}",
        ]
    return Run("FAIL" if failed else "REVIEW", deciding, used, kept=kept, **out)


@dataclass(frozen=True)
class Slot:
    """Where one run is recorded and what it is: its dir, its suite and case, its kits ({kit_ref,
    kit_sha}, and with --runs or --baseline its run, of and config), and the reviews dir its latest
    review is read from (--help, Review)."""

    out: Path
    suite: Result
    case: Result
    kits: Result
    reviews: Path


def record(
    slot: Slot, run: Run, *, inputs: Result, secs: float, prompt: str | None = None
) -> tuple[Result, list[str]]:
    """One run's artifacts written into its slot (prompt.md, input.json, sandbox.json,
    transcript.jsonl, stderr.txt, review.json, grading.json, result.json: each one this run has),
    and (its result, the lines to print). INPUTS: input.json; SECS: the run's seconds; PROMPT: its
    task."""
    out, suite, case, kits = slot.out, slot.suite, slot.case, slot.kits
    out.mkdir(parents=True, exist_ok=True)
    if prompt is not None:
        (out / "prompt.md").write_text(prompt + "\n", encoding="utf-8")
    (out / "input.json").write_text(json.dumps(inputs, indent=2) + "\n")
    if run.sandbox is not None:
        (out / "sandbox.json").write_text(json.dumps(run.sandbox, indent=2) + "\n")
    if run.transcript is not None:
        (out / "transcript.jsonl").write_text(run.transcript)
        (out / "stderr.txt").write_text(run.stderr or "")
    if run.kept is not None:
        (out / "review.json").write_text(json.dumps(run.kept, indent=2) + "\n")
    w = run.stop or {}
    (out / "grading.json").write_text(
        json.dumps({"facts": run.graded, "deciding": run.deciding}, indent=2) + "\n"
    )
    res = {
        "suite": suite["suite"],
        "id": case["id"],
        "verdict": run.verdict,
        "deciding": run.deciding,
        "model": run.model,
        "seconds": secs,
        "stop": w.get("stop"),
        "tool_calls": w.get("tool_calls"),
        **({k: case[k] for k in ("role", "should_trigger", "split", "review") if k in case}),
        **kits,
    }
    (out / "result.json").write_text(json.dumps(res, indent=2) + "\n")
    # run k of N (--runs): its line indented, under its case
    at = (
        f"  {kits['config'] + ' ' if kits['config'] else ''}run {kits['run']}/{kits['of']}: "
        if "run" in kits
        else ""
    )
    lines = [at + result_line(res, watched=run.stop is not None)]
    if run.kept is not None:
        latest = latest_review(slot.reviews, str(suite["suite"]), str(case["id"]))
        lines += review_lines(run.kept, out / "review.json", latest)
    return res, lines


def review_file(reviews: Path, suite: str, case: str) -> Path:
    return reviews / suite / f"{case}.jsonl"


def review_records(reviews: Path, suite: str, case: str) -> list[Result]:
    """The case's recorded verdicts, oldest first (--help, Review)."""
    f = review_file(reviews, suite, case)
    raw = [safe_json(ln) for ln in f.read_text().splitlines()] if f.is_file() else []
    return [r for r in raw if isinstance(r, dict)]


def latest_review(reviews: Path, suite: str, case: str) -> Result | None:
    recs = review_records(reviews, suite, case)
    return recs[-1] if recs else None


def show_review(r: Result) -> str:
    return (
        f"{r.get('verdict')} (run {r.get('run_id')}, kit {str(r.get('kit_sha'))[:12]}, "
        f"{r.get('at')}): {r.get('note')}"
    )


def review_lines(kept: Result, where: Path, latest: Result | None) -> list[str]:
    """A review case's output and its latest recorded verdict, as printed under its line."""
    msg = " / ".join(str(kept.get("final_message") or "(no final message)").splitlines())
    return [
        f"  output: final message: {msg[:400]}",
        f"  output: kept in {where}",
        f"  latest review: {show_review(latest) if latest else 'none'}",
    ]


def review(
    run_dir: Path, key: str, verdict: str | None = None, note: str | None = None
) -> list[str]:
    """--review RUN_DIR SUITE/CASE [pass|fail NOTE]: a stored run's review case shown, after
    recording VERDICT and NOTE on it when given (--help, Review); the lines to print. Raises
    UsageError."""
    suite, _, cid = key.partition("/")
    sm: Result = {}
    res: Result = {}
    try:
        sm = cast("Result", json.loads((run_dir / "summary.json").read_text()))
        res = cast("Result", json.loads((run_dir / suite / cid / "result.json").read_text()))
    except (OSError, ValueError) as e:
        msg = f"--review {run_dir} {key}: no stored run case ({e})"
        raise UsageError(msg) from None
    if not isinstance(res.get("review"), dict):
        msg = f"--review {key}: not a review case in run {sm.get('run_id')}"
        raise UsageError(msg)
    reviews = run_dir.parent / "reviews"
    if verdict is not None:
        if verdict not in ("pass", "fail") or not cast("str", note).strip():
            msg = "--review: the verdict is pass or fail, and the note is not blank"
            raise UsageError(msg)
        rec = {
            "run_id": sm.get("run_id"),
            "kit_sha": res.get("kit_sha"),
            "verdict": verdict,
            "note": note,
            "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        review_file(reviews, suite, cid).parent.mkdir(parents=True, exist_ok=True)
        with review_file(reviews, suite, cid).open("a") as fh:
            fh.write(json.dumps(rec) + "\n")
    mine = [r for r in review_records(reviews, suite, cid) if r.get("run_id") == sm.get("run_id")]
    lines = [
        f"REVIEWED {key}: {show_review(mine[-1])}"
        if mine
        else f"REVIEW {key}: awaiting review (run {sm.get('run_id')})"
    ]
    for f in sorted((run_dir / suite / cid).glob("**/review.json")):
        kept = cast("Result", json.loads(f.read_text()))
        lines += review_lines(kept, f, None)[:2]
    return lines


def result_line(res: Result, *, watched: bool) -> str:
    """One run's result line, as printed: with its stop record when the watcher ran (WATCHED)."""
    secs = res["seconds"]
    stop = (
        f" [stop: {res['stop']}, {res['tool_calls']} tool calls, {secs} s]"
        if watched
        else f" [{secs} s]"
    ) + f" [kit {res['kit_sha']}]"
    return (
        f"{res['verdict']} {res['suite']}/{res['id']}: "
        f"{'; '.join(cast('list[str]', res['deciding']))}{stop}"
    )


RUN_KEYS = ("verdict", "deciding", "model", "seconds", "stop", "tool_calls")

USAGE_KEYS = (
    ("input", "input"),
    ("output", "output"),
    ("cache_read", "cacheRead"),
    ("cache_write", "cacheWrite"),
)


def run_usage(transcript: Path) -> Result:
    """The tokens a run's assistant messages used (summed message_end usage, as Pi reports it) and
    their cost (cost_usd None when Pi reported none); every count 0 for a run with no transcript."""
    tot: dict[str, float] = {k: 0 for k, _ in USAGE_KEYS}
    total, cost = 0, None
    lines = transcript.read_text().splitlines() if transcript.is_file() else []
    for raw in (safe_json(ln) for ln in lines):
        e = raw if isinstance(raw, dict) else {}
        msg = e.get("message") if e.get("type") == "message_end" else None
        m = cast("Result", msg) if isinstance(msg, dict) else {}
        u = m.get("usage") if m.get("role") == "assistant" else None
        if not isinstance(u, dict):
            continue
        u = cast("Result", u)
        part = {k: v if isinstance(v := u.get(pi), int | float) else 0 for k, pi in USAGE_KEYS}
        for k, v in part.items():
            tot[k] += v
        t = u.get("totalTokens")
        total += t if isinstance(t, int | float) else sum(part.values())
        c = u.get("cost")
        c = cast("Result", c).get("total") if isinstance(c, dict) else None
        if isinstance(c, int | float):
            cost = (cost or 0) + c
    return {**tot, "total": total, "cost_usd": None if cost is None else round(cost, 6)}


def spread(values: list[float]) -> Result:
    """Mean and sample standard deviation (0 for one value), as --help says; None for no values."""
    if not values:
        return {"mean": None, "stddev": None}
    return {
        "mean": round(statistics.fmean(values), 4),
        "stddev": round(statistics.stdev(values), 4) if len(values) > 1 else 0.0,
    }


def run_facts(grading: Path) -> list[Result]:
    """A run's graded facts, each its parameters and status (grading.json without the evidence
    text)."""
    raw = safe_json(grading.read_text()) if grading.is_file() else None
    g = raw if isinstance(raw, dict) else {}
    fs = cast("list[Result]", g.get("facts", []))
    return [{k: v for k, v in f.items() if k != "evidence"} for f in fs]


def combine(
    case_dir: Path,
    done: dict[str, list[tuple[str, Result]]],
    *,
    runs: int,
    baseline: tuple[str | None, str | None] | None,
) -> tuple[Result, list[str]]:
    """A case over its runs on each config (--runs, --baseline and the result fields: --help), from
    its stored runs: DONE {config: [(run dir under CASE_DIR, its result)]} in config order, the
    current kit's last; BASELINE the baseline kit's (ref, sha) when compared. Writes the case's
    result.json; returns (its result, the lines to print)."""
    ags = {name: aggregate(done[name], case_dir, runs) for name in done}
    res = ags[list(done)[-1]]
    if baseline is not None:
        base = ags["baseline"]
        res = {
            **res,
            "baseline": {
                "kit_ref": baseline[0],
                "kit_sha": baseline[1],
                **{k: base[k] for k in BASE_KEYS},
            },
            "delta": {k: diff(res, base, k) for k in ("pass_rate", "time", "tokens", "cost_usd")},
        }
    (case_dir / "result.json").write_text(json.dumps(res, indent=2) + "\n")
    return res, case_lines(res) if baseline is not None or runs > 1 else []


def case_lines(res: Result) -> list[str]:
    """A repeated or compared case's lines as the run prints them, from its result RES (--runs,
    --baseline: --help): its case line, then with a baseline the baseline's line and the compare
    table, else its cost line."""
    name = f"{res['suite']}/{res['id']}"

    def line(at: str, r: Result) -> str:
        return (
            f"{at}{r['verdict']} {name}: {'; '.join(cast('list[str]', r['deciding']))} "
            f"[{r['seconds']} s] [kit {r['kit_sha']}]"
        )

    b = res.get("baseline")
    if not isinstance(b, dict):
        return [
            line("", res),
            f"  cost {name}: "
            + "; ".join(
                f"{lb} {show_spread(res[k], fmt)}"
                for lb, k, fmt in (("time s", "time", "{:.1f}"), ("tokens", "tokens", "{:.0f}"))
            ),
        ]
    return [line("", res), line("  baseline ", cast("Result", b)), *compare(res)]


BASE_KEYS = (
    "verdict",
    "deciding",
    "seconds",
    "runs",
    "runs_passed",
    "pass_rate",
    "stddev",
    "time",
    "tokens",
    "cost_usd",
)


def mean(res: Result, k: str) -> float | None:
    """Config result RES's mean of K: pass_rate itself, else K's spread mean (None when not
    measured)."""
    v = res.get(k)
    v = cast("Result", v).get("mean") if isinstance(v, dict) else v
    return float(v) if isinstance(v, int | float) else None


def diff(cur: Result, base: Result, k: str) -> float | None:
    """Current minus baseline mean of K (skill-creator's delta), None when either side has none."""
    c, b = mean(cur, k), mean(base, k)
    return None if c is None or b is None else round(c - b, 4)


def aggregate(done: list[tuple[str, Result]], out: Path, runs: int) -> Result:
    """One config's runs of a case as its result: one run's own, else the first failed run's (or run
    1's) with the case's verdict and deciding; with runs, runs_passed, pass_rate, stddev, time,
    tokens and cost_usd."""
    rs = [r for _, r in done]
    ok = [float(r["verdict"] == "PASS") for r in rs]
    use = [run_usage(out / d / "transcript.jsonl") for d, _ in done]
    costs = [cast("float", u["cost_usd"]) for u in use if u["cost_usd"] is not None]
    agg: Result = {
        "runs": [
            {
                "run": k,
                "dir": d,
                **{x: r.get(x) for x in RUN_KEYS},
                "usage": u,
                "facts": run_facts(out / d / "grading.json"),
            }
            for k, ((d, r), u) in enumerate(zip(done, use, strict=True), 1)
        ],
        "runs_passed": int(sum(ok)),
        "pass_rate": round(statistics.fmean(ok), 4),
        "stddev": round(statistics.stdev(ok), 4) if len(ok) > 1 else 0.0,
        "time": spread([cast("float", r["seconds"]) for r in rs]),
        "tokens": spread([cast("float", u["total"]) for u in use]),
        "cost_usd": spread(costs) if len(costs) == len(use) else None,
    }
    if len(rs) == 1 and done[0][0] == ".":
        return {**rs[0], **agg}

    def said(r: Result) -> str:
        return "; ".join(cast("list[str]", r["deciding"]))

    lead = next((r for r in rs if r["verdict"] == "FAIL"), None) or next(
        (r for r in rs if r["verdict"] != "PASS"), rs[0]
    )  # the first failed run, else run 1
    head = (
        f"{agg['runs_passed']}/{runs} runs passed (pass rate {agg['pass_rate']:.2f}, stddev "
        f"{agg['stddev']:.2f})"
    )
    why = [f"run {k}: {said(r)}" for k, r in enumerate(rs, 1) if r["verdict"] != "PASS"] or [
        f"run 1: {said(rs[0])}"
    ]
    secs = round(sum(cast("float", r["seconds"]) for r in rs), 1)
    return {
        **{k: v for k, v in lead.items() if k not in ("run", "of", "config")},
        "verdict": next((v for v in ("FAIL", "REVIEW") if v in {r["verdict"] for r in rs}), "PASS"),
        "deciding": [head, *why],
        "seconds": secs,
        **agg,
    }


def show_spread(sp: object, fmt: str = "{:.2f}") -> str:
    if not isinstance(sp, dict) or cast("Result", sp).get("mean") is None:
        return "n/a"
    sp = cast("Result", sp)
    return f"{fmt.format(sp['mean'])} +/- {fmt.format(sp['stddev'])}"


def compare(cur: Result) -> list[str]:
    """A case's `compare` table from its result CUR, its baseline and delta (--baseline: --help)."""
    rows = [
        ("pass rate", "pass_rate", "{:.2f}"),
        ("time s", "time", "{:.1f}"),
        ("tokens", "tokens", "{:.0f}"),
        ("cost usd", "cost_usd", "{:.4f}"),
    ]
    delta = cast("Result", cur["delta"])
    base = cast("Result", cur["baseline"])
    out = [
        (
            f"  compare {cur['suite']}/{cur['id']}: baseline kit {str(base['kit_sha'])[:12]} "
            f"beside current kit {str(cur['kit_sha'])[:12]}"
        ),
        f"    {'':<10} {'baseline':<20} {'current':<20} difference",
    ]

    def shown(res: Result, k: str, fmt: str) -> str:
        return show_spread(
            {"mean": res["pass_rate"], "stddev": res["stddev"]} if k == "pass_rate" else res[k], fmt
        )

    for lb, k, fmt in rows:
        d = delta[k]
        out.append(
            f"    {lb:<10} {shown(base, k, fmt):<20} {shown(cur, k, fmt):<20} "
            + ("n/a" if d is None else ("+" if cast("float", d) >= 0 else "") + fmt.format(d))
        )
    return out


TRADEOFF = 0.5  # a cost tradeoff's growth over the baseline mean (rule: --help, --analyze)


def compared(r: Result, base: Result, flags: Result) -> None:
    """A case run on both kits (--baseline) into FLAGS: a cost tradeoff, a non-discriminating case,
    or each non-discriminating fact (rules: --help, --analyze)."""
    name = f"{r['suite']}/{r['id']}"
    same = r["pass_rate"] == base["pass_rate"]
    grew: Result = {}
    for k in ("time", "tokens"):
        c, bm = mean(r, k), mean(base, k)
        if c is not None and bm is not None and c > bm * (1 + TRADEOFF):
            grew[k] = {"baseline": bm, "current": c}
    if same and grew:
        flags["cost_tradeoffs"].append({"case": name, "pass_rate": r["pass_rate"], **grew})
    elif same and r["pass_rate"] in (0.0, 1.0):
        flags["non_discriminating_cases"].append({"case": name, "pass_rate": r["pass_rate"]})
    if same:
        return
    fl: list[list[Result]] = [x.get("facts") or [] for x in [*base["runs"], *r["runs"]]]
    for i in range(min(len(f) for f in fl) if fl else 0):
        st = {f[i].get("status") for f in fl}
        if len(st) == 1:
            fact = {k: v for k, v in fl[0][i].items() if k != "status"}
            flags["non_discriminating_facts"].append(
                {"case": name, "fact": fact, "status": st.pop()}
            )


def analyze(cases: list[Result]) -> Result:
    """The deterministic analysis of a run's fact cases (rules: --help, --analyze); no model."""
    flags: Result = {
        "non_discriminating_cases": [],
        "non_discriminating_facts": [],
        "high_variance": [],
        "cost_tradeoffs": [],
    }
    for r in cases:
        if "runs" not in r or "review" in r:
            continue
        b = r.get("baseline")
        base = cast("Result", b) if isinstance(b, dict) else None
        for kit, x in [("baseline", base), ("current", r)] if base else [("", r)]:
            if 0 < x["pass_rate"] < 1:
                flags["high_variance"].append(
                    {
                        "case": f"{r['suite']}/{r['id']}",
                        "kit": kit or None,
                        "pass_rate": x["pass_rate"],
                        "stddev": x["stddev"],
                    }
                )
        if base is not None:
            compared(r, base, flags)
    return {"threshold": TRADEOFF, **flags}


def analysis_lines(a: Result) -> list[str]:
    """The analysis as printed: one line per flag, or `no flags`."""

    def fact(f: Result) -> str:
        return " ".join(
            [
                str(f.get("fact")),
                *(
                    json.dumps(v) if isinstance(v, list | dict) else str(v)
                    for k, v in f.items()
                    if k != "fact"
                ),
            ]
        )

    out = ["qa: analysis (deterministic, no model; rules: octo-feather-qa --help, --analyze):"]
    out += [
        (
            f"  non-discriminating case {x['case']}: every run on both kits "
            f"{'passed' if x['pass_rate'] == 1.0 else 'failed'}"
        )
        for x in cast("list[Result]", a["non_discriminating_cases"])
    ]
    out += [
        (
            f"  non-discriminating fact {x['case']}: {fact(cast('Result', x['fact']))}: "
            f"{x['status']} in every run on both kits"
        )
        for x in cast("list[Result]", a["non_discriminating_facts"])
    ]
    out += [
        f"  high variance {x['case']}: "
        + (f"{x['kit']} kit " if x["kit"] else "")
        + f"pass rate {x['pass_rate']:.2f} +/- {x['stddev']:.2f}"
        for x in cast("list[Result]", a["high_variance"])
    ]
    out += [
        f"  cost tradeoff {x['case']}: pass rate {x['pass_rate']:.2f} on both kits; "
        + "; ".join(
            (
                f"{k} mean {cast('Result', x[k])['baseline']:.1f} to "
                f"{cast('Result', x[k])['current']:.1f}"
            )
            for k in ("time", "tokens")
            if k in x
        )
        for x in cast("list[Result]", a["cost_tradeoffs"])
    ]
    return out if len(out) > 1 else [*out, "  no flags"]


def analysis(cases: list[Result]) -> tuple[Result, list[str]]:
    """The deterministic analysis of a run's fact cases (rules: --help, --analyze) and its lines as
    printed; no model."""
    a = analyze(cases)
    return a, analysis_lines(a)


def summary(run_dir: str | Path) -> Result:
    """RUN_DIR's summary.json, the stored run --analyze reads. Raises UsageError when unreadable."""
    try:
        raw: object = json.loads((Path(run_dir) / "summary.json").read_text())
    except (OSError, ValueError) as e:
        raw = f"no readable summary.json ({e})"
    if not isinstance(raw, dict):
        msg = (
            f"--analyze {run_dir}: "
            f"{raw if isinstance(raw, str) else 'summary.json is not an object'}"
        )
        raise UsageError(msg)
    return cast("Result", raw)


def reanalysis(run_dir: str | Path) -> list[str]:
    """--analyze RUN_DIR: the analysis of a stored run, from its summary.json only, as printed; no
    case, sandbox or model runs. Raises UsageError."""
    sm = summary(run_dir)
    return [
        f"qa: run {sm.get('run_id')} reanalyzed from {Path(run_dir) / 'summary.json'}",
        *analysis(cast("list[Result]", sm.get("cases") or []))[1],
    ]


def evidence(run_dir: str | Path) -> str:
    """--analyze RUN_DIR --evidence: the stored run's evidence block (--help, Evidence). Raises
    UsageError."""
    return evidence_block(Path(run_dir), summary(run_dir))


def fenced(lines: list[str]) -> list[str]:
    """LINES as one markdown text block, its fence longer than any backtick run in them."""
    fence = "`" * max([3, *(len(m) + 1 for ln in lines for m in re.findall("`+", ln))])
    return [f"{fence}text", *lines, fence]


def ran_cited(case_dir: Path, cite: str, runs: list[Result]) -> list[str]:
    """Each graded `ran` fact of RUNS (stored under CASE_DIR, cited as CITE/<dir>) with every
    recorded run matching it, its argv whole as JSON (rules: schema, Run record; --help, Evidence).
    """
    out: list[str] = []
    for r in runs:
        d = str(r.get("dir", "."))
        where = cite if d == "." else f"{cite}/{d}"
        g, sb, inp = (
            stored(case_dir / d / n) for n in ("grading.json", "sandbox.json", "input.json")
        )
        facts = [
            f for f in cast("list[Result]", (g or {}).get("facts") or []) if f.get("fact") == "ran"
        ]
        if g is None:
            out.append(f"{where}: no readable grading.json")
        att = (sb or {}).get("attempts")
        record = (
            [cast("Result", x) for x in cast("list[object]", att) if isinstance(x, dict)]
            if isinstance(att, list)
            else None
        )
        head = (inp or {}).get("fixture_head")
        for f in facts:
            want = [str(x) for x in cast("list[object]", f.get("args") or [])]
            name = " ".join(["ran", str(f.get("program")), *want]) + "".join(
                f" {k} {f[k]}" for k in ("exit", "count") if k in f
            )
            out.append(f"{where}: {name}: {f.get('status')}")
            if record is None:
                out.append("  no whole attempt record in sandbox.json")
                continue
            hits = [
                x
                for x in record
                if x.get("kind") == "run"
                and x.get("program") == f.get("program")
                and isinstance(x.get("argv"), list)
                and ("exit" not in f or x.get("exit") == f["exit"])
                and args_match(
                    want,
                    [str(a) for a in cast("list[object]", x["argv"])],
                    head if isinstance(head, str) else None,
                )
            ]
            out += [
                f"  {x['program']} {json.dumps(x['argv'])} exit {x.get('exit')}" for x in hits
            ] or ["  no matching recorded run"]
    return out


def evidence_block(run_dir: Path, sm: Result) -> str:
    """--analyze RUN_DIR --evidence: the stored run's markdown evidence block (--help, Evidence);
    the same run, the same bytes."""
    rid = str(sm.get("run_id") or run_dir.name)
    b = sm.get("baseline")
    base = cast("Result", b) if isinstance(b, dict) else None
    cases = [
        cast("Result", c)
        for c in cast("list[object]", sm.get("cases") or [])
        if isinstance(c, dict)
    ]
    out = [
        f"## Eval evidence: run {rid}",
        "",
        (
            f"Generated from the stored run alone by `octo-feather-qa --analyze <qa dir>/{rid} "
            "--evidence`; never edited by hand."
        ),
        "",
        f"- run: {rid}, {sm.get('runs', 1)} run(s) per case",
        f"- current kit: {sm.get('kit_sha')} (kit ref {sm.get('kit_ref', 'HEAD')})",
        f"- baseline kit: {base.get('kit_sha')} (--baseline {base.get('kit_ref')})"
        if base
        else "- baseline kit: none",
        f"- cases passed: {sm.get('passed')}/{sm.get('total')}",
    ]
    for c in cases:
        name = f"{c.get('suite')}/{c.get('id')}"
        runs = [
            cast("Result", r)
            for r in cast("list[object]", c.get("runs") or [{"dir": "."}])
            if isinstance(r, dict)
        ]
        bruns = [
            cast("Result", r)
            for r in cast("list[object]", cast("Result", c.get("baseline") or {}).get("runs") or [])
            if isinstance(r, dict)
        ]
        alone = "baseline" not in c and len(runs) == 1
        shown = (
            [result_line(c, watched=c.get("stop") is not None or c.get("tool_calls") is not None)]
            if alone
            else case_lines(c)
        )
        ran = ran_cited(
            run_dir / str(c.get("suite")) / str(c.get("id")), f"{rid}/{name}", [*bruns, *runs]
        )
        out += [
            "",
            f"### {name}",
            "",
            *fenced(shown),
            "",
            f"Pin: `octo-feather-qa --verdict {rid}/{name}`",
        ]
        if ran:
            out += [
                "",
                (
                    "Each graded `ran` fact and every recorded run matching it (sandbox.json "
                    "attempts, argv whole as JSON):"
                ),
                "",
                *fenced(ran),
            ]
    out += [
        "",
        "### Analysis",
        "",
        *fenced(analysis_lines(analyze(cases))),
        "",
        "### To fill",
        "",
        f"Smoke: <each changed role or skill path> run {rid}: <what the run exercised>",
        "Removed: <what the change deleted, or the incident that justifies it>",
    ]
    return "\n".join(out) + "\n"


# ---- --verdict: a qc verdict from pinned stored runs (rules: --help, Verdict) -----------------

INSUFFICIENT = 77  # schemas/qc.v2.schema.json demo command: the demo did not run to its end
# The keys run_case adds to the case it records in input.json: the run's, not the case's.
RUN_INPUT_KEYS = (
    "suite",
    "model",
    "fixture_head",
    "max_tool_calls",
    "timeout_s",
    "kit_ref",
    "kit_sha",
    "run",
    "of",
    "config",
)
# What a role's launch reads beside agents/<role>.md and what pi-role --json lists (scripts/pi-role
# --help).
LAUNCH_PATHS = ("scripts/pi-role", "web-mcp.json")
PIN = re.compile(r"[^-/][^/]*/[^/]+/[^/]+")  # RUN_ID/SUITE/CASE, never an option


def fixture_names(x: object) -> list[str]:
    """Every fixture dir case X names, at any depth: each string value of a `fixture` key."""
    if isinstance(x, dict):
        d = cast("Result", x)
        return [
            n
            for k, v in d.items()
            for n in ([v] if k == "fixture" and isinstance(v, str) else fixture_names(v))
        ]
    return (
        [n for v in cast("list[object]", x) for n in fixture_names(v)]
        if isinstance(x, list)
        else []
    )


def stored(p: Path) -> Result | None:
    """The JSON object at P, None when unreadable or not an object."""
    try:
        raw: object = json.loads(p.read_text())
    except (OSError, ValueError):
        return None
    return cast("Result", raw) if isinstance(raw, dict) else None


def launched(top: str, role: str) -> tuple[list[str], str | None]:
    """The repo paths ROLE launches with, asked of the launcher at HEAD (`scripts/pi-role --json`,
    from an empty dir so no target selects a skill): each --skill folder (a trailing /) and
    --extension file inside TOP; a path outside it (an external skill) is not compared. (paths,
    None), or ([], why the launcher gave no list)."""
    with tempfile.TemporaryDirectory(prefix="qa-verdict-") as cwd:
        p = subprocess.run(
            [
                str(Path(top) / "scripts" / "pi-role"),
                "--json",
                str(Path(top) / "agents" / f"{role}.md"),
            ],
            capture_output=True,
            text=True,
            cwd=cwd,
            check=False,
        )
    raw = safe_json(p.stdout) if p.returncode == 0 else None
    args = raw.get("args") if isinstance(raw, dict) else None
    if not isinstance(args, list):
        return (
            [],
            (
                f"scripts/pi-role --json agents/{role}.md listed no launch (exit "
                f"{p.returncode}: {p.stderr.strip()[-200:]})"
            ),
        )
    a = [str(x) for x in cast("list[object]", args)]
    real = os.path.realpath(top)
    out: list[str] = []
    for flag, val in itertools.pairwise(a):
        if flag in ("--skill", "--extension"):
            rel = os.path.relpath(os.path.realpath(val), real)
            if not rel.startswith(".."):
                out.append(rel + ("/" if flag == "--skill" else ""))
    return sorted(set(out)), None


def entry_change(top: str, sha: str, head: str, rel: str, cid: str) -> str | None:
    """How case CID's own entry in REL (cases.json: a list by id; expectations.json: an object by
    id) differs between the run's kit SHA and HEAD, None when equal."""

    def entry(rev: str) -> object:
        p = run(["git", "-C", top, "show", f"{rev}:{rel}"])
        x = safe_json(p.stdout) if p.returncode == 0 else None
        if isinstance(x, list):
            return next(
                (
                    c
                    for c in cast("list[Result]", x)
                    if isinstance(cast("object", c), dict) and c.get("id") == cid
                ),
                None,
            )
        return x.get(cid) if isinstance(x, dict) else None

    was, now = entry(sha), entry(head)
    if was == now:
        return None
    return f"{rel} case {cid} " + (
        "added" if was is None else "deleted" if now is None else "changed"
    )


def trees_changed(top: str, sha: str, head: str, names: list[str]) -> tuple[list[str], list[str]]:
    """(refusals, changes) of fixtures NAMES' materialized trees between the run's kit SHA and HEAD:
    each rev's evals/ exported from git into scratch outside the repo, each tree built by this kit's
    materializer (check-evals fixture_tree) and hashed as `check-evals --trees` does (schema.md,
    Fixtures)."""
    if not names:
        return [], []
    mod = check_evals()
    bad: list[str] = []
    seen: dict[str, dict[str, str]] = {}
    with tempfile.TemporaryDirectory(prefix="qa-verdict-trees-") as tmp:
        for rev in dict.fromkeys((sha, head)):
            d = Path(tmp) / rev
            d.mkdir()
            err = export(Path(top), rev, d)
            if err is not None:
                bad.append(f"evals/ at {rev[:12]} not exported: {err}")
                continue
            try:
                seen[rev] = {
                    n: str(mod.tree_sha(mod.fixture_tree(d / "evals", n, d / "scratch")))
                    for n in names
                }
            except mod.FixtureError as e:
                bad.append(f"a fixture tree at {rev[:12]} refused: {e}")
    if bad:
        return bad, []
    return [], [f"evals/fixtures/{n} tree changed" for n in names if seen[sha][n] != seen[head][n]]


def pinned(root: Path, top: str, head: str, arg: str) -> tuple[str, str, list[str]]:
    """(verdict PASS, FAIL or INSUFFICIENT, its line, what makes it insufficient) for one
    RUN_ID/SUITE/CASE."""
    rid, suite, cid = arg.split("/")
    d = root / rid / suite / cid
    res = stored(d / "result.json")
    if res is None:
        why = [f"run {rid} has no readable {suite}/{cid}/result.json in {root}"]
        return "INSUFFICIENT", f"INSUFFICIENT {suite}/{cid}: run {rid}: missing: {why[0]}", why
    runs = [
        cast("Result", r)
        for r in cast("list[object]", res.get("runs") or [{"dir": "."}])
        if isinstance(r, dict)
    ]
    sha = str(res.get("kit_sha"))
    missing: list[str] = []
    got: list[tuple[Result, Result, Result]] = []
    for r in runs:
        files = [
            stored(d / str(r.get("dir", ".")) / n)
            for n in ("input.json", "grading.json", "result.json")
        ]
        if any(f is None for f in files):
            missing.append(
                f"run {rid} {suite}/{cid}/{r.get('dir', '.')}: no readable input.json, "
                "grading.json and result.json"
            )
        else:
            got.append(
                (cast("Result", files[0]), cast("Result", files[1]), cast("Result", files[2]))
            )
    if res.get("kit_ref", "HEAD") != "HEAD":
        missing.append(
            f"run {rid} ran with --kit-ref {res.get('kit_ref')}: its fixtures' commit is "
            "not recorded"
        )
    if run(["git", "-C", top, "cat-file", "-e", f"{sha}^{{commit}}"]).returncode:
        missing.append(f"kit sha {sha} of run {rid} is not a commit in {top}")
    review = isinstance(res.get("review"), dict)
    if review:
        mine = [x for x in review_records(root / "reviews", suite, cid) if x.get("run_id") == rid]
        if not mine:
            missing.append(
                f"no maintainer verdict recorded for review case {suite}/{cid} in run "
                f"{rid} (--review)"
            )
        verdict, count = (
            (
                {"pass": "PASS", "fail": "FAIL"}.get(str(mine[-1].get("verdict")), "FAIL")
                if mine
                else "none"
            ),
            "review",
        )
    else:
        ok = sum(rr.get("verdict") == "PASS" for _, _, rr in got)
        verdict, count = (
            ("PASS" if got and ok == len(runs) else "FAIL"),
            f"runs {ok}/{len(runs)} passed",
        )
    stale: list[str] = []
    if not missing:
        role = sorted({str(i.get("role")) for i, _, _ in got})
        fx = sorted(
            {
                n
                for i, _, _ in got
                for n in fixture_names({k: v for k, v in i.items() if k not in RUN_INPUT_KEYS})
            }
        )
        asked = [launched(top, r) for r in role]
        missing += [why for _, why in asked if why]
        paths = [
            *(f"agents/{r}.md" for r in role),
            *LAUNCH_PATHS,
            *sorted({p for ps, _ in asked for p in ps}),
        ]
        bad, changed = trees_changed(top, sha, head, fx)
        missing += bad
        stale += changed
        diff = run(
            ["git", "-C", top, "diff", "--no-renames", "--name-status", sha, head, "--", *paths]
        )
        how = {"A": "added", "D": "deleted"}
        stale += [
            f"{p} {how.get(k[:1], 'changed')}"
            for k, _, p in (ln.partition("\t") for ln in diff.stdout.splitlines())
            if p
        ]
        stale += [
            c
            for rel in (f"evals/{suite}/cases.json", f"evals/{suite}/reference/expectations.json")
            if (c := entry_change(top, sha, head, rel, cid))
        ]
    fresh = (
        f"missing: {'; '.join(missing)}"
        if missing
        else f"stale at HEAD {head[:12]}: {'; '.join(stale)}"
        if stale
        else f"fresh at HEAD {head[:12]}"
    )
    word = "INSUFFICIENT" if missing or stale else verdict
    return (
        word,
        f"{word} {suite}/{cid}: stored {verdict}, run {rid}, kit {sha[:12]}, {count}; {fresh}",
        missing + stale,
    )


@dataclass(frozen=True)
class Judged:
    """--verdict's outcome: a line per pin, the insufficient-evidence line for stderr (None when
    none), the exit."""

    lines: list[str]
    insufficient: str | None
    code: int


def verdict(pins: list[str], *, cwd: str, qa_dir: Path) -> Judged:
    """--verdict RUN_ID/SUITE/CASE...: each pinned case's stored verdict under QA_DIR and its
    freshness against the HEAD of the judged repo at CWD (--help, Verdict). Raises UsageError."""
    bad = [a for a in pins if not PIN.fullmatch(a)]
    if not pins or bad:
        msg = (
            "--verdict takes one or more RUN_ID/SUITE/CASE and no other option (got "
            f"{' '.join(bad) or 'none'})"
        )
        raise UsageError(msg)
    top, head = (git_out("rev-parse", a, cwd=cwd) for a in ("--show-toplevel", "HEAD"))
    if not top or not head:
        msg = "--verdict runs in the judged repo: no git HEAD here"
        raise UsageError(msg)
    done = [pinned(qa_dir, top, head, a) for a in pins]
    short = [f"{a}: {'; '.join(why)}" for a, (_, _, why) in zip(pins, done, strict=True) if why]
    lines = [line for _, line, _ in done]
    if short:
        return Judged(
            lines, f"octo-feather-qa: insufficient evidence: {' | '.join(short)}", INSUFFICIENT
        )
    return Judged(lines, None, 1 if any(w == "FAIL" for w, _, _ in done) else 0)
