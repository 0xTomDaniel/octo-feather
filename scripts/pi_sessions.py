#!/usr/bin/env python3
"""pi_sessions: what a Pi session read: the session reader octo-feather-lane's skills and report share. Moved from scripts/octo-feather-lane, the dispatcher (ticket #1333)."""

import dataclasses
import json
import os
import re
import shlex
from pathlib import Path
from typing import cast

from lane_cli import dtm
from tracker_calls import utc

# Skill reach (spec comms #report-skill-reach), from the agents' Pi session files: offered = the session's system
# prompt <available_skills> list, read = a tool call reading <skill>/SKILL.md. Rules: octo-feather-lane --help (report).
SKILL_PATH = re.compile(r"(?:^|.*/)([A-Za-z0-9_.-]+)/SKILL\.md")   # a whole operand naming a SKILL.md, its folder
OFFERED = re.compile(r"<skill>\s*<name>([^<]+)</name>.*?<location>([^<]+)</location>", re.S)
READERS = {"cat", "head", "tail", "sed", "less", "more", "bat", "nl"}
VALUED = {"head": {"-n", "-c"}, "tail": {"-n", "-c"}, "sed": {"-l"}, "nl": {"-b", "-d", "-f", "-h", "-i", "-l", "-n", "-s", "-v", "-w"}}
SHELL_STOP = {"|", "||", "&", "&&", ";", ";;", "(", ")", "\n"}
SHELL_LEAD = {"{", "}", "!", "then", "do", "else", "time", "if", "while", "until", "exec", "command"}
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n.*?^\s*\2\s*$", re.S | re.M)
# A `#` inside a word, hidden from shlex as NUL (no shell word holds one) and put back in each word. Rule: --help (report).
MID_WORD_HASH = re.compile(r"(?<=[^\s;&|()<>])#")
STAMP = re.compile(r'"timestamp":\s*"([^"]+)"')
# A call naming a SKILL.md, read or not (rules: --help, skills): the path's folder piece; `*` stands for every folder.
SKILL_NAMED = re.compile(r"([^\s'\"=;|&()<>]*)/SKILL\.md(?!\.?\w)")
WRITERS = {"write", "edit"}


def sessions_dir() -> Path:
    """Pi's session folder: PI_CODING_AGENT_DIR (else ~/.pi/agent)/sessions, as Pi and octo-feather-qc read it."""
    return Path(os.environ.get("PI_CODING_AGENT_DIR") or Path.home() / ".pi" / "agent") / "sessions"


def skill_operand(word: str) -> str | None:
    """The skill folder of a file operand that is exactly a SKILL.md path; None for a computed one (--help, report)."""
    m = SKILL_PATH.fullmatch(word)
    return m.group(1) if m and not re.search(r"[$*?\[{`]", word) else None


def shell_reads(cmd: str) -> list[str]:
    """The skill folders whose SKILL.md a shell command CMD opens as a reader's file operand (rules: --help, report)."""
    try:
        lex = shlex.shlex(MID_WORD_HASH.sub("\0", HEREDOC.sub("", cmd)), posix=True, punctuation_chars=";&|()<>\n")
        lex.whitespace = " \t\r"
        lex.whitespace_split = True
        words = [w.replace("\0", "#") for w in lex]
    except ValueError:
        return []   # unbalanced quotes: nothing resolved, nothing counted
    out: list[str] = []
    cmds: list[list[str]] = [[]]
    for w in words:
        if w in SHELL_STOP:
            cmds.append([])
        else:
            cmds[-1].append(w)
    for words_of in cmds:
        lead = 0
        while lead < len(words_of) and (words_of[lead] in SHELL_LEAD or re.fullmatch(r"[A-Za-z_]\w*=.*", words_of[lead])):
            lead += 1
        c = words_of[lead:]
        prog = Path(c[0]).name if c else ""
        if prog not in READERS:
            continue
        operands: list[str] = []
        script = prog == "sed"
        i = 1
        while i < len(c):
            w = c[i]
            if w in (">", ">>", ">|", "<<", "<<<") or re.fullmatch(r"\d?>&?", w):
                i += 2   # a write target, a heredoc delimiter or here-string: no read
                continue
            if w == "<":
                operands.append(c[i + 1] if i + 1 < len(c) else "")
                i += 2
                continue
            if prog == "sed" and w in ("-e", "-f", "--expression", "--file"):
                script = False   # the script is this option's value; every later operand is a file
                i += 2
                continue
            if prog == "sed" and w in ("-i", "--in-place") or w.startswith("-i") and prog == "sed":
                operands = []
                break   # sed -i edits, it is no read
            if w.startswith("-") and w != "-":
                i += 2 if w in VALUED.get(prog, set()) else 1
                continue
            if script:
                script = False   # sed's first operand is its script text, never a file
            else:
                operands.append(w)
            i += 1
        out += [f for f in map(skill_operand, operands) if f]
    return out


def tool_reads(name: object, args: object) -> list[str]:
    """The skill folders whose SKILL.md one read or bash call with arguments ARGS opens (rules: --help, report)."""
    key = {"read": "path", "bash": "command"}.get(str(name))
    arg = cast("dict[str, object]", args).get(key) if isinstance(args, dict) and key else None
    if not isinstance(arg, str):
        return []
    if name == "read":
        f = skill_operand(arg.strip())
        return [f] if f else []
    return shell_reads(arg)


