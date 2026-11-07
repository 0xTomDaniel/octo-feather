"""The scenarios of tests/gate/kit/test_spend_ledger.py (its items), this file their command
(testkit.main): the kit's spend-ledger Pi extension (extensions/spend-ledger.ts, issue #187,
spec spend#writer-agent). Real Pi at the kit's pin (pi-version), headless, against the fake
provider (testkit/provider.py) whose model has a catalog price (input $1000/M tokens, output
$2000/M; fake/free all 0), then `octo-feather-lane spend`. Credential-free: Pi starts from an
empty environment (PATH, mise's data dir) with an empty HOME, its own PI_CODING_AGENT_DIR and
its own state dir; it reads nothing of the box's ~/.pi or ledger. Each Pi run's stderr is a pipe
read to its end: the extension's detached writers inherit it (spend-ledger.ts, record), so a
run returns only once every writer has exited (readiness, never a wait), and `spend` then counts
every call it made. Never skips: without pi, or with pi at another version, it fails naming the
install command. tests/spend-ledger-qc.sh, -qa.sh and -qc-unwritable.sh hold the other groups.

`agents` (cases agents, role-unset, pi-role, headless):
  agents      in lane gh149's space (HERDR_WORKSPACE_ID=w37) as implementer: a prompt that calls
              a tool reporting nested usage (tests/fixtures/spend-ledger/nested-tool.ts), then an
              answer: 3 calls (2 model messages, 1 tool result), shown under gh149 and
              implementer with the model, tokens and Pi's cost (spend#acceptance-spend-agents)
  role-unset  no OCTO_FEATHER_ROLE, no Herdr space: the extension's purpose fallback, no lane
  pi-role     the implementer role launched through scripts/pi-role (which loads the extension)
              as a pane launch does, JSON mode, in lane gh149's space, no OCTO_FEATHER_ROLE: its
              message under gh149 and implementer (spend#writer-agent)
  headless    pi-role -p (issue #189), no OCTO_FEATHER_ROLE: implementer in lane gh149's space
              records under gh149 and implementer; code-reviewer in space w99, no lane's, under
              no lane and code-reviewer (spend#rule-lane, spend#writer-agent)
`later` (the ledger as `agents` leaves it, written through `spend record`, the extension's
writer; then cases zero-priced, unwritable, inherited):
  zero-priced fake/free, its catalog rates all 0 (rule: extensions/spend-ledger.ts header, Cost):
              `spend` shows it at $0, its call counted under unknown cost (spend#rule-cost)
  unwritable  the ledger is a directory: same answer and exit 0, stderr names the unrecorded
              spend (spend#rule-write-fails)
  inherited   pi-role agents/implementer.md -p under a parent's inherited
              OCTO_FEATHER_ROLE=supervisor (a supervisor's headless worker): under gh149 and
              implementer, no supervisor row (spend#writer-agent)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from contextlib import ExitStack
from dataclasses import dataclass
from typing import TYPE_CHECKING

from testkit import ROOT, Scratch, kit, main, provider, real_pi, tool_homes

if TYPE_CHECKING:
    from pathlib import Path

TAG = "spend-ledger test"
EXT = ROOT / "extensions" / "spend-ledger.ts"
NESTED = ROOT / "tests" / "fixtures" / "spend-ledger" / "nested-tool.ts"
OK = "fake-answer-ok"


@dataclass
class World:
    s: Scratch
    pi: str
    port: int

    @property
    def state(self) -> Path:
        return self.s.root / "state"

    @property
    def ledger(self) -> Path:
        return self.state / "octo-feather" / "spend.jsonl"

    def pienv(self, **extra: str) -> dict[str, str]:
        """Pi's environment: nothing inherited but PATH (the caller's: the real pi) and mise's
        data dir (the qc sandbox's installs), plus EXTRA."""
        r = self.s.root
        return {
            "PATH": os.environ["PATH"],
            "MISE_DATA_DIR": tool_homes()["MISE_DATA_DIR"],
            "HOME": str(r / "home"),
            "TMPDIR": str(r),
            "XDG_CACHE_HOME": str(r / "cache"),
            "XDG_STATE_HOME": str(self.state),
            "PI_CODING_AGENT_DIR": str(r / "agent"),
            "PI_OFFLINE": "1",
            "PI_SKIP_VERSION_CHECK": "1",
            "PI_TELEMETRY": "0",
            **extra,
        }

    def go(self, cmd: list[str], **extra: str) -> subprocess.CompletedProcess[str]:
        """CMD in the repo under pienv, its stdout and stderr read to their ends (every detached
        writer gone)."""
        return subprocess.run(
            cmd,
            cwd=self.s.root / "repo",
            env=self.pienv(**extra),
            capture_output=True,
            text=True,
            check=False,
        )

    def run(self, prompt: str, model: str = "fake/fake", **extra: str) -> str:
        """One headless pi with the extension and the nested tool: exit 0 and the fake answer;
        its stderr."""
        cmd = [self.pi, "-e", str(EXT), "-e", str(NESTED), "--model", model, "--no-session"]
        p = self.go([*cmd, "-p", prompt], **extra)
        assert p.returncode == 0, f"{TAG}: pi exit {p.returncode}, answer '{p.stdout}': {p.stderr}"
        assert p.stdout.strip() == OK, f"{TAG}: answer '{p.stdout}': {p.stderr}"
        return p.stderr

    def role(self, role: str, *args: str, **extra: str) -> subprocess.CompletedProcess[str]:
        md = str(ROOT / "agents" / f"{role}.md")
        return self.go([kit("pi-role"), md, "--model", "fake/fake", "--no-session", *args], **extra)

    def headless(self, space: str, role: str, **extra: str) -> None:
        p = self.role(role, "-p", "answer", HERDR_WORKSPACE_ID=space, **extra)
        assert p.returncode == 0, f"{TAG}: headless {role}: exit {p.returncode}: {p.stderr}"
        assert p.stdout.strip() == OK, f"{TAG}: headless {role}: answer '{p.stdout}': {p.stderr}"

    def spend(self, calls: int) -> str:
        """`spend`, counting CALLS calls in all (every writer has exited: World.go); its output."""
        env = {"PATH": self.s.env["PATH"], "HOME": str(self.s.root / "home")}
        env["XDG_STATE_HOME"] = str(self.state)
        p = subprocess.run(
            [kit("octo-feather-lane"), "spend"],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        head = re.fullmatch(r"Spend ledger: .* \(([0-9]+) calls?\)", p.stdout.split("\n", 1)[0])
        got = int(head.group(1)) if head else 0
        assert got == calls, f"{TAG}: spend counts {got} calls, want {calls}: {p.stdout}{p.stderr}"
        return p.stdout

    def row(self, out: str, *row: str) -> None:
        """OUT's row (tests/spend-out row: TITLE KEY USD CALLS UNKNOWN IN OUT)."""
        p = subprocess.run(
            [str(ROOT / "tests" / "spend-out"), "row", *row],
            input=out,
            capture_output=True,
            text=True,
            check=False,
        )
        assert p.returncode == 0, f"{TAG}: {p.stdout} in: {out}"


def world(s: Scratch, stack: ExitStack) -> World:
    pi = real_pi(TAG)
    r = s.root
    for d in ("agent", "repo"):  # HOME: the scratch's own, empty
        (r / d).mkdir()
    # The commit identity a role launch needs (#665).
    s.run([kit("pi-role"), "--set-identity", "t", "t@t"], env={"XDG_STATE_HOME": str(r / "state")})
    s.git(r, "-c", "init.defaultBranch=main", "init", "-q", str(r / "repo"))
    (r / "agent" / "settings.json").write_text('{"retry":{"enabled":false}}\n')
    port = stack.enter_context(provider())
    price = {"input": 1000, "output": 2000, "cacheRead": 0, "cacheWrite": 0}
    free = dict.fromkeys(price, 0)
    fake = {
        "baseUrl": f"http://127.0.0.1:{port}/v1",
        "api": "openai-completions",
        "apiKey": "x",
        "models": [{"id": "fake", "cost": price}, {"id": "free", "cost": free}],
    }
    (r / "agent" / "models.json").write_text(json.dumps({"providers": {"fake": fake}}) + "\n")
    lanes = r / "state" / "octo-feather" / "lanes"
    lanes.mkdir(parents=True)
    (lanes / "gh149.toml").write_text('supervisor = "w37:p2"\n')
    return World(s, pi, port)


def agents(s: Scratch) -> None:
    with ExitStack() as stack:
        w = world(s, stack)
        # agents: 2 model messages (0.1 + 0.04 = $0.14; 0.15 + 0.02 = $0.17) and the tool's $0.004.
        w.run(
            "use the tool, then answer", HERDR_WORKSPACE_ID="w37", OCTO_FEATHER_ROLE="implementer"
        )
        o = w.spend(3)
        w.row(o, "lane", "gh149", "0.314000", "3", "0", "257", "33")
        w.row(o, "purpose", "implementer", "0.314000", "3", "0", "257", "33")
        w.row(o, "model", "fake/fake", "0.310000", "2", "0", "250", "30")
        w.row(o, "model", "tool/nested_work", "0.004000", "1", "0", "7", "3")
        # role-unset: purpose agent, no lane.
        w.run("answer")
        o = w.spend(4)
        w.row(o, "lane", "(no lane)", "0.170000", "1", "0", "150", "10")
        w.row(o, "purpose", "agent", "0.170000", "1", "0", "150", "10")
        # pi-role: no -e here; pi-role loads the extension. Not -p: a headless pi-role run drops
        # the Herdr space (scripts/pi-role HEADLESS_UNSET), a pane launch keeps it. No
        # OCTO_FEATHER_ROLE: the role file names the purpose.
        p = w.role("implementer", "--mode", "json", "answer", HERDR_WORKSPACE_ID="w37")
        assert p.returncode == 0, f"{TAG}: pi-role: exit {p.returncode}: {p.stderr}"
        assert OK in p.stdout, f"{TAG}: pi-role: no {OK}: {p.stdout} {p.stderr}"
        o = w.spend(5)
        w.row(o, "lane", "gh149", "0.484000", "4", "0", "407", "43")
        w.row(o, "purpose", "implementer", "0.484000", "4", "0", "407", "43")
        w.row(o, "model", "fake/fake", "0.650000", "4", "0", "550", "50")
        # headless: pi-role -p drops HERDR_WORKSPACE_ID (#77); the spend still finds the lane.
        w.headless("w37", "implementer")
        o = w.spend(6)
        w.row(o, "lane", "gh149", "0.654000", "5", "0", "557", "53")
        w.row(o, "purpose", "implementer", "0.654000", "5", "0", "557", "53")
        w.headless("w99", "code-reviewer")
        o = w.spend(7)
        w.row(o, "lane", "(no lane)", "0.340000", "2", "0", "300", "20")
        w.row(o, "purpose", "code-reviewer", "0.170000", "1", "0", "150", "10")
        w.row(o, "lane", "gh149", "0.654000", "5", "0", "557", "53")


# The ledger as `agents` leaves it: gh149 implementer (fake/fake 100 in 20 out $0.14, 150 in 10
# out $0.17 three times, tool/nested_work 7 in 3 out $0.004); no lane: agent and code-reviewer,
# fake/fake 150 in 10 out $0.17 each.
FF, USE = '"model":"fake/fake"', '"input_tokens":150,"output_tokens":10,"cost_usd":0.17'
GH149 = [
    f'{{{FF},"purpose":"implementer","input_tokens":100,"output_tokens":20,"cost_usd":0.14}}',
    f'{{{FF},"purpose":"implementer",{USE}}}',
    (
        '{"model":"tool/nested_work","purpose":"implementer","input_tokens":7,"output_tokens":3,'
        '"cost_usd":0.004}'
    ),
    f'{{{FF},"purpose":"implementer",{USE}}}',
    f'{{{FF},"purpose":"implementer",{USE}}}',
]
NO_LANE = [f'{{{FF},"purpose":"agent",{USE}}}', f'{{{FF},"purpose":"code-reviewer",{USE}}}']


def later(s: Scratch) -> None:
    with ExitStack() as stack:
        w = world(s, stack)
        env = {"HOME": str(s.root / "home"), "XDG_STATE_HOME": str(w.state)}
        rec = [kit("octo-feather-lane"), "spend", "record"]
        s.run([*rec, "--lane", "gh149"], env=env, stdin="\n".join(GH149) + "\n")
        s.run(rec, env=env, stdin="\n".join(NO_LANE) + "\n")
        # zero-priced: fake/free answers with the same usage (150 in, 10 out); Pi reports $0,
        # spend counts it as unknown cost.
        w.run("answer", "fake/free", HERDR_WORKSPACE_ID="w37", OCTO_FEATHER_ROLE="implementer")
        o = w.spend(8)
        w.row(o, "model", "fake/free", "0.000000", "1", "1", "150", "10")
        w.row(o, "lane", "gh149", "0.654000", "6", "1", "707", "63")
        w.row(o, "model", "fake/fake", "0.990000", "6", "0", "850", "70")
        # unwritable: the ledger path is a directory.
        w.ledger.rename(s.root / "ledger.bak")
        w.ledger.mkdir()
        err = w.run("answer", HERDR_WORKSPACE_ID="w37", OCTO_FEATHER_ROLE="implementer")
        want = (
            "octo-feather-lane spend record: spend unrecorded (1 call(s), $0.170000): cannot write"
        )
        assert want in err, f"{TAG}: unwritable: stderr lacks '{want}': {err}"
        w.ledger.rmdir()
        (s.root / "ledger.bak").rename(w.ledger)
        # inherited: a supervisor's headless worker keeps the parent's OCTO_FEATHER_ROLE=supervisor;
        # the role pi-role launches wins (spend#writer-agent). One more fake/fake answer (150 in,
        # 10 out, $0.17) on gh149 implementer's 6 calls.
        w.headless("w37", "implementer", OCTO_FEATHER_ROLE="supervisor")
        o = w.spend(9)
        w.row(o, "lane and purpose", "gh149 implementer", "0.824000", "7", "1", "857", "73")
        assert "supervisor" not in o, f"{TAG}: inherited: a supervisor row: {o}"


if __name__ == "__main__":
    main(agents, later)
