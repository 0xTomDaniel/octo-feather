#!/usr/bin/env python3
"""Owned-rule search for #173: every comment, docstring, help text, eval description and doc line in the
kit that names a normative term of .agents/skills/eval-cases/references/schema.md, one block per schema.md
section. Prints path:line: text; a reviewer reads each hit and judges restatement versus pointer or setup.
Scope: scripts/, tests/*.sh (comments), evals/*/suite.json descriptions, .agents/skills/ (md, schema.md
itself excluded), agents/, AGENTS.md, justfile comments, docs/ (not docs/specs). Run from the repo root."""
import json, re, sys
from pathlib import Path

SECTIONS = {
    "Layout": r"EVALS_DIR|suite\.json|cases\.json|expectations\.json|question\.json|judgment-model\.json|classifiers\.json|fixtures/",
    "Suite": r"max_tool_calls|timeout_s|\bcovers\b|\bkind\b|\bchosen\b|any depth|names? (no |a )?model",
    "Case": r"should_trigger|\bsplit\b|fake_gh|\borigin\b.*\b(true|bare)|\{repo\}|\{head\}|repo setup|setup fields",
    "Facts": r"skill_read|skill_not_read|attempt_blocked|declared_includes|\bdeclared\b|field_lines|branch_paths|never reached|vacuous|fact is decided|closed (fact )?list",
    "Skill load": r"truncat|normaliz|CRLF|full (SKILL\.md )?content|skill load|a load\b",
    "Before targets": r"test_write|git_commit|git_push|gh_call|kit_contract_edit|final_message|before.target|snapshot|testpaths",
    "Attempt record": r"attempt record|lane_state|forge|recorder|refusal|whole record|never a prefix",
    "Final JSON": r"json block|fenced|Final JSON",
    "Field lines": r"Field lines|\bincludes\b|\bevery\b.*field|none line",
    "Branch paths": r"untouched|\btouched\b|Branch paths",
    "Leaks": r"\bleak|its grade|whole (path )?component|key order",
    "Coverage": r"role-skills|Coverage|\{tracker\}|four cases|near.miss",
    "Judgment suite": r"label_help|state_shape|labelled_by|relabel|labell?ed set|closed question|at least 15|fifteen|one line\b",
    "Calibration": r"calibration|held_out\b|threshold|accuracy_min|brier_max|\baccepted\b",
    "Judgment model and classifiers": r"moving_alias|moving alias|yes_no_only|yes/no.only|\bpinned\b|one judgment model|-latest",
    "Bench": r"Brier|\bECE\b|Wilson|1\.96|best.scoring|tie.break|unavailable|unclassified|skipped|held_out_meets|train only|bench FAILS|choice question",
}


def comment_lines(p: Path):
    """(line, text) of the prose in P: comments, docstrings, help, descriptions, markdown."""
    text = p.read_text(errors="replace")
    if p.suffix == ".md":
        yield from enumerate(text.splitlines(), 1); return
    if p.name == "suite.json":
        d = json.loads(text).get("description", "")
        n = next((i for i, l in enumerate(text.splitlines(), 1) if '"description"' in l), 0)
        for s in re.split(r"(?<=[.;:])\s+", d):
            yield n, s
        return
    py = text.startswith("#!/usr/bin/env python3")
    doc = False
    for i, l in enumerate(text.splitlines(), 1):
        q = l.count('"""')
        if py and (doc or q):
            yield i, l
            if q % 2: doc = not doc
            continue
        m = re.search(r"(^|\s)(#|//)\s(.*)", l)
        if m:
            yield i, m.group(3)


def files(root: Path):
    out = [p for p in (root / "scripts").iterdir() if p.is_file()]
    out += sorted((root / "tests").glob("*.sh"))
    out += sorted((root / "evals").glob("*/suite.json"))
    out += [p for p in (root / ".agents/skills").rglob("*.md") if p != root / ".agents/skills/eval-cases/references/schema.md"]
    out += sorted((root / "agents").rglob("*.md")) + [root / "AGENTS.md", root / "justfile"]
    out += [p for p in (root / "docs").rglob("*.md") if "specs" not in p.parts]
    return sorted(set(out))


root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
lines = [(p.relative_to(root), n, t) for p in files(root) for n, t in comment_lines(p)]
for sec, pat in SECTIONS.items():
    rx = re.compile(pat)
    hits = [f"{p}:{n}: {t.strip()[:200]}".replace("\u2014", "(dash)").replace("\u2013", "(dash)") for p, n, t in lines if rx.search(t)]
    print(f"## {sec}  /{pat}/  {len(hits)} hits")
    print("\n".join(hits))
