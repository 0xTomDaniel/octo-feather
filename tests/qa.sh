#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape),
# driven as commands with a stub `pi` and a fake `herdr` first on PATH: no model, no live Herdr.
# Proves: one PASS/FAIL line per case naming the deciding transcript facts, exit 1 on any failure and 0
# when all pass, train and held-out score lines, --sample stratified and deterministic, --suite/--case selection, per-run artifacts outside the repo, the run stops once its
# facts are decided, a pi that dies without an answer fails its case, each case runs in the qc sandbox
# and a failed sandbox proof is a FAIL, refusal inside a check run, and the shape check naming case and field.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
set -euo pipefail
# A test harness, not a gate recipe reaching the evals: its stub-pi runs start outside any check run (the one
# boundary; octo-feather-qa refuses under the marker, proved below).
unset OCTO_FEATHER_CHECK_RUN
[[ "$(uname -s)" != Darwin ]] || { echo "qa: skipped, not on macOS (the qc sandbox needs Linux; CI runs it)"; exit 0; }
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
Q="$kit/scripts/octo-feather-qa"; C="$kit/scripts/check-evals"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fail() { echo "qa test: $*" >&2; exit 1; }
export TMPDIR="$t/tmp"; mkdir "$TMPDIR"
# A throwaway HOME: the sandbox masks its (empty) live state, never the box's.
export HOME="$t/home" OCTO_FEATHER_QA_DIR="$t/out"
unset XDG_CONFIG_HOME XDG_STATE_HOME XDG_CACHE_HOME GH_CONFIG_DIR HERDR_SESSION HERDR_SOCKET_PATH HERDR_BIN_PATH HERDR_ENV
mkdir -p "$HOME" "$t/bin" "$t/evals/trig/reference" "$t/evals/fixtures/fx"
cat > "$t/bin/pi" <<'EOF'
#!/usr/bin/env python3
# Stub pi --mode json: canned event stream chosen by tokens in the -p prompt; its own argv as the first record.
import json, sys, time
a = sys.argv[1:]
prompt = a[a.index("-p") + 1]
tdd = next(x for x in a if x.endswith("/tdd")) + "/SKILL.md"
out = lambda e: print(json.dumps(e), flush=True)
out({"type": "stub_argv", "argv": a})
out({"type": "session", "version": 3, "id": "stub", "cwd": "."})
out({"type": "agent_start"})
if "STUB-CRASH" in prompt:
    sys.exit(3)
def tool(i, name, args):   # as pi: the assistant message holding the call ends, then the tool runs
    out({"type": "message_end", "message": {"role": "assistant", "provider": "stub", "model": "stub-model", "stopReason": "toolUse",
                                           "content": [{"type": "toolCall", "id": i, "name": name, "arguments": args}]}})
    out({"type": "tool_execution_start", "toolCallId": i, "toolName": name, "args": args})
tool("c1", "bash", {"command": "ls"})
if "STUB-READ-TDD" in prompt:
    tool("c2", "read", {"path": tdd})
if "STUB-LINGER" in prompt:
    time.sleep(120)
out({"type": "message_end", "message": {"role": "assistant", "provider": "stub", "model": "stub-model", "stopReason": "stop",
                                       "content": [{"type": "text", "text": "done"}]}})
EOF
cat > "$t/bin/herdr" <<'EOF'
#!/usr/bin/env bash
# Fake Herdr: a session's socket is a file under the config dir naming the session; FAKE_HERDR_LEAK reaches "live".
C="${XDG_CONFIG_HOME:-$HOME/.config}/herdr"; s=default; a=()
while (($#)); do case "$1" in --session) s="$2"; shift 2;; --remote|--machine) shift 2;; *) a+=("$1"); shift;; esac; done
[[ "$s" == default ]] && sock="$C/herdr.sock" || sock="$C/sessions/$s/herdr.sock"
case "${a[*]}" in
  server) mkdir -p "${sock%/*}"; echo "$s" > "$sock"; exec sleep 600;;
  "session stop "*) rm -f "$C/sessions/${a[2]}/herdr.sock"; exit 0;;
  "session delete "*) rm -rf "${C:?}/sessions/${a[2]}"; exit 0;;
