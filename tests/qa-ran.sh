#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape),
# driven as commands with a stub `pi` and a fake `herdr` first on PATH: no model, no live Herdr (tests/lib/qa.sh).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves: ran: a run through the sandbox's recording shim matched by its arguments (positional prefix, flag and value pairs anywhere) and {head}, a count of matching runs, a case's stand-ins ({repo}, {head}, {head:N} filled), stdin/stdout/exit
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
# count (rule: schema.md, Run record).
python3 - "$t/rf/rf" <<'PY'
import json, sys
d = sys.argv[1]
two, other = "runme --role shaper < /dev/null; runme --role shaper < /dev/null; runme --x y", "runme --x y"
cases = [("rc2", two, 2), ("rc1", two, 1), ("rc0", other, 0), ("rc0hit", two, 0)]
steps = lambda c: [["bash", x + " < /dev/null; true"] for x in c.split(" ;; ")]
# rclater: the first call's run decides the plain ran fact beside it; the count stays open and sees the later call's run.
cases.append(("rclater", "runme --role shaper ;; runme --x y ;; runme --role shaper", 1))
json.dump([{"id": i, "role": "implementer", "fixture": "fx", "task": "Do it. STUB-STEPS:" + json.dumps(steps(c))}
           for i, c, _ in cases], open(f"{d}/cases.json", "w"))
fact = lambda n: {"fact": "ran", "program": "runme", "args": ["--role"], "count": n}
json.dump({i: {"facts": [fact(n)] + ([{"fact": "ran", "program": "runme", "args": ["--role"]}] if i == "rclater" else [])} for i, _, n in cases},
          open(f"{d}/reference/expectations.json", "w"))
PY
run 1 "$Q" --evals "$t/rf"
rf PASS rc2 | grep -q 'ran runme --role count 2: 2 matching runs: ' || fail "ran count 2: want PASS naming both runs: $out"
rf PASS rc0 | grep -q 'ran runme --role count 0: 0 matching runs (' || fail "ran count 0: want PASS: $out"
rf FAIL rc1 | grep -q 'ran runme --role count 1: 2 matching runs: ' || fail "ran count 1: want FAIL on the second run: $out"
rf FAIL rc0hit | grep -q 'ran runme --role count 0: [12] matching runs: ' || fail "ran count 0: want FAIL at the first run: $out"
rf FAIL rclater | grep -q 'ran runme --role count 1: 2 matching runs: ' || fail "ran count 1: want FAIL on a later call's run after a fact beside it was decided: $out"
# stand_ins (rule: schema.md, Case).
python3 - "$t/rf/rf" <<'PY'
import json, sys
d = sys.argv[1]
step = [["bash", "herdr-say --parent 'hi there' < /dev/null; echo rc=$?; herdr-say --parent < /dev/null; echo rc=$?; herdr-say other x < /dev/null; echo rc=$?; "
                 "herdr agent get p1; echo rc=$?; herdr-close p1; herdr agent get p1; echo rc=$?; echo REPO=$PWD; herdr pane read p1; echo HEAD=$(git rev-parse HEAD); echo SHORT=$(git rev-parse --short=12 HEAD)"]]
stands = {"herdr-say": [{"args": ["--parent"], "argc": 2, "stdout": "delivered\n", "exit": 0},
                        {"args": ["--parent"], "stdout": "usage: herdr-say\n", "exit": 64}],
          "herdr": [{"args": ["agent", "get", "p1"], "stdout": "gone\n", "exit": 1, "after": ["herdr-close", "p1"]},
                    {"args": ["agent", "get", "p1"], "stdout": "up in {repo}\n", "exit": 0},
                    {"args": ["pane", "read", "p1"], "stdout": "at {head:12} of {head}\n", "exit": 0}],
          "herdr-close": [{"args": [], "stdout": "", "exit": 0}]}
json.dump([{"id": "rstand", "role": "implementer", "fixture": "fx", "task": "Do it. STUB-STEPS:" + json.dumps(step),
            "stand_ins": stands}], open(f"{d}/cases.json", "w"))
