#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qc with a fake `pi` and a fake
# `herdr` on PATH (no model call; a real Herdr only in the pane test on a box): only passed criteria
# become built, one status-only commit, a same-family judge, a dirty tree, an
# unusable report and a judge that writes are refused, reports never overwrite;
# the sandbox (#33): a judge trying each escape fails at every one, a failed
# proof aborts before the judge, leftovers are killed and agents counted,
# masks cannot be unmounted, a nested-namespace survivor dies, no judge write
# persists (the worktree is an overlay on the run tmpfs; credential copies vanish), a pane
# the judge spawns runs in its PID namespace and dies with it (the fake herdr; the box's
# real herdr only with QC_TEST_HERDR=real, `just qc-real-herdr`; the test prints which),
# --no-sandbox never commits, and the qc recipes pass arguments as data.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`).
# Offline and bounded (#55): the test re-runs itself in a fresh user+network namespace
# (`unshare -cn`, no route anywhere, proved below), each qc run is killed after
# QC_TEST_RUN_TIMEOUT s (default 90) and the whole test after QC_TEST_TIMEOUT s (default 600),
# failing with a message naming what hung.
set -euo pipefail
# A test harness, not a gate recipe reaching the judge: its fake-pi runs start outside any check run (the one
# boundary; octo-feather-qc refuses under the marker, whatever pi it would launch).
unset OCTO_FEATHER_CHECK_RUN
# The qc sandbox is Linux-only (unshare, /proc); CI runs this on Linux.
[[ "$(uname -s)" != Darwin ]] || { echo "qc: skipped, not on macOS (just qc needs Linux; CI runs it)"; exit 0; }
if [[ -z "${QC_TEST_NETNS:-}" ]]; then
  unshare -cn true 2>/dev/null || { echo "qc test: unshare -cn failed: the test runs offline in a user+network namespace (enable unprivileged user namespaces)" >&2; exit 1; }
  set +e; QC_TEST_NETNS=1 timeout -k 10 "${QC_TEST_TIMEOUT:-600}" unshare -cn "$0" "$@"; rc=$?; set -e
  [[ "$rc" != 124 && "$rc" != 137 ]] || echo "qc test: timed out after ${QC_TEST_TIMEOUT:-600} s (QC_TEST_TIMEOUT), killed" >&2
  exit "$rc"
fi
fail() { echo "qc test: $*" >&2; exit 1; }
python3 - <<'EOF' || fail "network reachable: the test must run with no route (unshare -cn)"
import errno, socket, sys
for fam, addr in ((socket.AF_INET, ("192.0.2.1", 9)), (socket.AF_INET6, ("2001:db8::1", 9))):
    try:
        s = socket.socket(fam, socket.SOCK_STREAM); s.settimeout(2); s.connect(addr)
    except OSError as e:
        if e.errno in (errno.ENETUNREACH, errno.EAFNOSUPPORT, errno.EADDRNOTAVAIL):
            continue
        sys.exit(f"{addr[0]}: {e}")
    sys.exit(f"{addr[0]}: connected")
