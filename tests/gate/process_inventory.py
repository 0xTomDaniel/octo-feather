"""Static ownership inventory, never imports or executes reviewed source.

Kit-only stdlib reason: Git supplies tracked paths; pathlib/os, re, hashlib and JSON
cover source traversal, broad lexical candidates and reporting. Not a language parser,
process discovery tool, classifier or enforcing CI gate. Broad matches stay UNKNOWN.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tokenize

ROOT = Path(__file__).resolve().parents[2]
SOURCE = "835f76de2d31f371c3cfb88d523d73b4a4039001"
ARTIFACTS = {
    "tests/gate/kind-audit-judgments.json",
    "evidence/2026-11-09-gh653-test-kind-audit.md",
    "evidence/2026-11-09-gh653-fixture-tool-home-gaps.md",
    "evidence/2026-11-09-gh653-process-ownership.json",
    "evidence/2026-11-09-gh653-process-ownership.md",
}
DEPENDENCIES = {".git", ".venv", ".cache", "node_modules", "__pycache__", ".pytest_cache"}
PATTERNS = {
    "proc-path-or-composition": re.compile(r"/proc\b|\bproc\b", re.I),
    "process-command-or-api": re.compile(r"\b(?:pgrep|pkill|killall|ps|psutil|process_iter|pidfd_open|pidfd_send_signal|getppid)\b"),
    "process-data-or-signal": re.compile(r"\b(?:cmdline|environ|killpg|pidfd|ppid)\b|\bos\.kill\b"),
    "read-or-dispatch-context": re.compile(r"\b(?:read_text|read_bytes|readFile|readFileSync|readlink|open|listdir|iterdir|glob|rglob|children|tr|cat|grep|kill|signal|ss|wchan|stack)\b|(?:^|[;|&]|\$\()\s*[\"']?\$\{?\w+"),
    "dynamic-execution-context": re.compile(r"\b(?:subprocess|Popen|check_output|os\.system|eval|exec|getattr|globals|importlib|shlex)\b|\b(?:bash|sh)\s+-c\b"),
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    out: dict[str, object] = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"duplicate judgment key: {key}")
        out[key] = value
    return out


def source_path(path: Path, links: frozenset[str] = frozenset()) -> Path:
    """Resolve source links using filesystem metadata only, rejecting live roots BEFORE access.

    Resolve parents first so relative .. is applied to the actual safe source parent.
    Never resolve/read a proc/dev/sys alias, including indirect helper symlink chains.
    """
    if not path.is_absolute():
        path = ROOT / path
    if path.parent == path:
        return path
    parent = source_path(path.parent, links)
    if path.name == "..":
        return parent.parent
    candidate = parent / path.name
    if candidate == Path("/proc") or candidate == Path("/dev") or candidate == Path("/sys"):
        raise ValueError(f"live-filesystem source boundary: {candidate}")
    if candidate.is_symlink():
        key = str(candidate)
        if key in links:
            raise ValueError(f"source symlink cycle: {candidate}")
        target = Path(os.readlink(candidate))
        return source_path(target if target.is_absolute() else parent / target, links | {key})
    return candidate


def inventory(only: str | None) -> tuple[list[dict], list[dict]]:
    paths = subprocess.run(["git", "ls-files", "-z", "--cached"], cwd=ROOT,
                           capture_output=True, check=True).stdout.decode().split("\0")
    manifest: list[dict] = []
    sites: list[dict] = []
    seen: set[str] = set()

    def visit(logical: str, path: Path, origin: str, ancestors: frozenset[str]) -> None:
        if logical in seen:
            return
        seen.add(logical)
        row = {"path": logical, "origin": origin}
        try:
            row["realpath"] = str(source_path(path))
        except (OSError, RuntimeError, ValueError) as error:
            manifest.append({**row, "coverage": "unresolved-cycle-or-blocked-live-target", "error": str(error),
                             "route": "director: helper target owner; unresolved boundary"})
            return
        real = row["realpath"]
        logical_path = path
        path = Path(real)
        if logical in ARTIFACTS:
            manifest.append({**row, "coverage": "excluded-exact-generated-or-annotation-artifact"})
            return
        if any(part in DEPENDENCIES for part in path.parts):
            manifest.append({**row, "coverage": "dependency-or-git-boundary", "route": "director: dependency/tool owner; not authored source"})
            return
        if real in ancestors:
            manifest.append({**row, "coverage": "symlink-cycle"})
            return
        if str(logical_path.absolute()) != real:
            row["symlink_source_path"] = str(logical_path.absolute())
            origin = "helper-symlink-closure"
            row["origin"] = origin
        if path.is_dir():
            manifest.append({**row, "coverage": "directory-traversed"})
            try:
                children = sorted(path.iterdir())
            except OSError as error:
                manifest.append({**row, "coverage": "unreadable", "error": str(error)})
                return
            for child in children:
                visit(logical + "/" + child.name, child, origin, ancestors | {real})
            return
        try:
            if not stat.S_ISREG(path.stat().st_mode):
                manifest.append({**row, "coverage": "nonregular-source-boundary", "route": "director: source/helper owner; never read live device/socket/fifo"})
                return
            data = path.read_bytes()
        except OSError as error:
            manifest.append({**row, "coverage": "unreadable", "error": str(error)})
            return
        row["sha256"] = digest(data)
        if b"\0" in data:
            manifest.append({**row, "coverage": "binary-not-scanned", "bytes": len(data)})
            return
        try:
            source = data.decode("utf-8")
        except UnicodeDecodeError:
            manifest.append({**row, "coverage": "non-utf8-not-scanned", "bytes": len(data)})
            return
        comments: set[int] = set()
        if logical.endswith(".py") or source.startswith("#!/usr/bin/env python"):
            try:
                comments = {t.start[0] for t in tokenize.generate_tokens(io.StringIO(source).readline)
                            if t.type == tokenize.COMMENT and not t.line[:t.start[1]].strip()}
            except (tokenize.TokenError, IndentationError, SyntaxError) as error:
                row["python_comment_token_boundary"] = str(error)
        row["coverage"] = "text-scanned"
        row["lines"] = len(source.splitlines())
        manifest.append(row)
        lines = source.splitlines()
        for number, line in enumerate(lines, 1):
            constructs = [name for name, pattern in PATTERNS.items() if pattern.search(line)]
            if not constructs:
                continue
            ident = logical + ":" + str(number) + ":" + digest(line.encode())[:16]
            sites.append({"id": ident, "path": logical, "line": number,
                          "line_sha256": digest(line.encode()), "file_sha256": row["sha256"],
                          "realpath": real, "origin": origin, "constructs": constructs,
                          "text": line, "context": lines[max(0, number - 4):number + 3],
                          "context_kind": "data-documentation-or-embedded-source" if logical.endswith((".md", ".html", ".json", ".jsonl", ".txt", ".patch")) else "source-or-executable-fixture-candidate",
                          "classification": "NONEXEC" if number in comments else "UNKNOWN",
                          "evidence": "Python stdlib tokenize COMMENT token covers this complete physical line, no executable prefix; source comment only, not runtime clearance." if number in comments else "Broad lexical candidate; ownership/caller/executable context not yet established.",
                          "route": "director: materialized/external helper owner" if origin != "tracked" or logical.startswith((".agents/", ".skillfile/")) else "parent653: source review/grouped child shaping",
                          "blocked_execution": number not in comments})

    if only:
        if only not in paths:
            raise ValueError("smoke must select a tracked source path")
        visit(only, ROOT / only, "tracked", frozenset())
    else:
        for logical in sorted(set(paths) - {""}):
            visit(logical, ROOT / logical, "tracked", frozenset())
        # Materialized skills/helpers may be ignored or symlinked outside tracked corpus.
        visit(".agents", ROOT / ".agents", "materialized-helper-closure", frozenset())
    return sorted(manifest, key=lambda x: (x["path"], x["coverage"])), sorted(sites, key=lambda x: x["id"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", help="Static smoke source only; never a reviewed command")
    parser.add_argument("--initialize", action="store_true", help="Explicit first inventory or source-drift reset; missing candidates become UNKNOWN, never owned")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()
    drift = subprocess.run(["git", "diff", "--name-only", SOURCE], cwd=ROOT, check=True,
                           capture_output=True, text=True).stdout.splitlines()
    allowed = ARTIFACTS | {"tests/gate/kind_audit.py", "tests/gate/process_inventory.py"}
    if set(drift) - allowed:
        raise ValueError(f"reviewed source drift outside audit artifacts: {sorted(set(drift) - allowed)}")
    manifest, sites = inventory(args.only)
    document = json.loads((ROOT / "tests/gate/kind-audit-judgments.json").read_text(), object_pairs_hook=unique)
    judgments = document.get("process_sites", {})
    ids = {s["id"] for s in sites}
    if len(ids) != len(sites):
        raise ValueError("duplicate generated site IDs")
    if not args.only and not args.initialize:
        previous = json.loads(args.output.read_text(), object_pairs_hook=unique)
        if previous["manifest_sha256"] != digest(json.dumps(manifest, sort_keys=True).encode()):
            raise ValueError("source manifest drift; review before explicit initialization")
        prior_sites = previous["sites"]
        prior_ids = [s["id"] for s in prior_sites]
        if len(set(prior_ids)) != len(prior_ids) or set(prior_ids) != ids:
            raise ValueError("missing/stale/duplicate inventory judgment keys; inspect drift before explicit initialization")
        for prior in prior_sites:
            if prior["classification"] not in {"owned", "foreign", "NONEXEC", "UNKNOWN"}:
                raise ValueError("invalid persisted classification")
            for field in ("classification", "evidence", "route", "blocked_execution"):
                if field not in prior:
                    raise ValueError(f"missing persisted judgment: {prior['id']} {field}")
        prior_by_id = {s["id"]: s for s in prior_sites}
        for site in sites:
            prior = prior_by_id[site["id"]]
            if prior["classification"] != "UNKNOWN":
                for field in ("classification", "evidence", "route", "blocked_execution"):
                    site[field] = prior[field]
    if not args.only and set(judgments) - ids:
        raise ValueError(f"stale judgment keys: {sorted(set(judgments) - ids)}")
    for site in sites:
        if site["id"] in judgments:
            judgment = judgments[site["id"]]
            if judgment["classification"] not in {"owned", "foreign", "NONEXEC", "UNKNOWN"}:
                raise ValueError("invalid classification")
            for field in ("evidence", "route", "blocked_execution"):
                if field not in judgment:
                    raise ValueError(f"missing judgment field: {field}")
            for field in ("classification", "evidence", "route", "blocked_execution"):
                site[field] = judgment[field]
    counts = {kind: sum(s["classification"] == kind for s in sites)
              for kind in ("owned", "foreign", "NONEXEC", "UNKNOWN")}
    direct = {"proc-path-or-composition", "process-command-or-api", "process-data-or-signal"}
    groups = {"direct-lexical-candidates-not-semantic-proof": sum(bool(direct.intersection(s["constructs"])) for s in sites),
              "generic-read-launch-or-indirection-only": sum(not direct.intersection(s["constructs"]) for s in sites)}
    audit_revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                                    capture_output=True, text=True).stdout.strip()
    result = {"source": SOURCE, "audit_revision": audit_revision,
              "manifest_sha256": digest(json.dumps(manifest, sort_keys=True).encode()),
              "groups": groups,
              "coverage_counts": {c: sum(m["coverage"] == c for m in manifest) for c in sorted({m["coverage"] for m in manifest})},
              "context_counts": {c: sum(s["context_kind"] == c for s in sites) for c in sorted({s["context_kind"] for s in sites})},
              "construct_counts": {c: sum(c in s["constructs"] for s in sites) for c in PATTERNS},
              "covered_roots": ["entire Git tracked corpus, not path/diff selection", ".agents full materialized recursive helper/symlink closure"],
              "scope": args.only or "all tracked text plus materialized .agents/helper symlink closure",
              "exclusions": sorted(ARTIFACTS), "dependency_boundaries": sorted(DEPENDENCIES),
              "limits": "Lexical overapproximation with full context, NOT semantic completeness or clearance. Arbitrarily constructed commands/paths and external command/helper implementations remain dynamic UNKNOWN boundaries; no handwritten parser/dataflow interpreter or live discovery. No dependency-cache traversal. Spec Chat clone helpers referenced by scripts/review-host are external/configurable, director/Spec Chat owner; Herdr/native OS tools and pinned srt are external implementation boundaries, not cleared by argv filters. Every matched candidate retained; comments use real stdlib tokenizer, all other classifications require persisted source judgment. No source executed/imported/evaluated. No runtime proof.",
              "counts": counts, "manifest": manifest, "sites": sites}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    out = ["# Process ownership source inventory: PARTIAL judgments, no execution", "",
           f"Source `{SOURCE}`. Files/entries {len(manifest)}; sites {len(sites)}; classes {counts}.",
           f"Construct groups {groups}. Generic contexts are retained, not pruned to reduce UNKNOWNs.",
           "Python full-line comments are identified only by stdlib tokenize COMMENT spans; NONEXEC is source syntax evidence, not an execution grant.",
           "Full hashes/origins/context/boundaries and every candidate are in the adjacent machine JSON.",
           result["limits"], "", "| Site | Constructs | Class | Ownership evidence | Routing | Block execution |", "| --- | --- | --- | --- | --- | --- |"]
    for site in sites:
        values = [site["id"], ", ".join(site["constructs"]), site["classification"], site["evidence"], site["route"], str(site["blocked_execution"])]
        out.append("| " + " | ".join(str(v).replace("|", "\\|").replace("\n", " ") for v in values) + " |")
    args.markdown.write_text("\n".join(out) + "\n")
    print(f"STATIC source only: entries={len(manifest)} sites={len(sites)} classes={counts}")


if __name__ == "__main__":
    main()
