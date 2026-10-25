#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape),
# driven as commands with a stub `pi` and a fake `herdr` first on PATH: no model, no live Herdr.
# Proves: one PASS/FAIL line per case naming the deciding transcript facts, exit 1 on any failure and 0
# when all pass, train and held-out score lines, --sample stratified and deterministic, role-skill coverage,
# --suite/--case selection, per-run artifacts outside the repo, the run stops once its facts are decided, a pi
# that dies without an answer fails its case, each case runs in the qc sandbox and a failed sandbox proof is a FAIL,
# refusal inside a check run, and the shape check naming case and field.
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
import json, subprocess, sys, time
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
def pi_read(path):   # as Pi's read tool: the file's text; a missing file is an error
    try:
        return False, open(path).read()
    except OSError as e:
        return True, f"ENOENT: {e}"
if "STUB-READ-TDD" in prompt and tdd:
    tool("c2", "read", {"path": tdd})
    err, txt = pi_read(tdd)
    out({"type": "tool_execution_end", "toolCallId": "c2", "toolName": "read", "isError": err, "result": {"content": [{"type": "text", "text": txt}]}})
if "STUB-LINGER" in prompt:
    time.sleep(120)
if "STUB-ATTEMPTS" in prompt:   # really run each command in the sandbox, as pi's bash tool would, result and all
    cmds = ['herdr agent prompt w2:p2 "diag online"; echo "exit=$?"', 'ls -la "$HOME/.local/state/octo-feather/lanes"',
            'ls "$(octo-feather-state)/lanes/archive"', 'cat "$HOME/.local/state/octo-feather/director.toml"']
    if "STUB-LEAK" in prompt:
        cmds.append('echo "octo-feather/lanes/gh1.toml: lane = gh1"; ls /nowhere/octo-feather/lanes')   # a refusal beside a live name
    if "STUB-NOCRED" not in prompt:
        cmds += ['gh auth token 2>&1 | cut -c1-60', 'cat "$HOME/.git-credentials"']
    for k, c in enumerate(cmds):
        tool(f"a{k}", "bash", {"command": c})
        p = subprocess.run(["bash", "-c", c], capture_output=True, text=True)
        o = p.stdout + p.stderr
        out({"type": "tool_execution_end", "toolCallId": f"a{k}", "toolName": "bash", "isError": p.returncode != 0,
             "result": {"content": [{"type": "text", "text": o + (f"\n\nCommand exited with code {p.returncode}" if p.returncode else "")}],
                        "structuredContent": {"output": o, "exit_code": p.returncode}}})
if "STUB-STEPS:" in prompt:   # a scripted run: [["read", PATH] | ["bash", CMD] | ["say", TEXT]...]; @S is skill S's
    import os                 # SKILL.md, @@S its dir, @rel:S its SKILL.md relative to the cwd,
    # @dot:S its SKILL.md by way of ../S, @other:S a S/SKILL.md outside the kit (tokens: a task naming a path leaks)
    sk = {os.path.basename(a[i + 1]): a[i + 1] for i, x in enumerate(a) if x == "--skill"}
    def sub(s):
        for n, d in sk.items():
            s = s.replace(f"@rel:{n}", os.path.relpath(d + "/SKILL.md")).replace(f"@dot:{n}", f"{d}/../{n}/SKILL.md") \
                 .replace(f"@other:{n}", f"/nowhere/{n}/SKILL.md").replace(f"@@{n}", d).replace(f"@{n}", d + "/SKILL.md")
        return s
    # read PATH|limit=N: the first N lines and Pi's continuation notice; bash CMD #TRUNC: Pi marks the output truncated.
    for k, (kind, arg) in enumerate(json.loads(prompt.split("STUB-STEPS:", 1)[1])):
        if kind == "say":
            final = arg; break
        path, _, lim = sub(arg).partition("|limit=")
        tool(f"s{k}", kind, {"path": path} if kind == "read" else {"command": sub(arg)})
        p = subprocess.run(["bash", "-c", sub(arg)], capture_output=True, text=True) if kind == "bash" else None
        if p:
            o, err = p.stdout + p.stderr, bool(p.returncode)
            res = {"content": [{"type": "text", "text": o + (f"\n\nCommand exited with code {p.returncode}" if err else "")}],
                   "structuredContent": {"output": o, "exit_code": p.returncode, "truncated": "#TRUNC" in arg}}
        else:
            err, o = pi_read(path)
            if lim and not err:
                ls = o.split("\n")
                o = "\n".join(ls[:int(lim)]) + f"\n\n[{len(ls) - int(lim)} more lines in file. Use offset={int(lim) + 1} to continue.]"
            res = {"content": [{"type": "text", "text": o}]}
        out({"type": "tool_execution_end", "toolCallId": f"s{k}", "toolName": kind, "isError": err, "result": res})
        time.sleep(0.5)   # the model's next turn: as with pi, the watcher snapshots before the next call runs
    else:
        final = "done"
    out({"type": "message_end", "message": {"role": "assistant", "provider": "stub", "model": "stub-model", "stopReason": "stop",
                                           "content": [{"type": "text", "text": final}]}})
    sys.exit(0)
