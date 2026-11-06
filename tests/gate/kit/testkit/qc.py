"""The qc scenarios' shared scratch target and runs (tests/gate/kit/qc_*.py): what `just qc` judges
is octo-feather-qc --help's, its contract quality spec #qc-contract."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from testkit import FIXTURES, ROOT, Ran, Scratch, kit, tool_homes

if TYPE_CHECKING:
    from collections.abc import Mapping

STATUS = "docs/specs/demo.status.json"
MODEL = json.loads((ROOT / "evals" / "judgment-model.json").read_text())["model"]
RID = r"[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}"  # an evidence record id (octo-feather-evidence --help)
# Each qc run killed after this many seconds, as the old scripts bounded theirs: a hang fails.
LIMIT_S = "180"
# Unset in every qc scenario (clean), as the old qc scripts unset them: a Herdr pane's session, a
# qc report dir, a sandbox PATH, the stub judge's modes, a claims gate's claims.
UNSET = (
    "HERDR_SESSION",
    "HERDR_SOCKET_PATH",
    "HERDR_BIN_PATH",
    "HERDR_ENV",
    "OCTO_FEATHER_QC_DIR",
    "OCTO_FEATHER_QC_PATH",
    "OCTO_FEATHER_QC_CLAIMS",
    "FAKE_QC_JUDGE",
    "FAKE_QC_FAIL",
)


def clean(s: Scratch) -> None:
    """S's env without UNSET, with a git identity (as the old qc scripts exported one): a command
    the judged worktree's demo runs may commit, in a kit checkout with no identity of its own."""
    for k in UNSET:
        s.env.pop(k, None)
    for who in ("AUTHOR", "COMMITTER"):
        s.env |= {f"GIT_{who}_NAME": "t", f"GIT_{who}_EMAIL": "t@t"}


def report(r: Ran) -> dict[str, Any]:
    """Qc run R's report: the file its last stdout line names (octo-feather-qc --help, Report)."""
    return json.loads(Path(r.out.splitlines()[-1].rpartition("; report ")[2]).read_text())


def block(out: str, first: str, n: int = 2) -> list[str]:
    """The result block in qc's stdout OUT whose first line starts FIRST: it and the N lines
    after it (as grep -A N); empty when none does."""
    ls = out.splitlines()
    k = next((i for i, x in enumerate(ls) if x.startswith(first)), None)
    return [] if k is None else ls[k : k + n + 1]


def target(s: Scratch, files: Mapping[str, str] = {}) -> Path:
    """S's repo: the good demo spec (tests/fixtures/spec-status/good) and FILES committed, its
    status file then initialized at that commit (octo-feather-spec-status init) and committed."""
    r = s.root / "repo"
    (r / "docs" / "specs").mkdir(parents=True)
    s.git(r, "init", "-q", "-b", "main")
    for k, v in (("user.email", "t@t"), ("user.name", "t"), ("commit.gpgsign", "false")):
        s.git(r, "config", k, v)
    shutil.copy(FIXTURES / "spec-status" / "good" / "demo.spec.html", r / "docs" / "specs")
    for name, text in files.items():
        (r / name).parent.mkdir(parents=True, exist_ok=True)
        (r / name).write_text(text)
    s.git(r, "add", "-A")
    s.git(r, "commit", "-qm", "accepted")
    short = s.git(r, "rev-parse", "--short", "HEAD")
    s.run([kit("octo-feather-spec-status"), "init", "docs/specs/demo.spec.html", short], cwd=r)
    s.git(r, "add", "-A")
    s.git(r, "commit", "-qm", "status")
    return r


def qc(s: Scratch, repo: Path, *args: str, want: int, env: Mapping[str, str] | None = None) -> Ran:
    """`octo-feather-qc STATUS ARGS...` (what `just qc` runs) in REPO, bounded by LIMIT_S."""
    return s.run(
        ["timeout", "-k", "5", LIMIT_S, kit("octo-feather-qc"), STATUS, *args],
        want=want,
        cwd=repo,
        env=env,
    )


def reports(s: Scratch, head: str) -> list[dict[str, object]]:
    """The qc reports at HEAD, oldest first (octo-feather-qc --help, Report)."""
    q = Path(s.run([kit("octo-feather-state")]).out) / "qc"
    return [json.loads(p.read_text()) for p in sorted(q.glob(f"{head}-*.json"))]


def alive(mark: str) -> bool:
    """Whether a process `sleep MARK` runs (its cmdline, world-readable: no other /proc read)."""
    want = f"sleep\0{mark}\0".encode()

    def cmdline(d: Path) -> bytes:
        try:
            return (d / "cmdline").read_bytes()
        except OSError:  # gone meanwhile
            return b""

    return any(cmdline(d) == want for d in Path("/proc").iterdir() if d.name.isdigit())


