#!/usr/bin/env bash
# Integration test for the kit's spend-ledger Pi extension (extensions/spend-ledger.ts, issue #187,
# spec spend#writer-agent): real Pi at the kit's pin (pi-version), headless, against a fake
# OpenAI-compatible provider on 127.0.0.1 whose model has a catalog price (input $1000/M tokens,
# output $2000/M), then `octo-feather-lane spend`. Credential-free: Pi starts from an empty
# environment with an empty HOME, its own PI_CODING_AGENT_DIR and its own state dir; it reads
# nothing of the box's ~/.pi or ledger. Cases:
#   agents      in lane gh149's space (HERDR_WORKSPACE_ID=w37) as implementer: a prompt that calls
#               a tool reporting nested usage (tests/fixtures/spend-ledger/nested-tool.ts), then an
#               answer: 3 calls (2 model messages, 1 tool result), shown under gh149 and
#               implementer with the model, tokens and Pi's cost (spend#acceptance-spend-agents)
#   role-unset  no OCTO_FEATHER_ROLE, no Herdr space: the extension's purpose fallback, no lane
#   pi-role     the implementer role launched through scripts/pi-role (which loads the extension) as
#               a pane launch does, JSON mode, in lane gh149's space, no OCTO_FEATHER_ROLE: its message under
#               gh149 and implementer (spend#writer-agent)
#   headless    pi-role -p (issue #189), no OCTO_FEATHER_ROLE: implementer in lane gh149's space records
#               under gh149 and implementer; code-reviewer in space w99, no lane's, under no lane and
#               code-reviewer (spend#rule-lane, spend#writer-agent)
#   zero-priced fake/free, its catalog rates all 0 (rule: extensions/spend-ledger.ts header, Cost):
#               `spend` shows it at $0, its call counted under unknown cost (spend#rule-cost)
#   qc          `just qc` (scripts/octo-feather-qc, its sandbox) in lane gh149's space, beside a classifier judge
#               call: the judge's message under gh149 and qc-judge, the lane's roles and total in `spend`'s lane and
#               purpose rows (spend#acceptance-spend-agents)
#   unwritable  the ledger is a directory: same answer and exit 0, stderr names the unrecorded spend
#               (spend#rule-write-fails); then the same for the qc run (qc-unwritable): same verdict and exit
#   qa          a `just qa` eval case (role implementer) in no lane: under no lane and implementer (spend#rule-lane)
#   inherited   pi-role agents/implementer.md -p under a parent's inherited OCTO_FEATHER_ROLE=supervisor (a
#               supervisor's headless worker): under gh149 and implementer, no supervisor row (spend#writer-agent)
# One real pi process at a time (the box's Pi load budget). Never skips: without pi, or with pi at
# another version, it fails naming the install command. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
pin="$(tr -d '[:space:]' < "$kit/pi-version")"
install="npm install -g --ignore-scripts @earendil-works/pi-coding-agent@$pin"
command -v pi >/dev/null || { echo "spend-ledger test: pi not on PATH; install Pi $pin: $install" >&2; exit 1; }
v="$(pi --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)"
[[ "$v" == "$pin" ]] || { echo "spend-ledger test: pi reports ${v:-no version}, the kit pins $pin (pi-version); $install" >&2; exit 1; }
L="$kit/scripts/octo-feather-lane"
t="$(mktemp -d)"; srv=""
trap '[[ -z "$srv" ]] || kill "$srv" 2>/dev/null || true; rm -rf "$t"' EXIT
fail() { echo "spend-ledger test: $*" >&2; exit 1; }

