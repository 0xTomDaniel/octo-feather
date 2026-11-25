#!/usr/bin/env python3
"""octo-feather-start's director relaunch (comms spec #director-relaunch; #1310), and the
one-session check every `octo-feather-start --director --resume` runs. octo-feather-start (its
header) runs this file; the rule, its refusals and who runs it from where: comms spec
#director-relaunch.

held SESSION: exit 73 naming each pane, when a live Pi in Herdr holds SESSION (its agent_session
in `herdr agent list`, or `--session-id SESSION` in its pane's foreground argv); else 0.

relaunch --cwd DIR --wait SECONDS [--resume SESSION] [--operating-model FILE]: the director
named by director.toml's `pane` (OLD) relaunched on its own session in a new pane, in order:

1. Refused, nothing changed: HERDR_PANE_ID is OLD, or this process sits in OLD's own agent scope
   (herdr_scope.scope_of of OLD's shell), exit 64: a run there ends with the pane it replaces.
2. The session: OLD's herdr-spawn Pi's `--session-id` (as park reads it); OLD gone (no pane
   Herdr knows), --resume SESSION's, else refused 65. A --resume naming another session than
   OLD's refused 64. Resumed in OLD's Pi's cwd, else DIR.
3. Refused 73: a live Pi other than OLD holds the session (held, above).
4. The wait, never an interrupt: OLD read idle or done SETTLE_READS times in a row, SETTLE_GAP s
   apart (as the 2026-11-25 hand script read it), within SECONDS; else refused 75 naming it busy.
5. `herdr-close --park OLD`: refused, its own exit and refusal, nothing else done (no plain close
   fallback: one killed the 2026-11-25 hand script with the scope).
6. No Pi holds the session any more, else exit 1, nothing spawned.
7. `octo-feather-start --director --resume SESSION --cwd CWD`: its line printed (the new pane=);
   it lands a new tab in workspace `director` (a new workspace when the park closed it with its
   only tab) and repoints director.toml.
8. The new pane told once: OLD, the session, and the director log's path (herdr-say).
9. Checks on the real artifacts: `herdr agent get director` answers the new pane, director.toml's
   `pane` names it, and one Pi (it) holds the session; each failing one named on stderr, exit 1.

A Herdr answer that fails or breaks its shape stops it: Herdr's exit, or 76 (herdr_scope.py).
Standard library only (AGENTS.md Rules, kit scripts); Herdr read through herdr_scope.py's readers.
"""

from __future__ import annotations

import argparse
import importlib.machinery
import importlib.util
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, cast

import tomllib

KIT = Path(__file__).resolve().parent.parent
ASSETS = KIT / ".agents" / "skills" / "herdr-comms" / "assets"
SETTLE_READS = 4
SETTLE_GAP = 15  # s
ME = "octo-feather-start"


def _load(name: str, path: Path) -> Any:  # noqa: ANN401 (a kit file loaded by path: untyped)
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    assert spec
    mod = sys.modules[name] = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


scope = _load("herdr_scope", ASSETS / "herdr_scope.py")


class RefusedError(Exception):
    def __init__(self, rc: int, why: str) -> None:
        super().__init__(why)
        self.rc = rc


def holds(answer: object, at: str, session: str) -> bool:
    """An AgentInfo's agent_session (Herdr's AgentSessionInfo, or null) names SESSION: its id, or
    a Pi session file `<time>_<SESSION>.jsonl`."""
    if answer is None:
        return False
    keys = {"source", "agent", "kind", "value"}
    d = scope.record(answer, f"{at}.agent_session", keys, keys)
    value = scope.text(d, "value", f"{at}.agent_session")
    return value == session or Path(value).name.endswith(f"_{session}.jsonl")


def holders(session: str, but: str = "") -> list[str]:
    """The panes, BUT aside, whose live Pi holds SESSION (module docstring, held)."""
    where = "herdr agent list"
    got = scope.result(scope.herdr("agent", "list"), where, "agent_list", "agents", typed=False)
    if not isinstance(got, list):
        msg = f"{where}: result.agents not a list"
        raise scope.BadAnswerError(msg)
    out: list[str] = []
    for i, v in enumerate(cast("list[object]", got)):
        at = f"{where}: result.agents[{i}]"
        d = scope.record(v, at, scope.AGENT_FIELDS, scope.AGENT_REQUIRED)
        pane = scope.text(d, "pane_id", at)
        if pane == but:
            continue
        if holds(d.get("agent_session"), at, session):
            out.append(pane)
            continue
        info = process_info(pane)
        got_pi = scope.pi_session(info) if info else None
        if got_pi and got_pi[1] == session:
            out.append(pane)
    return out


