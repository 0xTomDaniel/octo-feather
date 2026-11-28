"""The scenarios of tests/gate/kit/test_lane_start.py (its items), this file their command
(testkit.main): `octo-feather-lane start`, the director's lane start (issue-lifecycle spec
#acceptance-lane-start; issue 1155), offline.

Seam (ticket #1155, recorded before any test): `octo-feather-lane start` run as a command, the
testkit's herdr and gh stand-ins first on PATH (testkit/herdr.py's FAKE_HERDR world,
testkit/gh.py's store holding repo o/r and its open issue 905), the real octo-feather-start and
herdr-spawn behind it. The target is a scratch clone of a local origin whose main moved after the
clone, so the lane branch must come from origin's main as fetched, not the checkout's stale main.

  started  run from the director's pane w0:p1 in the checkout: the lane workspace labelled gh905
           holds the supervisor gh905 (tab supervisor); the worktree <checkout>-gh905 is on branch
           gh905 at origin's main; lanes/gh905.toml holds exactly comms #lane-record's keys at
           launch; the supervisor received the goal, then the brief (its generated header, then
           the file's text) and nothing else; the director log holds one prod line for the lane
           (beside the spawn line herdr-spawn writes for the director's spawn); it printed
           `key=gh905 pane=<pane> issue=905`; Herdr names the supervisor's working directory
           that worktree. Each observation printed, for the qc demo.
  unicode_title  options before the ticket and in `--opt=value` form (argparse's grammar), a title
           with an emoji, a quote and a backslash: the record parses (tomllib) and its goal is the
           title exactly.
  refused  each exits 1 naming what it rejects and makes nothing (no worktree, branch, workspace,
           record or prompt): a missing --brief-file (argparse's usage error); `gh repo view`
           printing nameWithOwner null and an unknown field; issue-view printing a title that is no
           string (each edge validated before anything is made).

Seams (ticket #1156, recorded before any test): the same command and stand-ins.

  files    with --new TITLE --body-file FILE instead of a ticket (issue-lifecycle
           #acceptance-lane-start-files): the gh log holds one `issue create` with that title and
           body file and no --parent; issue-view 906 reads back that title and body and no parent;
           the lane started under gh906 (its record, its worktree); `filed=906` printed before
           `key=gh906 ...`.
  filed_stopped  a --new start that stops after filing (the goal's delivery failing once, the
           stand-in's prompt-down) printed `filed=906` all the same; rerun naming 906, the lane
           starts under gh906 and no second issue is filed.
  sub_issue  ticket 907, a sub-issue of 905 (issue-lifecycle #acceptance-lane-start-sub-issue):
           exit 1 naming 905; no worktree, branch, workspace, record or prompt for gh907, no issue
           filed.
  behind_kit  OCTO_FEATHER_KIT_INSTALL a scratch kit clone one commit behind its origin's main
           (issue 1158, #acceptance-lane-start-current-kit): exit 1 naming the install, its commit,
           main's and that it is behind main; no gh or herdr call, so no ticket read or filed, and
           no worktree, branch, workspace, record or prompt.

The other scenarios' kit install is a scratch kit clone at its origin's main, never the real
kit's origin (the command fetches the install's origin first).

Seams (ticket #1157, recorded before any test): issue-lifecycle#acceptance-lane-start-exists and
#acceptance-lane-start-rerun, `octo-feather-lane start` run as a command, the same stand-ins.

  exists   each of a lane record lanes/gh905.toml, a worktree <checkout>-gh905 (on branch gh905),
           a branch gh905 alone, and a Herdr workspace labelled gh905, there before a start: it
           exits 1 naming that one, leaves it as it was and starts no supervisor (no workspace,
           tab or agent started, no prompt, no record, no worktree it did not find).
  rerun    the stand-in refusing the goal's delivery once (its file prompt-down: Herdr's
           agent_blocked, nothing typed): the first run exits 1 naming step goal and that it was
           not delivered; the same start run again prints the first run's pane, and
           the lane has one worktree, one supervisor gh905 (one workspace create), one record,
           the goal then the brief once each, one spawn line and one prod line in the director
           log, and nothing kept of the start; a third run exits 1 naming the record.
  unknown_send  the stand-in timing out the goal's send once (its file prompt-timeout: the goal
           submitted, Herdr never seeing a turn; herdr-say exit 124): the first run exits 1
           naming step goal, delivery unknown and --shown/--absent; the same start again exits 1
           naming the unknown send, the supervisor's pane and what to look at, and sends nothing
           (the goal once in the pane); `--absent brief` is refused, no brief send being unknown;
           with `--shown goal` the start finishes: the goal and the brief once each.

Seam (ticket #1159, recorded before any test): `octo-feather-lane start`, as above.

  help_    `start --help` and `start -h`, the kit install behind its origin's main: exit 0, stdout
           the start entry of `octo-feather-lane --help` alone (every step agents/director.md points
           to it for: the parent filed or taken, the worktree and branch, the supervisor, the lane
           record, the goal, the brief, the director log line, the refusals, the rerun, and the
           brake: issue 1346); no gh or herdr call and nothing made.

Seams (ticket #1346, recorded before any test): issue-lifecycle#acceptance-lane-start-clear and
#acceptance-lane-start-unread, `octo-feather-lane start`, the same stand-ins; every scenario's Pi
config (PI_CODING_AGENT_DIR) and state (XDG_STATE_HOME) in its scratch, so none reaches the box's
route or readings, the route there none unless a scenario names one (route) and the start saying
so. The brake's cases ride the scenarios above, adding no gh store entry:

  started  the route testkit/provider.py replaying the real route's recorded answers
           (fixtures/lane-brake/, scripts/lane_brake.py record): before `key=...` the usage line
           (window, share, the answer's Date, the route's host, burn, reset, course, under the
           line, worked by hand in CLEAR); usage-readings.jsonl holds that one reading, its time
           and window's share and reset only.
  unicode_title  the route at a closed port: `usage: not read (... Connection refused)` and no
           reading this week, then the lane starts; nothing stored.
  files    the route replaying the real recorded 401: `usage: not read (... answered 401)`, then
           filed=906 and the lane; nothing stored.
  rerun    its first run with baseUrl `not-a-url` (no request can be built): `usage: not read
           (... unknown url type ...)`, the supervisor started (code review on c973ad51).
  filed_stopped  its first run with the route replaying the recorded 401 cut short (provider.py
           --truncated: the error body's read fails): `usage: not read (... IncompleteRead ...)`,
           the supervisor started, nothing stored.
  Each of these: the dummy key in no output and no state or Herdr file.
"""