# The fake provider: a request whose prompt asks for the tool, and that has no tool result yet,
# gets a nested_work tool call (usage 100 in, 20 out); any other request gets the answer
# fake-answer-ok (usage 150 in, 10 out).
cat > "$t/fake.py" <<'EOF'
import http.server, json, os, re, sys
port_file = sys.argv[1]
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("content-length", 0))))
        msgs = body.get("messages", [])
        tool = "use the tool" in json.dumps(msgs) and not any(m.get("role") == "tool" for m in msgs)
        qc = re.search(r"Repo: .*, head ([0-9a-f]{40})\.", json.dumps(msgs))
        self.send_response(200); self.send_header("content-type", "text/event-stream"); self.end_headers()
        base = {"id": "x", "object": "chat.completion.chunk", "created": 0, "model": "fake"}
        if tool:
            delta = {"role": "assistant", "tool_calls": [{"index": 0, "id": "call_1", "type": "function",
                     "function": {"name": "nested_work", "arguments": "{}"}}]}
            end, usage = "tool_calls", {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120}
        elif qc:   # a qc brief (scripts/octo-feather-qc BRIEF): every criterion it names passes
            ids = re.findall(r"\\n- (acceptance-[a-z0-9-]+): ", json.dumps(msgs))
            crit = [{"id": i, "verdict": "pass", "command": "demo", "output": "ok", "why": "shown"} for i in ids]
            delta = {"role": "assistant", "content": "```json\n" + json.dumps({"head": qc.group(1), "criteria": crit}) + "\n```"}
            end, usage = "stop", {"prompt_tokens": 150, "completion_tokens": 10, "total_tokens": 160}
        else:
            delta = {"role": "assistant", "content": "fake-answer-ok"}
            end, usage = "stop", {"prompt_tokens": 150, "completion_tokens": 10, "total_tokens": 160}
        for d in ({**base, "choices": [{"index": 0, "delta": delta, "finish_reason": None}]},
                  {**base, "choices": [{"index": 0, "delta": {}, "finish_reason": end}], "usage": usage}):
            self.wfile.write(b"data: " + json.dumps(d).encode() + b"\n\n")
        self.wfile.write(b"data: [DONE]\n\n")
s = http.server.HTTPServer(("127.0.0.1", 0), H)
open(port_file + ".tmp", "w").write(str(s.server_address[1])); os.replace(port_file + ".tmp", port_file)
s.serve_forever()
EOF
mkdir -p "$t/home" "$t/agent" "$t/repo"
git -c init.defaultBranch=main init -q "$t/repo"
echo '{"retry":{"enabled":false}}' > "$t/agent/settings.json"
python3 "$t/fake.py" "$t/port" & srv=$!
for _ in $(seq 50); do [[ -s "$t/port" ]] && break; sleep 0.1; done
[[ -s "$t/port" ]] || fail "fake provider did not start"
printf '{"providers":{"fake":{"baseUrl":"http://127.0.0.1:%s/v1","api":"openai-completions","apiKey":"x","models":[{"id":"fake","cost":{"input":1000,"output":2000,"cacheRead":0,"cacheWrite":0}},{"id":"free","cost":{"input":0,"output":0,"cacheRead":0,"cacheWrite":0}}]}}}\n' \
  "$(cat "$t/port")" > "$t/agent/models.json"

state="$t/state/octo-feather"; ledger="$state/spend.jsonl"
mkdir -p "$state/lanes"; printf 'supervisor = "w37:p2"\n' > "$state/lanes/gh149.toml"
# Pi's environment: nothing inherited but PATH and mise's data dir, plus the given variables. mise's data dir as mise
# reports it here: the qc sandbox installs nothing, so the moved HOME must not hide the box's installs (#437).
mdata="$(mise doctor --json | jq -r .dirs.data)"
pienv() { env -i PATH="$PATH" MISE_DATA_DIR="$mdata" HOME="$t/home" TMPDIR="$t" XDG_CACHE_HOME="$t/cache" XDG_STATE_HOME="$t/state" \
  PI_CODING_AGENT_DIR="$t/agent" PI_OFFLINE=1 PI_SKIP_VERSION_CHECK=1 PI_TELEMETRY=0 "$@"; }
