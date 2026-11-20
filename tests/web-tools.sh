#!/usr/bin/env bash
# gate: e2e
# Integration test for a role's `web` tool (issue #262; spec roles#launch-web, roles#roles-web,
# roles#fm-tools): real Pi, at the kit's pin (pi-version), launched headless through a copy of the
# kit's scripts/pi-role whose web-mcp.json names a stub stdio MCP server instead of the hosted ones
# (no network), against the testkit's model provider (tests/gate/kit/testkit/provider.py) on 127.0.0.1. The
# provider logs each request and answers the first with one codemode call listing ALL_TOOLS, so the test reads both
# the tools declared to the model and the tools a codemode script reaches. The user Pi config and
# the target repo's .pi/mcp.json each name another stub server. Cases:
#   roles      roles#acceptance-web-roles, roles#acceptance-web-no-other-mcp,
#              roles#acceptance-director-tools: each role's declared and codemode tools are exactly
#              its role file's tools plus codemode, plus the web list's tools for a role listing
#              web; no role has a tool of the other servers; supervisor and qc judge none of MCP
#   list-once  roles#acceptance-web-list-once: a server added to the web list, no role file
#              changed, reaches the implementer and not the supervisor; an unreachable server in
#              the list leaves the role starting with the other servers' tools
#   tab        roles#acceptance-codemode-every-role in a tab: herdr-spawn --role (fake herdr) hands the tab the
#              role's pi-role launch, and Pi started on that argv has the same tools as the roles case
#   check      check-roles accepts `web` and still rejects an unknown tool
# The stub server and the testkit provider are hand-written test doubles (stdlib, offline). Never
# skips: without pi at the pin it fails naming the install command. Run by `just check`.
# criterion: roles#acceptance-codemode-every-role
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
pin="$(tr -d '[:space:]' < "$kit/pi-version")"
install="npm install -g --ignore-scripts @earendil-works/pi-coding-agent@$pin"
command -v pi >/dev/null || { echo "web-tools test: pi not on PATH; install Pi $pin: $install" >&2; exit 1; }
v="$(pi --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)"
[[ "$v" == "$pin" ]] || { echo "web-tools test: pi reports ${v:-no version}, the kit pins $pin (pi-version); $install" >&2; exit 1; }
t="$(mktemp -d)"; srv=""
XDG_STATE_HOME="$t/state" "$kit/scripts/pi-role" --set-identity t t@t >/dev/null   # the commit identity a role launch needs (#665)
trap '[[ -z "$srv" ]] || kill "$srv" 2>/dev/null || true; rm -rf "$t"' EXIT
fail() { echo "web-tools test: $*" >&2; exit 1; }

# A stub MCP server over stdio (newline-delimited JSON-RPC 2.0): argv[1] names it, each later arg is a tool.
cat > "$t/stub_mcp.py" <<'EOF'
import json, sys
name, tools = sys.argv[1], sys.argv[2:]
def send(o): sys.stdout.write(json.dumps(o) + "\n"); sys.stdout.flush()
for line in sys.stdin:
    try: m = json.loads(line)
    except ValueError: continue
    if "id" not in m: continue
    meth, i = m.get("method"), m["id"]
    if meth == "initialize":
        send({"jsonrpc": "2.0", "id": i, "result": {"protocolVersion": m["params"].get("protocolVersion", "2025-06-18"),
              "capabilities": {"tools": {}}, "serverInfo": {"name": name, "version": "1"}}})
    elif meth == "tools/list":
        send({"jsonrpc": "2.0", "id": i, "result": {"tools": [{"name": x, "description": f"{name} {x}",
              "inputSchema": {"type": "object", "properties": {"q": {"type": "string"}}}} for x in tools]}})
    elif meth == "tools/call":
        send({"jsonrpc": "2.0", "id": i, "result": {"content": [{"type": "text", "text": f"{name}-{m['params']['name']}-result"}]}})
    elif meth == "ping":
        send({"jsonrpc": "2.0", "id": i, "result": {}})
    else:
        send({"jsonrpc": "2.0", "id": i, "error": {"code": -32601, "message": "method not found"}})
EOF

# Reads the provider log: "<declared tools>|<codemode tools>", each sorted, space-separated.
cat > "$t/seen.py" <<'EOF'
import json, re, sys
reqs = [json.loads(l) for l in open(sys.argv[1])]
declared = sorted(x["function"]["name"] for x in reqs[0].get("tools", []))
out = [m["content"] for r in reqs for m in r["messages"] if m["role"] == "tool"]
text = out[0] if isinstance(out[0], str) else " ".join(p.get("text", "") for p in out[0])
reached = re.search(r"TOOLS:(.*)", text).group(1).split()
print(" ".join(declared) + "|" + " ".join(sorted(reached)))
EOF