from __future__ import annotations

import contextlib
import json
import re
import socket
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import tomllib
from testkit import HERE, ROOT, Ran, Scratch, kit, main

if TYPE_CHECKING:
    from collections.abc import Generator

TITLE = "Lane start as one command"
OUTCOME = "a scratch proof"
BRIEF = "Build the lane start.\nSpec: docs/specs/issue-lifecycle.spec.html\n"
DIRECTOR = {"OCTO_FEATHER_ROLE": "director", "HERDR_PANE_ID": "w0:p1", "HERDR_WORKSPACE_ID": "w0"}
# The brake's route (issue 1346): a dummy key that must show nowhere, and the real route's answers
# recorded by scripts/lane_brake.py record (each file's note), replayed by testkit/provider.py.
KEY = "testkit-dummy-anthropic-key-1346"
RECORDED = Path(__file__).resolve().parent / "fixtures" / "lane-brake"
# The recording's reading as a person reads it: Date Sat, 28 Nov 2026 06:19:36 GMT; 7d utilization
# 0.19, reset 1796266800. Worked by hand: the week from 2026-11-26T03:00Z, 51.33 h in, so 0.37%/h;
# 116.67 h to the reset, so 19% + 43% = 62%.
CLEAR = (
    "usage: 7d 19% used at 2026-11-28T06:19:36Z ({host}), burn 0.37%/h (week average 0.37%/h,"
    " last 6h none), reset 2026-12-03T03:00:00Z, course 62% at reset, under 90% (reserve 10%,"
    " gate-budget.toml usage_reserve)"
)
NOT_READ = "usage: not read ({why}); no reading this week: the brake did not stop this start"


def show(line: str) -> None:
    """One observation on stdout, for the qc demo's output."""
    sys.stdout.write(line + "\n")