# run PROMPT [VAR=VALUE...]: one headless pi with the extension; $out, $rc, stderr in $t/err.
run() {
  local prompt="$1"; shift
  set +e
  out="$(cd "$t/repo" && pienv "$@" pi -e "$kit/extensions/spend-ledger.ts" -e "$kit/tests/fixtures/spend-ledger/nested-tool.ts" \
    --model "${model:-fake/fake}" --no-session -p "$prompt" 2>"$t/err")"; rc=$?
  set -e
}
row() { # OUT TITLE KEY USD CALLS UNKNOWN IN OUT: the KEY row under "By TITLE:" (tests/spend-out)
  local r; r="$("$kit/tests/spend-out" row "${@:2}" <<<"$1")" || fail "$r in: $1"; }
spendcmd=(env -i PATH="$PATH" HOME="$t/home" XDG_STATE_HOME="$t/state" "$L" spend)
spend() { "${spendcmd[@]}"; }
# calls N: wait up to 10 s for `spend` to count N calls in all (the writer runs detached; tests/spend-out).
calls() { local r; r="$("$kit/tests/spend-out" calls "$1" -- "${spendcmd[@]}")" || fail "$r"; }

# agents: 2 model messages (0.1 + 0.04 = $0.14; 0.15 + 0.02 = $0.17) and the tool's $0.004.
run "use the tool, then answer" HERDR_WORKSPACE_ID=w37 OCTO_FEATHER_ROLE=implementer
[[ "$rc" == 0 && "$out" == fake-answer-ok ]] || fail "agents: exit $rc, answer '$out': $(cat "$t/err")"
calls 3
s="$(spend)"
row "$s" lane gh149 0.314000 3 0 257 33
row "$s" purpose implementer 0.314000 3 0 257 33
row "$s" model fake/fake 0.310000 2 0 250 30
row "$s" model tool/nested_work 0.004000 1 0 7 3
echo "case agents: ok (3 calls under gh149 and implementer: fake/fake \$0.31 250 in 30 out, tool/nested_work \$0.004 7 in 3 out)"

# role-unset: purpose agent, no lane.
run "answer"
[[ "$rc" == 0 && "$out" == fake-answer-ok ]] || fail "role-unset: exit $rc, answer '$out': $(cat "$t/err")"
calls 4
s="$(spend)"
row "$s" lane '(no lane)' 0.170000 1 0 150 10
row "$s" purpose agent 0.170000 1 0 150 10
echo "case role-unset: ok (purpose agent, no lane)"

# pi-role: no -e here; pi-role loads the extension. Not -p: a headless pi-role run drops the Herdr
# space (scripts/pi-role HEADLESS_UNSET), a pane launch keeps it. No OCTO_FEATHER_ROLE: the role file names the purpose.
set +e
out="$(cd "$t/repo" && pienv HERDR_WORKSPACE_ID=w37 "$kit/scripts/pi-role" "$kit/agents/implementer.md" --model fake/fake \
  --no-session --mode json "answer" 2>"$t/err")"; rc=$?
set -e
[[ "$rc" == 0 && "$out" == *fake-answer-ok* ]] || fail "pi-role: exit $rc: $(cat "$t/err")"
calls 5
s="$(spend)"
row "$s" lane gh149 0.484000 4 0 407 43
row "$s" purpose implementer 0.484000 4 0 407 43
row "$s" model fake/fake 0.650000 4 0 550 50
echo "case pi-role: ok (pi-role launch recorded under gh149 and implementer)"

# headless: pi-role -p drops HERDR_WORKSPACE_ID (#77); the spend still finds the lane. No OCTO_FEATHER_ROLE.
headless() { local space="$1" role="$2"; shift 2
  set +e
  out="$(cd "$t/repo" && pienv HERDR_WORKSPACE_ID="$space" "$@" "$kit/scripts/pi-role" "$kit/agents/$role.md" --model fake/fake \
    --no-session -p "answer" 2>"$t/err")"; rc=$?
  set -e
  [[ "$rc" == 0 && "$out" == fake-answer-ok ]] || fail "headless $role: exit $rc, answer '$out': $(cat "$t/err")"; }
