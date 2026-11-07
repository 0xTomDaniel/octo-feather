"""Herdr messaging through the commands with the testkit's Herdr stand-in (testkit/herdr.py, its
FAKE_HERDR world). It never fails silently or hangs (#666; #585, #619; owner rulings #585 and
#619 2026-11-05): herdr-spawn returns only once its agent reads idle on `herdr agent wait`, so an
agent that turns ready late is not returned early, and a herdr-say right after it is delivered; a
herdr-say whose `herdr agent get` lookup fails names that lookup (not the up-chain refusal, 77); a
prompt Herdr reports stalled exits non-zero naming the pane and its state; and `octo-feather-lane
post-merge` step 4 to a busy (working) supervisor returns within its bound, its step 4 line naming
the supervisor NOT told (lane, pane, timeout, the re-send command) and going on to tell the others
(director rule #619).

herdr-spawn and pi-role vs Pi's trust dialog (#3): every launch carries --approve (pane and
headless); a dialog that opens anyway is never answered (69, no key, tab closed, its text on
stderr), also when a read fails; pi-role runs in --cwd (that target's tracker); the tab's env and
PATH (LINEAR_API_KEY only from the caller and in no file written; mise's shims before the system
dirs in a mise.toml repo; the caller's stub pi before ~/.local/bin, its fallback, last; #261,
#437). herdr-say resuming a parked agent (#9; comms #roles-park, #acceptance-resume-live-space):
in its live lane workspace or a new one, its session kept, told so with its new pane; a fresh
start on an existing workspace 73; its up-chain guard (#75): a supervisor resumes its own parked
worker (by lane log or parent), a worker never a sibling, a supervisor never another lane's (77).
post-merge step 4 (owner ruling on issue 206; issues 398, 458): live supervisors of the PR's repo
(every lane on a kit PR) told once with the merge, PR, title and rule files, one prod line each,
a rerun telling nothing new; parked and gone lanes listed, never sent to; a failed send named, no
prod line, exit 1; any other herdr failure stops the step; step 5 reached, Herdr's
workspace_not_found read as already closed."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from typing import TYPE_CHECKING

from testkit import HERE, ROOT, Ran, Scratch, kit, main, reflector, settled

if TYPE_CHECKING:
    from pathlib import Path

ASSETS = ROOT / ".agents" / "skills" / "herdr-comms" / "assets"
TELL_BOUND = 20  # post-merge step 4's bound on one send, seconds (octo-feather-lane --help)


def herdr_world(
    s: Scratch, agents: dict[str, dict[str, object]] | None = None, name: str = "herdr"
) -> Path:
    """S's Herdr: the stand-in's agents world in S/NAME, holding AGENTS, the caller's Herdr and
    kit variables cleared (a scenario's caller is no pane unless it sets one)."""
    d = s.root / name
    d.mkdir()
    (d / "agents.json").write_text(json.dumps(agents or {}))
    for k in [k for k in s.env if k.startswith(("HERDR_", "OCTO_FEATHER_"))]:
        del s.env[k]
    s.env["FAKE_HERDR"] = str(d)
    return d


def agent(pane: str, name: str, status: str, ready_at: float = 0) -> dict[str, object]:
    w = pane.split(":", maxsplit=1)[0]
    return {
        "name": name,
        "pane_id": pane,
        "workspace_id": w,
        "tab_id": f"{w}:t{pane.split(':p')[1]}",
        "agent_status": status,
        "ready_at": ready_at,
    }


SUPERVISOR = {
    "OCTO_FEATHER_ROLE": "supervisor",
    "OCTO_FEATHER_PARENT": "w0:p1",
    "HERDR_PANE_ID": "w1:p0",
    "HERDR_WORKSPACE_ID": "w1",
}


def lines(p: Path) -> list[str]:
    return p.read_text().splitlines() if p.exists() else []


def spawn_ready_late(s: Scratch) -> None:
    """An agent that turns idle 2 s after its start: herdr-spawn returns only once Herdr reads it
    idle (never while it still boots), and a herdr-say to its pane right after is delivered,
    nothing left typed and unsent."""
    d = herdr_world(s)
    (d / "ready_after").write_text("2")
    s.identity()
    wt = s.root / "wt"
    wt.mkdir()
    spawn = [str(ASSETS / "herdr-spawn"), "--workspace", "w1", "--name", "implementer-gh1"]
    ran = s.run([*spawn, "--role", "implementer", "--cwd", str(wt)], env=SUPERVISOR)
    pane = next(x.removeprefix("pane=") for x in ran.out.split() if x.startswith("pane="))
    got = json.loads(s.run(["herdr", "agent", "get", pane]).out)["result"]["agent"]
    assert got["agent_status"] == "idle", f"spawn returned while the agent read {got}"
    s.run([str(ASSETS / "herdr-say"), pane, "the brief"], env=SUPERVISOR)
    assert lines(d / "prompts") == [f"{pane}\tthe brief"], lines(d / "prompts")
    assert lines(d / "typed") == [], lines(d / "typed")


def say_lookup_fails(s: Scratch) -> None:
    """A supervisor's herdr-say to its worker while `herdr agent get` fails: an error naming the
    lookup and what it printed, never the up-chain refusal (77); nothing prompted."""
    d = herdr_world(s, {"w1:p2": agent("w1:p2", "implementer-gh1", "idle")})
    (d / "get-down").touch()
    ran = s.run([str(ASSETS / "herdr-say"), "w1:p2", "hi"], want=69, env=SUPERVISOR)
    assert "herdr agent get w1:p2" in ran.err, ran.err
    assert "server not reachable" in ran.err, ran.err
    assert "up its chain" not in ran.err, ran.err
    assert not lines(d / "prompts"), lines(d / "prompts")


def say_stalled(s: Scratch) -> None:
    """A prompt Herdr reports stalled (typed, never seen to land): herdr-say exits non-zero, its
    last line naming the pane and the state Herdr reads it in, and Herdr's own error kept."""
    late = time.time() + 3600
    d = herdr_world(s, {"w1:p2": agent("w1:p2", "implementer-gh1", "idle", late)})
    ran = s.run([str(ASSETS / "herdr-say"), "implementer-gh1", "hi"], want=1)
    last = ran.err.splitlines()[-1]
    assert "agent_prompt_stalled" in ran.err, ran.err
    assert "w1:p2" in last, ran.err
    assert "unknown" in last, ran.err
    assert lines(d / "typed") == ["w1:p2\thi"], lines(d / "typed")


def merged_repo(s: Scratch) -> tuple[Path, str]:
    """A repo whose main merged PR 7 (head H, changing a role file): its dir and H."""
    r = s.root / "repo"
    s.run(["git", "init", "-q", "-b", "main", str(r)])
    (r / "agents").mkdir()
    (r / "agents" / "supervisor.md").write_text("a\n")
    s.git(r, "add", "-A")
    s.git(r, "commit", "-qm", "base")
    s.git(r, "checkout", "-qb", "gh7")
    (r / "agents" / "supervisor.md").write_text("b\n")
    s.git(r, "commit", "-qam", "change")
    head = s.git(r, "rev-parse", "HEAD")
    s.git(r, "checkout", "-q", "main")
    s.git(r, "merge", "-q", "--no-ff", "gh7", "-m", "Merge #7")
    return r, head


def post_merge_busy(s: Scratch) -> None:
    """post-merge after PR 7 merged, lane live1's supervisor w1:p1 busy (working the whole run),
    lane live2's w2:p1 idle: step 4 returns within its bound; live2 told (its prod line), live1
    NOT told, named with its pane, the timeout, its state and the herdr-say that re-sends it by
    hand, no prod line; the summary names live1 NOT told; exit 1."""
    busy = agent("w1:p1", "live1", "working")
    d = herdr_world(s, {"w1:p1": busy, "w2:p1": agent("w2:p1", "live2", "idle")})
    r, head = merged_repo(s)
    merge = s.git(r, "rev-parse", "HEAD")
    url = "https://github.com/o/r/pull/7"
    s.gh.put(
        7,
        {
            "state": "MERGED",
            "headRefOid": head,
            "mergeCommit": {"oid": merge},
            "baseRefName": "main",
            "headRefName": "gh7",
            "title": "Add foo",
            "url": url,
        },
    )
    run = {"databaseId": 1, "status": "completed", "conclusion": "success"}
    s.gh.store("run/1.json", run | {"workflowName": "check", "url": f"{url}/checks"})
    # Step 3 asks `gh repo view` for the PR's repo and the kit install's origin: the fake gh knows
    # only o/r, so a gh first on PATH names the install's origin o/kit (step 3 then leaves it).
    gh = s.root / "ghbin"
    gh.mkdir()
    (gh / "gh").write_text(
        '#!/bin/sh\n[ "$1 $2 $3" = "repo view https://github.com/o/kit.git" ] && '
        'exec echo \'{"nameWithOwner": "o/kit"}\'\n'
        '[ "$1 $2" = "repo view" ] && exec echo \'{"nameWithOwner": "o/r"}\'\n'
        f'exec {s.bin}/gh "$@"\n'
    )
    (gh / "gh").chmod(0o755)
    kit_clone = s.root / "kit"
    s.run(["git", "clone", "-q", str(r), str(kit_clone)])
    s.git(kit_clone, "remote", "set-url", "origin", "https://github.com/o/kit.git")
    lanes = s.home / ".local" / "state" / "octo-feather" / "lanes"
    lanes.mkdir(parents=True)
    for n, issue in ((1, 11), (2, 12)):
        (lanes / f"live{n}.toml").write_text(
            f'supervisor = "w{n}:p1"\nrepository = "o/r"\nissue = {issue}\ngoal = "g"\n'
            'started_at = "2026-11-06T00:00:00Z"\n'
        )
    env = s.env | {
        "PATH": f"{gh}{os.pathsep}{ASSETS}{os.pathsep}{s.env['PATH']}",
        "OCTO_FEATHER_KIT_INSTALL": str(kit_clone),
    }
    cmd = [kit("octo-feather-lane"), "post-merge", "7", head, "--lane", "gh7", "--repo", "o/r"]
    t0 = time.monotonic()
    p = subprocess.run(
        [*cmd, "--wait", "0"],
        cwd=r,
        env=env,
        capture_output=True,
        text=True,
        timeout=TELL_BOUND + 60,
        check=False,
    )
    took = time.monotonic() - t0
    said = f"exit {p.returncode} after {took:.0f}s\n{p.stdout}\n{p.stderr}"
    assert p.returncode == 1, said
    assert took < TELL_BOUND + 20, said
    tell = next((x for x in p.stdout.splitlines() if x.startswith("step 4 ")), "")
    assert tell.startswith("step 4 tell supervisors: stopped: NOT told: live1 w1:p1: "), said
    assert f"send timed out after {TELL_BOUND}s" in tell, said
    assert f"w1:p1 (pane w1:p1) still working after {TELL_BOUND}s" in tell, said
    assert "re-send by hand: herdr-say w1:p1 'main moved to " in tell, said
    assert "; NOT told: live1 w1:p1; told: live2 w2:p1;" in tell, said
    last = p.stdout.splitlines()[-1]
    want = "step 5 teardown not run; NOT told: live1 w1:p1 (step 4 names each re-send)"
    assert last.endswith(f"step 4 tell supervisors stopped; {want}"), said
    assert [x.split("\t")[0] for x in lines(d / "prompts")] == ["w1:p1", "w2:p1"], said
    prods = [json.loads(x) for x in lines(lanes.parent / "director.handoffs.jsonl")]
    assert [x["issue"] for x in prods] == [12], said


# herdr-spawn, pi-role and herdr-say resuming a parked agent (#3, #9; #75): each spawn's world
# as the stand-in records it (testkit/herdr.py).
KITPATH = f"{ASSETS}{os.pathsep}{ROOT / 'scripts'}"
SPAWN_ENV = {
    "HERDR_PANE_ID": "w9:p0",
    "HERDR_SPAWN_TRUST_RETRIES": "3",
    "HERDR_SPAWN_READY_RETRIES": "2",
}


def spawner(s: Scratch) -> Path:
    """S set up to spawn: its own state (the commit identity a role launch needs) and mise state,
    no Linear key; the worktree S/cwd, made."""
    s.env |= {"XDG_STATE_HOME": str(s.root / "state"), "MISE_STATE_DIR": str(s.root / "mise")}
    s.env.pop("LINEAR_API_KEY", None)
    s.identity()
    cwd = s.root / "cwd"
    cwd.mkdir(exist_ok=True)
    return cwd


def spawn(s: Scratch, d: Path, cwd: Path, want: int = 0, env: dict[str, str] | None = None) -> Ran:
    """herdr-spawn of implementer t1 into workspace w9 at CWD, world D, from S's root."""
    cmd = [str(ASSETS / "herdr-spawn"), "--workspace", "w9", "--name", "t1"]
    e = SPAWN_ENV | {"FAKE_HERDR": str(d)} | (env or {})
    return s.run([*cmd, "--role", "implementer", "--cwd", str(cwd)], want=want, env=e)


def tab_env(d: Path) -> dict[str, str]:
    return dict(x.split("=", 1) for x in lines(d / "tab-env"))


def toolbox(s: Scratch) -> tuple[Path, Path, Path]:
    """A throwaway HOME whose ~/.local/bin holds a pi and a tool only it has, a stub pi dir, and
    a dir linking mise and jq: (home, stub dir, mise dir); S's bin without its pi (the stub is
    the caller's)."""
    (s.bin / "pi").unlink()
    uh, stub, mbin = s.root / "uh", s.root / "stub", s.root / "mbin"
    (uh / ".local" / "bin").mkdir(parents=True)
    for d, n, text in (
        (uh / ".local" / "bin", "pi", "home pi"),
        (uh / ".local" / "bin", "only-home", "home only-home"),
        (stub, "pi", "stub pi"),
    ):
        d.mkdir(exist_ok=True)
        (d / n).write_text(f"#!/bin/sh\necho '{text}'\n")
        (d / n).chmod(0o755)
    mbin.mkdir()
    for t in ("mise", "jq"):
        w = shutil.which(t)
        assert w, f"no {t} on PATH: this case needs it"
        (mbin / t).symlink_to(w)
    return uh, stub, mbin


def resolves(tp: str, uh: Path, stub: Path, what: str) -> None:
    """Tab PATH TP finds the caller's stub pi before ~/.local/bin's, and a tool only ~/.local/bin
    holds there (its fallback, last): resolved only, never run."""
    assert shutil.which("pi", path=tp) == str(stub / "pi"), f"{what}: pi not the stub's: {tp}"
    got = shutil.which("only-home", path=tp)
    assert got == str(uh / ".local" / "bin" / "only-home"), f"{what}: lost the fallback: {tp}"


def spawn_plain(s: Scratch) -> None:
    """A plain spawn (no mise.toml in its worktree) with LINEAR_API_KEY set in the caller, a
    stub pi first on its PATH, a pi in ~/.local/bin: Pi launched with --approve beside pi-role's
    --no-skills and the implementer's web list; exit 0, tab and pane printed, no key sent; the
    tab's env holds the Linear key, no file the spawn writes does, and a ticket filed from that
    env through the linear skill's issue-create reaches the store; the tab's PATH the kit dirs,
    the caller's PATH as it was, ~/.local/bin last, finding the stub pi first and a tool only
    ~/.local/bin holds. Then headless pi-role passes --approve too."""
    cwd = spawner(s)
    d = herdr_world(s)
    uh, stub, mbin = toolbox(s)
    key = f"lin-test-{os.urandom(8).hex()}"
    path = os.pathsep.join([str(s.bin), str(stub), str(mbin), "/usr/bin", "/bin"])
    ran = spawn(s, d, cwd, env={"LINEAR_API_KEY": key, "HOME": str(uh), "PATH": path})
    argv = lines(d / "start-argv")
    for f in ("--approve", "--no-skills", "--octo-feather-web-servers"):
        assert f in argv, f"agent start argv lacks {f}: {argv}"
    assert "tab=w9:t1 pane=w9:p1" in ran.out, ran.out
    assert lines(d / "keys") == [], lines(d / "keys")
    env = tab_env(d)
    assert env.get("LINEAR_API_KEY") == key, sorted(env)
    for top in (uh, s.root / "state", s.root / "mise", cwd):
        for f in (f for f in top.rglob("*") if f.is_file() and not f.is_symlink()):
            assert key.encode() not in f.read_bytes(), f"{f} holds the Linear key"
    assert key not in ran.out + ran.err, "the spawn printed the Linear key"
    assert env["PATH"] == f"{KITPATH}{os.pathsep}{path}{os.pathsep}{uh}/.local/bin", env["PATH"]
    resolves(env["PATH"], uh, stub, "no mise.toml")
    store = s.root / "store.json"
    store.write_text('{"workspace": "acme", "default_team": "ENG", "issues": {}}')
    create = ROOT / ".agents" / "skills" / "linear" / "scripts" / "issue-create"
    filed = subprocess.run(
        [str(create), "--title", "T", "--body-file", "-"],
        env=env
        | {"OCTO_FEATHER_LINEAR_STORE": str(store), "PATH": f"{create.parent}:{env['PATH']}"},
        input="body",
        capture_output=True,
        text=True,
        check=False,
    )
    assert filed.stdout.strip() == "ENG-1", f"issue-create from the tab env: {filed}"
    assert json.loads(store.read_text())["issues"]["ENG-1"]["title"] == "T", store.read_text()
    reflector(s)
    s.run([kit("pi-role"), str(ROOT / "agents" / "implementer.md"), "-p", "brief"], cwd=cwd)
    headless = (s.root / "argv.lane").read_text().split("\0")
    assert "--approve" in headless, f"headless pi-role argv lacks --approve: {headless}"


def spawn_cwd(s: Scratch) -> None:
    """pi-role runs in --cwd, not the caller's dir: a caller in a jira target spawning into a
    target with no config gets github-issues; spawning into the jira target is refused (65,
    unknown tracker 'jira') before any agent starts."""
    cwd = spawner(s)
    d = herdr_world(s)
    jira = s.root / "jira"
    s.git(s.root, "init", "-q", str(jira))
    (jira / ".octo-feather.toml").write_text('tracker = "jira"\n')
    cmd = [str(ASSETS / "herdr-spawn"), "--workspace", "w9", "--name", "t1", "--role"]
    e = SPAWN_ENV | {"FAKE_HERDR": str(d)}
    s.run([*cmd, "implementer", "--cwd", str(cwd)], cwd=jira, env=e)
    argv = lines(d / "start-argv")
    assert any(x.endswith("/github-issues") for x in argv), f"no github-issues skill: {argv}"
    (d / "start-argv").unlink()
    ran = s.run([*cmd, "implementer", "--cwd", str(jira)], want=65, cwd=cwd, env=e)
    assert "unknown tracker 'jira'" in ran.err, ran.err
    assert not (d / "start-argv").exists(), "spawn into a jira target started an agent"


def armed(d: Path, reads_ok: int) -> None:
    """A failing-read case is vacuous unless the spawn read up to the armed boundary READS_OK;
    reads past it are recorded failures."""
    r, f = len(lines(d / "reads")), len(lines(d / "failed-reads"))
    assert r >= reads_ok, f"{r} pane reads < {reads_ok}: the failing read was never reached"
    assert r == reads_ok or f >= 1, f"{r} reads past {reads_ok} but no failed read recorded"


def spawn_dialog(s: Scratch) -> None:
    """A Pi trust dialog that opens anyway is never answered: exit 69, no key, tab closed, pane
    text on stderr; the same when the pane read fails after the detecting read; a non-Pi dialog
    that never clears closes its tab, 69, its text on stderr, also when the read after the last
    detecting one fails."""
    cwd = spawner(s)
    for case, dialog, ok, retries, text in (
        ("dialog", "pi", "", "3", "Trust project folder?"),
        ("readfail", "pi", "1", "3", "Trust project folder?"),
        ("stuck", "other", "4", "1", "Quick safety check"),
    ):
        d = herdr_world(s, name=case)
        (d / "dialog").write_text(dialog)
        if ok:
            (d / "reads_ok").write_text(ok)
        env = {"HERDR_SPAWN_TRUST_RETRIES": retries}
        ran = spawn(s, d, cwd, want=69, env=env)
        if ok:
            armed(d, int(ok))
        if dialog == "pi":
            assert lines(d / "keys") == [], f"{case}: keys sent: {lines(d / 'keys')}"
        assert lines(d / "closed") == ["w9:t1"], f"{case}: tab not closed: {lines(d / 'closed')}"
        assert text in ran.err, f"{case}: pane text not on stderr: {ran.err}"


def spawn_mise_path(s: Scratch) -> None:
    """#261, owner ruling #437: in a worktree with its own mise.toml the tab's PATH is the kit
    dirs, the caller's PATH with mise's shims (as `mise doctor` names them) just before its first
    system dir, ~/.local/bin last, the caller's stub pi still first; with no mise on PATH, the
    caller's PATH as it was. No Linear key in the caller: none in the tab."""
    cwd = spawner(s)
    (cwd / "mise.toml").write_text("[tools]\n")
    uh, stub, mbin = toolbox(s)
    d = herdr_world(s)
    sys_dirs = ["/usr/local/bin", "/usr/bin", "/bin"]
    path = os.pathsep.join([str(s.bin), str(stub), str(mbin), *sys_dirs])
    env = {"HOME": str(uh), "PATH": path}
    doctor = subprocess.run(
        ["mise", "doctor", "--json"],  # noqa: S607
        env=s.env | env,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    shims = json.loads(doctor.stdout)["dirs"]["shims"]
    spawn(s, d, cwd, env=env)
    tab = tab_env(d)
    want = [str(s.bin), str(stub), str(mbin), shims, *sys_dirs, f"{uh}/.local/bin"]
    assert tab["PATH"] == os.pathsep.join([KITPATH, *want]), tab["PATH"]
    resolves(tab["PATH"], uh, stub, "mise.toml")
    assert "LINEAR_API_KEY" not in tab, "LINEAR_API_KEY set in a tab whose caller had none"
    bare = os.pathsep.join([str(s.bin), "/usr/bin", "/bin"])
    d = herdr_world(s, name="bare")
    spawn(s, d, cwd, env={"PATH": bare})
    got = tab_env(d)["PATH"]
    assert got == os.pathsep.join([KITPATH, bare, f"{s.home}/.local/bin"]), got


# One parked line per lane hand-off log (octo-feather-handoff parked's form).
def parked_line(pane: str, session: str, parent: str, cwd: Path, name: str = "") -> str:
    who = {"name": name, "label": name, "role": "implementer"} if name else {}
    at = {"at": "2026-10-20T00:00:00Z", "kind": "parked", "pane": pane}
    return json.dumps(at | who | {"cwd": str(cwd), "session": session, "parent": parent})


def parked_world(
    s: Scratch,
    spaces: list[tuple[str, str]],
    logs: dict[str, list[str]],
    agents: dict[str, dict[str, object]] | None = None,
) -> Path:
    """S's world: workspaces SPACES (label, id), AGENTS live, each lane's hand-off log LOGS (its
    lines), the state dir S/state holding them and the commit identity."""
    d = herdr_world(s, agents)
    (d / "workspaces.json").write_text(
        json.dumps([{"label": lb, "workspace_id": w} for lb, w in spaces])
    )
    s.env["XDG_STATE_HOME"] = str(s.root / "state")
    s.identity()
    lanes = s.root / "state" / "octo-feather" / "lanes"
    lanes.mkdir(parents=True)
    for lane, ls in logs.items():
        (lanes / f"{lane}.handoffs.jsonl").write_bytes(
            b"".join(x.encode("latin-1") + b"\n" for x in ls)
        )
    (s.root / "cwd").mkdir()
    return d


DIRECTOR = {
    "HERDR_PANE_ID": "w2:p1",
    "HERDR_WORKSPACE_ID": "w2",
    "HERDR_SPAWN_TRUST_RETRIES": "1",
    "HERDR_SPAWN_READY_RETRIES": "2",
}


def say(s: Scratch, env: dict[str, str], *args: str, want: int = 0) -> Ran:
    """herdr-say ARGS as the caller ENV, settled: it and every process it started (a resume's
    start runs the director reflection detached) ended before it returns."""
    return s.run(settled([str(ASSETS / "herdr-say"), *args]), want=want, env=env)


def resumed(d: Path, ran: Ran, space: str, who: tuple[str, str], text: str) -> str:
    """RAN resumed WHO (its name, its session) in a new tab of SPACE: its pane printed, the agent
    there, the message it got the resume notice naming that pane, then TEXT; its pane."""
    name, session = who
    pane = next((x.removeprefix("pane=") for x in ran.out.split() if x.startswith("pane=")), "")
    assert pane.startswith(f"{space}:p"), f"no pane in {space} printed: {ran.out}"
    got = json.loads((d / "agents.json").read_text())[pane]
    assert got["name"] == name, f"{name} not started at {pane}: {got}"
    assert any(x.startswith(f"tab create --workspace {space} ") for x in lines(d / "log")), lines(
        d / "log"
    )
    argv = lines(d / "start-argv")
    i = argv.index("--session-id")
    assert argv[i + 1] == session, f"not resumed with session {session}: {argv}"
    want = f"{pane}\tResumed from park as pane={pane}. {text}"
    assert lines(d / "prompts")[-1] == want, lines(d / "prompts")
    return pane


def resume_live(s: Scratch) -> None:
    """comms #acceptance-resume-live-space: a parked supervisor whose lane workspace gh2 (w5)
    still exists: --parked gh2 prints its line named for the lane, session kept; a message to it
    resumes it in a new tab of w5 (no workspace created, no tab closed, its session kept, the
    notice naming its new pane); a message to that pane, now live, arrives plain (no resume); a
    fresh start (no --resume) of lane gh2 refuses with 73, nothing created."""
    cwd = s.root / "cwd"
    sup = parked_line("w5:p1", "S1", "w2:p1", cwd)
    d = parked_world(s, [("gh2", "w5")], {"gh2": [sup]})
    line = json.loads(say(s, DIRECTOR, "--parked", "gh2").out)
    assert (line["session"], line["name"]) == ("S1", "gh2"), line
    ran = say(s, DIRECTOR, "gh2", "hello")
    assert not any(x.startswith("workspace create") for x in lines(d / "log")), lines(d / "log")
    pane = resumed(d, ran, "w5", ("gh2", "S1"), "hello")
    assert lines(d / "closed") == [], f"tabs closed in the live workspace: {lines(d / 'closed')}"
    tabs = len([x for x in lines(d / "log") if x.startswith("tab create")])
    ran = say(s, DIRECTOR, pane, "hello")
    assert lines(d / "prompts")[-1] == f"{pane}\thello", lines(d / "prompts")
    assert "pane=" not in ran.out, ran.out
    assert len([x for x in lines(d / "log") if x.startswith("tab create")]) == tabs, "resumed again"
    n = len(lines(d / "log"))
    start = [kit("octo-feather-start"), "--issue", "2", "--cwd", str(cwd)]
    s.run(settled(start), want=73, env=DIRECTOR)
    made = [x for x in lines(d / "log")[n:] if x.startswith(("tab create", "workspace create"))]
    assert made == [], f"a fresh start on an existing gh2 created {made}"


def resume_gone(s: Scratch) -> None:
    """comms #roles-park: a parked supervisor whose lane workspace is gone resumes in a new lane
    workspace gh2, only its seed tab closed, told it was resumed with its new pane."""
    sup = parked_line("w5:p1", "S1", "w2:p1", s.root / "cwd")
    d = parked_world(s, [], {"gh2": [sup]})
    ran = say(s, DIRECTOR, "w5:p1", "hello")
    made = [x for x in lines(d / "log") if x.startswith("workspace create --label gh2 ")]
    assert made, lines(d / "log")
    w = json.loads((d / "workspaces.json").read_text())[-1]["workspace_id"]
    resumed(d, ran, w, ("gh2", "S1"), "hello")
    assert lines(d / "closed") == [f"{w}:t0"], f"closed {lines(d / 'closed')}, want the seed tab"


SUP_GH2 = {
    "OCTO_FEATHER_ROLE": "supervisor",
    "OCTO_FEATHER_PARENT": "w2:p1",
    "HERDR_PANE_ID": "w5:p1",
    "HERDR_WORKSPACE_ID": "w5",
    "HERDR_SPAWN_TRUST_RETRIES": "1",
    "HERDR_SPAWN_READY_RETRIES": "2",
}


def say_resume_lane(s: Scratch) -> None:
    """#75: supervisor gh2 (live at w5:p1) to its parked worker impl1, found by its lane log (the
    line's parent a pane the supervisor had before its own park): another lane's corrupt log
    named line by line on stderr, the lookup still answered; the worker resumed in the caller's
    space w5 with its old session, pane= printed, told it was resumed."""
    cwd = s.root / "cwd"
    other = ["not JSON", '{"kind":', "42", "\xff"]
    worker = parked_line("w5:p3", "S2", "w5:p0", cwd, "impl1")
    d = parked_world(
        s,
        [("gh2", "w5")],
        {"gh2": [worker], "other": other},
        {"w5:p1": agent("w5:p1", "gh2", "idle")},
    )
    ran = say(s, SUP_GH2, "--parked", "impl1")
    line = json.loads(ran.out)
    assert (line["session"], line["name"]) == ("S2", "impl1"), line
    for n in (1, 2, 3, 4):
        assert f"other.handoffs.jsonl:{n}:" in ran.err, f"no diagnostic for line {n}: {ran.err}"
    resumed(d, say(s, SUP_GH2, "impl1", "go on"), "w5", ("impl1", "S2"), "go on")


def say_resume_parent(s: Scratch) -> None:
    """#75: a supervisor Herdr knows by no name to a parked worker whose line names the caller's
    pane as its parent: resumed, old session, told it was resumed."""
    worker = parked_line("w5:p3", "S3", "w5:p1", s.root / "cwd", "impl1")
    d = parked_world(s, [("gh2", "w5")], {"gh2": [worker]})
    resumed(d, say(s, SUP_GH2, "w5:p3", "go on"), "w5", ("impl1", "S3"), "go on")


def say_refused(s: Scratch) -> None:
    """#75: a worker to a parked sibling (not its parent), and supervisor gh2 to a parked worker
    of lane gh3: each 77, the up-chain refusal on stderr, nothing resumed or prompted."""
    cwd = s.root / "cwd"
    sib = parked_line("w5:p3", "S4", "w5:p1", cwd, "impl1")
    gh3 = parked_line("w6:p3", "S5", "w6:p1", cwd, "impl9")
    live = {
        "w5:p1": agent("w5:p1", "gh2", "idle"),
        "w5:p2": agent("w5:p2", "implementer-gh2", "idle"),
    }
    d = parked_world(s, [("gh2", "w5")], {"gh2": [sib], "gh3": [gh3]}, live)
    worker = SUP_GH2 | {
        "OCTO_FEATHER_ROLE": "implementer",
        "OCTO_FEATHER_PARENT": "w5:p1",
        "HERDR_PANE_ID": "w5:p2",
    }
    for what, env, target in (
        ("worker to parked sibling", worker, "w5:p3"),
        ("other lane", SUP_GH2, "impl9"),
    ):
        ran = say(s, env, target, "hi", want=77)
        assert "may message only up its chain" in ran.err, f"{what}: {ran.err}"
    acts = ("tab create", "workspace create", "agent start", "agent prompt")
    assert not [x for x in lines(d / "log") if x.startswith(acts)], lines(d / "log")


# octo-feather-lane post-merge step 4, tell supervisors (owner ruling 2026-10-29 on issue 206;
# issues 398, 458), and step 5 reached: the kit's own herdr-say
# and herdr-close over the Herdr world, each run in a PID namespace of its own (herdr-close's
# sweep of tagged processes sees only the run's own).
PIDNS = ("unshare", "--map-current-user", "--pid", "--fork", "--mount-proc")
# A kit install's recipes step 3's refresh runs (by the real just): nothing to fetch or check.
TELL_JUSTFILE = "vendored-fetch:\n    @true\n\ninstall-check target:\n    @true\n"
RULED = ".agents/skills/foo/SKILL.md, agents/supervisor.md"


def build_tell(p: Scratch) -> None:
    """repo: main merged gh7 (two rule files and a product file changed) then gh8 (a file under
    no rule path); kit: a clone of it at main, its origin o/kit (fetched from repo)."""
    r = p.root / "repo"
    p.run(["git", "init", "-q", "-b", "main", str(r)])
    for f, text in (("agents/supervisor.md", "a"), ("src/app.py", "a"), ("docs/notes.md", "a")):
        (r / f).parent.mkdir(parents=True, exist_ok=True)
        (r / f).write_text(text + "\n")
    (r / "justfile").write_text(TELL_JUSTFILE)
    p.git(r, "add", "-A")
    p.git(r, "commit", "-qm", "base")
    for branch, files, msg in (
        ("gh7", ("agents/supervisor.md", ".agents/skills/foo/SKILL.md", "src/app.py"), "#7"),
        ("gh8", ("docs/notes.md",), "#8"),
    ):
        p.git(r, "checkout", "-qb", branch)
        for f in files:
            (r / f).parent.mkdir(parents=True, exist_ok=True)
            (r / f).write_text(f"{branch}\n")
        p.git(r, "add", "-A")
        p.git(r, "commit", "-qm", "change")
        p.git(r, "checkout", "-q", "main")
        p.git(r, "merge", "-q", "--no-ff", branch, "-m", f"Merge {msg}")
    k = p.root / "kit"
    p.run(["git", "clone", "-q", str(r), str(k)])
    p.git(k, "remote", "set-url", "origin", "https://github.com/o/kit.git")
    p.git(k, "config", f"url.{r}.insteadOf", "https://github.com/o/kit.git")


class Tell:
    """The prepared repo and kit install in S, its lanes and director log, Herdr's world; `run`
    runs post-merge from the repo."""

    def __init__(self, s: Scratch) -> None:
        s.prepare("lane-post-merge-tell", build_tell)
        self.s, self.r = s, s.root / "repo"
        # The kit install's url rewrite names the prepared tree's repo: this copy's own.
        s.git(s.root / "kit", "config", f"url.{self.r}.insteadOf", "https://github.com/o/kit.git")
        self.d = herdr_world(s)
        s.env.pop("GH_REPO", None)
        st = s.root / "state" / "octo-feather"
        self.lanes, self.dlog = st / "lanes", st / "director.handoffs.jsonl"
        self.lanes.mkdir(parents=True)
        rec = s.root / "rec"
        rec.mkdir()
        for n in ("uv", "pnpm"):  # step 3's refresh reaching the registries: argv_recorder.sh
            (rec / n).symlink_to(HERE / "argv_recorder.sh")
        s.env |= {
            "XDG_STATE_HOME": str(s.root / "state"),
            "OCTO_FEATHER_KIT_INSTALL": str(s.root / "kit"),
            "ARGV_LOG": str(s.root / "argv.log"),
            "PATH": os.pathsep.join([str(rec), str(ASSETS), s.env["PATH"]]),
        }
        log = s.git(self.r, "log", "--first-parent", "--format=%H %P", "main").splitlines()
        (self.m2, _, self.h2), (self.m, _, self.h) = (x.split() for x in log[:2])
        s.gh.store("repo.json", {"nameWithOwner": "o/r"})
        s.gh.store("api/repos/o/kit.json", {"nameWithOwner": "o/kit"})
        run = {"databaseId": 1, "status": "completed", "conclusion": "success"}
        s.gh.store("run/1.json", run | {"workflowName": "check", "url": "https://x/runs/1"})
        self.store("o/r", "Add foo")

    def store(self, repo: str, title: str) -> None:
        """PRs 7 (TITLE) and 8 (Notes) of REPO, merged."""
        for n, head, merge, t in ((7, self.h, self.m, title), (8, self.h2, self.m2, "Notes")):
            pr = {
                "state": "MERGED",
                "headRefOid": head,
                "mergeCommit": {"oid": merge},
                "baseRefName": "main",
                "headRefName": f"gh{n}",
                "title": t,
                "url": f"https://github.com/{repo}/pull/{n}",
            }
            self.s.gh.store(f"repo/{repo}/pr/{n}.json" if repo != "o/r" else f"pr/{n}.json", pr)

    def lane(self, name: str, pane: str, repo: str, issue: int) -> None:
        (self.lanes / f"{name}.toml").write_text(
            f'supervisor = "{pane}"\nrepository = "{repo}"\nissue = {issue}\ngoal = "g"\n'
            'started_at = "2026-10-29T00:00:00Z"\n'
        )

    def parked(self, lane: str, pane: str, at: str) -> None:
        line = {"at": at, "kind": "parked", "pane": pane, "name": lane}
        with (self.lanes / f"{lane}.handoffs.jsonl").open("a") as f:
            f.write(json.dumps(line) + "\n")

    def live(self, *panes: str, blocked: str = "") -> None:
        """Herdr's agents: PANES live (idle), BLOCKED (one of them) on a dialog."""
        live = {p: agent(p, p, "blocked" if p == blocked else "idle") for p in panes}
        (self.d / "agents.json").write_text(json.dumps(live))

    def run(self, want: int, pr: int, *args: str) -> tuple[str, str]:
        """post-merge PR (its head) ARGS --wait 0, exit WANT, no traceback: its step 4 line and
        its last line."""
        head = self.h if pr == 7 else self.h2
        cmd = [*PIDNS, kit("octo-feather-lane"), "post-merge", str(pr), head, *args, "--wait", "0"]
        ran = self.s.run(cmd, want=want, cwd=self.r)
        tell = [x for x in ran.out.splitlines() if re.match(r"step [0-9]+ tell supervisors: ", x)]
        assert tell, f"no tell supervisors line: {ran.out}"
        self.out = ran.out
        return tell[0], ran.out.splitlines()[-1]

    def said(self) -> list[str]:
        """Each pane a send was tried to, sorted."""
        return sorted(x.split()[2] for x in lines(self.d / "log") if x.startswith("agent prompt "))

    def told(self) -> list[str]:
        return [x.split("\t", 1)[1] for x in lines(self.d / "prompts")]

    def prods(self) -> list[dict[str, object]]:
        return [json.loads(x) for x in lines(self.dlog)]

    def clear(self) -> None:
        """The sends, Herdr's call log and the director log emptied."""
        for f in (self.d / "log", self.d / "prompts", self.dlog):
            f.write_text("")


def tell_live(s: Scratch) -> None:
    """Only a live supervisor of the PR's repo gets one message naming the merge commit, PR,
    title and changed rule files; the --lane lane, a parked one (its latest parked line names its
    pane) and another repo's lane (never looked up) none; one canonical prod line per lane told,
    after the director's own; step 4 ok, step 5 pending, exit 3. A rerun sends and logs nothing
    new (already told). A merge touching no rule file says none, and is told again."""
    t = Tell(s)
    t.lane("gh7", "w0:p1", "o/r", 7)
    t.lane("live1", "w1:p1", "o/r", 11)
    t.lane("parked", "w2:p1", "o/r", 12)
    t.lane("other", "w3:p1", "x/y", 13)
    t.parked("parked", "w2:p0", "2026-10-28T00:00:00Z")
    t.parked("parked", "w2:p1", "2026-10-29T00:00:00Z")
    t.live("w0:p1", "w1:p1", "w3:p1")
    earlier = '{"at": "2026-10-29T00:00:00+00:00", "kind": "prod", "issue": 11, "note": "earlier"}'
    t.dlog.write_text(earlier + "\n")
    tell, last = t.run(3, 7, "--lane", "gh7", "--repo", "o/r")
    assert t.said() == ["w1:p1"], t.said()
    m12 = t.m[:12]
    reread = "re-read the changed ones before your next step."
    want = f"main moved to {m12} (#7 Add foo); rule files changed: {RULED}; {reread}"
    assert t.told() == [want], t.told()
    assert "told: live1 w1:p1" in tell, tell
    assert tell.endswith("not woken: parked w2:p1; gone: director to resume or archive: none"), tell
    assert last.endswith("tell supervisors ok; step 5 teardown pending"), last
    assert not [x for x in lines(t.d / "log") if x == "agent get w3:p1"], lines(t.d / "log")
    prods = t.prods()
    assert len(prods) == 2, prods
    note = f"post-merge {t.m} #7: main moved, told live1 to re-read {RULED}"
    p = prods[1]
    assert sorted(p) == ["at", "issue", "kind", "note"], p
    assert (p["kind"], p["issue"], p["note"]) == ("prod", 11, note), p
    assert re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:.]+\+00:00", str(p["at"])), p
    tell, _ = t.run(3, 7, "--lane", "gh7", "--repo", "o/r")
    assert len(t.told()) == 1, f"rerun sent again: {t.told()}"
    assert len(t.prods()) == 2, f"rerun logged again: {t.prods()}"
    assert "already told: live1" in tell, tell
    assert "not woken: parked w2:p1" in tell, tell
    t.run(3, 8, "--lane", "gh7", "--repo", "o/r")
    none = f"main moved to {t.m2[:12]} (#8 Notes); rule files changed: none; {reread}"
    assert t.told()[-1] == none, t.told()
    assert t.prods()[-1]["note"] == f"post-merge {t.m2} #8: main moved, told live1 to re-read none"


def tell_kit(s: Scratch) -> None:
    """A kit PR (o/kit, the install's own repo): every lane runs kit roles, so another repo's live
    lane is told too, one prod line each (step 3 refreshes the install first: its recipes no-ops,
    uv and pnpm argv_recorder.sh)."""
    t = Tell(s)
    t.store("o/kit", "Kit rule")
    t.lane("gh7", "w0:p1", "o/r", 7)
    t.lane("live1", "w1:p1", "o/r", 11)
    t.lane("other", "w3:p1", "x/y", 13)
    t.live("w0:p1", "w1:p1", "w3:p1")
    t.run(3, 7, "--lane", "gh7", "--repo", "o/kit")
    assert t.said() == ["w1:p1", "w3:p1"], f"{t.said()}: {t.out}"
    assert sorted(int(str(p["issue"])) for p in t.prods()) == [11, 13], t.prods()


def tell_failed(s: Scratch) -> None:
    """A send that fails (its supervisor blocked on a dialog, herdr-say's 75): named, no prod line
    for it, the others still tried and told, the step stopped, exit 1. A rerun tells only that
    one."""
    t = Tell(s)
    t.lane("gh7", "w0:p1", "o/r", 7)
    t.lane("live1", "w1:p1", "o/r", 11)
    t.lane("live2", "w4:p1", "o/r", 14)
    t.live("w0:p1", "w1:p1", "w4:p1", blocked="w1:p1")
    tell, last = t.run(1, 7, "--lane", "gh7", "--repo", "o/r")
    assert t.said() == ["w1:p1", "w4:p1"], t.said()
    assert "stopped: " in tell, tell
    assert "herdr-say failed: live1 w1:p1 exit 75" in tell, tell
    assert "told: live2 w4:p1" in tell, tell
    assert [p["issue"] for p in t.prods()] == [14], t.prods()
    assert "tell supervisors stopped" in last, last
    t.live("w0:p1", "w1:p1", "w4:p1")
    (t.d / "log").write_text("")
    t.run(3, 7, "--lane", "gh7", "--repo", "o/r")
    assert t.said() == ["w1:p1"], f"retry: {t.said()}"
    assert [p["issue"] for p in t.prods()] == [14, 11], t.prods()


def tell_gone(s: Scratch) -> None:
    """Issue 458: --lane gh1 with a live, a parked and two gone lanes (one never parked, one
    whose latest parked line names an older pane): only the live one told, the rest listed, step 4
    ok, step 5 pending (not archived). Archived: step 5 runs, herdr-close failing and Herdr's
    workspace_not_found read as already closed. Any other herdr failure (on the parked lane's
    lookup) stops step 4, named, the other lanes still handled."""
    t = Tell(s)
    t.lane("live1", "w1:p1", "o/r", 11)
    t.lane("parked", "w2:p1", "o/r", 12)
    t.lane("gone", "w5:p1", "o/r", 15)
    t.lane("moved", "w6:p1", "o/r", 16)
    t.parked("parked", "w2:p1", "2026-10-29T00:00:00Z")
    t.parked("moved", "w6:p1", "2026-10-28T00:00:00Z")
    t.parked("moved", "w6:p0", "2026-10-29T00:00:00Z")
    t.live("w1:p1")
    gone = "gone: director to resume or archive: gone w5:p1, moved w6:p1"
    tell, _ = t.run(3, 7, "--lane", "gh1", "--repo", "o/r")
    assert t.said() == ["w1:p1"], t.said()
    want = "told: live1 w1:p1; already told: none; not woken: parked w2:p1; " + gone
    assert tell.startswith("step 4 tell supervisors: ok: "), tell
    assert tell.endswith(want), tell
    pending = "step 5 teardown: pending: lane gh1 not archived; rerun on its close report"
    assert pending in t.out.splitlines(), t.out
    (t.lanes / "archive").mkdir()
    (t.lanes.parent / "director.toml").write_text('pane = "w0:p9"\n')
    t.s.git(t.r, "remote", "add", "origin", str(t.r))
    (t.lanes / "archive" / "gh1.toml").write_text(
        'supervisor = "w9:p1"\nrepository = "o/r"\nissue = 1\npr = 7\ngoal = "g"\n'
        'started_at = "2026-10-29T00:00:00Z"\n'
    )
    t.run(0, 7, "--lane", "gh1", "--repo", "o/r")
    down = (
        "step 5 teardown: ok: space w9 already closed; worktree of gh1 already removed; no open "
        "PR based on gh1; local branch gh1 already deleted; remote branch gh1 already deleted "
        "from origin"
    )
    assert down in t.out.splitlines(), t.out
    assert "workspace get w9" in lines(t.d / "log"), lines(t.d / "log")
    (t.lanes / "archive" / "gh1.toml").unlink()
    (t.d / "get-down").write_text("w2:p1\n")
    tell, _ = t.run(1, 7, "--lane", "gh1", "--repo", "o/r")
    stop = (
        "step 4 tell supervisors: stopped: parked w2:p1: herdr agent get w2:p1 failed (herdr: "
        "server not reachable)"
    )
    assert tell.startswith(stop), tell
    assert tell.endswith(gone), tell


if __name__ == "__main__":
    main(
        spawn_ready_late,
        say_lookup_fails,
        say_stalled,
        post_merge_busy,
        spawn_plain,
        spawn_cwd,
        spawn_dialog,
        spawn_mise_path,
        resume_live,
        resume_gone,
        say_resume_lane,
        say_resume_parent,
        say_refused,
        tell_live,
        tell_kit,
        tell_failed,
        tell_gone,
    )
