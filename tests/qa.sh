#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape),
# driven as commands with a stub `pi` and a fake `herdr` first on PATH: no model, no live Herdr (tests/lib/qa.sh).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves: one PASS/FAIL line per case naming the deciding transcript facts, exit 1 on any failure and 0 when all
# pass, train and held-out score lines, per-run artifacts outside the repo, --suite/--case selection, --sample stratified
# and deterministic, role-skill coverage ({tracker} resolved per fixture), the run stops once its facts are decided, a pi
# that dies without an answer fails its case, each case runs in the qc sandbox and a failed sandbox proof is a FAIL,
# refusal inside a check run.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
# shellcheck source=tests/lib/qa.sh
source "$(dirname "$0")/lib/qa.sh"
# The kit's own suites are well formed.
"$C" > /dev/null || fail "kit evals/ fails its shape check"

# Every case: one line each, facts named; any failure exits 1.
t0=$SECONDS
run 1 "$Q" --evals "$t/evals"
line PASS reads | grep -q "skill_read tdd: loaded at tool call 2 of 2 (read .*/tdd/SKILL.md)" || fail "reads: deciding fact not named: $out"
line FAIL near | grep -q "skill_not_read tdd: loaded at tool call 2" || fail "near: deciding fact not named: $out"
line PASS quiet | grep -q "skill_not_read tdd: no load of tdd/SKILL.md (its full content in a tool result) in 1 tool calls" || fail "quiet: deciding fact not named: $out"
line PASS linger | grep -q "stop: decided" || fail "linger: run not stopped once decided: $out"
(( SECONDS - t0 < 100 )) || fail "the lingering stub was not stopped once its fact was decided ($((SECONDS - t0)) s)"
line FAIL crash | grep -q "run: pi exited 3 on its own" || fail "crash: a dead pi must fail, not pass skill_not_read: $out"
grep -q "qc sandbox: ok   writable persistent paths: none" <<< "$out" || fail "no sandbox proof printed: $out"
grep -q "qa: 3/5 passed" <<< "$out" || fail "no summary line: $out"
# Train (reads, quiet, crash) and held-out (near, linger) scored apart, after every case line, before the summary.
[[ "$(grep -E '^(PASS|FAIL) |^qa: (train|held-out) score|^qa: [0-9]+/' <<< "$out" | tail -3 | sed 's/ (run .*//')" == $'qa: train score 2/3 passed\nqa: held-out score 1/2 passed\nqa: 3/5 passed' ]] \
  || fail "score lines missing or out of order: $out"
# Artifacts outside the repo, per case and per run; the prompt's content (rule: schema.md, Layout).
d="$(ls -d "$t"/out/*/)"; c="$d/trig/reads"
for f in prompt.md input.json transcript.jsonl stderr.txt sandbox.json grading.json result.json; do [[ -e "$c/$f" ]] || fail "artifact $f missing"; done
[[ -s "$d/summary.json" ]] || fail "no summary.json"
grep -q "STUB-READ-TDD" "$c/prompt.md" && ! grep -q "skill_read" "$c/prompt.md" "$c/input.json" || fail "prompt or input leaks the expectations"
python3 - "$c" "$d" <<'EOF' || fail "artifacts wrong"
import json, sys
c, d = sys.argv[1:]
argv = json.loads(open(f"{c}/transcript.jsonl").readline())["argv"]
s = " ".join(argv)
assert "--mode json" in s and "--session-dir /tmp/qa-session" in s and "-p" in argv, s   # never ~/.pi sessions
assert "--no-skills" in argv and any(a.endswith("/tdd") for a in argv), "not launched through pi-role's implementer"
r = json.load(open(f"{c}/result.json")); assert r["verdict"] == "PASS" and r["model"] == "stub/stub-model", r
g = json.load(open(f"{c}/grading.json")); assert g["facts"][0]["status"] == "pass", g
sb = json.load(open(f"{c}/sandbox.json")); assert sb["proof"] and "agents_started" in sb, sb
sm = json.load(open(f"{d}/summary.json")); assert (sm["passed"], sm["total"]) == (3, 5), sm
assert sm["scores"] == {"train": {"passed": 2, "total": 3}, "held-out": {"passed": 1, "total": 2}}, sm["scores"]
EOF

# Selection: --case and --suite; all selected pass: exit 0. Unknown names: 64.
run 0 "$Q" --evals "$t/evals" --case reads --case quiet
[[ "$(grep -cE '^(PASS|FAIL) ' <<< "$out")" == 2 ]] || fail "--case selected the wrong cases: $out"
run 64 "$Q" --evals "$t/evals" --suite nope
run 64 "$Q" --evals "$t/evals" --case nope
run 64 "$Q" --evals "$t/evals" --sample 0

# --sample 2: one should and one should-not, one train and one held-out, named before the run; the same picks twice.
sampled() { grep '^qa: sample ' <<< "$out" || fail "no sample line: $out"; }
run 1 "$Q" --evals "$t/evals" --sample 2; s1="$(sampled)"
[[ "$(grep -cE '^(PASS|FAIL) ' <<< "$out")" == 2 ]] || fail "--sample 2 ran the wrong number of cases: $out"
for want in "should_trigger true" "should_trigger false" ", train)" ", held-out)"; do
  grep -qF "$want" <<< "$s1" || fail "sample not stratified, no '$want': $s1"; done
