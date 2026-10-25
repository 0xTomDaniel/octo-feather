#!/usr/bin/env bash
# Integration test for the kit's Pi extension on a run stopped by a provider error (issue #152):
# real Pi launched through scripts/pi-role, against a fake OpenAI-compatible provider on localhost
# (503 for its first N requests, then a normal answer), a fake herdr-say first on PATH as the
# parent recorder. Isolated: temp HOME and PI_CODING_AGENT_DIR (Pi's own retries off), no live
# Herdr, no network. Cases:
#   recovers  provider fails twice then answers: the run continues and finishes, nothing sent
#   down      provider keeps failing: 3 resume rounds then stop; exactly one --parent line naming
#             agent, pane, error and "stopped"
#   normal    provider answers: one request, no continuation, nothing sent
#   headless  pi-role -p, provider keeps failing: exit non-zero, nothing sent
# Without pi on PATH (CI) it skips with a notice. Run by `just check`.
set -euo pipefail
command -v pi >/dev/null || { echo "resume-on-error: skipped, no pi on PATH (the kit gate in CI has none)"; exit 0; }
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; srv=""
trap '[[ -z "$srv" ]] || kill "$srv" 2>/dev/null || true; rm -rf "$t"' EXIT
fail() { echo "resume-on-error test: $*" >&2; tail -c 1500 "$t/out" "$t/err" >&2; exit 1; }

cat > "$t/fake.py" <<'EOF'
import http.server, json, sys
port_file, fail, log = sys.argv[1], int(sys.argv[2]), sys.argv[3]
n = 0
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        global n
        self.rfile.read(int(self.headers.get("content-length", 0)))
        n += 1
        with open(log, "a") as f: f.write("request\n")
        if fail < 0 or n <= fail:
            b = json.dumps({"error": {"message": "fake upstream overloaded", "type": "overloaded_error"}}).encode()
            self.send_response(503); self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(b))); self.end_headers(); self.wfile.write(b); return
        self.send_response(200); self.send_header("content-type", "text/event-stream"); self.end_headers()
        base = {"id": "x", "object": "chat.completion.chunk", "created": 0, "model": "fake"}
        for d in ({**base, "choices": [{"index": 0, "delta": {"role": "assistant", "content": "fake-answer-ok"}, "finish_reason": None}]},
                  {**base, "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}):
            self.wfile.write(b"data: " + json.dumps(d).encode() + b"\n\n")
        self.wfile.write(b"data: [DONE]\n\n")
s = http.server.HTTPServer(("127.0.0.1", 0), H)
open(port_file + ".tmp", "w").write(str(s.server_address[1]))
import os; os.replace(port_file + ".tmp", port_file)
s.serve_forever()
EOF
mkdir -p "$t/bin" "$t/home" "$t/agent" "$t/repo"
printf '#!/usr/bin/env bash\nprintf "%%s\\n" "$*" >> "%s/said"\n' "$t" > "$t/bin/herdr-say"; chmod +x "$t/bin/herdr-say"
git -c init.defaultBranch=main init -q "$t/repo"
echo '{"retry":{"enabled":false}}' > "$t/agent/settings.json"

# provider FAIL_N: restart the fake provider failing its first FAIL_N requests (-1: always).
provider() {
  [[ -z "$srv" ]] || kill "$srv" 2>/dev/null || true
  rm -f "$t/port" "$t/requests" "$t/said"; : > "$t/requests"
  python3 "$t/fake.py" "$t/port" "$1" "$t/requests" & srv=$!
  for _ in $(seq 50); do [[ -s "$t/port" ]] && break; sleep 0.1; done
  [[ -s "$t/port" ]] || fail "fake provider did not start"
  printf '{"providers":{"fake":{"baseUrl":"http://127.0.0.1:%s/v1","api":"openai-completions","apiKey":"x","models":[{"id":"fake"}]}}}\n' \
    "$(cat "$t/port")" > "$t/agent/models.json"
}
# run MODE...: the implementer through pi-role as a pane launch would have it (parent route set);
# stdout in $t/out, exit code in $rc.
run() {
  set +e
  (cd "$t/repo" && env HOME="$t/home" PI_CODING_AGENT_DIR="$t/agent" PI_OFFLINE=1 PI_SKIP_VERSION_CHECK=1 \
    XDG_CACHE_HOME="$t/cache" PATH="$t/bin:$PATH" OCTO_FEATHER_RESUME_DELAYS=0.2,0.4,0.6 \
    OCTO_FEATHER_ROLE=implementer OCTO_FEATHER_PARENT=fake:p1 HERDR_PANE_ID=fake:p9 \
    timeout 120 "$kit/scripts/pi-role" "$kit/agents/implementer.md" --model fake/fake --no-session "$@" >"$t/out" 2>"$t/err")
  rc=$?; set -e
}
requests() { wc -l < "$t/requests" | tr -d ' '; }
# said_after SECS: herdr-say runs detached after Pi settles; wait for it up to SECS.
said_after() { for _ in $(seq "$(($1 * 10))"); do [[ -s "$t/said" ]] && break; sleep 0.1; done; }

provider 2; run --mode json "do the task"
[[ "$rc" == 0 ]] || fail "recovers: exit $rc: $(tail -3 "$t/err")"
grep -q fake-answer-ok "$t/out" || fail "recovers: the run did not finish with the provider's answer"
[[ "$(requests)" == 3 ]] || fail "recovers: $(requests) provider requests, want 3 (2 failed, 1 answered)"
said_after 2; [[ ! -s "$t/said" ]] || fail "recovers: parent was messaged: $(cat "$t/said")"
echo "case recovers: ok (2 provider errors, resumed, finished, exit 0, parent not messaged)"

provider -1; run --mode json "do the task"
[[ "$(requests)" == 4 ]] || fail "down: $(requests) provider requests, want 4 (1 + 3 resume rounds)"
said_after 5; [[ -s "$t/said" ]] || fail "down: parent got no message"
sleep 1
[[ "$(wc -l < "$t/said")" == 1 ]] || fail "down: want exactly one message, got: $(cat "$t/said")"
line="$(cat "$t/said")"
for w in "--parent " implementer fake:p9 "fake upstream overloaded" stopped; do
  [[ "$line" == *"$w"* ]] || fail "down: message lacks '$w': $line"
done
echo "case down: ok (4 requests then stop; one parent line: $line)"

provider 0; run --mode json "do the task"
[[ "$rc" == 0 && "$(requests)" == 1 ]] || fail "normal: exit $rc, $(requests) requests, want 0 and 1"
! grep -q octo-feather-resume "$t/out" || fail "normal: a resume continuation was made"
said_after 2; [[ ! -s "$t/said" ]] || fail "normal: parent was messaged: $(cat "$t/said")"
echo "case normal: ok (1 request, no continuation, parent not messaged)"

provider -1; run -p "do the task"
[[ "$rc" != 0 ]] || fail "headless: exit 0 on a provider that keeps failing"
said_after 3; [[ ! -s "$t/said" ]] || fail "headless: herdr-say ran: $(cat "$t/said")"
echo "case headless: ok (pi-role -p exit $rc after $(requests) requests, nothing sent)"
echo "resume-on-error: ok"
