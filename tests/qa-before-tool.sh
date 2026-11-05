#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape), driven as
# commands with a stub `pi` and a fake `herdr` first on PATH: no model, no live Herdr (tests/lib/qa.sh).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves the fact tool_called_before and the before target edit_under (rules: schema.md, Facts, Before targets): a
# search before the first write under a path passes; one only after it, or a run that never writes there, fails;
# skill_read_before takes edit_under too; the shape check refuses a malformed target, naming case and field.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
# shellcheck source=tests/lib/qa.sh
source "$(dirname "$0")/lib/qa.sh"
mkdir -p "$t/tb/tb/reference"; cp -r "$t/good/fixtures" "$t/tb/"
echo '{"suite": "tb", "kind": "role-transcript", "description": "stub tool before", "max_tool_calls": 10, "timeout_s": 60}' > "$t/tb/tb/suite.json"
python3 - "$t/tb/tb" <<'PY'
import json, sys
d = sys.argv[1]
st = lambda steps: "Build it. STUB-STEPS:" + json.dumps(steps)
under = {"edit_under": ["lib/x/"]}
web = {"fact": "tool_called_before", "tools": ["web_a", "web_b"], "before": under}
w = lambda p: ["bash", f"mkdir -p {p.rsplit('/', 1)[0]} && echo a > {p}"]
cases = [("searched", [["web_a", "PyYAML"], w("lib/x/p.ts")], [web]),
         ("late", [w("other.txt"), w("lib/x/p.ts"), ["web_b", "smol-toml"]], [web]),
         ("never", [["web_a", "PyYAML"], w("other.txt"), w("lib/xy/p.ts")], [web]),
         ("readfirst", [["read", "@tdd"], w("lib/x/q.ts")], [{"fact": "skill_read_before", "skill": "tdd", "before": under}])]
json.dump([{"id": i, "role": "implementer", "fixture": "fx", "task": st(s)} for i, s, _ in cases], open(f"{d}/cases.json", "w"))
json.dump({i: {"facts": f} for i, _, f in cases}, open(f"{d}/reference/expectations.json", "w"))
PY
cp -r "$t/tb" "$t/tb-good"
line() { grep -E "^$1 tb/$2: " <<< "$out" || fail "no $1 line for $2: $out"; }
run 1 "$Q" --evals "$t/tb"
line PASS searched | grep -q "tool_called_before web_a | web_b edit_under lib/x/: called at tool call 2 of 3 (web_a), before first edit_under lib/x/ at tool call 3 of 3 (bash mkdir -p lib/x" \
  || fail "searched: want PASS naming the search and the target: $out"
line FAIL late | grep -q "tool_called_before web_a | web_b edit_under lib/x/: first edit_under lib/x/ at tool call 3 of 3 (bash mkdir -p lib/x.*), no call to any of them before it" \
  || fail "late: want FAIL, the write under lib/x/ before any search: $out"
line FAIL never | grep -q "tool_called_before web_a | web_b edit_under lib/x/: target never reached" || fail "never: want FAIL target never reached: $out"
line PASS readfirst | grep -q "skill_read_before tdd edit_under lib/x/: loaded at tool call 2 of 3" || fail "readfirst: want PASS: $out"
# Shape (schema.md, Facts, Before targets).
bad 'e["searched"]["facts"][0]["before"] = {"edit_under": []}' "case searched fact #1: field before: edit_under must be a non-empty list of relative paths" "$t/tb-good" tb
bad 'e["searched"]["facts"][0]["before"] = {"edit_under": ["/abs/"]}' "case searched fact #1: field before: edit_under must be a non-empty list of relative paths" "$t/tb-good" tb
bad 'e["searched"]["facts"][0]["before"] = {"edit_under": ["lib/"], "x": 1}' "case searched fact #1: field before: must be one of" "$t/tb-good" tb
bad 'del e["searched"]["facts"][0]["tools"]' "case searched fact #1: field tools: missing" "$t/tb-good" tb
echo "qa-before-tool: ok (tool_called_before before edit_under: pass, late, never reached; skill_read_before edit_under; shape refusals)"
