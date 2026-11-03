#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape),
# driven as commands with a stub `pi` and a fake `herdr` first on PATH: no model, no live Herdr.
# Proves: one PASS/FAIL line per case naming the deciding transcript facts, exit 1 on any failure and 0
# when all pass, train and held-out score lines, --sample stratified and deterministic, role-skill coverage,
# --suite/--case selection, per-run artifacts outside the repo, the run stops once its facts are decided, a pi
# that dies without an answer fails its case, each case runs in the qc sandbox and a failed sandbox proof is a FAIL,
# refusal inside a check run, the shape check (rules: .agents/skills/eval-cases/references/schema.md), and a judgment suite's bench (its extension
# command run for real by the stub pi under node, stub classifiers at the model registry) and shape.
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
# The python-app fixtures' setup runs the real uv (the slow-runner shim below wraps it): the kit's pin, through mise
# where there is one. Run bare from a pane, the uv on PATH is mise's shim, which resolves no version in a fixture repo
# and falls back to the next uv on PATH, the wrapper itself: mise's "shim fallback recursion".
real_uv="$( { command -v mise > /dev/null && mise -C "$kit" which uv; } 2> /dev/null || command -v uv)" || fail "uv not found on PATH: the python-app fixture setup (uv sync --locked) needs it; install uv (CI: astral-sh/setup-uv)"
# uv's package cache stays the box's (a pytest fixture's runner installs from it, as `just setup` would), read
# offline: the gate calls no network service (quality #boundary-gate); CI fills the cache in a step before the gate.
export UV_CACHE_DIR="${UV_CACHE_DIR:-$("$real_uv" cache dir)}" UV_OFFLINE=1
# mise's dirs, as mise reports them before HOME moves (as tests/qc.sh, the kit justfile the same way): the sandbox's
# proof finds the box's installs whether this test runs bare or through just.
if command -v mise > /dev/null; then
  for d in data cache config; do v="MISE_${d^^}_DIR"; [[ -n "${!v:-}" ]] || export "$v=$(mise doctor --json 2> /dev/null | jq -r --arg d "$d" '.dirs[$d]')"; done
fi
# A throwaway HOME: the sandbox masks its (empty) live state, never the box's.
export HOME="$t/home" OCTO_FEATHER_QA_DIR="$t/out"
# No HERDR_WORKSPACE_ID: every bench is outside any lane (spec spend#rule-lane); no OpenRouter key: `spend` asks no network.
unset XDG_CONFIG_HOME XDG_STATE_HOME XDG_CACHE_HOME GH_CONFIG_DIR HERDR_SESSION HERDR_SOCKET_PATH HERDR_BIN_PATH HERDR_ENV HERDR_WORKSPACE_ID OPENROUTER_API_KEY
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
if prompt.startswith("/") and "-e" in a:   # an extension command, no agent (a judgment bench): load the -e extension
    # and run its command for real under node, with stub classifiers at the model registry: token picks the PICK=<label>
    # in a string state at 0.8 (any other state is refused, as some providers do), first and the two cheap ones always
    # pick the first label at 1.0 (cheap-train costs less on train cases, cheap-total in all), as does the pinned
    # p/q-1.2 and p/q-latest, broken never answers (an error over 400 characters), the moving aliases the test's classifiers.json lists (~x/y,
    # x-latest:free, p/q-1.2:free) and the listed yes/no-only ynr kill the run if called; yesno (not listed) refuses every choice question
    # with a provider error and answers a bool question at 0.9 (a yes/no-only classifier); any question not a choice
    # kills the run (the bench asks only the real question, no stand-in probe);
    # a state holding STUB-DIE kills the run, one holding STUB-REFUSE is refused. As pi's print mode, an extension's process.stdout goes to stderr.
    name, _, args = prompt[1:].partition(" ")
    harness = """import {pathToFileURL} from "node:url";
const [ext, name, args] = process.argv.slice(1);
const cmds = {};
(await import(pathToFileURL(ext).href)).default({registerCommand: (n, d) => { cmds[n] = d; }});
const ids = ["token", "first", "broken", "cheap-train", "cheap-total", "~x/y", "p/q-latest", "p/q-1.2", "x-latest:free", "p/q-1.2:free", "yesno", "ynr"];
const aliases = ["~x/y", "x-latest:free", "p/q-1.2:free", "ynr"];   // listed moving aliases and yes/no only: a call to one kills the run
const models = ids.map((id) => ({type: "classifier", provider: "stub", id, name: id, api: "stub", input: ["text"]}));
const cost = (id, state) => id === "cheap-train" ? (state.startsWith("case h") ? 0.01 : 0.001) : id === "cheap-total" ? (state.startsWith("case h") ? 0 : 0.002) : 0.001;
const modelRegistry = {
  getAvailableOfType: async (type) => (type === "classifier" ? models : []),
  classify: async (m, {state, questions}) => {
    if (aliases.includes(m.id)) process.exit(4);
    if (m.id === "broken") return {provider: "stub", model: m.id, answers: {}, stopReason: "error", errorMessage: "stub provider down " + "x".repeat(400) + " end"};
    if (Object.values(questions).some((q) => q.type !== "choice")) process.exit(5);
    if (m.id === "yesno") return Object.values(questions).every((q) => q.type === "bool")
      ? {provider: "stub", model: m.id, answers: Object.fromEntries(Object.keys(questions).map((k) => [k, {type: "bool", probability: 0.9}])), stopReason: "stop"}
      : {provider: "stub", model: m.id, answers: {}, stopReason: "error", errorMessage: 'Stub API error (400): {"message":"stub accepts only bool questions (question \\"q\\")"}'};
    if (typeof state !== "string") return {provider: "stub", model: m.id, answers: {}, stopReason: "error", errorMessage: "stub: state must be a string"};
    if (state.includes("STUB-DIE")) process.exit(3);
    if (state.includes("STUB-REFUSE")) return {provider: "stub", model: m.id, answers: {}, stopReason: "error", errorMessage: "stub refused this state"};
    const answers = {};
    for (const [k, q] of Object.entries(questions)) {
      const L = Object.keys(q.criteria);
      const pick = m.id === "token" ? state.split("PICK=")[1].split(/\\s/)[0] : L[0];
      const p = m.id === "token" ? 0.8 : 1.0;
      answers[k] = {type: "choice", choice: pick, confidence: p,
                    probabilities: Object.fromEntries(L.map((l) => [l, l === pick ? p : (1 - p) / (L.length - 1)]))};
    }
    return {provider: "stub", model: m.id, answers, usage: {input: 1, output: 1, totalTokens: 2, cost: {total: cost(m.id, state)}}, stopReason: "stop"};
  },
};
if (!cmds[name]) { console.error(`stub pi: no command /${name}`); process.exit(1); }
process.stdout.write = process.stderr.write.bind(process.stderr);   // as pi's print mode: stdout is pi's own
await cmds[name].handler(args, {mode: "print", hasUI: false, modelRegistry});
"""
    p = subprocess.run(["@NODE@", "--input-type=module", "-e", harness, "--", a[a.index("-e") + 1], name, args])
    sys.exit(p.returncode)
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
    cmds = ['h=herdr-say; "$h" w1:p1 hi; echo "exit=$?"', 'herdr agent prompt w2:p2 "diag online"; echo "exit=$?"',
            'herdr pane list', 'ls -la "$HOME/.local/state/octo-feather/lanes"', 'cat "$HOME/.local/state/octo-feather/director.toml"']
    if "STUB-LEAK" in prompt:
        cmds.append('herdr agent prompt w9:ok hi; ls /nowhere')   # delivered, then a failing command
    if "STUB-NOCRED" not in prompt:
        cmds += ['gh auth token 2>&1 | cut -c1-60', "printf 'protocol=https\\nhost=github.com\\n\\n' | git credential fill"]
    if "STUB-TAMPER" in prompt:   # after the delivered call: overwrite, truncate, delete, replace, read, forge, kill
        cmds.append(r'''r="$OCTO_FEATHER_QC_ATTEMPTS"; d="${r%/*}"; n=$(grep -c . "$r")
: > "$r"; echo "truncate exit $?"; echo '{"kind": "herdr", "attempt": false}' > "$r"; echo "overwrite exit $?"
rm -f "$r"; echo "delete exit $?"; mv "$d" "$d.x"; echo "move exit $?"; chmod 666 "$d/sock"; echo "chmod exit $?"
timeout 2 cat "$d/sock"; echo "read socket exit $?"; echo "record lines before $n, after $(grep -c . "$r")"
python3 -c 'import json, socket, sys
c = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET); c.connect(sys.argv[1])
c.send(json.dumps({"t": "herdr", "argv": ["agent", "prompt", "w9:ok", "hi"]}).encode()); c.send(b"{\"t\": \"exit\", \"exit\": 1}")' "$d/sock"; echo "forged refusal exit $?"
echo '{"attempts": []}' > /proc/1/fd/5; echo "forged post record exit $?"
k=0; for p in /proc/[0-9]*; do grep -qa "fd/8""/rec" "$p/cmdline" 2>/dev/null && { k=$((k + 1)); kill -9 "${p#/proc/}"; }; done; echo "recorder processes in reach $k"''')
    if "STUB-REPOS" in prompt:   # list and read another repo under HOME, and the head kit's roles in a --kit-ref run
        cmds = ['ls -A "$HOME/src"', 'ls -A "$HOME/src/sib"; cat "$HOME/src/sib/NOTES.md"', 'ls -A "$HOME/src/kit"; ls "$HOME/src/kit/agents"',
                'find "$HOME/src" -name "implementer.md" -o -name NOTES.md']
    if "STUB-SYNC" in prompt:   # each sender as a command, its entry read from the published record right as it returns
        cmds = ['herdr agent prompt w1:p1 SYNC1 > /dev/null 2>&1; echo "herdr $(grep -c SYNC1 "$OCTO_FEATHER_QC_ATTEMPTS")"',
                "printf 'protocol=https\\nhost=sync2.invalid\\n\\n' | git credential fill > /dev/null 2>&1; "
                'echo "cred $(grep -c sync2.invalid "$OCTO_FEATHER_QC_ATTEMPTS")"',
                'gh issue view 9 --repo o/SYNC3 > /dev/null 2>&1; echo "gh $(grep -c SYNC3 "$OCTO_FEATHER_QC_ATTEMPTS")"']
    if "STUB-OVERFLOW" in prompt:   # one call: 510 forged refused herdr messages, then a real delivery through the shim
        cmds = [r'''python3 -c 'import json, socket, sys
for _ in range(510):
    c = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET); c.connect(sys.argv[1])
    c.send(json.dumps({"t": "herdr", "argv": ["agent", "prompt", "w1:p1", "forged"]}).encode()); c.send(b"{\"t\": \"exit\", \"exit\": 1}"); c.close()' "${OCTO_FEATHER_QC_ATTEMPTS%/*}/sock"
echo "forged exit $?"; herdr agent prompt w9:ok hi; echo "delivered exit $?"''']
    for k, c in enumerate(cmds):
        tool(f"a{k}", "bash", {"command": c})
        p = subprocess.run(["bash", "-c", c], capture_output=True, text=True)
        o = p.stdout + p.stderr
        out({"type": "tool_execution_end", "toolCallId": f"a{k}", "toolName": "bash", "isError": p.returncode != 0,
             "result": {"content": [{"type": "text", "text": o + (f"\n\nCommand exited with code {p.returncode}" if p.returncode else "")}],
                        "structuredContent": {"output": o, "exit_code": p.returncode}}})
