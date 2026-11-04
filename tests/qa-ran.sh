#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape),
# driven as commands with a stub `pi` and a fake `herdr` first on PATH: no model, no live Herdr (tests/lib/qa.sh).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves: ran: a run through the sandbox's recording shim matched by its arguments (positional prefix, flag and value pairs anywhere) and {head}, stdin/stdout/exit
# passed through, an echo or other arguments fail naming the record, a shim only for a named program.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
# shellcheck source=tests/lib/qa.sh
source "$(dirname "$0")/lib/qa.sh"
# ran (rule: schema.md, Run record): cases rpass, recho, rother; then rpass's transcript and record.
printf '#!/usr/bin/env bash\necho "runme: $* stdin=$(cat)"; exit 3\n' > "$t/bin/runme"
printf '#!/usr/bin/env bash\necho other\n' > "$t/bin/other-prog"; chmod +x "$t/bin/runme" "$t/bin/other-prog"
mk_ran
run 1 "$Q" --evals "$t/ran"
rn() { grep -E "^$1 ran/$2: " <<< "$out" | grep -qE "$3" || fail "ran $2: want $1 with '$3': $out"; }
rn PASS rpass 'ran runme lane show \{head\}: recorded run runme lane show [0-9a-f]{7,} extra \(exit 3\)'
rn FAIL recho "ran runme lane show \\{head\\}: no run of runme with these arguments in the sandbox's record \\([0-9]+ entries; no run of runme recorded\\)"
rn FAIL rother 'runs of runme: runme lane show 0000000 \(exit 3\); runme lane list \(exit 3\)\)'
grep -q "qc sandbox: ok   run record: shims first on PATH for runme " <<< "$out" || fail "ran: no proof line naming the run shims: $out"
d="$(ls -dt "$t"/out/*/ | head -1)"
ro="$(jq -r 'select(.type == "tool_execution_end") | .result.structuredContent.output' "$d/ran/rpass/transcript.jsonl")"
grep -qE '^runme: lane show [0-9a-f]+ extra stdin=IN$' <<< "$ro" && grep -qx 'rc=3' <<< "$ro" \
  || fail "ran: the shim did not pass argv, stdin, stdout and exit through: $ro"
grep -qx "$t/bin/other-prog" <<< "$ro" || fail "ran: shim only for the named program: $ro"
jq -e '[.attempts[] | select(.kind == "run" and .program == "runme" and .exit == 3 and .attempt == false)] | length == 1' \
  "$d/ran/rpass/sandbox.json" > /dev/null || fail "ran: run not in the record: $(cat "$d/ran/rpass/sandbox.json")"
# Flag and value pairs anywhere after the positional prefix (rule: schema.md, Run record).
mkdir -p "$t/rf/rf/reference"; cp -r "$t/good/fixtures" "$t/rf/"
echo '{"suite": "rf", "kind": "role-transcript", "description": "stub ran flags", "max_tool_calls": 10, "timeout_s": 60}' > "$t/rf/rf/suite.json"
python3 - "$t/rf/rf" <<'PY'
import json, sys
d = sys.argv[1]
role = ["--role", "shaper"]
cases = [("rflag", "runme --a x --role shaper", role), ("rsplit", "runme --role --x shaper", role), ("rnoval", "runme --x shaper", role),
         ("rpos", "runme other --role shaper", ["sub", *role]), ("rposok", "runme sub --a x --role shaper", ["sub", *role])]
json.dump([{"id": i, "role": "implementer", "fixture": "fx", "task": "Do it. STUB-STEPS:" + json.dumps([["bash", c + " < /dev/null; true"]])}
           for i, c, _ in cases], open(f"{d}/cases.json", "w"))