def call_names(name: object, args: object) -> tuple[set[str], str]:
    """The folders whose SKILL.md one call's arguments ARGS name, read or not, and the call as said (--help, skills):
    a literal folder piece names that folder; a computed one ($var, glob, brace) names each word of the call (`*` for
    a bare wildcard: every folder). A write or edit names none."""
    def strings(x: object) -> list[str]:
        if isinstance(x, str):
            return [x]
        vals: list[object] = list(cast("dict[str, object]", x).values()) if isinstance(x, dict) else (
            cast("list[object]", x) if isinstance(x, list) else [])
        return [s for v in vals for s in strings(v)]
    text = " ".join(" ".join(strings(args)).split())
    if str(name) in WRITERS or "SKILL.md" not in text:
        return set(), ""
    out: set[str] = set()
    for m in SKILL_NAMED.finditer(text):
        seg = m.group(1).rsplit("/", 1)[-1].strip("`")
        if not re.search(r"[$*?\[{]", seg):
            out.add(seg)
        else:
            out |= set(re.findall(r"[A-Za-z0-9_.-]+", text)) | ({"*"} if re.fullmatch(r"[*?]+", seg) else set())
    i = text.find("SKILL.md")
    cut = ("..." if i > 100 else "") + text[max(0, i - 100):i + 30] + ("..." if i + 30 < len(text) else "")
    return out, f"{name} `{cut}`"


@dataclasses.dataclass(frozen=True)
class SessionReach:
    """One Pi session's role, the skills it was offered ({name: folder}), the skills it read (by offered name) and the
    folders whose SKILL.md a successful call named ({folder: that call}, the first; `*` any folder)."""
    role: str
    offered: dict[str, str]
    read: set[str]
    named: dict[str, str] = dataclasses.field(default_factory=dict)


def session_reach(path: Path, since: dtm.datetime) -> SessionReach | None:
    """One Pi session file's role, offered skills and read skills (what counts and when: --help, report); None when it
    has no activity after SINCE. OSError or ValueError when unreadable."""
    role: str | None = None
    offered: dict[str, str] = {}
    folders: set[str] = set()
    named: dict[str, str] = {}
    pending: dict[str, tuple[list[str], set[str], str]] = {}   # a call's id: the folders it would read and names, until its result
    with path.open(encoding="utf-8", errors="replace") as fh:
        head: object = json.loads(fh.readline() or "null")
        hd = cast("dict[str, object]", head) if isinstance(head, dict) else {}
        start = utc(hd.get("timestamp")) if hd.get("type") == "session" else None
        if start is None:
            raise ValueError("no session line with a timestamp first")
        active = start > since
        for line in fh:
            if not active and (t := STAMP.search(line[:300])):
                active = (utc(t.group(1)) or since) > since
            if "SKILL.md" not in line and '"system"' not in line and not any(i in line[:1000] for i in pending):
                continue   # no system prompt, no call naming a SKILL.md, no result of one: not parsed
            try:
                d: object = json.loads(line)
            except ValueError:
                continue   # a line Pi left partial
            e = cast("dict[str, object]", d) if isinstance(d, dict) else {}
            m = e.get("message")
            if not isinstance(m, dict):
                continue
            m = cast("dict[str, object]", m)
            if m.get("role") == "system" and isinstance(sec := m.get("sections"), dict):
                sec = cast("dict[str, object]", sec)
                h = re.search(r"^#\s+(.+?)\s*$", str(sec.get("addendum") or ""), re.M)
                role = role or (h.group(1).lower() if h else None)
                offered |= {n.strip(): Path(loc.strip()).parent.name for n, loc in OFFERED.findall(str(sec.get("skills") or ""))}
            elif m.get("role") == "assistant" and isinstance(content := m.get("content"), list):
                for x in cast("list[object]", content):
                    c = cast("dict[str, object]", x) if isinstance(x, dict) else {}
                    if c.get("type") != "toolCall":
                        continue
                    got = tool_reads(c.get("name"), c.get("arguments"))
                    names, said = call_names(c.get("name"), c.get("arguments"))
                    if got or names:
                        pending[str(c.get("id"))] = got, names, said
            elif m.get("role") == "toolResult":
                did, names, said = pending.pop(str(m.get("toolCallId")), ([], set(), ""))
                at = utc(e.get("timestamp"))
                if at is None or at <= since:
                    continue   # a result before the window, or at no readable time: no read counted
                nested = m.get("nestedCalls")
                calls = cast("dict[str, object]", nested).get("calls") if isinstance(nested, dict) else None
                if m.get("isError") is not True:
                    folders |= set(did)
                    # a call whose result records its nested calls is judged by them, never by its own source
                    named |= {f: said for f in names if f not in named} if not isinstance(calls, list) else {}
                for x in cast("list[object]", calls) if isinstance(calls, list) else []:
                    c = cast("dict[str, object]", x) if isinstance(x, dict) else {}
                    if c.get("status") == "ok":
                        folders |= set(tool_reads(c.get("name"), c.get("arguments")))
                        names, said = call_names(c.get("name"), c.get("arguments"))
                        named |= {f: said for f in names if f not in named}
    if not active:
        return None
    by_folder = {f: n for n, f in offered.items()}
    return SessionReach(role or "no role", offered, {by_folder.get(f, f) for f in folders}, named)