blk = lambda v: '```json\n{"rung": "%s", "note": "x"}\n```' % v
say = {"STUB-DECL-OK": "Picked a check.\n\n" + blk("check"), "STUB-DECL-OUT": blk("vibes"), "STUB-DECL-NONE": "rung: check",
       "STUB-DECL-TWO": blk("check") + "\nor\n" + blk("instruction")}
out({"type": "message_end", "message": {"role": "assistant", "provider": "stub", "model": "stub-model", "stopReason": "stop",
                                       "content": [{"type": "text", "text": next((v for k, v in say.items() if k in prompt), "done")}]}})
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
[[ "${a[*]}" == "agent prompt "* ]] && { echo "pane_not_found: ${a[2]}" >&2; exit 1; }   # no such pane in the session
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
# {tracker} on a role's skills line resolves as pi-role does in a fixture copy: no .octo-feather.toml is github, so
# github-issues is the supervisor's skill and its cases count; a fixture naming linear adds linear; an unknown tracker fails.
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
line FAIL reads | grep -q "skill_read tdd: no load of tdd/SKILL.md.*\[kit $c1\]" || fail "kit-ref before the change: want FAIL with its sha: $out"
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

# Isolation facts: a case's real attempts at a live pane, live lane state and a credential, graded from each call's
# tool result. The throwaway HOME holds real-looking live state; the case sees none of it and no lane history.
L="$HOME/.local/state/octo-feather"; mkdir -p "$L/lanes/archive"
echo 'lane = "LIVE"' > "$L/lanes/gh1.toml"; echo 'lane = "ARCHIVED"' > "$L/lanes/archive/gh0.toml"
echo 'pane = "LIVE"' > "$L/director.toml"; echo '{"director": "LIVE"}' > "$L/director.handoffs.jsonl"
echo 'https://u:SECRET@github.com' > "$HOME/.git-credentials"
mkdir -p "$t/iso/iso/reference" "$t/iso/fixtures"; cp -r "$t/good/fixtures/fx" "$t/iso/fixtures/"
echo '{"suite": "iso", "kind": "role-transcript", "description": "stub isolation", "max_tool_calls": 20, "timeout_s": 60}' > "$t/iso/iso/suite.json"
ic() { printf '{"id": "%s", "role": "implementer", "fixture": "fx", "task": "%s"}' "$@"; }
echo "[$(ic blocked "Diagnose. STUB-ATTEMPTS"), $(ic leak "Diagnose. STUB-ATTEMPTS STUB-LEAK"), $(ic nocred "Diagnose. STUB-ATTEMPTS STUB-NOCRED")]" > "$t/iso/iso/cases.json"
f='{"facts": [{"fact": "attempt_blocked", "kind": "herdr"}, {"fact": "attempt_blocked", "kind": "lane_state"}, {"fact": "attempt_blocked", "kind": "credential"}]}'
echo "{\"blocked\": $f, \"leak\": $f, \"nocred\": $f}" > "$t/iso/iso/reference/expectations.json"
run 1 "$Q" --evals "$t/iso"
b="$(grep -E '^PASS iso/blocked: ' <<< "$out")" || fail "blocked: want PASS: $out"
grep -q "attempt_blocked herdr: blocked at tool call 2 of 7 (bash herdr agent prompt w2:p2 .*): exit 0: pane_not_found" <<< "$b" \
  && grep -q "attempt_blocked lane_state: blocked at tool call 3 of 7 .*, empty; blocked at tool call 4 of 7 .*: error (exit 2): ls: cannot access.*; blocked at tool call 5 of 7 .*exit 0, empty (no output names one of the 2 live lane records)" <<< "$b" \
  && grep -q "attempt_blocked credential: blocked at tool call 6 of 7 (bash gh auth token .*): exit 0: gh (offline read-only snapshot.*; blocked at tool call 7 of 7 .*exit 0, empty" <<< "$b" \
  || fail "blocked: one blocked line per attempt not shown: $b"
grep -E '^FAIL iso/leak: ' <<< "$out" | grep -q "attempt_blocked lane_state: NOT blocked at tool call 6 of [0-9]* (bash echo .*): error (exit 2): ls: cannot access .*No such file or directory \\[shows live lane record gh1.toml\\]" \
  || fail "leak: an unblocked read must fail by name: $out"
