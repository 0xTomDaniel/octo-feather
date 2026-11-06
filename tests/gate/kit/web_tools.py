"""The scenarios of tests/gate/kit/test_web_tools.py (its items), this file their command
(testkit.main): a role's `web` tool (issue #262; spec roles#launch-web, roles#roles-web,
roles#fm-tools). Real Pi, at the kit's pin (pi-version), launched headless through a copy of the
kit whose web-mcp.json names stub stdio MCP servers (testkit/mcp_stub.py: the
hosted search servers' stand-in, no network) and one unreachable server, against testkit's fake
model provider (testkit/provider.py) on 127.0.0.1. The provider logs each request and answers the
first with one codemode call listing ALL_TOOLS, so a run reads both the tools declared to the
model and the tools a codemode script reaches. The user Pi config and the target repo's
.pi/mcp.json each name another stub server.

  roles      roles#acceptance-web-roles, roles#acceptance-web-no-other-mcp,
             roles#acceptance-director-tools: each role's declared and codemode tools are exactly
             its role file's tools plus codemode, plus every listed server's tools for a role
             listing web; no role has a tool of the user's or the project's server; supervisor
             and qc judge none of MCP
  list-once  roles#acceptance-web-list-once: the list holds a second server and an unreachable
             one, the copy's role files the kit's own (compared): the second reaches every web
             role and no other, and the unreachable one leaves each role starting with the other
             servers' tools. One list for every run, so each role's launch proves both cases
  check      check-roles accepts `web` and still rejects an unknown tool

Each Pi launch is most of an item's CPU, so the roles are split in three items. The fixture kit
(the real pi-role and check-roles, roles and extensions, the real skills linked, the stub list;
pi-role takes the kit from the role file's dir) is prepared once per gate run (Scratch.prepare),
the pin checked there. Never skips: without pi at the pin it fails naming the install
command.
"""

from __future__ import annotations

import filecmp
import json
import os
import re
import subprocess
import sys

from testkit import HERE, ROOT, Scratch, main

PIN = (ROOT / "pi-version").read_text().strip()
INSTALL = f"npm install -g --ignore-scripts @earendil-works/pi-coding-agent@{PIN}"
RO = ("bash", "find", "grep", "ls", "read")
RW = ("bash", "edit", "find", "grep", "ls", "read", "write")
WEB = tuple(f"mcp__{n}__{t}" for n in ("webstub", "second") for t in ("fetch", "search"))
# Each role, its role file's tools, and whether it lists web.
ROLES = {
    "director": (RO, True),
    "code-reviewer": (RO, True),
    "implementer": (RW, True),
    "corrector": (RW, True),
    "shaper": (RW, True),
    "supervisor": (RW, False),
    "qc-judge": (RO, False),
}
CODE = 'return "TOOLS:" + ALL_TOOLS.map(t => t.name).join(" ")'


def stub(name: str) -> dict[str, object]:
    """NAME's entry in an mcp.json: the stub server listing search and fetch."""
    return {"command": sys.executable, "args": [str(HERE / "mcp_stub.py"), name, "search", "fetch"]}


def servers(**entries: dict[str, object]) -> str:
    return json.dumps({"mcpServers": entries})


def build(p: Scratch) -> None:
    """The real pi at the pin, else fail naming the install (once per gate run). P/kit: the kit's
    pi-role and check-roles, its agents and extensions, its skills linked, the web list naming
    webstub, second and an unreachable server; P/repo, a git repo whose .pi/mcp.json names
    projonly; P/agent, Pi's user dir whose mcp.json names useronly; the commit identity set."""
    import shutil  # noqa: PLC0415 (only the build copies)

    pi_at_pin()
    k = p.root / "kit"
    (k / ".agents").mkdir(parents=True)
    (k / "scripts").mkdir()
    for d in ("agents", "extensions"):
        shutil.copytree(ROOT / d, k / d, symlinks=True)
    for f in ("pi-role", "check-roles"):  # check-roles asks its own dir's pi-role
        shutil.copy2(ROOT / "scripts" / f, k / "scripts" / f)
    (k / ".agents" / "skills").symlink_to(ROOT / ".agents" / "skills")
    dead: dict[str, object] = {"url": "http://127.0.0.1:9/mcp"}
    (k / "web-mcp.json").write_text(
        servers(webstub=stub("webstub"), second=stub("second"), dead=dead)
    )
    (p.root / "agent").mkdir()
    (p.root / "agent" / "mcp.json").write_text(servers(useronly=stub("useronly")))
    (p.root / "repo" / ".pi").mkdir(parents=True)
    (p.root / "repo" / ".pi" / "mcp.json").write_text(servers(projonly=stub("projonly")))
    p.run(["git", "-c", "init.defaultBranch=main", "init", "-q", str(p.root / "repo")])
    p.identity()


def pi_at_pin() -> None:
    """The real pi on the caller's PATH reports the kit's pin, else fail naming the install."""
    v = subprocess.run(
        ["pi", "--version"],  # noqa: S607 (the caller's pi, as pi-role execs it)
        capture_output=True,
        text=True,
        check=False,
        env=os.environ,
    )
    got = re.search(r"\d+\.\d+\.\d+", v.stdout + v.stderr)
    said = got.group() if got else "no version"
    assert said == PIN, f"pi reports {said}, the kit pins {PIN} (pi-version); {INSTALL}"