def gone(mark: str, within: float = 10) -> bool:
    """Whether no `sleep MARK` runs, or none within WITHIN seconds (a process-state wait)."""
    end = time.monotonic() + within
    while alive(mark):
        if time.monotonic() > end:
            return False
        time.sleep(0.01)
    return True


# The "live" box a qc sandbox test's judge must not reach (as tests/lib/qc.sh's throwaway HOME):
# a live Herdr session, gh and git creds, live and archived lanes, the director's files, another
# repo, Pi's credentials; and the secrets and parent route in the caller's env.
BOX_ENV = {
    "LINEAR_API_KEY": "SECRET-linear-key",
    "GH_TOKEN": "SECRET-token",
    "OCTO_FEATHER_PARENT": "wX:p9",
    "HERDR_PANE_ID": "p9",
    "HERDR_TAB_ID": "t9",
    "HERDR_WORKSPACE_ID": "w9",
    "OCTO_FEATHER_SPEND_SPACE": "w9",
}
AUTH = '{"k": "SECRET-pi-auth-0123456789", "exp": 1}\n'
MODELS = '{"providers": {"p": {"apiKey": "SECRET-pi-models-0123456789"}}}\n'


def build_box(p: Scratch) -> None:
    """The live box in P's HOME and the target (scratch/ ignored), as tests/lib/qc.sh does."""
    h = p.home
    live = h / ".local" / "state" / "octo-feather"
    files = {
        ".config/herdr/herdr.sock": "default\n",
        ".config/gh/hosts.yml": "oauth_token: SECRET-gh\n",
        ".git-credentials": "https://x:SECRET-git@github.com\n",
        ".local/state/octo-feather/lanes/gh9.toml": "LIVE\n",
        ".local/state/octo-feather/lanes/archive/gh1.toml": "ARCHIVED\n",
        ".local/state/octo-feather/director.handoffs.jsonl": '{"director":1}\n',
        ".local/state/octo-feather/director.toml": 'pane = "LIVE"\n',
        "src/sib/notes.md": "SIBSECRET\n",  # another repo on the box (#182)
        ".pi/agent/auth.json": AUTH,
        ".pi/agent/models.json": MODELS,
    }
    for rel, text in files.items():
        (h / rel).parent.mkdir(parents=True, exist_ok=True)
        (h / rel).write_text(text)
    assert live.is_dir()
    (h / ".pi" / "agent" / "auth.json").chmod(0o600)
    p.git(h / "src" / "sib", "init", "-q")
    target(p, {".gitignore": "scratch/\n"})


def box(s: Scratch) -> Path:
    """S holding the prepared live box and target (build_box), the fake judge (testkit/judge.py)
    its pi, the box's secrets in its env, reports in S's reports/, a token marking the judge's
    sleeps; its repo."""
    s.prepare("qc-box", build_box)
    clean(s)
    (s.bin / "pi").unlink()
    (s.bin / "pi").symlink_to(ROOT / "tests" / "gate" / "kit" / "testkit" / "judge.py")
    tok = f"{os.getpid()}{time.monotonic_ns() % 100000}"
    s.env |= (
        tool_homes()
        | BOX_ENV
        | {
            "OCTO_FEATHER_QC_DIR": str(s.root / "reports"),
            "FAKE_QC_TOK": tok,
        }
    )
    return s.root / "repo"


def judged(
    s: Scratch, mode: str, *args: str, want: int, env: Mapping[str, str] | None = None
) -> Ran:
    """octo-feather-qc STATUS 5 ARGS in S's repo, the fake judge answering MODE (FAKE_QC), offline
    (`unshare -cn`: no route) and bounded by LIMIT_S; its stdout and stderr in .out, as one."""
    cmd = [
        "unshare",
        "-cn",
        "timeout",
        "-k",
        "5",
        LIMIT_S,
        kit("octo-feather-qc"),
        STATUS,
        "5",
        *args,
    ]
    p = subprocess.run(
        cmd,
        cwd=s.root / "repo",
        env={**s.env, "FAKE_QC": mode, **(env or {})},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    said = f"FAKE_QC={mode} {' '.join(args)}: exit {p.returncode}, want {want}\n{p.stdout}"
    assert p.returncode == want, said
    assert "Traceback" not in p.stdout, f"a traceback: {said}"
    return Ran(p.returncode, p.stdout.rstrip("\n"), "")


def latest(s: Scratch) -> dict[str, Any]:
    """The newest qc report in S's reports/."""
    reps = sorted((s.root / "reports").glob("*.json"), key=lambda f: f.stat().st_mtime_ns)
    return json.loads(reps[-1].read_text())
