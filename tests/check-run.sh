#!/usr/bin/env bash
# Integration test for scripts/octo-feather-check, the gate's step runner (#204, owner ruling #201): in a throwaway
# repo with its own small justfile and tests (never the kit's gate, so no recursion), each run prints its steps'
# output, a summary slowest first with the total, exits with the failing step's status, and appends one JSON line
# to check-runs.jsonl in the state dir; an unwritable state dir only warns. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
run="$kit/scripts/octo-feather-check"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fail() { echo "check-run test: $1" >&2; [[ -z "${2:-}" ]] || printf '%s\n' "$2" >&2; exit 1; }
r="$t/repo"; mkdir -p "$r/tests"
cat > "$r/justfile" <<'EOF'
check-a:
    @echo a-out
check-slow:
    @sleep 1; echo slow-out
check-bad:
    @echo bad-out; exit 3
EOF
printf '#!/bin/sh\necho "t1-out tmp=$TMPDIR"\n' > "$r/tests/t1.sh"; chmod +x "$r/tests/t1.sh"
git -C "$r" init -q; git -C "$r" add -A; git -C "$r" -c user.name=t -c user.email=t@t commit -qm base
head="$(git -C "$r" rev-parse HEAD)"
mkdir "$t/realtmp"; ln -s "$t/realtmp" "$t/linktmp"
trend="$t/state/octo-feather/check-runs.jsonl"
# go ARGS...: the runner in the repo, state under $t/state; sets rc, out (stdout), err (stderr).
go() {
  set +e
  out="$(cd "$r" && env -u HERDR_SESSION XDG_STATE_HOME="${STATE:-$t/state}" TMPDIR="$t/linktmp" "$run" "$@" 2>"$t/err")"; rc=$?
  set -e; err="$(cat "$t/err")"
}
# field EXPR: a Python expression over the trend file's last line `j`.
field() { tail -n 1 "$trend" | python3 -c 'import json, sys; j = json.loads(sys.stdin.read()); print(eval(sys.argv[1]))' "$1"; }

# A green run: every step's output, the summary slowest first, the total, one trend line.
go --step check-a --step check-slow --glob 'tests/*.sh'
[[ "$rc" == 0 ]] || fail "green run exited $rc" "$out$err"
for w in a-out slow-out "t1-out tmp=$t/realtmp"; do grep -qxF "$w" <<<"$out" || fail "green run lacks step output: $w" "$out"; done
summary="$(sed -n '/^octo-feather-check: step times, slowest first$/,$p' <<<"$out")"
[[ "$(wc -l <<<"$summary")" == 5 ]] || fail "summary is not a header, 3 steps and a total" "$out"
grep -qE '^ +[0-9]+\.[0-9]s  ok    check-slow$' <<<"$(sed -n 2p <<<"$summary")" || fail "slowest step not first" "$summary"
grep -qE '^ +[0-9]+\.[0-9]s  ok    total \(3 of 3 steps, exit 0\)$' <<<"$(tail -n 1 <<<"$summary")" || fail "no ok total line last" "$summary"
grep -qE '  ok    check-a$' <<<"$summary" && grep -qE '  ok    tests/t1\.sh$' <<<"$summary" || fail "a step missing from the summary" "$summary"
[[ "$(wc -l <"$trend")" == 1 ]] || fail "green run did not append exactly one trend line" "$(cat "$trend")"
[[ "$(field 'j["head"]')" == "$head" && "$(field 'j["exit"]')" == 0 && "$(field 'j["not_run"]')" == "[]" ]] || fail "trend head, exit or not_run wrong" "$(tail -n 1 "$trend")"
[[ "$(field '[(s["name"], s["result"]) for s in j["steps"]]')" == "[('check-a', 'ok'), ('check-slow', 'ok'), ('tests/t1.sh', 'ok')]" ]] || fail "trend steps wrong" "$(tail -n 1 "$trend")"
[[ "$(field 'j["steps"][1]["seconds"] >= 1 and j["total_s"] >= j["steps"][1]["seconds"]')" == True ]] || fail "trend seconds wrong" "$(tail -n 1 "$trend")"
field 'j["start"]' | grep -qE '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$' || fail "trend start is not UTC" "$(tail -n 1 "$trend")"

# A failing step fails the run with its own status and output; later steps do not run; the line still lands.
go --step check-a --step check-bad --step check-slow
[[ "$rc" == 3 ]] || fail "failing run exited $rc, want the step's 3" "$out$err"
grep -qxF bad-out <<<"$out" && ! grep -qxF slow-out <<<"$out" || fail "failing step output missing or a later step ran" "$out"
grep -qE '  FAIL  check-bad$' <<<"$out" && grep -qE '1 steps not run' <<<"$out" && grep -qE '  FAIL  total \(2 of 3 steps, exit 3\)$' <<<"$(tail -n 1 <<<"$out")" \
  || fail "failing summary wrong" "$out"
[[ "$(wc -l <"$trend")" == 2 && "$(field 'j["exit"]')" == 3 && "$(field 'j["not_run"]')" == "['check-slow']" ]] || fail "failing trend line wrong" "$(cat "$trend")"

# A state dir that cannot be written warns; the verdict stands.
: > "$t/notadir"
STATE="$t/notadir" go --step check-a
[[ "$rc" == 0 ]] && grep -qF 'octo-feather-check: warning: trend line not written' <<<"$err" || fail "unwritable state dir: exit $rc" "$out$err"
STATE="$t/notadir" go --step check-bad
[[ "$rc" == 3 ]] || fail "unwritable state dir changed a failing verdict: exit $rc" "$out$err"

# No steps is a usage error, not a green gate.
go
[[ "$rc" == 2 ]] || fail "no steps exited $rc" "$out$err"
go --glob 'none/*.sh'
[[ "$rc" == 2 ]] || fail "an empty glob exited $rc" "$out$err"
echo "check-run: ok (step output, summary slowest first with total, failing status kept, one trend line per run, unwritable state warns)"
