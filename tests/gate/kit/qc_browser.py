"""The scenarios of tests/gate/kit/test_qc_browser.py (its items), this file their command
(testkit.main): a browser demo's capture (quality spec #qc-capture, #qc-contract,
#acceptance-qc-capture-browser) through octo-feather-qc (what `just qc` runs) and
octo-feather-evidence read, with no model: a scratch target's qc.toml pins Playwright ([browser]
playwright) and declares a demo with browser = true that screenshots a page in Playwright's
headless Chromium shell. The box's shell lives where `just install-check` names (remote spec
#host-tools: ${XDG_DATA_HOME:-~/.local/share}/octo-feather/ms-playwright/<pin>); the qc sandbox
reaches it read-only by PLAYWRIGHT_BROWSERS_PATH, ~/.cache stays masked, the proof stays all ok,
and the screenshots the demo wrote to $QC_SCREENSHOTS land in the criterion's new evidence
record. A browser demo with no pin, or with no shell installed at it, is refused before anything
runs.
Browser: the box's real headless shell when one is installed (install-check's folder at any pin,
or Playwright's default ~/.cache/ms-playwright), linked into the scratch data dir; else (a
browser-less CI runner) a planted shell that writes a PNG where --screenshot says, which proves
the bind, the environment and the collection without a browser. The scenario prints which. The
target is prepared once per gate run (build)."""

from __future__ import annotations

import json
import os
import re
import struct
import sys
from pathlib import Path
from typing import Any

from testkit import Scratch, fixture, kit, main
from testkit.qc import RID, block, clean, qc, report, target

PIN = "1.64.1"
PAGE = (
    '<!doctype html><title>qc browser demo</title><body style="background:#2a7"><h1>qc browser '
    "demo</h1></body>\n"
)
# The demo, and the shell planted on a runner with no browser (each file's header: what it does).
DEMO = fixture("qc-browser/demo.sh")
PLANTED = fixture("qc-browser/chrome-headless-shell")


def contract(pin: str) -> str:
    return (
        'format = 1\n[entry]\ncommand = "true"\n[services]\n[fixture]\n[values]\n'
        f"{pin}\n"
        '[demo."demo#acceptance-a"]\ncommand = "./demo.sh"\nbrowser = true\n'
        'covers = ["page.html"]\ntests = ["demo.sh"]\n'
    )


def box_shell() -> Path | None:
    """The box's installed headless shell: install-check's folder at any pin, else Playwright's
    default cache."""
    home = Path(os.environ["HOME"])
    data = Path(os.environ.get("XDG_DATA_HOME") or home / ".local" / "share")
    cache = Path(os.environ.get("XDG_CACHE_HOME") or home / ".cache")
    for d in (
        *sorted((data / "octo-feather" / "ms-playwright").glob("*/chromium_headless_shell-*")),
        *sorted((cache / "ms-playwright").glob("chromium_headless_shell-*")),
    ):
        exe = d / "chrome-headless-shell-linux64" / "chrome-headless-shell"
        if (d / "INSTALLATION_COMPLETE").is_file() and os.access(exe, os.X_OK):
            return d
    return None


def build(p: Scratch) -> None:
    """The target with its pinned browser demo; the scratch data dir holding the box's shell (or
    a planted one) at the pin; the masked cache's marker; which shell, in which.txt."""
    folder = p.root / "data" / "octo-feather" / "ms-playwright" / PIN
    folder.mkdir(parents=True)
    (p.home / ".cache" / "ms-playwright").mkdir(parents=True)
    (p.home / ".cache" / "ms-playwright" / "masked-marker").write_text("")
    real = box_shell()
    if real:
        (folder / real.name).symlink_to(real)
        which = f"real headless shell {real.name} ({real})"
    else:
        sh = folder / "chromium_headless_shell-0" / "chrome-headless-shell-linux64"
        sh.mkdir(parents=True)
        (folder / "chromium_headless_shell-0" / "INSTALLATION_COMPLETE").write_text("")
        (sh / "chrome-headless-shell").write_text(PLANTED)
        (sh / "chrome-headless-shell").chmod(0o755)
        which = (
            "planted shell (no headless shell on this runner: the bind, environment and "
            "collection proved without a browser)"
        )
    (p.root / "which.txt").write_text(which)
    r = target(
        p,
        {
            "page.html": PAGE,
            "demo.sh": DEMO,
            "qc.toml": contract(f'[browser]\nplaywright = "{PIN}"'),
        },
    )
    (r / "demo.sh").chmod(0o755)
    p.git(r, "commit", "-qam", "demo.sh executable")


