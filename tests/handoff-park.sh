#!/usr/bin/env bash
# Park's public stdout/stderr contract, isolated Herdr and process session, no Pi.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
[[ -d /proc/self ]] || exit 0
t="$(mktemp -d)"; mkdir -p "$t/bin" "$t/cwd\"quoted"
pids="$(git -C "$kit" rev-parse --absolute-git-dir)/pids"; mkdir -p "$pids"
pidfile="$pids/handoff-park-$$"
trap '[[ ! -f "$pidfile" ]] || kill -- -"$(<"$pidfile")" 2>/dev/null || true; rm -f "$pidfile"; rm -rf "$t"' EXIT
cp "$kit/tests/fixtures/herdr-say/herdr" "$t/bin/herdr"; chmod +x "$t/bin/herdr"
echo 'impl w6:p4 w6:t4' >"$t/agents"
export HERDR_SESSION="handoff-park-test-$$" FAKE_HERDR_DIR="$t"
(cd "$t/cwd\"quoted"; export HERDR_PANE_ID=w6:p4 HERDR_TAB_ID=w6:t4 OCTO_FEATHER_SESSION_ID=original-session OCTO_FEATHER_ROLE=implementer OCTO_FEATHER_PARENT=w6:p1
 setsid sh -c 'echo $$ > "$1"; exec sleep 300' sh "$pidfile" &)
for _ in {1..50}; do [[ -s "$pidfile" ]] && break; sleep .02; done
PATH="$t/bin:$PATH" "$kit/.agents/skills/herdr-comms/assets/herdr-close" --park w6:p4 >"$t/out" 2>"$t/err" || { printf 'park failed: '; head -20 "$t/err"; exit 1; }
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d["session"]=="original-session" and d["kind"]=="parked" and d["cwd"].endswith("cwd\"quoted"); assert set(d)=={"at","kind","pane","name","label","role","parent","cwd","session"}' "$t/out"
grep -qx 'tab=w6:t4 tab_close_rc=0 killed=1' "$t/err"
echo 'handoff park: ok (JSON only stdout, close report stderr, original session and all fields retained)'
