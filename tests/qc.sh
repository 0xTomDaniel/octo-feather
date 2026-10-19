#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qc with a fake `pi` and a fake
# `herdr` on PATH (no model call, no real Herdr session): only passed criteria
# become built, one status-only commit, a same-family judge, a dirty tree, an
# unusable report and a judge that writes are refused, reports never overwrite;
# the sandbox (#33): a judge trying each escape fails at every one, a failed
# proof aborts before the judge, leftovers are killed and agents counted,
# --no-sandbox never commits, and the qc recipes pass arguments as data.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`).
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
Q="$kit/scripts/octo-feather-qc"; S="$kit/scripts/octo-feather-spec-status"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fail() { echo "qc test: $*" >&2; exit 1; }
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
# A throwaway HOME holding a "live" box: a live Herdr session, gh and git creds, live and archived lanes.
export HOME="$t/home" OCTO_FEATHER_QC_DIR="$t/reports"
unset XDG_CONFIG_HOME XDG_STATE_HOME XDG_CACHE_HOME GH_CONFIG_DIR HERDR_SESSION SPEC_CHAT_STATE
export GH_TOKEN=SECRET-token OCTO_FEATHER_PARENT=wX:p9 HERDR_PANE_ID=p9 HERDR_TAB_ID=t9 HERDR_WORKSPACE_ID=w9
live="$HOME/.local/state/octo-feather"
mkdir -p "$HOME/.config/herdr" "$HOME/.config/gh" "$live/lanes/archive" "$t/bin" "$t/repo/docs/specs"
echo default > "$HOME/.config/herdr/herdr.sock"
echo 'oauth_token: SECRET-gh' > "$HOME/.config/gh/hosts.yml"; echo 'https://x:SECRET-git@github.com' > "$HOME/.git-credentials"
echo LIVE > "$live/lanes/gh9.toml"; echo ARCHIVED > "$live/lanes/archive/gh1.toml"; echo '{"director":1}' > "$live/director.handoffs.jsonl"
echo 'pane = "LIVE"' > "$live/director.toml"
cat > "$t/bin/herdr" <<'EOF'
#!/usr/bin/env bash
# Fake Herdr: a session's socket is a file under the config dir naming the session.
C="${XDG_CONFIG_HOME:-$HOME/.config}/herdr"; s=default; a=()
while (($#)); do case "$1" in --session) s="$2"; shift 2;; --remote|--machine) shift 2;; *) a+=("$1"); shift;; esac; done
[[ "$s" == default ]] && sock="$C/herdr.sock" || sock="$C/sessions/$s/herdr.sock"
case "${a[*]}" in
  server) mkdir -p "${sock%/*}"; echo "$s" > "$sock"; exec sleep 3011;;
  "session stop "*) rm -f "$C/sessions/${a[2]}/herdr.sock"; exit 0;;
  "session delete "*) rm -rf "${C:?}/sessions/${a[2]}"; exit 0;;
