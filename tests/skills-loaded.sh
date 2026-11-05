#!/usr/bin/env bash
# Integration test for the launch's side of spec skills#loading-refuse (skills#acceptance-launch-refuses-unloaded,
# skills#acceptance-only-listed; #558): real Pi, at the kit's pin (pi-version), started through a copy of the kit's
# scripts/pi-role against a fake OpenAI-compatible provider on 127.0.0.1 that logs each request. Cases:
#   ok        the implementer starts in a target declaring a good repo skill: the request offers every skill its
#             role file lists (tdd, python, typescript among them) and not the declared one
#   listed    a listed kit skill whose description is invalid YAML: pi-role exits non-zero naming the skill and
#             Pi's reason, and the provider saw no request
#   declared  the same for a skill the target's AGENTS.md declares on its Repo skills: line
#   unresolved  a declared entry with no folder, a dangling link or a folder with no SKILL.md: the same refusal,
#             naming the skill and why
#   parent    a pane launch (no -p, OCTO_FEATHER_PARENT set) tells the parent through herdr-say --parent
# No call leaves the test: every start runs under env -i (no Herdr or parent route but the parent case's own
# OCTO_FEATHER_PARENT), with stub herdr-say and herdr first on PATH recording each call; the parent case asserts
# exactly one herdr-say call, and every case that herdr never ran.
# The fake provider, herdr-say and herdr are hand-written test doubles (stdlib, offline). Never skips: without pi at the
# pin it fails naming the install command. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
pin="$(tr -d '[:space:]' < "$kit/pi-version")"
install="npm install -g --ignore-scripts @earendil-works/pi-coding-agent@$pin"
command -v pi >/dev/null || { echo "skills-loaded test: pi not on PATH; install Pi $pin: $install" >&2; exit 1; }
t="$(mktemp -d)"; srv=""
trap '[[ -z "$srv" ]] || kill "$srv" 2>/dev/null || true; rm -rf "$t"' EXIT
fail() { echo "skills-loaded test: $*" >&2; exit 1; }

cat > "$t/fake.py" <<'EOF'
import http.server, json, os, sys
port_file, log = sys.argv[1], sys.argv[2]
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("content-length", 0))))
        with open(log, "a") as f: f.write(json.dumps(body) + "\n")
        self.send_response(200); self.send_header("content-type", "text/event-stream"); self.end_headers()
        base = {"id": "x", "object": "chat.completion.chunk", "created": 0, "model": "fake"}
        for d, fin in [({"role": "assistant", "content": "fake-done"}, None), ({}, "stop")]:
            c = {**base, "choices": [{"index": 0, "delta": d, "finish_reason": fin}]}
            if fin: c["usage"] = {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}
            self.wfile.write(b"data: " + json.dumps(c).encode() + b"\n\n")
        self.wfile.write(b"data: [DONE]\n\n")
s = http.server.HTTPServer(("127.0.0.1", 0), H)
open(port_file + ".tmp", "w").write(str(s.server_address[1])); os.replace(port_file + ".tmp", port_file)
s.serve_forever()
EOF
# The skill names the first request's system prompt offers, sorted, space-separated.
cat > "$t/offered.py" <<'EOF'
import json, re, sys
m = json.loads(open(sys.argv[1]).readline())["messages"][0]["content"]
m = m if isinstance(m, str) else " ".join(p.get("text", "") for p in m)
print(" ".join(sorted(re.findall(r"<name>([^<]+)</name>", m))))
EOF

# The fixture kit: the real scripts, roles, extensions and web list; its skills a copy, so one can be broken.
mkdir -p "$t/kit" "$t/agent" "$t/home" "$t/cache" "$t/bin"
cp -r "$kit/scripts" "$kit/agents" "$kit/extensions" "$kit/web-mcp.json" "$t/kit/"
mkdir -p "$t/kit/.agents"; cp -r "$kit/.agents/skills" "$t/kit/.agents/"
# The target: a git repo whose AGENTS.md declares a kit skill and its own skill `local`.
tgt="$t/target"; mkdir -p "$tgt/.agents/skills/local"
git -c init.defaultBranch=main init -q "$tgt"
printf '# target\n\nRepo skills: python, local\n' > "$tgt/AGENTS.md"
good='---\nname: local\ndescription: "A local skill: fine when quoted."\n---\nBody.\n'
bad='---\nname: %s\ndescription: A broken skill: plain value holding a colon.\n---\nBody.\n'
printf -- "$good" > "$tgt/.agents/skills/local/SKILL.md"
for b in herdr-say herdr; do
  printf '#!/bin/sh\nprintf "%%s\\n" "$*" >> "%s/%s.calls"\n' "$t" "$b" > "$t/bin/$b"; chmod +x "$t/bin/$b"
done

python3 "$t/fake.py" "$t/port" "$t/log" & srv=$!
for _ in $(seq 50); do [[ -s "$t/port" ]] && break; sleep 0.1; done
[[ -s "$t/port" ]] || fail "fake provider did not start"
printf '{"providers":{"fake":{"baseUrl":"http://127.0.0.1:%s/v1","api":"openai-completions","apiKey":"x","models":[{"id":"fake"}]}}}\n' \
  "$(cat "$t/port")" > "$t/agent/models.json"

