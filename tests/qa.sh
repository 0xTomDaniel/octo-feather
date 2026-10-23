#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape),
# driven as commands with a stub `pi` and a fake `herdr` first on PATH: no model, no live Herdr.
# Proves: one PASS/FAIL line per case naming the deciding transcript facts, exit 1 on any failure and 0
# when all pass, --suite/--case selection, per-run artifacts outside the repo, the run stops once its
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
tdd = next((x + "/SKILL.md" for x in a if x.endswith("/tdd")), None)   # None: the role does not list tdd
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
if "STUB-READ-TDD" in prompt and tdd:
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
case_() { printf '{"id": "%s", "role": "implementer", "fixture": "fx", "should_trigger": %s, "split": "train", "task": "%s"}' "$@"; }
cat > "$t/evals/trig/cases.json" <<EOF
[$(case_ reads true "Build it. STUB-READ-TDD"), $(case_ near false "Only look. STUB-READ-TDD"), $(case_ quiet false "Only look."),
 $(case_ linger true "Build it. STUB-READ-TDD STUB-LINGER"), $(case_ crash false "Only look. STUB-CRASH")]
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
EOF

# Selection: --case and --suite; all selected pass: exit 0. Unknown names: 64.
run 0 "$Q" --evals "$t/evals" --case reads --case quiet
[[ "$(grep -cE '^(PASS|FAIL) ' <<< "$out")" == 2 ]] || fail "--case selected the wrong cases: $out"
run 64 "$Q" --evals "$t/evals" --suite nope
run 64 "$Q" --evals "$t/evals" --case nope

# A failed sandbox proof (raw herdr reaches a live session) is a FAIL; the case never runs.
FAKE_HERDR_LEAK=1 run 1 "$Q" --evals "$t/evals" --case reads
line FAIL reads | grep -q "sandbox: proof failed, case not run: .*FAIL live Herdr unreachable" || fail "proof failure not a FAIL: $out"
[[ ! -e "$(ls -dt "$t"/out/*/ | head -1)/trig/reads/transcript.jsonl" ]] || fail "case ran after a failed proof"

# Inside a check run (marker set) it refuses before any case: 70.
OCTO_FEATHER_CHECK_RUN='{"just":1}' run 70 "$Q" --evals "$t/evals"
! grep -q "qa: run " <<< "$out" || fail "a case started inside a check run: $out"

# --kit-ref: the same case against an earlier kit commit. A throwaway kit repo (this kit's tree) whose history
# is c0 no implementer role, c1 the implementer not listing tdd, c2 the head; cases and grader stay the head's.
gk() { git -C "$t/kit" -c user.name=t -c user.email=t@t.invalid -c commit.gpgsign=false -c core.hooksPath=/dev/null "$@"; }
mkdir "$t/kit"; tar -C "$kit" --exclude=./.git -cf - . | tar -C "$t/kit" -xf -
im="$t/kit/agents/implementer.md"; cp "$im" "$t/im.md"
gk init -q -b main; rm "$im"; gk add -A; gk commit -qm c0; c0="$(gk rev-parse HEAD)"
sed 's/^skills:\(.*\), tdd,/skills:\1,/' "$t/im.md" > "$im"; grep -q '^skills:' "$im" && ! grep -q '^skills:.*tdd' "$im" || fail "c1 still lists tdd"
gk add -A; gk commit -qm c1; c1="$(gk rev-parse HEAD)"
cp "$t/im.md" "$im"; gk commit -qam c2; c2="$(gk rev-parse HEAD)"
K="$t/kit/scripts/octo-feather-qa"
run 1 "$K" --evals "$t/evals" --case reads --kit-ref "${c1:0:9}"
line FAIL reads | grep -q "skill_read tdd: no read of tdd/SKILL.md.*\[kit $c1\]" || fail "kit-ref before the change: want FAIL with its sha: $out"
grep -q "ok   extra binds read-only" <<< "$out" || fail "the earlier kit is not bound read-only in the sandbox: $out"
d="$(ls -dt "$t"/out/*/ | head -1)"
python3 - "$d/trig/reads" "$c1" <<'EOF' || fail "kit-ref artifacts wrong"
import json, sys
c, sha = sys.argv[1:]
argv = json.loads(open(f"{c}/transcript.jsonl").readline())["argv"]
sk = [argv[i + 1] for i, a in enumerate(argv) if a == "--skill"]
assert sk and all("/qa-kit-" in s for s in sk), sk   # the earlier kit's own skills, not the head's
assert json.load(open(f"{c}/input.json"))["kit_sha"] == sha and json.load(open(f"{c}/result.json"))["kit_sha"] == sha
EOF
! ls -d "$TMPDIR"/qa-kit-* 2>/dev/null || fail "the earlier kit's scratch copy outlived the run"
run 0 "$K" --evals "$t/evals" --case reads --kit-ref "$c2"
line PASS reads | grep -q "\[kit $c2\]" || fail "kit-ref at the change: want PASS with its sha: $out"
run 0 "$K" --evals "$t/evals" --case reads
line PASS reads | grep -q "\[kit $c2\]" || fail "head run does not record the kit's HEAD sha: $out"
run 1 "$K" --evals "$t/evals" --case reads --kit-ref "$c0"
line FAIL reads | grep -q "kit $c0: no agents/implementer.md at that commit" || fail "missing role file not named: $out"
run 64 "$K" --evals "$t/evals" --case reads --kit-ref no-such-ref
grep -q "kit-ref no-such-ref: no such commit" <<< "$out" && ! grep -q "qa: run " <<< "$out" || fail "unknown ref not refused by name: $out"

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
echo "qa: ok (PASS/FAIL per case with deciding facts, exit 1/0, --suite/--case, artifacts, stop once decided, dead pi fails, sandbox proof failure fails, refused in a check run, --kit-ref FAIL before and PASS at a kit change with its sha, missing role file named, unknown ref 64, shape check names case and field)"
