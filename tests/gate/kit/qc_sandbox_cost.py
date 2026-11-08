"""quality#acceptance-qc-sandbox-cost through its demo: the verify-octo-feather qc-sandbox-cost
drive runs the qc sandbox around a judge that does nothing, 5 runs one after another, prints each
run's CPU and the median, and reports the optimization target without gating on it (e2e)."""

from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path

from testkit import ROOT, Scratch, main, tool_homes

DRIVE = ROOT / ".agents" / "skills" / "verify-octo-feather" / "scripts" / "verify-octo-feather"


def installed_herdr(s: Scratch) -> str:
    fake = (s.bin / "herdr").resolve()
    path = os.pathsep.join(
        d for d in s.env["PATH"].split(os.pathsep) if (Path(d) / "herdr").resolve() != fake
    )
    herdr = shutil.which("herdr", path=path)
    assert herdr is not None, "qc-sandbox-cost requires installed real Herdr outside testkit PATH"
    return str(Path(herdr).absolute())


def selection(s: Scratch) -> None:
    """Probe executable identity separately so the cost workload starts with cold caches."""
    herdr = installed_herdr(s)
    ran = s.run([herdr, "--version"])
    assert re.search(r"herdr \d+\.\d+\.\d+", ran.out), ran.out
    sys.stdout.write(f"qc-sandbox-cost installed Herdr: {herdr}: {ran.out}\n")


def cost(s: Scratch) -> None:
    env = tool_homes() | {
        "QC_HERDR": installed_herdr(s),
        "VERIFY_OCTO_FEATHER_RUN_DIR": str(s.root / "run"),
        "VERIFY_OCTO_FEATHER_EVIDENCE_DIR": str(s.root / "evidence"),
    }
    ran = s.run([str(DRIVE), "run", "qc-sandbox-cost"], env=env)
    sys.stdout.write(ran.out + "\n")
    runs = re.findall(r"qc-sandbox-cost run-\d: (\d+\.\d+) s CPU", ran.out)
    assert len(runs) == 5, ran.out
    assert all(float(c) >= 0 for c in runs), runs
    comparisons = re.findall(r"target < 0\.8 s: (True|False) \(report-only\)", ran.out)
    assert len(comparisons) == 5, ran.out
    assert comparisons == [str(float(c) < 0.8) for c in runs], ran.out
    assert re.search(
        r"median \d+\.\d+ s, each under 0\.8 s: (True|False) \(report-only\)", ran.out
    ), ran.out
    assert "verify-octo-feather: run PASS" in ran.out, ran.out


if __name__ == "__main__":
    main(cost, selection)
