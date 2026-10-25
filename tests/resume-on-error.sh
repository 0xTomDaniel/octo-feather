#!/usr/bin/env bash
# Integration test for the kit's Pi extension on a run stopped by a provider error (issue #152,
# docs/adr/0023): real Pi, at the kit's pin (pi-version), launched through scripts/pi-role, against
# a fake OpenAI-compatible provider on 127.0.0.1 (503 for its first N requests, then an answer), a
# fake herdr-say first on PATH as the parent recorder. A pane is driven as Pi's RPC mode (stdin
# commands, stdout events); headless is pi-role -p. Credential-free: Pi starts from an empty
# environment (no provider key variables) with an empty HOME and its own PI_CODING_AGENT_DIR
# (Pi's retries off); it reads nothing of the box's ~/.pi. Cases:
#   recovers  2 errors then an answer: resumed twice, finished, parent not messaged
#   down      errors throughout: 3 resume rounds then stop; exactly one --parent line naming
#             agent, pane, error and "stopped"
#   normal    an answer: one request, no resume, nothing sent
#   idle      mid-backoff Pi is idle (get_state isStreaming false), an abort is answered at once and
#             Pi stays usable; the resume still fires after the backoff (docs/adr/0023 Takeover)
#   takeover  a prompt sent mid-backoff runs at once; no scheduled resume follows, nothing sent
#   headless  pi-role -p, errors throughout: exits non-zero promptly, no resume, nothing sent
# Cases run one after another, one real pi process at a time: each case's pi has exited before the
# next starts (the box's Pi load budget). Never skips: without pi, or with pi at another version, it fails naming the install command.
# Run by `just check` (CI installs Pi at the pin first).
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
pin="$(tr -d '[:space:]' < "$kit/pi-version")"
install="npm install -g --ignore-scripts @earendil-works/pi-coding-agent@$pin"
command -v pi >/dev/null || { echo "resume-on-error test: pi not on PATH; install Pi $pin: $install" >&2; exit 1; }
v="$(pi --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)"
[[ "$v" == "$pin" ]] || { echo "resume-on-error test: pi reports ${v:-no version}, the kit pins $pin (pi-version); $install" >&2; exit 1; }
t="$(mktemp -d)"; srv=""
trap '[[ -z "$srv" ]] || kill "$srv" 2>/dev/null || true; rm -rf "$t"' EXIT
fail() { echo "resume-on-error test: $*" >&2; exit 1; }

cat > "$t/fake.py" <<'EOF'
import http.server, json, os, sys
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
open(port_file + ".tmp", "w").write(str(s.server_address[1])); os.replace(port_file + ".tmp", port_file)
s.serve_forever()
EOF

# The pane driver: Pi in RPC mode through pi-role. argv: case, then the pi-role command.
# Exits non-zero naming what failed; prints one detail line on success.
cat > "$t/rpc.py" <<'EOF'
import json, os, queue, subprocess, sys, threading, time
case, cmd, requests_file = sys.argv[1], sys.argv[3:], sys.argv[2]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
events, seen = queue.Queue(), []
def pump():
    for line in p.stdout:
        try: events.put(json.loads(line))
        except ValueError: pass
threading.Thread(target=pump, daemon=True).start()
def die(msg): p.kill(); p.wait(); print(f"{case}: {msg}", file=sys.stderr); sys.exit(1)
def send(o): p.stdin.write(json.dumps(o) + "\n"); p.stdin.flush()
def wait(pred, secs, what):
    end = time.time() + secs
    while time.time() < end:
        try: e = events.get(timeout=max(0.01, end - time.time()))
        except queue.Empty: break
        seen.append(e)
        if pred(e): return e
    die(f"timed out waiting for {what}")
def drain(secs):
    end = time.time() + secs
    while time.time() < end:
        try: seen.append(events.get(timeout=max(0.01, end - time.time())))
        except queue.Empty: pass
