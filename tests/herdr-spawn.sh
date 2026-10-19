#!/usr/bin/env bash
# Integration test for herdr-spawn and pi-role vs Pi's project trust dialog
# (issue #3): drives herdr-spawn's CLI with a fake herdr first on PATH
# (tests/fixtures/herdr-spawn/), and pi-role headless with a fake pi. No real
# herdr or pi. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
mkdir -p "$t/bin" "$t/cwd" "$t/cache"
cp "$kit/tests/fixtures/herdr-spawn/"* "$t/bin/"
chmod +x "$t/bin/herdr"
fail() { echo "herdr-spawn test: $*" >&2; exit 1; }
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

# 1. A plain spawn launches Pi with --approve, so no dialog opens and it succeeds.
spawn ok
grep -qx -- --approve "$t/ok/start-argv" || fail "agent start argv lacks --approve: $(tr '\n' ' ' <"$t/ok/start-argv")"
for f in --no-skills --no-mcp; do grep -qx -- "$f" "$t/ok/start-argv" || fail "pi-role --json args lost $f beside --approve"; done
[[ "$rc" == 0 ]] || fail "spawn exited $rc: $(cat "$t/ok/err")"
grep -q 'tab=w9:t1 pane=w9:p1' "$t/ok/out" || fail "spawn printed no tab and pane: $(cat "$t/ok/out")"
[[ ! -s "$t/ok/keys" ]] || fail "keys sent to a ready pane: $(cat "$t/ok/keys")"

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

# 3. Headless pi-role passes --approve too (fake pi records its argv).
printf '#!/usr/bin/env bash\nprintf "%%s\\n" "$@" >"%s/pi-argv"\n' "$t" >"$t/bin/pi"; chmod +x "$t/bin/pi"
(cd "$t/cwd" && PATH="$t/bin:$PATH" "$kit/scripts/pi-role" "$kit/agents/implementer.md" -p brief)
grep -qx -- --approve "$t/pi-argv" || fail "headless pi-role argv lacks --approve"

echo "herdr-spawn: ok (pane and headless launch carry --approve; Pi trust dialog fails closed, exit 69, no key, also on a failed read; did-not-clear closes on a failed read)"
