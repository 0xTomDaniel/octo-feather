"""The scenario of tests/gate/kit/test_pi_role.py (its item), this file its command
(testkit.main): scripts/pi-role's launch, run directly.

externalSkills: looked up in the target repo's .agents/skills (the main checkout's, seen from a
lane worktree), never home; a missing one warned (`--json`, no Pi). #77: a headless run (-p or
--print) drops the parent route and Herdr's ids, a pane launch keeps them. #261: in a repo with its
own mise.toml, mise's shims dir (mise's own answer) goes just before the caller PATH's first
system dir, the caller's earlier dirs still first; in a repo without one, or with no mise on PATH,
PATH is left as it was. What pi was started with is read through real Pi (the kit's pin, as
installed) against the fake provider (testkit/provider.py): its scripted turn has Pi run `env` as
a tool, and the tool's result, Pi's own environment as its tools see it (Pi puts its agent dir's
bin first on PATH), reaches the provider's log. One launch proves each headless or pane fact and
a PATH fact together. #175 (roles#launch-codemode, roles#acceptance-codemode-every-role), #262
(roles#launch-web): each role's tools and web servers (`--json`). #175 (roles#fm-tools):
check-roles refuses a role listing codemode, naming the file."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from contextlib import ExitStack
from pathlib import Path

from testkit import ROOT, Scratch, asked, kit, main, provider, real_pi, tool_homes

TAG = "pi-role test"
ROUTE = {
    "OCTO_FEATHER_PARENT": "fake:p1",
    "HERDR_PANE_ID": "fake:p0",
    "HERDR_TAB_ID": "fake:t0",
    "HERDR_WORKSPACE_ID": "fake",
}
RO, RW = "read,grep,find,ls,bash,codemode", "read,grep,find,ls,bash,edit,write,codemode"
WEB = ",mcp__parallel__*,mcp__exa__*;web"
TOOLS = {
    "director": RO + WEB,
    "code-reviewer": RO + WEB,
    "qc-judge": RO + ";--no-mcp",
    "supervisor": RW + ";--no-mcp",
    "implementer": RW + WEB,
    "corrector": RW + WEB,
    "shaper": RW + WEB,
}


def skills(s: Scratch, t: Path) -> Path:
    """externalSkills from a lane worktree; the worktree, gh1."""
    home = t / "home2"
    (home / ".agents" / "skills" / "spec-chat-review").mkdir(parents=True)
    (home / ".agents" / "skills" / "spec-chat-review" / "SKILL.md").write_text("# home\n")
    repo = t / "repo"
    s.git(t, "-c", "init.defaultBranch=main", "init", "-q", str(repo))
    (repo / ".gitignore").write_text(".agents/skills/spec-chat-*\n")
    s.git(repo, "add", "-A")
    s.git(repo, "commit", "-qm", "init")
    gh1 = t / "gh1"
    s.git(repo, "worktree", "add", "-q", "-b", "gh1", str(gh1))
    (repo / ".agents" / "skills" / "spec-chat-shape").mkdir(parents=True)
    (repo / ".agents" / "skills" / "spec-chat-shape" / "SKILL.md").write_text("# repo\n")
    sup = str(ROOT / "agents" / "supervisor.md")
    r = s.run([kit("pi-role"), "--json", sup], cwd=gh1, env={"HOME": str(home)})
    want = f'"{repo}/.agents/skills/spec-chat-shape"'
    assert want in r.out, f"{TAG}: repo skill not found from the lane worktree: {r.out}"
    assert f"{home}/.agents" not in r.out, f"{TAG}: a home skill loaded: {r.out}"
    assert "external skill spec-chat-review not installed" in r.err, f"{TAG}: no warning: {r.err}"
    return gh1


def tools(s: Scratch, gh1: Path) -> None:
    for role, want in TOOLS.items():
        a: list[str] = json.loads(
            s.run([kit("pi-role"), "--json", str(ROOT / "agents" / f"{role}.md")], cwd=gh1).out
        )["args"]
        t = a[a.index("--tools") + 1] if "--tools" in a else "none"
        if "--no-mcp" in a:
            how = "--no-mcp"
        else:
            how = (
                "web"
                if a[a.index("--octo-feather-web-servers") + 1].endswith("/web-mcp.json")
                else "?"
            )
        assert f"{t};{how}" == want, f"{TAG}: {role} --tools is {t};{how}, want {want}"


def check_roles(s: Scratch, t: Path) -> None:
    """A fixture kit: the real scripts and skills, a director whose tools list codemode."""
    k = t / "kit"
    (k / "scripts").mkdir(parents=True)
    for f in ("check-roles", "pi-role"):
        shutil.copy2(ROOT / "scripts" / f, k / "scripts")
    shutil.copytree(ROOT / "agents", k / "agents")
    shutil.copy(ROOT / "web-mcp.json", k)
    (k / ".agents").mkdir()
    (k / ".agents" / "skills").symlink_to(ROOT / ".agents" / "skills")
    d = k / "agents" / "director.md"
    lines = d.read_text().splitlines(keepends=True)
    d.write_text(
        "".join(
            "tools: read, grep, find, ls, bash, codemode\n" if ln.startswith("tools: ") else ln
            for ln in lines
        )
    )
    r = s.run([str(k / "scripts" / "check-roles")], want=1)
    said = r.err
    assert "agents/director.md: " in said, f"{TAG}: check-roles did not name the file: {said}"
    assert "`codemode`" in said, f"{TAG}: check-roles did not name codemode: {said}"
    assert "pi-role adds it" in said, f"{TAG}: check-roles: {said}"


class Pi:
    """Real pi launched through pi-role against the fake provider: the env its tools see."""

    def __init__(self, s: Scratch, stack: ExitStack) -> None:
        self.s, t = s, s.root.resolve()
        self.t, self.agent, self.log = t, t / "agent", t / "requests.jsonl"
        self.agent.mkdir()
        port = stack.enter_context(provider("--log", str(self.log)))
        fake = {
            "baseUrl": f"http://127.0.0.1:{port}/v1",
            "api": "openai-completions",
            "apiKey": "x",
            "models": [{"id": "fake"}],
        }
        (self.agent / "models.json").write_text(json.dumps({"providers": {"fake": fake}}) + "\n")
        # The caller's earlier dirs: pi and node (pi's interpreter) found here first, as a stub pi
        # was before; PATHs below fixed, so an empty entry in the caller's cannot change them.
        self.bin = t / "callerbin"
        self.bin.mkdir()
        pi = Path(real_pi(TAG, pinned=False)).resolve()
        (self.bin / "pi").symlink_to(pi)
        (self.bin / "node").symlink_to(Path(shutil.which("node") or "node").resolve())

    def env(self, cwd: Path, path: str, *flags: str, **extra: str) -> dict[str, str]:
        """pi-role implementer FLAGS in CWD, PATH, the route and EXTRA set: the env its Pi's
        tools see, from the provider's log."""
        self.log.write_text("")
        env = {
            "PATH": path,
            "HOME": str(self.s.home),
            "TMPDIR": str(self.t),
            "XDG_STATE_HOME": str(self.t / "state"),
            "XDG_CACHE_HOME": str(self.t / "cache"),
            "PI_CODING_AGENT_DIR": str(self.agent),
            "PI_OFFLINE": "1",
            "PI_SKIP_VERSION_CHECK": "1",
            "PI_TELEMETRY": "0",
            "MISE_DATA_DIR": tool_homes()["MISE_DATA_DIR"],  # mise's own, as the caller's
            **ROUTE,
            **extra,
        }
        cmd = [kit("pi-role"), str(ROOT / "agents" / "implementer.md"), "--model", "fake/fake"]
        p = subprocess.run(
            [*cmd, "--no-session", *flags],
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        assert p.returncode == 0, f"{TAG}: pi-role {flags}: exit {p.returncode}: {p.stderr}"
        for line in self.log.read_text().splitlines():
            for m in json.loads(line)["messages"]:
                if m.get("role") == "tool":
                    c = m["content"]
                    text = c if isinstance(c, str) else "".join(x.get("text", "") for x in c)
                    pairs = (ln.partition("=") for ln in text.splitlines() if "=" in ln)
                    return {k: v for k, _, v in pairs}
        msg = f"{TAG}: pi-role {flags}: no tool result reached the provider: {p.stdout} {p.stderr}"
        raise AssertionError(msg)


def pi_role(s: Scratch) -> None:
    t = s.root.resolve()
    s.env["XDG_STATE_HOME"] = str(t / "state")
    s.identity()  # the commit identity a role launch needs (#665)
    gh1 = skills(s, t)
    tools(s, gh1)
    check_roles(s, t)
    with ExitStack() as stack:
        pi = Pi(s, stack)
        b, ask = str(pi.bin), "PROVIDER-BASH: env"
        first = f"{pi.agent}/bin"  # Pi's own first PATH dir for its tools
        made = t / "made"
        s.git(t, "init", "-q", str(made))
        (made / "mise.toml").write_text("[tools]\n")
        mbin = t / "mbin"
        mbin.mkdir()
        mise = shutil.which("mise")
        assert mise, f"{TAG}: mise not on PATH"
        (mbin / "mise").symlink_to(mise)
        shims = json.loads(asked("mise", "doctor", "--json"))["dirs"]["shims"]
        sysdirs = "/usr/local/bin:/usr/bin:/bin"
        # -p in a mise.toml repo: no route, and mise's shims before the system dirs.
        e = pi.env(made, f"{b}:{mbin}:{sysdirs}", "-p", ask)
        for v in ROUTE:
            assert v not in e, f"{TAG}: headless (-p) child has {v}={e[v]}"
        want = f"{first}:{b}:{mbin}:{shims}:{sysdirs}"
        assert e["PATH"] == want, f"{TAG}: -p in a mise.toml repo: PATH {e['PATH']}, want {want}"
        # --print with no mise on PATH: no route, PATH as it was.
        e = pi.env(made, f"{b}:/usr/bin:/bin", "--print", ask)
        for v in ROUTE:
            assert v not in e, f"{TAG}: headless (--print) child has {v}={e[v]}"
        want = f"{first}:{b}:/usr/bin:/bin"
        assert e["PATH"] == want, f"{TAG}: without mise: PATH {e['PATH']}, want {want}"
        # A pane launch (not -p) in a repo without mise.toml: the route kept, PATH as it was.
        caller = f"{b}:{os.environ['PATH']}"
        e = pi.env(gh1, caller, "--mode", "json", ask)
        for v, val in ROUTE.items():
            assert e.get(v) == val, f"{TAG}: pane launch child lacks {v}={val}: {e.get(v)}"
        assert e["PATH"] == f"{first}:{caller}", f"{TAG}: no mise.toml: PATH changed: {e['PATH']}"


if __name__ == "__main__":
    main(pi_role)