# The fixture kit: the real scripts, roles and extensions, the real skills, a stub web list.
mkdir -p "$t/kit/.agents" "$t/agent" "$t/home" "$t/repo/.pi" "$t/cache"
cp -r "$kit/scripts" "$kit/agents" "$kit/extensions" "$t/kit/"; ln -s "$kit/.agents/skills" "$t/kit/.agents/skills"
stub() { printf '"%s":{"command":"python3","args":["%s","%s","search","fetch"]}' "$1" "$t/stub_mcp.py" "$1"; }
echo "{\"mcpServers\":{$(stub webstub)}}" > "$t/kit/web-mcp.json"
echo "{\"mcpServers\":{$(stub useronly)}}" > "$t/agent/mcp.json"
echo "{\"mcpServers\":{$(stub projonly)}}" > "$t/repo/.pi/mcp.json"
git -c init.defaultBranch=main init -q "$t/repo"

python3 "$kit/tests/gate/kit/testkit/provider.py" --log "$t/log" --code 'return "TOOLS:" + ALL_TOOLS.map(t => t.name).join(" ")' \
  > "$t/port" & srv=$!
for _ in $(seq 50); do [[ -s "$t/port" ]] && break; sleep 0.1; done
[[ -s "$t/port" ]] || fail "fake provider did not start"
printf '{"providers":{"fake":{"baseUrl":"http://127.0.0.1:%s/v1","api":"openai-completions","apiKey":"x","models":[{"id":"fake"}]}}}\n' \
  "$(cat "$t/port")" > "$t/agent/models.json"

# run ROLE: the role started headless in the target repo; prints what seen.py reads.
run() {
  : > "$t/log"
  local out
  out="$(cd "$t/repo" && env -i PATH="$PATH" HOME="$t/home" TMPDIR="$t" XDG_CACHE_HOME="$t/cache" PI_CODING_AGENT_DIR="$t/agent" \
    PI_OFFLINE=1 PI_SKIP_VERSION_CHECK=1 PI_TELEMETRY=0 XDG_STATE_HOME="$t/state" \
    "$t/kit/scripts/pi-role" "$t/kit/agents/$1.md" --model fake/fake --no-session -p go 2>"$t/err")" \
    || fail "$1: pi-role exited non-zero: $(cat "$t/err")"
  [[ "$out" == *fake-done* ]] || fail "$1: no answer after the codemode call: $out"
  python3 "$t/seen.py" "$t/log"
}

ro="bash find grep ls read"; rw="bash edit find grep ls read write"; web="mcp__webstub__fetch mcp__webstub__search"
sorted() { tr ' ' '\n' <<<"$*" | sort | tr '\n' ' ' | sed 's/ $//'; }
for rt in "director:$ro:$web" "code-reviewer:$ro:$web" "implementer:$rw:$web" "general-worker:$rw:$web" "corrector:$rw:$web" "shaper:$rw:$web" "supervisor:$rw:" "qc-judge:$ro:"; do
  IFS=: read -r role tools mcp <<<"$rt"
  want="$(sorted codemode $tools $mcp)|$(sorted $tools $mcp)"
  got="$(run "$role")"
  [[ "$got" == "$want" ]] || fail "roles: $role has declared|codemode tools $got, want $want"
done
echo "case roles: ok (web roles: their tools plus the web list's, declared and in codemode; supervisor, qc judge: no MCP; user and project servers reach none)"

# tab: roles#acceptance-codemode-every-role's tab launches (ADR 0016). The real herdr-spawn, copied so its kit root
# (four dirs up) is the fixture kit, opens the role's tab through the fake herdr of tests/fixtures/herdr-spawn,
# which records the agent start argv and the tab's env instead of starting Pi. The argv must be the role's
# `pi-role --json` args plus herdr-spawn's --session-id and Herdr's Pi integration (--extension, the file the fake
# herdr's `integration install pi` wrote into herdr-spawn's cache dir); real Pi then starts on exactly that argv in that env
# (the model swapped for the fake provider's, -p for no TUI) and its codemode script reaches the role's tools.
mkdir -p "$t/kit/.agents/spawn/herdr-comms/assets" "$t/hbin"
cp "$kit/.agents/skills/herdr-comms/assets/herdr-spawn" "$kit/.agents/skills/herdr-comms/assets/herdr_ready.py" \
  "$kit/.agents/skills/herdr-comms/assets/herdr_scope.py" \
  "$t/kit/.agents/spawn/herdr-comms/assets/"