def process_info(pane: str) -> Any:  # noqa: ANN401 (herdr_scope.ProcessInfo, loaded by path)
    """PANE's process info, None once Herdr knows no such pane."""
    try:
        return scope.process_info(pane)
    except scope.HerdrFailedError as e:
        if "not_found" in str(e):
            return None
        raise


def state() -> Path:
    run = [str(KIT / "scripts" / "octo-feather-state")]
    return Path(subprocess.run(run, capture_output=True, text=True, check=True).stdout.strip())


def recorded_pane(toml: Path) -> str:
    """director.toml's `pane`, '' with no file or no key."""
    if not toml.is_file():
        return ""
    try:
        pane = tomllib.loads(toml.read_text(encoding="utf-8")).get("pane", "")
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
        raise RefusedError(65, f"{toml} does not parse as TOML ({e})") from e
    return pane if isinstance(pane, str) else ""


def status(pane: str) -> str:
    """PANE's agent_status as `herdr pane list` reads it (as park reads it), '' once gone."""
    shown = scope.panes(pane.split(":", 1)[0])
    return next((p.agent_status for p in shown if p.pane_id == pane), "")


def settle(old: str, wait: int) -> None:
    """Return once OLD reads idle or done SETTLE_READS times in a row, SETTLE_GAP s apart; refused
    75 when WAIT s pass first (module docstring, 4)."""
    end = time.monotonic() + wait
    calm, now = 0, ""
    while True:
        now = status(old)
        if not now:
            why = f"the director at pane {old} left Herdr during the wait"
            raise RefusedError(75, f"{why}; rerun with --resume SESSION")
        calm = calm + 1 if now in ("idle", "done") else 0
        if calm >= SETTLE_READS:
            return
        left = end - time.monotonic()
        if left <= 0:
            why = f"the director at pane {old} is busy (last read {now}): not idle or done for"
            why += f" {SETTLE_READS} reads {SETTLE_GAP} s apart within --wait {wait} s; its turn"
            raise RefusedError(75, f"{why} is never interrupted. Retry once it is idle")
        time.sleep(min(SETTLE_GAP, left))


def relaunch(args: argparse.Namespace) -> int:
    """The relaunch (module docstring); a refusal before the park done names nothing changed."""
    toml = state() / "director.toml"
    try:
        live, session, cwd = prepare(args, toml)
    except RefusedError as e:
        raise RefusedError(e.rc, f"{e}; nothing changed") from e
    return after(args, toml, live, session, cwd)


def prepare(args: argparse.Namespace, toml: Path) -> tuple[str, str, str]:
    """Steps 1 to 5 (module docstring): the parked director's pane ('' for none), the session
    and the cwd to resume in."""
    old = recorded_pane(toml)
    outside = "run it from outside the director's pane: the owner's shell, or another agent's pane"
    if old and os.environ.get("HERDR_PANE_ID") == old:
        raise RefusedError(64, f"this run's HERDR_PANE_ID is the director's pane {old}; {outside}")
    info = process_info(old) if old else None
    session, cwd = cast("str", args.resume or ""), cast("str", args.cwd)
    if info is not None:
        own = scope.scope_of(info.shell_pid, old) if info.shell_pid is not None else None
        if own and scope.scope_of(os.getpid(), old) == own:
            unit = own.rsplit("/", 1)[-1]
            why = f"this run sits in the director pane {old}'s agent scope {unit}, so it would end"
            raise RefusedError(64, f"{why} with the pane it replaces; {outside}")
        got = scope.pi_session(info)
        if got is None or scope.environ(got[0].pid).get("OCTO_FEATHER_SESSION_ID") != got[1]:
            raise RefusedError(65, f"no herdr-spawn Pi session in the director's pane {old}")
        if session and session != got[1]:
            why = f"--resume {session}, but the director at pane {old} runs session {got[1]}"
            raise RefusedError(64, why)
        session, cwd = got[1], got[0].cwd or cwd
    elif not session:
        where = f"director.toml's pane {old}" if old else f"{toml} names no pane and"
        raise RefusedError(65, f"{where} runs no director; give --resume SESSION")
    live = old if info is not None else ""
    held = holders(session, live)
    if held:
        why = f"a live Pi in pane {', '.join(held)} holds session {session}; one director runs a"
        raise RefusedError(73, f"{why} session")
    if live:
        settle(live, cast("int", args.wait))
        rc = subprocess.run([str(ASSETS / "herdr-close"), "--park", live], check=False).returncode
        if rc != 0:
            why = f"herdr-close --park {live} refused (exit {rc}, above); the director runs on, no"
            raise RefusedError(rc, f"{why} plain close tried")
    return live, session, cwd