def requests(): return sum(1 for _ in open(requests_file))
settled = lambda e: e.get("type") == "agent_settled"
resumed = lambda: sum(1 for e in seen if e.get("type") == "message_end" and e.get("message", {}).get("customType") == "octo-feather-resume")
answered = lambda: any(e.get("type") == "message_end" and "fake-answer-ok" in json.dumps(e.get("message", {})) for e in seen)
def response(cmd): return lambda e: e.get("type") == "response" and e.get("command") == cmd

send({"type": "prompt", "message": "do the task"})
if case == "recovers":
    wait(lambda e: settled(e) and answered(), 30, "a settle after the provider's answer")
    drain(1)
    if requests() != 3 or resumed() != 2: die(f"{requests()} requests, {resumed()} resumes; want 3 and 2")
    print("2 provider errors, 2 resumes, finished")
elif case == "down":
    for _ in range(4): wait(settled, 30, "an error settle")
    drain(2.5)
    if requests() != 4 or resumed() != 3: die(f"{requests()} requests, {resumed()} resumes; want 4 and 3 (no 4th round)")
    print("4 requests, 3 resumes, then stopped")
elif case == "normal":
    wait(settled, 30, "the settle")
    drain(1.5)
    if requests() != 1 or resumed() or not answered(): die(f"{requests()} requests, {resumed()} resumes; want 1 answered and 0")
    print("1 request, no resume")
elif case == "idle":
    wait(settled, 30, "the error settle")
    t0 = time.time(); send({"type": "get_state", "id": "s"})
    st = wait(response("get_state"), 2, "get_state")
    if st.get("data", {}).get("isStreaming") is not False: die(f"Pi busy mid-backoff: {st}")
    send({"type": "abort", "id": "a"})
    ab = wait(response("abort"), 2, "the abort response")
    dt = time.time() - t0
    if not ab.get("success") or dt > 1.5: die(f"abort mid-backoff: {ab} after {dt:.2f}s")
    send({"type": "get_state", "id": "s2"})
    st = wait(response("get_state"), 2, "get_state after the abort")
    if st.get("data", {}).get("isStreaming") is not False: die(f"Pi not usable after the abort: {st}")
    wait(settled, 6, "the resume run's settle after the 3 s backoff")
    drain(0.5)
    if requests() != 2 or resumed() != 1: die(f"after the backoff: {requests()} requests, {resumed()} resumes; want 2 and 1")
    print(f"mid-backoff isStreaming false, abort answered in {dt:.2f}s, Pi usable; resume fired after the backoff")
elif case == "takeover":
    wait(settled, 30, "the error settle")
    t0 = time.time(); time.sleep(0.5)
    send({"type": "prompt", "message": "the parent takes over"})
    wait(lambda e: settled(e) and answered(), 10, "the takeover prompt's answer")
    dt = time.time() - t0
    if requests() != 2 or dt > 2.5: die(f"takeover: {requests()} requests after {dt:.2f}s; want 2 within the 3 s backoff")
    drain(max(0, 5 - (time.time() - t0)))
    if requests() != 2 or resumed(): die(f"after the backoff: {requests()} requests, {resumed()} resumes; want 2 and 0")
    print(f"takeover answered {dt:.2f}s after the error, no resume after the 3 s backoff")
p.stdin.close(); p.terminate()
try: p.wait(5)
except subprocess.TimeoutExpired: p.kill()
EOF
mkdir -p "$t/bin" "$t/home" "$t/agent" "$t/repo"
printf '#!/usr/bin/env bash\nprintf "%%s\\n" "$*" >> "%s/said"\n' "$t" > "$t/bin/herdr-say"; chmod +x "$t/bin/herdr-say"
git -c init.defaultBranch=main init -q "$t/repo"
echo '{"retry":{"enabled":false}}' > "$t/agent/settings.json"

