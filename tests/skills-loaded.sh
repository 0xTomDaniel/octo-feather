#!/usr/bin/env bash
# gate: e2e
# Integration test for the launch's side of spec skills#loading-refuse (skills#acceptance-launch-refuses-unloaded,
# skills#acceptance-only-listed; #558): real Pi, at the kit's pin (pi-version), started through a copy of the kit's
# scripts/pi-role against the testkit's model provider (tests/gate/kit/testkit/provider.py), which logs each request. Cases:
#   ok        the implementer starts in a target declaring a good repo skill: the request offers every skill its
#             role file lists (tdd, python, typescript among them) and not the declared one
#   own copy  the target declares a skill the role lists from its own copy: the role starts, offered it once, that copy
#   listed    a listed kit skill whose description is invalid YAML: pi-role exits non-zero naming the skill and
#             Pi's reason, and the provider saw no request
#   declared  the same for a skill the target's AGENTS.md declares on its Repo skills: line
#   unresolved  a declared entry with no folder, a dangling link or a folder with no SKILL.md: the same refusal,
#             naming the skill and why
#   parent    a pane launch (no -p, OCTO_FEATHER_PARENT set) tells the parent through the kit's herdr-say --parent:
#             Herdr (the testkit's stand-in, its FAKE_HERDR world, parent pane w9:p9 idle) gets exactly one prompt,
#             to w9:p9, naming the role and the skill
# No call leaves the test: every start runs under env -i (no Herdr or parent route but the parent case's own
# OCTO_FEATHER_PARENT), the copy's herdr-say and the testkit's herdr first on PATH, its world logging each call;
# every case but parent reaches Herdr not once.
# Stand-ins only for what the kit does not own: the testkit's provider and Herdr (stdlib, offline). Never skips:
# without pi at the pin it fails naming the install command. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
pin="$(tr -d '[:space:]' < "$kit/pi-version")"
install="npm install -g --ignore-scripts @earendil-works/pi-coding-agent@$pin"
command -v pi >/dev/null || { echo "skills-loaded test: pi not on PATH; install Pi $pin: $install" >&2; exit 1; }
v="$(pi --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)"
[[ "$v" == "$pin" ]] || { echo "skills-loaded test: pi reports ${v:-no version}, the kit pins $pin (pi-version); $install" >&2; exit 1; }
t="$(mktemp -d)"; srv=""
XDG_STATE_HOME="$t/state" "$kit/scripts/pi-role" --set-identity t t@t >/dev/null   # the commit identity a role launch needs (#665)
trap '[[ -z "$srv" ]] || kill "$srv" 2>/dev/null || true; rm -rf "$t"' EXIT
fail() { echo "skills-loaded test: $*" >&2; exit 1; }

# The skill names the first request's system prompt offers, sorted, space-separated.
cat > "$t/offered.py" <<'EOF'
import json, re, sys
m = json.loads(open(sys.argv[1]).readline())["messages"][0]["content"]
m = m if isinstance(m, str) else " ".join(p.get("text", "") for p in m)
print(" ".join(sorted(re.findall(r"<name>([^<]+)</name>", m))))
EOF

# The fixture kit: the real scripts, roles, extensions and web list; its skills a copy, so one can be broken.
mkdir -p "$t/kit" "$t/agent" "$t/home" "$t/cache" "$t/bin" "$t/herdr"
cp -r "$kit/scripts" "$kit/agents" "$kit/extensions" "$kit/web-mcp.json" "$t/kit/"
mkdir -p "$t/kit/.agents"; cp -r "$kit/.agents/skills" "$t/kit/.agents/"
# The target: a git repo whose AGENTS.md declares a kit skill and its own skill `local`.
tgt="$t/target"; mkdir -p "$tgt/.agents/skills/local"
git -c init.defaultBranch=main init -q "$tgt"
printf '# target\n\nRepo skills: python, local\n' > "$tgt/AGENTS.md"
good='---\nname: local\ndescription: "A local skill: fine when quoted."\n---\nBody.\n'
bad='---\nname: %s\ndescription: A broken skill: plain value holding a colon.\n---\nBody.\n'
printf -- "$good" > "$tgt/.agents/skills/local/SKILL.md"
# Herdr: the testkit's stand-in, its world holding the parent pane w9:p9, idle.
ln -s "$kit/tests/gate/kit/testkit/herdr.py" "$t/bin/herdr"
echo '{"w9:p9": {"name": "supervisor", "pane_id": "w9:p9", "workspace_id": "w9", "tab_id": "w9:t9", "agent_status": "idle", "ready_at": 0}}' \
  > "$t/herdr/agents.json"

