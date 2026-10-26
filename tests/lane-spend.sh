#!/usr/bin/env bash
# Integration test for scripts/octo-feather-lane spend (spec spend): totals by lane, purpose, model and day,
# unknown cost apart (rule-cost); the lane (rule-lane); append-only writes (rule-append); an unwritable
# ledger (rule-write-fails); the reconcile per window (acceptance-spend-reconcile), against a fake curl
# (tests/fixtures/lane-spend/curl) first on PATH. Each rule as `octo-feather-lane --help` (spend) states it.
# Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
L="$kit/scripts/octo-feather-lane"
t="$(mktemp -d)"
trap 'chmod -R u+w "$t"; rm -rf "$t"' EXIT
export HOME="$t/home" XDG_STATE_HOME="$t/state"   # never the real state dir or auth.json
unset HERDR_SESSION HERDR_WORKSPACE_ID HERDR_PANE_ID OPENROUTER_API_KEY FAKE_CURL_EXIT
export PATH="$kit/tests/fixtures/lane-spend:$PATH" FAKE_CURL_DIR="$t"   # never the network
mkdir -p "$HOME"
fail() { echo "lane-spend test: $*" >&2; exit 1; }
state="$XDG_STATE_HOME/octo-feather"; ledger="$state/spend.jsonl"
line() { printf '{"model":"%s","purpose":"%s","input_tokens":%s,"output_tokens":%s,"cost_usd":%s%s}\n' "$@"; }
row() { # OUT TITLE KEY USD CALLS UNKNOWN IN OUT: the KEY row under "By TITLE:"
  awk -v t="By $2:" '$0==t{on=1;next} /^By |^OpenRouter/{on=0} on' <<<"$1" |
    grep -qE "^  $3 +\\\$$4 +calls +$5 +unknown cost +$6 +tokens in $7 out $8\$" || fail "no $2 row '$3 \$$4 calls $5 unknown $6 in $7 out $8' in: $1"
}

# Empty ledger: totals print, no records.
out="$("$L" spend)" || fail "spend on an empty ledger failed"
grep -qF "Spend ledger: $ledger (0 calls)" <<<"$out" || fail "empty ledger header: $out"

# rule-lane: in a lane's space -> that lane; outside any -> no lane; --lane wins without HERDR env.
mkdir -p "$state/lanes"; printf 'supervisor = "w9:p2"\nissue = 9\n' >"$state/lanes/gh9.toml"
printf 'supervisor = "w10:p2"\n' >"$state/lanes/gh10.toml"
line openrouter/qwen/qwen3-8b judge 100 5 0.25 ',"at":"2026-03-04T10:00:00Z"' | HERDR_WORKSPACE_ID=w9 "$L" spend record || fail "record in a lane failed"
line openrouter/qwen/qwen3-8b bench 40 2 0.125 ',"at":"2026-03-04T23:59:59Z"' | HERDR_WORKSPACE_ID=w77 "$L" spend record || fail "record outside a lane failed"
line anthropic/claude-x supervisor 7 3 1 ',"at":"2026-03-05T00:00:00Z"' | "$L" spend record --lane gh10 || fail "record --lane failed"
# rule-cost: unreported cost is null, counted apart from the dollars.
line openrouter/qwen/qwen3-8b judge 10 1 null ',"at":"2026-03-04T11:00:00Z"' | HERDR_WORKSPACE_ID=w9 "$L" spend record || fail "unknown-cost record failed"
[[ "$(wc -l <"$ledger")" == 4 ]] || fail "ledger has $(wc -l <"$ledger") lines, want 4"
python3 -c 'import json,sys; [json.loads(l) for l in open(sys.argv[1])]' "$ledger" || fail "ledger not JSON lines"
out="$("$L" spend)"
grep -qF "(4 calls)" <<<"$out" || fail "header count: $out"
row "$out" lane gh9 0.250000 2 1 110 6
row "$out" lane '\(no lane\)' 0.125000 1 0 40 2
row "$out" lane gh10 1.000000 1 0 7 3
row "$out" purpose judge 0.250000 2 1 110 6
row "$out" purpose bench 0.125000 1 0 40 2
row "$out" purpose supervisor 1.000000 1 0 7 3
row "$out" model openrouter/qwen/qwen3-8b 0.375000 3 1 150 8
row "$out" model anthropic/claude-x 1.000000 1 0 7 3
row "$out" "day (UTC)" 2026-03-04 0.375000 3 1 150 8
row "$out" "day (UTC)" 2026-03-05 1.000000 1 0 7 3

# rule-append: the old bytes stay a prefix; 20 concurrent writers.
before="$(cat "$ledger")"
writers=()
for i in $(seq 20); do
  (for j in $(seq 50); do line openrouter/a/b "p$i" "$j" 1 0.001 ''; done | "$L" spend record) &
  writers+=("$!")