json.dump({"rstand": {"facts": [{"fact": "ran", "program": "herdr-say", "args": ["--parent", "hi there"], "count": 1},
                                 {"fact": "ran", "program": "herdr-say", "args": ["--parent"], "exit": 64, "count": 1}]}},
          open(f"{d}/reference/expectations.json", "w"))
PY
run 0 "$Q" --evals "$t/rf"
grep -q '^PASS rf/rstand: ran herdr-say --parent hi there count 1: 1 matching runs: herdr-say --parent hi there (exit 0)' <<< "$out" \
  || fail "stand_ins: want PASS on the recorded stand-in call: $out"
grep -q 'ran herdr-say --parent exit 64 count 1: 1 matching runs: herdr-say --parent (exit 64)' <<< "$out" \
  || fail "ran exit 64 count 1: want PASS counting only the run that exited 64, not the --parent run that exited 0: $out"
d="$(ls -dt "$t"/out/*/ | head -1)"
so="$(jq -r 'select(.type == "tool_execution_end") | .result.structuredContent.output' "$d/rf/rstand/transcript.jsonl")"
grep -qx 'delivered' <<< "$so" && grep -qx 'rc=0' <<< "$so" && grep -qx 'usage: herdr-say' <<< "$so" && grep -qx 'rc=64' <<< "$so" && grep -q '^stand-in: no answer for .*herdr-say other x$' <<< "$so" && grep -qx 'rc=1' <<< "$so" \
  || fail "stand_ins: want the canned answer, exit 0, the argc-mismatch answer, exit 64, then the no-answer exit 1: $so"
repo="$(sed -n 's/^REPO=//p' <<< "$so")"
[[ -n "$repo" ]] && grep -qx "up in $repo" <<< "$so" && grep -qx 'gone' <<< "$so" \
  || fail "stand_ins: want {repo} filled, then the after-close answer: $so"