esac
[[ -n "${FAKE_HERDR_LEAK:-}" ]] && { echo '{"session":"default"}'; exit 0; }
[[ -f "$sock" ]] || { echo server_not_running >&2; exit 1; }
echo "{\"session\":\"$(cat "$sock")\"}"
EOF
cat > "$t/bin/pi" <<'EOF'
#!/usr/bin/env bash
# Fake judge: FAKE_QC picks the reply; `escape` tries every way out and prints ESCAPE per success.
[[ "${1:-}" == --version ]] && exit 0
ok='```json\n{"head": "x", "criteria": [{"id": "acceptance-a", "verdict": "pass", "command": "app a --json", "output": "ok", "why": "shown"}]}\n```\n'
case "$FAKE_QC" in
  mixed) printf 'done\n```json\n{"head": "x", "criteria": [{"id": "acceptance-a", "verdict": "pass", "command": "app a --json", "output": "{\\"ok\\": true}", "why": "shown"}, {"id": "acceptance-b", "verdict": "fail", "command": "app b --json", "output": "error", "why": "no b"}]}\n```\n' ;;
  garbage) echo "I think it works." ;;
  writes) echo hacked > judge-was-here; printf '```json\n{"criteria": []}\n```\n' ;;
  escape)
    for h in herdr $(type -ap herdr); do
      for flag in "--session default" "--remote live" "--machine live" ""; do
        # shellcheck disable=SC2086
        "$h" $flag workspace list 2>/dev/null | grep -q '"default"' && echo "ESCAPE live Herdr via $h $flag"
      done
    done
    cat "$HOME/.config/gh/hosts.yml" "$GH_CONFIG_DIR/hosts.yml" "$HOME/.git-credentials" 2>/dev/null | grep -q SECRET && echo "ESCAPE gh/git creds file"
    env | grep -q SECRET && echo "ESCAPE token in env"
    [[ -n "${OCTO_FEATHER_PARENT:-}${HERDR_PANE_ID:-}${HERDR_TAB_ID:-}${HERDR_WORKSPACE_ID:-}" ]] && echo "ESCAPE parent route"
    d="$(mktemp -d /tmp/qc-escape-XXXXXX)"; echo k > "$d/auth.json"; echo m > "$d/models.json"
    L="$HOME/.local/state/octo-feather"; st="$(octo-feather-state)"
    grep -q LIVE "$L/lanes/gh9.toml" "$L/director.toml" 2>/dev/null && echo "ESCAPE read live lanes"
    echo x > "$L/lanes/escaped" 2>/dev/null; echo x >> "$L/director.handoffs.jsonl" 2>/dev/null
    echo x >> "$st/lanes/archive/gh1.toml" 2>/dev/null && echo "ESCAPE wrote archive"
    echo x >> "$st/director.handoffs.jsonl" 2>/dev/null && echo "ESCAPE wrote director log"
    grep -q ARCHIVED "$st/lanes/archive/gh1.toml" && grep -q director "$st/director.handoffs.jsonl" || echo "MISSING history"
    [[ "$st" == "$L" ]] && echo "ESCAPE state dir is live"
    setsid sleep 3012 < /dev/null > /dev/null 2>&1 &
    pi --version
    printf "$ok" ;;
esac
EOF
chmod +x "$t/bin/pi" "$t/bin/herdr"; export PATH="$t/bin:$kit/scripts:$PATH"
cp "$kit/tests/fixtures/spec-status/good/demo.spec.html" "$t/repo/docs/specs/"
cd "$t/repo"; git init -q -b main .
"$S" init docs/specs/demo.spec.html 0123abc >/dev/null; git add -A; git commit -qm spec
st=docs/specs/demo.status.json
run() { local want="$1"; shift; set +e; out="$(FAKE_QC="$1" "$Q" "${@:2}" 2>&1)"; rc=$?; set -e
  [[ "$rc" == "$want" ]] || fail "FAKE_QC=$1 '${*:2}' want exit $want, got $rc: $out"; }
report() { python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))'"$1"')' "$(ls -t "$t"/reports/*.json | head -1)"; }
OCTO_FEATHER_QC_MODEL=anthropic/claude-opus-5-5 run 64 mixed $st 5 acceptance-a acceptance-b   # judge of the implementer's family
echo x > dirty; run 65 mixed $st 5 acceptance-a; rm dirty                                      # dirty worktree
before="$(git rev-parse HEAD)"
run 3 garbage $st 5 acceptance-a acceptance-b                                                   # no json report
run 3 writes $st 5 acceptance-a                                                                 # judge wrote a file
[[ "$(git rev-parse HEAD)" == "$before" ]] || fail "refused run moved the head"
git clean -qfd
[[ "$(find "$t/reports" -name "$before-*.json" | wc -l)" == 2 ]] || fail "two runs at one head must leave two reports"
grep -q "qc sandbox: ok   live Herdr unreachable" <<< "$out" || fail "no pre-run proof printed: $out"

