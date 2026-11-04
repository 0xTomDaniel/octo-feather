#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape),
# driven as commands with a stub `pi` and a fake `herdr` first on PATH: no model, no live Herdr (tests/lib/qa.sh).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves: role-transcript before targets from filesystem snapshots (test_write by the fixture's declared tests, edit,
# git_commit, git_push, gh_call, final_message, kit_contract_edit), a target never reached fails; the rt suite's cases
# on the python-app fixtures (the rest: tests/qa-rt.sh).
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
# shellcheck source=tests/lib/qa.sh
source "$(dirname "$0")/lib/qa.sh"
mk_rt
run 1 "$Q" --evals "$t/rt" --case order --case fsonly --case contract --case declared
d="$(ls -dt "$t"/out/*/ | head -1)"
rl() { grep -E "^$1 rt/$2: " <<< "$out" || fail "rt $2: want $1: $out"; }
rl FAIL order >/dev/null; rl PASS declared >/dev/null; rl FAIL contract >/dev/null; rl PASS fsonly >/dev/null
python3 - "$d/rt" <<'EOF' || fail "rt artifacts wrong"
import json, re, sys
d = sys.argv[1]
g = {(f["skill"], f.get("before")): (f["status"], f["evidence"]) for f in json.load(open(f"{d}/order/grading.json"))["facts"]}
want = {("tdd", "test_write"): ("pass", "loaded at tool call 2 of 8 (read "), ("commit", "test_write"): ("fail", "first test_write at tool call 3 of 8"),
        ("commit", "git_commit"): ("pass", "first git_commit at tool call 5 of 8"), ("tdd", "git_push"): ("pass", "first git_push at tool call 6 of 8"),
        ("github-pr", "gh_call"): ("fail", "first gh_call at tool call 7 of 8 (bash gh pr create --title x), loaded only at tool call 8 of 8"),
        ("python", "edit"): ("fail", "first edit at tool call 3 of 8"), ("commit", "final_message"): ("pass", "before the final message")}
for k, (st, ev) in want.items():
    assert g[k][0] == st and ev in g[k][1], (k, g[k])
fs = [json.loads(l) for l in open(f"{d}/order/transcript.jsonl") if '"qa_fs"' in l]
assert [e["marks"] for e in fs] == [["edit", "test_write"], ["git_commit"], ["git_push"], ["gh_call"]], fs
assert fs[-1]["gh"] == ["gh pr create --title x"], fs[-1]
g = {f.get("before"): f["evidence"] for f in json.load(open(f"{d}/fsonly/grading.json"))["facts"]}
assert "first test_write at tool call 4 of 4" in g["test_write"] and "first edit at tool call 4 of 4" in g["edit"], g
fs = [json.loads(l)["marks"] for l in open(f"{d}/declared/transcript.jsonl") if '"qa_fs"' in l]
assert fs == [["edit"], ["edit"], ["edit", "test_write"]], fs   # tests/README.md, tests/test_y.py, specs/cli_check.py
g = json.load(open(f"{d}/declared/grading.json"))["facts"][0]
assert g["status"] == "pass" and "first test_write at tool call 5 of 5 (bash echo 'def test_c(): pass' > specs/cli_check.py)" in g["evidence"], g
g = {f.get("before"): (f["status"], f["evidence"]) for f in json.load(open(f"{d}/contract/grading.json"))["facts"]}
assert g["edit"][0] == "fail" and "first edit at tool call 2 of 4" in g["edit"][1], g
assert g["kit_contract_edit"][0] == "pass" and "loaded at tool call 3 of 4" in g["kit_contract_edit"][1] \
    and "before first kit_contract_edit at tool call 4 of 4" in g["kit_contract_edit"][1], g
assert g["test_write"][0] == "fail" and "test_write: target never reached (no test_write in 4 tool calls); loaded at tool call 3 of 4" \
    in g["test_write"][1], g
EOF
echo "qa-rt-targets: ok (before-targets from filesystem snapshots incl. kit_contract_edit, test_write by declared tests, a target never reached fails)"
