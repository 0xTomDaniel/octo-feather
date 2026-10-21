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
g init -q "$t/fieldnote"; mkdir -p "$t/fieldnote/sub"
export PATH="$t/bin:$PATH" FAKE_LOG="$t/log"
S="$kit/scripts/octo-feather-start"
start() { set +e; out="$(env -u HERDR_SESSION -u HERDR_PANE_ID "$@" "$S" --director --cwd "$t/fieldnote/sub" 2>&1)"; rc=$?; set -e; }

FAKE_UNAME=Darwin start env
[[ "$rc" == 69 && "$out" == *"HERDR_SESSION=fieldnote"* && "$out" == *"herdr --session fieldnote"* ]] || fail "macOS, session not running: rc=$rc $out"
grep -qxF '*.review/' "$t/fieldnote/.git/info/exclude" || fail "review state exclude not written"
: > "$t/log"; FAKE_UNAME=Darwin FAKE_RUNNING=fieldnote start env
[[ "$rc" == 1 && "$out" == *"workspace create returned no workspace"* ]] || fail "macOS, session running: rc=$rc $out"
grep -q '^HERDR_SESSION=fieldnote workspace create --label director' "$t/log" || fail "herdr not called in session fieldnote: $(cat "$t/log")"
: > "$t/log"; FAKE_UNAME=Darwin start env HERDR_SESSION=other
grep -q '^HERDR_SESSION=other workspace create' "$t/log" || fail "an explicit HERDR_SESSION was overridden: $(cat "$t/log")"
: > "$t/log"; start env
grep -q '^HERDR_SESSION= workspace create' "$t/log" || fail "Linux start changed the session: $(cat "$t/log")"
[[ "$(grep -cxF '*.review/' "$t/fieldnote/.git/info/exclude")" == 1 ]] || fail "exclude line not exactly once after reruns"
echo "start: ok (macOS project session, not running refused, explicit session kept, Linux unchanged, review exclude once)"
