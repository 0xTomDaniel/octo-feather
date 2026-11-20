#!/usr/bin/env python3
"""herdr_scope.py adopt PANE | close TAB|SPACE | park PANE: an agent's own systemd user scope
(#1000), and parking it (#1001).

The rule (the scoped launch, owned teardown, unowned panes, the no-manager refusal and the
macOS limit; park's metadata and refusals): herdr-comms SKILL.md, Spawn an agent, Close an agent
or a lane space, and Park an idle agent.

adopt PANE (herdr-spawn's step, before agent start): PANE's shell adopted into a new scope
octo-feather-agent-PANE-<hex>.scope, waited until active. Exit 0 scoped, or unscoped on macOS;
69 the Linux refusal, busctl's own error and the need on stderr; 76 Herdr's answer malformed;
Herdr's own exit when it fails. Closing the tab is the caller's.

close TAB|SPACE (herdr-close's plain close): prints `tab=|space=ID ..._close_rc=RC killed=N
[unowned=PANE,...]` and exits RC, Herdr's close status. A Herdr answer that fails or breaks the
shape below stops it before anything is closed: Herdr's exit, or 76 for a malformed one. Before
the close it reads each closed pane's agent (its name from `herdr agent get`, its role and
session from its Pi process, as park reads them); once Herdr's close succeeded, it hands them to
`octo-feather-handoff close --caller HERDR_PANE_ID`, and names on stderr a caller owning no log
(the rule: herdr-comms SKILL.md, Close an agent or a lane space).

park PANE (herdr-close --park): close's report on stderr, nothing on stdout, and exits close's
status; it hands the parked line to `octo-feather-handoff park --caller HERDR_PANE_ID` (when:
comms spec #roles-park; which log takes it: its --help), and names on stderr, with the line, a
park no log takes; what it reads and its refusals: herdr-comms SKILL.md, Park an idle agent.

Herdr's answers are checked here by hand against the shape Herdr 0.9.5 states for them
(`herdr api schema --json`, protocol 22: PaneInfo, PaneProcessInfo): every field named,
unknown ones rejected, the failing field named; of `agent get` and `tab get` (AgentInfo,
TabInfo) only the one field read is required, and the type only checked when given. Hand-written,
not jsonschema: this runs under an agent's own python3, which has no jsonschema (the kit's
scripts stay standard-library-only: AGENTS.md Rules).
"""

from __future__ import annotations

import json
import os
import platform
import re
import secrets
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO, cast

BAD_ANSWER = 76  # EX_PROTOCOL
REFUSED = 69  # EX_UNAVAILABLE
PREFIX = "octo-feather-agent-"
ENVELOPE = {"id", "result"}
# Herdr 0.9.5 PaneInfo: its fields, and the required ones.
PANE_FIELDS = {
    "agent", "agent_session", "agent_status", "cwd", "display_agent", "focused", "foreground_cwd",
    "label", "pane_id", "restore_error", "revision", "scroll", "state_labels", "tab_id",
    "terminal_id", "terminal_title", "terminal_title_stripped", "title", "tokens", "workspace_id",
}  # fmt: skip
PANE_REQUIRED = {
    "pane_id", "terminal_id", "workspace_id", "tab_id", "focused", "agent_status", "revision",
}  # fmt: skip
# Herdr 0.9.5 PaneProcessInfo: its fields; pane_id the only required one.
PROCESS_FIELDS = {
    "foreground_process_group_id",
    "foreground_processes",
    "pane_id",
    "shell_pid",
    "tty",
}
# Herdr 0.9.5 PaneProcessInfoProcess: its fields, and the required ones.
FG_FIELDS = {"argv", "argv0", "cmdline", "cwd", "name", "pid"}
FG_REQUIRED = {"pid", "name"}
# Herdr 0.9.5 AgentInfo and TabInfo: their fields.
AGENT_FIELDS = {
    "agent", "agent_session", "agent_status", "completion_seq", "cwd", "display_agent", "focused",
    "foreground_cwd", "interactive_ready", "launch_pending", "name", "pane_id", "revision",
    "screen_detection_skipped", "state_change_seq", "state_labels", "tab_id", "terminal_id",
    "terminal_title", "terminal_title_stripped", "title", "tokens", "workspace_id",
}  # fmt: skip
# Herdr 0.9.5 AgentInfo's required fields, checked on `agent list` (octo-feather-lane stale).
AGENT_REQUIRED = {
    "terminal_id", "agent_status", "workspace_id", "tab_id", "pane_id", "focused", "revision",
}  # fmt: skip
TAB_FIELDS = {
    "agent_status", "focused", "label", "number", "pane_count", "tab_id", "workspace_id",
}  # fmt: skip
NOT_NOW = 75  # EX_TEMPFAIL
NOT_SPAWNED = 65  # EX_DATAERR