grep -q "^qa: sample 2 of 5 (seed " <<< "$s1" || fail "sample line does not say its seed and size: $s1"
grep -q '^qa: train score 1/1' <<< "$out" || fail "no train score in a sample: $out"
run 1 "$Q" --evals "$t/evals" --sample 2; [[ "$(sampled)" == "$s1" ]] || fail "--sample not deterministic: $s1 vs $(sampled)"

# Coverage (rule: schema.md, Coverage): the kit's suite passes; then one held-out near miss dropped.
cp -r "$kit/evals" "$t/kit-evals"
python3 - "$t/kit-evals/skill-triggers" <<'EOF'
import json, sys
d = sys.argv[1]; c = json.load(open(f"{d}/cases.json")); e = json.load(open(f"{d}/reference/expectations.json"))
gone = [x["id"] for x in c if x["role"] == "implementer" and not x["should_trigger"] and x["split"] == "held-out"
        and e[x["id"]]["facts"] == [{"fact": "skill_not_read", "skill": "pull"}]]
assert gone, "no held-out near miss for implementer pull in the kit suite"
json.dump([x for x in c if x["id"] not in gone], open(f"{d}/cases.json", "w"))
json.dump({k: v for k, v in e.items() if k not in gone}, open(f"{d}/reference/expectations.json", "w"))
EOF
run 1 "$C" "$t/kit-evals"
grep -qF "skill-triggers: role implementer skill pull: no case for should_trigger false split held-out" <<< "$out" || fail "coverage gap not named: $out"
# {tracker} on a role's skills line (rule: schema.md, Coverage): fixtures with no .octo-feather.toml, one naming linear,
# one naming an unknown tracker.
cp -r "$kit/evals" "$t/trk-evals"
python3 - "$t/trk-evals/skill-triggers" <<'EOF'
import json, sys
d = sys.argv[1]; c = json.load(open(f"{d}/cases.json")); e = json.load(open(f"{d}/reference/expectations.json"))
gone = [x["id"] for x in c if x["role"] == "supervisor" and x["should_trigger"] and x["split"] == "train"
        and e[x["id"]]["facts"] == [{"fact": "skill_read", "skill": "github-issues"}]]
assert gone, "no train should case for supervisor github-issues in the kit suite"
json.dump([x for x in c if x["id"] not in gone], open(f"{d}/cases.json", "w"))
json.dump({k: v for k, v in e.items() if k not in gone}, open(f"{d}/reference/expectations.json", "w"))
EOF
run 1 "$C" "$t/trk-evals"
grep -qF "skill-triggers: role supervisor skill github-issues: no case for should_trigger true split train;" <<< "$out" \
  || fail "a {tracker} gap not named as github-issues: $out"
[[ "$(grep -c ': role .* skill ' <<< "$out")" == 1 ]] || fail "only the dropped {tracker} pair should be missing: $out"
cp -r "$kit/evals" "$t/lin-evals"; echo 'tracker = "linear"' > "$t/lin-evals/fixtures/lane-mini/.octo-feather.toml"
run 1 "$C" "$t/lin-evals"
for r in director implementer supervisor; do grep -qF "skill-triggers: role $r skill linear: no case for should_trigger true split train" <<< "$out" \
  || fail "a fixture's linear tracker did not add $r linear: $out"; done
grep -q "skill {tracker}\|skill github-issues:" <<< "$out" && fail "{tracker} left unresolved, or github-issues dropped: $out"
echo 'tracker = "jira"' > "$t/lin-evals/fixtures/lane-mini/.octo-feather.toml"
run 1 "$C" "$t/lin-evals"
grep -qF "fixtures/lane-mini/.octo-feather.toml: field tracker: 'jira' has no kit tracker skill" <<< "$out" || fail "unknown tracker not named: $out"

# A failed sandbox proof (raw herdr reaches a live session) is a FAIL; the case never runs.
FAKE_HERDR_LEAK=1 run 1 "$Q" --evals "$t/evals" --case reads
line FAIL reads | grep -q "sandbox: proof failed, case not run: .*FAIL live Herdr unreachable" || fail "proof failure not a FAIL: $out"
[[ ! -e "$(ls -dt "$t"/out/*/ | head -1)/trig/reads/transcript.jsonl" ]] || fail "case ran after a failed proof"

# Inside a check run (marker set) it refuses before any case: 70.
OCTO_FEATHER_CHECK_RUN='{"just":1}' run 70 "$Q" --evals "$t/evals"
! grep -q "qa: run " <<< "$out" || fail "a case started inside a check run: $out"
echo "qa: ok (PASS/FAIL per case with deciding facts, exit 1/0, train and held-out scores, --sample, role-skill coverage ({tracker} resolved per fixture), --suite/--case, artifacts, stop once decided, dead pi fails, sandbox proof failure fails, refused in a check run)"