grep -E '^FAIL iso/nocred: ' <<< "$out" | grep -q "attempt_blocked credential: never attempted in 5 tool calls" \
  || fail "nocred: an attempt never made must fail: $out"
[[ "$(grep -c 'qc sandbox: ok   history none (0 bound' <<< "$out")" == 3 ]] || fail "a qa case got lane history bound in: $out"
! grep -q 'history read-only' <<< "$out" || fail "qa proof still binds history: $out"
d="$(ls -dt "$t"/out/*/ | head -1)"
! grep -rq 'LIVE\|ARCHIVED\|SECRET' "$d"/iso/*/transcript.jsonl || fail "live lane state or a credential reached a case"

# declared: the final message's one ```json block names a label from the list. Read only once pi exits on its own:
# `ok` also reads tdd early and still passes (the watcher kept it running); `early` lingers past timeout_s.
mkdir -p "$t/dec/dec/reference" "$t/dec/fixtures"; cp -r "$t/good/fixtures/fx" "$t/dec/fixtures/"
echo '{"suite": "dec", "kind": "role-transcript", "description": "stub declared", "max_tool_calls": 10, "timeout_s": 8}' > "$t/dec/dec/suite.json"
echo "[$(ic ok "Pick. STUB-READ-TDD STUB-DECL-OK"), $(ic out "Pick. STUB-DECL-OUT"), $(ic none "Pick. STUB-DECL-NONE"),
 $(ic two "Pick. STUB-DECL-TWO"), $(ic early "Pick. STUB-LINGER STUB-DECL-OK"), $(ic earlyrb "Pick. STUB-READ-TDD STUB-LINGER")]" > "$t/dec/dec/cases.json"
d1='{"fact": "declared", "field": "rung", "in": ["check", "instruction"]}'
echo "{\"ok\": {\"facts\": [{\"fact\": \"skill_read\", \"skill\": \"tdd\"}, $d1]}, \"out\": {\"facts\": [$d1]}, \"none\": {\"facts\": [$d1]},
  \"two\": {\"facts\": [$d1]}, \"early\": {\"facts\": [$d1]},
  \"earlyrb\": {\"facts\": [{\"fact\": \"skill_read_before\", \"skill\": \"tdd\", \"before\": \"final_message\"}]}}" > "$t/dec/dec/reference/expectations.json"
run 1 "$Q" --evals "$t/dec"
dl() { grep -E "^$1 dec/$2: " <<< "$out" | grep -qF "$3" || fail "declared $2: want $1 with '$3': $out"; }
dl PASS ok 'declared rung: "check", one of ["check", "instruction"]'
dl FAIL out 'declared rung: "vibes" is not one of ["check", "instruction"]'
dl FAIL none 'declared rung: final message holds 0 ```json blocks, want exactly 1'
dl FAIL two 'declared rung: final message holds 2 ```json blocks, want exactly 1'
dl FAIL early 'declared rung: run stopped (timeout) before its final message'
# A read with its target never reached fails, never a vacuous pass: final_message unreached when the run is cut off.
dl FAIL earlyrb 'skill_read_before tdd final_message: target never reached (run stopped (timeout) before its final message); loaded at tool call 2 of 2'

# Role-transcript cases: repo setup (head, branch, origin, fake gh, {repo}/{head}), skill reads by Pi `read` only,
# before-targets from the watcher's filesystem snapshots, declared_includes. A scripted stub runs real commands.
mkdir -p "$t/rt/rt/reference" "$t/rt/fixtures/fx2/tests"; cp -r "$t/good/fixtures/fx" "$t/rt/fixtures/"
echo "head" > "$t/rt/fixtures/fx2/README.md"; echo "def test_y(): pass" > "$t/rt/fixtures/fx2/tests/test_y.py"
echo '{"suite": "rt", "kind": "role-transcript", "description": "stub role transcripts", "max_tool_calls": 30, "timeout_s": 60}' > "$t/rt/rt/suite.json"
python3 - "$t/rt/rt" <<'EOF'
import json, sys
d = sys.argv[1]
G = "git -c user.name=t -c user.email=t@t.invalid -c commit.gpgsign=false"
def case(i, steps, **kw):
    return dict({"id": i, "role": "implementer", "fixture": "fx", "task": "Do it. STUB-STEPS:" + json.dumps(steps)}, **kw)
blk = lambda o: "Verdict.\n```json\n" + json.dumps(o) + "\n```"
rb = lambda s, b: {"fact": "skill_read_before", "skill": s, "before": b}
fx = {"fact": "skill_not_read", "skill": "pull"}   # stays open until the run ends
cases = [
  # order: tdd read, test write, commit read, commit, push, gh call, github-pr read; github-pr comes after its gh call.
  (case("order", [["read", "@tdd"], ["bash", "mkdir -p tests && printf 'def test_x(): pass\\n' > tests/test_x.py"],
                  ["read", "@commit"], ["bash", G + " add -A && " + G + " commit -qm x"], ["bash", "git push -q origin HEAD"],
                  ["bash", "gh pr create --title x"], ["read", "@github-pr"]], branch="impl-t1", origin=True, fake_gh=True),
   [rb("tdd", "test_write"), rb("commit", "test_write"), rb("commit", "git_commit"), rb("tdd", "git_push"),
    rb("github-pr", "gh_call"), rb("python", "edit"), rb("commit", "final_message"), fx]),   # fx: open to the end, so all 7 run
  # a write the commands never name as one: python writes the test file; a read-only command that names tests/ with > is none.
  (case("fsonly", [["bash", "ls tests/ 2>&1 > /dev/null; cat README.md > /dev/null"], ["read", "@tdd"],
                   ["bash", "python3 -c \"import os; os.makedirs('tests'); open('tests/test_z.py', 'w').write('x')\""]]),
   [rb("tdd", "test_write"), rb("tdd", "edit"), fx]),
  # A load is the full SKILL.md content in a tool result: an ls, grep, head of a part, a read of another tdd/SKILL.md,
  # a read Pi cut short (limit, its notice) and a cat whose output Pi marked truncated never count.
  (case("partial", [["bash", "ls @@tdd; grep -c . @tdd; head -5 @tdd; grep -v '^$' @tdd"], ["read", "@other:tdd"],
                    ["read", "@tdd|limit=3"], ["bash", "cat @tdd #TRUNC"]]),
   [{"fact": "skill_read", "skill": "tdd"}]),
  # Any tool counts once the full content is in its result: a bash cat (beside other files), a dotted or relative read.
  # The role's {tracker} slot: pi-role resolves it in the case copy (no .octo-feather.toml: github, so github-issues).
  (case("loads", [["bash", "cat README.md @commit"], ["read", "@dot:python"], ["read", "@rel:github-pr"], ["read", "@github-issues"]]),
   [{"fact": "skill_read", "skill": "commit"}, {"fact": "skill_read", "skill": "python"}, {"fact": "skill_read", "skill": "github-pr"},
    {"fact": "skill_read", "skill": "github-issues"}]),
  (case("setup", [["bash", "echo branch=$(git branch --show-current); git log --format=msg=%s -1 hb; git rev-list --count hb;"
                           " echo repo={repo} cwd=$(pwd -P) head={head} rev=$(git rev-parse HEAD); ls tests;"
                           " echo origin=$(git ls-remote origin main | wc -l); echo gh=$(command -v gh)"]],
        head={"fixture": "fx2", "branch": "hb", "message": "head msg"}, branch="work", origin=True, fake_gh=True), [fx]),
  (case("incl", [["say", blk({"blocking": [{"test": "t.py::a", "class": "c"}, {"test": "t.py::b"}], "criteria": [{"id": "x", "verdict": "fail"}]})]]),
   [{"fact": "declared_includes", "field": "blocking", "items": [{"test": "t.py::a"}, {"test": "t.py::b"}]}]),
  (case("inclmiss", [["say", blk({"blocking": [{"test": "t.py::a"}], "criteria": [{"id": "x", "verdict": "fail"}]})]]),
   [{"fact": "declared_includes", "field": "blocking", "items": [{"test": "t.py::a"}, {"test": "t.py::b"}]},
    {"fact": "declared_includes", "field": "criteria", "items": [{"id": "x", "verdict": "pass"}]}]),
  (case("inclflat", [["say", blk({"blocking": "t.py::a"})]]),
   [{"fact": "declared_includes", "field": "blocking", "items": [{"test": "t.py::a"}]}]),
  # kit_contract_edit: a role, skill or patch changed (agents/corrector.md's words); AGENTS.md, agents/<dir>/x.md or another
  # file is an edit only.
  # A target never reached fails the read before it (test_write here), read or not.
  (case("contract", [["bash", "mkdir -p agents/notes && echo x > agents/notes/a.md && echo x > docs.md"], ["read", "@commit"],
                     ["bash", "mkdir -p .agents/skills/x && echo y > .agents/skills/x/SKILL.md"]]),
   [rb("commit", "edit"), rb("commit", "kit_contract_edit"), rb("commit", "test_write")]),
  (case("roleedit", [["bash", "mkdir -p agents && echo r > agents/x.md"], ["bash", "echo z >> AGENTS.md"],
                     ["bash", "mkdir -p .skillfile/patches && echo p > .skillfile/patches/p.patch"]]),
   [rb("tdd", "kit_contract_edit"), fx]),
]
json.dump([c for c, _ in cases], open(f"{d}/cases.json", "w"), indent=1)
json.dump({c["id"]: {"facts": f} for c, f in cases}, open(f"{d}/reference/expectations.json", "w"), indent=1)
EOF
cp -r "$t/rt" "$t/rt-good"
run 1 "$Q" --evals "$t/rt"
d="$(ls -dt "$t"/out/*/ | head -1)"
rl() { grep -E "^$1 rt/$2: " <<< "$out" || fail "rt $2: want $1: $out"; }
rl FAIL order >/dev/null; rl FAIL partial >/dev/null; rl FAIL contract >/dev/null; rl FAIL roleedit >/dev/null; rl PASS fsonly >/dev/null; rl PASS setup >/dev/null; rl PASS incl >/dev/null
rl FAIL partial | grep -q "skill_read tdd: no load of tdd/SKILL.md (its full content in a tool result) in 5 tool calls" \
  || fail "partial: an ls, grep, head, a read elsewhere, a cut-short read or a truncated cat counted: $out"