head="$(sed -n 's/^HEAD=//p' <<< "$so")"   # {head:N}: schema.md, Case, stand_ins
short="$(sed -n 's/^SHORT=//p' <<< "$so")"   # git's own --short=12 of that HEAD, the oracle
[[ ${#head} == 40 && ${#short} == 12 ]] && grep -qx "at $short of $head" <<< "$so" || fail "stand_ins: want {head:12} and {head} filled: $so"
# fake_qa (schema.md, Case): the role's own octo-feather-qa call recorded by the ran shim and answered in the real
# tool's output form, with no case run; a poison octo-feather-qa further down PATH (where the kit's real one would be
# found) never runs. The case repo holds an eval suite (fixture fxe: fx plus evals/s1, case c1).
printf '#!/bin/sh\necho POISON-REAL-QA-REACHED\nexit 9\n' > "$t/bin/octo-feather-qa"; chmod +x "$t/bin/octo-feather-qa"
mkdir -p "$t/fq/fq/reference"; cp -r "$t/good/fixtures" "$t/fq/"
cp -r "$t/fq/fixtures/fx" "$t/fq/fixtures/fxe"; mkdir -p "$t/fq/fixtures/fxe/evals/s1/reference"
echo '{"suite": "s1", "kind": "role-transcript", "description": "x"}' > "$t/fq/fixtures/fxe/evals/s1/suite.json"
echo '[{"id": "c1", "role": "implementer", "fixture": "fx", "task": "x"}]' > "$t/fq/fixtures/fxe/evals/s1/cases.json"
echo '{"c1": {"facts": [{"fact": "skill_read", "skill": "tdd"}]}}' > "$t/fq/fixtures/fxe/evals/s1/reference/expectations.json"
echo '{"suite": "fq", "kind": "role-transcript", "description": "stub fake qa", "max_tool_calls": 10, "timeout_s": 60}' > "$t/fq/fq/suite.json"
python3 - "$t/fq/fq" <<'PY'
import json, sys
d = sys.argv[1]
step = [["bash", "octo-feather-qa --case c1 --runs 3 --baseline main < /dev/null; echo rc=$?; octo-feather-qa --help | head -1"]]
json.dump([{"id": "fq", "role": "implementer", "fixture": "fxe", "fake_qa": True, "task": "Prove it. STUB-STEPS:" + json.dumps(step)}],
          open(f"{d}/cases.json", "w"))
json.dump({"fq": {"facts": [{"fact": "ran", "program": "octo-feather-qa", "args": ["--baseline"]},
                            {"fact": "ran", "program": "octo-feather-qa", "args": ["--runs"]}]}}, open(f"{d}/reference/expectations.json", "w"))
PY
run 0 "$Q" --evals "$t/fq"
grep -qE '^PASS fq/fq: ran octo-feather-qa --baseline: recorded run octo-feather-qa --case c1 --runs 3 --baseline main \(exit 0\); ran octo-feather-qa --runs: ' <<< "$out" \
  || fail "fake_qa: want PASS on both ran facts: $out"
d="$(ls -dt "$t"/out/*/ | head -1)"
fo="$(jq -r 'select(.type == "tool_execution_end") | .result.structuredContent.output' "$d/fq/fq/transcript.jsonl")"
for want in '^evals: ok \(1 suites, 1 cases\)$' '^qa: run [0-9]{8}T[0-9]{6}Z-[0-9a-f]{6}: 1 case\(s\), 3 runs each; kit [0-9a-f]{40}; baseline kit [0-9a-f]{40} \(--baseline main\), runs interleaved; artifacts ' \
    '^  baseline run 1/3: FAIL s1/c1: skill_read tdd: no load of tdd/SKILL.md' '^  current run 3/3: PASS s1/c1: skill_read tdd: loaded at tool call 2 of ' \
    '^PASS s1/c1: 3/3 runs passed \(pass rate 1.00, stddev 0.00\); run 1: ' '^  baseline FAIL s1/c1: 0/3 runs passed \(pass rate 0.00, stddev 0.00\)' \
    '^  compare s1/c1: baseline kit [0-9a-f]{12} beside current kit [0-9a-f]{12}$' '^    pass rate  0.00 \+/- 0.00        1.00 \+/- 0.00        \+1.00$' \
    '^qa: analysis \(deterministic, no model; rules: octo-feather-qa --help, --analyze\):$' '^qa: 1/1 passed \(run [0-9T]{15}Z-[0-9a-f]{6}\); artifacts ' '^rc=0$' \
    '^octo-feather-qa \[--suite NAME\]'; do
  grep -qE "$want" <<< "$fo" || fail "fake_qa: no line like $want in: $fo"; done
! grep -qi 'fake\|POISON-REAL-QA-REACHED\|qc sandbox' <<< "$fo" || fail "fake_qa: the answer names itself, or something real ran: $fo"
# A run count and a bare flag together (schema.md, Run record): ran octo-feather-qa [--runs, 3, --baseline] holds for
# `--runs 3 --baseline main`, not for the smoke `--runs 1 --baseline main`.
python3 - "$t/fq/fq" <<'PY'
import json, sys
d = sys.argv[1]
st = lambda n: "Prove it. STUB-STEPS:" + json.dumps([["bash", f"octo-feather-qa --case c1 --runs {n} --baseline main < /dev/null; echo rc=$?"]])
json.dump([{"id": f"fq{n}", "role": "implementer", "fixture": "fxe", "fake_qa": True, "task": st(n)} for n in (1, 3)], open(f"{d}/cases.json", "w"))
json.dump({f"fq{n}": {"facts": [{"fact": "ran", "program": "octo-feather-qa", "args": ["--runs", "3", "--baseline"]}]} for n in (1, 3)},
          open(f"{d}/reference/expectations.json", "w"))
PY
run 1 "$Q" --evals "$t/fq"
grep -q '^FAIL fq/fq1: ran octo-feather-qa --runs 3 --baseline: no run of octo-feather-qa with these arguments' <<< "$out" \
  && grep -q '^PASS fq/fq3: ran octo-feather-qa --runs 3 --baseline: recorded run octo-feather-qa --case c1 --runs 3 --baseline main (exit 0)' <<< "$out" \
  || fail "fake_qa runs 3: want fq1 FAIL (the smoke) and fq3 PASS: $out"
echo "qa-ran: ok (ran (a run through the sandbox's recording shim matched by its arguments (positional prefix, flag and value pairs anywhere) and {head}, a count of matching runs, a case's stand-ins, stdin/stdout/exit passed through, an echo or other arguments fail naming the record, a shim only for a named program))"