json.dump({i: {"facts": [{"fact": "ran", "program": "runme", "args": a}]} for i, _, a in cases}, open(f"{d}/reference/expectations.json", "w"))
PY
run 1 "$Q" --evals "$t/rf"
rf() { grep -E "^$1 rf/$2: " <<< "$out" || fail "ran $2: want $1: $out"; }
rf PASS rflag > /dev/null; rf PASS rposok > /dev/null
for c in rsplit rnoval rpos; do rf FAIL "$c" | grep -q "no run of runme with these arguments" || fail "ran $c: want FAIL naming the record: $out"; done
# fake_qa (schema.md, Case): the role's own octo-feather-qa call recorded by the ran shim and answered by the fake;
# a poison octo-feather-qa further down PATH (where the kit's real one would be found) never runs.
printf '#!/bin/sh\necho POISON-REAL-QA-REACHED\nexit 9\n' > "$t/bin/octo-feather-qa"; chmod +x "$t/bin/octo-feather-qa"
mkdir -p "$t/fq/fq/reference"; cp -r "$t/good/fixtures" "$t/fq/"
echo '{"suite": "fq", "kind": "role-transcript", "description": "stub fake qa", "max_tool_calls": 10, "timeout_s": 60}' > "$t/fq/fq/suite.json"
python3 - "$t/fq/fq" <<'PY'
import json, sys
d = sys.argv[1]
step = [["bash", "octo-feather-qa --case c1 --runs 3 --baseline 0f4f1ba < /dev/null; echo rc=$?"]]
json.dump([{"id": "fq", "role": "implementer", "fixture": "fx", "fake_qa": True, "task": "Prove it. STUB-STEPS:" + json.dumps(step)}],
          open(f"{d}/cases.json", "w"))
json.dump({"fq": {"facts": [{"fact": "ran", "program": "octo-feather-qa", "args": ["--baseline"]},
                            {"fact": "ran", "program": "octo-feather-qa", "args": ["--runs"]}]}}, open(f"{d}/reference/expectations.json", "w"))
PY
run 0 "$Q" --evals "$t/fq"
grep -qE '^PASS fq/fq: ran octo-feather-qa --baseline: recorded run octo-feather-qa --case c1 --runs 3 --baseline 0f4f1ba \(exit 0\); ran octo-feather-qa --runs: ' <<< "$out" \
  || fail "fake_qa: want PASS on both ran facts: $out"
d="$(ls -dt "$t"/out/*/ | head -1)"
fo="$(jq -r 'select(.type == "tool_execution_end") | .result.structuredContent.output' "$d/fq/fq/transcript.jsonl")"
grep -qx 'qa (fake, factory eval: no case runs): octo-feather-qa --case c1 --runs 3 --baseline 0f4f1ba' <<< "$fo" && grep -qx 'rc=0' <<< "$fo" \
  && ! grep -q 'POISON-REAL-QA-REACHED\|qc sandbox' <<< "$fo" || fail "fake_qa: the fake did not answer, or something real ran: $fo"
# A run count and a bare flag together (schema.md, Run record): ran octo-feather-qa [--runs, 3, --baseline] holds for
# `--runs 3 --baseline main`, not for the smoke `--runs 1 --baseline main`.
python3 - "$t/fq/fq" <<'PY'
import json, sys
d = sys.argv[1]
st = lambda n: "Prove it. STUB-STEPS:" + json.dumps([["bash", f"octo-feather-qa --case c1 --runs {n} --baseline main < /dev/null; echo rc=$?"]])
json.dump([{"id": f"fq{n}", "role": "implementer", "fixture": "fx", "fake_qa": True, "task": st(n)} for n in (1, 3)], open(f"{d}/cases.json", "w"))
json.dump({f"fq{n}": {"facts": [{"fact": "ran", "program": "octo-feather-qa", "args": ["--runs", "3", "--baseline"]}]} for n in (1, 3)},
          open(f"{d}/reference/expectations.json", "w"))
PY
run 1 "$Q" --evals "$t/fq"
grep -q '^FAIL fq/fq1: ran octo-feather-qa --runs 3 --baseline: no run of octo-feather-qa with these arguments' <<< "$out" \
  && grep -q '^PASS fq/fq3: ran octo-feather-qa --runs 3 --baseline: recorded run octo-feather-qa --case c1 --runs 3 --baseline main (exit 0)' <<< "$out" \
  || fail "fake_qa runs 3: want fq1 FAIL (the smoke) and fq3 PASS: $out"
echo "qa-ran: ok (ran (a run through the sandbox's recording shim matched by its arguments (positional prefix, flag and value pairs anywhere) and {head}, stdin/stdout/exit passed through, an echo or other arguments fail naming the record, a shim only for a named program))"