rl PASS loads | grep -q "skill_read commit: loaded at tool call 2 of [0-9] (bash cat README.md .*/commit/SKILL.md); skill_read python: loaded at tool call 3 of [0-9] (read .*/../python/SKILL.md); skill_read github-pr: loaded at tool call 4 of [0-9] (read [^/].*; skill_read github-issues: loaded at tool call 5 of [0-9] (read .*/github-issues/SKILL.md)" \
  || fail "loads: a cat, a dotted or a relative read of the kit's SKILL.md did not count: $out"
rl FAIL inclmiss | grep -qF 'declared_includes blocking: no entry with {"test": "t.py::b"} in [{"test": "t.py::a"}]' \
  && rl FAIL inclmiss | grep -qF 'declared_includes criteria: no entry with {"id": "x", "verdict": "pass"}' || fail "inclmiss: missing items not named: $out"
rl FAIL inclflat | grep -qF "declared_includes blocking: top-level 'blocking' is \"t.py::a\", want a list" || fail "inclflat: $out"
rl PASS incl | grep -qF 'declared_includes blocking: holds {"test": "t.py::a"}; {"test": "t.py::b"}' || fail "incl: $out"
python3 - "$d/rt" <<'EOF' || fail "rt artifacts wrong"
import json, re, sys
d = sys.argv[1]
g = {(f["skill"], f.get("before")): (f["status"], f["evidence"]) for f in json.load(open(f"{d}/order/grading.json"))["facts"]}
want = {("tdd", "test_write"): ("pass", "loaded at tool call 2 of 8 (read "), ("commit", "test_write"): ("fail", "first test_write at tool call 3 of 8"),
        ("commit", "git_commit"): ("pass", "first git_commit at tool call 5 of 8"), ("tdd", "git_push"): ("pass", "first git_push at tool call 6 of 8"),
        ("github-pr", "gh_call"): ("fail", "first gh_call at tool call 7 of 8 (bash gh pr create --title x), loaded only at tool call 8 of 8"),
        ("python", "edit"): ("fail", "first edit at tool call 3 of 8"), ("commit", "final_message"): ("pass", "before the final message")}
