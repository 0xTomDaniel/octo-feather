#!/usr/bin/env -S python3 -I -S
"""Fake `herdr` (the testkit's stand-in for Herdr, which the kit does not own), as
tests/lib/qa.sh's: a session's socket is a file under the config dir naming the session.

`server` writes it and sleeps; `session stop S` removes S's socket, `session delete S` its dir;
with no socket a call fails `server_not_running`; `agent list` prints no agent in Herdr's envelope
(Herdr 0.9.5's form); one pane per workspace (as tests/lib/qc.sh's): `workspace
create` answers root pane w1:p1, `pane run P CMD...` starts CMD detached (as the server would) and
logs {"pane_id": P} beside the socket, which `pane list` prints (nothing before a run); any other
call prints {"session": S}.

With FAKE_HERDR set, it stands for Herdr's agents instead (#666): a world in that dir, each call one
line in its `log`. `agents.json` maps each pane id to its agent, {name, pane_id, workspace_id,
tab_id, agent_status}, and `ready_at` (an epoch time: `unknown` until then, a Pi still booting);
a scenario may write it. `tab create --workspace W` makes tab W:tN, pane W:pN; `tab close T` drops
T's agents; `agent start NAME --pane P` starts NAME there, ready (idle) the seconds in the file
`ready_after` later (0 without one). `agent get T` (by name or pane), as Herdr 0.9.5 prints it:
found, the agent on stdout; else agent_not_found on stderr, exit 1; a file `get-down` makes it
fail plain (`herdr: server not reachable`, exit 1). `agent wait T --until S... --timeout MS`
returns once T reads a state S, else `timeout`. `agent prompt T TEXT --wait [--until S...]
[--timeout MS]`: blocked is `agent_blocked`, nothing sent; a booting agent gets TEXT typed,
unsent (a line in `typed`), `agent_prompt_stalled`; any other gets it submitted (a line
"PANE<TAB>TEXT" in `prompts`): an idle one turns working, then idle, so the wait matches; a
working one (busy, as #619 saw it) never matches, so the wait ends only at --timeout
(`timeout`), else never.
`workspace get W` finds W while an agent's pane is in it, else workspace_not_found;
`workspace close W` drops W's agents (workspace_not_found when none); `workspace create --label
L` makes the next space W with its seed tab W:t1 (a bare pane, no agent), `workspace list` lists
each space by its label. `agent list` prints every agent, in the order the world holds them, in
Herdr's envelope; a file `down` fails every call as a herdr with no server does. `pane read`
shows a ready Pi prompt; `pane send-keys|send-text` log only. Anything else exits 2.

Started light (-I -S, only os and sys imported up front): a qc run calls it dozens of times, and
each start is CPU the item pays (#672): pathlib's import alone costs more than the rest of a call.
"""
# ruff: noqa: PTH103, PTH108, PTH111, PTH113, PTH118, PTH120, PTH123  # os.path, not pathlib: above

from __future__ import annotations

import os
import sys


def fail(code: str, rc: int = 1) -> int:
    sys.stderr.write(json.dumps({"error": {"code": code, "message": code}}) + "\n")
    return rc


def opts(a: list[str], flag: str) -> list[str]:
    return [a[i + 1] for i, x in enumerate(a[:-1]) if x == flag]


def say(d: object) -> int:
    sys.stdout.write(json.dumps({"result": d}) + "\n")
    return 0