# --no-sandbox: printed, report written, status never changes.
run 1 mixed $st 5 acceptance-a acceptance-b --no-sandbox
grep -q UNSANDBOXED <<< "$out" || fail "--no-sandbox not printed: $out"
[[ "$(git rev-parse HEAD)" == "$before" && -z "$(git status --porcelain)" ]] || fail "--no-sandbox changed the status file"
[[ "$(report '["sandbox"]')" == False ]] || fail "--no-sandbox report must record sandbox false"

run 1 mixed $st 5 acceptance-a acceptance-b                                                     # a passes, b fails
python3 - "$st" <<'EOF'
import json, sys
c = json.load(open(sys.argv[1]))["criteria"]
assert c["acceptance-a"] == {"status": "built", "pr": 5}, c
assert c["acceptance-b"] == {"status": "planned", "pr": None}, c
EOF
[[ "$(git diff --name-only "$before" HEAD)" == "$st" && "$(git rev-list --count "$before"..HEAD)" == 1 ]] \
  || fail "expected one commit touching only the status file"

# A failed proof check aborts before the judge: here raw herdr still reaches a live session.
FAKE_HERDR_LEAK=1 run 66 escape $st 5 acceptance-a
grep -q "FAIL live Herdr unreachable" <<< "$out" || fail "leaking Herdr not caught by the proof: $out"
[[ "$(report '.get("stdout", "none")')" == none ]] || fail "judge started after a failed proof"

# Every escape fails; leftovers killed, agents counted, credential copies gone, live records untouched.
run 0 escape $st 5 acceptance-a
judge="$(report '["stdout"]')"
grep -E 'ESCAPE|MISSING' <<< "$judge" && fail "sandbox escape: $judge"
grep -q "cleanup: agents started 1 (headless pi 1, Herdr panes 0)" <<< "$out" || fail "no agent count: $out"
[[ "$(report '["sandbox"]["left_after_kill"]')" == 0 && "$(report '["sandbox"]["credential_copies_left"]')" == 0 \
  && "$(report '["sandbox"]["credential_copies_removed"]')" == 2 ]] || fail "cleanup record: $(report '["sandbox"]')"
report '["sandbox"]["killed"]' | grep -q "sleep 3012" || fail "leftover judge process not killed: $(report '["sandbox"]')"
! pgrep -fx 'sleep 301[12]' >/dev/null || fail "sandbox processes survived the run"
ls -d /tmp/qc-escape-* 2>/dev/null && fail "judge's /tmp writes survived"
[[ ! -e "$live/lanes/escaped" && "$(cat "$live/lanes/archive/gh1.toml")" == ARCHIVED && "$(wc -l < "$live/director.handoffs.jsonl")" == 1 ]] \
  || fail "judge wrote live state"
[[ ! -e "$HOME/.config/herdr/sessions" ]] || fail "sandbox Herdr session left in the real config dir"

# The qc recipes pass arguments as data, never as shell source.
for jf in "$kit/justfile" "$kit/templates/python/justfile" "$kit/templates/typescript/justfile"; do
  set +e; o="$(just --justfile "$jf" --working-directory "$t/repo" qc "$st" 5 'acceptance-a$(touch pwned)' 'x;touch pwned2' 2>&1)"; rc=$?; set -e
  [[ "$rc" != 0 && ! -e pwned && ! -e pwned2 && ! -e "$kit/pwned" ]] || fail "$jf qc ran its arguments as shell (exit $rc): $o"
  grep -q 'not in docs/specs/demo.status.json: acceptance-a$(touch pwned) x;touch pwned2' <<< "$o" || fail "$jf qc mangled its arguments: $o"
done
echo "qc: ok (pass flips built, fail stays planned, status-only commit, same family, dirty, unusable report, judge wrote, unique reports, sandbox escapes, proof abort, cleanup count, --no-sandbox, recipe args as data)"