class BadAnswerError(Exception):
    """A Herdr answer not of the shape Herdr states for it."""


class HerdrFailedError(Exception):
    """A Herdr call that failed: its exit and output."""

    def __init__(self, rc: int, said: str) -> None:
        super().__init__(said)
        self.rc = rc


@dataclass(frozen=True)
class Pane:
    pane_id: str
    tab_id: str
    workspace_id: str
    agent_status: str


@dataclass(frozen=True)
class Process:
    """One foreground process Herdr names for a pane."""

    pid: int
    argv: tuple[str, ...]
    cwd: str


@dataclass(frozen=True)
class ProcessInfo:
    shell_pid: int | None
    foreground: tuple[Process, ...]


def herdr(*args: str) -> object:
    """`herdr ARGS`'s parsed JSON answer; HerdrFailedError when it fails."""
    p = subprocess.run(["herdr", *args], capture_output=True, text=True, check=False)  # noqa: S607
    if p.returncode != 0:
        raise HerdrFailedError(p.returncode, (p.stderr or p.stdout).strip())
    try:
        return cast("object", json.loads(p.stdout))
    except ValueError as e:
        msg = f"herdr {' '.join(args)}: not JSON ({e})"
        raise BadAnswerError(msg) from e


def record(v: object, where: str, fields: set[str], required: set[str]) -> dict[str, object]:
    """V as an object holding only FIELDS, each of REQUIRED present."""
    if not isinstance(v, dict):
        msg = f"{where}: not an object"
        raise BadAnswerError(msg)
    d = cast("dict[str, object]", v)
    unknown = sorted(set(d) - fields)
    if unknown:
        msg = f"{where}: unknown field {unknown[0]}"
        raise BadAnswerError(msg)
    missing = sorted(required - set(d))
    if missing:
        msg = f"{where}: no field {missing[0]}"
        raise BadAnswerError(msg)
    return d


def text(d: dict[str, object], key: str, where: str) -> str:
    v = d[key]
    if not isinstance(v, str) or not v:
        msg = f"{where}.{key}: not a non-empty string"
        raise BadAnswerError(msg)
    return v


def pid_of(v: object, where: str) -> int:
    if not isinstance(v, int) or isinstance(v, bool) or v <= 0:
        msg = f"{where}: not a pid"
        raise BadAnswerError(msg)
    return v


def result(answer: object, where: str, kind: str, key: str, *, typed: bool = True) -> object:
    """The answer's result[KEY], its envelope and type checked (unless not TYPED, when given)."""
    env = record(answer, where, ENVELOPE, {"result"})
    res = record(env["result"], f"{where}.result", {key, "type"}, {key, "type"} if typed else {key})
    if res.get("type", kind) != kind:
        msg = f"{where}.result.type: {res['type']!r}, not {kind!r}"
        raise BadAnswerError(msg)
    return res[key]


def panes(workspace: str) -> list[Pane]:
    """WORKSPACE's panes, from `herdr pane list --workspace`."""
    where = f"herdr pane list --workspace {workspace}"
    got = result(herdr("pane", "list", "--workspace", workspace), where, "pane_list", "panes")
    if not isinstance(got, list):
        msg = f"{where}: result.panes not a list"
        raise BadAnswerError(msg)
    out: list[Pane] = []
    for i, v in enumerate(cast("list[object]", got)):
        at = f"{where}: result.panes[{i}]"
        d = record(v, at, PANE_FIELDS, PANE_REQUIRED)
        ids = (text(d, "pane_id", at), text(d, "tab_id", at), text(d, "workspace_id", at))
        out.append(Pane(*ids, text(d, "agent_status", at)))
    return out


