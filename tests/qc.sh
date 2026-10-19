#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qc with a fake `pi` and a fake
# `herdr` on PATH (no model call; a real Herdr only in the pane test on a box): only passed criteria
# become built, one status-only commit, a same-family judge, a dirty tree, an
# unusable report and a judge that writes are refused, reports never overwrite;
# the sandbox (#33): a judge trying each escape fails at every one, a failed
# proof aborts before the judge, leftovers are killed and agents counted,
# masks cannot be unmounted, a nested-namespace survivor dies, no judge write
# persists (the worktree is an overlay on the run tmpfs; credential copies vanish), a pane
# the judge spawns runs in its PID namespace and dies with it (real herdr when
# installed, else the fake; the test prints which),
# --no-sandbox never commits, and the qc recipes pass arguments as data.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`).
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
Q="$kit/scripts/octo-feather-qc"; S="$kit/scripts/octo-feather-spec-status"
t="$(mktemp -d)"
stop() { local f; for f in "$t"/pids/*; do [[ -f "$f" ]] && kill -- -"$(cat "$f")" 2>/dev/null; done; rm -rf "$t"; }
trap stop EXIT
fail() { echo "qc test: $*" >&2; exit 1; }
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
# A throwaway HOME holding a "live" box: a live Herdr session, gh and git creds, live and archived lanes.
export HOME="$t/home" OCTO_FEATHER_QC_DIR="$t/reports"
unset XDG_CONFIG_HOME XDG_STATE_HOME XDG_CACHE_HOME GH_CONFIG_DIR HERDR_SESSION SPEC_CHAT_STATE HERDR_SOCKET_PATH HERDR_BIN_PATH HERDR_ENV
export GH_TOKEN=SECRET-token OCTO_FEATHER_PARENT=wX:p9 HERDR_PANE_ID=p9 HERDR_TAB_ID=t9 HERDR_WORKSPACE_ID=w9
live="$HOME/.local/state/octo-feather"
mkdir -p "$HOME/.config/herdr" "$HOME/.config/gh" "$live/lanes/archive" "$t/bin" "$t/fakeherdr" "$t/pids" "$t/repo/docs/specs"
echo default > "$HOME/.config/herdr/herdr.sock"
echo 'oauth_token: SECRET-gh' > "$HOME/.config/gh/hosts.yml"; echo 'https://x:SECRET-git@github.com' > "$HOME/.git-credentials"
echo LIVE > "$live/lanes/gh9.toml"; echo ARCHIVED > "$live/lanes/archive/gh1.toml"; echo '{"director":1}' > "$live/director.handoffs.jsonl"
echo 'pane = "LIVE"' > "$live/director.toml"
mkdir -p "$HOME/.pi/agent"; echo '{"k": "SECRET-pi-auth-0123456789", "exp": 1}' > "$HOME/.pi/agent/auth.json"; chmod 600 "$HOME/.pi/agent/auth.json"
echo '{"providers": {"p": {"apiKey": "SECRET-pi-models-0123456789"}}}' > "$HOME/.pi/agent/models.json"
cat > "$t/fakeherdr/herdr" <<'EOF'
#!/usr/bin/env bash
# Fake Herdr: a session's socket is a file under the config dir naming the session.
C="${XDG_CONFIG_HOME:-$HOME/.config}/herdr"; s=default; a=()
while (($#)); do case "$1" in --session) s="$2"; shift 2;; --remote|--machine) shift 2;; *) a+=("$1"); shift;; esac; done
[[ "$s" == default ]] && sock="$C/herdr.sock" || sock="$C/sessions/$s/herdr.sock"
case "${a[*]}" in
  server) mkdir -p "${sock%/*}"; echo "$s" > "$sock"; exec sleep 3011@TOK@;;
  "session stop "*) rm -f "$C/sessions/${a[2]}/herdr.sock"; exit 0;;
  "session delete "*) rm -rf "${C:?}/sessions/${a[2]}"; exit 0;;
esac
[[ -n "${FAKE_HERDR_LEAK:-}" ]] && { echo '{"session":"default"}'; exit 0; }
[[ -f "$sock" ]] || { echo server_not_running >&2; exit 1; }
case "${a[*]}" in   # one pane per workspace; `pane run` starts its command detached, as the server would
  "workspace create"*) echo '{"result":{"root_pane":{"pane_id":"w1:p1"}}}'; exit 0;;
  "pane run "*) echo "{\"pane_id\":\"${a[2]}\"}" >> "${sock%/*}/panes"; setsid sh -c "${a[*]:3}" < /dev/null > /dev/null 2>&1 & exit 0;;
  "pane list") cat "${sock%/*}/panes" 2>/dev/null; exit 0;;
esac
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
  writes) echo hacked > judge-was-here; mkdir -p scratch; echo ignored > scratch/fine; printf '```json\n{"criteria": []}\n```\n' ;;
  tracked) echo hacked >> .gitignore; rm docs/specs/demo.spec.html; printf "$ok" ;;
  copycreds) mkdir -p scratch; cp -p "$HOME/.pi/agent/auth.json" scratch/a; cp -p "$HOME/.pi/agent/models.json" .git/m; printf "$ok" ;;
  bigcopy) mkdir -p scratch; cp "$HOME/.pi/agent/auth.json" scratch/big; truncate -s 67108865 scratch/big; printf "$ok" ;;
  refresh)   # auth A becomes B, keep B, B becomes C (a refresh between two judge copies), and stash into HOME
    rf() { echo "{\"k\": \"SECRET-pi-auth-$1-987654\", \"exp\": 2}" > "$HOME/.pi/agent/auth.json.new" && mv "$HOME/.pi/agent/auth.json.new" "$HOME/.pi/agent/auth.json" \
      || echo "{\"k\": \"SECRET-pi-auth-$1-987654\", \"exp\": 2}" > "$HOME/.pi/agent/auth.json"; }
    mkdir -p scratch; rf B; cp "$HOME/.pi/agent/auth.json" scratch/oldauth; cp "$HOME/.pi/agent/auth.json" .git/oldauth
    cp "$HOME/.pi/agent/auth.json" "$HOME/oldauth" 2>/dev/null; rf REFRESHED
    printf "$ok" ;;
  savedcopy)   # persist a copy inside auth.json itself: an added key
    python3 - "$HOME/.pi/agent/auth.json" <<'P'
import json, sys
a = json.load(open(sys.argv[1])); a["saved_copy"] = dict(a); open(sys.argv[1], "w").write(json.dumps(a))
P
    printf "$ok" ;;
  race)   # refresh in place, then wait while the box's own Pi refreshes auth.json (the test, outside)
    echo '{"k": "SECRET-pi-auth-JUDGE-987654", "exp": 3}' > "$HOME/.pi/agent/auth.json"
    sleep 3013@TOK@ < /dev/null > /dev/null 2>&1 &
    for _ in $(seq 100); do [[ -e "$FAKE_GO" ]] && break; sleep 0.1; done
    printf "$ok" ;;
  token)   # only extracted values, as jq -r would print them: no whole-file match
    mkdir -p scratch; python3 -c 'import json,sys; print("x", json.load(open(sys.argv[1]))["k"], "y")' "$HOME/.pi/agent/auth.json" > scratch/tok
    python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["providers"]["p"]["apiKey"])' "$HOME/.pi/agent/models.json" > .git/tok2
    printf "$ok" ;;
  pane)   # spawn a pane through the sandbox herdr; it reports what it sees, then tries to outlive the run
    mkdir -p scratch; rm -f scratch/pane.txt
    cat > scratch/pane.sh <<'P'
{ echo "pane pidns $(readlink /proc/self/ns/pid)"
  for h in $(type -ap herdr); do for s in default qclive; do
    "$h" --session "$s" workspace list 2>/dev/null | grep -q '"default"\|QCLIVE' && echo "ESCAPE pane reached Herdr $s via $h"; done; done
  cat "$HOME/.config/herdr/herdr.sock" "$HOME/.config/gh/hosts.yml" "$HOME/.git-credentials" 2>/dev/null | grep -q 'SECRET\|default' && echo "ESCAPE pane creds or live socket"
  env | grep -q SECRET && echo "ESCAPE pane token in env"
  echo "PANE done"; } > "$1.tmp"; mv "$1.tmp" "$1"
exec sleep 303031@TOK@
P
    id=$(herdr workspace create --cwd "$PWD" --no-focus | grep -o '"pane_id":"[^"]*"' | head -1 | cut -d'"' -f4)
    herdr pane run "$id" "bash $PWD/scratch/pane.sh $PWD/scratch/pane.txt" > /dev/null
    for _ in $(seq 100); do [[ -f scratch/pane.txt ]] && break; sleep 0.1; done
    echo "judge pidns $(readlink /proc/self/ns/pid)"; cat scratch/pane.txt 2>/dev/null || echo "MISSING pane output (pane $id)"
    printf "$ok" ;;
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
    # Review exploits (#33 round 2): undo a mask, outlive the run, keep a credential copy.
    for m in "$HOME/.git-credentials" "$HOME/.config/herdr" "$L/lanes"; do
      umount "$m" 2>/dev/null; unshare -rm sh -c 'umount "$1" 2>/dev/null; cat "$1/../.git-credentials" "$1/herdr.sock" "$1/gh9.toml" 2>/dev/null' _ "$m" | grep -q 'SECRET\|default\|LIVE' && echo "ESCAPE umount $m"
    done
    grep -q SECRET "$HOME/.git-credentials" 2>/dev/null && echo "ESCAPE umount revealed git creds"
    unshare -rm env -u HERDR_SESSION sh -c 'exec sleep 302921@TOK@' < /dev/null > /dev/null 2>&1 &
    mkdir -p "$HOME/qc-saved" 2>/dev/null && cp -p "$HOME/.pi/agent/auth.json" "$HOME/.pi/agent/models.json" "$HOME/qc-saved/" 2>/dev/null
    setsid sleep 3012@TOK@ < /dev/null > /dev/null 2>&1 &
    pi --version
    printf "$ok" ;;
esac
EOF
# Survivor checks key on a per-run token in the sleeps' argv, so concurrent test runs never collide.
tok="$(od -An -N4 -tu4 /dev/urandom | tr -d ' ')$$"; sed -i "s/@TOK@/$tok/g" "$t/bin/pi" "$t/fakeherdr/herdr"
chmod +x "$t/bin/pi" "$t/fakeherdr/herdr"; base="$t/bin:$kit/scripts:$PATH"; export PATH="$t/bin:$t/fakeherdr:$kit/scripts:$PATH"
# Sandbox Herdr mode for the pane test: the real herdr when installed (the box), else the fake (CI).
real="$(PATH="$base" command -v herdr || true)"; mode=fake
[[ -n "$real" && "${QC_TEST_HERDR:-}" != fake ]] && mode=real
echo "qc test: sandbox Herdr mode: $mode${real:+ ($real)}" >&2
cp "$kit/tests/fixtures/spec-status/good/demo.spec.html" "$t/repo/docs/specs/"
cd "$t/repo"; git init -q -b main .
"$S" init docs/specs/demo.spec.html 0123abc >/dev/null; echo scratch/ > .gitignore; git add -A; git commit -qm spec
st=docs/specs/demo.status.json
run() { local want="$1"; shift; set +e; out="$(FAKE_QC="$1" "$Q" "${@:2}" 2>&1)"; rc=$?; set -e
  [[ "$rc" == "$want" ]] || fail "FAKE_QC=$1 '${*:2}' want exit $want, got $rc: $out"; }
report() { python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))'"$1"')' "$(ls -t "$t"/reports/*.json | head -1)"; }
OCTO_FEATHER_QC_MODEL=anthropic/claude-opus-5-5 run 64 mixed $st 5 acceptance-a acceptance-b   # judge of the implementer's family
echo x > dirty; run 65 mixed $st 5 acceptance-a; rm dirty                                      # dirty worktree
before="$(git rev-parse HEAD)"
run 3 garbage $st 5 acceptance-a acceptance-b                                                   # no json report
run 3 writes $st 5 acceptance-a                                                                 # judge wrote a non-ignored file
grep -q "new judge-was-here" <<< "$out" && ! grep -q scratch/fine <<< "$out" || fail "non-ignored write not listed alone: $out"
run 3 tracked $st 5 acceptance-a                                                                # judge changed and deleted tracked files
grep -q "changed .gitignore; deleted docs/specs/demo.spec.html" <<< "$out" || fail "tracked writes not listed: $out"
[[ "$(git rev-parse HEAD)" == "$before" && -z "$(git status --porcelain --ignored)" ]] || fail "refused run changed the real worktree"
[[ "$(find "$t/reports" -name "$before-*.json" | wc -l)" == 3 ]] || fail "three runs at one head must leave three reports"
grep -q "qc sandbox: ok   live Herdr unreachable" <<< "$out" || fail "no pre-run proof printed: $out"
grep -q "qc sandbox: ok   worktree $PWD is an overlay" <<< "$out" && grep -q "qc sandbox: ok   writable persistent paths: none" <<< "$out" \
  || fail "no overlay / persistent-writable proof: $out"

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
[[ "$(report '["sandbox"]["left_after_kill"]')" == 0 && "$(report '["worktree_writes"]')" == "[]" ]] \
  || fail "cleanup record: $(report '["sandbox"]')"
for p in "sleep 3012" "sleep 302921"; do
  report '["sandbox"]["killed"]' | grep -q "$p" || fail "leftover '$p' not killed and counted: $(report '["sandbox"]')"
done
! pgrep -fx "sleep (301[12]|302921)$tok" >/dev/null || fail "sandbox processes survived the run"
[[ ! -e "$HOME/qc-saved" ]] || fail "judge wrote into HOME"

# Credential copies cannot survive anywhere: every judge write (ignored scratch/, .git, any size, a copy of an
# intermediate auth.json between two refreshes, token values alone) lives in the overlay and dies with the run.
copycase() { run 0 "$1" $st 5 acceptance-a; local f; for f in "${@:2}"; do [[ ! -e "$f" ]] || fail "$1: credential copy $f survived"; done
  [[ -z "$(git status --porcelain --ignored)" ]] || fail "$1: worktree not pristine: $(git status --porcelain --ignored)"
  ! grep -rqa 'SECRET-pi' . "$HOME" --exclude-dir=.pi || fail "$1: a Pi credential survived: $(grep -rla 'SECRET-pi' . "$HOME" --exclude-dir=.pi)"
  echo "qc test: $1: ${*:2} discarded with the run ($(report '["discarded_writes"]') writes), exit 0" >&2; }
copycase copycreds scratch/a .git/m
copycase bigcopy scratch/big
pa="$HOME/.pi/agent/auth.json"; orig="$(cat "$pa")"
piok() { [[ "$(ls -A "$HOME/.pi/agent" | tr '\n' ' ')" == "auth.json models.json " && "$(stat -c %a "$pa")" == 600 ]] \
  || fail "$1: Pi dir holds a stray file or auth.json mode changed: $(ls -lA "$HOME/.pi/agent")"
  [[ "$(report '["sandbox"]["auth_writeback"]')" == "$2" ]] && grep -q "qc: cleanup: auth_writeback: $2" <<< "$out" \
  || fail "$1: want auth_writeback $2, got $(report '["sandbox"]["auth_writeback"]')"; }
# The judge stores a copy under a new key in auth.json: refused, the box file byte-identical.
copycase savedcopy; piok savedcopy refused:keys-changed
[[ "$(cat "$pa")" == "$orig" ]] || fail "savedcopy: box auth.json changed"
# The box's own Pi refreshes auth.json while the judge also refreshes its copy: the box value is kept.
(for _ in $(seq 100); do pgrep -fx "sleep 3013$tok" > /dev/null && break; sleep 0.1; done
 echo '{"k": "SECRET-pi-auth-BOX-987654", "exp": 4}' > "$pa"; touch "$t/bin/go") &
FAKE_GO="$t/bin/go" copycase race; wait; rm -f "$t/bin/go"; piok race refused:box-auth-changed
[[ "$(cat "$pa")" == '{"k": "SECRET-pi-auth-BOX-987654", "exp": 4}' ]] || fail "race: box value not kept"
# The final window: a box Pi takes '<auth>.lock' (proper-lockfile) while the judge runs, holds it as qc reaches
# write-back, then writes in place and releases. qc waits for the lock, never writes under it, and keeps the Pi value.
orig="$(cat "$pa")"
(for _ in $(seq 100); do pgrep -fx "sleep 3013$tok" > /dev/null && break; sleep 0.1; done
 mkdir "$pa.lock"; seen="$(cat "$pa")"; touch "$t/bin/go"; sleep 2
 [[ "$(cat "$pa")" == "$seen" ]] || touch "$t/clobbered"
 echo '{"k": "SECRET-pi-auth-LOCKED-987654", "exp": 5}' > "$pa"; rmdir "$pa.lock") &
FAKE_GO="$t/bin/go" copycase race; wait; rm -f "$t/bin/go"; piok lockedrace refused:box-auth-changed
[[ ! -e "$t/clobbered" && "$(cat "$pa")" == '{"k": "SECRET-pi-auth-LOCKED-987654", "exp": 5}' ]] \
  || fail "lockedrace: qc wrote auth.json under Pi's lock or lost the Pi value"
# A lock held past the bound (stale by mtime, too): refused:auth-locked, box and lock dir untouched.
mkdir "$pa.lock"; touch -d '-1 hour' "$pa.lock"; lm="$(stat -c %Y "$pa.lock")"; orig="$(cat "$pa")"
copycase refresh scratch/oldauth .git/oldauth "$HOME/oldauth"
[[ "$(report '["sandbox"]["auth_writeback"]')" == refused:auth-locked && "$(cat "$pa")" == "$orig" && -d "$pa.lock" \
   && "$(stat -c %Y "$pa.lock")" == "$lm" && -z "$(ls -A "$pa.lock")" ]] \
  || fail "held lock: want refused:auth-locked, box and lock untouched, got $(report '["sandbox"]["auth_writeback"]')"
rmdir "$pa.lock"
# A token refresh in place (intermediate copies anywhere discarded): written back, the new value only.
copycase refresh scratch/oldauth .git/oldauth "$HOME/oldauth"; piok refresh written
[[ "$(cat "$pa")" == '{"k": "SECRET-pi-auth-REFRESHED-987654", "exp": 2}' ]] || fail "refresh case did not write back the new token"
grep -q "qc sandbox: ok   writable persistent paths: none$" <<< "$out" || fail "proof must say writable persistent paths: none: $out"
copycase token scratch/tok .git/tok2; piok token none
ls -d /tmp/qc-escape-* 2>/dev/null && fail "judge's /tmp writes survived"
[[ ! -e "$live/lanes/escaped" && "$(cat "$live/lanes/archive/gh1.toml")" == ARCHIVED && "$(wc -l < "$live/director.handoffs.jsonl")" == 1 ]] \
  || fail "judge wrote live state"
[[ ! -e "$HOME/.config/herdr/sessions" ]] || fail "sandbox Herdr session left in the real config dir"

# A pane the judge spawns through the sandbox herdr runs in the judge's PID namespace (the sandbox
# server started inside it), sees no live Herdr socket and no creds, and dies with the run.
pp="$t/bin:$t/fakeherdr:$kit/scripts:$PATH"
if [[ "$mode" == real ]]; then   # a real "live" Herdr session under the throwaway HOME
  pp="$base"
  setsid sh -c 'echo $$ > "$1"; exec "$2" --session qclive server' _ "$t/pids/qclive" "$real" < /dev/null > /dev/null 2>&1 &
  for _ in $(seq 50); do "$real" --session qclive workspace list > /dev/null 2>&1 && break; sleep 0.2; done
  "$real" --session qclive workspace create --label QCLIVE --cwd "$t" --no-focus > /dev/null || fail "real herdr: live test session did not start"
fi
PATH="$pp" run 0 pane $st 5 acceptance-a
judge="$(report '["stdout"]')"
grep -E 'ESCAPE|MISSING' <<< "$judge" && fail "sandbox pane escape ($mode herdr): $judge"
grep -q "PANE done" <<< "$judge" || fail "pane never ran ($mode herdr): $judge"
[[ "$(grep 'judge pidns' <<< "$judge" | cut -d' ' -f3)" == "$(grep 'pane pidns' <<< "$judge" | cut -d' ' -f3)" \
  && "$(grep 'pane pidns' <<< "$judge" | cut -d' ' -f3)" != "$(readlink /proc/self/ns/pid)" ]] \
  || fail "pane not in the judge's PID namespace ($mode herdr): $judge"
[[ "$(report '["sandbox"]["herdr_panes"]')" == 1 ]] || fail "pane not counted ($mode herdr): $(report '["sandbox"]')"
sleep 0.3; ! pgrep -fx "sleep 303031$tok" > /dev/null || fail "judge's pane survived the run ($mode herdr)"
if [[ "$mode" == real ]]; then
  "$real" --session qclive workspace list > /dev/null 2>&1 || fail "the run hurt the live Herdr session"
  [[ "$(ls "$HOME/.config/herdr/sessions")" == qclive ]] || fail "sandbox session left: $(ls "$HOME/.config/herdr/sessions")"
fi
[[ ! -e scratch ]] || fail "pane run's scratch survived"

# The qc recipes pass arguments as data, never as shell source.
for jf in "$kit/justfile" "$kit/templates/python/justfile" "$kit/templates/typescript/justfile"; do
  set +e; o="$(just --justfile "$jf" --working-directory "$t/repo" qc "$st" 5 'acceptance-a$(touch pwned)' 'x;touch pwned2' 2>&1)"; rc=$?; set -e
  [[ "$rc" != 0 && ! -e pwned && ! -e pwned2 && ! -e "$kit/pwned" ]] || fail "$jf qc ran its arguments as shell (exit $rc): $o"
  grep -q 'not in docs/specs/demo.status.json: acceptance-a$(touch pwned) x;touch pwned2' <<< "$o" || fail "$jf qc mangled its arguments: $o"
done
echo "qc: ok (pass flips built, fail stays planned, status-only commit, same family, dirty, unusable report, judge wrote (non-ignored, tracked), unique reports, sandbox escapes, no persistent write (credential copies: >64 MiB, intermediate refresh, token only, HOME; auth.json: added key refused, refresh written, box race kept, Pi auth lock waited for and never stolen), proof abort, cleanup count, judge pane in the sandbox ($mode herdr), --no-sandbox, recipe args as data)"