def world(s: Scratch) -> tuple[Path, Path, str]:
    """S's Herdr (director w0:p1, idle), its state dir with director.toml, GitHub (repo o/r, open
    issue 905) and the target: origin with main moved past the director's clone. The Herdr world
    dir, the checkout and origin's main."""
    d = s.root / "herdr"
    d.mkdir()
    director = {"name": "director", "pane_id": "w0:p1", "workspace_id": "w0", "tab_id": "w0:t1"}
    (d / "agents.json").write_text(json.dumps({"w0:p1": director | {"agent_status": "idle"}}))
    for k in [k for k in s.env if k.startswith(("HERDR_", "OCTO_FEATHER_"))]:
        del s.env[k]
    s.env["FAKE_HERDR"] = str(d)
    s.env["PI_CODING_AGENT_DIR"] = str(s.root / "pi-agent")  # never the box's route
    s.env["XDG_STATE_HOME"] = str(s.home / ".local" / "state")  # never the box's readings
    state = s.home / ".local" / "state" / "octo-feather"
    state.mkdir(parents=True)
    (state / "director.toml").write_text('pane = "w0:p1"\n')
    s.identity()
    kit_origin, kit_install = s.root / "kit-origin.git", s.root / "kit-install"
    s.run(["git", "init", "-q", "--bare", "-b", "main", str(kit_origin)])
    s.run(["git", "clone", "-q", str(kit_origin), str(kit_install)])
    s.git(kit_install, "commit", "-q", "--allow-empty", "-m", "kit")
    s.git(kit_install, "push", "-q", "origin", "main")
    s.env["OCTO_FEATHER_KIT_INSTALL"] = str(kit_install)
    s.gh.store("repo.json", {"nameWithOwner": "o/r"})
    none: list[object] = []
    issue: dict[str, object] = {"number": 905, "title": TITLE, "body": "b", "state": "OPEN"}
    issue |= {"url": "https://github.com/o/r/issues/905", "parent": None}
    issue |= {"blockedBy": {"nodes": none}, "subIssues": {"totalCount": 0, "nodes": none}}
    s.gh.store("issue/905.json", issue)
    origin, seed = s.root / "origin.git", s.root / "seed"
    s.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)])
    s.run(["git", "clone", "-q", str(origin), str(seed)])
    s.git(seed, "commit", "-q", "--allow-empty", "-m", "first")
    s.git(seed, "push", "-q", "origin", "main")
    checkout = s.root / "src" / "target"
    s.run(["git", "clone", "-q", str(origin), str(checkout)])
    s.git(seed, "commit", "-q", "--allow-empty", "-m", "main moved")
    s.git(seed, "push", "-q", "origin", "main")
    return d, checkout, s.git(seed, "rev-parse", "HEAD")


def route(s: Scratch, base: str) -> None:
    """S's Pi config: providers.anthropic at BASE with the dummy KEY."""
    agent = Path(s.env["PI_CODING_AGENT_DIR"])
    agent.mkdir(parents=True, exist_ok=True)
    anthropic = {"baseUrl": base, "apiKey": KEY}
    (agent / "models.json").write_text(json.dumps({"providers": {"anthropic": anthropic}}))