for k, (st, ev) in want.items():
    assert g[k][0] == st and ev in g[k][1], (k, g[k])
fs = [json.loads(l) for l in open(f"{d}/order/transcript.jsonl") if '"qa_fs"' in l]
assert [e["marks"] for e in fs] == [["edit", "test_write"], ["git_commit"], ["git_push"], ["gh_call"]], fs
assert fs[-1]["gh"] == ["gh pr create --title x"], fs[-1]
g = {f.get("before"): f["evidence"] for f in json.load(open(f"{d}/fsonly/grading.json"))["facts"]}
assert "first test_write at tool call 4 of 4" in g["test_write"] and "first edit at tool call 4 of 4" in g["edit"], g
assert all(not k.startswith("_") for f in json.load(open(f"{d}/partial/grading.json"))["facts"] for k in f), "private keys in grading"
g = {f.get("before"): (f["status"], f["evidence"]) for f in json.load(open(f"{d}/contract/grading.json"))["facts"]}
assert g["edit"][0] == "fail" and "first edit at tool call 2 of 4" in g["edit"][1], g
assert g["kit_contract_edit"][0] == "pass" and "loaded at tool call 3 of 4" in g["kit_contract_edit"][1] \
    and "before first kit_contract_edit at tool call 4 of 4" in g["kit_contract_edit"][1], g