@dataclass(frozen=True)
class Agent:
    pane_id: str
    name: str


def agents() -> list[Agent]:
    """Every agent Herdr runs, from `herdr agent list` (AgentInfo each, name a string or null)."""
    where = "herdr agent list"
    got = result(herdr("agent", "list"), where, "agent_list", "agents", typed=False)
    if not isinstance(got, list):
        msg = f"{where}: result.agents not a list"
        raise BadAnswerError(msg)
    out: list[Agent] = []
    for i, v in enumerate(cast("list[object]", got)):
        at = f"{where}: result.agents[{i}]"
        d = record(v, at, AGENT_FIELDS, AGENT_REQUIRED)
        name = d.get("name")
        if name is not None and not isinstance(name, str):
            msg = f"{at}.name: not a string or null"
            raise BadAnswerError(msg)
        out.append(Agent(text(d, "pane_id", at), name or ""))
    return out


def shell_pid(pane: str) -> int | None:
    """PANE's shell pid from `herdr pane process-info`; None when Herdr names none."""
    return process_info(pane).shell_pid


def process_info(pane: str) -> ProcessInfo:
    """PANE's shell pid and foreground processes, from `herdr pane process-info`."""
    where = f"herdr pane process-info --pane {pane}"
    got = result(
        herdr("pane", "process-info", "--pane", pane), where, "pane_process_info", "process_info"
    )
    d = record(got, f"{where}: result.process_info", PROCESS_FIELDS, {"pane_id"})
    if d["pane_id"] != pane:
        msg = f"{where}: result.process_info.pane_id {d['pane_id']!r}, not {pane!r}"
        raise BadAnswerError(msg)
    pid = d.get("shell_pid")
    if pid is not None:
        pid = pid_of(pid, f"{where}: result.process_info.shell_pid")
    fg = d.get("foreground_processes", [])
    if not isinstance(fg, list):
        msg = f"{where}: result.process_info.foreground_processes not a list"
        raise BadAnswerError(msg)
    procs: list[Process] = []
    for i, v in enumerate(cast("list[object]", fg)):
        at = f"{where}: result.process_info.foreground_processes[{i}]"
        p = record(v, at, FG_FIELDS, FG_REQUIRED)
        # argv: array of string, or null; cwd: string or null. Only absent or null become empty.
        raw = p.get("argv")
        items = cast("list[object]", raw) if isinstance(raw, list) else None
        if raw is not None and (items is None or not all(isinstance(x, str) for x in items)):
            msg = f"{at}.argv: not a list of strings or null"
            raise BadAnswerError(msg)
        argv = cast("list[str]", items or [])
        cwd = p.get("cwd")
        if cwd is not None and not isinstance(cwd, str):
            msg = f"{at}.cwd: not a string or null"
            raise BadAnswerError(msg)
        cwd = cwd or ""
        procs.append(Process(pid_of(p["pid"], f"{at}.pid"), tuple(argv), cwd))
    return ProcessInfo(pid, tuple(procs))


def scope_of(pid: int, pane: str) -> str | None:
    """The scope PID runs in (its cgroup v2 path) when it is PANE's own, the unit adopt names for
    PANE under this user's own manager (the rule: herdr-comms SKILL.md, Close an agent or a lane
    space), else None: an unowned process, one gone, or no /proc (macOS)."""
    try:
        lines = Path(f"/proc/{pid}/cgroup").read_text().splitlines()
    except OSError:
        return None
    path = next((x[3:] for x in lines if x.startswith("0::")), "")
    name = path.rsplit("/", 1)[-1]
    mine = f"/user@{os.getuid()}.service/" in path
    own = re.fullmatch(re.escape(f"{PREFIX}{pane}-") + r"[0-9a-f]{8}\.scope", name)
    return path if mine and own else None