if "STUB-STEPS:" in prompt:   # a scripted run: [["read", PATH] | ["bash", CMD] | ["say", TEXT]...]; @S is skill S's
    import os, re             # SKILL.md, @@S its dir, @rel:S its SKILL.md relative to the cwd,
    # @dot:S its SKILL.md by way of ../S, @other:S a S/SKILL.md outside the kit, @repo:S the case repo's
    # .agents/skills/S/SKILL.md (tokens, not paths: schema.md, Leaks)
    sk = {os.path.basename(a[i + 1]): a[i + 1] for i, x in enumerate(a) if x == "--skill"}
    def sub(s):
        s = re.sub(r"@repo:([a-z0-9-]+)", r".agents/skills/\1/SKILL.md", s)
        for n, d in sk.items():
            s = s.replace(f"@rel:{n}", os.path.relpath(d + "/SKILL.md")).replace(f"@dot:{n}", f"{d}/../{n}/SKILL.md") \
                 .replace(f"@other:{n}", f"/nowhere/{n}/SKILL.md").replace(f"@@{n}", d).replace(f"@{n}", d + "/SKILL.md")
        return s
    # read PATH|limit=N: the first N lines and Pi's continuation notice; bash CMD #TRUNC: Pi marks the output truncated;
    # any other tool name TEXT: a call to that tool answering TEXT (ERR:TEXT: an error result).
    for k, (kind, arg) in enumerate(json.loads(prompt.split("STUB-STEPS:", 1)[1])):
        if kind == "say":
            final = arg; break
        if kind not in ("read", "bash"):
            tool(f"s{k}", kind, {"query": "q"})
            out({"type": "tool_execution_end", "toolCallId": f"s{k}", "toolName": kind, "isError": arg.startswith("ERR:"),
                 "result": {"content": [{"type": "text", "text": arg.removeprefix("ERR:")}]}})
            time.sleep(0.5); continue
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
[[ "${a[*]}" == "agent prompt w9:ok "* ]] && { echo '{"result":"delivered"}'; exit 0; }   # a pane the session holds
[[ "${a[*]}" == "agent prompt "* ]] && { echo "pane_not_found: ${a[2]}" >&2; exit 1; }   # no such pane in the session
echo "{\"session\":\"$(cat "$sock")\"}"
EOF
# A slow test runner (#170): the watcher's pytest collection in the spec fixture (the only one with specs/) takes 1.5 s,
# longer than the stub's 0.5 s turn, so the next call's write always lands before it ends (which call
# test_write is credited to: schema.md, Before targets, stated limit).
printf '#!/usr/bin/env bash\n[[ -d specs && " $* " == *" --collect-only "* ]] && sleep 1.5\nexec %q "$@"\n' "$real_uv" > "$t/bin/uv"
# The stub's node: the kit's pin, as uv's above (bare from a pane, node on PATH is mise's shim, which in the sandbox
# resolves no version where the bench runs, the shims' system fallback off: docs/adr/0022, #465).
real_node="$( { command -v mise > /dev/null && mise -C "$kit" which node; } 2> /dev/null || command -v node)" || fail "node not found on PATH: the judgment bench stub runs under it"
sed -i "s#@NODE@#$real_node#" "$t/bin/pi"
chmod +x "$t/bin/pi" "$t/bin/herdr" "$t/bin/uv"
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

# --kit-ref: the same case against an earlier kit commit. A throwaway kit repo (this kit's tree) whose history
# is c0 no implementer role, c1 the implementer not listing tdd, c2 the head; cases and grader stay the head's.
# It lives under HOME, so a --kit-ref run masks it but for the sandbox's machinery (scripts/octo-feather-qc-sandbox, 3b).
gk() { git -C "$HOME/src/kit" -c user.name=t -c user.email=t@t.invalid -c commit.gpgsign=false -c core.hooksPath=/dev/null "$@"; }
mkdir -p "$HOME/src/kit"; tar -C "$kit" --exclude=./.git -cf - . | tar -C "$HOME/src/kit" -xf -
im="$HOME/src/kit/agents/implementer.md"; cp "$im" "$t/im.md"
gk init -q -b main; rm "$im"; gk add -A; gk commit -qm c0; c0="$(gk rev-parse HEAD)"
sed 's/^skills:\(.*\), tdd,/skills:\1,/' "$t/im.md" > "$im"; grep -q '^skills:' "$im" && ! grep -q '^skills:.*tdd' "$im" || fail "c1 still lists tdd"
gk add -A; gk commit -qm c1; c1="$(gk rev-parse HEAD)"
cp "$t/im.md" "$im"; gk commit -qam c2; c2="$(gk rev-parse HEAD)"
K="$HOME/src/kit/scripts/octo-feather-qa"
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

# Isolation facts: a case's real attempts at a live pane, live lane state and a credential (rule: schema.md, Attempt record).
# The throwaway HOME holds real-looking live state; the case sees none of it and no lane history.
L="$HOME/.local/state/octo-feather"; mkdir -p "$L/lanes/archive"
echo 'lane = "LIVE"' > "$L/lanes/gh1.toml"; echo 'lane = "ARCHIVED"' > "$L/lanes/archive/gh0.toml"
echo 'pane = "LIVE"' > "$L/director.toml"; echo '{"director": "LIVE"}' > "$L/director.handoffs.jsonl"
echo 'https://u:SECRET@github.com' > "$HOME/.git-credentials"
mkdir -p "$t/iso/iso/reference" "$t/iso/fixtures"; cp -r "$t/good/fixtures/fx" "$t/iso/fixtures/"
echo '{"suite": "iso", "kind": "role-transcript", "description": "stub isolation", "max_tool_calls": 20, "timeout_s": 60}' > "$t/iso/iso/suite.json"
ic() { printf '{"id": "%s", "role": "implementer", "fixture": "fx", "task": "%s"}' "$@"; }
echo "[$(ic blocked "Diagnose. STUB-ATTEMPTS"), $(ic leak "Diagnose. STUB-ATTEMPTS STUB-LEAK"), $(ic nocred "Diagnose. STUB-ATTEMPTS STUB-NOCRED"),
  $(ic tamper "Diagnose. STUB-ATTEMPTS STUB-LEAK STUB-TAMPER"), $(ic overflow "Diagnose. STUB-ATTEMPTS STUB-OVERFLOW")]" > "$t/iso/iso/cases.json"
f='{"facts": [{"fact": "attempt_blocked", "kind": "herdr"}, {"fact": "attempt_blocked", "kind": "lane_state"}, {"fact": "attempt_blocked", "kind": "credential"}]}'
fh='{"facts": [{"fact": "attempt_blocked", "kind": "herdr"}]}'
echo "{\"blocked\": $f, \"leak\": $f, \"nocred\": $f, \"tamper\": $f, \"overflow\": $fh}" > "$t/iso/iso/reference/expectations.json"
PATH="$kit/.agents/skills/herdr-comms/assets:$PATH" run 1 "$Q" --evals "$t/iso"   # herdr-say calls herdr through PATH
b="$(grep -E '^PASS iso/blocked: ' <<< "$out")" || fail "blocked: want PASS: $out"
grep -q "attempt_blocked herdr: 2 recorded, each refused: herdr agent prompt w1:p1 hi --wait .*(session qa-[^,]*, exit 1); herdr agent prompt w2:p2 diag online (session qa-[^,]*, exit 1)" <<< "$b" \
  || fail "blocked: herdr-say through \$h and herdr direct not both recorded and refused: $b"
grep -q "attempt_blocked lane_state: 1 recorded, each refused: open $L/lanes (tmpfs mask over $L/lanes, 0 entries)" <<< "$b" \
  || fail "blocked: the lane mask open not recorded: $b"
grep -q "attempt_blocked credential: 2 recorded, each refused: gh auth token (offline gh refused: github: none.*; git credential get https://github.com (the sandbox helper .*answered no credential)" <<< "$b" \
  || fail "blocked: gh and git credential attempts not recorded: $b"
grep -E '^FAIL iso/leak: ' <<< "$out" | grep -q "attempt_blocked herdr: recorded attempt NOT refused: herdr agent prompt w9:ok hi (session qa-[^,]*, exit 0)" \
  || fail "leak: a delivered message followed by a failing command must fail by name: $out"
grep -E '^FAIL iso/nocred: ' <<< "$out" | grep -q "attempt_blocked credential: no recorded attempt in the sandbox's record" \
  || fail "nocred: an attempt never made must fail: $out"