headless w37 implementer
calls 6
s="$(spend)"
row "$s" lane gh149 0.654000 5 0 557 53
row "$s" purpose implementer 0.654000 5 0 557 53
headless w99 code-reviewer
calls 7
s="$(spend)"
row "$s" lane '(no lane)' 0.340000 2 0 300 20
row "$s" purpose code-reviewer 0.170000 1 0 150 10
row "$s" lane gh149 0.654000 5 0 557 53
echo "case headless: ok (implementer in w37 under gh149 and implementer; code-reviewer in w99 under no lane and code-reviewer)"

# zero-priced: fake/free answers with the same usage (150 in, 10 out); Pi reports $0, spend counts it as unknown cost.
model=fake/free run "answer" HERDR_WORKSPACE_ID=w37 OCTO_FEATHER_ROLE=implementer
[[ "$rc" == 0 && "$out" == fake-answer-ok ]] || fail "zero-priced: exit $rc, answer '$out': $(cat "$t/err")"
calls 8
s="$(spend)"
row "$s" model fake/free 0.000000 1 1 150 10
row "$s" lane gh149 0.654000 6 1 707 63
row "$s" model fake/fake 0.990000 6 0 850 70
echo "case zero-priced: ok (fake/free: \$0.000000, 1 call of unknown cost, 150 in 10 out; fake/fake priced as before)"

# qc: the product judge's run in its sandbox (scripts/octo-feather-qc), in lane gh149's space, beside the lane's
# implementer spend above and a classifier judge call: its one message (150 in, 10 out, $0.17) under gh149 and qc-judge
# (spec spend#acceptance-spend-agents; how: scripts/octo-feather-qc record_spend). Linux only (the sandbox needs unshare), as tests/qc.sh.
sandbox=1; [[ "$(uname -s)" != Darwin ]] || { sandbox=0; echo "cases qc, qa: skipped, not on macOS (the qc sandbox needs Linux; CI runs them)"; }
qcrepo="$t/qcrepo"; mkdir -p "$qcrepo/docs/specs" "$t/home/.pi"; cp -r "$t/agent" "$t/home/.pi/agent"   # under HOME: kept in the sandbox
cp "$kit/tests/fixtures/spec-status/good/demo.spec.html" "$qcrepo/docs/specs/"
gitenv=(GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t)
(cd "$qcrepo" && git init -q -b main && git add -A && env "${gitenv[@]}" git commit -qm spec \
  && "$kit/scripts/octo-feather-spec-status" init docs/specs/demo.spec.html "$(git rev-parse --short HEAD)" >/dev/null \
  && git add -A && env "${gitenv[@]}" git commit -qm status)
# qc SPACE: one `just qc` of acceptance-a; $out, $rc, stderr in $t/err.
qc() { set +e
  out="$(cd "$qcrepo" && pienv HERDR_WORKSPACE_ID="$1" PI_CODING_AGENT_DIR="$t/home/.pi/agent" OCTO_FEATHER_QC_MODEL=fake/fake "${gitenv[@]}" \
    "$kit/scripts/octo-feather-qc" docs/specs/demo.status.json 5 acceptance-a 2>"$t/err")"; rc=$?
  set -e; }
if ((sandbox)); then
  printf '{"model":"openrouter/typesafe/jev-1.13","purpose":"judge","input_tokens":500,"output_tokens":40,"cost_usd":0.0001}\n' |
    env -i PATH="$PATH" HOME="$t/home" XDG_STATE_HOME="$t/state" HERDR_WORKSPACE_ID=w37 "$L" spend record
  qc w37
  [[ "$rc" == 0 && "$out" == *"PASS acceptance-a"* ]] || fail "qc: exit $rc: $out $(tail -20 "$t/err")"
  calls 10
  s="$(spend)"
  row "$s" 'lane and purpose' 'gh149 qc-judge' 0.170000 1 0 150 10
  row "$s" 'lane and purpose' 'gh149 implementer' 0.654000 6 1 707 63
  row "$s" 'lane and purpose' 'gh149 judge' 0.000100 1 0 500 40
  row "$s" lane gh149 0.824100 8 1 1357 113
  echo "case qc: ok (the judge's call under gh149 and qc-judge, beside gh149 implementer and judge, lane gh149 \$0.8241)"
fi

