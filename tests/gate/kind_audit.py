"""Read-only audit report adapter for the existing OCTO_FEATHER_GATE_ITEMS metadata hook.

Kit-only: its authoritative collector is tests/gate/conftest.py. Uses stdlib JSON and
subprocess, not another parser, collector, kind registry or test runner. Judgments are
explicit human/agent source assessments, not automated classification evidence.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = "835f76de2d31f371c3cfb88d523d73b4a4039001"


def run(*args: str) -> str:
    return subprocess.run(args, cwd=ROOT, check=True, capture_output=True, text=True).stdout


def pairs(rows: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in rows:
        if key in result:
            raise ValueError(f"duplicate key: {key}")
        result[key] = value
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", required=True, help="Prepared interpreter; no install/sync")
    parser.add_argument("--judgments", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--only", help="Render one smoke row, still validate complete inventory")
    args = parser.parse_args()
    # Reports may be committed above the source, but audited source must stay byte-equivalent.
    changes = run("git", "diff", "--name-only", SOURCE, "--", "tests", "scripts", "templates",
                  ".agents", "justfile", "pyproject.toml").splitlines()
    allowed = {"tests/gate/kind_audit.py", "tests/gate/kind-audit-judgments.json",
               "tests/gate/process_inventory.py"}
    if set(changes) - allowed:
        raise ValueError(f"audited source changed: {changes}")
    document = json.loads(args.judgments.read_text(), object_pairs_hook=pairs)
    if document["source"] != SOURCE:
        raise ValueError("judgment source mismatch")
    recipes = run("just", "--evaluate", "GATE_RECIPES").split()
    statics = {f"tests/gate/test_gate.py::test_recipe[{name}]" for name in recipes}
    with tempfile.TemporaryDirectory(prefix="kind-audit-") as tmp:
        metadata = Path(tmp) / "items.json"
        env = {k: v for k, v in os.environ.items() if k not in (
            "OCTO_FEATHER_QC_CLAIMS", "OCTO_FEATHER_QC_CAPTURE_DIR", "OCTO_FEATHER_QC_TAGS",
            "PYTEST_ADDOPTS", "OCTO_FEATHER_GATE_ITEMS")}
        env.update(GATE_RECIPES=" ".join(recipes), PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
                   PYTHONDONTWRITEBYTECODE="1", OCTO_FEATHER_GATE_ITEMS=str(metadata))
        cmd = [args.python, "-m", "pytest", "--collect-only", "-q", "-o", "addopts=",
               "-p", "no:cacheprovider"]
        collected = subprocess.run(cmd, cwd=ROOT, env=env, check=True,
                                   capture_output=True, text=True)
        inventory = json.loads(metadata.read_text(), object_pairs_hook=pairs)
    judgments = document["items"]
    if set(inventory) != set(judgments):
        raise ValueError(f"judgment keys missing={sorted(set(inventory)-set(judgments))} "
                         f"stale={sorted(set(judgments)-set(inventory))}")
    if not statics <= inventory.keys():
        raise ValueError("declared static recipe missing from collection")
    counts = Counter("static" if k in statics else "e2e" if v["e2e"] else "integration"
                     for k, v in inventory.items())
    assessed = Counter()
    rows = []
    for node, item in inventory.items():
        current = "static" if node in statics else "e2e" if item["e2e"] else "integration"
        judgment = judgments[node]
        if judgment["status"] not in ("source-assessed", "unassessed"):
            raise ValueError(f"invalid assessment status: {node}")
        if judgment["status"] == "source-assessed":
            assessed[current] += 1
        if args.only and node != args.only:
            continue
        values = [node, current, judgment["proposed"], judgment["reason"],
                  judgment["facts"], judgment["parity"], judgment["status"],
                  judgment.get("historical", "none"), judgment.get("issue731", "not assessed")]
        rows.append((judgment.get("priority", 100), node, values))
    if args.only and not rows:
        raise ValueError("smoke row not collected")
    out = ["# Whole-suite test-kind audit: PARTIAL, source judgments only", "",
           f"Source: `{SOURCE}`. Metadata: existing OCTO_FEATHER_GATE_ITEMS pytest hook.",
           f"Inventory: {len(inventory)} items; kinds {dict(sorted(counts.items()))}.",
           f"Source-assessed counts: {dict(sorted(assessed.items()))}. Unassessed is NOT retain-kind approval.",
           f"Unassessed counts: {dict(sorted((k, counts[k] - assessed[k]) for k in counts))}.",
           "No test body, fixture, model, gate recipe or performance measurement executed.",
           "No reclassification, retirement, budget adjustment or acceptance claim.",
           "Historical CPU/wall are integrate21 at 3cd67ebb, never current measurements.",
           "Integration overlap review remains incomplete; unknown does not mean unique or redundant.",
           "Historical unsafe observer exposure: integrate21 at 3cd67ebb ran test_qc_gh.py::test_killed "
           "(log line213: 1.223 CPU / 3.696 wall). qc_gh.py blob at historical3cd67ebb and runtime2a2271 "
           "is 7f55997a5d3803b240bee758d45004ec02556e64. This audit executes no test bodies; "
           "the current owned-observer pair is recorded separately below. "
           "Historical execution is not historical safety proof; unrelated-process read exposure extent unknown.",
           "Current inheritance is exact835f76d; inventory re-collected, not relabeled. Delta from prior21a1 "
           "touches only qc_creds, qc_gh, judge and new faulty_timeout under the audited code paths. "
           "Unchanged-source judgments carried by byte equivalence; changed rows re-read. "
           "#749 same-judge RED/restored GREEN executed at e38 with identical runtime blobs at835; "
           "see evidence/2026-11-09-gh749-owned-judge.md. This audit executes no test body.",
           "Source ownership/setup findings and routing: evidence/2026-11-09-gh653-fixture-tool-home-gaps.md. "
           "Current qc-escapes host-wide pgrep is a separate execution blocker, NOT repaired by749.",
           "Ownership source appendix: [process inventory](2026-11-09-gh653-process-ownership.md); "
           "full file manifest/sites/hashes: [machine JSON](2026-11-09-gh653-process-ownership.json). "
           "Mechanical source coverage is NOT semantic completeness or an execution grant.",
           "#731: gh576 by_hand/network currently marked with genuine isolation purpose. gh577 analyst "
           "stub now uses readiness-pipe draining instead of fixed turn sleeps; no clock-only exemption. Issue remains open.",
           "Regenerate (metadata only, from this worktree):", "```sh",
           "<prepared-python> tests/gate/kind_audit.py --python <prepared-python> "
           "--judgments tests/gate/kind-audit-judgments.json "
           "--output evidence/2026-11-09-gh653-test-kind-audit.md", "```", "", 
           "| Test | Current kind | Proposed kind | Real system/reason | Source/facts | Parity/retire plan | Status | Historical six | #731 |",
           "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for _, _, values in sorted(rows):
        out.append("| " + " | ".join(str(v).replace("|", "\\|").replace("\n", " ") for v in values) + " |")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(out) + "\n")
    print(f"metadata/report only: {len(inventory)} items, {len(rows)} rows rendered; {dict(counts)}")


if __name__ == "__main__":
    main()