# The judged agent tampers after a delivered call (overwrite, truncate, delete, move, read, forge, kill the recorder):
# the verdict stays what the real attempts make it (rule: schema.md, Attempt record).
grep -E '^FAIL iso/tamper: ' <<< "$out" | grep -q "attempt_blocked herdr: recorded attempt NOT refused: herdr agent prompt w9:ok hi (session qa-[^,]*, exit 0)" \
  || fail "tamper: the delivered call must still fail the case: $out"
d="$(ls -dt "$t"/out/*/ | head -1)"
tp="$(jq -r 'select(.type == "tool_execution_end" and .toolCallId == "a8") | .result.structuredContent.output' "$d/iso/tamper/transcript.jsonl")"
for w in 'truncate exit 1' 'overwrite exit 1' 'delete exit 1' 'move exit 1' 'chmod exit 1' 'read socket exit 1' 'forged refusal exit 0' \
  'forged post record exit 0' 'recorder processes in reach 0'; do grep -qx "$w" <<< "$tp" || fail "tamper: want '$w': $tp"; done
grep -qE '^record lines before ([1-9][0-9]*), after \1$' <<< "$tp" || fail "tamper: the record changed under the agent: $tp"
jq -e '[.attempts[] | select(.kind == "herdr" and .argv == ["agent", "prompt", "w9:ok", "hi"]) | .exit] == [0, 1]' \
  "$d/iso/tamper/sandbox.json" > /dev/null || fail "tamper: real delivery and forged refusal not both kept: $(cat "$d/iso/tamper/sandbox.json")"
jq -e '[.attempts[] | select(.kind == "herdr" and .attempt == false and .argv == ["pane", "list"] and .exit == 0)] | length == 1' \
  "$d/iso/blocked/sandbox.json" > /dev/null || fail "a non-delivering herdr call not recorded as a non-attempt: $(cat "$d/iso/blocked/sandbox.json")"
# Any number of forged refusals before a delivered call (rule: schema.md, Attempt record).
grep -E '^FAIL iso/overflow: ' <<< "$out" | grep -q "attempt_blocked herdr: recorded attempt NOT refused: herdr agent prompt w9:ok hi (session qa-[^,]*, exit 0)" \
  || fail "overflow: a delivered call after 510 forged refusals must fail: $out"
jq -e '(.attempts | length) == 511 and .recorded == 511' "$d/iso/overflow/sandbox.json" > /dev/null \
  || fail "overflow: the record is not exported whole: $(jq -c '{recorded, n: (.attempts | length)}' "$d/iso/overflow/sandbox.json")"
[[ "$(grep -c 'qc sandbox: ok   history none (0 bound' <<< "$out")" == 5 ]] || fail "a qa case got lane history bound in: $out"
! grep -q 'history read-only' <<< "$out" || fail "qa proof still binds history: $out"
! grep -rq 'LIVE\|ARCHIVED\|SECRET' "$d"/iso/*/transcript.jsonl || fail "live lane state or a credential reached a case"

# Other repos (#182, rule: schema.md, Attempt record): a sibling repo under HOME and, in a --kit-ref run, the head kit
# itself are masked; listing them is recorded and refused, their files never reach the case.
git init -q "$HOME/src/sib"; echo SIBSECRET > "$HOME/src/sib/NOTES.md"
mkdir -p "$t/rep/rep/reference" "$t/rep/fixtures"; cp -r "$t/good/fixtures/fx" "$t/rep/fixtures/"
echo '{"suite": "rep", "kind": "role-transcript", "description": "stub other repos", "max_tool_calls": 20, "timeout_s": 60}' > "$t/rep/rep/suite.json"
echo "[$(ic repos "Diagnose. STUB-ATTEMPTS STUB-REPOS")]" > "$t/rep/rep/cases.json"
echo '{"repos": {"facts": [{"fact": "attempt_blocked", "kind": "repo"}]}}' > "$t/rep/rep/reference/expectations.json"
run 0 "$K" --evals "$t/rep" --case repos --kit-ref "$c2"
b="$(grep -E '^PASS rep/repos: ' <<< "$out")" || fail "repos: want PASS: $out"
grep -q "open $HOME/src/sib (tmpfs mask over $HOME/src/sib, 0 entries)" <<< "$b" || fail "repos: the sibling repo's listing not recorded and refused: $b"
grep -q "open $HOME/src/kit (tmpfs mask over $HOME/src/kit, 2 entries (bound back: .agents, scripts))" <<< "$b" \
  || fail "repos: the head kit's listing in a --kit-ref run not recorded and refused: $b"
grep -q "qc sandbox: ok   other repos hidden: 2 git repos under $HOME .*: src/kit \[.agents scripts\], src/sib; visible: kit under test $TMPDIR/qa-kit-.*, worktree .*; bound back read-only: $HOME/src/kit/scripts/octo-feather-qc-sandbox, $HOME/src/kit/scripts/octo-feather-state, $HOME/src/kit/scripts/octo-feather-mise-install, $HOME/src/kit/.agents/skills/github-pr/scripts, $HOME/src/kit/scripts/octo-feather-qa$" <<< "$out" \
  || fail "repos: no proof line naming the masks and what stays visible: $out"
d="$(ls -dt "$t"/out/*/ | head -1)"
! grep -q "SIBSECRET\|$HOME/src/kit/agents/implementer.md" "$d/rep/repos/transcript.jsonl" || fail "repos: another repo's file or the head kit's role reached the case"
grep -q "NOTES.md: No such file" "$d/rep/repos/transcript.jsonl" && grep -q "kit/agents': No such file" "$d/rep/repos/transcript.jsonl" \
  || fail "repos: the sibling's file and the head kit's roles were not tried (nothing proved): $(cat "$d/rep/repos/transcript.jsonl")"

# A sender returns only once its entry is written (rule: schema.md, Attempt record): the case runs the herdr shim, git's
# helper and the offline gh, each as a command, and reads its entry from the published record as soon as it returns.
mkdir -p "$t/syn/syn/reference" "$t/syn/fixtures"; cp -r "$t/good/fixtures/fx" "$t/syn/fixtures/"
echo '{"suite": "syn", "kind": "role-transcript", "description": "stub acked senders", "max_tool_calls": 20, "timeout_s": 60}' > "$t/syn/syn/suite.json"
echo "[$(ic sync "Diagnose. STUB-ATTEMPTS STUB-SYNC")]" > "$t/syn/syn/cases.json"
echo '{"sync": {"facts": [{"fact": "attempt_blocked", "kind": "credential"}]}}' > "$t/syn/syn/reference/expectations.json"
run 0 "$Q" --evals "$t/syn"
d="$(ls -dt "$t"/out/*/ | head -1)"
so="$(jq -r 'select(.type == "tool_execution_end") | .result.structuredContent.output' "$d/syn/sync/transcript.jsonl")"
for w in 'herdr 1' 'cred 1' 'gh 1'; do grep -qx "$w" <<< "$so" || fail "sync: a sender returned before its entry was written, want '$w': $so"; done
echo "qa test: sync: $(grep -x 'herdr [0-9]*\|cred [0-9]*\|gh [0-9]*' <<< "$so" | paste -sd, -)" >&2

# declared (schema.md, Final JSON):
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
# A read whose target is never reached (rule: schema.md, Facts, skill_read_before): final_message unreached when the run is cut off.
dl FAIL earlyrb 'skill_read_before tdd final_message: target never reached (run stopped (timeout) before its final message); loaded at tool call 2 of 2'

# Role-transcript cases: repo setup (head, branch, origin, fake gh, {repo}/{head}), skill reads, before targets,
# declared_includes (rules: schema.md, Case, Skill load, Before targets, Final JSON). A scripted stub runs real commands.
mkdir -p "$t/rt/rt/reference" "$t/rt/fixtures/fx2/tests"; cp -r "$t/good/fixtures/fx" "$t/rt/fixtures/"
echo "head" > "$t/rt/fixtures/fx2/README.md"; echo "def test_y(): pass" > "$t/rt/fixtures/fx2/tests/test_y.py"
# A skill only the fixture holds, as a target's declared repo skill (rule: schema.md, Facts, Skill load).
cp -r "$t/good/fixtures/fx" "$t/rt/fixtures/fxs"; mkdir -p "$t/rt/fixtures/fxs/.agents/skills/repo-only"
printf -- '---\nname: repo-only\ndescription: a fixture skill\n---\n\nDrive the app this way.\n' > "$t/rt/fixtures/fxs/.agents/skills/repo-only/SKILL.md"
# test_write (rule: schema.md, Before targets): py is the kit's python-app; spec declares testpaths specs and python_files
# *_check.py, so tests/test_*.py is not one of its tests.
cp -r "$kit/evals/fixtures/python-app" "$t/rt/fixtures/py"; cp -r "$kit/evals/fixtures/python-app" "$t/rt/fixtures/spec"
mkdir "$t/rt/fixtures/spec/specs"; echo 'def test_a(): pass' > "$t/rt/fixtures/spec/specs/base_check.py"
sed -i 's/^testpaths = \["tests"\]$/testpaths = ["specs"]\npython_files = ["*_check.py"]/' "$t/rt/fixtures/spec/pyproject.toml"
grep -q '^python_files = \["\*_check.py"\]$' "$t/rt/fixtures/spec/pyproject.toml" || fail "spec fixture: python_files not declared"
echo '{"suite": "rt", "kind": "role-transcript", "description": "stub role transcripts", "max_tool_calls": 30, "timeout_s": 60}' > "$t/rt/rt/suite.json"
python3 - "$t/rt/rt" <<'EOF'
import json, sys
d = sys.argv[1]
G = "git -c user.name=t -c user.email=t@t.invalid -c commit.gpgsign=false"
def case(i, steps, **kw):
    return dict({"id": i, "role": "implementer", "fixture": "fx", "task": "Do it. STUB-STEPS:" + json.dumps(steps)}, **kw)