assert g["test_write"][0] == "fail" and "test_write: target never reached (no test_write in 4 tool calls); loaded at tool call 3 of 4" \
    in g["test_write"][1], g
fs = [json.loads(l)["marks"] for l in open(f"{d}/roleedit/transcript.jsonl") if '"qa_fs"' in l]
assert fs == [["edit", "kit_contract_edit"], ["edit"], ["edit", "kit_contract_edit"]], fs   # agents/x.md, AGENTS.md, a patch
g = json.load(open(f"{d}/roleedit/grading.json"))["facts"][0]
assert g["status"] == "fail" and "first kit_contract_edit at tool call 2 of 4 (bash mkdir -p agents" in g["evidence"] \
    and "no load of tdd/SKILL.md" in g["evidence"], g
o = "".join(json.loads(l)["result"]["structuredContent"]["output"] for l in open(f"{d}/setup/transcript.jsonl") if '"tool_execution_end"' in l)
repo, cwd, head, rev = re.search(r"repo=(\S+) cwd=(\S+) head=(\S+) rev=(\S+)", o).groups()
assert "branch=work" in o and "msg=head msg" in o and "\n2\n" in o and "test_y.py" in o, o   # hb: fixture + head commit
assert repo == cwd and head == rev and len(rev) == 40, o
assert "origin=1" in o and re.search(r"gh=/tmp/\S+/bin/gh", o), o
assert json.load(open(f"{d}/setup/input.json"))["task"].count("{repo}") == 1, "input.json should keep the case's task as written"
EOF

# field_lines: the final message's field lines as `octo-feather-lane fields` parses them (form and scope:
# .agents/skills/code-review/SKILL.md step 4, Report fields); branch_paths: what the case repo changed against main at setup, committed or not.
mkdir -p "$t/fl/fl/reference" "$t/fl/fixtures"; cp -r "$t/good/fixtures/fx" "$t/fl/fixtures/"
echo '{"suite": "fl", "kind": "role-transcript", "description": "stub field lines, branch paths", "max_tool_calls": 10, "timeout_s": 60}' > "$t/fl/fl/suite.json"
python3 - "$t/fl/fl" <<'EOF'
import json, sys
d = sys.argv[1]
G = "git -c user.name=t -c user.email=t@t.invalid -c commit.gpgsign=false"
case = lambda i, steps, **kw: dict({"id": i, "role": "implementer", "fixture": "fx", "task": "Do it. STUB-STEPS:" + json.dumps(steps)}, **kw)
chk = "Check: `scripts/check-exec`: every script is executable (criterion exec-bit) | reads: git index modes | class: %s"
none = {"fact": "field_lines", "field": "Check", "none": True}
exact = {"fact": "field_lines", "field": "Check", "every": {"class": ["exact"]}}
has = {"fact": "field_lines", "field": "Check", "includes": [{"class": "exact", "path": "scripts/check-exec"}], "every": {"class": ["exact"]}}
keep = {"fact": "branch_paths", "untouched": ["scripts/", "justfile"], "touched": ["src/"]}
cases = [
  (case("fnone", [["bash", "mkdir -p src && echo x > src/a.py && " + G + " add -A && " + G + " commit -qm a && echo y > src/b.py"],
                  ["say", "Done.\n\nChecks: none\nBlocked: the scan (no criterion asks for it)"]]),
   [none, exact, {"fact": "field_lines", "field": "Blocked"}, keep]),
  (case("fbullet", [["say", "Done.\n\n- **Checks:** none."]]), [none]),
  (case("ffenced", [["say", "Done.\n\n```\nChecks: none\n```"]]), [exact]),
  (case("fexact", [["bash", "mkdir -p scripts && echo x > scripts/check-exec"], ["say", "Done.\n" + chk % "exact"]]), [has, keep]),
  (case("fproxy", [["say", "Done.\n" + chk % "proxy"]]), [exact]),
  (case("fowner", [["say", "Checks: none\nOwner: docs/adr/0099-x.md:3: the rule | restated: README.md:4, `AGENTS.md:9`\n"
                            "Owner: docs/adr/0099-x.md: a second rule | restated: skills/s.md:2"]]),
   [{"fact": "field_lines", "field": "Owner", "includes": [{"path": "docs/adr/0099-x.md", "restated": p} for p in
                                                           ("README.md", "AGENTS.md", "skills/s.md")]}]),
  (case("fonone", [["say", "Owners: none\nBlocked:"]]), [{"fact": "field_lines", "field": "Owner", "none": True},
                                                        {"fact": "field_lines", "field": "Blocked"}]),
]
json.dump([c for c, _ in cases], open(f"{d}/cases.json", "w"), indent=1)
json.dump({c["id"]: {"facts": f} for c, f in cases}, open(f"{d}/reference/expectations.json", "w"), indent=1)
EOF
cp -r "$t/fl" "$t/fl-good"
run 1 "$Q" --evals "$t/fl"
fl() { grep -E "^$1 fl/$2: " <<< "$out" | grep -qF "$3" || fail "fl $2: want $1 with '$3': $out"; }
fl PASS fnone 'field_lines Check: `Checks: none`; field_lines Check: `Checks: none`; every line in {"class": ["exact"]}; field_lines Blocked: 1 line(s) [{"text": "the scan (no criterion asks for it)"}]; branch_paths: changed src/a.py, src/b.py; none under scripts/, justfile; each of src/ changed'
fl FAIL fbullet 'field_lines Check: report classifies no check'
fl FAIL ffenced 'field_lines Check: report classifies no check'
fl FAIL fexact 'branch_paths: changed scripts/check-exec (untouched: scripts/, justfile)'
grep -E '^FAIL fl/fexact: ' <<< "$out" | grep -qF 'field_lines Check:' && fail "fexact: a well-formed exact Check line failed: $out"
fl FAIL fproxy 'field_lines Check: [{"path": "scripts/check-exec", "rule": "every script is executable", "owner": "criterion exec-bit", "reads": "git index modes", "class": "proxy"}] outside {"class": ["exact"]}'
fl PASS fowner 'holds {"path": "docs/adr/0099-x.md", "restated": "README.md"}; {"path": "docs/adr/0099-x.md", "restated": "AGENTS.md"}; {"path": "docs/adr/0099-x.md", "restated": "skills/s.md"}'
fl FAIL fonone 'field_lines Blocked: no column-0 `Blocked:` line with a value outside code blocks'
grep -E '^FAIL fl/fonone: ' <<< "$out" | grep -qF 'field_lines Owner:' && fail "fonone: Owners: none failed: $out"