EOF
echo "qc test: offline: no route to any network (user+network namespace)" >&2
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
Q="$kit/scripts/octo-feather-qc"; S="$kit/scripts/octo-feather-spec-status"
t="$(mktemp -d)"
stop() { local f p; [[ "$BASHPID" == "$$" ]] || return 0   # the test shell only, never a killed command substitution
  for f in "$t"/pids/*; do [[ -f "$f" ]] || continue; p="$(cat "$f")"; kill -- -"$p" 2>/dev/null || true
    for _ in $(seq 50); do kill -0 -- -"$p" 2>/dev/null || break; sleep 0.1; done; kill -9 -- -"$p" 2>/dev/null || true; done   # a Herdr server writes its snapshot as it exits
  rm -rf "$t"; }
trap stop EXIT; trap 'trap "" TERM; exit 143' TERM   # timeout signals twice (child, group): the 2nd must not cut stop short
export TMPDIR="$t/tmp"; mkdir "$TMPDIR"   # qc's scratch (miss logs) lives under $t: a killed test leaves nothing
lim="${QC_TEST_RUN_TIMEOUT:-90}"
# One qc run; 124/137: it hung and was killed. timeout gives the run its own process group, so a killed test
# reaches it only through stop (pids/run): the run reclaims its scratch before $t goes.
bounded() { timeout -k 5 "$lim" "$@" & echo $! > "$t/pids/run"; wait $!; set -- $?; rm -f "$t/pids/run"; return "$1"; }
hung() { [[ "$1" != 124 && "$1" != 137 ]] || fail "$2 hung: no exit after ${lim} s (QC_TEST_RUN_TIMEOUT), killed: ${3:-}"; }
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
vc0="${XDG_CACHE_HOME:-$HOME/.cache}/octo-feather/skillfile"   # the caller's warm check-vendored cache (#69)
# A throwaway HOME holding a "live" box: a live Herdr session, gh and git creds, live and archived lanes.
export HOME="$t/home" OCTO_FEATHER_QC_DIR="$t/reports"
unset XDG_CONFIG_HOME XDG_STATE_HOME XDG_CACHE_HOME GH_CONFIG_DIR HERDR_SESSION HERDR_SOCKET_PATH HERDR_BIN_PATH HERDR_ENV
export LINEAR_API_KEY=SECRET-linear-key GH_TOKEN=SECRET-token OCTO_FEATHER_PARENT=wX:p9 HERDR_PANE_ID=p9 HERDR_TAB_ID=t9 HERDR_WORKSPACE_ID=w9 OCTO_FEATHER_SPEND_SPACE=w9
live="$HOME/.local/state/octo-feather"
mkdir -p "$HOME/.config/herdr" "$HOME/.config/gh" "$live/lanes/archive" "$t/bin" "$t/fakeherdr" "$t/pids" "$t/repo/docs/specs"
echo default > "$HOME/.config/herdr/herdr.sock"
echo 'oauth_token: SECRET-gh' > "$HOME/.config/gh/hosts.yml"; echo 'https://x:SECRET-git@github.com' > "$HOME/.git-credentials"
echo LIVE > "$live/lanes/gh9.toml"; echo ARCHIVED > "$live/lanes/archive/gh1.toml"; echo '{"director":1}' > "$live/director.handoffs.jsonl"
echo 'pane = "LIVE"' > "$live/director.toml"
git init -q "$HOME/src/sib"; echo SIBSECRET > "$HOME/src/sib/notes.md"   # another repo on the box (#182)
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
[[ -z "${LINEAR_API_KEY+x}" ]] || echo "LINEAR KEY IN JUDGE ENV"   # remote#acceptance-linear-key-qc
h="$(grep -o 'head [0-9a-f]\{40\}' <<< "$*" | head -1 | cut -d' ' -f2)"   # the judged head, from the brief
ok='```json\n{"head": "'"$h"'", "criteria": [{"id": "acceptance-a", "verdict": "pass", "command": "app a --json", "output": "ok", "why": "shown"}]}\n```\n'
case "$FAKE_QC" in
  dup) printf '```json\n{"head": "%s", "criteria": [{"id": "acceptance-a", "verdict": "pass", "command": "a", "output": "ok"}, {"id": "acceptance-a", "verdict": "fail", "command": "a", "output": "no"}, {"id": "acceptance-b", "verdict": "pass", "command": "b", "output": "ok"}]}\n```\n' "$h" ;;
  head) printf "${ok//$h/0000000000000000000000000000000000000000}" ;;
  mixed) printf 'done\n```json\n{"head": "'"$h"'", "criteria": [{"id": "acceptance-a", "verdict": "pass", "command": "app a --json", "output": "{\\"ok\\": true}", "why": "shown"}, {"id": "acceptance-b", "verdict": "fail", "command": "app b --json", "output": "error", "why": "no b"}]}\n```\n' ;;
  garbage) echo "I think it works." ;;
  argv) python3 -c 'import json, sys; print("ARGV", json.dumps(sys.argv[1:]))' "$@"; printf "$ok" ;;
  hang) exec sleep 3040@TOK@ ;;
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
  rewrite)   # rewrite both Pi files in place; the judge sees its own writes
    echo '{"k": "SECRET-pi-auth-JUDGE-987654", "exp": 3}' > "$HOME/.pi/agent/auth.json"
    echo '{"providers": {"p": {"apiKey": "SECRET-pi-models-JUDGE-987654"}}}' > "$HOME/.pi/agent/models.json"
    if grep -q JUDGE "$HOME/.pi/agent/auth.json" && grep -q JUDGE "$HOME/.pi/agent/models.json"; then printf "$ok"; else echo "copies not writable"; fi ;;
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
  vendored)   # `just check`'s check-vendored on the kit reads the cache; every write into it fails
    vc="$HOME/.cache/octo-feather/skillfile"; kit="$(dirname "$(command -v octo-feather-state)")/.."
    just --justfile "$kit/justfile" check-vendored 2>&1 | grep -q '^vendored: ok' && echo "VENDORED green" || echo "MISSING check-vendored green"
    touch "$vc/judge" 2>/dev/null && echo "ESCAPE wrote new file in cache"
    b="$(find "$vc/bin" -type f | head -1)"; (: >> "$b") 2>/dev/null && echo "ESCAPE opened cached binary for write"
    rm -rf "$vc/git" 2>/dev/null; [[ -d "$vc/git" ]] || echo "ESCAPE deleted cached git"
    unshare -rm sh -c 'mount -o remount,bind,rw "$1" && touch "$1/judge2"' _ "$vc" 2>/dev/null && echo "ESCAPE remounted cache rw"
    printf "$ok" ;;
  nested)   # `just check` in the sandbox runs this test (fresh HOME, its own state): a sandboxed qc inside the judge's gets past its proof
    h="$(mktemp -d)"; git clone -q "$PWD" "$h/repo"   # its own worktree: the outer overlay is covered there
    # The judge's PATH as is: `herdr` there is the outer sandbox's shim; the nested run wraps the real (fake) binary.
    o="$(cd "$h/repo" && env -u XDG_STATE_HOME -u HERDR_SESSION -u HERDR_SOCKET_PATH -u HERDR_BIN_PATH HOME="$h" PATH="${0%/pi}:$PATH" \
      FAKE_QC=garbage octo-feather-qc docs/specs/demo.status.json 5 acceptance-a 2>&1)"; echo "NESTED exit $?"
    grep -q 'qc sandbox: ok   writable persistent paths: none$' <<< "$o" && grep -q 'qc sandbox: ok   [1-9][0-9]* writable mounts covered' <<< "$o" \
      || echo "MISSING nested proof: $o"
    grep -q 'qc sandbox: ok   live Herdr unreachable: raw herdr --session default workspace list exits 1$' <<< "$o" \
      && grep -q 'qc sandbox: ok   herdr shim pins sandbox session' <<< "$o" && grep -q 'qc sandbox: ok   Herdr config shows only the sandbox session' <<< "$o" \
      || echo "MISSING nested Herdr proof (real binary, not the outer shim): $o"
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
    [[ -n "${OCTO_FEATHER_PARENT:-}${HERDR_PANE_ID:-}${HERDR_TAB_ID:-}${HERDR_WORKSPACE_ID:-}${OCTO_FEATHER_SPEND_SPACE:-}" ]] && echo "ESCAPE parent route"
    d="$(mktemp -d /tmp/qc-escape-XXXXXX)"; echo k > "$d/auth.json"; echo m > "$d/models.json"
    L="$HOME/.local/state/octo-feather"; st="$(octo-feather-state)"
    grep -q LIVE "$L/lanes/gh9.toml" "$L/director.toml" 2>/dev/null && echo "ESCAPE read live lanes"
    ls -A "$HOME/src/sib" 2>/dev/null | grep -q notes && echo "ESCAPE listed another repo"
    grep -q SIBSECRET "$HOME/src/sib/notes.md" 2>/dev/null && echo "ESCAPE read another repo"
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
# Sandbox Herdr mode for the pane test: the fake, on every box and in CI; the box's real herdr
# only on explicit opt-in (QC_TEST_HERDR=real, `just qc-real-herdr`), never by presence on PATH.
mode="${QC_TEST_HERDR:-fake}"; real=""
case "$mode" in
  fake) ;;
  real) real="$(PATH="$base" command -v herdr)" || fail "QC_TEST_HERDR=real but no herdr on PATH";;
  *) fail "QC_TEST_HERDR must be fake or real, got '$mode'";;
esac
echo "qc test: sandbox Herdr mode: $mode${real:+ ($real)}" >&2
cp "$kit/tests/fixtures/spec-status/good/demo.spec.html" "$t/repo/docs/specs/"
cd "$t/repo"; git init -q -b main .
git add -A; git commit -qm accepted; "$S" init docs/specs/demo.spec.html "$(git rev-parse --short HEAD)" >/dev/null
echo scratch/ > .gitignore; git add -A; git commit -qm spec
st=docs/specs/demo.status.json
run() { local want="$1"; shift; set +e; out="$(FAKE_QC="$1" bounded "$Q" "${@:2}" 2>&1)"; rc=$?; set -e
  hung "$rc" "FAKE_QC=$1 '${*:2}'" "$out"
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
grep -q "qc sandbox: ok   vendored-skill cache: none on the box, nothing bound" <<< "$out" || fail "absent cache: want no bind, no failure: $out"
# issue-lifecycle#acceptance-qc-interim, #acceptance-one-head (#121 D19 D20): a duplicate id, another head.
run 3 dup $st 5 acceptance-a acceptance-b                                                       # acceptance-a judged twice
grep -q "judged more than once: acceptance-a" <<< "$out" || fail "duplicate id not named: $out"
run 3 head $st 5 acceptance-a                                                                   # report for another head
grep -q "report head '0000000000000000000000000000000000000000' is not the judged head $before" <<< "$out" || fail "wrong head not named: $out"
[[ "$(git rev-parse HEAD)" == "$before" && -z "$(git status --porcelain)" ]] || fail "unusable report changed the status file"

# --no-sandbox: printed, report written, status never changes.
run 1 mixed $st 5 acceptance-a acceptance-b --no-sandbox
grep -q UNSANDBOXED <<< "$out" || fail "--no-sandbox not printed: $out"
[[ "$(git rev-parse HEAD)" == "$before" && -z "$(git status --porcelain)" ]] || fail "--no-sandbox changed the status file"
[[ "$(report '["sandbox"]')" == False ]] || fail "--no-sandbox report must record sandbox false"
! report '["stdout"]' | grep -q "LINEAR KEY IN JUDGE ENV" || fail "--no-sandbox judge got LINEAR_API_KEY"
# A run killed mid-judge (as a timeout kills it: SIGTERM to its process group) leaves no scratch behind.
FAKE_QC=hang timeout -k 5 "$lim" "$Q" $st 5 acceptance-a --no-sandbox > /dev/null 2>&1 & hp=$!; echo "$hp" > "$t/pids/run"
for _ in $(seq 100); do compgen -G "$TMPDIR/qc-ghmiss-*" > /dev/null && break; sleep 0.1; done
compgen -G "$TMPDIR/qc-ghmiss-*" > /dev/null || fail "hang run: no scratch before the judge (nothing to prove)"
kill -TERM "$hp"; set +e; wait "$hp"; rc=$?; set -e; rm -f "$t/pids/run"
[[ "$rc" != 0 ]] || fail "hang run exited 0"
sleep 0.2; [[ -z "$(ls -A "$TMPDIR")" ]] || fail "killed run left scratch: $(ls -A "$TMPDIR")"
! pgrep -fx "sleep 3040$tok" > /dev/null || fail "killed run's judge survived"

run 1 mixed $st 5 acceptance-a acceptance-b                                                     # a passes, b fails
python3 - "$st" <<'EOF'
import json, sys
c = json.load(open(sys.argv[1]))["criteria"]
assert c["acceptance-a"] == {"status": "built", "pr": 5}, c
assert c["acceptance-b"] == {"status": "planned", "pr": None}, c
EOF
[[ "$(git diff --name-only "$before" HEAD)" == "$st" && "$(git rev-list --count "$before"..HEAD)" == 1 ]] \
  || fail "expected one commit touching only the status file"

# The judge launches from its own role file (agents/qc-judge.md), its model read from there: never code-reviewer.md.
run 0 argv $st 5 acceptance-a
judge="$(report '["stdout"]')"
python3 - "$kit/agents/qc-judge.md" "$judge" <<'EOF' || fail "judge not launched from agents/qc-judge.md: ${judge:0:600}"
import json, os, re, sys
fm, body = re.match(r"---\n(.*?)\n---\n?(.*)", open(sys.argv[1]).read(), re.S).groups()
fm = dict(l.split(": ", 1) for l in fm.splitlines())
a = json.loads(next(l for l in sys.argv[2].splitlines() if l.startswith("ARGV "))[5:])
val = lambda f: [a[i + 1] for i, x in enumerate(a) if x == f]
assert val("--append-system-prompt") == [body.strip()], "role prompt is not qc-judge.md's body"
assert set(val("--model")) == {fm["model"]}, f"model {val('--model')} != {fm['model']}"
assert sorted(os.path.basename(s) for s in val("--skill")) == sorted(s.strip() for s in fm["skills"].split(",")), val("--skill")
EOF

# A failed proof check aborts before the judge: here raw herdr still reaches a live session.
FAKE_HERDR_LEAK=1 run 66 escape $st 5 acceptance-a
grep -q "FAIL live Herdr unreachable" <<< "$out" || fail "leaking Herdr not caught by the proof: $out"
[[ "$(report '.get("stdout", "none")')" == none ]] || fail "judge started after a failed proof"

# remote#acceptance-linear-key-qc: a Linear key re-entering the judge's env (here a BASH_ENV that exports it
# again after the scrub) fails the proof, so the judge never starts; the plain run below proves it absent.
printf 'export LINEAR_API_KEY=SECRET-linear-leak\n' > "$t/bin/leak.env"
BASH_ENV="$t/bin/leak.env" run 66 escape $st 5 acceptance-a
grep -q "FAIL no tracker credential: LINEAR_API_KEY set 1 times" <<< "$out" || fail "leaking Linear key not caught by the proof: $out"
[[ "$(report '.get("stdout", "none")')" == none ]] || fail "judge started with a Linear key in its env"

# A mask over another repo that cannot be set up (here a path to bind back on it is missing) aborts before the judge.
OCTO_FEATHER_QC_RO_BINDS="$HOME/src/sib/missing" run 66 escape $st 5 acceptance-a
grep -q "qc sandbox: FAIL bind back $HOME/src/sib/missing on the mask over $HOME/src/sib" <<< "$out" || fail "a failed repo mask not named: $out"
[[ "$(report '.get("stdout", "none")')" == none ]] || fail "judge started after a failed repo mask"

# Every escape fails; leftovers killed, agents counted, credential copies gone, live records untouched.
run 0 escape $st 5 acceptance-a
judge="$(report '["stdout"]')"
grep -E 'ESCAPE|MISSING|LINEAR KEY' <<< "$judge" && fail "sandbox escape: $judge"
grep -q "qc sandbox: ok   no tracker credential: LINEAR_API_KEY set 0 times" <<< "$out" || fail "no Linear key proof: $out"
grep -q "qc sandbox: ok   parent route unset: 0 of OCTO_FEATHER_PARENT/SESSION_ID/ROLE/SPEND_SPACE," <<< "$out" || fail "no route proof naming the spend space: $out"
grep -q "qc sandbox: ok   other repos hidden: 1 git repos under $HOME .*: src/sib; visible: kit under test $kit, worktree $PWD$" <<< "$out" \
  || fail "no other-repos proof naming the mask and what stays visible: $out"
report '["sandbox"]["attempts"]' | grep -q "'kind': 'repo', 'attempt': True, 'refused': True, 'what': 'open $HOME/src/sib'" \
  || fail "the listing of another repo not recorded and refused: $(report '["sandbox"]')"
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
pa="$HOME/.pi/agent/auth.json"; pm="$HOME/.pi/agent/models.json"; cp -p "$pa" "$t/auth0"; cp -p "$pm" "$t/models0"
piok() { [[ "$(ls -A "$HOME/.pi/agent" | tr '\n' ' ')" == "auth.json models.json " && "$(stat -c %a "$pa")" == 600 ]] \
  || fail "$1: Pi dir holds a stray file or auth.json mode changed: $(ls -lA "$HOME/.pi/agent")"
  cmp -s "$pa" "$t/auth0" && cmp -s "$pm" "$t/models0" || fail "$1: box auth.json or models.json changed (never written back)"
  ! grep -q "auth_writeback" <<< "$out$(report '["sandbox"]')" || fail "$1: auth_writeback still reported"; }
# The judge rewrites both Pi files: its per-run copies, discarded; the box files byte-identical; no OAuth warning.
copycase rewrite; piok rewrite
! grep -q "OAuth" <<< "$out" || fail "rewrite: OAuth warning without OAuth credentials: $out"
# A token refresh in place (intermediate copies anywhere discarded): discarded too, never written back.
copycase refresh scratch/oldauth .git/oldauth "$HOME/oldauth"; piok refresh
grep -q "qc sandbox: ok   writable persistent paths: none$" <<< "$out" || fail "proof must say writable persistent paths: none: $out"
copycase token scratch/tok .git/tok2; piok token
# OAuth credentials on the box (type oauth, or only a refresh token field): one warning line, the run proceeds.
cp -p "$pa" "$t/auth-plain"
for a in '{"anthropic": {"type": "oauth", "refresh": "SECRET-pi-oauth-r", "access": "SECRET-pi-oauth-a", "expires": 1}}' \
         '{"p": {"refresh_token": "SECRET-pi-oauth-r"}}'; do
  echo "$a" > "$pa"; cp -p "$pa" "$t/auth0"
  copycase rewrite; piok oauth
  [[ "$(grep -c '^qc: warning: auth.json has OAuth credentials: a token refresh during this run is discarded$' <<< "$out")" == 1 ]] \
    || fail "oauth: want one warning line: $out"
  ! grep -q 'SECRET-pi-oauth' <<< "$out" || fail "oauth: credential value printed"
done
cp -p "$t/auth-plain" "$pa"
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

# A warm vendored-skill cache (#69): bound back read-only after the cache tmpfs, so `just check` in the sandbox
# reaches check-vendored green; the proof names the bind; the judge cannot write it.
[[ -d "$vc0/git" && -d "$vc0/bin" ]] || fail "no warm check-vendored cache at $vc0: run just vendored-fetch"
vc="$HOME/.cache/octo-feather/skillfile"; mkdir -p "${vc%/*}"; cp -a "$vc0" "$vc"; vsum() { find "$vc" -printf '%P %s %m\n' | sort | md5sum; }; v0="$(vsum)"
run 0 vendored $st 5 acceptance-a
judge="$(report '["stdout"]')"
grep -E 'ESCAPE|MISSING' <<< "$judge" && fail "vendored cache: $judge"
grep -q "VENDORED green" <<< "$judge" || fail "check-vendored not green in the sandbox: $judge"
grep -q "qc sandbox: ok   vendored-skill cache $vc bound read-only" <<< "$out" && grep -q "qc sandbox: ok   writable persistent paths: none$" <<< "$out" \
  || fail "no read-only cache proof: $out"
[[ "$(vsum)" == "$v0" ]] || fail "the judge changed the vendored-skill cache"
rm -rf "$HOME/.cache"
# A qc sandbox nested in the judge's (outer /proc submounts covered by its own /proc) passes its proof.
run 0 nested $st 5 acceptance-a
judge="$(report '["stdout"]')"
grep -E 'ESCAPE|MISSING' <<< "$judge" && fail "nested qc: $judge"
grep -q "NESTED exit 3" <<< "$judge" || fail "nested qc: want the inner judge to run (exit 3, unusable report): $judge"

# The qc recipes pass arguments as data, never as shell source.
for jf in "$kit/justfile" "$kit/templates/python/justfile" "$kit/templates/typescript/justfile"; do
  set +e; o="$(bounded just --justfile "$jf" --working-directory "$t/repo" qc "$st" 5 'acceptance-a$(touch pwned)' 'x;touch pwned2' 2>&1)"; rc=$?; set -e; hung "$rc" "$jf qc" "$o"
  [[ "$rc" != 0 && ! -e pwned && ! -e pwned2 && ! -e "$kit/pwned" ]] || fail "$jf qc ran its arguments as shell (exit $rc): $o"
  grep -q 'not in docs/specs/demo.status.json: acceptance-a$(touch pwned) x;touch pwned2' <<< "$o" || fail "$jf qc mangled its arguments: $o"
done
echo "qc: ok (pass flips built, fail stays planned, status-only commit, judge from agents/qc-judge.md, same family, dirty, unusable report, judge wrote (non-ignored, tracked), unique reports, killed run leaves no scratch, sandbox escapes, no persistent write (credential copies: >64 MiB, intermediate refresh, token only, HOME; auth.json and models.json: per-run copies rewritten, box files unchanged, OAuth warned), proof abort, other repos masked (listing recorded and refused; a failed mask aborts), cleanup count, vendored cache read-only (check-vendored green, writes refused), nested sandbox, judge pane in the sandbox ($mode herdr), --no-sandbox, recipe args as data; offline, runs bounded)"