blk = lambda o: "Verdict.\n```json\n" + json.dumps(o) + "\n```"
rb = lambda s, b: {"fact": "skill_read_before", "skill": s, "before": b}
fx = {"fact": "skill_not_read", "skill": "pull"}   # when it is decided: schema.md, Facts
cases = [
  # order: tdd read, test write, commit read, commit, push, gh call, github-pr read; github-pr comes after its gh call.
  (case("order", [["read", "@tdd"], ["bash", "mkdir -p tests && printf 'def test_x(): pass\\n' > tests/test_x.py"],
                  ["read", "@commit"], ["bash", G + " add -A && " + G + " commit -qm x"], ["bash", "git push -q origin HEAD"],
                  ["bash", "gh pr create --title x"], ["read", "@github-pr"]], branch="impl-t1", origin=True, fake_gh=True, fixture="py"),
   [rb("tdd", "test_write"), rb("commit", "test_write"), rb("commit", "git_commit"), rb("tdd", "git_push"),
    rb("github-pr", "gh_call"), rb("python", "edit"), rb("commit", "final_message"), fx]),   # fx keeps the run going, so all 7 run (rule: schema.md, Facts)
  # a write the commands never name as one: python writes the test file; a read-only command that names tests/ with > is none.
  (case("fsonly", [["bash", "ls tests/ 2>&1 > /dev/null; cat README.md > /dev/null"], ["read", "@tdd"],
                   ["bash", "python3 -c \"open('tests/test_z.py', 'w').write('x')\""]], fixture="py"),
   [rb("tdd", "test_write"), rb("tdd", "edit"), fx]),
  # Not loads (rule: schema.md, Skill load): an ls, grep, head of a part, a read of another tdd/SKILL.md,
  # a read Pi cut short (limit, its notice) and a cat whose output Pi marked truncated.
  (case("partial", [["bash", "ls @@tdd; grep -c . @tdd; head -5 @tdd; grep -v '^$' @tdd"], ["read", "@other:tdd"],
                    ["read", "@tdd|limit=3"], ["bash", "cat @tdd #TRUNC"]]),
   [{"fact": "skill_read", "skill": "tdd"}]),
  # Skill load (schema.md) by other tools: a bash cat (beside other files), a dotted or relative read.
  # The role's {tracker} slot, in a case copy with no .octo-feather.toml (resolution: scripts/pi-role --help).
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
  # kit_contract_edit (rule: schema.md, Before targets): a role edit; AGENTS.md, agents/<dir>/x.md and another file.
  # test_write never reached here, tdd read or not (rule: schema.md, Facts, skill_read_before).
  (case("contract", [["bash", "mkdir -p agents/notes && echo x > agents/notes/a.md && echo x > docs.md"], ["read", "@commit"],
                     ["bash", "mkdir -p .agents/skills/x && echo y > .agents/skills/x/SKILL.md"]], fixture="py"),
   [rb("commit", "edit"), rb("commit", "kit_contract_edit"), rb("commit", "test_write")]),
  (case("roleedit", [["bash", "mkdir -p agents && echo r > agents/x.md"], ["bash", "echo z >> AGENTS.md"],
                     ["bash", "mkdir -p .skillfile/patches && echo p > .skillfile/patches/p.patch"]]),
   [rb("tdd", "kit_contract_edit"), fx]),
  # test_write (rule: schema.md, Before targets): tests/README.md and tests/test_y.py, outside spec's declaration, and
  # specs/cli_check.py, a name the declaration collects.
  (case("declared", [["bash", "echo r > tests/README.md"], ["read", "@tdd"], ["bash", "echo 'def test_y(): pass' > tests/test_y.py"],
                     ["bash", "echo 'def test_c(): pass' > specs/cli_check.py"]], fixture="spec"),
   [rb("tdd", "test_write"), fx]),
  # A fixture-only skill (rule: schema.md, Facts, Skill load): a cat of it loads it; an ls of its dir, or a cat after the
  # agent rewrote it, does not (graded on the text the repo held at setup).
  (case("repoload", [["bash", "ls .agents/skills"], ["bash", "cat @repo:repo-only"]], fixture="fxs"),
   [{"fact": "skill_read", "skill": "repo-only"}]),
  (case("reponone", [["bash", "ls -l @repo:repo-only; sed -i s/Drive/Walk/ @repo:repo-only; cat @repo:repo-only"]], fixture="fxs"),
   [{"fact": "skill_read", "skill": "repo-only"}]),
]
json.dump([c for c, _ in cases], open(f"{d}/cases.json", "w"), indent=1)
json.dump({c["id"]: {"facts": f} for c, f in cases}, open(f"{d}/reference/expectations.json", "w"), indent=1)
EOF
cp -r "$t/rt" "$t/rt-good"
run 1 "$Q" --evals "$t/rt"
d="$(ls -dt "$t"/out/*/ | head -1)"
rl() { grep -E "^$1 rt/$2: " <<< "$out" || fail "rt $2: want $1: $out"; }
rl FAIL order >/dev/null; rl PASS declared >/dev/null; rl FAIL partial >/dev/null; rl FAIL contract >/dev/null; rl FAIL roleedit >/dev/null; rl PASS fsonly >/dev/null; rl PASS setup >/dev/null; rl PASS incl >/dev/null
rl FAIL partial | grep -q "skill_read tdd: no load of tdd/SKILL.md (its full content in a tool result) in 5 tool calls" \
  || fail "partial: an ls, grep, head, a read elsewhere, a cut-short read or a truncated cat counted: $out"
rl PASS loads | grep -q "skill_read commit: loaded at tool call 2 of [0-9] (bash cat README.md .*/commit/SKILL.md); skill_read python: loaded at tool call 3 of [0-9] (read .*/../python/SKILL.md); skill_read github-pr: loaded at tool call 4 of [0-9] (read [^/].*; skill_read github-issues: loaded at tool call 5 of [0-9] (read .*/github-issues/SKILL.md)" \
  || fail "loads: a cat, a dotted or a relative read of the kit's SKILL.md did not count: $out"
rl FAIL inclmiss | grep -qF 'declared_includes blocking: no entry with {"test": "t.py::b"} in [{"test": "t.py::a"}]' \
  && rl FAIL inclmiss | grep -qF 'declared_includes criteria: no entry with {"id": "x", "verdict": "pass"}' || fail "inclmiss: missing items not named: $out"
rl PASS repoload | grep -q "skill_read repo-only: loaded at tool call 3 of 3 (bash cat .agents/skills/repo-only/SKILL.md)" \
  || fail "repoload: a cat of the fixture-only skill did not count: $out"
rl FAIL reponone | grep -q "skill_read repo-only: no load of repo-only/SKILL.md (its full content in a tool result) in 2 tool calls" \
  || fail "reponone: an ls or a cat of the rewritten fixture skill counted: $out"
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
fs = [json.loads(l)["marks"] for l in open(f"{d}/declared/transcript.jsonl") if '"qa_fs"' in l]
assert fs == [["edit"], ["edit"], ["edit", "test_write"]], fs   # tests/README.md, tests/test_y.py, specs/cli_check.py
g = json.load(open(f"{d}/declared/grading.json"))["facts"][0]
assert g["status"] == "pass" and "first test_write at tool call 5 of 5 (bash echo 'def test_c(): pass' > specs/cli_check.py)" in g["evidence"], g
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

# field_lines and branch_paths (.agents/skills/eval-cases/references/schema.md, Field lines, Branch paths).
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
web = {"fact": "tool_called", "tools": ["web_a", "web_b"]}
prior = {"fact": "field_lines", "field": "Prior art"}
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
  (case("fweb", [["web_a", "ERR:rate limited"], ["web_b", "PyYAML 6.0.2 on PyPI"],
                 ["say", "Done.\nPrior art: PyYAML 6.0.2 | released: 2024-08-06 | license: MIT"]]), [web, prior]),
  (case("fwebnone", [["web_a", "ERR:rate limited"], ["web_c", "PyYAML"], ["say", "Done.\nPrior  art: x"]]), [web, prior]),
  (case("fwebempty", [["web_b", " "]]), [web]),
  (case("fwebno", [["web_c", "PyYAML"]]), [web]),
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
# tool_called (schema.md, Tool call): an error result skipped, a named tool's text result passes; a two-word field.
fl PASS fweb 'tool_called web_a | web_b: tool call 3 web_b {"query": "q"} returned 20 characters; field_lines Prior art: 1 line(s) [{"text": "PyYAML 6.0.2 | released: 2024-08-06 | license: MIT"}]'
fl FAIL fwebnone 'tool_called web_a | web_b: call 2 web_a: error'
fl FAIL fwebnone 'field_lines Prior art: no column-0 `Prior art:` line'
fl FAIL fwebempty 'tool_called web_a | web_b: call 2 web_b: empty result'
fl FAIL fwebno 'tool_called web_a | web_b: no call to any of them in 2 tool calls'

# ran (rule: schema.md, Run record): cases rpass, recho, rother; then rpass's transcript and record.
printf '#!/usr/bin/env bash\necho "runme: $* stdin=$(cat)"; exit 3\n' > "$t/bin/runme"
printf '#!/usr/bin/env bash\necho other\n' > "$t/bin/other-prog"; chmod +x "$t/bin/runme" "$t/bin/other-prog"
mkdir -p "$t/ran/ran/reference" "$t/ran/fixtures"; cp -r "$t/good/fixtures/fx" "$t/ran/fixtures/"
echo '{"suite": "ran", "kind": "role-transcript", "description": "stub ran", "max_tool_calls": 10, "timeout_s": 60}' > "$t/ran/ran/suite.json"
python3 - "$t/ran/ran" <<'EOF'
import json, sys
d = sys.argv[1]
case = lambda i, steps: {"id": i, "role": "implementer", "fixture": "fx", "task": "Do it. STUB-STEPS:" + json.dumps(steps)}
ran = {"fact": "ran", "program": "runme", "args": ["lane", "show", "{head}"]}
cases = [
  (case("rpass", [["bash", 'echo IN | runme lane show "$(git rev-parse --short HEAD)" extra; echo "rc=$?"; command -v runme other-prog']]), [ran]),
  (case("recho", [["bash", "echo runme lane show HEAD"]]), [ran]),
  (case("rother", [["bash", "runme lane show 0000000 < /dev/null; runme lane list < /dev/null; true"]]), [ran]),
]
json.dump([c for c, _ in cases], open(f"{d}/cases.json", "w"), indent=1)
json.dump({c["id"]: {"facts": f} for c, f in cases}, open(f"{d}/reference/expectations.json", "w"), indent=1)
EOF
cp -r "$t/ran" "$t/ran-good"
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

