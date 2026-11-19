#!/usr/bin/env bash
# gate: e2e
# Integration test for the kit's results-on-wake Pi extension (extensions/results-on-wake.ts; comms spec #roles-goal,
# #1013): real Pi, at the kit's pin (pi-version), launched as the supervisor through scripts/pi-role in RPC mode (a
# pane launch), against the testkit's model provider (tests/gate/kit/testkit/provider.py, logging each request) and
# the testkit's Herdr (tests/gate/kit/testkit/herdr.py, its FAKE_HERDR world: implementer-gh7 live at w1:p2). Lane
# gh7's record names the supervisor w1:p1; its hand-off log holds implementer-gh7's spawn line (session S7) and its
# result file sits in lanes/gh7.results/S7.md. Cases:
#   start     the first run after the session starts: its request holds the listing, naming S7.md
#   once      the next run: no second listing
#   compact   after a compaction (RPC compact), the first run's request holds the listing again
#   no log    the same launch at a pane owning no lane record (HERDR_PANE_ID w9:p9): no listing
#   implementer  an implementer launch at that supervisor pane: its role file loads no results-on-wake.ts
#             (spec roles#fm-extensions; only the director and the supervisor do), so no listing
#   none      the caller's log holds no outstanding worker: no listing
# Pi starts from an empty environment (env -i), its own HOME and agent dir; no call leaves the test. Never skips:
# without pi at the pin it fails naming the install command. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
pin="$(tr -d '[:space:]' < "$kit/pi-version")"
install="npm install -g --ignore-scripts @earendil-works/pi-coding-agent@$pin"
command -v pi >/dev/null || { echo "results-on-wake test: pi not on PATH; install Pi $pin: $install" >&2; exit 1; }
v="$(pi --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)"
[[ "$v" == "$pin" ]] || { echo "results-on-wake test: pi reports ${v:-no version}, the kit pins $pin (pi-version); $install" >&2; exit 1; }
t="$(mktemp -d)"; srv=""
trap '[[ -z "$srv" ]] || kill "$srv" 2>/dev/null || true; rm -rf "$t"' EXIT
fail() { echo "results-on-wake test: $*" >&2; exit 1; }

mkdir -p "$t/bin" "$t/home" "$t/agent" "$t/cache" "$t/herdr" "$t/state/octo-feather/lanes/gh7.results"
XDG_STATE_HOME="$t/state" "$kit/scripts/pi-role" --set-identity t t@t >/dev/null   # the commit identity a role launch needs (#665)
git -c init.defaultBranch=main init -q "$t/repo"
ln -s "$kit/tests/gate/kit/testkit/herdr.py" "$t/bin/herdr"
lanes="$t/state/octo-feather/lanes"
echo 'pane = "w0:p1"' > "$t/state/octo-feather/director.toml"
printf 'issue = 7\nsupervisor = "w1:p1"\n' > "$lanes/gh7.toml"
spawn='{"at": "2026-11-18T00:00:00Z", "kind": "spawn", "name": "implementer-gh7", "role": "implementer", "pane": "w1:p2", "session": "S7"}'
echo "$spawn" > "$lanes/gh7.handoffs.jsonl"
printf '## 2026-11-18T00:01:00Z implementer-gh7 (implementer)\n\nDONE commit abc\n' > "$lanes/gh7.results/S7.md"
echo '{"w1:p2": {"name": "implementer-gh7", "pane_id": "w1:p2", "workspace_id": "w1", "tab_id": "w1:t2", "agent_status": "idle"}}' \
  > "$t/herdr/agents.json"

python3 "$kit/tests/gate/kit/testkit/provider.py" --log "$t/log" > "$t/port" & srv=$!
for _ in $(seq 50); do [[ -s "$t/port" ]] && break; sleep 0.1; done
[[ -s "$t/port" ]] || fail "fake provider did not start"
printf '{"providers":{"fake":{"baseUrl":"http://127.0.0.1:%s/v1","api":"openai-completions","apiKey":"x","models":[{"id":"fake"}]}}}\n' \
  "$(cat "$t/port")" > "$t/agent/models.json"
echo '{"retry":{"enabled":false},"compaction":{"keepRecentTokens":0}}' > "$t/agent/settings.json"  # the compaction case: summarize every earlier run

# The RPC driver: prompts and a compaction, then each request's count of listing messages, one line per request.
cat > "$t/rpc.py" <<'EOF'
import json, queue, subprocess, sys, threading, time
steps, log, cmd = sys.argv[1].split(","), sys.argv[2], sys.argv[3:]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
events = queue.Queue()
def pump():
    for line in p.stdout:
        try: events.put(json.loads(line))
        except ValueError: pass
