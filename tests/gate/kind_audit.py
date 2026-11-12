"""Audit report adapter for the existing OCTO_FEATHER_GATE_ITEMS metadata hook.

Canonical read-only by default; --apply-shard updates only registered judgment assignments.
Default collection invokes just's parse-time helpers, so is NOT source-only.
--shard-only validates the registered frozen inventory and never invokes just/pytest.

Kit-only: its authoritative collector is tests/gate/conftest.py. Uses stdlib JSON and
subprocess, not another parser, collector, kind registry or test runner. Judgments are
explicit human/agent source assessments, not automated classification evidence.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

from process_inventory import source_path

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


def row_hash(row: object) -> str:
    return hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()


def persist(document: dict, path: Path) -> None:
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as pending:
        pending.write(json.dumps(document, indent=2) + "\n")
    try:
        os.replace(pending.name, path)
    finally:
        Path(pending.name).unlink(missing_ok=True)


def merge_shard(document: dict, shard: dict, name: str, content_hash: str) -> dict:
    """Merge one registered assignment, refusing stale canonical state and status regression.

    Assignment IDs/expected hashes live in the existing canonical judgment document;
    no second collector or implicit grant to overwrite another worker's rows.
    """
    if shard.get("source") != SOURCE:
        raise ValueError("shard source mismatch")
    assignments = document.get("shard_assignments", {})
    if name not in assignments:
        raise ValueError(f"unregistered shard assignment: {name}")
    assignment = assignments[name]
    if assignment.get("source") != SOURCE:
        raise ValueError("assignment source mismatch")
    ids = assignment["ids"]
    if not isinstance(ids, list) or len(set(ids)) != len(ids):
        raise ValueError("duplicate/invalid assigned IDs")
    assigned = set(ids)
    incoming = shard.get("items")
    if not isinstance(incoming, dict) or set(incoming) != assigned:
        raise ValueError("shard keys must exactly match assigned IDs, including UNKNOWN rows")
    canonical = document["items"]
    if row_hash(sorted(canonical)) != assignment.get("inventory_sha256"):
        raise ValueError("registered frozen inventory key mismatch")
    if not assigned <= canonical.keys() or set(assignment["expected"]) != assigned:
        raise ValueError("missing/stale assigned canonical IDs or expected hashes")
    for other_name, other in assignments.items():
        if other_name != name and assigned.intersection(other["ids"]):
            raise ValueError(f"overlapping shard assignments: {name}, {other_name}")
    for node in ids:
        current, proposed = canonical[node], incoming[node]
        if row_hash(current) != assignment["expected"][node]:
            raise ValueError(f"canonical overwrite/stale-assignment conflict: {node}")
        if not isinstance(proposed, dict):
            raise ValueError(f"invalid shard row: {node}")
        for field in ("status", "proposed", "reason", "facts", "parity"):
            if not isinstance(proposed.get(field), str) or not proposed[field].strip():
                raise ValueError(f"missing/invalid shard field {field}: {node}")
        if proposed["status"] not in ("source-assessed", "unassessed"):
            raise ValueError(f"invalid shard assessment: {node}")
        if current["status"] == "source-assessed" and proposed["status"] == "unassessed":
            raise ValueError(f"shard cannot erase completed source assessment: {node}")
        if current["status"] == "source-assessed" and (current | proposed) != current:
            raise ValueError(f"completed source assessment content conflict: {node}")
    merged = copy.deepcopy(document)
    for node in ids:
        merged["items"][node].update(incoming[node])
    merged_assignment = merged["shard_assignments"][name]
    merged_assignment["expected"] = {node: row_hash(merged["items"][node]) for node in ids}
    merged_assignment["last_import_sha256"] = content_hash
    return merged


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", required=True, help="Prepared interpreter; no install/sync")
    parser.add_argument("--judgments", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--only", help="Render one smoke row, still validate complete inventory")
    parser.add_argument("--shard", type=Path, help="Source judgments, not another collected inventory")
    parser.add_argument("--assignment", help="Registered assignment in canonical judgment JSON")
    parser.add_argument("--apply-shard", action="store_true", help="Explicitly persist validated assignment rows")
    parser.add_argument("--shard-only", action="store_true", help="Validate shard metadata without collection or fixture imports")
    args = parser.parse_args()
    if bool(args.shard) != bool(args.assignment):
        parser.error("--shard and --assignment must be provided together")
    if (args.apply_shard or args.shard_only) and not args.shard:
        parser.error("shard flags require --shard")
    if args.apply_shard and args.only:
        parser.error("persisting a shard requires full metadata/report completeness validation")
    args.judgments = source_path(args.judgments.absolute())
    args.output = source_path(args.output.absolute())
    if args.shard:
        args.shard = source_path(args.shard.absolute())
    # Reports may be committed above the source, but audited source must stay byte-equivalent.
    changes = run("git", "diff", "--name-only", SOURCE).splitlines()
    changes += run("git", "ls-files", "--others", "--exclude-standard").splitlines()
    allowed = {"tests/gate/kind_audit.py", "tests/gate/kind-audit-judgments.json",
               "tests/gate/process_inventory.py",
               "evidence/2026-11-09-gh653-test-kind-audit.md",
               "evidence/2026-11-09-gh653-fixture-tool-home-gaps.md",
               "evidence/2026-11-09-gh653-process-ownership.json",
               "evidence/2026-11-09-gh653-process-ownership.md",
               "evidence/2026-11-09-gh653-semantic-a.json",
               "evidence/2026-11-09-gh653-semantic-a.md"}
    if set(changes) - allowed:
        raise ValueError(f"audited source changed: {changes}")
    document = json.loads(args.judgments.read_text(), object_pairs_hook=pairs)
    if document["source"] != SOURCE:
        raise ValueError("judgment source mismatch")
    if args.shard:
        body = args.shard.read_bytes()
        shard = json.loads(body, object_pairs_hook=pairs)
        if not isinstance(shard, dict):
            raise ValueError("shard must be an object")
        document = merge_shard(document, shard, args.assignment, hashlib.sha256(body).hexdigest())
    if args.shard_only:
        for node, row in document["items"].items():
            if row.get("status") not in ("source-assessed", "unassessed"):
                raise ValueError(f"invalid canonical assessment status: {node}")
            for field in ("proposed", "reason", "facts", "parity"):
                if not isinstance(row.get(field), str) or not row[field].strip():
                    raise ValueError(f"invalid canonical assessment field {field}: {node}")
        counts = Counter(row["status"] for row in document["items"].values())
        assigned_counts = Counter(row["status"] for row in shard["items"].values())
        out = ["# Frozen-source shard completeness, NOT a collection/kind refresh", "",
               f"Source: `{SOURCE}`. Assignment: `{args.assignment}`.",
               f"Shard SHA256: `{hashlib.sha256(body).hexdigest()}`.",
               f"Registered artifact revision: `{document['shard_assignments'][args.assignment].get('artifact_revision', 'not recorded')}`.",
               f"Registered inventory SHA256: `{document['shard_assignments'][args.assignment]['inventory_sha256']}`.",
               f"Canonical: {len(document['items'])} frozen IDs; {dict(sorted(counts.items()))}.",
               f"Assignment: {len(shard['items'])} exact IDs; {dict(sorted(assigned_counts.items()))}.",
               "This checks the prior authoritative frozen inventory, not fresh discovery or kind markers.",
               "No just/pytest/reviewed-helper/test/model execution; UNKNOWN is not approval or uniqueness.",
               "No retirement, budget or acceptance proof. Full live metadata path remains separately gated.",
               "Historical kinded snapshot: this report at532fb09fa6c39ef116102c5179a4a745fcde7c6f.",
               "Prior835 collection:341=28 e2e+297 integration+16 static. No marker/source delta imported.",
               "Historical just metadata queries reached check-gate-free parse-time helpers; their native/ancestor ownership remains unproved, not retroactively safe.",
               "Ownership/routes: evidence/2026-11-09-gh653-fixture-tool-home-gaps.md; machine process inventory and manifest: evidence/2026-11-09-gh653-process-ownership.json.",
               "Same-judge752 proof remains scoped to e38/835; historical filename evidence/2026-11-09-gh749-owned-judge.md retained.", "",
               "| Test | Proposed kind | Real system/reason | Source/facts | Parity/retire plan | Status | Historical six | #731 |",
               "| --- | --- | --- | --- | --- | --- | --- | --- |"]
        for node, row in sorted(document["items"].items(), key=lambda entry: (entry[1].get("priority", 100), entry[0])):
            values = [node, row["proposed"], row["reason"], row["facts"], row["parity"],
                      row["status"], row.get("historical", "none"), row.get("issue731", "not assessed")]
            out.append("| " + " | ".join(str(v).replace("|", "\\|").replace("\n", " ") for v in values) + " |")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text("\n".join(out) + "\n")
        if args.apply_shard:
            persist(document, args.judgments)
        print(f"metadata only: validated {len(shard['items'])} assigned rows; "
              f"canonical {'written' if args.apply_shard else 'NOT written'}; no collection; {dict(counts)}")
        return
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
    if args.apply_shard:
        # No canonical write before all source, assignment, inventory and row checks pass.
        persist(document, args.judgments)
    print(f"metadata/report only: {len(inventory)} items, {len(rows)} rows rendered; {dict(counts)}")


if __name__ == "__main__":
    main()