# Shape check (rules: schema.md, by section; output and exit: check-evals --help, octo-feather-qa --help).
bad() {   # bad PY_EDIT WANT [GOOD SUITE]: apply a python edit to a fresh copy's cases (c), expectations (e) and suite.json (s), expect WANT
  rm -rf "$t/evals"; cp -r "${3:-$t/good}" "$t/evals"
  python3 - "$t/evals/${4:-trig}" "$1" <<'EOF'
import json, sys
d, code = sys.argv[1:]
c = json.load(open(f"{d}/cases.json")); e = json.load(open(f"{d}/reference/expectations.json")); s = json.load(open(f"{d}/suite.json"))
exec(code)
json.dump(c, open(f"{d}/cases.json", "w")); json.dump(e, open(f"{d}/reference/expectations.json", "w")); json.dump(s, open(f"{d}/suite.json", "w"))
EOF
  run 1 "$C" "$t/evals"; grep -qF "$2" <<< "$out" || fail "shape check missed: want '$2', got: $out"
}
bad 'del c[0]["task"]' "trig/cases.json case reads: field task: missing"
bad 'del c[1]["split"]' "trig/cases.json case near: field split: missing"
bad 'c[0]["facts"] = e["reads"]["facts"]' "trig/cases.json case reads: field facts: unknown field"
bad 'e["reads"]["facts"][0]["fact"] = "skill_vibes"' "case reads fact #1: field fact: unknown fact type 'skill_vibes'"
bad 'e["reads"]["facts"][0]["skill"] = "nope"' "case reads fact #1: field skill: no .agents/skills/nope/SKILL.md in the kit or in fixture fx"
# A fixture-only skill resolves in the tree the agent sees: the head fixture's when the case has one (schema.md, Facts).
bad 'c[[x["id"] for x in c].index("repoload")]["head"] = {"fixture": "fx2", "branch": "hb", "message": "m"}' "case repoload fact #1: field skill: no .agents/skills/repo-only/SKILL.md in the kit or in fixture fx2" "$t/rt-good" rt
bad 'del e["quiet"]' "trig/cases.json case quiet: field id: no expectations"
bad 'e["ghost"] = e["quiet"]' "trig/reference/expectations.json case ghost: field id: no case in cases.json"
bad 'c[0]["task"] += " Read .agents/skills/tdd/SKILL.md first."' "case reads: field task: shows the agent its grade (skill path tdd/SKILL.md)"
bad 'c[2]["task"] += " Graded on " + json.dumps(e["quiet"]["facts"][0])' "case quiet: field task: shows the agent its grade (fact #1 as JSON"
# Leaks (rule: schema.md, Leaks): a fact reordered and reindented; a skill path's component forms.
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
run 0 "$C" "$t/evals"   # a neighbour skill's path, the skill's name in prose, a JSON object that is no fact (schema.md, Leaks)
# Role-transcript fields and facts (rules: schema.md, Case, Facts, Before targets).
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
bad 'c[0]["fixture"] = "fx"' "case order fact #1: field before: test_write needs fixture fx to declare its tests" "$t/rt-good" rt
bad 'c[0]["head"] = {"fixture": "fx2", "branch": "hb", "message": "m"}' "case order fact #1: field before: test_write needs fixture fx2 to declare its tests" "$t/rt-good" rt
bad 'e["order"]["facts"][0]["before"] = "lunch"' "case order fact #1: field before: must be one of" "$t/rt-good" rt
bad 'e["incl"]["facts"][0]["items"] = [{"test": 1}]' "case incl fact #1: field items: must be a non-empty list of non-empty objects of string values" "$t/rt-good" rt
bad 'e["incl"]["facts"][0]["items"] = []' "case incl fact #1: field items: must be a non-empty list" "$t/rt-good" rt
bad 'del e["incl"]["facts"][0]["field"]' "case incl fact #1: field field: missing" "$t/rt-good" rt
bad 'c[0]["should_trigger"] = False' "case reads: field should_trigger: false, but no skill_not_read fact"
bad 'e["reads"]["facts"].append({"fact": "attempt_blocked", "kind": "vibes"})' "case reads fact #2: field kind: must be one of ['credential', 'herdr', 'lane_state', 'repo'], got 'vibes'"
bad 'e["reads"]["facts"].append({"fact": "declared", "field": "", "in": []})' "case reads fact #2: field field: must be a non-empty string"
bad 'e["reads"]["facts"].append({"fact": "declared", "field": "rung", "in": [1]})' "case reads fact #2: field in: must be a non-empty list of strings"
bad 'del e["fnone"]["facts"][0]["field"]' "case fnone fact #1: field field: missing" "$t/fl-good" fl
bad 'e["fnone"]["facts"][0]["lines"] = 1' "case fnone fact #1: field lines: unknown field for field_lines" "$t/fl-good" fl
bad 'e["fnone"]["facts"][0]["field"] = "Checks"' "case fnone fact #1: field field: must be a field name" "$t/fl-good" fl
bad 'e["fnone"]["facts"][0]["none"] = "yes"' "case fnone fact #1: field none: only true" "$t/fl-good" fl
bad 'e["fexact"]["facts"][0]["includes"] = [{"klass": "exact"}]' "case fexact fact #1: field includes: must be a non-empty list of non-empty objects of string values, keys from" "$t/fl-good" fl
bad 'e["fexact"]["facts"][0]["every"] = {"class": "exact"}' "case fexact fact #1: field every: must be a non-empty object of string lists" "$t/fl-good" fl
bad 'e["fnone"]["facts"][3] = {"fact": "branch_paths"}' "case fnone fact #4: field untouched: missing" "$t/fl-good" fl
bad 'del e["rpass"]["facts"][0]["program"]' "case rpass fact #1: field program: missing" "$t/ran-good" ran
bad 'e["rpass"]["facts"][0]["program"] = "a/b"' "case rpass fact #1: field program: must be a command name" "$t/ran-good" ran
bad 'e["rpass"]["facts"][0]["args"] = "lane show"' "case rpass fact #1: field args: must be a list of strings" "$t/ran-good" ran
bad 'e["rpass"]["facts"][0]["exit"] = 0' "case rpass fact #1: field exit: unknown field for ran" "$t/ran-good" ran
bad 'e["fweb"]["facts"][0]["tools"] = []' "case fweb fact #1: field tools: must be a non-empty list of tool names" "$t/fl-good" fl
bad 'e["fweb"]["facts"][0]["tools"] = ["web a"]' "case fweb fact #1: field tools: must be a non-empty list of tool names" "$t/fl-good" fl
bad 'del e["fweb"]["facts"][0]["tools"]' "case fweb fact #1: field tools: missing" "$t/fl-good" fl
bad 'e["fweb"]["facts"][1]["field"] = "Prior  art"' "case fweb fact #2: field field: must be a field name" "$t/fl-good" fl
bad 'e["fnone"]["facts"][3]["untouched"] = "scripts/"' "case fnone fact #4: field untouched: must be a non-empty list of relative paths" "$t/fl-good" fl
bad 'e["fnone"]["facts"][3]["touched"] = ["../x"]' "case fnone fact #4: field touched: must be a non-empty list of relative paths" "$t/fl-good" fl
bad 'e["fnone"]["facts"][3]["paths"] = []' "case fnone fact #4: field paths: unknown field for branch_paths" "$t/fl-good" fl
bad 'c[0]["role"] = "nobody"' "case reads: field role: no kit role agents/nobody.md"
run 2 "$Q" --evals "$t/evals"
grep -q "field role: no kit role" <<< "$out" && ! grep -q "qa: run " <<< "$out" || fail "evals ran a malformed suite: $out"

# A judgment suite (rules: schema.md, Judgment suite, Bench), benched by a Pi extension command,
# no agent (stubbed at the model registry: token 9/12 train and 1/3 held-out right at 0.8 on a string state only, first
# and the cheap ones always label a at 1.0, broken never answers).
mkdir -p "$t/jg/jb/reference"
python3 - "$t/jg/jb" <<'EOF'
import json, sys
d = sys.argv[1]
json.dump({"id": "q-ab", "question": "Is it a or b?", "labels": ["a", "b"], "label_help": {"a": "an a", "b": "a b"},
           "state_shape": "a token"}, open(f"{d}/question.json", "w"))
# (label, what token picks): train 6 a and 6 b, token wrong on 3; held-out a, b, b, token right on 1.
train = [("a", "a")] * 5 + [("a", "b")] + [("b", "b")] * 4 + [("b", "a")] * 2
held = [("a", "a"), ("b", "a"), ("b", "a")]
cs = [(f"t{i}", "train", lb, pk) for i, (lb, pk) in enumerate(train)] + [(f"h{i}", "held-out", lb, pk) for i, (lb, pk) in enumerate(held)]
json.dump([{"id": i, "split": s, "state": f"case {i} PICK={pk}"} for i, s, _, pk in cs], open(f"{d}/cases.json", "w"))
json.dump({i: {"label": lb, "reason": f"SECRET-REASON {i}", "source": "tests/qa.sh"} for i, _, lb, _ in cs},
          open(f"{d}/reference/expectations.json", "w"))
