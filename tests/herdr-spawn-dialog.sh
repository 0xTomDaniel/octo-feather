#!/usr/bin/env bash
# Integration test for herdr-spawn vs a trust dialog that opens anyway (issue #3): drives herdr-spawn's CLI with the
# fake herdr of tests/fixtures/herdr-spawn/ first on PATH. No real herdr, pi or state dir. Moved out of
# tests/herdr-spawn.sh (#1323: each item under the per-test CPU budget). Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
# ident DIR: the commit identity a role launch needs (#665) in state dir DIR: set once through pi-role --set-identity,
# its file copied for each later DIR (one Python start, not one per case: the CPU budget).
ident() {
  [[ -f "$t/ident/octo-feather/onboarding.toml" ]] || XDG_STATE_HOME="$t/ident" "$kit/scripts/pi-role" --set-identity t t@t >/dev/null
  mkdir -p "$1/octo-feather"; cp "$t/ident/octo-feather/onboarding.toml" "$1/octo-feather/"
}
export XDG_STATE_HOME="$t/state"; ident "$t/state"
mkdir -p "$t/bin" "$t/cwd" "$t/cache"
# mise's state its own, also run bare outside the gate: mise in $t/cwd's mise.toml records it there, never in the caller's (#664).
export MISE_STATE_DIR="$t/mise-state"
cp "$kit/tests/fixtures/herdr-spawn/"* "$t/bin/"
cp "$kit/tests/gate/kit/testkit/systemd.py" "$t/bin/busctl"; cp "$kit/tests/gate/kit/testkit/systemd.py" "$t/bin/systemctl"   # systemd stood in: the scope is e2e
chmod +x "$t/bin/herdr"
fail() { echo "herdr-spawn-dialog test: $*" >&2; exit 1; }
# A failing-read case is vacuous unless herdr-spawn read up to the armed
# boundary: fewer reads than READS_OK means the failing read was never reachable.
# Reads past it must be recorded failures (the fake's failed-reads).
armed() { # $1: case dir, $2: READS_OK
  local r f=0; r="$(wc -l <"$t/$1/reads")"
  [[ ! -f "$t/$1/failed-reads" ]] || f="$(wc -l <"$t/$1/failed-reads")"
  ((r >= $2)) || fail "$1: $r pane reads < READS_OK=$2; the failing read was never reached, so this case proves nothing"
  ((r == $2 || f >= 1)) || fail "$1: $r reads past READS_OK=$2 but no failed read recorded"
}

spawn() { # $1: case dir; rest: env assignments
  local c="$t/$1"; shift; mkdir -p "$c"; rc=0
  env FAKE_HERDR_DIR="$c" PATH="$t/bin:$PATH" XDG_CACHE_HOME="$t/cache" HERDR_PANE_ID=w9:p0 \
    HERDR_SPAWN_TRUST_RETRIES=3 HERDR_SPAWN_READY_RETRIES=2 "$@" \
    "$kit/.agents/skills/herdr-comms/assets/herdr-spawn" --workspace w9 --name t1 --role implementer \
    --cwd "$t/cwd" >"$c/out" 2>"$c/err" || rc=$?
}

# 2. A trust dialog that opens anyway is never answered: exit 69, zero keys,
#    tab closed, pane text on stderr.
spawn dialog FAKE_HERDR_FORCE_DIALOG=1
[[ "$rc" == 69 ]] || fail "forced dialog: exit $rc, want 69: $(cat "$t/dialog/err")"
[[ ! -s "$t/dialog/keys" ]] || fail "forced dialog: keys sent: $(tr '\n' ' ' <"$t/dialog/keys")"
grep -qx 'w9:t1' "$t/dialog/closed" 2>/dev/null || fail "forced dialog: tab not closed"
grep -q 'Trust project folder?' "$t/dialog/err" || fail "forced dialog: pane text not on stderr: $(cat "$t/dialog/err")"

# 2b. Same when the pane read fails after the detecting read: the report shows
#     the text already read, and close and 69 still run.
spawn dialog-readfail FAKE_HERDR_FORCE_DIALOG=1 FAKE_HERDR_READS_OK=1
armed dialog-readfail 1
[[ "$rc" == 69 ]] || fail "dialog then failed read: exit $rc, want 69: $(cat "$t/dialog-readfail/err")"
[[ ! -s "$t/dialog-readfail/keys" ]] || fail "dialog then failed read: keys sent"
grep -qx 'w9:t1' "$t/dialog-readfail/closed" 2>/dev/null || fail "dialog then failed read: tab not closed"
grep -q 'Trust project folder?' "$t/dialog-readfail/err" || fail "dialog then failed read: detected text not on stderr"

# 2c. The "did not clear" path (a non-Pi dialog that stays open) keeps the same
#     guarantee when the pane read fails after the last detecting read.
spawn stuck FAKE_HERDR_FORCE_DIALOG=other HERDR_SPAWN_TRUST_RETRIES=1 FAKE_HERDR_READS_OK=4
armed stuck 4
[[ "$rc" == 69 ]] || fail "stuck dialog then failed read: exit $rc, want 69: $(cat "$t/stuck/err")"
grep -qx 'w9:t1' "$t/stuck/closed" 2>/dev/null || fail "stuck dialog then failed read: tab not closed"
grep -q 'Quick safety check' "$t/stuck/err" || fail "stuck dialog then failed read: detected text not on stderr"

echo "herdr-spawn-dialog: ok (Pi trust dialog fails closed, exit 69, no key, also on a failed read; did-not-clear closes on a failed read)"