cp "$kit/tests/fixtures/herdr-spawn/"* "$t/hbin/"; chmod +x "$t/hbin/herdr"
cp "$kit/tests/gate/kit/testkit/systemd.py" "$t/hbin/busctl"; cp "$kit/tests/gate/kit/testkit/systemd.py" "$t/hbin/systemctl"   # systemd stood in: the scope is e2e
tab() {
  local d="$t/tab-$1"; mkdir -p "$d"; : > "$t/log"
  (cd "$t/repo" && env FAKE_HERDR_DIR="$d" PATH="$t/hbin:$PATH" HOME="$t/home" XDG_CACHE_HOME="$t/cache" XDG_STATE_HOME="$t/state" \
    HERDR_PANE_ID=w9:p0 "$t/kit/.agents/spawn/herdr-comms/assets/herdr-spawn" --workspace w9 --name "$1" --role "$1" \
    --cwd "$t/repo" >/dev/null 2>"$d/err") || fail "tab: herdr-spawn --role $1 failed: $(cat "$d/err")"
  local want_args; want_args="$(cd "$t/repo" && XDG_CACHE_HOME="$t/cache" XDG_STATE_HOME="$t/state" \
    "$t/kit/scripts/pi-role" --json "$t/kit/agents/$1.md" 2>/dev/null | python3 -c 'import json,sys; print("\n".join(json.load(sys.stdin)["args"]))')"
  [[ "$(head -n -4 "$d/start-argv")" == "$want_args" && "$(tail -n 4 "$d/start-argv" | head -1)" == --session-id \
    && "$(tail -n 2 "$d/start-argv" | tr '\n' ' ')" == "--extension $t/cache/octo-feather/herdr-pi/herdr-agent-state.ts " ]] \
    || fail "tab: $1's tab argv is not its pi-role --json args plus --session-id and Herdr's Pi integration: $(cat "$d/start-argv")"
  local argv envs out; mapfile -t argv < "$d/start-argv"; mapfile -t envs < "$d/tab-env"
  out="$(cd "$t/repo" && env -i "${envs[@]}" TMPDIR="$t" XDG_CACHE_HOME="$t/cache" PI_CODING_AGENT_DIR="$t/agent" PI_OFFLINE=1 \
    PI_SKIP_VERSION_CHECK=1 PI_TELEMETRY=0 XDG_STATE_HOME="$t/state" pi "${argv[@]}" --model fake/fake -p go 2>"$d/pierr")" \
    || fail "tab: $1: pi on the tab argv exited non-zero: $(cat "$d/pierr")"
  [[ "$out" == *fake-done* ]] || fail "tab: $1: no answer after the codemode call: $out"
  python3 "$t/seen.py" "$t/log"
}
for rt in "director:$ro:$web" "supervisor:$rw:" "general-worker:$rw:$web" "implementer:$rw:$web" "corrector:$rw:$web" "code-reviewer:$ro:$web"; do
  IFS=: read -r role tools mcp <<<"$rt"
  want="$(sorted codemode $tools $mcp)|$(sorted $tools $mcp)"
  got="$(tab "$role")"
  [[ "$got" == "$want" ]] || fail "tab: $role has declared|codemode tools $got, want $want"
done
echo "case tab: ok (herdr-spawn --role hands each tab its pi-role launch; Pi started on it has its role file's tools plus codemode, and codemode reaches exactly those)"

# list-once: one more server and an unreachable one in the list; no role file changed.
echo "{\"mcpServers\":{$(stub webstub),$(stub second),\"dead\":{\"url\":\"http://127.0.0.1:9/mcp\"}}}" > "$t/kit/web-mcp.json"
diff -r "$kit/agents" "$t/kit/agents" >/dev/null || fail "list-once: the fixture's role files differ from the kit's"
want="$(sorted codemode $rw $web mcp__second__fetch mcp__second__search)|$(sorted $rw $web mcp__second__fetch mcp__second__search)"
got="$(run implementer)"
[[ "$got" == "$want" ]] || fail "list-once: implementer has $got, want $want"
want="$(sorted codemode $rw)|$(sorted $rw)"
got="$(run supervisor)"
[[ "$got" == "$want" ]] || fail "list-once: supervisor has $got, want $want"
echo "case list-once: ok (an added server reaches the implementer, not the supervisor; an unreachable one leaves the role starting)"

# check: check-roles accepts web (the real roles) and still rejects an unknown tool.
"$t/kit/scripts/check-roles" >/dev/null 2>"$t/cr" || fail "check: check-roles refused the kit's roles: $(cat "$t/cr")"
sed -i 's/^tools: .*/tools: read, grep, find, ls, bash, web, websearch/' "$t/kit/agents/director.md"
if "$t/kit/scripts/check-roles" >/dev/null 2>"$t/cr"; then fail "check: check-roles passed an unknown tool"; fi
grep -q 'agents/director.md: unknown tool `websearch`' "$t/cr" || fail "check: check-roles did not name the unknown tool: $(cat "$t/cr")"
echo "case check: ok"
echo "web-tools: ok (pi $v, stub MCP servers, no network)"