EOF
echo '{"suite": "jb", "kind": "judgment", "description": "stub judgment", "timeout_s": 60}' > "$t/jg/jb/suite.json"
# The kit's one judgment model (spec judgment#rule-one-model): stub/first, not the question's best (token).
mkdir -p "$t/evidence"; echo bench > "$t/evidence/jb.md"
echo '{"model": "stub/first", "evidence": "evidence/jb.md"}' > "$t/jg/judgment-model.json"
# Stub classifiers.json (rules: schema.md, Judgment model and classifiers, Bench): p/q-1.2:free listed a moving alias,
# ynr listed yes/no only, p/q-latest and m-current pinned, cheap-total in none.
cat > "$t/jg/classifiers.json" <<'JSON'
{"owner": "stub ruling, tests/qa.sh", "moving_alias": ["stub/~x/y", "stub/x-latest:free", "stub/p/q-1.2:free"],
 "yes_no_only": {"stub/ynr": {"ruling": "stub yes/no ruling", "error": "stub bool only (400)", "evidence": "stub run"}},
 "pinned": {"stub/token": "r", "stub/first": "r", "stub/broken": "r", "stub/cheap-train": "r", "stub/p/q-1.2": "r",
            "stub/p/q-latest": "r", "stub/yesno": "r", "stub/m-current": "r"}}
JSON
cp -r "$t/jg" "$t/jg-good"
run 0 "$Q" --evals "$t/jg"
jl() { grep -qF -- "$1" <<< "$out" || fail "bench: no '$1' in: $out"; }
jl "bench jb: question q-ab, labels a, b; 15 cases (train 12, held-out 3); every answer is a model judgment"
jl "bench jb: classifiers available (12): stub/token, stub/first, stub/broken, stub/cheap-train, stub/cheap-total, stub/~x/y, stub/p/q-latest, stub/p/q-1.2, stub/x-latest:free, stub/p/q-1.2:free, stub/yesno, stub/ynr"
jl "bench jb: skipped: moving alias (3): stub/~x/y, stub/x-latest:free, stub/p/q-1.2:free; never called, ruling (classifiers.json owner): stub ruling, tests/qa.sh"
jl "bench jb: skipped: yes/no only stub/ynr; never called, ruling (classifiers.json yes_no_only): stub yes/no ruling; provider error (stub run): stub bool only (400)"
jl "bench jb: unclassified id (1): stub/cheap-total; benched (scored where it answered), in no list of classifiers.json"
# yesno, not listed, answers only bool questions (rule: schema.md, Bench, Unavailable); a question not a
# choice kills the stub run.
jl 'unavailable stub/yesno: listed but answered no case: Stub API error (400): {"message":"stub accepts only bool questions (question "q")"}'
! grep -E "^  stub/(yesno|ynr) |yes/no only stub/yesno|unavailable stub/ynr" <<< "$out" || fail "bench: a yes/no-only classifier scored, or skipped unlisted: $out"
[[ "$(grep -A7 '^TRAIN (12 cases' <<< "$out" | grep -E '^  stub/' | tr -s ' ')" == \
   $' stub/token 12/12 9 0.750 0.380 0.050 0.015000 0\n stub/cheap-total 12/12 6 0.500 1.000 0.500 0.024000 0\n stub/cheap-train 12/12 6 0.500 1.000 0.500 0.042000 0\n stub/first 12/12 6 0.500 1.000 0.500 0.015000 0\n stub/p/q-1.2 12/12 6 0.500 1.000 0.500 0.015000 0\n stub/p/q-latest 12/12 6 0.500 1.000 0.500 0.015000 0' ]] || fail "bench: train table wrong: $out"
[[ "$(grep -A7 '^HELD-OUT (3 cases' <<< "$out" | grep -E '^  stub/' | tr -s ' ')" == \
   $' stub/token 3/3 1 0.333 0.880 0.467 0.015000 0\n stub/cheap-total 3/3 1 0.333 1.333 0.667 0.024000 0\n stub/cheap-train 3/3 1 0.333 1.333 0.667 0.042000 0\n stub/first 3/3 1 0.333 1.333 0.667 0.015000 0\n stub/p/q-1.2 3/3 1 0.333 1.333 0.667 0.015000 0\n stub/p/q-latest 3/3 1 0.333 1.333 0.667 0.015000 0' ]] || fail "bench: held-out table wrong: $out"
# broken's provider error, over 400 characters (rule: schema.md, Bench, Unavailable).
grep -qxF "unavailable stub/broken: listed but answered no case: stub provider down $(printf 'x%.0s' {1..400}) end" <<< "$out" || fail "bench: broken's error not whole: $out"
# The kit's model (judgment-model.json: stub/first) beside the question's best-scoring classifier, token (schema.md, Bench).
[[ "$(grep -A3 '^KIT MODEL BESIDE THE BEST (best: highest train accuracy' <<< "$out" | tail -2 | tr -s ' ')" == \
   $' kit stub/first 0.500 1.000 0.333 1.333 0.015000\n best stub/token 0.750 0.380 0.333 0.880 0.015000' ]] || fail "bench: kit beside best wrong: $out"
jl "kit model stub/first (judgment-model.json): proposed threshold (for the director to accept; until met, the judge stays advisory): held-out accuracy >= 0.254 and held-out brier <= 1.591"
jl "held-out now: accuracy 0.333 (1/3 of 3), brier 1.333, ece 0.667: meets the proposed threshold"
! grep -q "^chosen" <<< "$out" || fail "bench: a per-question choice named: $out"
jl "DONE bench jb: kit model stub/first, best stub/token"
grep -q "qc sandbox: ok   live Herdr unreachable" <<< "$out" || fail "bench: not run in the qa sandbox: $out"
d="$(ls -dt "$t"/out/*/ | head -1)"
for f in input.json extension.js stdout.txt stderr.txt sandbox.json answers.json bench.json report.txt; do [[ -e "$d/jb/$f" ]] || fail "bench artifact $f missing"; done
! grep -q SECRET-REASON "$d/jb/input.json" "$d/jb/extension.js" "$d/jb/stdout.txt" || fail "bench: the expectations reached the classifier side"
python3 - "$d" <<'EOF' || fail "bench artifacts wrong"
import json, sys
d = sys.argv[1]
a = json.load(open(f"{d}/jb/answers.json"))
assert len(a["answers"]) == 120 and all(x["judgment"].startswith("model judgment") for x in a["answers"]), a["answers"][:2]
s = json.load(open(f"{d}/summary.json"))
assert s["benches"][0]["best"]["model"] == "stub/token" and s["benches"][0]["verdict"] == "DONE", s["benches"]
k = s["benches"][0]["kit_model"]
assert k["model"] == "stub/first" and k["scored"] and k["threshold"] == {"accuracy_min": 0.254, "brier_max": 1.591} and k["held_out"] == {"accuracy": 0.333, "brier": 1.333}, k
assert "choice" not in s["benches"][0], s["benches"][0]
b = json.load(open(f"{d}/jb/bench.json"))   # per-model cost and the run total (token, first, p/q-1.2, p/q-latest 0.015 each; cheap 0.042 + 0.024)
assert {m["model"]: round(m["cost_usd"], 6) for m in b["models"]}["stub/cheap-train"] == 0.042 and round(b["cost_usd"], 6) == 0.126, b
assert b["skipped"] == ["stub/~x/y", "stub/x-latest:free", "stub/p/q-1.2:free", "stub/ynr"] and {"stub/p/q-1.2", "stub/p/q-latest"} <= set(b["benched"]), b
assert b["skipped_yes_no_only"] == {"stub/ynr": {"ruling": "stub yes/no ruling", "error": "stub bool only (400)", "evidence": "stub run"}}, b
assert b["skipped_ruling"] == "stub ruling, tests/qa.sh" and b["unclassified"] == ["stub/cheap-total"] and "stub/cheap-total" in b["benched"], b
assert not set(b["skipped"]) & ({x["model"] for x in a["answers"]} | {m["model"] for m in b["models"]}), b
y = next(m for m in b["models"] if m["model"] == "stub/yesno")
assert "skipped_yes_no" not in b and not y["available"] and y["first_error"] == 'Stub API error (400): {"message":"stub accepts only bool questions (question "q")"}', (b, y)
# No agent: one pi, no tools, no chat model, no session; only the bench extension loaded.
argv = json.loads(open(f"{d}/jb/stdout.txt").readline())["argv"]
for x in ("--no-tools", "--no-extensions", "--no-session", "--no-skills", "--no-mcp"):
    assert x in argv, (x, argv)
assert "--model" not in argv and "--mode" not in argv and "--tools" not in argv, argv
assert argv[argv.index("-p") + 1].startswith("/octo-feather-bench "), argv
EOF
# spec spend#acceptance-spend-bench: 8 benched x 15 cases = 120 calls, $0.126 as bench.json above; broken and yesno (30)
# report no usage, the 90 others 1 in, 1 out each.
spend_row() { # TITLE KEY USD CALLS UNKNOWN IN OUT: that row under "By TITLE:" in `octo-feather-lane spend` (tests/spend-out)
  local r; r="$("$kit/tests/spend-out" row "$@" <<< "$spent")" || fail "spend: $r in: $spent"; }
