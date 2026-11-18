#!/usr/bin/env bash
# Integration test for herdr-close's id forms (issue #76): a pane id closes its
# tab exactly as that tab id would (same output); a pane id it cannot map fails
# naming TAB|SPACE|PANE with no close; tab and space ids close as before. The
# agent's pane here is unowned (its shell, the fake's stand-in, in no agent
# scope, #1000): closed, nothing swept, named in unowned=, and a process tagged
# with the closed tab survives (no environ is read). Owned scopes: the e2e
# tests/gate/kit/agent_scope.py. Drives herdr-close's CLI with the fake herdr in
# tests/fixtures/herdr-say/; HERDR_* and OCTO_FEATHER_* are reset, so no live
# pane or process is reached.
# Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; sleeper=""
trap '[[ -n "$sleeper" ]] && kill "$sleeper" 2>/dev/null; rm -rf "$t"' EXIT
mkdir -p "$t/sbin"
cp "$kit/tests/fixtures/herdr-say/herdr" "$t/sbin/"; chmod +x "$t/sbin/herdr"
fail() { echo "herdr-close test: $*" >&2; exit 1; }

setup() { # $1: case. Agent impl lives in pane w6:p4 of tab w6:t4.
  c="$t/$1"; mkdir -p "$c"; echo "impl w6:p4 w6:t4" >"$c/agents"
}
close() { # args: herdr-close args
  rc=0
  env -u HERDR_PANE_ID -u HERDR_TAB_ID -u HERDR_WORKSPACE_ID -u OCTO_FEATHER_PARENT \
    FAKE_HERDR_DIR="$c" PATH="$t/sbin:$PATH" \
    "$kit/.agents/skills/herdr-comms/assets/herdr-close" "$@" >"$c/out" 2>"$c/err" || rc=$?
}
# 1. Pane id: its tab w6:t4 is closed, tab= printed, its unowned pane named; a
#    process tagged with that tab (as the old environ sweep found them) lives on.
setup pane
env HERDR_TAB_ID=w6:t4 HERDR_WORKSPACE_ID=w6 sleep 300 & sleeper=$!
close w6:p4
[[ "$rc" == 0 ]] || fail "pane: exit $rc, want 0: $(cat "$c/err")"
[[ "$(cat "$c/out")" == "tab=w6:t4 tab_close_rc=0 killed=0 unowned=w6:p4" ]] || fail "pane: printed '$(cat "$c/out")', want tab=w6:t4 tab_close_rc=0 killed=0 unowned=w6:p4"
[[ "$(cat "$c/closed" 2>/dev/null)" == w6:t4 ]] || fail "pane: closed '$(cat "$c/closed" 2>/dev/null)', want w6:t4"
kill -0 "$sleeper" 2>/dev/null || fail "pane: the tagged process outside any scope was ended"

# 2. Unknown pane id: non-zero, stderr names TAB|SPACE|PANE, no close call.
setup unknown
close w6:p7
[[ "$rc" != 0 ]] || fail "unknown pane: exit 0, want non-zero"
grep -qF 'TAB|SPACE|PANE' "$c/err" || fail "unknown pane: stderr lacks TAB|SPACE|PANE: $(cat "$c/err")"
grep -q 'close' "$c/argv" 2>/dev/null && fail "unknown pane: close called: $(cat "$c/argv")"

# 3. Tab id and space id close as before.
setup tab
close w6:t4
[[ "$rc" == 0 && "$(cat "$c/out")" == "tab=w6:t4 tab_close_rc=0 killed=0 unowned=w6:p4" ]] || fail "tab: exit $rc, printed '$(cat "$c/out")'"
[[ "$(cat "$c/closed" 2>/dev/null)" == w6:t4 ]] || fail "tab: closed '$(cat "$c/closed" 2>/dev/null)', want w6:t4"
setup space
close w6
[[ "$rc" == 0 && "$(cat "$c/out")" == "space=w6 space_close_rc=0 killed=0 unowned=w6:p4" ]] || fail "space: exit $rc, printed '$(cat "$c/out")'"
grep -qx 'workspace close w6' "$c/argv" || fail "space: no workspace close w6: $(cat "$c/argv")"

echo "herdr-close: ok (pane id closes its tab, prints tab=, its unowned pane named and nothing swept, a tagged process alive; unknown pane id exits non-zero naming TAB|SPACE|PANE, no close; tab and space ids close as before)"