@contextlib.contextmanager
def replaying(s: Scratch, recorded: Path, *flags: str) -> Generator[str]:
    """The route at testkit/provider.py replaying RECORDED with FLAGS (its header; route); its host
    while it serves."""
    p = subprocess.Popen(
        [sys.executable, str(HERE / "provider.py"), "--replay", str(recorded), *flags],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert p.stdout is not None
        host = f"127.0.0.1:{p.stdout.readline().strip()}"
        route(s, f"http://{host}")
        yield host
    finally:
        p.kill()
        p.wait()


def closed(s: Scratch) -> str:
    """The route at a port no one listens on (bound, then closed); its host."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        host = f"127.0.0.1:{sock.getsockname()[1]}"
    route(s, f"http://{host}")
    return host


def supervised(d: Path, key: str) -> str:
    """The pane of the supervisor KEY the start started (testkit Herdr's agents), else fail."""
    agents = json.loads((d / "agents.json").read_text())
    panes = [p for p, g in agents.items() if g["name"] == key]
    assert len(panes) == 1, agents
    return panes[0]


def readings(s: Scratch) -> Path:
    return s.home / ".local" / "state" / "octo-feather" / "usage-readings.jsonl"


def keyless(s: Scratch, *outs: str) -> None:
    """The dummy KEY in none of OUTS, the readings, the state dir's files or the Herdr world's."""
    files = [p for d in (s.home / ".local" / "state", s.root / "herdr") for p in d.rglob("*")]
    for text in [*outs, *(p.read_text() for p in files if p.is_file())]:
        assert KEY not in text, text
    show(f"the key in no output and none of {len(files)} state and Herdr files")


def clear(s: Scratch, r: Ran, host: str) -> str:
    """R, a start on the replayed recording at HOST, printed the usage line (CLEAR) first and
    stored that one reading, the key nowhere; its other line."""
    usage, out = r.out.split("\n")
    assert usage == CLEAR.format(host=host), usage
    show(f"printed first: {usage}")
    stored = [json.loads(x) for x in readings(s).read_text().splitlines()]
    window = {"used": 0.19, "reset": "2026-12-03T03:00:00Z"}
    assert stored == [{"at": "2026-11-28T06:19:36Z", "windows": {"7d": window}}], stored
    show(f"usage-readings.jsonl: {stored}")
    keyless(s, r.out, r.err)
    return out


def started(s: Scratch) -> None:
    d, checkout, main_ = world(s)
    brief = s.root / "brief.md"
    brief.write_text(BRIEF)
    cmd = [kit("octo-feather-lane"), "start", "905", "--goal", TITLE, "--outcome", OUTCOME]
    with replaying(s, RECORDED) as host:
        r = s.run([*cmd, "--brief-file", str(brief)], cwd=checkout, env=DIRECTOR)
    out = clear(s, r, host)
    m = re.fullmatch(r"key=gh905 pane=(\S+) issue=905", out)
    assert m, out
    pane = m.group(1)
    show(f"printed: {out}")

    agents = json.loads((d / "agents.json").read_text())
    sup = agents[pane]
    wt = checkout.with_name("target-gh905")
    got_agent = json.loads(s.run(["herdr", "agent", "get", "gh905"]).out)["result"]["agent"]
    assert (got_agent["pane_id"], got_agent["cwd"]) == (pane, str(wt)), got_agent
    show(f"herdr agent get gh905: pane {pane}, cwd {got_agent['cwd']}")
    calls = (d / "log").read_text().splitlines()
    assert [c for c in calls if c.startswith("workspace create ")] == [
        c for c in calls if c.startswith("workspace create --label gh905 ")
    ], calls
    assert len([c for c in calls if c.startswith("workspace create ")]) == 1, calls
    assert (sup["name"], sup["label"]) == ("gh905", "supervisor"), sup
    assert sup["env"]["OCTO_FEATHER_ROLE"] == "supervisor", sup
    assert [p for p, g in agents.items() if g["workspace_id"] == sup["workspace_id"]] == [pane]
    show(
        f"workspace gh905 ({sup['workspace_id']}) holds supervisor gh905 at {pane}, tab supervisor"
    )

    assert s.git(wt, "rev-parse", "--abbrev-ref", "HEAD") == "gh905"
    assert s.git(wt, "rev-parse", "HEAD") == main_, "the branch is not at origin's main"
    show(f"worktree {wt.name} on branch gh905 at origin's main {main_[:12]}")

    state = s.home / ".local" / "state" / "octo-feather"
    rec = tomllib.loads((state / "lanes" / "gh905.toml").read_text())
    at = rec.pop("started_at")
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", at), at
    want = {"supervisor": pane, "repository": "o/r", "issue": "gh905", "goal": TITLE}
    assert rec == want | {"waiting_on": ""}, rec
    show(f"lanes/gh905.toml: {rec | {'started_at': at}}")

    goal = (
        f"/goal {OUTCOME} for gh905, delivered through implement-spec; done when an owner gate"
        " is pending (review link or merge ask sent) or PR merged and lane torn down"
    )
    head = (
        "Lane facts (octo-feather-lane start):\nLane key: gh905\n"
        f"Parent issue: 905 {TITLE} (https://github.com/o/r/issues/905)\n"
        f"Director pane: w0:p1\nWorktree: {wt}\nBranch: gh905\nMain commit: {main_}\n\n"
    )
    got = (d / "prompts").read_text()
    assert got == f"{pane}\t{goal}\n{pane}\t{head}{BRIEF}\n", got
    show(f"{pane} received the goal, then the brief: {got!r}")

    log = [json.loads(x) for x in (state / "director.handoffs.jsonl").read_text().splitlines()]
    prods = [x for x in log if x["kind"] == "prod"]
    assert [x for x in log if x not in prods] == [x for x in log if x["kind"] == "spawn"], log
    assert [(x["name"], x["pane"]) for x in log if x["kind"] == "spawn"] == [("gh905", pane)]
    assert len(prods) == 1, prods
    assert prods[0]["issue"] == "gh905", prods
    assert set(prods[0]) == {"at", "kind", "issue", "note"}, prods
    assert pane in prods[0]["note"], prods
    show(f"director log: one prod line {prods[0]}")


def unicode_title(s: Scratch) -> None:
    _, checkout, _ = world(s)
    brief = s.root / "brief.md"
    brief.write_text(BRIEF)
    title = 'Ship \U0001f680 "quoted" back\\slash'
    cmd = [kit("octo-feather-lane"), "start", f"--goal={title}", f"--brief-file={brief}"]
    host = closed(s)
    r = s.run([*cmd, "--outcome", OUTCOME, "905"], cwd=checkout, env=DIRECTOR)
    why = f"GET {host}/v1/models: [Errno 111] Connection refused"
    assert r.out.split("\n")[0] == NOT_READ.format(why=why), r.out
    assert re.fullmatch(r"key=gh905 pane=\S+ issue=905", r.out.split("\n")[1]), r.out
    assert not readings(s).exists()
    show(f"route at a closed port: printed {r.out!r}, nothing stored")
    keyless(s, r.out, r.err)
    state = s.home / ".local" / "state" / "octo-feather"
    rec = tomllib.loads((state / "lanes" / "gh905.toml").read_text(encoding="utf-8"))
    assert rec["goal"] == title, rec
    show(f"lanes/gh905.toml goal reads back {rec['goal']!r}")


def nothing_made(s: Scratch, d: Path, checkout: Path, key: str = "gh905") -> None:
    """No worktree, branch, workspace, record or prompt for KEY."""
    assert not checkout.with_name(f"target-{key}").exists()
    assert s.git(checkout, "branch", "--list", key) == ""
    calls = (d / "log").read_text().splitlines() if (d / "log").exists() else []
    assert not [c for c in calls if c.startswith(("workspace create", "tab create"))], calls
    assert not (d / "prompts").exists()
    assert not (s.home / ".local" / "state" / "octo-feather" / "lanes" / f"{key}.toml").exists()


def refused(s: Scratch) -> None:
    d, checkout, _ = world(s)
    brief = s.root / "brief.md"
    brief.write_text(BRIEF)
    cmd = [kit("octo-feather-lane"), "start", "905", "--goal", TITLE, "--outcome", OUTCOME]
    err = s.run(cmd, cwd=checkout, env=DIRECTOR, want=1).err
    assert "the following arguments are required: --brief-file" in err, err
    nothing_made(s, d, checkout)
    show(f"no --brief-file: exit 1, {err}")

    cmd += ["--brief-file", str(brief)]
    s.gh.store("repo.json", {"nameWithOwner": None, "unexpected": True})
    err = s.run(cmd, cwd=checkout, env=DIRECTOR, want=1).err
    assert "gh repo view printed" in err, err
    assert "want exactly nameWithOwner" in err, err
    nothing_made(s, d, checkout)
    show(f"gh repo view malformed: exit 1, {err}")

    s.gh.store("repo.json", {"nameWithOwner": "o/r"})
    issue = json.loads((s.gh.dir / "issue" / "905.json").read_text()) | {"title": 7}
    s.gh.store("issue/905.json", issue)
    err = s.run(cmd, cwd=checkout, env=DIRECTOR, want=1).err
    assert "issue-view 905 printed title is no string" in err, err
    nothing_made(s, d, checkout)
    show(f"issue-view malformed: exit 1, {err}")


NEW = "Scratch lane"
BODY = "The scratch lane's parent.\nIt has two lines.\n"


def new_start(s: Scratch) -> tuple[list[str], Path]:
    """The --new start's command (title NEW, body file BODY) and the body file."""
    brief, body = s.root / "brief.md", s.root / "body.md"
    brief.write_text(BRIEF)
    body.write_text(BODY)
    cmd = [kit("octo-feather-lane"), "start", "--new", NEW, "--body-file", str(body)]
    return [*cmd, "--goal", NEW, "--outcome", OUTCOME, "--brief-file", str(brief)], body


def creates(s: Scratch) -> list[str]:
    """The gh log's issue create calls."""
    return [c for c in s.gh.log() if c.startswith("issue create")]


def files(s: Scratch) -> None:
    _, checkout, _ = world(s)
    cmd, body = new_start(s)
    with replaying(s, RECORDED / "unauthorized") as host:
        r = s.run(cmd, cwd=checkout, env=DIRECTOR)
    out = r.out.splitlines()
    assert out[0] == NOT_READ.format(why=f"GET {host}/v1/models answered 401"), out
    assert out[1] == "filed=906", out
    assert re.fullmatch(r"key=gh906 pane=\S+ issue=906", out[2]), out
    assert len(out) == 3, out
    assert not readings(s).exists()
    show(f"printed: {out}")
    keyless(s, r.out, r.err)
    assert creates(s) == [f"issue create --title {NEW} --body-file {body}"], s.gh.log()
    show(f"gh log: {creates(s)}")
    view = json.loads(
        s.run(
            [str(ROOT / ".agents" / "skills" / "github-issues" / "scripts" / "issue-view"), "906"]
        ).out
    )
    assert (view["title"], view["body"], view["parent"]) == (NEW, BODY, None), view
    show(f"issue-view 906: title {view['title']!r}, body {view['body']!r}, parent None")
    state = s.home / ".local" / "state" / "octo-feather"
    rec = tomllib.loads((state / "lanes" / "gh906.toml").read_text())
    assert (rec["issue"], rec["goal"]) == ("gh906", NEW), rec
    wt = checkout.with_name("target-gh906")
    assert s.git(wt, "rev-parse", "--abbrev-ref", "HEAD") == "gh906"
    show(f"lane started under gh906: record {rec}, worktree {wt.name} on gh906")


def filed_stopped(s: Scratch) -> None:
    d, checkout, _ = world(s)
    cmd, _ = new_start(s)
    (d / "prompt-down").write_text("")
    with replaying(s, RECORDED / "unauthorized", "--truncated") as host:
        r = s.run(cmd, cwd=checkout, env=DIRECTOR, want=1)
    why = f"GET {host}/v1/models: IncompleteRead(27 bytes read, 100 more expected)"
    assert r.out.split("\n") == [NOT_READ.format(why=why), "filed=906"], r.out
    assert "step goal (made so far: " in r.err, r.err
    show(f"the 401's body cut short: printed {r.out!r}, supervisor {supervised(d, 'gh906')}")
    assert not readings(s).exists()
    keyless(s, r.out, r.err)
    show(f"stopped after filing: exit 1, printed {r.out!r}, {r.err}")
    rerun = [kit("octo-feather-lane"), "start", "906", *cmd[cmd.index("--goal") :]]
    out = s.run(rerun, cwd=checkout, env=DIRECTOR).out
    assert re.fullmatch(r"key=gh906 pane=\S+ issue=906", out), out
    assert len(creates(s)) == 1, s.gh.log()
    show(f"rerun naming 906: {out}; one issue filed")


def sub_issue(s: Scratch) -> None:
    d, checkout, _ = world(s)
    brief = s.root / "brief.md"
    brief.write_text(BRIEF)
    none: list[object] = []
    issue: dict[str, object] = {"number": 907, "title": "A child", "body": "b", "state": "OPEN"}
    issue |= {"url": "https://github.com/o/r/issues/907", "parent": {"number": 905}}
    issue |= {"blockedBy": {"nodes": none}, "subIssues": {"totalCount": 0, "nodes": none}}
    s.gh.store("issue/907.json", issue)
    cmd = [kit("octo-feather-lane"), "start", "907", "--goal", "A child", "--outcome", OUTCOME]
    r = s.run([*cmd, "--brief-file", str(brief)], cwd=checkout, env=DIRECTOR, want=1)
    assert "ticket 907 is a sub-issue of 905" in r.err, r.err
    assert r.out.startswith("usage: not read ("), r.out
    assert "\n" not in r.out, r.out
    nothing_made(s, d, checkout, "gh907")
    assert not creates(s), s.gh.log()
    show(f"sub-issue 907: exit 1, {r.err}")


def no_supervisor(d: Path) -> None:
    """No workspace, tab or agent started, no prompt sent."""
    calls = (d / "log").read_text().splitlines() if (d / "log").exists() else []
    made = ("workspace create", "tab create", "agent start")
    assert not [c for c in calls if c.startswith(made)], calls
    assert not (d / "prompts").exists()


def exists(s: Scratch) -> None:
    d, checkout, main_ = world(s)
    brief = s.root / "brief.md"
    brief.write_text(BRIEF)
    cmd = [kit("octo-feather-lane"), "start", "905", "--goal", TITLE, "--outcome", OUTCOME]
    cmd += ["--brief-file", str(brief)]
    lanes = s.home / ".local" / "state" / "octo-feather" / "lanes"
    wt = checkout.with_name("target-gh905")

    lanes.mkdir()
    record = lanes / "gh905.toml"
    record.write_text('supervisor = "w7:p7"\nissue = "gh905"\n')
    err = s.run(cmd, cwd=checkout, env=DIRECTOR, want=1).err
    assert f"lane gh905 exists: lane record {record};" in err, err
    assert record.read_text() == 'supervisor = "w7:p7"\nissue = "gh905"\n'
    assert not wt.exists()
    assert s.git(checkout, "branch", "--list", "gh905") == ""
    no_supervisor(d)
    show(f"record there: exit 1, {err}")
    record.unlink()

    s.git(checkout, "worktree", "add", "-q", "-b", "gh905", str(wt))
    head = s.git(wt, "rev-parse", "HEAD")
    err = s.run(cmd, cwd=checkout, env=DIRECTOR, want=1).err
    assert f"lane gh905 exists: worktree {wt}, branch gh905;" in err, err
    assert s.git(wt, "rev-parse", "--abbrev-ref", "HEAD") == "gh905"
    assert s.git(wt, "rev-parse", "HEAD") == head != main_
    assert not record.exists()
    no_supervisor(d)
    show(f"worktree there: exit 1, {err}")
    s.git(checkout, "worktree", "remove", str(wt))

    err = s.run(cmd, cwd=checkout, env=DIRECTOR, want=1).err
    assert "lane gh905 exists: branch gh905;" in err, err
    assert s.git(checkout, "rev-parse", "gh905") == head
    assert not wt.exists()
    no_supervisor(d)
    show(f"branch there: exit 1, {err}")
    s.git(checkout, "branch", "-q", "-D", "gh905")

    agents = json.loads((d / "agents.json").read_text())
    other = {"name": "gh905", "pane_id": "w5:p9", "workspace_id": "w5", "tab_id": "w5:t9"}
    agents["w5:p9"] = other | {"agent_status": "working"}
    (d / "agents.json").write_text(json.dumps(agents))
    (d / "workspaces.json").write_text(json.dumps({"w5": "gh905"}))
    err = s.run(cmd, cwd=checkout, env=DIRECTOR, want=1).err
    assert "lane gh905 exists: Herdr workspace gh905 (w5);" in err, err
    assert json.loads((d / "agents.json").read_text()) == agents
    assert not wt.exists()
    assert s.git(checkout, "branch", "--list", "gh905") == ""
    assert not record.exists()
    no_supervisor(d)
    show(f"workspace there: exit 1, {err}")


def rerun(s: Scratch) -> None:
    d, checkout, main_ = world(s)
    brief = s.root / "brief.md"
    brief.write_text(BRIEF)
    cmd = [kit("octo-feather-lane"), "start", "905", "--goal", TITLE, "--outcome", OUTCOME]
    cmd += ["--brief-file", str(brief)]
    state = s.home / ".local" / "state" / "octo-feather"
    wt = checkout.with_name("target-gh905")

    (d / "prompt-down").write_text("")
    route(s, "not-a-url")
    r = s.run(cmd, cwd=checkout, env=DIRECTOR, want=1)
    why = "GET not-a-url/v1/models: unknown url type: 'not-a-url/v1/models'"
    assert r.out == NOT_READ.format(why=why), r.out
    show(f"baseUrl not-a-url: printed {r.out!r}, supervisor {supervised(d, 'gh905')}")
    keyless(s, r.out, r.err)
    err = r.err
    assert "step goal (made so far: " in err, err
    assert " exit 75 (" in err, err
    assert "not delivered; rerun once the cause is fixed" in err, err
    assert not (d / "prompts").exists()
    show(f"first run: exit 1, {err}")

    out = s.run(cmd, cwd=checkout, env=DIRECTOR).out
    m = re.fullmatch(r"key=gh905 pane=(\S+) issue=905", out)
    assert m, out
    pane = m.group(1)
    show(f"second run: {out}")

    trees = s.git(checkout, "worktree", "list", "--porcelain").splitlines()
    assert [x for x in trees if x.startswith("worktree ")] == [
        f"worktree {checkout}",
        f"worktree {wt}",
    ], trees
    assert s.git(wt, "rev-parse", "HEAD") == main_
    agents = json.loads((d / "agents.json").read_text())
    assert [p for p, g in agents.items() if g["name"] == "gh905"] == [pane], agents
    calls = (d / "log").read_text().splitlines()
    assert len([c for c in calls if c.startswith("workspace create ")]) == 1, calls
    assert len([c for c in calls if c.startswith("agent start ")]) == 1, calls
    lanes = state / "lanes"
    assert sorted(p.name for p in lanes.iterdir()) == ["gh905.toml"], list(lanes.iterdir())
    rec = tomllib.loads((lanes / "gh905.toml").read_text())
    assert (rec["supervisor"], rec["goal"]) == (pane, TITLE), rec
    show(f"one worktree {wt.name}, one supervisor gh905 at {pane}, one record {rec}")

    goal = (
        f"/goal {OUTCOME} for gh905, delivered through implement-spec; done when an owner gate"
        " is pending (review link or merge ask sent) or PR merged and lane torn down"
    )
    head = (
        "Lane facts (octo-feather-lane start):\nLane key: gh905\n"
        f"Parent issue: 905 {TITLE} (https://github.com/o/r/issues/905)\n"
        f"Director pane: w0:p1\nWorktree: {wt}\nBranch: gh905\nMain commit: {main_}\n\n"
    )
    got = (d / "prompts").read_text()
    assert got == f"{pane}\t{goal}\n{pane}\t{head}{BRIEF}\n", got
    show(f"{pane} received the goal, then the brief, once each")
    log = [json.loads(x) for x in (state / "director.handoffs.jsonl").read_text().splitlines()]
    assert [(x["kind"], x.get("name") or x.get("issue")) for x in log] == [
        ("spawn", "gh905"),
        ("prod", "gh905"),
    ], log
    show("director log: one spawn line, one prod line")

    err = s.run(cmd, cwd=checkout, env=DIRECTOR, want=1).err
    assert f"lane gh905 exists: lane record {lanes / 'gh905.toml'}, " in err, err
    assert (d / "prompts").read_text() == got
    show(f"third run: exit 1, {err}")


def unknown_send(s: Scratch) -> None:
    d, checkout, main_ = world(s)
    brief = s.root / "brief.md"
    brief.write_text(BRIEF)
    cmd = [kit("octo-feather-lane"), "start", "905", "--goal", TITLE, "--outcome", OUTCOME]
    cmd += ["--brief-file", str(brief)]
    wt = checkout.with_name("target-gh905")
    goal = (
        f"/goal {OUTCOME} for gh905, delivered through implement-spec; done when an owner gate"
        " is pending (review link or merge ask sent) or PR merged and lane torn down"
    )

    (d / "prompt-timeout").write_text("")
    err = s.run(cmd, cwd=checkout, env=DIRECTOR, want=1).err
    agents = json.loads((d / "agents.json").read_text())
    pane = next(p for p, g in agents.items() if g["name"] == "gh905")
    assert f"step goal (made so far: worktree {wt}" in err, err
    assert f"herdr-say {pane} exit 124 (" in err, err
    assert "delivery unknown, not sent again blind" in err, err
    assert (d / "prompts").read_text() == f"{pane}\t{goal}\n"
    show(f"first run, the goal's send timed out: exit 1, {err}")

    err = s.run(cmd, cwd=checkout, env=DIRECTOR, want=1).err
    assert f"step goal: the goal send to {pane} is unknown (herdr-say {pane} exit 124" in err, err
    assert "not sent again blind (comms spec #delivery-unknown)" in err, err
    assert f"look at supervisor pane {pane} (herdr pane read {pane})" in err, err
    assert "rerun this start with --shown goal" in err, err
    assert "with --absent goal (sent once more)" in err, err
    assert (d / "prompts").read_text() == f"{pane}\t{goal}\n"
    show(f"second run, not sent again: exit 1, {err}")

    err = s.run([*cmd, "--absent", "brief"], cwd=checkout, env=DIRECTOR, want=1).err
    assert "--absent brief, but no unknown send of it is kept" in err, err
    assert (d / "prompts").read_text() == f"{pane}\t{goal}\n"

    out = s.run([*cmd, "--shown", "goal"], cwd=checkout, env=DIRECTOR).out
    assert out == f"key=gh905 pane={pane} issue=905", out
    head = (
        "Lane facts (octo-feather-lane start):\nLane key: gh905\n"
        f"Parent issue: 905 {TITLE} (https://github.com/o/r/issues/905)\n"
        f"Director pane: w0:p1\nWorktree: {wt}\nBranch: gh905\nMain commit: {main_}\n\n"
    )
    got = (d / "prompts").read_text()
    assert got == f"{pane}\t{goal}\n{pane}\t{head}{BRIEF}\n", got
    show(f"--shown goal: {out}; {pane} holds the goal, then the brief, once each")


def behind_kit(s: Scratch) -> None:
    d, checkout, _ = world(s)
    kit_install = s.root / "kit-install"
    head = s.git(kit_install, "rev-parse", "HEAD")
    seed = s.root / "kit-seed"
    s.run(["git", "clone", "-q", str(s.root / "kit-origin.git"), str(seed)])
    s.git(seed, "commit", "-q", "--allow-empty", "-m", "kit moved")
    s.git(seed, "push", "-q", "origin", "main")
    main_ = s.git(seed, "rev-parse", "HEAD")
    brief = s.root / "brief.md"
    brief.write_text(BRIEF)
    cmd = [kit("octo-feather-lane"), "start", "905", "--goal", TITLE, "--outcome", OUTCOME]
    err = s.run([*cmd, "--brief-file", str(brief)], cwd=checkout, env=DIRECTOR, want=1).err
    assert f"kit install {kit_install} at {head} is behind main on its origin ({main_}" in err, err
    assert "post-merge" in err, err
    assert f"git -C {kit_install} merge --ff-only origin/main" in err, err
    assert s.gh.log() == [], s.gh.log()
    nothing_made(s, d, checkout)
    assert not (d / "log").exists(), (d / "log").read_text()
    show(f"kit install one commit behind: exit 1, {err}")


def help_(s: Scratch) -> None:
    d, checkout, _ = world(s)
    seed = s.root / "kit-seed"
    s.run(["git", "clone", "-q", str(s.root / "kit-origin.git"), str(seed)])
    s.git(seed, "commit", "-q", "--allow-empty", "-m", "kit moved")
    s.git(seed, "push", "-q", "origin", "main")
    steps = (
        "issue-create with that title and FILE, a top-level issue, never --parent",
        "adds the worktree `<checkout>-<key>` beside the checkout",
        "new branch `<key>` from origin's main",
        "starts the supervisor with the octo-feather-start",
        "writes lanes/<supervisor name>.toml",
        "sends the supervisor with herdr-say `/goal TEXT for <key>",
        "then the brief: a header",
        "appends one director log line",
        "It refuses a lane that exists",
        "the same start run again",
        "The brake (spec issue-lifecycle #lanes-start",
        "models.json providers.anthropic baseUrl and apiKey",
        "max_tokens 1",
        "anthropic-ratelimit-unified-7d*-utilization and -reset headers",
        "its Date header is now",
        "${XDG_STATE_HOME:-~/.local/state}/octo-feather/usage-readings.jsonl",
        "no less than its first 6 hours",
        "usage_reserve in the kit's gate-budget.toml",
        "a route to another provider",
    )
    for flag in ("--help", "-h"):
        out = s.run([kit("octo-feather-lane"), "start", flag], cwd=checkout, env=DIRECTOR).out
        assert out.startswith("  octo-feather-lane start TICKET|--new TITLE"), out
        assert out.rstrip().endswith("and the start goes on."), out
        for step in steps:
            assert step in out, (step, out)
    assert s.gh.log() == [], s.gh.log()
    nothing_made(s, d, checkout)
    assert not (d / "log").exists(), (d / "log").read_text()
    show(f"start --help, kit behind: exit 0, {len(out.splitlines())} lines, the start entry")


if __name__ == "__main__":
    main(
        started,
        unicode_title,
        refused,
        files,
        filed_stopped,
        sub_issue,
        exists,
        unknown_send,
        rerun,
        behind_kit,
        help_,
    )
