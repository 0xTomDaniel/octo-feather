#!/usr/bin/env bash
# Integration test for herdr-close's id forms (issue #76): a pane id closes its
# tab exactly as that tab id would (same output, same TERM sweep); a pane id it
# cannot map fails naming TAB|SPACE|PANE with no close; tab and space ids close
# as before. Drives herdr-close's CLI with the fake herdr in
# tests/fixtures/herdr-say/; HERDR_* and OCTO_FEATHER_* are reset and the sweep
# runs under a test-only HERDR_SESSION, so no live pane or process is reached.
# Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; sleeper=""
trap '[[ -n "$sleeper" ]] && kill "$sleeper" 2>/dev/null; rm -rf "$t"' EXIT
mkdir -p "$t/sbin"
cp "$kit/tests/fixtures/herdr-say/herdr" "$t/sbin/"; chmod +x "$t/sbin/herdr"
fail() { echo "herdr-close test: $*" >&2; exit 1; }
sess="herdr-close-test-$$"
# macOS has no /proc: herdr-close skips the sweep and says so.
k1=1; k0=0; [[ -d /proc/self ]] || { k1=skipped-no-proc; k0=skipped-no-proc; }

setup() { # $1: case. Agent impl lives in pane w6:p4 of tab w6:t4.
  c="$t/$1"; mkdir -p "$c"; echo "impl w6:p4 w6:t4" >"$c/agents"
}
close() { # args: herdr-close args
  rc=0
  env -u HERDR_PANE_ID -u HERDR_TAB_ID -u HERDR_WORKSPACE_ID -u OCTO_FEATHER_PARENT \
    FAKE_HERDR_DIR="$c" PATH="$t/sbin:$PATH" HERDR_SESSION="$sess" \
    "$kit/.agents/skills/herdr-comms/assets/herdr-close" "$@" >"$c/out" 2>"$c/err" || rc=$?
}
sleeper() { # $1: tag line. A detached process of the closed tab, in the test session.
  [[ -d /proc/self ]] || return 0
  env HERDR_SESSION="$sess" "$1" sleep 300 & sleeper=$!
  for _ in 1 2 3 4 5 6 7 8 9 10; do tr '\0' '\n' <"/proc/$sleeper/environ" 2>/dev/null | grep -qxF "$1" && return; sleep 0.1; done
}

# 1. Pane id: its tab w6:t4 is closed, tab= printed, the tab's process swept.
setup pane
sleeper HERDR_TAB_ID=w6:t4
close w6:p4
[[ "$rc" == 0 ]] || fail "pane: exit $rc, want 0: $(cat "$c/err")"
[[ "$(cat "$c/out")" == "tab=w6:t4 tab_close_rc=0 killed=$k1" ]] || fail "pane: printed '$(cat "$c/out")', want tab=w6:t4 tab_close_rc=0 killed=$k1"
[[ "$(cat "$c/closed" 2>/dev/null)" == w6:t4 ]] || fail "pane: closed '$(cat "$c/closed" 2>/dev/null)', want w6:t4"
[[ -n "$sleeper" ]] && { wait "$sleeper" 2>/dev/null || true; sleeper=""; }

# 2. Unknown pane id: non-zero, stderr names TAB|SPACE|PANE, no close call.
setup unknown
close w6:p7
[[ "$rc" != 0 ]] || fail "unknown pane: exit 0, want non-zero"
grep -qF 'TAB|SPACE|PANE' "$c/err" || fail "unknown pane: stderr lacks TAB|SPACE|PANE: $(cat "$c/err")"
grep -q 'close' "$c/argv" 2>/dev/null && fail "unknown pane: close called: $(cat "$c/argv")"

# 3. Tab id and space id close as before.
setup tab
close w6:t4
[[ "$rc" == 0 && "$(cat "$c/out")" == "tab=w6:t4 tab_close_rc=0 killed=$k0" ]] || fail "tab: exit $rc, printed '$(cat "$c/out")'"
[[ "$(cat "$c/closed" 2>/dev/null)" == w6:t4 ]] || fail "tab: closed '$(cat "$c/closed" 2>/dev/null)', want w6:t4"
setup space
close w6
[[ "$rc" == 0 && "$(cat "$c/out")" == "space=w6 space_close_rc=0 killed=$k0" ]] || fail "space: exit $rc, printed '$(cat "$c/out")'"
grep -qx 'workspace close w6' "$c/argv" || fail "space: no workspace close w6: $(cat "$c/argv")"

echo "herdr-close: ok (pane id closes its tab, prints tab=, TERMs the tab's process; unknown pane id exits non-zero naming TAB|SPACE|PANE, no close; tab and space ids close as before)"