done
wait "${writers[@]}"
[[ "$(head -c "${#before}" "$ledger")" == "$before" ]] || fail "old records changed"
[[ "$(wc -l <"$ledger")" == 1004 ]] || fail "concurrent appends: $(wc -l <"$ledger") lines, want 1004"
python3 -c 'import json,sys; [json.loads(l) for l in open(sys.argv[1])]' "$ledger" || fail "concurrent appends interleaved"

# A line it cannot read is reported, not fatal; the good lines still land.
set +e; err="$( { line openrouter/a/b x 1 1 0.5 ''; echo 'not json'; } | "$L" spend record 2>&1 >/dev/null)"; rc=$?; set -e
[[ "$rc" == 0 && "$(wc -l <"$ledger")" == 1005 ]] || fail "bad stdin line: exit $rc, $(wc -l <"$ledger") lines"
grep -qF "spend unrecorded" <<<"$err" || fail "bad stdin line not reported: $err"

# rule-write-fails: a directory in the ledger's place.
mkdir -p "$state/sessions/ro/spend.jsonl"
set +e; err="$(line openrouter/a/b judge 1 1 0.5 '' | HERDR_SESSION=ro "$L" spend record 2>&1 >/dev/null)"; rc=$?; set -e
[[ "$rc" == 0 ]] || fail "unwritable ledger: exit $rc, want 0"
[[ "$(wc -l <<<"$err")" == 1 ]] || fail "unwritable ledger: want one stderr line: $err"
grep -qF 'spend unrecorded (1 call(s), $0.500000)' <<<"$err" || fail "unwritable ledger line: $err"

# Reconcile (the fake answers today $1.5, this week $2.5, this month $4.0): the ledger column counts
# openrouter/* calls with a cost in the window; each session is its own ledger.
iso() { date -u -d "@$1" +%Y-%m-%dT%H:%M:%SZ; }
rec() { line "$1" judge 1 1 "$2" ",\"at\":\"$(iso "$3")\"" | "$L" spend record; }
reconcile() { # LABEL OPENROUTER LEDGER GAP [UNKNOWN]: that row is in $out
  local want; want="$(printf '  %-11s %12s %12s %12s' "$1" "$2" "$3" "$4")${5:+  ($5 ledger calls of unknown cost)}"
  grep -qxF -- "$want" <<<"$out" || fail "reconcile row for $1, want '$want' in: $out"
}
now=$(date -u +%s); day=$(date -u -d "$(date -u +%F)" +%s)
mon=$(( day - ($(date -u +%u) - 1) * 86400 )); m1=$(date -u -d "$(date -u +%Y-%m-01)" +%s)
mkdir -p "$HOME/.pi/agent"; printf '{"openrouter":{"type":"api_key","key":"sk-test-123"}}\n' >"$HOME/.pi/agent/auth.json"
export HERDR_SESSION=rc   # every window: one call now, plus calls that count in none
rec openrouter/a/b 0.25 "$now"; rec openrouter/a/b null "$now"; rec anthropic/x 7 "$now"; rec openrouter/a/b 9 1577836800
out="$("$L" spend)" || fail "spend with the fake OpenRouter failed"
reconcile today '$1.500000' '$0.250000' '$1.250000' 1
reconcile 'this week' '$2.500000' '$0.250000' '$2.250000' 1
reconcile 'this month' '$4.000000' '$0.250000' '$3.750000' 1
grep -qF sk-test-123 <<<"$out$(cat "$t/argv")" && fail "the key was printed or passed in argv"
HERDR_SESSION=d; rec openrouter/a/b 2 "$day"; rec openrouter/a/b 0.125 $((day - 1))   # today's first second, yesterday's last
out="$(HERDR_SESSION=d "$L" spend)"; reconcile today '$1.500000' '$2.000000' '-$0.500000'
HERDR_SESSION=w; rec openrouter/a/b 0.5 "$mon"; rec openrouter/a/b 0.125 $((mon - 1))   # the week's first second, the last before
out="$(HERDR_SESSION=w "$L" spend)"; reconcile 'this week' '$2.500000' '$0.500000' '$2.000000'
HERDR_SESSION=m; rec openrouter/a/b 1 "$m1"; rec openrouter/a/b 0.125 $((m1 - 1))       # the month's first second, the last before
out="$(HERDR_SESSION=m "$L" spend)"; reconcile 'this month' '$4.000000' '$1.000000' '$3.000000'
HERDR_SESSION=rc
# OPENROUTER_API_KEY wins over auth.json (a wrong env key gets the fake's 401).
out="$(OPENROUTER_API_KEY=sk-wrong "$L" spend)" || fail "spend with a wrong key failed"
grep -qF "OpenRouter unavailable: GET https://openrouter.ai/api/v1/key: HTTP 401" <<<"$out" || fail "wrong key not reported: $out"
grep -qF sk-wrong <<<"$out$(cat "$t/argv")" && fail "the env key was printed or passed in argv"

# Unreachable endpoint and no key: the reason prints, the totals still print, exit 0.
out="$(FAKE_CURL_EXIT=7 "$L" spend)" || fail "spend with OpenRouter unreachable failed"
grep -qF "OpenRouter unavailable: GET https://openrouter.ai/api/v1/key: unreachable (curl: (7)" <<<"$out" && grep -qF "By model:" <<<"$out" || fail "unreachable: $out"
rm "$HOME/.pi/agent/auth.json"
out="$("$L" spend)" || fail "spend with no key failed"
grep -qF "OpenRouter unavailable: no OpenRouter key" <<<"$out" && grep -qF "(4 calls)" <<<"$out" || fail "no key: $out"
echo "lane-spend: ok (totals by day, lane, purpose, model, unknown cost apart; lane from space, --lane, none; append-only, 1000 concurrent lines; unwritable ledger exit 0; reconcile today/week/month with gap; wrong key, unreachable, no key)"
