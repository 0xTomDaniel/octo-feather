#!/usr/bin/env bash
# Integration test for the kit's spend-ledger Pi extension (extensions/spend-ledger.ts, issue #187), one gate item
# per case group (#509; the fake provider, Pi environment and helpers: tests/lib/spend-ledger.sh). Case here, on the
# ledger as tests/gate/kit/spend_ledger.py's cases agents to zero-priced and tests/spend-ledger-qc.sh's qc case leave it (seed 10):
#   qa  a `just qa` eval case (role implementer) in no lane: under no lane and implementer (spend#rule-lane)
# Linux only (the qa sandbox needs unshare), as tests/qc.sh. Never skips on Linux: without pi, or with pi at another
# version, it fails naming the install command. Run by `just check`.
set -euo pipefail
[[ "$(uname -s)" != Darwin ]] || { echo "spend-ledger-qa: skipped, not on macOS (the qc sandbox needs Linux; CI runs it)"; exit 0; }
# shellcheck source=tests/lib/spend-ledger.sh
source "$(dirname "$0")/lib/spend-ledger.sh"
seed 10
mkdir -p "$t/home/.pi"; cp -r "$t/agent" "$t/home/.pi/agent"   # under HOME: kept in the sandbox

# qa: a factory eval case (role implementer) run by `just qa` (scripts/octo-feather-qa) outside any lane: its call
# under no lane and implementer (spec spend#rule-lane).
ev="$t/evals"; mkdir -p "$ev/one/reference" "$ev/fixtures/fx"; echo fixture > "$ev/fixtures/fx/README.md"
echo '{"suite": "one", "kind": "skill-trigger", "description": "spend", "max_tool_calls": 5, "timeout_s": 120}' > "$ev/one/suite.json"
echo '[{"id": "look", "role": "implementer", "fixture": "fx", "should_trigger": false, "split": "train", "task": "Only look."}]' > "$ev/one/cases.json"
echo '{"look": {"facts": [{"fact": "skill_not_read", "skill": "tdd"}]}}' > "$ev/one/reference/expectations.json"
set +e
out="$(cd "$t/repo" && pienv PI_CODING_AGENT_DIR="$t/home/.pi/agent" OCTO_FEATHER_QA_DIR="$t/qa" "${gitenv[@]}" \
  "$kit/scripts/octo-feather-qa" --evals "$ev" --model fake/fake 2>"$t/err")"; rc=$?
set -e
[[ "$rc" == 0 && "$out" == *"PASS one/look"* ]] || fail "qa: exit $rc: $out $(tail -20 "$t/err")"
calls 11
s="$(spend)"
row "$s" 'lane and purpose' '(no lane) implementer' 0.170000 1 0 150 10
row "$s" lane gh149 0.824100 8 1 1357 113
echo "case qa: ok (the eval case's call under no lane and implementer)"
echo "spend-ledger-qa: ok (pi $v, empty HOME and environment, no provider credential)"
