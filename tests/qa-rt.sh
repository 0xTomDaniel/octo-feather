#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape),
# driven as commands with a stub `pi` and a fake `herdr` first on PATH: no model, no live Herdr (tests/lib/qa.sh).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves: role-transcript setup head/branches/branch/origin/fake gh/{repo}{head}, skill load (read, cat; ls, grep, head,
# truncated; a fixture-only skill), declared_includes pass/missing/not a list, a kit_contract_edit fact failing on an
# unread skill; the rt suite's cases on the plain fixtures (the rest: tests/qa-rt-targets.sh).
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
# shellcheck source=tests/lib/qa.sh
source "$(dirname "$0")/lib/qa.sh"
mk_rt
run 1 "$Q" --evals "$t/rt" --case partial --case loads --case setup --case incl --case inclmiss --case inclflat --case roleedit --case repoload --case reponone
d="$(ls -dt "$t"/out/*/ | head -1)"
rl() { grep -E "^$1 rt/$2: " <<< "$out" || fail "rt $2: want $1: $out"; }
rl FAIL partial >/dev/null; rl FAIL roleedit >/dev/null; rl PASS setup >/dev/null; rl PASS incl >/dev/null
rl FAIL partial | grep -q "skill_read tdd: no load of tdd/SKILL.md (its full content in a tool result) in 5 tool calls" \
  || fail "partial: an ls, grep, head, a read elsewhere, a cut-short read or a truncated cat counted: $out"
rl PASS loads | grep -q "skill_read commit: loaded at tool call 2 of [0-9] (bash cat README.md .*/commit/SKILL.md); skill_read python: loaded at tool call 3 of [0-9] (read .*/../python/SKILL.md); skill_read github-pr: loaded at tool call 4 of [0-9] (read [^/].*; skill_read github-issues: loaded at tool call 5 of [0-9] (read .*/github-issues/SKILL.md)" \
  || fail "loads: a cat, a dotted or a relative read of the kit's SKILL.md did not count: $out"
rl FAIL inclmiss | grep -qF 'declared_includes blocking: no entry with {"test": "t.py::b"} in [{"test": "t.py::a"}]' \
  && rl FAIL inclmiss | grep -qF 'declared_includes criteria: no entry with {"id": "x", "verdict": "pass"}' || fail "inclmiss: missing items not named: $out"
rl PASS repoload | grep -q "skill_read repo-only: loaded at tool call 3 of 3 (bash cat .agents/skills/repo-only/SKILL.md)" \
  || fail "repoload: a cat of the fixture-only skill did not count: $out"
rl FAIL reponone | grep -q "skill_read repo-only: no load of repo-only/SKILL.md (its full content in a tool result) in 2 tool calls" \
  || fail "reponone: an ls or a cat of the rewritten fixture skill counted: $out"
rl FAIL inclflat | grep -qF "declared_includes blocking: top-level 'blocking' is \"t.py::a\", want a list" || fail "inclflat: $out"
rl PASS incl | grep -qF 'declared_includes blocking: holds {"test": "t.py::a"}; {"test": "t.py::b"}' || fail "incl: $out"
python3 - "$d/rt" <<'EOF' || fail "rt artifacts wrong"
import json, re, sys
d = sys.argv[1]
assert all(not k.startswith("_") for f in json.load(open(f"{d}/partial/grading.json"))["facts"] for k in f), "private keys in grading"
fs = [json.loads(l)["marks"] for l in open(f"{d}/roleedit/transcript.jsonl") if '"qa_fs"' in l]
assert fs == [["edit", "kit_contract_edit"], ["edit"], ["edit", "kit_contract_edit"]], fs   # agents/x.md, AGENTS.md, a patch
g = json.load(open(f"{d}/roleedit/grading.json"))["facts"][0]
assert g["status"] == "fail" and "first kit_contract_edit at tool call 2 of 4 (bash mkdir -p agents" in g["evidence"] \
    and "no load of tdd/SKILL.md" in g["evidence"], g
o = "".join(json.loads(l)["result"]["structuredContent"]["output"] for l in open(f"{d}/setup/transcript.jsonl") if '"tool_execution_end"' in l)
repo, cwd, head, rev = re.search(r"repo=(\S+) cwd=(\S+) head=(\S+) rev=(\S+)", o).groups()
assert "branch=work" in o and "msg=head msg" in o and "\n2\n" in o and "test_y.py" in o, o   # hb: fixture + head commit
assert repo == cwd and head == rev and len(rev) == 40, o
wb = re.search(r"wb=worker msg wbup=(\S+) hbrev=(\S+) wbtree=(\S+)", o)   # branches: cut from head, its own tree
assert wb and wb.group(1) == wb.group(2) and wb.group(3) == "README.md,", o
assert "origin=1" in o and re.search(r"gh=/tmp/\S+/bin/gh", o), o
assert json.load(open(f"{d}/setup/input.json"))["task"].count("{repo}") == 1, "input.json should keep the case's task as written"
EOF
echo "qa-rt: ok (role-transcript setup head/branches/branch/origin/fake gh/{repo}{head}, skill load (read, cat; ls, grep, head, truncated), declared_includes pass/missing/not a list)"