python3 "$kit/tests/gate/kit/testkit/provider.py" --log "$t/log" > "$t/port" & srv=$!
for _ in $(seq 50); do [[ -s "$t/port" ]] && break; sleep 0.1; done
[[ -s "$t/port" ]] || fail "fake provider did not start"
printf '{"providers":{"fake":{"baseUrl":"http://127.0.0.1:%s/v1","api":"openai-completions","apiKey":"x","models":[{"id":"fake"}]}}}\n' \
  "$(cat "$t/port")" > "$t/agent/models.json"

# start ROLE [ARGS...]: pi-role in the target, private home; sets rc, out (stdout), err (stderr); empties the log.
start() {
  local role=$1; shift
  : > "$t/log"
  set +e
  out="$(cd "$tgt" && env -i PATH="$t/bin:$t/kit/.agents/skills/herdr-comms/assets:$PATH" FAKE_HERDR="$t/herdr" HOME="$t/home" TMPDIR="$t" XDG_CACHE_HOME="$t/cache" PI_CODING_AGENT_DIR="$t/agent" \
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

# own copy: the target holds its own copy of a skill the role lists and declares it (the kit's own repo, #595): the
# role starts, offered that skill once, the target's copy.
mkdir -p "$tgt/.agents/skills/python"; cp "$kit/.agents/skills/python/SKILL.md" "$tgt/.agents/skills/python/"
start implementer -p go
[[ "$rc" == 0 && "$out" == *fake-done* ]] || fail "own copy: implementer did not start: rc=$rc $err"
[[ "$(python3 "$t/offered.py" "$t/log")" == "$want" ]] || fail "own copy: implementer offered [$(python3 "$t/offered.py" "$t/log")], its role file lists [$want]"
grep -qF "$(cd "$tgt" && pwd -P)/.agents/skills/python/SKILL.md" "$t/log" || fail "own copy: python not offered from the target's copy"
rm -rf "$tgt/.agents/skills/python"
echo "case own copy: a listed skill the target declares from its own copy is offered once, that copy, and the role starts"

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

[[ ! -e "$t/herdr/log" ]] || fail "a start with no parent route called Herdr: $(cat "$t/herdr/log")"
# parent: a pane launch (RPC here: not -p, so pi-role keeps OCTO_FEATHER_PARENT) tells the parent, through the kit's
# herdr-say: Herdr's world gets one prompt (a line "PANE<TAB>TEXT" in its prompts file).
PARENT=w9:p9 start implementer --mode rpc; refused parent local
for _ in $(seq 50); do [[ -s "$t/herdr/prompts" ]] && break; sleep 0.1; done
sleep 0.5  # a second send would land by now
[[ "$(wc -l < "$t/herdr/prompts" 2>/dev/null)" == 1 ]] && grep -qF $'w9:p9\timplementer did not start' "$t/herdr/prompts" \
  && grep -qF "skill local" "$t/herdr/prompts" || fail "parent: not exactly one prompt to w9:p9 naming local: $(cat "$t/herdr/prompts" 2>/dev/null)"
printf -- "$good" > "$tgt/.agents/skills/local/SKILL.md"
echo "skills-loaded: ok (listed and declared skills Pi cannot load refuse the launch before any request, naming skill and reason; a pane launch tells its parent; good skills offered exactly as listed)"
