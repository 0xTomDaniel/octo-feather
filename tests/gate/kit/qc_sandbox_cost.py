"""quality#acceptance-qc-sandbox-cost through its demo: the verify-octo-feather qc-sandbox-cost
drive runs the qc sandbox around a judge that does nothing, 5 runs one after another, prints each
run's CPU and the median, and passes with each run under the bound (a CPU check: e2e)."""

from __future__ import annotations

import re

from testkit import ROOT, Scratch, main, tool_homes

DRIVE = ROOT / ".agents" / "skills" / "verify-octo-feather" / "scripts" / "verify-octo-feather"


def cost(s: Scratch) -> None:
    env = tool_homes() | {
        "VERIFY_OCTO_FEATHER_RUN_DIR": str(s.root / "run"),
        "VERIFY_OCTO_FEATHER_EVIDENCE_DIR": str(s.root / "evidence"),
    }
    ran = s.run([str(DRIVE), "run", "qc-sandbox-cost"], env=env)
    runs = re.findall(r"qc-sandbox-cost run-\d: (\d+\.\d+) s CPU", ran.out)
    assert len(runs) == 5, ran.out
    assert all(float(c) < 0.8 for c in runs), runs
    assert re.search(r"median \d+\.\d+ s, each under 0\.8 s: True", ran.out), ran.out
    assert "verify-octo-feather: run PASS" in ran.out, ran.out


if __name__ == "__main__":
    main(cost)