def world(s: Scratch) -> tuple[Path, str]:
    s.prepare("qc-browser", build)
    clean(s)
    s.env.pop("PLAYWRIGHT_BROWSERS_PATH", None)
    s.env["XDG_DATA_HOME"] = str(s.root / "data")
    r = s.root / "repo"
    return r, s.git(r, "rev-parse", "HEAD")


def evidence(s: Scratch, r: Path, *args: str) -> list[dict[str, Any]]:
    return json.loads(
        s.run([kit("octo-feather-evidence"), "read", "--repo", ".", *args, "--json"], cwd=r).out
    )


def screenshot(s: Scratch) -> None:
    """The browser demo runs in the qc sandbox with the box's shell read-only, ~/.cache masked:
    PASS, every proof line ok, the browser line naming the folder read-only; its record holds the
    demo's output and the screenshot, a PNG; the report names it, no image bytes."""
    r, head = world(s)
    sys.stdout.write((s.root / "which.txt").read_text() + "\n")
    q = qc(s, r, "9", "acceptance-a", want=0)
    b = block(q.out, "PASS acceptance-a: ")
    assert b, q.out
    assert b[0] == "PASS acceptance-a: $ ./demo.sh", q.out
    m = next(
        (
            m
            for x in b[1:]
            if (m := re.fullmatch(rf"  evidence complete; decision demo checks; record ({RID})", x))
        ),
        None,
    )
    assert m, f"want PASS acceptance-a, evidence complete, its record named: {q.out}"
    assert not re.search("^qc sandbox: FAIL", q.err, re.MULTILINE), f"a proof line failed: {q.err}"
    folder = s.root / "data" / "octo-feather" / "ms-playwright" / PIN
    line = f"qc sandbox: ok   browser: PLAYWRIGHT_BROWSERS_PATH={folder} read-only"
    assert line in q.err, f"no browser proof line: {q.err}"
    (x,) = [
        x
        for x in evidence(s, r, "--criterion", "demo#acceptance-a", "--commit", head)
        if x["record"]["id"] == m.group(1)
    ]
    rec, out = x["record"], Path(str(x["dir"])) / "outputs"
    assert rec["revision"] == head, rec
    assert not rec["dirty"], rec
    want = {"demo.cmd", "demo.exit", "demo.stdout", "demo.stderr", "screenshots/page.png"}
    assert want <= set(rec["outputs"]), rec["outputs"]
    png = (out / "screenshots" / "page.png").read_bytes()
    assert png[:8] == b"\x89PNG\r\n\x1a\n", png[:16]
    assert (out / "demo.exit").read_text() == "0\n"
    assert "screenshot taken with " in (out / "demo.stdout").read_text()
    w, h = struct.unpack(">II", png[16:24])
    sys.stdout.write(f"screenshot {w}x{h}, {len(png)} bytes\n")
    c = report(q)["captures"][0]
    assert c["screenshots"] == ["page.png"], c
    assert "shots" not in c["sandbox"], f"image bytes in the report: {c}"


def refused(s: Scratch) -> None:
    """Refused before anything runs, no record appended: a browser demo with no [browser] pin (64),
    and a pin with no shell installed at it (66), naming the folder and install-check."""
    r, _ = world(s)
    before = len(evidence(s, r))
    (r / "qc.toml").write_text(contract(""))
    s.git(r, "commit", "-qam", "contract no pin")
    q = qc(s, r, "9", "acceptance-a", want=64)
    assert "browser = true but qc.toml has no [browser] playwright pin" in q.err, q.err
    (r / "qc.toml").write_text(contract('[browser]\nplaywright = "1.0.0"'))
    s.git(r, "commit", "-qam", "contract pin not installed")
    q = qc(s, r, "9", "acceptance-a", want=66)
    data = s.root / "data" / "octo-feather" / "ms-playwright" / "1.0.0"
    assert f"no Playwright 1.0.0 headless Chromium shell in {data}" in q.err, q.err
    assert "just install-check" in q.err, q.err
    assert len(evidence(s, r)) == before, "a refused run appended a record"


if __name__ == "__main__":
    main(screenshot, refused)
