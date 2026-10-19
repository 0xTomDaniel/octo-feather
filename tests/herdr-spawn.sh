#!/usr/bin/env bash
# Integration test for herdr-spawn and pi-role vs Pi's project trust dialog
# (issue #3): drives herdr-spawn's CLI with a fake herdr first on PATH
# (tests/fixtures/herdr-spawn/), and pi-role headless with a fake pi. No real
# herdr or pi. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
mkdir -p "$t/bin" "$t/cwd" "$t/cache"
cp "$kit/tests/fixtures/herdr-spawn/herdr" "$kit/tests/fixtures/herdr-spawn/pi-trust-dialog.txt" "$t/bin/"
chmod +x "$t/bin/herdr"
fail() { echo "herdr-spawn test: $*" >&2; exit 1; }

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

# 3. Headless pi-role passes --approve too (fake pi records its argv).
printf '#!/usr/bin/env bash\nprintf "%%s\\n" "$@" >"%s/pi-argv"\n' "$t" >"$t/bin/pi"; chmod +x "$t/bin/pi"
(cd "$t/cwd" && PATH="$t/bin:$PATH" "$kit/scripts/pi-role" "$kit/agents/implementer.md" -p brief)
grep -qx -- --approve "$t/pi-argv" || fail "headless pi-role argv lacks --approve"

echo "herdr-spawn: ok (pane and headless launch carry --approve; Pi trust dialog fails closed, exit 69, no key)"