class World:
    """The prepared fixture in a scratch and the fake provider serving it."""

    def __init__(self, s: Scratch) -> None:
        s.prepare("web-tools", build)
        self.s, self.log = s, s.root / "provider.log"
        self.p = subprocess.Popen(
            [sys.executable, str(HERE / "provider.py"), str(self.log), CODE],
            stdout=subprocess.PIPE,
            text=True,
        )
        assert self.p.stdout
        port = self.p.stdout.readline().strip()  # readiness off the provider's own pipe
        assert port.isdigit(), "the fake provider did not start"
        models = {
            "providers": {
                "fake": {
                    "baseUrl": f"http://127.0.0.1:{port}/v1",
                    "api": "openai-completions",
                    "apiKey": "x",
                    "models": [{"id": "fake"}],
                }
            }
        }
        (s.root / "agent" / "models.json").write_text(json.dumps(models))

    def close(self) -> None:
        self.p.kill()
        self.p.wait()

    def run(self, role: str) -> tuple[list[str], list[str]]:
        """ROLE started headless in the repo: the tools declared to the model and those its
        codemode script reached, each sorted."""
        s, r = self.s, self.s.root
        self.log.write_text("")
        env = {
            "PATH": os.environ["PATH"],  # the real pi, never testkit's stand-in
            "HOME": str(s.home),
            "TMPDIR": str(r / "tmp"),
            "XDG_CACHE_HOME": str(r / "cache"),
            "PI_CODING_AGENT_DIR": str(r / "agent"),
            "PI_OFFLINE": "1",
            "PI_SKIP_VERSION_CHECK": "1",
            "PI_TELEMETRY": "0",
        }
        cmd = [str(r / "kit" / "scripts" / "pi-role"), str(r / "kit" / "agents" / f"{role}.md")]
        p = subprocess.run(
            [*cmd, "--model", "fake/fake", "--no-session", "-p", "go"],
            cwd=r / "repo",
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert p.returncode == 0, f"{role}: pi-role exited {p.returncode}: {p.stderr}"
        assert "fake-done" in p.stdout, f"{role}: no answer after the codemode call: {p.stdout}"
        reqs = [json.loads(ln) for ln in self.log.read_text().splitlines()]
        declared = sorted(t["function"]["name"] for t in reqs[0].get("tools", []))
        said = [m["content"] for q in reqs for m in q["messages"] if m["role"] == "tool"]
        assert said, f"{role}: no tool result reached the provider"
        text = said[0] if isinstance(said[0], str) else " ".join(x.get("text", "") for x in said[0])
        found = re.search(r"TOOLS:(.*)", text)
        assert found, f"{role}: the codemode result lists no tools: {text}"
        return declared, sorted(found.group(1).split())


def roles(s: Scratch, *names: str) -> None:
    """Each role NAMES: declared tools exactly codemode, its role file's and, listing web, every
    reachable listed server's; codemode reaches the same less itself (the module docstring)."""
    w = World(s)
    try:
        cmp = filecmp.dircmp(ROOT / "agents", s.root / "kit" / "agents")
        differ = [*cmp.diff_files, *cmp.left_only, *cmp.right_only]
        assert not differ, f"list-once: the fixture's role files differ from the kit's: {differ}"
        for role in names:
            tools, web = ROLES[role]
            want = sorted((*tools, *(WEB if web else ())))
            declared, reached = w.run(role)
            assert declared == sorted(("codemode", *want)), (
                f"{role}: declared {declared}, want codemode, {want}"
            )
            assert reached == want, f"{role}: codemode reaches {reached}, want {want}"
    finally:
        w.close()


def web_read_roles(s: Scratch) -> None:
    """The read-only web roles: director and code reviewer."""
    roles(s, "director", "code-reviewer")


def web_write_roles(s: Scratch) -> None:
    """The web roles that write: implementer, corrector, shaper."""
    roles(s, "implementer", "corrector", "shaper")


def no_web_roles(s: Scratch) -> None:
    """The roles not listing web: supervisor and qc judge; then check-roles on the copy."""
    roles(s, "supervisor", "qc-judge")
    check(s)


def check(s: Scratch) -> None:
    """check-roles accepts web (the real roles) and still rejects an unknown tool, naming it."""
    k = s.root / "kit"
    s.run([str(k / "scripts" / "check-roles")])
    director = k / "agents" / "director.md"
    text = re.sub(
        r"^tools: .*$",
        "tools: read, grep, find, ls, bash, web, websearch",
        director.read_text(),
        count=1,
        flags=re.MULTILINE,
    )
    director.write_text(text)
    r = s.run([str(k / "scripts" / "check-roles")], want=1)
    assert "agents/director.md: unknown tool `websearch`" in r.out + r.err, r


if __name__ == "__main__":
    main(web_read_roles, web_write_roles, no_web_roles)
