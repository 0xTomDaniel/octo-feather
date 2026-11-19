#!/usr/bin/env bash
# Integration test for herdr-close's id forms (issue #76): a pane id closes its
# tab exactly as that tab id would (same output); a pane id it cannot map fails
# naming TAB|SPACE|PANE with no close; tab and space ids close as before. The
# agent's pane here is unowned (its shell, the fake's stand-in, in no agent
# scope, #1000): closed, nothing swept, named in unowned=, and a process tagged
# with the closed tab survives (no environ is read). Owned scopes: the e2e
# tests/gate/kit/agent_scope.py; here systemd is the testkit stand-in, first on
# PATH, so a run inside an agent's scope never reaches the real manager, and no
# stop is ever asked for an unowned pane (#1070). Drives herdr-close's CLI with the fake herdr in
# tests/fixtures/herdr-say/; HERDR_* and OCTO_FEATHER_* are reset, so no live
# pane or process is reached.
# Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; sleeper=""
trap '[[ -n "$sleeper" ]] && kill "$sleeper" 2>/dev/null; rm -rf "$t"' EXIT
mkdir -p "$t/sbin"
cp "$kit/tests/fixtures/herdr-say/herdr" "$t/sbin/"; chmod +x "$t/sbin/herdr"
for s in busctl systemctl; do cp "$kit/tests/gate/kit/testkit/systemd.py" "$t/sbin/$s"; done   # systemd stood in: the scope is e2e
fail() { echo "herdr-close test: $*" >&2; exit 1; }

setup() { # $1: case. Agent impl lives in pane w6:p4 of tab w6:t4.
  c="$t/$1"; mkdir -p "$c"; echo "impl w6:p4 w6:t4" >"$c/agents"
}
close() { # args: herdr-close args
  rc=0
  env -u HERDR_PANE_ID -u HERDR_TAB_ID -u HERDR_WORKSPACE_ID -u OCTO_FEATHER_PARENT \
    FAKE_HERDR_DIR="$c" FAKE_SYSTEMD_LOG="$c/systemd" PATH="$t/sbin:$PATH" \
    "$kit/.agents/skills/herdr-comms/assets/herdr-close" "$@" >"$c/out" 2>"$c/err" || rc=$?
}
nostop() { ! grep -q ' stop ' "$c/systemd" 2>/dev/null || fail "$1: a scope stopped for an unowned pane: $(cat "$c/systemd")"; }
# 1. Pane id: its tab w6:t4 is closed, tab= printed, its unowned pane named; a
#    process tagged with that tab (as the old environ sweep found them) lives on.
setup pane
env HERDR_TAB_ID=w6:t4 HERDR_WORKSPACE_ID=w6 sleep 300 & sleeper=$!
close w6:p4
[[ "$rc" == 0 ]] || fail "pane: exit $rc, want 0: $(cat "$c/err")"
[[ "$(cat "$c/out")" == "tab=w6:t4 tab_close_rc=0 killed=0 unowned=w6:p4" ]] || fail "pane: printed '$(cat "$c/out")', want tab=w6:t4 tab_close_rc=0 killed=0 unowned=w6:p4"
[[ "$(cat "$c/closed" 2>/dev/null)" == w6:t4 ]] || fail "pane: closed '$(cat "$c/closed" 2>/dev/null)', want w6:t4"
kill -0 "$sleeper" 2>/dev/null || fail "pane: the tagged process outside any scope was ended"
nostop pane

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
nostop tab
setup space
close w6
[[ "$rc" == 0 && "$(cat "$c/out")" == "space=w6 space_close_rc=0 killed=0 unowned=w6:p4" ]] || fail "space: exit $rc, printed '$(cat "$c/out")'"
grep -qx 'workspace close w6' "$c/argv" || fail "space: no workspace close w6: $(cat "$c/argv")"
nostop space

# 4. A malformed Herdr answer (a pane with no tab_id) fails loud, naming the field: exit 76,
#    nothing closed, never read as an unowned pane.
setup malformed
mkdir -p "$t/broken"
printf '#!/usr/bin/env bash\nif [[ "$1 $2" == "pane list" ]]; then "%s" "$@" | jq -c "del(.result.panes[].tab_id)"; else exec "%s" "$@"; fi\n' \
  "$t/sbin/herdr" "$t/sbin/herdr" >"$t/broken/herdr"; chmod +x "$t/broken/herdr"
rc=0
env -u HERDR_PANE_ID -u HERDR_TAB_ID -u HERDR_WORKSPACE_ID -u OCTO_FEATHER_PARENT FAKE_HERDR_DIR="$c" PATH="$t/broken:$PATH" \
  "$kit/.agents/skills/herdr-comms/assets/herdr-close" w6:t4 >"$c/out" 2>"$c/err" || rc=$?
[[ "$rc" == 76 ]] || fail "malformed: exit $rc, want 76: $(cat "$c/err")"
grep -qF 'no field tab_id' "$c/err" || fail "malformed: stderr does not name tab_id: $(cat "$c/err")"
[[ ! -s "$c/out" && ! -s "$c/closed" ]] || fail "malformed: printed '$(cat "$c/out")' or closed '$(cat "$c/closed" 2>/dev/null)'"

echo "herdr-close: ok (malformed Herdr answer exits 76 naming the field, nothing closed; pane id closes its tab, prints tab=, its unowned pane named and nothing swept or stopped, a tagged process alive; unknown pane id exits non-zero naming TAB|SPACE|PANE, no close; tab and space ids close as before)"