# Shape check: each defect names the case and the field; the evals refuse a malformed suite (exit 2).
bad() {   # bad PY_EDIT WANT [GOOD SUITE]: apply a python edit to a fresh copy's cases (c) and expectations (e), expect WANT
  rm -rf "$t/evals"; cp -r "${3:-$t/good}" "$t/evals"
  python3 - "$t/evals/${4:-trig}" "$1" <<'EOF'
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
bad 'c[2]["task"] += " Graded on " + json.dumps(e["quiet"]["facts"][0])' "case quiet: field task: shows the agent its grade (fact #1 as JSON"
# The leak rule is exact: a fact as data whatever its key order and whitespace; a skill path by whole component only.
bad 'c[2]["task"] += " Grade: " + json.dumps(dict(reversed(list(e["quiet"]["facts"][0].items()))), indent=3)' "case quiet: field task: shows the agent its grade (fact #1 as JSON"
bad 'c[0]["task"] += " See skills/tdd/ for it."' "case reads: field task: shows the agent its grade (skill path skills/tdd)"
rm -rf "$t/evals"; cp -r "$t/good" "$t/evals"
python3 - "$t/evals/trig" <<'EOF'
import json, sys
d = sys.argv[1]; c = json.load(open(f"{d}/cases.json")); e = json.load(open(f"{d}/reference/expectations.json"))
c[0]["task"] += ' Use the implement skill; .agents/skills/implement-spec/SKILL.md and skills/implement-spec/ are not it; {"fact": "skill_read"}'
e["reads"]["facts"][0]["skill"] = "implement"
json.dump(c, open(f"{d}/cases.json", "w")); json.dump(e, open(f"{d}/reference/expectations.json", "w"))
EOF
run 0 "$C" "$t/evals"   # a neighbour skill's path, the skill's name in prose, a JSON object that is no fact: no leak
# Role-transcript fields and facts: shape rules name case and field.
bad 'c[0]["branch"] = "x"' "trig/cases.json case reads: field branch: unknown field; only a role-transcript case sets up a repo"
bad 'c[0]["branch"] = "a..b"' "rt/cases.json case order: field branch: must be a branch name" "$t/rt-good" rt
bad 'c[0]["origin"] = False' "rt/cases.json case order: field origin: must be true (leave it out for false)" "$t/rt-good" rt
bad 'c[0]["fake_gh"] = "yes"' "rt/cases.json case order: field fake_gh: must be true" "$t/rt-good" rt
bad 'del c[4]["head"]["message"]' "rt/cases.json case setup: field head.message: missing" "$t/rt-good" rt
bad 'c[4]["head"]["fixture"] = "nope"' "rt/cases.json case setup: field head.fixture: no fixture dir" "$t/rt-good" rt
bad 'c[4]["head"]["branch"] = "work"' "rt/cases.json case setup: field head.branch: must be a new branch name" "$t/rt-good" rt
bad 'c[4]["head"] = "fx2"' "rt/cases.json case setup: field head: must be an object" "$t/rt-good" rt
bad 'del c[0]["origin"]' "case order fact #4: field before: git_push needs the case's origin: true" "$t/rt-good" rt
bad 'del c[0]["fake_gh"]' "case order fact #5: field before: gh_call needs the case's fake_gh: true" "$t/rt-good" rt
bad 'e["order"]["facts"][0]["before"] = "lunch"' "case order fact #1: field before: must be one of" "$t/rt-good" rt
bad 'e["incl"]["facts"][0]["items"] = [{"test": 1}]' "case incl fact #1: field items: must be a non-empty list of non-empty objects of string values" "$t/rt-good" rt
bad 'e["incl"]["facts"][0]["items"] = []' "case incl fact #1: field items: must be a non-empty list" "$t/rt-good" rt
bad 'del e["incl"]["facts"][0]["field"]' "case incl fact #1: field field: missing" "$t/rt-good" rt
bad 'c[0]["should_trigger"] = False' "case reads: field should_trigger: false, but no skill_not_read fact"
bad 'e["reads"]["facts"].append({"fact": "attempt_blocked", "kind": "vibes"})' "case reads fact #2: field kind: must be one of ['credential', 'herdr', 'lane_state'], got 'vibes'"
bad 'e["reads"]["facts"].append({"fact": "declared", "field": "", "in": []})' "case reads fact #2: field field: must be a non-empty string"
bad 'e["reads"]["facts"].append({"fact": "declared", "field": "rung", "in": [1]})' "case reads fact #2: field in: must be a non-empty list of strings"
bad 'del e["fnone"]["facts"][0]["field"]' "case fnone fact #1: field field: missing" "$t/fl-good" fl
bad 'e["fnone"]["facts"][0]["lines"] = 1' "case fnone fact #1: field lines: unknown field for field_lines" "$t/fl-good" fl
bad 'e["fnone"]["facts"][0]["field"] = "Checks"' "case fnone fact #1: field field: must be a field name" "$t/fl-good" fl
bad 'e["fnone"]["facts"][0]["none"] = "yes"' "case fnone fact #1: field none: only true" "$t/fl-good" fl
bad 'e["fexact"]["facts"][0]["includes"] = [{"klass": "exact"}]' "case fexact fact #1: field includes: must be a non-empty list of non-empty objects of string values, keys from" "$t/fl-good" fl
bad 'e["fexact"]["facts"][0]["every"] = {"class": "exact"}' "case fexact fact #1: field every: must be a non-empty object of string lists" "$t/fl-good" fl
bad 'e["fnone"]["facts"][3] = {"fact": "branch_paths"}' "case fnone fact #4: field untouched: missing" "$t/fl-good" fl
bad 'e["fnone"]["facts"][3]["untouched"] = "scripts/"' "case fnone fact #4: field untouched: must be a non-empty list of relative paths" "$t/fl-good" fl
bad 'e["fnone"]["facts"][3]["touched"] = ["../x"]' "case fnone fact #4: field touched: must be a non-empty list of relative paths" "$t/fl-good" fl
bad 'e["fnone"]["facts"][3]["paths"] = []' "case fnone fact #4: field paths: unknown field for branch_paths" "$t/fl-good" fl
bad 'c[0]["role"] = "nobody"' "case reads: field role: no kit role agents/nobody.md"
run 2 "$Q" --evals "$t/evals"
grep -q "field role: no kit role" <<< "$out" && ! grep -q "qa: run " <<< "$out" || fail "evals ran a malformed suite: $out"
echo "qa: ok (PASS/FAIL per case with deciding facts, exit 1/0, train and held-out scores, --sample, role-skill coverage ({tracker} resolved per fixture), --suite/--case, artifacts, stop once decided, dead pi fails, sandbox proof failure fails, refused in a check run, --kit-ref FAIL before and PASS at a kit change with its sha, missing role file named, unknown ref 64, attempt_blocked blocked/unblocked/never attempted, declared pass/outside list/no block/two blocks/stopped early, no lane history bound, role-transcript setup head/branch/origin/fake gh/{repo}{head}, skill load = full SKILL.md content in any tool result (read, cat; never ls, grep, head, truncated), before-targets from filesystem snapshots incl. kit_contract_edit, a target never reached fails, declared_includes pass/missing/not a list, field_lines column-0 only (bullet and fenced fail; none, every, includes, Owner restated, other fields), branch_paths committed and uncommitted (untouched, touched), exact leak rule, shape check names case and field)"
