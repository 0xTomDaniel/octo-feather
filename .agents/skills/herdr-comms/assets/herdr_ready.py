#!/usr/bin/env python3
"""herdr_ready.py PANE NAME: wait until the Pi agent NAME just started in PANE takes prompts.

herdr-spawn's readiness step; what ready means and why: herdr-comms SKILL.md, Spawn an agent.
One bound, HERDR_SPAWN_READY_TIMEOUT seconds (default 120), covers the whole wait: the report
poll (Herdr has no wait on agent_session), then `herdr agent wait --until idle` with what is
left of it. Exit 0 ready; exit 69 not ready, the cause on stderr. Closing the tab is the
caller's.
"""

import json
import os
import subprocess
import sys
import time
from typing import cast

POLL = 0.2  # s between reads of the report


def herdr(*args: str, merge: bool = False) -> subprocess.CompletedProcess[str]:
    err = subprocess.STDOUT if merge else subprocess.PIPE
    cmd = ["herdr", *args]
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=err, text=True, check=False)


def agent(out: str) -> dict[str, object]:
    try:
        got: object = json.loads(out)["result"]["agent"]
    except (ValueError, KeyError, TypeError):
        return {}
    return cast("dict[str, object]", got) if isinstance(got, dict) else {}


def reported(pane: str) -> bool:
    session = agent(herdr("agent", "get", pane).stdout).get("agent_session")
    return (
        isinstance(session, dict) and cast("dict[str, object]", session).get("source") == "herdr:pi"
    )


def main() -> int:
    if len(sys.argv) != 3:  # noqa: PLR2004
        sys.stderr.write(__doc__ or "")
        return 64
    pane, name = sys.argv[1:]
    bound = int(os.environ.get("HERDR_SPAWN_READY_TIMEOUT") or 120)
    end = time.monotonic() + bound

    def fail(cause: str) -> int:
        sys.stderr.write(f"herdr-spawn: agent {name} (pane {pane}) {cause}\n")
        return 69

    while not reported(pane):
        if time.monotonic() >= end:
            report = "Herdr's Pi integration, agent_session"
            return fail(
                f"never reported to Herdr within {bound}s ({report}); not ready for prompts"
            )
        time.sleep(POLL)
    left_ms = max(1, int((end - time.monotonic()) * 1000))
    waited = herdr("agent", "wait", pane, "--until", "idle", "--timeout", str(left_ms))
    if waited.returncode != 0:
        if waited.stderr:
            sys.stderr.write(waited.stderr.rstrip("\n") + "\n")
        state = agent(herdr("agent", "get", pane).stdout).get("agent_status") or "unknown"
        return fail(
            f"not idle within {bound}s (herdr agent wait; state {state}); not ready for prompts"
        )
    for t in (name, pane):
        found = herdr("agent", "get", t, merge=True).stdout
        if agent(found).get("pane_id") != pane:
            last = found.rstrip("\n").rsplit("\n", 1)[-1]
            sys.stderr.write(f"herdr-spawn: herdr agent get {t} does not find pane {pane}")
            sys.stderr.write(f" ({last})\n")
            return 69
    return 0


if __name__ == "__main__":
    sys.exit(main())
