#!/usr/bin/env python3
"""herdr_scope.py adopt PANE | close TAB|SPACE: an agent's own systemd user scope (#1000).

The rule (the scoped launch, owned teardown, unowned panes, the no-manager refusal and the
macOS limit): herdr-comms SKILL.md, Spawn an agent and Close an agent or a lane space.

adopt PANE (herdr-spawn's step, before agent start): PANE's shell adopted into a new scope
octo-feather-agent-PANE-<hex>.scope, waited until active. Exit 0 scoped, or unscoped on macOS;
69 the Linux refusal, busctl's own error and the need on stderr; 76 Herdr's answer malformed;
Herdr's own exit when it fails. Closing the tab is the caller's.

close TAB|SPACE (herdr-close's plain close): prints `tab=|space=ID ..._close_rc=RC killed=N
[unowned=PANE,...]` and exits RC, Herdr's close status. A Herdr answer that fails or breaks the
shape below stops it before anything is closed: Herdr's exit, or 76 for a malformed one.

Herdr's answers are checked here by hand against the shape Herdr 0.9.5 states for them
(`herdr api schema --json`, protocol 22: PaneInfo, PaneProcessInfo): every field named,
unknown ones rejected, the failing field named. Hand-written, not jsonschema: this runs under
an agent's own python3, which has no jsonschema (the kit's scripts stay standard-library-only:
AGENTS.md Rules).
"""

from __future__ import annotations

import json
import os
import platform
import secrets
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import cast

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


def result(answer: object, where: str, kind: str, key: str) -> object:
    """The answer's result[KEY], its envelope and type checked."""
    env = record(answer, where, ENVELOPE, {"result"})
    res = record(env["result"], f"{where}.result", {key, "type"}, {key, "type"})
    if res["type"] != kind:
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
        out.append(Pane(text(d, "pane_id", at), text(d, "tab_id", at), text(d, "workspace_id", at)))
    return out


def shell_pid(pane: str) -> int | None:
    """PANE's shell pid from `herdr pane process-info`; None when Herdr names none."""
    where = f"herdr pane process-info --pane {pane}"
    got = result(
        herdr("pane", "process-info", "--pane", pane), where, "pane_process_info", "process_info"
    )
    d = record(got, f"{where}: result.process_info", PROCESS_FIELDS, {"pane_id"})
    if d["pane_id"] != pane:
        msg = f"{where}: result.process_info.pane_id {d['pane_id']!r}, not {pane!r}"
        raise BadAnswerError(msg)
    pid = d.get("shell_pid")
    if pid is not None and (not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0):
        msg = f"{where}: result.process_info.shell_pid not a pid"
        raise BadAnswerError(msg)
    return pid


def scope_of(pid: int) -> str | None:
    """The agent scope PID runs in (its cgroup v2 path), or None: an unowned process, one gone,
    or no /proc (macOS). Owned: a scope named PREFIX* under this user's own systemd manager."""
    try:
        lines = Path(f"/proc/{pid}/cgroup").read_text().splitlines()
    except OSError:
        return None
    path = next((x[3:] for x in lines if x.startswith("0::")), "")
    name = path.rsplit("/", 1)[-1]
    mine = f"/user@{os.getuid()}.service/" in path
    return path if mine and name.startswith(PREFIX) and name.endswith(".scope") else None


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


def close(target: str) -> int:
    """Close TARGET through Herdr, then stop its panes' agent scopes (module docstring)."""
    kind = "tab" if ":" in target else "space"
    workspace = target.split(":", 1)[0]
    shown = [p for p in panes(workspace) if kind == "space" or p.tab_id == target]
    scopes: list[str] = []
    unowned: list[str] = []
    for p in shown:
        pid = shell_pid(p.pane_id)
        cg = scope_of(pid) if pid is not None else None
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
    sys.stdout.write(report + (f" unowned={','.join(unowned)}" if unowned else "") + "\n")
    return rc


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in ("adopt", "close"):  # noqa: PLR2004
        sys.stderr.write(__doc__ or "")
        return 64
    verb, arg = sys.argv[1:]
    who, after = (
        ("herdr-spawn", "not started") if verb == "adopt" else ("herdr-close", "nothing closed")
    )
    try:
        return adopt(arg) if verb == "adopt" else close(arg)
    except HerdrFailedError as e:
        sys.stderr.write(f"{who}: {e}; {after}\n")
        return e.rc
    except BadAnswerError as e:
        sys.stderr.write(f"{who}: malformed Herdr answer: {e}; {after}\n")
        return BAD_ANSWER


if __name__ == "__main__":
    sys.exit(main())