def adopt(pane: str) -> int:
    """PANE's shell into a new agent scope (module docstring). The one place an agent's launch
    is decided: macOS unscoped; on Linux a failed adoption refuses, the one branch that could
    become an unscoped launch (owner question open, #1000)."""
    if platform.system() == "Darwin":
        return 0
    pid = shell_pid(pane)
    unit = f"{PREFIX}{pane}-{secrets.token_hex(4)}.scope"
    why = "herdr names no shell for the pane" if pid is None else ""
    if pid is not None:
        # systemd-run cannot adopt a running pid, and agent start types `pi ARGS` itself: so
        # systemd's own D-Bus StartTransientUnit with PIDs. It only queues the job: wait until
        # the shell is a member, or what it starts next escapes.
        call = ["busctl", "--user", "call", "org.freedesktop.systemd1", "/org/freedesktop/systemd1"]
        call += ["org.freedesktop.systemd1.Manager", "StartTransientUnit", "ssa(sv)a(sa(sv))"]
        call += [unit, "fail", "3", "PIDs", "au", "1", str(pid), "CollectMode", "s"]
        call += ["inactive-or-failed", "TimeoutStopUSec", "t", "10000000", "0"]
        try:
            p = subprocess.run(call, capture_output=True, text=True, check=False)
            why = (
                "" if p.returncode == 0 else f"busctl: {(p.stderr or p.stdout).strip() or 'failed'}"
            )
        except OSError as e:
            why = f"busctl: {e}"
        if not why:
            for _ in range(50):
                active = ["systemctl", "--user", "is-active", "-q", unit]
                if subprocess.run(active, check=False).returncode == 0:
                    return 0
                time.sleep(0.1)
            why = f"{unit} never became active"
    uid = os.getuid()
    sys.stderr.write(
        f"herdr-spawn: could not start the agent in its own systemd user scope ({why}); it needs a"
        " reachable systemd user manager (on a server: loginctl enable-linger"
        f" {os.environ.get('USER', '$USER')}, then XDG_RUNTIME_DIR=/run/user/{uid})\n"
    )
    return REFUSED


def members(target: str) -> list[Pane]:
    """The panes TARGET, a tab (with a colon) or a space, holds."""
    shown = panes(target.split(":", 1)[0])
    return [p for p in shown if ":" not in target or p.tab_id == target]


def close(target: str, out: TextIO = sys.stdout) -> int:
    """Close TARGET through Herdr, then stop its panes' agent scopes (module docstring); the
    report on OUT."""
    kind = "tab" if ":" in target else "space"
    shown = members(target)
    scopes: list[str] = []
    unowned: list[str] = []
    for p in shown:
        pid = shell_pid(p.pane_id)
        cg = scope_of(pid, p.pane_id) if pid is not None else None
        if cg is None:
            unowned.append(p.pane_id)
        else:
            scopes.append(cg)
    verb = ["tab", "close"] if kind == "tab" else ["workspace", "close"]
    rc = subprocess.run(["herdr", *verb, target], capture_output=True, check=False).returncode  # noqa: S607
    killed = 0
    for cg in scopes:
        try:
            n = len(Path(f"/sys/fs/cgroup{cg}/cgroup.procs").read_text().split())
        except OSError:
            n = 0  # emptied and collected since
        stop = ["systemctl", "--user", "stop", cg.rsplit("/", 1)[-1]]
        if subprocess.run(stop, capture_output=True, check=False).returncode == 0:
            killed += n
    report = f"{kind}={target} {kind}_close_rc={rc} killed={killed}"
    out.write(report + (f" unowned={','.join(unowned)}" if unowned else "") + "\n")
    return rc


def found(answer: object, where: str, key: str, fields: set[str], need: str) -> str:
    """NEED of the answer's result[KEY], a record of FIELDS, of type KEY_info (module docstring:
    agent get, tab get)."""
    got = result(answer, where, f"{key}_info", key, typed=False)
    d = record(got, f"{where}: result.{key}", fields, {need})
    v = d[need]
    if not isinstance(v, str):
        msg = f"{where}: result.{key}.{need} not a string"
        raise BadAnswerError(msg)
    return v