# start ROLE [ARGS...]: pi-role in the target, private home; sets rc, out (stdout), err (stderr); empties the log.
start() {
  local role=$1; shift
  : > "$t/log"
  set +e
  out="$(cd "$tgt" && env -i PATH="$t/bin:$PATH" HOME="$t/home" TMPDIR="$t" XDG_CACHE_HOME="$t/cache" PI_CODING_AGENT_DIR="$t/agent" \
    PI_OFFLINE=1 PI_SKIP_VERSION_CHECK=1 PI_TELEMETRY=0 XDG_STATE_HOME="$t/state" ${PARENT:+OCTO_FEATHER_PARENT=$PARENT} \
    "$t/kit/scripts/pi-role" "$t/kit/agents/$role.md" --model fake/fake --no-session "$@" 2>"$t/err" </dev/null)"; rc=$?
  set -e
  err="$(cat "$t/err")"
}
# refused WHAT SKILL [REASON]: the last start exited non-zero naming SKILL and the reason (default Pi's YAML error),
# before any request.
refused() {
  [[ "$rc" != 0 ]] || fail "$1: pi-role exited 0 with a skill Pi cannot load"
  grep -qF "Pi did not load skill $2 (" <<<"$err" || fail "$1: stderr does not name $2: $err"
  grep -qF "${3:-Nested mappings are not allowed}" <<<"$err" || fail "$1: stderr lacks the reason ${3:-}: $err"
  [[ ! -s "$t/log" ]] || fail "$1: the provider saw $(wc -l < "$t/log") request(s)"
}

# ok: every listed skill offered, the declared repo skill checked but not offered.
start implementer -p go
[[ "$rc" == 0 && "$out" == *fake-done* ]] || fail "ok: implementer did not start: rc=$rc $err"
got="$(python3 "$t/offered.py" "$t/log")"
want="$(sed -n 's/^skills: *//p' "$kit/agents/implementer.md" | tr -d ' ' | tr ',' '\n' | sed 's/{tracker}/github-issues/' | sort | tr '\n' ' ' | sed 's/ $//')"
[[ "$got" == "$want" ]] || fail "ok: implementer offered [$got], its role file lists [$want]"
start code-reviewer -p go
got="$(python3 "$t/offered.py" "$t/log")"
[[ " $got " == *" tdd "* ]] || fail "ok: code-reviewer not offered tdd: [$got]"
echo "case ok: the implementer is offered exactly its listed skills, tdd, python, typescript included; code-reviewer tdd; the declared repo skill is not offered"

# listed: the kit's tdd broken; both roles listing it refuse.
cp "$t/kit/.agents/skills/tdd/SKILL.md" "$t/tdd.keep"
printf -- "$bad" tdd > "$t/kit/.agents/skills/tdd/SKILL.md"
start implementer -p go; refused "listed (implementer)" tdd
start code-reviewer -p go; refused "listed (code-reviewer)" tdd
cp "$t/tdd.keep" "$t/kit/.agents/skills/tdd/SKILL.md"
echo "case listed: a role whose listed skill Pi cannot load exits non-zero naming it and Pi's reason, no request"

# declared: the target's own declared skill broken.
printf -- "$bad" local > "$tgt/.agents/skills/local/SKILL.md"
start implementer -p go; refused declared local
echo "case declared: a target's declared repo skill Pi cannot load refuses the launch the same way"

# unresolved: a declared name with no folder anywhere, a dangling link, a folder with no SKILL.md.
printf -- "$good" > "$tgt/.agents/skills/local/SKILL.md"
printf '# target\n\nRepo skills: python, local, nowhere\n' > "$tgt/AGENTS.md"
start implementer -p go; refused "unresolved (missing)" nowhere "skill path does not exist"
ln -s "$t/gone" "$tgt/.agents/skills/nowhere"
start implementer -p go; refused "unresolved (dangling link)" nowhere "skill path does not exist"
rm "$tgt/.agents/skills/nowhere"; mkdir -p "$tgt/.agents/skills/nowhere"; echo notes > "$tgt/.agents/skills/nowhere/README.txt"
start implementer -p go; refused "unresolved (no SKILL.md)" nowhere "no SKILL.md in it"
rm -rf "$tgt/.agents/skills/nowhere"
printf '# target\n\nRepo skills: python, local\n' > "$tgt/AGENTS.md"
printf -- "$bad" local > "$tgt/.agents/skills/local/SKILL.md"
echo "case unresolved: a declared entry with no folder, a dangling link or no SKILL.md refuses the launch naming it and why"

[[ ! -e "$t/herdr-say.calls" && ! -e "$t/herdr.calls" ]] || fail "a start with no parent route called Herdr: $(cat "$t"/herdr*.calls)"
# parent: a pane launch (RPC here: not -p, so pi-role keeps OCTO_FEATHER_PARENT) tells the parent, through the stub.
PARENT=w9:p9 start implementer --mode rpc; refused parent local
for _ in $(seq 50); do [[ -s "$t/herdr-say.calls" ]] && break; sleep 0.1; done
sleep 0.5  # a second send would land by now
[[ "$(wc -l < "$t/herdr-say.calls" 2>/dev/null)" == 1 ]] && grep -qF -- "--parent implementer did not start" "$t/herdr-say.calls" \
  && grep -qF "skill local" "$t/herdr-say.calls" || fail "parent: not exactly one herdr-say --parent call naming local: $(cat "$t/herdr-say.calls" 2>/dev/null)"
[[ ! -e "$t/herdr.calls" ]] || fail "parent: herdr itself ran: $(cat "$t/herdr.calls")"
printf -- "$good" > "$tgt/.agents/skills/local/SKILL.md"
echo "skills-loaded: ok (listed and declared skills Pi cannot load refuse the launch before any request, naming skill and reason; a pane launch tells its parent; good skills offered exactly as listed)"