esac
[[ -n "${FAKE_HERDR_LEAK:-}" ]] && { echo '{"session":"default"}'; exit 0; }
[[ -f "$sock" ]] || { echo server_not_running >&2; exit 1; }
[[ "${a[*]}" == "pane list" ]] && exit 0
echo "{\"session\":\"$(cat "$sock")\"}"
EOF
chmod +x "$t/bin/pi" "$t/bin/herdr"
export PATH="$t/bin:$kit/scripts:$PATH"
echo "fixture" > "$t/evals/fixtures/fx/README.md"
cat > "$t/evals/trig/suite.json" <<'EOF'
{"suite": "trig", "kind": "skill-trigger", "description": "stub suite", "max_tool_calls": 5, "timeout_s": 60}
EOF
case_() { printf '{"id": "%s", "role": "implementer", "fixture": "fx", "should_trigger": %s, "split": "%s", "task": "%s"}' "$@"; }
cat > "$t/evals/trig/cases.json" <<EOF
[$(case_ reads true train "Build it. STUB-READ-TDD"), $(case_ near false held-out "Only look. STUB-READ-TDD"), $(case_ quiet false train "Only look."),
 $(case_ linger true held-out "Build it. STUB-READ-TDD STUB-LINGER"), $(case_ crash false train "Only look. STUB-CRASH")]
EOF
r='{"facts": [{"fact": "skill_read", "skill": "tdd"}]}'; n='{"facts": [{"fact": "skill_not_read", "skill": "tdd"}]}'
echo "{\"reads\": $r, \"near\": $n, \"quiet\": $n, \"linger\": $r, \"crash\": $n}" > "$t/evals/trig/reference/expectations.json"
cp -r "$t/evals" "$t/good"

run() { local want="$1"; shift; set +e; out="$(timeout -k 5 240 "$@" 2>&1)"; rc=$?; set -e
  [[ "$rc" != 124 && "$rc" != 137 ]] || fail "'$*' hung, killed: $out"
  [[ "$rc" == "$want" ]] || fail "'$*' want exit $want, got $rc: $out"; }
line() { grep -E "^$1 trig/$2: " <<< "$out" || fail "no $1 line for $2: $out"; }

# The kit's own suites are well formed.
"$C" > /dev/null || fail "kit evals/ fails its shape check"

# Every case: one line each, facts named; any failure exits 1.
t0=$SECONDS
run 1 "$Q" --evals "$t/evals"
line PASS reads | grep -q "skill_read tdd: read at tool call 2 of 2 (read .*/tdd/SKILL.md)" || fail "reads: deciding fact not named: $out"
line FAIL near | grep -q "skill_not_read tdd: read at tool call 2" || fail "near: deciding fact not named: $out"
line PASS quiet | grep -q "skill_not_read tdd: no read of tdd/SKILL.md in 1 tool calls" || fail "quiet: deciding fact not named: $out"
line PASS linger | grep -q "stop: decided" || fail "linger: run not stopped once decided: $out"
(( SECONDS - t0 < 100 )) || fail "the lingering stub was not stopped once its fact was decided ($((SECONDS - t0)) s)"
line FAIL crash | grep -q "run: pi exited 3 on its own" || fail "crash: a dead pi must fail, not pass skill_not_read: $out"
grep -q "qc sandbox: ok   writable persistent paths: none" <<< "$out" || fail "no sandbox proof printed: $out"
grep -q "qa: 3/5 passed" <<< "$out" || fail "no summary line: $out"
# Train (reads, quiet, crash) and held-out (near, linger) scored apart, after every case line, before the summary.
[[ "$(grep -E '^(PASS|FAIL) |^qa: (train|held-out) score|^qa: [0-9]+/' <<< "$out" | tail -3 | sed 's/ (run .*//')" == $'qa: train score 2/3 passed\nqa: held-out score 1/2 passed\nqa: 3/5 passed' ]] \
  || fail "score lines missing or out of order: $out"
