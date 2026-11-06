"""The scenarios of tests/gate/kit/test_skills_loaded.py (its items), this file their command
(testkit.main): the launch's side of spec skills#loading-refuse
(skills#acceptance-launch-refuses-unloaded, skills#acceptance-only-listed; #558). Real Pi (the
kit's pin, pi-version, as installed), started through scripts/pi-role against the fake provider
(testkit/provider.py), which logs each request; each start settled (testkit.settled): it returns
only once Pi and every process it left (the extension's detached herdr-say) have exited. One
start proves every case it can: ok and own copy share one, declared and the three unresolved
entries another, each skill named with its reason on its own line. Cases:
  ok          (`kit_skills`) the implementer starts in a target declaring a good repo skill: the
              request offers every skill its role file lists (tdd, python, typescript among them)
              and not the declared one; the code-reviewer is offered tdd
  own copy    (`kit_skills`) the target declares a skill the role lists from its own copy: the role
              starts, offered it once, that copy
  listed      (`kit_skills`) a listed kit skill whose description is invalid YAML (in a copy of the
              kit's scripts, roles, extensions, web list and skills): pi-role exits non-zero naming
              the skill and Pi's reason, and the provider saw no request (implementer and
              code-reviewer)
  declared    (`repo_skills`) the same for a skill the target's AGENTS.md declares on its Repo
              skills: line
  unresolved  (`repo_skills`) a declared entry with no folder, a dangling link or a folder with no
              SKILL.md: the same refusal, naming the skill and why
  parent      (`repo_skills`) a pane launch (no -p, OCTO_FEATHER_PARENT set) tells the parent
              through the kit's herdr-say --parent: Herdr (the testkit's stand-in, its agents
              world, the parent pane w9:p9 idle) gets exactly one prompt, to w9:p9, naming the
              role and the skill
No call leaves the test: every start runs from an empty environment (no Herdr or parent route but
the parent case's own OCTO_FEATHER_PARENT); every start with no parent route reaches Herdr not
once. Never skips: without pi at the pin it fails naming the install command."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from contextlib import ExitStack
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from testkit import HERE, ROOT, Scratch, kit, main, provider, real_pi, settled

if TYPE_CHECKING:
    from pathlib import Path

TAG = "skills-loaded test"
GOOD = '---\nname: local\ndescription: "A local skill: fine when quoted."\n---\nBody.\n'
BAD = "---\nname: {}\ndescription: A broken skill: plain value holding a colon.\n---\nBody.\n"
YAML = "Nested mappings are not allowed"
DECLARED = "# target\n\nRepo skills: python, local\n"
ASSETS = ROOT / ".agents" / "skills" / "herdr-comms" / "assets"


@dataclass
class Started:
    rc: int
    out: str
    err: str
    requests: list[dict[str, Any]]


class World:
    """A target repo declaring python and its own good skill `local`, the fake provider, Herdr's
    stand-in world (parent pane w9:p9 idle), and the kit whose pi-role starts each role."""

    def __init__(self, s: Scratch, stack: ExitStack, kit_dir: Path = ROOT) -> None:
        self.s, self.kit, self.pi = s, kit_dir, real_pi(TAG, pinned=False)
        r = s.root
        self.tgt = r / "target"
        (self.tgt / ".agents" / "skills" / "local").mkdir(parents=True)
        s.git(r, "-c", "init.defaultBranch=main", "init", "-q", str(self.tgt))
        (self.tgt / "AGENTS.md").write_text(DECLARED)
        self.local(GOOD)
        for d in ("agent", "cache", "hbin", "herdr"):
            (r / d).mkdir()
        (r / "hbin" / "herdr").symlink_to(HERE / "herdr.py")
        parent = {
            "name": "supervisor",
            "pane_id": "w9:p9",
            "workspace_id": "w9",
            "tab_id": "w9:t9",
            "agent_status": "idle",
            "ready_at": 0,
        }
        (r / "herdr" / "agents.json").write_text(json.dumps({"w9:p9": parent}))
        # The commit identity a role launch needs (#665).
        s.run(
            [kit("pi-role"), "--set-identity", "t", "t@t"], env={"XDG_STATE_HOME": str(r / "state")}
        )
        self.log = r / "requests.jsonl"
        port = stack.enter_context(provider("--log", str(self.log), "--answer", "fake-done"))
        fake = {
            "baseUrl": f"http://127.0.0.1:{port}/v1",
            "api": "openai-completions",
            "apiKey": "x",
            "models": [{"id": "fake"}],
        }
        (r / "agent" / "models.json").write_text(json.dumps({"providers": {"fake": fake}}) + "\n")

    def local(self, text: str) -> None:
        (self.tgt / ".agents" / "skills" / "local" / "SKILL.md").write_text(text)

    def start(self, role: str, *args: str, parent: str = "") -> Started:
        """pi-role ROLE ARGS in the target, private home, settled; the provider's requests."""
        r = self.s.root
        self.log.write_text("")
        env = {
            "PATH": os.pathsep.join([str(r / "hbin"), str(ASSETS), os.environ["PATH"]]),
            "HOME": str(self.s.home),
            "TMPDIR": str(r),
            "XDG_CACHE_HOME": str(r / "cache"),
            "PI_CODING_AGENT_DIR": str(r / "agent"),
            "PI_OFFLINE": "1",
            "PI_SKIP_VERSION_CHECK": "1",
            "PI_TELEMETRY": "0",
            "XDG_STATE_HOME": str(r / "state"),
            "FAKE_HERDR": str(r / "herdr"),  # the stand-in's world, not a route to a pane
        } | ({"OCTO_FEATHER_PARENT": parent} if parent else {})
        cmd = [str(self.kit / "scripts" / "pi-role"), str(self.kit / "agents" / f"{role}.md")]
        p = subprocess.run(
            settled([*cmd, "--model", "fake/fake", "--no-session", *args]),
            cwd=self.tgt,
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        reqs = [json.loads(ln) for ln in self.log.read_text().splitlines()]
        return Started(p.returncode, p.stdout, p.stderr, reqs)

    def no_herdr(self) -> None:
        """Herdr reached by no start so far (the stand-in logs every call)."""
        log = self.s.root / "herdr" / "log"
        assert not log.exists(), (
            f"{TAG}: a start with no parent route called Herdr: {log.read_text()}"
        )


def offered(st: Started) -> list[str]:
    """The skill names the first request's system prompt offers, sorted."""
    m: str | list[dict[str, str]] = st.requests[0]["messages"][0]["content"]
    text = m if isinstance(m, str) else " ".join(p.get("text", "") for p in m)
    return sorted(re.findall(r"<name>([^<]+)</name>", text))


def listed(role: str) -> list[str]:
    """The skills ROLE's role file lists (its skills: line), {tracker} the GitHub one."""
    head = (ROOT / "agents" / f"{role}.md").read_text()
    line = re.search(r"(?m)^skills: *(.*)$", head)
    assert line, role
    return sorted(x.strip().replace("{tracker}", "github-issues") for x in line.group(1).split(","))


def refused(what: str, st: Started, why: dict[str, str]) -> None:
    """ST exited non-zero before any request, its stderr naming each skill of WHY with its reason
    on that skill's own line."""
    assert st.rc != 0, f"{TAG}: {what}: pi-role exited 0 with a skill Pi cannot load"
    lines = st.err.splitlines()
    for skill, reason in why.items():
        hit = [ln for ln in lines if f"Pi did not load skill {skill} (" in ln]
        assert hit, f"{TAG}: {what}: stderr does not name {skill}: {st.err}"
        assert reason in hit[0], f"{TAG}: {what}: {skill} lacks the reason {reason}: {st.err}"
    assert not st.requests, f"{TAG}: {what}: the provider saw {len(st.requests)} request(s)"


def started(what: str, st: Started) -> None:
    assert st.rc == 0, f"{TAG}: {what}: did not start: rc={st.rc} {st.err}"
    assert "fake-done" in st.out, f"{TAG}: {what}: no answer: {st.out} {st.err}"


def kit_skills(s: Scratch) -> None:
    """ok and own copy on one start each role, then listed, from a copy of the kit (kit_copy)."""
    with ExitStack() as stack:
        w = World(s, stack, kit_copy(s))
        # ok and own copy at once: the target holds its own copy of a skill the role lists and
        # declares it (the kit's own repo, #595): the role starts, offered exactly its listed
        # skills (that one once, the target's copy), not the declared repo skill `local`.
        own = w.tgt / ".agents" / "skills" / "python"
        own.mkdir()
        shutil.copy(ROOT / ".agents" / "skills" / "python" / "SKILL.md", own)
        st = w.start("implementer", "-p", "go")
        started("ok", st)
        want = listed("implementer")
        assert {"tdd", "python", "typescript"} <= set(want), want
        assert "local" not in want, want
        assert offered(st) == want, f"{TAG}: ok: implementer offered {offered(st)}, lists {want}"
        path = str(own.resolve() / "SKILL.md")
        assert path in json.dumps(st.requests[0]), f"{TAG}: own copy: python not from {path}"
        st = w.start("code-reviewer", "-p", "go")
        assert "tdd" in offered(st), f"{TAG}: ok: code-reviewer not offered tdd: {offered(st)}"
        # listed: the kit's tdd broken; both roles listing it refuse.
        (w.kit / ".agents" / "skills" / "tdd" / "SKILL.md").write_text(BAD.format("tdd"))
        refused("listed (implementer)", w.start("implementer", "-p", "go"), {"tdd": YAML})
        refused("listed (code-reviewer)", w.start("code-reviewer", "-p", "go"), {"tdd": YAML})
        w.no_herdr()


def kit_copy(s: Scratch) -> Path:
    """The kit's scripts, roles, extensions and web list, its skills a copy, so one can break."""
    k = s.root / "kit"
    k.mkdir()
    for d in ("scripts", "agents", "extensions"):
        shutil.copytree(ROOT / d, k / d, symlinks=True)
    shutil.copy(ROOT / "web-mcp.json", k)
    shutil.copytree(ROOT / ".agents" / "skills", k / ".agents" / "skills", symlinks=True)
    return k


def repo_skills(s: Scratch) -> None:
    """declared and unresolved on one start, each named with its reason; then parent."""
    with ExitStack() as stack:
        w = World(s, stack)
        # declared: the target's own declared skill broken. unresolved: a declared name with no
        # folder anywhere (gone), a dangling link (dangling), a folder with no SKILL.md (bare).
        w.local(BAD.format("local"))
        (w.tgt / "AGENTS.md").write_text(
            "# target\n\nRepo skills: python, local, gone, dangling, bare\n"
        )
        skills = w.tgt / ".agents" / "skills"
        (skills / "dangling").symlink_to(s.root / "nowhere")
        (skills / "bare").mkdir()
        (skills / "bare" / "README.txt").write_text("notes\n")
        gone = "skill path does not exist"
        want = {"local": YAML, "gone": gone, "dangling": gone, "bare": "no SKILL.md in it"}
        refused("declared and unresolved", w.start("implementer", "-p", "go"), want)
        (w.tgt / "AGENTS.md").write_text(DECLARED)
        w.no_herdr()
        # parent: a pane launch (RPC here: not -p, so pi-role keeps OCTO_FEATHER_PARENT) tells the
        # parent, through the kit's herdr-say, once.
        refused("parent", w.start("implementer", "--mode", "rpc", parent="w9:p9"), {"local": YAML})
        told = s.root / "herdr" / "prompts"
        prompts = told.read_text().splitlines() if told.exists() else []
        assert len(prompts) == 1, f"{TAG}: parent: not exactly one prompt: {prompts}"
        pane, text = prompts[0].split("\t", 1)
        assert pane == "w9:p9", prompts
        assert "implementer did not start" in text, prompts
        assert "skill local" in text, prompts


if __name__ == "__main__":
    main(kit_skills, repo_skills)