class World:
    """The agents world in a dir (the module docstring)."""

    def __init__(self, d: Path) -> None:
        self.dir, self.store = d, d / "agents.json"
        self.agents: dict[str, dict[str, object]] = (
            json.loads(self.store.read_text()) if self.store.exists() else {}
        )

    def save(self) -> None:
        self.store.write_text(json.dumps(self.agents))

    def note(self, name: str, line: str) -> None:
        with (self.dir / name).open("a") as f:
            f.write(line + "\n")

    def find(self, t: str) -> dict[str, object] | None:
        """The started agent T names, by pane or name."""
        g = next((g for p, g in self.agents.items() if t in (p, g["name"])), None)
        return g if g and g["name"] else None

    @staticmethod
    def status(g: dict[str, object]) -> str:
        ready = g.get("ready_at")
        if isinstance(ready, (int, float)) and time.time() < ready:
            return "unknown"
        return str(g["agent_status"])

    def tab_create(self, a: list[str]) -> int:
        w, n = opts(a, "--workspace")[0], len(self.agents) + 1
        pane, tab = f"{w}:p{n}", f"{w}:t{n}"
        self.agents[pane] = {"name": "", "pane_id": pane, "workspace_id": w, "tab_id": tab}
        self.agents[pane]["agent_status"] = "none"
        self.save()
        return say({"tab": {"tab_id": tab}, "root_pane": {"pane_id": pane}})

    def tab_close(self, a: list[str]) -> int:
        self.agents = {p: g for p, g in self.agents.items() if g["tab_id"] != a[2]}
        self.save()
        return 0

    def workspace_create(self, a: list[str]) -> int:
        w = f"w{len({g['workspace_id'] for g in self.agents.values()}) + 1}"
        label = (opts(a, "--label") or [w])[0]
        self.agents[f"{w}:p1"] = {"name": "", "pane_id": f"{w}:p1", "workspace_id": w}
        self.agents[f"{w}:p1"] |= {"tab_id": f"{w}:t1", "agent_status": "none", "label": label}
        self.save()
        return say({"workspace": {"workspace_id": w}, "tab": {"tab_id": f"{w}:t1"}})

    def workspace_list(self, _: list[str]) -> int:
        spaces: dict[str, object] = {}
        for g in self.agents.values():
            spaces.setdefault(str(g["workspace_id"]), g.get("label", g["workspace_id"]))
        return say({"workspaces": [{"workspace_id": w, "label": n} for w, n in spaces.items()]})

    def workspace_get(self, a: list[str]) -> int:
        if not any(g["workspace_id"] == a[2] for g in self.agents.values()):
            return fail("workspace_not_found")
        return say({"type": "workspace_info", "workspace": {"workspace_id": a[2]}})

    def workspace_close(self, a: list[str]) -> int:
        kept = {p: g for p, g in self.agents.items() if g["workspace_id"] != a[2]}
        if len(kept) == len(self.agents):
            return fail("workspace_not_found")
        self.agents = kept
        self.save()
        return 0

    def agent_start(self, a: list[str]) -> int:
        after = self.dir / "ready_after"
        delay = float(after.read_text()) if after.exists() else 0.0
        g = self.agents[opts(a, "--pane")[0]]
        g |= {"name": a[2], "agent_status": "idle", "ready_at": time.time() + delay}
        self.save()
        return 0

    def agent_get(self, a: list[str]) -> int:
        if (self.dir / "get-down").exists():
            sys.stderr.write("herdr: server not reachable\n")
            return 1
        g = self.find(a[2])
        if g is None:
            return fail("agent_not_found")
        out = {k: v for k, v in g.items() if k != "ready_at"} | {"agent_status": self.status(g)}
        return say({"agent": out, "type": "agent_info"})

    def agent_wait(self, a: list[str]) -> int:
        g = self.find(a[2])
        if g is None:
            return fail("agent_not_found")
        until = opts(a, "--until") or ["idle", "done", "blocked"]
        ms = opts(a, "--timeout")
        end = time.time() + int(ms[0]) / 1000 if ms else float("inf")
        while self.status(g) not in until:
            if time.time() >= end:
                return fail("timeout")
            time.sleep(0.05)
        return say({"agent_status": self.status(g)})

    def agent_prompt(self, a: list[str]) -> int:
        g = self.find(a[2])
        if g is None:
            return fail("agent_not_found")
        s = self.status(g)
        if s == "blocked":
            return fail("agent_blocked")
        if s == "unknown":
            self.note("typed", f"{g['pane_id']}\t{a[3]}")
            return fail("agent_prompt_stalled")
        self.note("prompts", f"{g['pane_id']}\t{a[3]}")
        if s == "working" and "--wait" in a:
            ms = opts(a, "--timeout")
            time.sleep(int(ms[0]) / 1000 if ms else 3600)
            return fail("timeout")
        return say({"agent_status": "idle"})

    def call(self, a: list[str]) -> int:
        """One call A, logged."""
        self.note("log", " ".join(a))
        if (self.dir / "down").exists():
            sys.stderr.write("error: could not connect to herdr server\n")
            return 1
        if a == ["agent", "list"]:
            shown = [{k: v for k, v in g.items() if k != "ready_at"} for g in self.agents.values()]
            sys.stdout.write(json.dumps({"id": "1", "result": {"agents": shown}}) + "\n")
            return 0
        two = (a[0], a[1]) if len(a) > 1 else (" ".join(a), "")
        if two == ("pane", "read"):
            sys.stdout.write(" pi\n\n > \n")
            return 0
        if two in (("pane", "send-keys"), ("pane", "send-text")):
            return 0
        verbs = {
            ("tab", "create"): self.tab_create,
            ("tab", "close"): self.tab_close,
            ("workspace", "get"): self.workspace_get,
            ("workspace", "create"): self.workspace_create,
            ("workspace", "list"): self.workspace_list,
            ("workspace", "close"): self.workspace_close,
            ("agent", "start"): self.agent_start,
            ("agent", "get"): self.agent_get,
            ("agent", "wait"): self.agent_wait,
            ("agent", "prompt"): self.agent_prompt,
        }
        if two not in verbs:
            sys.stderr.write(f"fake herdr: unhandled: {' '.join(a)}\n")
            return 2
        return verbs[two](a)


