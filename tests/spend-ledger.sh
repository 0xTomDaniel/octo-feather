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
#               a pane launch does (herdr-spawn's role env), JSON mode, in lane gh149's space: its message under gh149 and
#               implementer
#   zero-priced fake/free, its catalog rates all 0 (rule: extensions/spend-ledger.ts header, Cost):
#               `spend` shows it at $0, its call counted under unknown cost (spend#rule-cost)
#   unwritable  the ledger is a directory: same answer and exit 0, stderr names the unrecorded spend
#               (spend#rule-write-fails)
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
import http.server, json, os, sys
port_file = sys.argv[1]
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("content-length", 0))))
        msgs = body.get("messages", [])
        tool = "use the tool" in json.dumps(msgs) and not any(m.get("role") == "tool" for m in msgs)
        self.send_response(200); self.send_header("content-type", "text/event-stream"); self.end_headers()
        base = {"id": "x", "object": "chat.completion.chunk", "created": 0, "model": "fake"}
        if tool:
            delta = {"role": "assistant", "tool_calls": [{"index": 0, "id": "call_1", "type": "function",
                     "function": {"name": "nested_work", "arguments": "{}"}}]}
            end, usage = "tool_calls", {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120}
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
# Pi's environment: nothing inherited but PATH, plus the given variables.
pienv() { env -i PATH="$PATH" HOME="$t/home" TMPDIR="$t" XDG_CACHE_HOME="$t/cache" XDG_STATE_HOME="$t/state" \
  PI_CODING_AGENT_DIR="$t/agent" PI_OFFLINE=1 PI_SKIP_VERSION_CHECK=1 PI_TELEMETRY=0 "$@"; }
# run PROMPT [VAR=VALUE...]: one headless pi with the extension; $out, $rc, stderr in $t/err.
run() {
  local prompt="$1"; shift
  set +e
  out="$(cd "$t/repo" && pienv "$@" pi -e "$kit/extensions/spend-ledger.ts" -e "$kit/tests/fixtures/spend-ledger/nested-tool.ts" \
    --model "${model:-fake/fake}" --no-session -p "$prompt" 2>"$t/err")"; rc=$?
  set -e
}
row() { # OUT TITLE KEY USD CALLS UNKNOWN IN OUT: the KEY row under "By TITLE:"
  awk -v t="By $2:" '$0==t{on=1;next} /^By |^OpenRouter/{on=0} on' <<<"$1" |
    grep -qE "^  $3 +\\\$$4 +calls +$5 +unknown cost +$6 +tokens in $7 out $8\$" || fail "no $2 row '$3 \$$4 calls $5 unknown $6 in $7 out $8' in: $1"
}
spend() { env -i PATH="$PATH" HOME="$t/home" XDG_STATE_HOME="$t/state" "$L" spend; }
# total: the calls `spend` counts in all, from its "Spend ledger: PATH (N calls)" header; 0 before any.
total() { spend 2>/dev/null | sed -nE '1s/^Spend ledger: .* \(([0-9]+) calls?\)$/\1/p' | grep . || echo 0; }
# calls N: wait up to 10 s for `spend` to count N calls in all (the writer runs detached).
calls() { for _ in $(seq 100); do [[ "$(total)" -ge "$1" ]] && break; sleep 0.1; done
  sleep 0.3; local n; n="$(total)"
  [[ "$n" == "$1" ]] || fail "spend counts $n calls, want $1: $(spend 2>&1)"; }

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
row "$s" lane '\(no lane\)' 0.170000 1 0 150 10
row "$s" purpose agent 0.170000 1 0 150 10
echo "case role-unset: ok (purpose agent, no lane)"

# pi-role: no -e here; pi-role loads the extension. Not -p: a headless pi-role run drops the Herdr
# space (scripts/pi-role HEADLESS_UNSET), a pane launch keeps it. OCTO_FEATHER_ROLE as herdr-spawn sets it.
set +e
out="$(cd "$t/repo" && pienv HERDR_WORKSPACE_ID=w37 OCTO_FEATHER_ROLE=implementer "$kit/scripts/pi-role" "$kit/agents/implementer.md" --model fake/fake \
  --no-session --mode json "answer" 2>"$t/err")"; rc=$?
set -e
[[ "$rc" == 0 && "$out" == *fake-answer-ok* ]] || fail "pi-role: exit $rc: $(cat "$t/err")"
calls 5
s="$(spend)"
row "$s" lane gh149 0.484000 4 0 407 43
row "$s" purpose implementer 0.484000 4 0 407 43
row "$s" model fake/fake 0.650000 4 0 550 50
echo "case pi-role: ok (pi-role launch recorded under gh149 and implementer)"

# zero-priced: fake/free answers with the same usage (150 in, 10 out); Pi reports $0, spend counts it as unknown cost.
model=fake/free run "answer" HERDR_WORKSPACE_ID=w37 OCTO_FEATHER_ROLE=implementer
[[ "$rc" == 0 && "$out" == fake-answer-ok ]] || fail "zero-priced: exit $rc, answer '$out': $(cat "$t/err")"
calls 6
s="$(spend)"
row "$s" model fake/free 0.000000 1 1 150 10
row "$s" lane gh149 0.484000 5 1 557 53
row "$s" model fake/fake 0.650000 4 0 550 50
echo "case zero-priced: ok (fake/free: \$0.000000, 1 call of unknown cost, 150 in 10 out; fake/fake priced as before)"

# unwritable: the ledger path is a directory.
mv "$ledger" "$t/ledger.bak"; mkdir "$ledger"
run "answer" HERDR_WORKSPACE_ID=w37 OCTO_FEATHER_ROLE=implementer
[[ "$rc" == 0 && "$out" == fake-answer-ok ]] || fail "unwritable: exit $rc, answer '$out' (want 0 and fake-answer-ok)"
want='octo-feather-lane spend record: spend unrecorded (1 call(s), $0.170000): cannot write'
for _ in $(seq 100); do grep -qF "$want" "$t/err" && break; sleep 0.1; done
grep -qF "$want" "$t/err" || fail "unwritable: stderr lacks '$want': $(cat "$t/err")"
echo "case unwritable: ok (exit 0, fake-answer-ok, stderr: $(grep -F "$want" "$t/err" | head -1))"
echo "spend-ledger: ok (pi $v, empty HOME and environment, no provider credential)"
