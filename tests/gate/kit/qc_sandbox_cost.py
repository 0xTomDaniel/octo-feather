"""quality#acceptance-qc-sandbox-cost through its demo: the verify-octo-feather qc-sandbox-cost
drive runs the qc sandbox around a judge that does nothing, 5 runs one after another, prints each
run's CPU, the median and target comparisons (e2e)."""

from __future__ import annotations

import math
import os
import re
import shlex
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


def exercise(s: Scratch, drive: Path = DRIVE) -> str:
    env = tool_homes() | {
        "QC_HERDR": installed_herdr(s),
        "VERIFY_OCTO_FEATHER_RUN_DIR": str(s.root / "run"),
        "VERIFY_OCTO_FEATHER_EVIDENCE_DIR": str(s.root / "evidence"),
    }
    ran = s.run([str(drive), "run", "qc-sandbox-cost"], env=env)
    sys.stdout.write(ran.out + "\n")
    runs = re.findall(r"qc-sandbox-cost run-\d: (\d+\.\d+) s CPU", ran.out)
    assert len(runs) == 5, ran.out
    assert all(math.isfinite(float(c)) and float(c) >= 0 for c in runs), runs
    comparisons = re.findall(r"target < 0\.8 s: (True|False) \(report-only\)", ran.out)
    assert len(comparisons) == 5, ran.out
    assert re.search(
        r"median \d+\.\d+ s, each under 0\.8 s: (True|False) \(report-only\)", ran.out
    ), ran.out
    assert "verify-octo-feather: run PASS" in ran.out, ran.out
    for i in range(1, 6):
        record = s.root / "evidence" / "qc-sandbox-cost" / f"run-{i}"
        assert record.with_suffix(".exit").read_text().strip() == "0"
        proof = record.with_suffix(".stderr").read_text()
        assert "qc sandbox: FAIL" not in proof, proof
        assert "judge runs in the srt sandbox" in proof, proof
        assert "Herdr config shows only the sandbox session" in proof, proof
        assert "stopped and deleted" in proof, proof
        assert '"left_after_kill": 0' in proof, proof
    return ran.out


def cost(s: Scratch) -> None:
    exercise(s)


def over_target(s: Scratch) -> None:
    """Public entry.command adds real CPU work before each real sandbox no-op."""
    repo = s.root / "entry-fixture"
    repo.mkdir()
    for p in ROOT.iterdir():
        if p.name not in {".git", ".agents", "qc.toml"}:
            (repo / p.name).symlink_to(p, target_is_directory=p.is_dir())
    folder = repo / ".agents/skills/verify-octo-feather"
    (folder / "scripts").mkdir(parents=True)
    drive = folder / "scripts" / DRIVE.name
    shutil.copy2(DRIVE, drive)
    (folder / "features").symlink_to(DRIVE.parent.parent / "features")
    workload = repo / "entry.py"
    workload.write_text(
        "import os, sys, time\n"
        "if sys.argv[1] == 'octo-feather-qc-sandbox':\n"
        "    start = time.process_time()\n"
        "    while time.process_time() - start < 1.1:\n"
        "        pass\n"
        "os.execvp(sys.argv[1], sys.argv[1:])\n"
    )
    entry = f'env PATH="$QC_REPO/scripts:$PATH" python3 {shlex.quote(str(workload))}'
    (repo / "qc.toml").write_text(
        (ROOT / "qc.toml")
        .read_text()
        .replace("command = 'env PATH=\"$QC_REPO/scripts:$PATH\"'", f"command = '{entry}'")
    )
    s.run(["git", "init", "-q", str(repo)])
    s.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.name=test",
            "-c",
            "user.email=test@example.org",
            "commit",
            "-q",
            "--allow-empty",
            "-m",
            "entry fixture",
        ]
    )
    out = exercise(s, drive)
    # Independent oracle: the entry itself consumes 1.1 CPU seconds before exec.
    # No baseline assumption or recomputation of the reporter's target predicate.
    assert re.findall(r"target < 0\.8 s: (True|False) \(report-only\)", out) == ["False"] * 5, out
    assert "each under 0.8 s: False (report-only)" in out, out
    for i in range(1, 6):
        cpu = s.root / "evidence" / "qc-sandbox-cost" / f"run-{i}.obs.cpu"
        assert float(cpu.read_text()) >= 1.1, "entry CPU missing from accounting"


if __name__ == "__main__":
    main(cost, over_target)