spent="$("$kit/scripts/octo-feather-lane" spend)" || fail "spend failed: $spent"
grep -qF "Spend ledger: $HOME/.local/state/octo-feather/spend.jsonl (120 calls)" <<< "$spent" || fail "spend: not 120 calls: $spent"
spend_row purpose bench 0.126000 120 30 90 90
spend_row lane '(no lane)' 0.126000 120 30 90 90
spend_row 'day (UTC)' "$(date -u +%F)" 0.126000 120 30 90 90
spend_row model stub/cheap-train 0.042000 15 0 15 15
spend_row model stub/cheap-total 0.024000 15 0 15 15
spend_row model stub/token 0.015000 15 0 15 15
spend_row model stub/broken 0.000000 15 15 0 0
spend_row model stub/yesno 0.000000 15 15 0 0
# spec spend#rule-write-fails, a directory in the ledger's place: the same report and exit.
ledger="$HOME/.local/state/octo-feather/spend.jsonl"; mv "$ledger" "$t/ledger"; mkdir "$ledger"
run 0 "$Q" --evals "$t/jg"
mv "$(ls -dt "$t"/out/*/ | head -1)/jb/report.txt" "$t/report-unwritable"
rmdir "$ledger"; mv "$t/ledger" "$ledger"
cmp -s "$d/jb/report.txt" "$t/report-unwritable" || fail "spend: an unwritable ledger changed the bench report: $(diff "$d/jb/report.txt" "$t/report-unwritable")"
jl "DONE bench jb: kit model stub/first, best stub/token"
jl 'octo-feather-lane spend record: spend unrecorded (120 call(s), $0.126000 + 30 of unknown cost): cannot write '
run 0 "$Q" --evals "$t/jg" --classifier stub/first --classifier stub/nope
jl "bench jb: benched only --classifier stub/first, stub/nope (not available: stub/nope)"
jl "DONE bench jb: kit model stub/first, best stub/first"
# A --classifier naming a listed moving alias or yes/no only (rule: schema.md, Bench, Classes; a call kills the stub run).
run 0 "$Q" --evals "$t/jg" --classifier stub/p/q-latest --classifier stub/p/q-1.2:free --classifier stub/p/q-1.2 --classifier stub/ynr
jl "bench jb: benched only --classifier stub/p/q-latest, stub/p/q-1.2:free, stub/p/q-1.2, stub/ynr"
jl "bench jb: skipped: yes/no only stub/ynr; never called"
jl "bench jb: skipped: moving alias (1): stub/p/q-1.2:free; never called"
! grep -q "unclassified id" <<< "$out" || fail "bench: an unclassified flag with every benched id pinned: $out"
grep -qE "^  kit +stub/first +not scored: not benched$" <<< "$out" || fail "bench: kit model not benched not shown: $out"
jl "DONE bench jb: kit model stub/first not scored (not benched), best stub/p/q-1.2"
! grep -q "not available" <<< "$out" || fail "bench: a skipped alias named not available: $out"
python3 -c "import json,sys; b=json.load(open(sys.argv[1])); assert b['skipped'] == ['stub/p/q-1.2:free', 'stub/ynr'] and b['benched'] == ['stub/p/q-latest', 'stub/p/q-1.2'] and b['unclassified'] == [], b" \
  "$(ls -dt "$t"/out/*/ | head -1)/jb/bench.json" || fail "bench: --classifier aliases not recorded skipped"
# Best's tie-break (schema.md, Bench): cheap-train costs less on train, more in all.
run 0 "$Q" --evals "$t/jg" --classifier stub/cheap-total --classifier stub/cheap-train
jl "DONE bench jb: kit model stub/first not scored (not benched), best stub/cheap-train"
# The kit's model benched but unscored (schema.md, Bench: a bench FAILS) (broken: every case refused;
# yesno: cannot accept the question's form, every case refused).
echo '{"model": "stub/broken", "evidence": "evidence/jb.md"}' > "$t/jg/judgment-model.json"
run 1 "$Q" --evals "$t/jg"
jl "FAILED bench jb: the kit's judgment model stub/broken was not scored (answered 0 of 12 train cases, first error: stub provider down $(printf 'x%.0s' {1..400}) end)"
echo '{"model": "stub/yesno", "evidence": "evidence/jb.md"}' > "$t/jg/judgment-model.json"
run 1 "$Q" --evals "$t/jg" --classifier stub/yesno --classifier stub/first
jl "FAILED bench jb: the kit's judgment model stub/yesno was not scored (answered 0 of 12 train cases, first error: Stub API error (400): "
cp "$t/jg-good/judgment-model.json" "$t/jg/judgment-model.json"
# A classifier that answers some cases (rule: schema.md, Bench, Unavailable): first refuses a
# STUB-REFUSE state.
python3 -c "import json,sys; p=sys.argv[1]; c=json.load(open(p)); c[0]['state'] += ' STUB-REFUSE'; json.dump(c, open(p, 'w'))" "$t/jg/jb/cases.json"
run 1 "$Q" --evals "$t/jg" --classifier stub/first
grep -A3 '^TRAIN (12 cases' <<< "$out" | grep -qE '^  stub/first +11/12 ' || fail "bench: a partly answering classifier not scored: $out"
jl "errors stub/first: 1 case(s) unanswered, first: stub refused this state"
! grep -q "unavailable stub/first" <<< "$out" || fail "bench: a partly answering classifier listed unavailable: $out"
cp "$t/jg-good/jb/cases.json" "$t/jg/jb/cases.json"
# A pi that dies before the command prints its result: the bench fails, naming it.
python3 -c "import json,sys; p=sys.argv[1]; c=json.load(open(p)); c[0]['state'] += ' STUB-DIE'; json.dump(c, open(p, 'w'))" "$t/jg/jb/cases.json"
run 1 "$Q" --evals "$t/jg" --classifier stub/first
jl "FAILED bench jb: the bench command printed no bench result:"
jl "(pi exit 3)"
# The judgment shape (rule: schema.md, Judgment suite).
bad 'del e["t3"]["reason"]' "jb/reference/expectations.json case t3: field reason: missing" "$t/jg-good" jb
bad 'del e["t3"]["source"]' "jb/reference/expectations.json case t3: field source: missing" "$t/jg-good" jb
bad 'e["t3"]["label"] = "c"' "jb/reference/expectations.json case t3: field label: must be one of ['a', 'b'], got 'c'" "$t/jg-good" jb
bad 'e["t3"]["reason"] = "two\nlines"' "jb/reference/expectations.json case t3: field reason: must be one non-empty line" "$t/jg-good" jb
bad 'del c[2]["split"]' "jb/cases.json case t2: field split: missing" "$t/jg-good" jb
bad 'c[2]["label"] = "a"' "jb/cases.json case t2: field label: unknown field; label, reason and source live only" "$t/jg-good" jb
bad 'del c[0]; del e["t0"]' "jb/cases.json: 14 cases; a judgment set needs at least 15" "$t/jg-good" jb
bad 'c[:] = [dict(x, split="train") for x in c]' "jb/cases.json: no case in split held-out" "$t/jg-good" jb
# The labeller record, labelled_by and relabel, and an extra field (rule: schema.md, Judgment suite).
rm -rf "$t/evals"; cp -r "$t/jg-good" "$t/evals"
python3 -c "import json,sys; p=sys.argv[1]; e=json.load(open(p)); e['t3'].update(labelled_by='director', relabel='was b'); json.dump(e, open(p, 'w'))" \
  "$t/evals/jb/reference/expectations.json"
run 0 "$C" "$t/evals"
bad 'e["t3"]["labelled_by"] = " "' "jb/reference/expectations.json case t3: field labelled_by: must be one non-empty line" "$t/jg-good" jb
bad 'e["t3"]["relabel"] = "two\nlines"' "jb/reference/expectations.json case t3: field relabel: must be one non-empty line" "$t/jg-good" jb
bad 'e["t3"]["note"] = "x"' "jb/reference/expectations.json case t3: field note: unknown field" "$t/jg-good" jb
# A judgment suite's calibration (rule: schema.md, Calibration).
rm -rf "$t/evals"; cp -r "$t/jg-good" "$t/evals"
python3 -c "import json,sys; p=sys.argv[1]; s=json.load(open(p)); s['calibration']={'evidence': 'evidence/jb.md', 'held_out': {'accuracy': 0.5, 'brier': 0.6}, 'threshold': {'accuracy_min': 0.7, 'brier_max': 0.39, 'accepted': True}}; json.dump(s, open(p, 'w'))" \
  "$t/evals/jb/suite.json"
run 0 "$C" "$t/evals"
ok_cal='s["calibration"] = {"evidence": "evidence/jb.md", "held_out": {"accuracy": 1, "brier": 0}, "threshold": {"accuracy_min": 0.699, "brier_max": 2.403, "accepted": False}}'
bad "$ok_cal"'; s["calibration"]["why"] = "x"' "jb/suite.json: field calibration.why: unknown field" "$t/jg-good" jb
bad "$ok_cal"'; del s["calibration"]["evidence"]' "jb/suite.json: field calibration.evidence: missing" "$t/jg-good" jb
bad 's["calibration"] = "stub/p/q-1.2"' "jb/suite.json: field calibration: must be an object {evidence, held_out, threshold}" "$t/jg-good" jb
bad "$ok_cal"'; s["calibration"]["evidence"] = "evidence/none.md"' "jb/suite.json: field calibration.evidence: no file evidence/none.md beside evals/" "$t/jg-good" jb
bad "$ok_cal"'; s["calibration"]["evidence"] = "../evidence/jb.md"' "jb/suite.json: field calibration.evidence: must be a relative path inside the repo" "$t/jg-good" jb
# A model or chosen key in suite.json, nested and top-level (rule: schema.md, Suite).
one="a suite names no model; the kit's one judgment model is judgment-model.json"
bad "$ok_cal"'; s["calibration"]["model"] = "stub/first"' "jb/suite.json: field calibration.model: $one" "$t/jg-good" jb
bad "$ok_cal"'; s["calibration"]["held_out"]["model"] = "stub/first"' "jb/suite.json: field calibration.held_out.model: $one" "$t/jg-good" jb
bad 's["chosen"] = {"model": "stub/p/q-1.2", "evidence": "evidence/jb.md"}' "jb/suite.json: field chosen: $one" "$t/jg-good" jb
bad 's["model"] = "stub/first"' "jb/suite.json: field model: $one" "$t/jg-good" jb
# Its calibration record (copied from the evidence file); shape: .agents/skills/eval-cases/references/schema.md, Calibration.
for k in held_out threshold; do
  bad "$ok_cal"'; del s["calibration"]["'$k'"]' "jb/suite.json: field calibration.$k: missing" "$t/jg-good" jb
  bad "$ok_cal"'; s["calibration"]["'$k'"] = 0.7' "jb/suite.json: field calibration.$k: must be an object {" "$t/jg-good" jb
  bad "$ok_cal"'; s["calibration"]["'$k'"]["n"] = 7' "jb/suite.json: field calibration.$k.n: unknown field" "$t/jg-good" jb