def after(args: argparse.Namespace, toml: Path, live: str, session: str, cwd: str) -> int:
    """Steps 6 to 9 (module docstring), once the old director is parked or was gone."""
    held: list[str] = []
    for _ in range(10):
        held = holders(session)
        if not held:
            break
        time.sleep(1)
    if held:
        why = f"parked {live}, but pane {', '.join(held)} still holds session {session}; nothing"
        raise RefusedError(1, f"{why} resumed")
    start = [str(KIT / "scripts" / "octo-feather-start"), "--director", "--resume", session]
    model = cast("str", args.operating_model)
    start += ["--cwd", cwd, *(["--operating-model", model] if model else [])]
    ran = subprocess.run(start, stdout=subprocess.PIPE, text=True, check=False)
    line = ran.stdout.strip().splitlines()[-1] if ran.stdout.strip() else ""
    new = next((x[5:] for x in line.split() if x.startswith("pane=")), "")
    if ran.returncode != 0 or not new:
        why = f"parked {live or 'nothing'}, but the resume did not start (exit {ran.returncode},"
        raise RefusedError(ran.returncode or 1, f"{why} above); rerun: {' '.join(start)}")
    sys.stdout.write(line + "\n")
    sys.stdout.flush()
    at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    was = f"replacing pane {live}" if live else "the previous director already gone"
    told = f"Relaunched ({was}, session {session}) as pane={new} at {at}; director log:"
    told += f" {toml.with_name('director.handoffs.jsonl')}"
    fails: list[str] = []
    if subprocess.run([str(ASSETS / "herdr-say"), new, told], check=False).returncode != 0:
        fails.append(f"the relaunch message to {new} not delivered (herdr-say above)")
    fails += checks(new, session, toml)
    for f in fails:
        sys.stderr.write(f"{ME}: relaunch check failed: {f}\n")
    return 1 if fails else 0


def checks(new: str, session: str, toml: Path) -> list[str]:
    """The checks on the real artifacts (module docstring, 9): each failing one, named."""
    fails: list[str] = []
    try:
        where = "herdr agent get director"
        answer = scope.herdr("agent", "get", "director")
        got = scope.found(answer, where, "agent", scope.AGENT_FIELDS, "pane_id")
        if got != new:
            fails.append(f"{where} answers pane {got}, not {new}")
    except (scope.HerdrFailedError, scope.BadAnswerError) as e:
        fails.append(f"herdr agent get director: {e}")
    try:
        pane = recorded_pane(toml)
    except RefusedError as e:
        pane = str(e)
    if pane != new:
        fails.append(f"{toml} names pane {pane or '(none)'}, not {new}")
    held = holders(session)
    if held != [new]:
        fails.append(f"session {session} held by {held or 'no pane'}, not by {new} alone")
    return fails


def held(session: str) -> int:
    """held SESSION (module docstring)."""
    panes = holders(session)
    if panes:
        why = f"a live Pi in pane {', '.join(panes)} holds session {session}"
        raise RefusedError(73, f"{why}; one agent runs a session: nothing started")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="director_relaunch.py", description=__doc__)
    verbs = parser.add_subparsers(dest="verb", required=True)
    verbs.add_parser("held").add_argument("session")
    r = verbs.add_parser("relaunch")
    r.add_argument("--cwd", required=True)
    r.add_argument("--wait", type=int, required=True)
    r.add_argument("--resume", default="")
    r.add_argument("--operating-model", default="")
    args = parser.parse_args()
    try:
        return held(cast("str", args.session)) if args.verb == "held" else relaunch(args)
    except RefusedError as e:
        sys.stderr.write(f"{ME}: refused: {e}\n")
        return e.rc
    except scope.HerdrFailedError as e:
        sys.stderr.write(f"{ME}: {e}\n")
        return cast("int", e.rc)
    except scope.BadAnswerError as e:
        sys.stderr.write(f"{ME}: malformed Herdr answer: {e}\n")
        return cast("int", scope.BAD_ANSWER)


if __name__ == "__main__":
    sys.exit(main())