# provider FAIL_N: restart the fake provider failing its first FAIL_N requests (-1: always).
provider() {
  [[ -z "$srv" ]] || kill "$srv" 2>/dev/null || true
  rm -f "$t/port" "$t/said"; : > "$t/requests"
  python3 "$t/fake.py" "$t/port" "$1" "$t/requests" & srv=$!
  for _ in $(seq 50); do [[ -s "$t/port" ]] && break; sleep 0.1; done
  [[ -s "$t/port" ]] || fail "fake provider did not start"
  printf '{"providers":{"fake":{"baseUrl":"http://127.0.0.1:%s/v1","api":"openai-completions","apiKey":"x","models":[{"id":"fake"}]}}}\n' \
    "$(cat "$t/port")" > "$t/agent/models.json"
}
# Pi's environment: nothing inherited but PATH (the fake herdr-say first), as a pane launch has it
# (parent route set) unless ROUTE is emptied.
pienv() { env -i PATH="$t/bin:$PATH" HOME="$t/home" TMPDIR="$t" XDG_CACHE_HOME="$t/cache" PI_CODING_AGENT_DIR="$t/agent" \
  PI_OFFLINE=1 PI_SKIP_VERSION_CHECK=1 PI_TELEMETRY=0 OCTO_FEATHER_ROLE=implementer OCTO_FEATHER_PARENT=fake:p1 HERDR_PANE_ID=fake:p9 "$@"; }
role=("$kit/scripts/pi-role" "$kit/agents/implementer.md" --model fake/fake --no-session)
# pane CASE DELAYS: the RPC driver; detail line in $detail.
pane() { detail="$(cd "$t/repo" && pienv OCTO_FEATHER_RESUME_DELAYS="$2" python3 "$t/rpc.py" "$1" "$t/requests" "${role[@]}" --mode rpc 2>&1)" \
  || fail "$detail"; }
said_after() { for _ in $(seq "$(($1 * 10))"); do [[ -s "$t/said" ]] && break; sleep 0.1; done; }

provider 2; pane recovers 0.3,0.6,0.9
said_after 1; [[ ! -s "$t/said" ]] || fail "recovers: parent was messaged: $(cat "$t/said")"
echo "case recovers: ok ($detail, parent not messaged)"

provider -1; pane down 0.3,0.6,0.9
said_after 3; [[ -s "$t/said" ]] || fail "down: parent got no message"
sleep 0.5
[[ "$(wc -l < "$t/said")" == 1 ]] || fail "down: want exactly one message, got: $(cat "$t/said")"
line="$(cat "$t/said")"
for w in "--parent " implementer fake:p9 "fake upstream overloaded" stopped; do
  [[ "$line" == *"$w"* ]] || fail "down: message lacks '$w': $line"
done
echo "case down: ok ($detail; one parent line: $line)"

provider 0; pane normal 0.3,0.6,0.9
said_after 1; [[ ! -s "$t/said" ]] || fail "normal: parent was messaged: $(cat "$t/said")"
echo "case normal: ok ($detail, parent not messaged)"

provider -1; pane idle 3,30
said_after 1; [[ ! -s "$t/said" ]] || fail "idle: parent was messaged: $(cat "$t/said")"
echo "case idle: ok ($detail)"

provider 1; pane takeover 3
said_after 1; [[ ! -s "$t/said" ]] || fail "takeover: parent was messaged: $(cat "$t/said")"
echo "case takeover: ok ($detail, parent not messaged)"

provider -1; s=$SECONDS
set +e; (cd "$t/repo" && pienv "${role[@]}" -p "do the task" >/dev/null 2>&1); rc=$?; set -e
dt=$((SECONDS - s))
[[ "$rc" != 0 ]] || fail "headless: exit 0 on a provider that keeps failing"
[[ "$dt" -le 10 && "$(wc -l < "$t/requests")" == 1 ]] || fail "headless: ${dt}s, $(wc -l < "$t/requests") requests; want <= 10 s and 1 (no kit resume)"
said_after 1; [[ ! -s "$t/said" ]] || fail "headless: herdr-say ran: $(cat "$t/said")"
echo "case headless: ok (pi-role -p exit $rc in ${dt}s, 1 request, no resume, nothing sent)"
echo "resume-on-error: ok (pi $v, empty HOME and environment, no provider credential)"