def environ(pid: int) -> dict[str, str]:
    """PID's own environment, or {} when it cannot be read (gone, another user's)."""
    try:
        raw = Path(f"/proc/{pid}/environ").read_bytes()
    except OSError:
        return {}
    pairs = (x.decode(errors="replace").split("=", 1) for x in raw.split(b"\0") if b"=" in x)
    return dict(cast("tuple[str, str]", tuple(kv)) for kv in pairs)


def live_members(cg: str, own: set[int]) -> list[str]:
    """The scope CG's live processes outside OWN (the pane's shell and Pi): `PID COMMAND` each."""
    try:
        pids = [int(x) for x in Path(f"/sys/fs/cgroup{cg}/cgroup.procs").read_text().split()]
    except OSError:
        return []
    out: list[str] = []
    for pid in sorted(set(pids) - own):
        try:
            if Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0] == "Z":
                continue
            cmd = (
                Path(f"/proc/{pid}/cmdline")
                .read_bytes()
                .replace(b"\0", b" ")
                .decode(errors="replace")
            )
        except (OSError, IndexError):
            continue  # ended since
        out.append(f"{pid} {cmd.strip()}")
    return out


def pi_session(info: ProcessInfo) -> tuple[Process, str] | None:
    """The foreground process launched with `--session-id S`, and S."""
    for p in info.foreground:
        argv = list(p.argv)
        if "--session-id" in argv[:-1]:
            return p, argv[argv.index("--session-id") + 1]
    return None


def park(pane: str) -> int:
    """Park PANE's idle agent (module docstring): its metadata only from the Pi process Herdr
    names for it, never another process's; refused while its scope runs anything else."""
    if platform.system() == "Darwin":
        sys.stderr.write(
            "herdr-close --park: not on macOS (it reads the pane's Pi session from /proc); not"
            " parked. Leave the agent running, or close its tab with herdr-close and relaunch it"
            " fresh when needed\n"
        )
        return REFUSED
    info = process_info(pane)
    got = pi_session(info)
    env = environ(got[0].pid) if got else {}
    if got is None or env.get("OCTO_FEATHER_SESSION_ID") != got[1]:
        sys.stderr.write(f"herdr-close: no herdr-spawn Pi session in {pane}; not parked\n")
        return NOT_SPAWNED
    pi, session = got
    workspace = pane.split(":", 1)[0]
    shown = panes(workspace)
    me = next((p for p in shown if p.pane_id == pane), None)
    if me is None or me.agent_status not in ("idle", "done"):
        sys.stderr.write(f"herdr-close: {pane} is not idle; not parked\n")
        return NOT_NOW
    cg = scope_of(info.shell_pid, pane) if info.shell_pid is not None else None
    busy = live_members(cg, {pi.pid, info.shell_pid or 0}) if cg else []
    if busy:
        sys.stderr.write(
            f"herdr-close: {pane} not parked: its scope {cg.rsplit('/', 1)[-1] if cg else ''} runs"
            f" {len(busy)} other live process(es) park would end; nothing closed. Wait for them"
            " or end them, then park:\n" + "".join(f"  {x}\n" for x in busy)
        )
        return NOT_NOW
    where = f"herdr agent get {pane}"
    name = found(herdr("agent", "get", pane), where, "agent", AGENT_FIELDS, "name")
    where = f"herdr tab get {me.tab_id}"
    label = found(herdr("tab", "get", me.tab_id), where, "tab", TAB_FIELDS, "label")
    only = {p.tab_id for p in shown} == {me.tab_id}
    fields = {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "kind": "parked"}
    fields |= {"pane": pane, "name": name, "role": env.get("OCTO_FEATHER_ROLE", "")}
    fields |= {"cwd": pi.cwd, "session": session, "label": label}
    fields |= {"parent": env.get("OCTO_FEATHER_PARENT", "")}
    encode = [str(Path(__file__).resolve().parents[4] / "scripts" / "octo-feather-handoff")]
    encode += ["encode", *(x for k, v in fields.items() for x in ("--field", k, v))]
    line = subprocess.run(encode, capture_output=True, text=True, check=True).stdout
    rc = close(workspace if only else me.tab_id, sys.stderr)
    if rc != 0:
        return rc
    caller = os.environ.get("HERDR_PANE_ID", "")
    log = [encode[0], "park", "--caller", caller]
    rc_log = subprocess.run(log, input=line, text=True, check=False).returncode
    if rc_log == 65:  # noqa: PLR2004 (octo-feather-handoff park: no log owns the line)
        who = f"pane {caller}" if caller else "the caller (no HERDR_PANE_ID)"
        sys.stderr.write(
            f"herdr-close: no hand-off log recorded this park: neither {pane} nor {who} owns one"
            " (no lane record's supervisor, not director.toml's pane); its parked line:\n" + line
        )
    elif rc_log != 0:
        sys.stderr.write(
            "herdr-close: park not recorded in its hand-off log (error above); parked, its"
            " parked line:\n" + line
        )
    return rc