home = os.path.join(
    os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config"), "herdr"
)
session, a = "default", list[str]()
it = iter(sys.argv[1:])
for x in it:
    if x == "--session":
        session = next(it, "default")
    elif x in ("--remote", "--machine"):
        next(it, None)
    else:
        a.append(x)
if os.environ.get("FAKE_HERDR"):  # the agents world: its imports only here, the lean start kept
    import json
    import time
    from pathlib import Path

    sys.exit(World(Path(os.environ["FAKE_HERDR"])).call(a))
sock = (
    os.path.join(home, "herdr.sock")
    if session == "default"
    else os.path.join(home, "sessions", session, "herdr.sock")
)
if a == ["server"]:
    os.makedirs(os.path.dirname(sock), exist_ok=True)
    with open(sock, "w") as f:
        f.write(session + "\n")
    os.execvp("sleep", ["sleep", "600"])  # noqa: S606, S607
if a[:2] == ["session", "stop"] and len(a) == 3:
    stale = os.path.join(home, "sessions", a[2], "herdr.sock")
    if os.path.lexists(stale):
        os.unlink(stale)
    sys.exit(0)
if a[:2] == ["session", "delete"] and len(a) == 3:
    import shutil

    shutil.rmtree(os.path.join(home, "sessions", a[2]), ignore_errors=True)
    sys.exit(0)
if not os.path.isfile(sock):
    sys.exit("server_not_running")
panes = os.path.join(os.path.dirname(sock), "panes")
if a[:2] == ["workspace", "create"]:
    sys.stdout.write('{"result":{"root_pane":{"pane_id":"w1:p1"}}}\n')
    sys.exit(0)
if a[:2] == ["pane", "run"] and len(a) > 3:
    with open(panes, "a") as f:
        f.write(f'{{"pane_id":"{a[2]}"}}\n')
    import subprocess

    subprocess.Popen(
        ["setsid", "sh", "-c", " ".join(a[3:])],  # noqa: S607
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    sys.exit(0)
if a == ["pane", "list"]:
    if os.path.isfile(panes):
        with open(panes) as f:
            sys.stdout.write(f.read())
elif a == ["agent", "list"]:
    sys.stdout.write('{"id": "1", "result": {"agents": []}}\n')
else:
    with open(sock) as f:
        name = f.read().strip()
    if '"' in name or "\\" in name or not (name.isascii() and name.isprintable()):
        import json

        sys.stdout.write(json.dumps({"session": name}) + "\n")
    else:  # as json.dumps writes it, without its import
        sys.stdout.write(f'{{"session": "{name}"}}\n')