# Artifacts outside the repo, per case and per run; the prompt holds the task, never its expectations.
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

# Coverage: the kit's suite covers every role-listed skill; dropping one held-out near miss names the role and skill.
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

# A failed sandbox proof (raw herdr reaches a live session) is a FAIL; the case never runs.
FAKE_HERDR_LEAK=1 run 1 "$Q" --evals "$t/evals" --case reads
line FAIL reads | grep -q "sandbox: proof failed, case not run: .*FAIL live Herdr unreachable" || fail "proof failure not a FAIL: $out"
[[ ! -e "$(ls -dt "$t"/out/*/ | head -1)/trig/reads/transcript.jsonl" ]] || fail "case ran after a failed proof"

# Inside a check run (marker set) it refuses before any case: 70.
OCTO_FEATHER_CHECK_RUN='{"just":1}' run 70 "$Q" --evals "$t/evals"
! grep -q "qa: run " <<< "$out" || fail "a case started inside a check run: $out"

# Shape check: each defect names the case and the field; the evals refuse a malformed suite (exit 2).
bad() {   # bad PY_EDIT WANT: apply a python edit to a fresh copy's cases (c) and expectations (e), expect WANT
  rm -rf "$t/evals"; cp -r "$t/good" "$t/evals"
  python3 - "$t/evals/trig" "$1" <<'EOF'
import json, sys
d, code = sys.argv[1:]
c = json.load(open(f"{d}/cases.json")); e = json.load(open(f"{d}/reference/expectations.json"))
exec(code)
json.dump(c, open(f"{d}/cases.json", "w")); json.dump(e, open(f"{d}/reference/expectations.json", "w"))
EOF
  run 1 "$C" "$t/evals"; grep -qF "$2" <<< "$out" || fail "shape check missed: want '$2', got: $out"
}
bad 'del c[0]["task"]' "trig/cases.json case reads: field task: missing"
bad 'del c[1]["split"]' "trig/cases.json case near: field split: missing"
bad 'c[0]["facts"] = e["reads"]["facts"]' "trig/cases.json case reads: field facts: unknown field"
bad 'e["reads"]["facts"][0]["fact"] = "skill_vibes"' "case reads fact #1: field fact: unknown fact type 'skill_vibes'"
bad 'e["reads"]["facts"][0]["skill"] = "nope"' "case reads fact #1: field skill: no kit skill"
bad 'del e["quiet"]' "trig/cases.json case quiet: field id: no expectations"
bad 'e["ghost"] = e["quiet"]' "trig/reference/expectations.json case ghost: field id: no case in cases.json"
bad 'c[0]["task"] += " Read .agents/skills/tdd/SKILL.md first."' "case reads: field task: shows the agent its grade (skill path tdd/SKILL.md)"
bad 'c[2]["task"] += " Graded on " + json.dumps(e["quiet"]["facts"][0])' "case quiet: field task: shows the agent its grade (expectation JSON"
bad 'c[0]["should_trigger"] = False' "case reads: field should_trigger: false, but no skill_not_read fact"
bad 'c[0]["role"] = "nobody"' "case reads: field role: no kit role agents/nobody.md"
run 2 "$Q" --evals "$t/evals"
grep -q "field role: no kit role" <<< "$out" && ! grep -q "qa: run " <<< "$out" || fail "evals ran a malformed suite: $out"
echo "qa: ok (PASS/FAIL per case with deciding facts, exit 1/0, train and held-out scores, --sample, role-skill coverage, --suite/--case, artifacts, stop once decided, dead pi fails, sandbox proof failure fails, refused in a check run, shape check names case and field)"
