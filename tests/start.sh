#!/usr/bin/env bash
# Integration test for scripts/octo-feather-start's target setup, offline: fake
# herdr and uname on PATH. On macOS outside Herdr with no HERDR_SESSION, the
# session is the project's and must be running; every start writes the review
# state exclude into the target. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fail() { echo "start test: $*" >&2; exit 1; }
mkdir -p "$t/bin"
cat > "$t/bin/herdr" <<'EOF'
#!/usr/bin/env bash
echo "HERDR_SESSION=${HERDR_SESSION:-} $*" >> "$FAKE_LOG"
case "$1 ${2:-}" in
  "session list") printf 'name status directory socket\ndefault running /d /d.sock\n'
                  [[ -z "${FAKE_RUNNING:-}" ]] || echo "$FAKE_RUNNING running /s /s.sock" ;;
  "workspace list") echo '{"result":{"workspaces":[]}}' ;;
  "workspace create") echo '{}' ;;   # no workspace: start stops before any spawn
esac
EOF
printf '#!/usr/bin/env bash\necho "${FAKE_UNAME:-Linux}"\n' > "$t/bin/uname"
chmod +x "$t/bin/herdr" "$t/bin/uname"
g() { git -c user.name=t -c user.email=t@t -c init.defaultBranch=main "$@"; }
g init -q "$t/pilot1"; mkdir -p "$t/pilot1/sub"
export PATH="$t/bin:$PATH" FAKE_LOG="$t/log"
S="$kit/scripts/octo-feather-start"
start() { set +e; out="$(env -u HERDR_SESSION -u HERDR_PANE_ID "$@" "$S" --director --cwd "$t/pilot1/sub" 2>&1)"; rc=$?; set -e; }

FAKE_UNAME=Darwin start env
[[ "$rc" == 69 && "$out" == *"HERDR_SESSION=pilot1"* && "$out" == *"herdr --session pilot1"* ]] || fail "macOS, session not running: rc=$rc $out"
grep -qxF '*.review/' "$t/pilot1/.git/info/exclude" || fail "review state exclude not written"
: > "$t/log"; FAKE_UNAME=Darwin FAKE_RUNNING=pilot1 start env
[[ "$rc" == 1 && "$out" == *"workspace create returned no workspace"* ]] || fail "macOS, session running: rc=$rc $out"
grep -q '^HERDR_SESSION=pilot1 workspace create --label director' "$t/log" || fail "herdr not called in session pilot1: $(cat "$t/log")"
: > "$t/log"; FAKE_UNAME=Darwin start env HERDR_SESSION=other
grep -q '^HERDR_SESSION=other workspace create' "$t/log" || fail "an explicit HERDR_SESSION was overridden: $(cat "$t/log")"
: > "$t/log"; start env
grep -q '^HERDR_SESSION= workspace create' "$t/log" || fail "Linux start changed the session: $(cat "$t/log")"
[[ "$(grep -cxF '*.review/' "$t/pilot1/.git/info/exclude")" == 1 ]] || fail "exclude line not exactly once after reruns"

# Lane key per tracker (roles spec #lane-key, #acceptance-supervise-layout-linear), with the stateful fake
# herdr (tests/fixtures/herdr-say): --issue ENG-123 in a Linear target makes workspace eng-123 holding one tab,
# supervisor; --issue 12 in a GitHub target still makes gh12; a ticket the target's tracker cannot key starts nothing.
mkdir -p "$t/lbin"; cp "$kit/tests/fixtures/herdr-say/herdr" "$t/lbin/"; chmod +x "$t/lbin/herdr"
# Startup owns only launch delivery; reflection behavior has its own integration tests.
cp "$kit/tests/fixtures/start-nohup" "$t/lbin/nohup"; chmod +x "$t/lbin/nohup"
g init -q "$t/lin"; echo 'tracker = "linear"' > "$t/lin/.octo-feather.toml"; g init -q "$t/ghr"
lane() { # $1: case, $2: ticket, $3: target
  c="$t/case-$1"; mkdir -p "$c"; mkfifo "$c/completion"; set +e
  out="$(env -u HERDR_SESSION -u HERDR_PANE_ID -u HERDR_WORKSPACE_ID -u OCTO_FEATHER_PARENT -u OCTO_FEATHER_ROLE \
    PATH="$t/lbin:$PATH" FAKE_HERDR_DIR="$c" START_COMPLETION="$c/completion" XDG_STATE_HOME="$c/state" XDG_CACHE_HOME="$t/cache" HERDR_SPAWN_READY_RETRIES=2 \
    "$S" --issue "$2" --cwd "$3" 2>"$c/err")"; rc=$?; set -e
  if [[ "$rc" == 0 ]]; then
    python3 "$kit/tests/fixtures/start-nohup" "$c/completion" "$kit/scripts/octo-feather-lane"
  fi
}
lane linear ENG-123 "$t/lin"
[[ "$rc" == 0 && "$out" == *" name=eng-123 role=supervisor "* ]] || fail "Linear ENG-123: rc=$rc $out $(cat "$c/err")"
[[ "$(grep -c '^workspace create' "$c/argv")" == 1 ]] && grep -q '^workspace create --label eng-123 ' "$c/argv" || fail "Linear: workspace not eng-123: $(cat "$c/argv")"
[[ "$(grep -c '^tab create' "$c/argv")" == 1 ]] && grep -q '^tab create --workspace w8 --label supervisor ' "$c/argv" || fail "Linear: not one tab supervisor: $(cat "$c/argv")"
grep -qx 'w8:t1' "$c/closed" && grep -qx 'eng-123 w8:p9' "$c/agents" || fail "Linear: seed tab kept or agent not eng-123: $(cat "$c/closed" "$c/agents")"
lane github 12 "$t/ghr"
[[ "$rc" == 0 && "$out" == *" name=gh12 role=supervisor "* ]] && grep -q '^workspace create --label gh12 ' "$c/argv" || fail "GitHub 12: rc=$rc $out $(cat "$c/err")"
lane linear-12 12 "$t/lin"
[[ "$rc" == 64 && "$(cat "$c/err")" == *"not a Linear issue key"* ]] || fail "12 in a Linear target: rc=$rc $(cat "$c/err")"
! grep -qE '^(workspace|tab|agent) ' "$c/argv" 2>/dev/null || fail "12 in a Linear target called herdr: $(cat "$c/argv")"
echo "start: ok (macOS project session, not running refused, explicit session kept, Linux unchanged, review exclude once; lane key: Linear ENG-123 -> eng-123 one tab supervisor, GitHub 12 -> gh12, unkeyable ticket starts nothing)"
