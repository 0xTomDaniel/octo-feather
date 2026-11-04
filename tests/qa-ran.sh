#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape),
# driven as commands with a stub `pi` and a fake `herdr` first on PATH: no model, no live Herdr (tests/lib/qa.sh).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves: ran: a run through the sandbox's recording shim matched by argv prefix and {head}, stdin/stdout/exit
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
rn FAIL recho "ran runme lane show \\{head\\}: no run of runme with these leading arguments in the sandbox's record \\([0-9]+ entries; no run of runme recorded\\)"
rn FAIL rother 'runs of runme: runme lane show 0000000 \(exit 3\); runme lane list \(exit 3\)\)'
grep -q "qc sandbox: ok   run record: shims first on PATH for runme " <<< "$out" || fail "ran: no proof line naming the run shims: $out"
d="$(ls -dt "$t"/out/*/ | head -1)"
ro="$(jq -r 'select(.type == "tool_execution_end") | .result.structuredContent.output' "$d/ran/rpass/transcript.jsonl")"
grep -qE '^runme: lane show [0-9a-f]+ extra stdin=IN$' <<< "$ro" && grep -qx 'rc=3' <<< "$ro" \
  || fail "ran: the shim did not pass argv, stdin, stdout and exit through: $ro"
grep -qx "$t/bin/other-prog" <<< "$ro" || fail "ran: shim only for the named program: $ro"
jq -e '[.attempts[] | select(.kind == "run" and .program == "runme" and .exit == 3 and .attempt == false)] | length == 1' \
  "$d/ran/rpass/sandbox.json" > /dev/null || fail "ran: run not in the record: $(cat "$d/ran/rpass/sandbox.json")"
echo "qa-ran: ok (ran (a run through the sandbox's recording shim matched by argv prefix and {head}, stdin/stdout/exit passed through, an echo or other arguments fail naming the record, a shim only for a named program))"