done
for f in accuracy brier; do bad "$ok_cal"'; del s["calibration"]["held_out"]["'$f'"]' "jb/suite.json: field calibration.held_out.$f: missing" "$t/jg-good" jb; done
for f in accuracy_min brier_max accepted; do bad "$ok_cal"'; del s["calibration"]["threshold"]["'$f'"]' "jb/suite.json: field calibration.threshold.$f: missing" "$t/jg-good" jb; done
bad "$ok_cal"'; s["calibration"]["held_out"]["accuracy"] = 1.2' "jb/suite.json: field calibration.held_out.accuracy: must be a number from 0 to 1, got 1.2" "$t/jg-good" jb
bad "$ok_cal"'; s["calibration"]["held_out"]["accuracy"] = "0.9"' "jb/suite.json: field calibration.held_out.accuracy: must be a number from 0 to 1, got '0.9'" "$t/jg-good" jb
bad "$ok_cal"'; s["calibration"]["held_out"]["brier"] = 2.1' "jb/suite.json: field calibration.held_out.brier: must be a number from 0 to 2, got 2.1" "$t/jg-good" jb
bad "$ok_cal"'; s["calibration"]["threshold"]["accuracy_min"] = True' "jb/suite.json: field calibration.threshold.accuracy_min: must be a number from 0 to 1, got True" "$t/jg-good" jb
bad "$ok_cal"'; s["calibration"]["threshold"]["brier_max"] = -0.1' "jb/suite.json: field calibration.threshold.brier_max: must be a number from 0 up, got -0.1" "$t/jg-good" jb
bad "$ok_cal"'; s["calibration"]["threshold"]["accepted"] = "no"' "jb/suite.json: field calibration.threshold.accepted: must be true or false, got 'no'" "$t/jg-good" jb
bad 's["calibration"] = {"evidence": "evidence/jb.md"}' "trig/suite.json: field calibration: only in a judgment suite"
# The one place (EVALS/judgment-model.json, spec judgment#rule-one-model; shape: schema.md, Judgment model and classifiers).
badm() {   # badm PY_EDIT WANT: edit a fresh judgment copy's judgment-model.json (m), expect WANT
  rm -rf "$t/evals"; cp -r "$t/jg-good" "$t/evals"
  python3 -c 'import json,sys; p=sys.argv[1]; m=json.load(open(p)); exec(sys.argv[2]); json.dump(m, open(p, "w"))' "$t/evals/judgment-model.json" "$1"
  run 1 "$C" "$t/evals"; grep -qF "$2" <<< "$out" || fail "model file check missed: want '$2', got: $out"
}
rm -rf "$t/evals"; cp -r "$t/jg-good" "$t/evals"; rm "$t/evals/judgment-model.json"
run 1 "$C" "$t/evals"; grep -qF "$t/evals/judgment-model.json: missing; it holds the kit's one judgment model {model, evidence}" <<< "$out" || fail "no model file: $out"
badm 'del m["model"]' "judgment-model.json: field model: missing"
badm 'del m["evidence"]' "judgment-model.json: field evidence: missing"
badm 'm["why"] = "x"' "judgment-model.json: field why: unknown field"
for m in stub/~x/y stub/p/q-1.2:free; do
  badm 'm["model"] = "'"$m"'"' "judgment-model.json: field model: $m is a moving alias in classifiers.json (owner: stub ruling, tests/qa.sh)"
done
badm 'm["model"] = "stub/ynr"' "judgment-model.json: field model: stub/ynr is yes/no only in classifiers.json (ruling: stub yes/no ruling)"
badm 'm["model"] = "stub/cheap-total"' "judgment-model.json: field model: stub/cheap-total is not in classifiers.json pinned"
for m in stub/p/q-latest stub/m-current; do   # pinned ids named -latest and -current (rule: schema.md, Judgment model and classifiers)
  rm -rf "$t/evals"; cp -r "$t/jg-good" "$t/evals"
  python3 -c 'import json,sys; p=sys.argv[1]; m=json.load(open(p)); m["model"]=sys.argv[2]; json.dump(m, open(p, "w"))' "$t/evals/judgment-model.json" "$m"
  run 0 "$C" "$t/evals"
done
# classifiers.json shape (rule: schema.md, Judgment model and classifiers).
badc() {   # badc PY_EDIT WANT: edit a fresh judgment copy's classifiers.json (o), expect WANT
  rm -rf "$t/evals"; cp -r "$t/jg-good" "$t/evals"
  python3 -c 'import json,sys; p=sys.argv[1]; o=json.load(open(p)); exec(sys.argv[2]); json.dump(o, open(p, "w"))' "$t/evals/classifiers.json" "$1"
  run 1 "$C" "$t/evals"; grep -qF "$2" <<< "$out" || fail "classifiers check missed: want '$2', got: $out"
}
rm -rf "$t/evals"; cp -r "$t/jg-good" "$t/evals"; rm "$t/evals/classifiers.json"
run 1 "$C" "$t/evals"; grep -qF "$t/evals/classifiers.json: missing; it holds every catalogue classifier ruled" <<< "$out" || fail "no classifiers file: $out"
for k in owner moving_alias yes_no_only pinned; do badc 'del o["'$k'"]' "classifiers.json: field $k: missing"; done
badc 'o["why"] = "x"' "classifiers.json: field why: unknown field"
badc 'o["owner"] = " "' "classifiers.json: field owner: must be the ruling's source, one non-empty line"
badc 'o["pinned"]["stub"] = "r"' "classifiers.json: field pinned.stub: must be a classifier <provider>/<id>, got 'stub'"
badc 'o["pinned"]["stub/first"] = " "' "classifiers.json: field pinned.stub/first: must be its pinning ruling's source, one non-empty line"
badc 'o["pinned"] = list(o["pinned"])' "classifiers.json: field pinned: must be an object {<provider>/<id>: its ruling's source}"
badc 'o["moving_alias"] = "stub/~x/y"' "classifiers.json: field moving_alias: must be a list of classifier ids"
badc 'o["pinned"]["stub/~x/y"] = "r"' "classifiers.json: field pinned.stub/~x/y: stub/~x/y already listed in moving_alias"
badc 'o["moving_alias"].append("stub/~x/y")' "classifiers.json: field moving_alias[3]: stub/~x/y already listed in moving_alias"
badc 'o["yes_no_only"] = ["stub/ynr"]' "classifiers.json: field yes_no_only: must be an object {<provider>/<id>: {ruling, error, evidence}}"
badc 'o["yes_no_only"]["stub"] = o["yes_no_only"]["stub/ynr"]' "classifiers.json: field yes_no_only.stub: must be a classifier <provider>/<id>, got 'stub'"
badc 'o["yes_no_only"]["stub/~x/y"] = o["yes_no_only"]["stub/ynr"]' "classifiers.json: field yes_no_only.stub/~x/y: stub/~x/y already listed in moving_alias"
badc 'o["pinned"]["stub/ynr"] = "r"' "classifiers.json: field pinned.stub/ynr: stub/ynr already listed in yes_no_only"
badc 'o["yes_no_only"]["stub/ynr"] = "r"' "classifiers.json: field yes_no_only.stub/ynr: must be an object {ruling, error, evidence}, got 'r'"
for k in ruling error evidence; do
  badc 'del o["yes_no_only"]["stub/ynr"]["'$k'"]' "classifiers.json: field yes_no_only.stub/ynr.$k: missing"
  badc 'o["yes_no_only"]["stub/ynr"]["'$k'"] = " "' "classifiers.json: field yes_no_only.stub/ynr.$k: must be"
done
badc 'o["yes_no_only"]["stub/ynr"]["why"] = "x"' "classifiers.json: field yes_no_only.stub/ynr.why: unknown field"
for m in stub 'stub/' '/x' 'stub/a b' ''; do
  badm 'm["model"] = "'"$m"'"' "judgment-model.json: field model: must be a classifier <provider>/<id>, got '$m'"
done
badm 'm["evidence"] = "evidence/none.md"' "judgment-model.json: field evidence: no file evidence/none.md beside evals/"
echo "qa: ok (PASS/FAIL per case with deciding facts, exit 1/0, train and held-out scores, --sample, role-skill coverage ({tracker} resolved per fixture), --suite/--case, artifacts, stop once decided, dead pi fails, sandbox proof failure fails, refused in a check run, --kit-ref FAIL before and PASS at a kit change with its sha, other repos and the --kit-ref head kit masked (attempt_blocked repo), missing role file named, unknown ref 64, attempt_blocked from the sandbox attempt record (herdr-say called through a variable and herdr both recorded, a delivered message then a failing command not blocked, never attempted, a delivered call after 510 forged refusals fails: the record graded whole), declared pass/outside list/no block/two blocks/stopped early, no lane history bound, role-transcript setup head/branch/origin/fake gh/{repo}{head}, skill load (read, cat; ls, grep, head, truncated), before-targets from filesystem snapshots incl. kit_contract_edit, a target never reached fails, declared_includes pass/missing/not a list, field_lines column-0 only (bullet and fenced fail; none, every, includes, Owner restated, other fields, a two-word field), tool_called (an error or empty result skipped, a named tool's text result passes, none called fails), ran (a run through the sandbox's recording shim matched by argv prefix and {head}, stdin/stdout/exit passed through, an echo or other arguments fail naming the record, a shim only for a named program), branch_paths committed and uncommitted (untouched, touched), exact leak rule, shape check names case and field, judgment bench: per classifier accuracy/calibration/cost train and held-out apart, classifiers.json lists applied (schema.md, Bench; catalogue and --classifier; moving alias and yes/no only skipped, never called), a classifier that cannot accept the question's form listed unavailable with the real question's provider error (no probe), one answering some cases scored, unavailable named, the kit's model beside the best (train) and its threshold, --classifier, best's tie-break, a kit model unscored fails, a dead bench command fails, judgment shape names case and field, labeller record labelled_by/relabel, calibration: evidence file, held_out and threshold shape, judgment suites only, no suite names a model; judgment-model.json and classifiers.json shape (schema.md))"