# unwritable: the ledger path is a directory.
mv "$ledger" "$t/ledger.bak"; mkdir "$ledger"
run "answer" HERDR_WORKSPACE_ID=w37 OCTO_FEATHER_ROLE=implementer
[[ "$rc" == 0 && "$out" == fake-answer-ok ]] || fail "unwritable: exit $rc, answer '$out' (want 0 and fake-answer-ok)"
want='octo-feather-lane spend record: spend unrecorded (1 call(s), $0.170000): cannot write'
for _ in $(seq 100); do grep -qF "$want" "$t/err" && break; sleep 0.1; done
grep -qF "$want" "$t/err" || fail "unwritable: stderr lacks '$want': $(cat "$t/err")"
echo "case unwritable: ok (exit 0, fake-answer-ok, stderr: $(grep -F "$want" "$t/err" | head -1))"
# qc-unwritable: the same qc run with the ledger unwritable: the same verdict and exit, stderr names the unrecorded call
# (spec spend#rule-write-fails).
if ((sandbox)); then
  qc w37
  [[ "$rc" == 0 && "$out" == *"PASS acceptance-a"* ]] || fail "qc-unwritable: exit $rc (want 0 and PASS acceptance-a): $out"
  grep -qF "$want" "$t/err" || fail "qc-unwritable: stderr lacks '$want': $(cat "$t/err")"
  echo "case qc-unwritable: ok (exit 0, PASS acceptance-a, stderr: $(grep -F "$want" "$t/err" | head -1))"
fi
rm -r "$ledger"; mv "$t/ledger.bak" "$ledger"

# qa: a factory eval case (role implementer) run by `just qa` (scripts/octo-feather-qa) outside any lane: its call
# under no lane and implementer (spec spend#rule-lane).
if ((sandbox)); then
  ev="$t/evals"; mkdir -p "$ev/one/reference" "$ev/fixtures/fx"; echo fixture > "$ev/fixtures/fx/README.md"
  echo '{"suite": "one", "kind": "skill-trigger", "description": "spend", "max_tool_calls": 5, "timeout_s": 120}' > "$ev/one/suite.json"
  echo '[{"id": "look", "role": "implementer", "fixture": "fx", "should_trigger": false, "split": "train", "task": "Only look."}]' > "$ev/one/cases.json"
  echo '{"look": {"facts": [{"fact": "skill_not_read", "skill": "tdd"}]}}' > "$ev/one/reference/expectations.json"
  set +e
  out="$(cd "$t/repo" && pienv PI_CODING_AGENT_DIR="$t/home/.pi/agent" OCTO_FEATHER_QA_DIR="$t/qa" "${gitenv[@]}" \
    "$kit/scripts/octo-feather-qa" --evals "$ev" --model fake/fake 2>"$t/err")"; rc=$?
  set -e
  [[ "$rc" == 0 && "$out" == *"PASS one/look"* ]] || fail "qa: exit $rc: $out $(tail -20 "$t/err")"
  calls 11
  s="$(spend)"
  row "$s" 'lane and purpose' '(no lane) implementer' 0.170000 1 0 150 10
  row "$s" lane gh149 0.824100 8 1 1357 113
  echo "case qa: ok (the eval case's call under no lane and implementer)"
fi

# inherited: a supervisor's headless worker keeps the parent's OCTO_FEATHER_ROLE=supervisor; the role pi-role launches
# wins (spend#writer-agent). One more fake/fake answer (150 in, 10 out, $0.17) on gh149 implementer's 6 calls.
headless w37 implementer OCTO_FEATHER_ROLE=supervisor
calls $((sandbox ? 12 : 9))
s="$(spend)"
row "$s" 'lane and purpose' 'gh149 implementer' 0.824000 7 1 857 73
! grep -q supervisor <<<"$s" || fail "inherited: a supervisor row: $s"
echo "case inherited: ok (pi-role implementer -p under inherited OCTO_FEATHER_ROLE=supervisor: under gh149 and implementer)"
echo "spend-ledger: ok (pi $v, empty HOME and environment, no provider credential)"