def agent_name(pane: str) -> str:
    """The name Herdr gives PANE's agent, '' when it has none or finds no agent there."""
    try:
        answer = herdr("agent", "get", pane)
    except HerdrFailedError as e:
        if "agent_not_found" in str(e):
            return ""
        raise
    where = f"herdr agent get {pane}"
    got = result(answer, where, "agent_info", "agent", typed=False)
    got = record(got, f"{where}: result.agent", AGENT_FIELDS, set())
    name = got.get("name")
    if name is not None and not isinstance(name, str):
        msg = f"{where}: result.agent.name: not a string or null"
        raise BadAnswerError(msg)
    return name or ""


def close_recorded(target: str) -> int:
    """herdr-close's plain close, recorded in the caller's own hand-off log (module docstring)."""
    me = os.environ.get("HERDR_PANE_ID", "")
    agents: list[dict[str, str]] = []
    for p in members(target) if me else []:
        got = pi_session(process_info(p.pane_id))
        role = environ(got[0].pid).get("OCTO_FEATHER_ROLE", "") if got else ""
        fields = {"pane": p.pane_id, "name": agent_name(p.pane_id), "role": role}
        agents.append(fields | {"session": got[1] if got else ""})
    rc = close(target)
    if rc != 0:
        return rc
    rc_log = 65
    if me:
        handoff = [str(Path(__file__).resolve().parents[4] / "scripts" / "octo-feather-handoff")]
        lines = "".join(json.dumps(x) + "\n" for x in agents)
        log = subprocess.run(
            [*handoff, "close", "--caller", me], input=lines, text=True, check=False
        )
        rc_log = log.returncode
    if rc_log == 65:  # noqa: PLR2004 (octo-feather-handoff close: the caller owns no log)
        who = f"pane {me}" if me else "the caller (no HERDR_PANE_ID)"
        sys.stderr.write(
            f"herdr-close: no hand-off log recorded this close: {who} owns none (no lane record's"
            " supervisor, not director.toml's pane)\n"
        )
    elif rc_log != 0:
        sys.stderr.write(
            "herdr-close: close not recorded in the caller's hand-off log (error above); closed\n"
        )
    return rc


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in ("adopt", "close", "park"):  # noqa: PLR2004
        sys.stderr.write(__doc__ or "")
        return 64
    verb, arg = sys.argv[1:]
    who, after = (
        ("herdr-spawn", "not started") if verb == "adopt" else ("herdr-close", "nothing closed")
    )
    try:
        return {"adopt": adopt, "close": close_recorded, "park": park}[verb](arg)
    except HerdrFailedError as e:
        sys.stderr.write(f"{who}: {e}; {after}\n")
        return e.rc
    except BadAnswerError as e:
        sys.stderr.write(f"{who}: malformed Herdr answer: {e}; {after}\n")
        return BAD_ANSWER


if __name__ == "__main__":
    sys.exit(main())
