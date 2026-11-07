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
`tab create` also writes the tab's environment (each --env KEY=VALUE, one per line) to `tab-env`,
`agent start` its Pi argv (after --, one per line) to `start-argv`, `tab close` each tab id to
`closed`; `tab get T` prints T's label (its agent's name). `pane read` shows a ready Pi prompt,
or a startup dialog while one is open (exit 0, the text of tests/fixtures/herdr-spawn/'s): Pi's
trust dialog when the start argv lacks --approve or the file `dialog` says `pi`, another that
never clears when it says `other`; while a dialog is open `agent start` answers
`agent_not_ready` (exit 1), as Herdr does. Each read is a line in `reads`; a file `reads_ok`
holding N fails every read after the first N (exit 42, a line in `failed-reads`). `pane
send-keys|send-text` log their key in `keys`. A `get-down` file naming targets (one per line)
fails only those. Workspaces (a start's):
`workspace create --label L` makes the next wN with its seed tab wN:t0 (`workspaces.json`, a
scenario may write it), `workspace list` lists them; `workspace get W` finds W while it is
listed or an agent's pane is in it, else workspace_not_found; `workspace close W` drops W and its
agents (workspace_not_found when there is no W); `session list` prints Herdr's table: `default`
running, and each name in the file `sessions` running. `agent list` prints every agent, in the
order the world holds them, in Herdr's envelope; a file `down` fails every call as a herdr with
no server does. Each call is also one line in `session-log`, "HERDR_SESSION=<the caller's>
CALL". Anything else exits 2.

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
        (self.dir / "tab-env").write_text("".join(f"{e}\n" for e in opts(a, "--env")))
        return say({"tab": {"tab_id": tab}, "root_pane": {"pane_id": pane}})

    def tab_close(self, a: list[str]) -> int:
        self.note("closed", a[2])
        self.agents = {p: g for p, g in self.agents.items() if g["tab_id"] != a[2]}
        self.save()
        return 0

    def workspace_get(self, a: list[str]) -> int:
        listed = any(w["workspace_id"] == a[2] for w in self.workspaces())
        if not listed and not any(g["workspace_id"] == a[2] for g in self.agents.values()):
            return fail("workspace_not_found")
        return say({"type": "workspace_info", "workspace": {"workspace_id": a[2]}})

    def workspace_close(self, a: list[str]) -> int:
        spaces, f = self.workspaces(), self.dir / "workspaces.json"
        left = [w for w in spaces if w["workspace_id"] != a[2]]
        kept = {p: g for p, g in self.agents.items() if g["workspace_id"] != a[2]}
        if len(left) == len(spaces) and len(kept) == len(self.agents):
            return fail("workspace_not_found")
        if len(left) != len(spaces):
            f.write_text(json.dumps(left))
        self.agents = kept
        self.save()
        return 0

    def agent_start(self, a: list[str]) -> int:
        after = self.dir / "ready_after"
        delay = float(after.read_text()) if after.exists() else 0.0
        g = self.agents[opts(a, "--pane")[0]]
        g |= {"name": a[2], "agent_status": "idle", "ready_at": time.time() + delay}
        self.save()
        if "--" in a:
            argv = a[a.index("--") + 1 :]
            (self.dir / "start-argv").write_text("".join(f"{x}\n" for x in argv))
        return fail("agent_not_ready") if self.dialog() else 0

    def dialog(self) -> str:
        """The startup dialog open in the pane: `pi`, `other`, or none (the module docstring)."""
        f, argv = self.dir / "dialog", self.dir / "start-argv"
        if f.exists():
            return f.read_text().strip()
        if argv.exists() and "--approve" not in argv.read_text().splitlines():
            return "pi"
        return ""

    def pane_read(self, _: list[str]) -> int:
        self.note("reads", "x")
        ok = self.dir / "reads_ok"
        n = len((self.dir / "reads").read_text().splitlines())
        if ok.exists() and n > int(ok.read_text()):
            self.note("failed-reads", "x")
            return 42
        shown = {"pi": "pi-trust-dialog.txt", "other": "other-dialog.txt"}.get(self.dialog())
        fixtures = Path(__file__).resolve().parents[3] / "fixtures" / "herdr-spawn"
        sys.stdout.write((fixtures / shown).read_text() if shown else " pi\n\n > \n")
        return 0

    def tab_get(self, a: list[str]) -> int:
        g = next((g for g in self.agents.values() if g["tab_id"] == a[2]), None)
        if g is None:
            return fail("tab_not_found")
        return say({"tab": {"tab_id": a[2], "label": g["name"]}})

    def agent_get(self, a: list[str]) -> int:
        down = self.dir / "get-down"
        if down.exists() and (not down.read_text().split() or a[2] in down.read_text().split()):
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

    def workspaces(self) -> list[dict[str, str]]:
        f = self.dir / "workspaces.json"
        return json.loads(f.read_text()) if f.exists() else []

    def workspace(self, a: list[str]) -> int:
        spaces, f = self.workspaces(), self.dir / "workspaces.json"
        if a[1] == "list":
            return say({"workspaces": spaces})
        if a[1] == "close":
            return self.workspace_close(a)
        w = f"w{len(spaces) + 1}"
        f.write_text(json.dumps([*spaces, {"label": opts(a, "--label")[0], "workspace_id": w}]))
        return say({"workspace": {"workspace_id": w}, "tab": {"tab_id": f"{w}:t0"}})

    def sessions(self) -> int:
        f = self.dir / "sessions"
        names = f.read_text().split() if f.exists() else []
        rows = ["name status directory socket", "default running /d /d.sock"]
        sys.stdout.write("\n".join(rows + [f"{n} running /s /s.sock" for n in names]) + "\n")
        return 0

    def session_list(self, _: list[str]) -> int:
        return self.sessions()

    def agent_list(self, _: list[str]) -> int:
        shown = [{k: v for k, v in g.items() if k != "ready_at"} for g in self.agents.values()]
        sys.stdout.write(json.dumps({"id": "1", "result": {"agents": shown}}) + "\n")
        return 0

    def call(self, a: list[str]) -> int:
        """One call A, logged."""
        self.note("log", " ".join(a))
        who = os.environ.get("HERDR_SESSION", "")
        self.note("session-log", f"HERDR_SESSION={who} {' '.join(a)}")
        if (self.dir / "down").exists():
            sys.stderr.write("error: could not connect to herdr server\n")
            return 1
        if a[:1] == ["workspace"] and a[1:2] in (["list"], ["create"], ["close"]):
            return self.workspace(a)
        two = (a[0], a[1]) if len(a) > 1 else (" ".join(a), "")
        if two in (("pane", "send-keys"), ("pane", "send-text")):
            self.note("keys", a[3] if len(a) > 3 else "")
            return 0
        verbs = {
            ("session", "list"): self.session_list,
            ("tab", "create"): self.tab_create,
            ("tab", "close"): self.tab_close,
            ("tab", "get"): self.tab_get,
            ("pane", "read"): self.pane_read,
            ("workspace", "get"): self.workspace_get,
            ("agent", "list"): self.agent_list,
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
