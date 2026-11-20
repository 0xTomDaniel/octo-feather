#!/usr/bin/env bash
# Park's public contract (herdr_scope.py park; its parked line: comms spec #roles-park),
# isolated Herdr, state and process session, no Pi; systemd the testkit stand-in, first on
# PATH: a run inside an agent's scope never reaches the real manager, and parking this unowned pane asks no stop (#1070).
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
[[ -d /proc/self ]] || exit 0
t="$(mktemp -d)"; mkdir -p "$t/bin" "$t/cwd\"quoted"
pids="$(git -C "$kit" rev-parse --absolute-git-dir)/pids"; mkdir -p "$pids"
pidfile="$pids/handoff-park-$$"
trap '[[ ! -f "$pidfile" ]] || kill -- -"$(<"$pidfile")" 2>/dev/null || true; rm -f "$pidfile"; rm -rf "$t"' EXIT
cp "$kit/tests/fixtures/herdr-say/herdr" "$t/bin/herdr"; chmod +x "$t/bin/herdr"
for s in busctl systemctl; do cp "$kit/tests/gate/kit/testkit/systemd.py" "$t/bin/$s"; done   # systemd stood in: the scope is e2e
printf 'impl w6:p4 w6:t4\nsup w6:p1 w6:t1\n' >"$t/agents"
export HERDR_SESSION="handoff-park-test-$$" FAKE_HERDR_DIR="$t" FAKE_SYSTEMD_LOG="$t/systemd" XDG_STATE_HOME="$t/state"
lanes="$t/state/octo-feather/sessions/$HERDR_SESSION/lanes"; mkdir -p "$lanes"
printf 'issue = "6"\nsupervisor = "w6:p1"\n' >"$lanes/gh6.toml"
(cd "$t/cwd\"quoted"; export HERDR_PANE_ID=w6:p4 HERDR_TAB_ID=w6:t4 OCTO_FEATHER_SESSION_ID=original-session OCTO_FEATHER_ROLE=implementer OCTO_FEATHER_PARENT=w6:p1
 setsid sh -c 'echo $$ > "$1"; exec python3 -c "import time; time.sleep(300)" --session-id original-session' sh "$pidfile" &)
for _ in {1..50}; do [[ -s "$pidfile" ]] && break; sleep .02; done
echo "w6:p4 $(<"$pidfile")" >"$t/pis"
HERDR_PANE_ID=w6:p1 PATH="$t/bin:$PATH" "$kit/.agents/skills/herdr-comms/assets/herdr-close" --park w6:p4 >"$t/out" 2>"$t/err" || { printf 'park failed: '; head -20 "$t/err"; exit 1; }
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d["session"]=="original-session" and d["kind"]=="parked" and d["cwd"].endswith("cwd\"quoted"); assert set(d)=={"at","kind","pane","name","label","role","parent","cwd","session"}' "$lanes/gh6.handoffs.jsonl"
[[ ! -s "$t/out" ]] || { echo "park printed on stdout: $(cat "$t/out")"; exit 1; }
grep -qx 'tab=w6:t4 tab_close_rc=0 killed=0 unowned=w6:p4' "$t/err"
! grep -q ' stop ' "$t/systemd" 2>/dev/null || { echo "park stopped a scope for an unowned pane: $(cat "$t/systemd")"; exit 1; }
echo 'handoff park: ok (parked line in the lane log, stdout empty, close report stderr, original session and all fields retained, no scope stopped)'
