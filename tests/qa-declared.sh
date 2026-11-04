#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape),
# driven as commands with a stub `pi` and a fake `herdr` first on PATH: no model, no live Herdr (tests/lib/qa.sh).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves: the declared fact (pass, outside its list, no block, two blocks, stopped early) and a
# skill_read_before target never reached.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
# shellcheck source=tests/lib/qa.sh
source "$(dirname "$0")/lib/qa.sh"
# declared (schema.md, Final JSON):
# `ok` also reads tdd early and still passes (the watcher kept it running); `early` lingers past timeout_s.
mkdir -p "$t/dec/dec/reference" "$t/dec/fixtures"; cp -r "$t/good/fixtures/fx" "$t/dec/fixtures/"
echo '{"suite": "dec", "kind": "role-transcript", "description": "stub declared", "max_tool_calls": 10, "timeout_s": 8}' > "$t/dec/dec/suite.json"
echo "[$(ic ok "Pick. STUB-READ-TDD STUB-DECL-OK"), $(ic out "Pick. STUB-DECL-OUT"), $(ic none "Pick. STUB-DECL-NONE"),
 $(ic two "Pick. STUB-DECL-TWO"), $(ic early "Pick. STUB-LINGER STUB-DECL-OK"), $(ic earlyrb "Pick. STUB-READ-TDD STUB-LINGER")]" > "$t/dec/dec/cases.json"
d1='{"fact": "declared", "field": "rung", "in": ["check", "instruction"]}'
echo "{\"ok\": {\"facts\": [{\"fact\": \"skill_read\", \"skill\": \"tdd\"}, $d1]}, \"out\": {\"facts\": [$d1]}, \"none\": {\"facts\": [$d1]},
  \"two\": {\"facts\": [$d1]}, \"early\": {\"facts\": [$d1]},
  \"earlyrb\": {\"facts\": [{\"fact\": \"skill_read_before\", \"skill\": \"tdd\", \"before\": \"final_message\"}]}}" > "$t/dec/dec/reference/expectations.json"
run 1 "$Q" --evals "$t/dec"
dl() { grep -E "^$1 dec/$2: " <<< "$out" | grep -qF "$3" || fail "declared $2: want $1 with '$3': $out"; }
dl PASS ok 'declared rung: "check", one of ["check", "instruction"]'
dl FAIL out 'declared rung: "vibes" is not one of ["check", "instruction"]'
dl FAIL none 'declared rung: final message holds 0 ```json blocks, want exactly 1'
dl FAIL two 'declared rung: final message holds 2 ```json blocks, want exactly 1'
dl FAIL early 'declared rung: run stopped (timeout) before its final message'
# A read whose target is never reached (rule: schema.md, Facts, skill_read_before): final_message unreached when the run is cut off.
dl FAIL earlyrb 'skill_read_before tdd final_message: target never reached (run stopped (timeout) before its final message); loaded at tool call 2 of 2'
echo "qa-declared: ok (declared pass/outside list/no block/two blocks/stopped early, a target never reached fails)"
