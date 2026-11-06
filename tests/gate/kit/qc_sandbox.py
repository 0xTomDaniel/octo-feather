"""The qc sandbox run by hand on anthropics/sandbox-runtime (srt; octo-feather-qc-sandbox
--help, docs/adr/0022 the sandbox paragraph), no model: `octo-feather-qc-sandbox -- CMD` in a
repo, every input defaulted, prints its pre-run proof naming srt, and CMD's escapes fail (a
write to HOME, an umount of a mask, a live Herdr session through the shim) and leave nothing
(its worktree write discarded, listed in the upper record); without srt installed where mise's
data dir says, it refuses before any judge, naming the kit's install command; the network: a
run with no Pi reaches no host, a Pi run only the hosts of Pi's models.json (here a local
provider, through srt's proxy)."""

from __future__ import annotations

import http.server
import json
import threading
from typing import TYPE_CHECKING

from testkit import Scratch, kit, main, tool_homes

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
    r = repo(s)
    empty = s.root / "mise-data"
    empty.mkdir()
    ran = s.run(
        [kit("octo-feather-qc-sandbox"), "--", "true"],
        cwd=r,
        want=66,
        env=tool_homes() | {"MISE_DATA_DIR": str(empty)},
    )
    for want in (
        "FAIL mise offline",
        "npm:@anthropic-ai/sandbox-runtime@",
        "octo-feather-mise-install",
        "judge not started (exit 66)",
    ):
        assert want in ran.err, (want, ran.err)


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
    main(by_hand, srt_missing, network)
