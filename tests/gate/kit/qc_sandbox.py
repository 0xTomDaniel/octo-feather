"""The qc sandbox run by hand on anthropics/sandbox-runtime (srt; octo-feather-qc-sandbox
--help, docs/adr/0022 the sandbox paragraph), no model: `octo-feather-qc-sandbox -- CMD` in a
repo, every input defaulted, prints its pre-run proof naming srt, and CMD's escapes fail (a
write to HOME, an umount of a mask, a live Herdr session through the shim) and leave nothing
(its worktree write discarded, listed in the upper record); without srt in the kit's
node_modules (no pnpm install yet), it refuses before any judge, naming the install command; the
network: a run with no Pi reaches no host, a Pi run only the hosts of Pi's models.json (here a
local provider, through srt's proxy); run by hand inside a qc sandbox (nested), its proof passes."""

from __future__ import annotations

import http.server
import json
import re
import shutil
import threading
from typing import TYPE_CHECKING

from testkit import ROOT, Scratch, kit, main, tool_homes

if TYPE_CHECKING:
    from pathlib import Path

SRT = "qc sandbox: ok   judge runs in the srt sandbox (@anthropic-ai/sandbox-runtime "


def repo(s: Scratch) -> Path:
    r = s.root / "repo"
    r.mkdir()
    s.git(r, "init", "-q", "-b", "main")
    (r / "README").write_text("x\n")
    s.git(r, "add", "-A")
    s.git(r, "commit", "-qm", "init")
    (s.home / ".config" / "herdr").mkdir(parents=True)
    return r


def by_hand(s: Scratch) -> None:
    r = repo(s)
    cmd = (
        'touch "$HOME/x"; echo "touch $?"; umount "$HOME/.config/herdr"; echo "umount $?"; '
        'herdr --session default workspace list; echo w > newfile; echo "wrote $?"'
    )
    ran = s.run([kit("octo-feather-qc-sandbox"), "--", "sh", "-c", cmd], cwd=r, env=tool_homes())
    assert SRT in ran.err, ran.err
    for want in ("touch 1", "umount 32", "wrote 0"):
        assert want in ran.out, (want, ran.out)
    assert "FAIL" not in ran.err, ran.err
    assert '{"upper": [["new", "newfile"]]}' in ran.err, ran.err
    assert not (s.home / "x").exists()
    assert not (r / "newfile").exists()
    assert s.git(r, "status", "--porcelain") == ""


def srt_missing(s: Scratch) -> None:
    """A kit checkout whose node_modules lacks srt (no `pnpm install` yet): refused before any
    judge, naming the package.json pin and the install command."""
    r = repo(s)
    k = s.root / "kit"
    shutil.copytree(ROOT / "scripts", k / "scripts", symlinks=True)
    shutil.copy(ROOT / "package.json", k)
    ran = s.run(
        [str(k / "scripts" / "octo-feather-qc-sandbox"), "--", "true"],
        cwd=r,
        want=66,
        env=tool_homes(),
    )
    for want in (
        "qc sandbox: FAIL srt (@anthropic-ai/sandbox-runtime ",
        f"not installed in {k}/node_modules (found: none)",
        f"run pnpm install --frozen-lockfile --dir {k}",
        "judge not started (exit 66)",
    ):
        assert want in ran.err, (want, ran.err)


def nested(s: Scratch) -> None:
    """The by-hand run inside a qc sandbox (a nested run, as a demo of the kit judging itself runs
    it): the inner proof passes, its live-record masks holding though the outer run's state dir is
    its caller's (none shows an entry)."""
    r = repo(s)
    sb = kit("octo-feather-qc-sandbox")
    repo2 = 'cd "$(mktemp -d)" && git init -q && git -c user.name=t -c user.email=t@t commit -q --allow-empty -m x'
    inner = f"{repo2} && {sb} -- echo inner-ran"
    ran = s.run([sb, "--", "sh", "-c", inner], cwd=r, env=tool_homes())
    assert "inner-ran" in ran.out, (ran.out, ran.err)
    assert "qc sandbox: FAIL" not in ran.err, ran.err
    masked = re.findall(
        r"live records masked \((\d+) paths, (\d+) bytes or entries visible\)", ran.err
    )
    assert len(masked) == 2, ran.err  # the outer proof's line, then the inner's
    assert all(v == "0" for _, v in masked), masked


class _Ok(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"provider")

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002  # the base class's own name
        pass


def network(s: Scratch) -> None:
    r = repo(s)
    srv = http.server.HTTPServer(("127.0.0.1", 0), _Ok)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}/v1"
    pi = s.home / ".pi" / "agent"
    pi.mkdir(parents=True)
    (pi / "models.json").write_text(
        json.dumps({"providers": {"p": {"baseUrl": url, "apiKey": "k"}}})
    )
    py = f'import urllib.request; print(urllib.request.urlopen("{url}", timeout=5).read().decode())'
    get = f"python3 -c '{py}' 2>&1 | tail -1"
    sb = [kit("octo-feather-qc-sandbox"), "--", "sh", "-c", get]
    none = s.run(sb, cwd=r, env=tool_homes())  # by hand: no Pi, so no host at all
    assert "network allowlist: none" in none.err, none.err
    assert "provider" not in none.out, none.out
    host = url.split("/")[2]
    piran = s.run(sb, cwd=r, env=tool_homes() | {"QC_PI": ""})
    assert f"network allowlist: {host}" in piran.err, piran.err
    assert piran.out == "provider", (piran.out, piran.err)
    srv.shutdown()


if __name__ == "__main__":
    main(by_hand, srt_missing, network, nested)
