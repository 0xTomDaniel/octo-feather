#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals), driven as a command with a stub `pi` and a fake
# `herdr` first on PATH: no model, no live Herdr (tests/lib/qa.sh; its stub streams a parallel codemode batch as Pi does).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves spec quality#acceptance-qa-skill-triggers at the max_tool_calls bound (the stop rule: octo-feather-qa --help):
# a skill read in flight in a batch that crosses the bound is graded; a read started after that batch is not.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
# shellcheck source=tests/lib/qa.sh
source "$(dirname "$0")/lib/qa.sh"
# Bound 3: the stub's first bash call is 1, the codemode call 2, its first nested call 3 (the bound), the read nested 5th.
mkdir -p "$t/cb/cb/reference"; cp -r "$t/good/fixtures" "$t/cb/"
echo '{"suite": "cb", "kind": "role-transcript", "description": "stub cap batch", "max_tool_calls": 3, "timeout_s": 60}' > "$t/cb/cb/suite.json"
python3 - "$t/cb/cb" <<'PY'
import json, sys
d = sys.argv[1]
st = lambda steps: "Build it. STUB-STEPS:" + json.dumps(steps)
cases = [("inbatch", st([["batch", [["bash", "echo a"], ["bash", "echo b"], ["read", "@tdd"]]]])),
         ("afterbatch", st([["batch", [["bash", "echo a"], ["bash", "echo b"]]], ["read", "@tdd"]]))]
json.dump([{"id": i, "role": "implementer", "fixture": "fx", "task": t} for i, t in cases], open(f"{d}/cases.json", "w"))
json.dump({i: {"facts": [{"fact": "skill_read", "skill": "tdd"}]} for i, _ in cases}, open(f"{d}/reference/expectations.json", "w"))
PY
line() { grep -E "^$1 cb/$2: " <<< "$out" || fail "no $1 line for $2: $out"; }
run 1 "$Q" --evals "$t/cb"
line PASS inbatch | grep -q "skill_read tdd: loaded at tool call 5 of 5 (read .*/tdd/SKILL.md) \[stop: decided, 5 tool calls, " \
  || fail "inbatch: the read in flight when the batch crossed the bound was not graded: $out"
line FAIL afterbatch | grep -q "skill_read tdd: no load of tdd/SKILL.md .* in 4 tool calls \[stop: max_tool_calls, 4 tool calls, " \
  || fail "afterbatch: a read started after the batch was credited, or the run did not stop at the bound: $out"
echo "qa-cap-batch: ok (a read in flight in a batch crossing max_tool_calls graded; a read after that batch not credited, stop max_tool_calls)"