threading.Thread(target=pump, daemon=True).start()
def die(msg): p.kill(); print(msg, file=sys.stderr); sys.exit(1)
def wait(pred, what, secs=30):
    end = time.time() + secs
    while time.time() < end:
        try: e = events.get(timeout=max(0.01, end - time.time()))
        except queue.Empty: break
        if pred(e): return e
    die(f"timed out waiting for {what}")
for i, step in enumerate(steps):
    if step == "compact":
        p.stdin.write(json.dumps({"type": "compact", "id": f"c{i}"}) + "\n"); p.stdin.flush()
        r = wait(lambda e: e.get("type") == "response" and e.get("command") == "compact", "the compact response")
        if not r.get("success"): die(f"compact failed: {r}")
    else:
        p.stdin.write(json.dumps({"type": "prompt", "message": step}) + "\n"); p.stdin.flush()
        wait(lambda e: e.get("type") == "agent_settled", f"the settle of {step}")
p.stdin.close(); p.terminate()
try: p.wait(5)
except subprocess.TimeoutExpired: p.kill()
# Per model request answering a prompt: the prompt, then how many listing messages follow it and how many name the
# result file (a compaction's own summary requests hold no prompt message of their own).
def text(m):
    c = m.get("content")
    return c if isinstance(c, str) else " ".join(x.get("text", "") for x in c if isinstance(x, dict))
for line in open(log):
    msgs = [text(m) for m in json.loads(line)["messages"]]
    at = max((i for i, x in enumerate(msgs) if x in steps), default=None)
    if at is None: continue
    after = [x for x in msgs[at + 1:] if x.startswith("Your outstanding workers")]
    print(f"{msgs[at]}:{len(after)}:{sum('/lanes/gh7.results/S7.md' in x for x in after)}")
EOF

# run PANE STEPS: the supervisor (ROLE, when set) at PANE through the driver; sets out (one line per model request).
run() {
  : > "$t/log"
  out="$(cd "$t/repo" && env -i PATH="$t/bin:$PATH" HOME="$t/home" TMPDIR="$t" XDG_CACHE_HOME="$t/cache" XDG_STATE_HOME="$t/state" \
    PI_CODING_AGENT_DIR="$t/agent" PI_OFFLINE=1 PI_SKIP_VERSION_CHECK=1 PI_TELEMETRY=0 FAKE_HERDR="$t/herdr" \
    OCTO_FEATHER_ROLE="${ROLE:-supervisor}" HERDR_PANE_ID="$1" HERDR_WORKSPACE_ID=w1 \
    python3 "$t/rpc.py" "$2" "$t/log" "$kit/scripts/pi-role" "$kit/agents/${ROLE:-supervisor}.md" --model fake/fake --no-session --mode rpc)" \
    || fail "$1 $2: the driver failed: $out"
}

run w1:p1 "go,again,compact,after"
[[ "$out" == $'go:1:1\nagain:0:0\nafter:1:1' ]] || fail "start, once, compact: want go:1:1 again:0:0 after:1:1 (prompt:listings:naming S7.md), got: $out"
echo "case start: the first run's request holds the listing naming lanes/gh7.results/S7.md"
echo "case once: the next run's request holds no second listing"
echo "case compact: after a compaction the first run's request holds the listing again"

run w9:p9 "go,compact,after"
[[ "$out" == $'go:0:0\nafter:0:0' ]] || fail "no log: want no listing at a pane owning no record, got: $out"
echo "case no log: a pane owning no lane record nor director.toml gets no listing"

ROLE=implementer run w1:p1 "go,compact,after"
[[ "$out" == $'go:0:0\nafter:0:0' ]] || fail "implementer: want no listing for a role not loading the extension, got: $out"
echo "case implementer: an implementer launch at the same pane loads no results-on-wake.ts: no listing"

echo '{"at": "2026-11-18T00:02:00Z", "kind": "attempt", "worker": "implementer-gh7", "session": "S7", "result": "done"}' >> "$lanes/gh7.handoffs.jsonl"
run w1:p1 "go"
[[ "$out" == "go:0:0" ]] || fail "none: want no listing with no outstanding worker, got: $out"
echo "case none: no outstanding worker, no listing"
echo "results-on-wake: ok (pi $v, empty environment, the testkit's provider and Herdr)"
