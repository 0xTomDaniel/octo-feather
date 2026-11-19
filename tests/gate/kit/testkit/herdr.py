#!/usr/bin/env python3
"""Fake `herdr` (the testkit's stand-in for Herdr, which the kit does not own), as
testkit/qa_box.py's: a session's socket is a file under the config dir naming the session.

`server` writes it and sleeps; `session stop S` removes S's socket, `session delete S` its dir;
with no socket a call fails `server_not_running`; `pane list` prints nothing; `agent list` prints
no agent in Herdr's envelope; any other call prints
{"session": S}.
Its panes, one per workspace, as the qc sandbox's judge spawns one (#997): `workspace create`
prints a root pane, `pane run P CMD` starts CMD detached (sh -c, its own session) and logs P in
the session's dir, `pane list` prints each logged pane. FAKE_HERDR_LEAK set: once past `server`
and `session stop|delete`, every call answers the default session, as a Herdr reaching its live
server past every mask would.
Its one pane a prompt reaches, as the qa items' attempt cases need (#998): `agent prompt w9:ok ...`
prints {"result": "delivered"}; `agent prompt P ...` to any other P fails `pane_not_found: P`.

With FAKE_HERDR set, it stands for Herdr's agents instead (#666): a world in that dir, each call one
line in its `log`. `agents.json` maps each pane id to its agent, {name, pane_id, workspace_id,
tab_id, agent_status}, and `ready_at` (an epoch time: `unknown` until then, a Pi still booting);
a scenario may write it. `tab create --workspace W [--label L] [--env K=V]...` makes tab W:tN,
pane W:pN (N past every earlier tab's), keeping L and the env (its agent's `label`, `env`);
`workspace create --label L` makes workspace wN, N past every agent's workspace, its seed tab
made as a tab create's (Herdr's envelope: workspace.workspace_id, tab.tab_id);
`tab get T` prints T's label; `tab close T` drops T's agents; `workspace close W` drops W's agents,
`workspace get W` finds W while an agent is in it, with its tab count, as Herdr 0.9.5 prints it
(else workspace_not_found on stderr, exit 1, as does a close of it);
`agent start NAME --pane P -- ARGS` starts Pi NAME there, taking input the seconds
in the file `ready_after` later (0 without one), then reading the state in the file `start-status`
(idle without one). Until then Herdr reads it `unknown`, and from
IDLE_FALLBACK s after its start `idle` (Herdr 0.9.5's screen fallback; why that is not ready:
herdr-comms SKILL.md, Spawn an agent). Pi reports itself only when ARGS load Herdr's Pi
integration (`--extension F`, F the file `integration install pi` wrote): once it takes input,
`agent_session` (source herdr:pi).
`integration install pi` writes that file to $PI_CODING_AGENT_DIR/extensions (else
$HOME/.pi/agent/extensions); with no agent dir it fails, as Herdr does, and so with a file
`install-down` (`herdr: integration install failed`); a file `no-report` makes Pi never report.
`agent get T` (by name or pane), as Herdr 0.9.5 prints it:
found, the agent on stdout; else agent_not_found on stderr, exit 1; a file `get-down` makes it
fail plain (`herdr: server not reachable`, exit 1), for the targets it lists, one a line, or for
every target when it is empty; a file `get-delay` holding S makes it answer no sooner than S
seconds after the call (a slow Herdr). `agent wait T --until S... --timeout MS`
returns once T reads a state S, else `timeout`: at once when T has booted, as its state then never
changes. `agent prompt T TEXT --wait [--until S...]
[--timeout MS]`: blocked is `agent_blocked`, nothing sent; an agent not yet taking input gets
TEXT typed, unsent (a line in `typed`), `agent_prompt_stalled`; any other gets it submitted (a line
"PANE<TAB>TEXT" in `prompts`): an idle one turns working, then idle, so the wait matches; a
working one (busy, as #619 saw it) never matches, so the wait ends only at --timeout
(`timeout`), else never.
An agent holding `compacting_until` (an epoch time) is a Pi compacting until then: a prompt to it
is queued, not submitted (a line in `queued`), Herdr seeing no turn start (`agent_prompt_stalled`),
and `agent read` shows Pi's compaction line and each queued text as Pi does (`Steering: TEXT`);
once that time passed, the next call has Pi take each queued text (a line in `prompts`).
`pane list [--workspace W]` lists every pane, or W's ({pane_id, tab_id, workspace_id,
agent_status, terminal_id, focused, revision}: PaneInfo's required fields), as Herdr 0.9.5
does; `pane process-info --pane P` gives P's `shell_pid`: the agent's `shell_pid` a
scenario wrote (a real process standing in for the pane's shell), else a stand-in shell it starts
(a real process, ending once this world's dir is gone) and records, and as its one foreground
process the agent's `pi_pid` a scenario wrote (a real process standing in for its Pi: pid, name,
argv and cwd read from its /proc, as Herdr does), else none; `tab close` and `workspace
close` send each closed pane's shell SIGHUP, as Herdr's close does.
`pane read` shows a ready Pi prompt; `pane send-keys|send-text` log only. `agent list` prints every
agent in Herdr's envelope ({"id", "result": {"agents"}}), as `agent get` shows one, with AgentInfo's
other required fields (terminal_id, focused, revision) as `pane list` gives them; a file
`list-answer` holding JSON is printed as its answer instead (a malformed Herdr). A file `down`
fails every call as a herdr with no server does (`error: could not connect to herdr server`,
exit 1). Anything else exits 2.
"""

import contextlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

IDLE_FALLBACK = 0.3  # s: Herdr 0.9.5 reads a booting Pi idle after about 5 s; scaled down
# the world's own, never shown
HIDDEN = ("ready_at", "started_at", "reports", "label", "env", "shell_pid", "pi_pid")
INTEGRATION = "// installed by herdr\n// HERDR_INTEGRATION_ID=pi\n"  # the file Herdr writes


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
    def booting(g: dict[str, object]) -> bool:
        ready = g.get("ready_at")
        return isinstance(ready, (int, float)) and time.time() < ready

    @staticmethod
    def status(g: dict[str, object]) -> str:
        if World.booting(g):
            started = g.get("started_at")
            fell_back = isinstance(started, float) and time.time() >= started + IDLE_FALLBACK
            return "idle" if fell_back else "unknown"
        return str(g["agent_status"])

    @staticmethod
    def compacting(g: dict[str, object]) -> bool:
        until = g.get("compacting_until")
        return isinstance(until, (int, float)) and time.time() < until

    def settle(self) -> None:
        """Pi takes what it queued once its compaction ended: each queued text submitted."""
        q = self.dir / "queued"
        kept = list[str]()
        for x in q.read_text().splitlines() if q.exists() else []:
            g = self.agents.get(x.split("\t")[0])
            if g and self.compacting(g):
                kept.append(x)
            else:
                self.note("prompts", x)
        if q.exists():
            q.write_text("".join(f"{x}\n" for x in kept))

    def agent_read(self, a: list[str]) -> int:
        g = self.find(a[2])
        if g is None:
            return fail("agent_not_found")
        q = self.dir / "queued"
        pane = f"{g['pane_id']}\t"
        queued = q.read_text().splitlines() if q.exists() else []
        shown = [f"Steering: {x[len(pane) :]}" for x in queued if x.startswith(pane)]
        busy = ["Auto-compacting... (escape to cancel)"] if self.compacting(g) else []
        sys.stdout.write("\n".join([" pi", "", *busy, *shown, " > "]) + "\n")
        return 0

    def tab_create(self, a: list[str]) -> int:
        pane, tab = self.tab(opts(a, "--workspace")[0], a)
        return say({"tab": {"tab_id": tab}, "root_pane": {"pane_id": pane}})

    def tab(self, w: str, a: list[str]) -> tuple[str, str]:
        """A new tab in workspace W, its pane bare: their ids."""
        last = self.dir / "last_tab"  # Herdr never reuses a closed tab's number
        n = max(len(self.agents), int(last.read_text()) if last.exists() else 0) + 1
        last.write_text(str(n))
        pane, tab = f"{w}:p{n}", f"{w}:t{n}"
        self.agents[pane] = {"name": "", "pane_id": pane, "workspace_id": w, "tab_id": tab}
        self.agents[pane]["agent_status"] = "none"
        self.agents[pane]["label"] = next(iter(opts(a, "--label")), "")
        self.agents[pane]["env"] = dict(kv.split("=", 1) for kv in opts(a, "--env"))
        self.save()
        return pane, tab

    def workspace_create(self, a: list[str]) -> int:
        """`workspace create --label L ...`: workspace wN, N past every agent's, with a seed tab."""
        ws = [str(g["workspace_id"])[1:] for g in self.agents.values()]
        w = f"w{max((int(x) for x in ws if x.isdigit()), default=0) + 1}"
        _, tab = self.tab(w, a)
        return say({"workspace": {"workspace_id": w}, "tab": {"tab_id": tab}})

    def tab_get(self, a: list[str]) -> int:
        g = next((g for g in self.agents.values() if g["tab_id"] == a[2]), None)
        if g is None:
            return fail("tab_not_found")
        return say({"tab": {"tab_id": a[2], "label": g.get("label", "")}})

    def close(self, key: str, target: str) -> None:
        """The panes whose KEY is TARGET dropped, each one's shell sent SIGHUP."""
        for g in self.agents.values():
            pid = g.get("shell_pid")
            if g[key] == target and isinstance(pid, int):
                with contextlib.suppress(ProcessLookupError):
                    os.kill(pid, signal.SIGHUP)
        self.agents = {p: g for p, g in self.agents.items() if g[key] != target}
        self.save()

    def tab_close(self, a: list[str]) -> int:
        self.close("tab_id", a[2])
        return 0

    def pane_list(self, a: list[str]) -> int:
        w = opts(a, "--workspace")
        panes = [
            {k: g[k] for k in ("pane_id", "tab_id", "workspace_id")}
            | {"agent_status": self.status(g), "terminal_id": f"term_{g['pane_id']}"}
            | {"focused": False, "revision": 0}
            for g in self.agents.values()
            if not w or g["workspace_id"] == w[0]
        ]
        return say({"panes": panes, "type": "pane_list"})

    def process_info(self, a: list[str]) -> int:
        p = opts(a, "--pane")
        g = self.agents.get(p[0]) if p else None
        if g is None:
            return fail("pane_not_found")
        if not isinstance(g.get("shell_pid"), int):
            loop = 'i=0; while [ -d "$0" ] && [ $i -lt 600 ]; do sleep 1; i=$((i+1)); done'
            shell = subprocess.Popen(
                ["sh", "-c", loop, str(self.dir)],  # noqa: S607
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            g["shell_pid"] = shell.pid
            self.save()
        fg: list[object] = []
        pi = g.get("pi_pid")
        if isinstance(pi, int):
            proc = Path(f"/proc/{pi}")
            argv = proc.joinpath("cmdline").read_bytes().decode().split("\0")[:-1]
            name = proc.joinpath("comm").read_text().strip()
            cwd = str((proc / "cwd").readlink())
            fg.append({"pid": pi, "name": name, "argv": argv, "argv0": argv[0], "cwd": cwd})
        info = {"pane_id": p[0], "shell_pid": g["shell_pid"], "foreground_processes": fg}
        return say({"process_info": info, "type": "pane_process_info"})

    def workspace(self, a: list[str]) -> int:
        """`workspace get|close W`."""
        w = a[2]
        tabs = {g["tab_id"] for g in self.agents.values() if g["workspace_id"] == w}
        if not tabs:
            return fail("workspace_not_found")
        if a[1] == "get":
            info = {"workspace_id": w, "tab_count": len(tabs)}
            return say({"type": "workspace_info", "workspace": info})
        self.close("workspace_id", w)
        return 0

    def agent_start(self, a: list[str]) -> int:
        after = self.dir / "ready_after"
        delay = float(after.read_text()) if after.exists() else 0.0
        g = self.agents[opts(a, "--pane")[0]]
        ext = [Path(x) for x in opts(a[a.index("--") :] if "--" in a else [], "--extension")]
        reports = any(x.is_file() and x.read_text() == INTEGRATION for x in ext)
        reports = reports and not (self.dir / "no-report").exists()
        state = self.dir / "start-status"
        status = state.read_text().strip() if state.exists() else "idle"
        now = time.time()
        g |= {"name": a[2], "agent_status": status, "ready_at": now + delay, "started_at": now}
        g["reports"] = reports
        self.save()
        return 0

    def integration_install(self, a: list[str]) -> int:
        if (self.dir / "install-down").exists():
            sys.stderr.write("herdr: integration install failed\n")
            return 1
        if a[2:] != ["pi"]:
            sys.stderr.write(f"fake herdr: unhandled: {' '.join(a)}\n")
            return 2
        agent_dir = Path(os.environ.get("PI_CODING_AGENT_DIR") or Path.home() / ".pi" / "agent")
        if not agent_dir.is_dir():
            sys.stderr.write(f"pi extension directory not found at {agent_dir / 'extensions'}\n")
            return 1
        f = agent_dir / "extensions" / "herdr-agent-state.ts"
        f.parent.mkdir(exist_ok=True)
        f.write_text(INTEGRATION)
        sys.stdout.write(f"installed pi integration to {f}\n")
        return 0

    def agent_get(self, a: list[str]) -> int:
        down = self.dir / "get-down"
        if down.exists() and a[2] in (down.read_text().split() or [a[2]]):
            sys.stderr.write("herdr: server not reachable\n")
            return 1
        delay = self.dir / "get-delay"
        if delay.exists():
            time.sleep(float(delay.read_text()))
        g = self.find(a[2])
        if g is None:
            return fail("agent_not_found")
        out = {k: v for k, v in g.items() if k not in HIDDEN} | {"agent_status": self.status(g)}
        if g.get("reports") and not self.booting(g):
            out["agent_session"] = {"source": "herdr:pi", "agent": "pi", "kind": "id", "value": "s"}
        return say({"agent": out, "type": "agent_info"})

    def agent_wait(self, a: list[str]) -> int:
        g = self.find(a[2])
        if g is None:
            return fail("agent_not_found")
        until = opts(a, "--until") or ["idle", "done", "blocked"]
        ms = opts(a, "--timeout")
        end = time.time() + int(ms[0]) / 1000 if ms else float("inf")
        while self.status(g) not in until:
            if time.time() >= end or not self.booting(g):
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
        if self.compacting(g):
            self.note("queued", f"{g['pane_id']}\t{a[3]}")
            return fail("agent_prompt_stalled")
        if self.booting(g):
            self.note("typed", f"{g['pane_id']}\t{a[3]}")
            return fail("agent_prompt_stalled")
        self.note("prompts", f"{g['pane_id']}\t{a[3]}")
        if s == "working" and "--wait" in a:
            ms = opts(a, "--timeout")
            time.sleep(int(ms[0]) / 1000 if ms else 3600)
            return fail("timeout")
        return say({"agent_status": "idle"})

    def agent_list(self) -> int:
        told = self.dir / "list-answer"
        if told.exists():
            sys.stdout.write(told.read_text() + "\n")
            return 0
        agents = [
            {k: v for k, v in g.items() if k not in HIDDEN}
            | {"agent_status": self.status(g), "terminal_id": f"term_{g['pane_id']}"}
            | {"focused": False, "revision": 0}
            for g in self.agents.values()
        ]
        sys.stdout.write(json.dumps({"id": "1", "result": {"agents": agents}}) + "\n")
        return 0

    def call(self, a: list[str]) -> int:
        """One call A, logged."""
        self.note("log", " ".join(a))
        if (self.dir / "down").exists():
            sys.stderr.write("error: could not connect to herdr server\n")
            return 1
        self.settle()
        if a == ["agent", "list"]:
            return self.agent_list()
        two = (a[0], a[1]) if len(a) > 1 else (" ".join(a), "")
        if two == ("pane", "read"):
            sys.stdout.write(" pi\n\n > \n")
            return 0
        if two in (("pane", "send-keys"), ("pane", "send-text")):
            return 0
        verbs = {
            ("tab", "create"): self.tab_create,
            ("tab", "close"): self.tab_close,
            ("tab", "get"): self.tab_get,
            ("pane", "list"): self.pane_list,
            ("pane", "process-info"): self.process_info,
            ("workspace", "close"): self.workspace,
            ("workspace", "get"): self.workspace,
            ("workspace", "create"): self.workspace_create,
            ("agent", "start"): self.agent_start,
            ("agent", "get"): self.agent_get,
            ("agent", "wait"): self.agent_wait,
            ("agent", "prompt"): self.agent_prompt,
            ("agent", "read"): self.agent_read,
            ("integration", "install"): self.integration_install,
        }
        if two not in verbs:
            sys.stderr.write(f"fake herdr: unhandled: {' '.join(a)}\n")
            return 2
        return verbs[two](a)


home = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "herdr"
session, a = "default", list[str]()
it = iter(sys.argv[1:])
for x in it:
    if x == "--session":
        session = next(it, "default")
    elif x in ("--remote", "--machine"):
        next(it, None)
    else:
        a.append(x)
if os.environ.get("FAKE_HERDR"):
    sys.exit(World(Path(os.environ["FAKE_HERDR"])).call(a))
sock = home / "herdr.sock" if session == "default" else home / "sessions" / session / "herdr.sock"
if a == ["server"]:
    sock.parent.mkdir(parents=True, exist_ok=True)
    sock.write_text(session + "\n")
    os.execvp("sleep", ["sleep", "600"])  # noqa: S606, S607
if a[:2] == ["session", "stop"] and len(a) == 3:
    (home / "sessions" / a[2] / "herdr.sock").unlink(missing_ok=True)
    sys.exit(0)
if a[:2] == ["session", "delete"] and len(a) == 3:
    shutil.rmtree(home / "sessions" / a[2], ignore_errors=True)
    sys.exit(0)
if os.environ.get("FAKE_HERDR_LEAK"):
    sys.stdout.write(json.dumps({"session": "default"}) + "\n")
    sys.exit(0)
if not sock.is_file():
    sys.exit("server_not_running")
if a[:2] == ["workspace", "create"]:
    sys.stdout.write(json.dumps({"result": {"root_pane": {"pane_id": "w1:p1"}}}) + "\n")
    sys.exit(0)
if a[:2] == ["pane", "run"] and len(a) > 3:
    with (sock.parent / "panes").open("a") as f:
        f.write(json.dumps({"pane_id": a[2]}) + "\n")
    io = subprocess.DEVNULL
    cmd = ["sh", "-c", " ".join(a[3:])]
    subprocess.Popen(cmd, stdin=io, stdout=io, stderr=io, start_new_session=True)
    sys.exit(0)
if a == ["pane", "list"] and (sock.parent / "panes").is_file():
    sys.stdout.write((sock.parent / "panes").read_text())
    sys.exit(0)
if a[:2] == ["agent", "prompt"] and len(a) > 2:  # its one pane a prompt reaches (docstring)
    if a[2] != "w9:ok" or len(a) == 3:
        sys.exit(f"pane_not_found: {a[2]}")
    sys.stdout.write(json.dumps({"result": "delivered"}) + "\n")
    sys.exit(0)
if a == ["agent", "list"]:
    sys.stdout.write(json.dumps({"id": "1", "result": {"agents": []}}) + "\n")
elif a != ["pane", "list"]:
    sys.stdout.write(json.dumps({"session": sock.read_text().strip()}) + "\n")
