#!/usr/bin/env bash
# Integration test for scripts/octo-feather-lane spend (spec spend): records piped to `spend record`
# show in the totals under their lane, purpose, model and day, unknown-cost calls apart (rule-cost);
# the lane comes from the caller's Herdr space or --lane, else none (rule-lane); records only grow and
# concurrent writers never interleave (rule-append); an unwritable ledger warns once and exits 0
# (rule-write-fails); the reconcile shows OpenRouter's count, the ledger's OpenRouter total and the gap
# per window (acceptance-spend-reconcile), against a fake OpenRouter on localhost. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
L="$kit/scripts/octo-feather-lane"
t="$(mktemp -d)"; srv=""
trap '[[ -n "$srv" ]] && kill "$srv" 2>/dev/null; chmod -R u+w "$t"; rm -rf "$t"' EXIT
export HOME="$t/home" XDG_STATE_HOME="$t/state"   # never the real state dir or auth.json
unset HERDR_SESSION HERDR_WORKSPACE_ID HERDR_PANE_ID OPENROUTER_API_KEY
export OPENROUTER_API_BASE="http://127.0.0.1:9/api/v1"   # never the network; replaced by the fake below
mkdir -p "$HOME"
fail() { echo "lane-spend test: $*" >&2; exit 1; }
state="$XDG_STATE_HOME/octo-feather"; ledger="$state/spend.jsonl"
line() { printf '{"model":"%s","purpose":"%s","input_tokens":%s,"output_tokens":%s,"cost_usd":%s%s}\n' "$@"; }
row() { # OUT TITLE KEY USD CALLS UNKNOWN IN OUT: the KEY row under "By TITLE:"
  awk -v t="By $2:" '$0==t{on=1;next} /^By |^OpenRouter/{on=0} on' <<<"$1" |
    grep -qE "^  $3 +\\\$$4 +calls +$5 +unknown cost +$6 +tokens in $7 out $8\$" || fail "no $2 row '$3 \$$4 calls $5 unknown $6 in $7 out $8' in: $1"
}

# A fake OpenRouter: GET /api/v1/key with the right Bearer key answers the usage windows, else 401.
port_file="$t/port"
python3 - "$port_file" <<'PY' &
import http.server, json, sys
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        ok = self.path == "/api/v1/key" and self.headers.get("Authorization") == "Bearer sk-test-123"
        body = json.dumps({"data": {"label": "x", "usage": 9, "usage_daily": 1.5, "usage_weekly": 2.5, "usage_monthly": 4.0}} if ok else {"error": {"code": 401}}).encode()
        self.send_response(200 if ok else 401); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(body)
    def log_message(self, *a): pass
s = http.server.HTTPServer(("127.0.0.1", 0), H)
open(sys.argv[1] + ".tmp", "w").write(str(s.server_port)); __import__("os").rename(sys.argv[1] + ".tmp", sys.argv[1])
s.serve_forever()
PY
srv=$!
for _ in $(seq 50); do [[ -s "$port_file" ]] && break; sleep 0.1; done
[[ -s "$port_file" ]] || fail "fake OpenRouter did not start"
fake="http://127.0.0.1:$(cat "$port_file")/api/v1"

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

# rule-append: records only grow (the old bytes stay a prefix); concurrent writers never interleave.
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

# rule-write-fails: unwritable ledger (a directory in its place) -> exit 0, one stderr line naming the spend.
mkdir -p "$state/sessions/ro/spend.jsonl"
set +e; err="$(line openrouter/a/b judge 1 1 0.5 '' | HERDR_SESSION=ro "$L" spend record 2>&1 >/dev/null)"; rc=$?; set -e
[[ "$rc" == 0 ]] || fail "unwritable ledger: exit $rc, want 0"
[[ "$(wc -l <<<"$err")" == 1 ]] || fail "unwritable ledger: want one stderr line: $err"
grep -qF 'spend unrecorded (1 call(s), $0.500000)' <<<"$err" || fail "unwritable ledger line: $err"

# Reconcile over the windows `octo-feather-lane --help` (spend) states; the ledger column counts openrouter/* only.
# Fresh session so the totals are exact; amounts in micro-dollars.
export HERDR_SESSION=rc
now=$(date -u +%s); today=$(date -u +%F)
mon=$(date -u -d "$today -$(( $(date -u +%u) - 1 )) days" +%s); m1=$(date -u -d "$(date -u +%Y-%m-01)" +%s)
iso() { date -u -d "@$1" +%Y-%m-%dT%H:%M:%SZ; }
rec() { line "$1" judge 1 1 "$2" ",\"at\":\"$3\"" | "$L" spend record; }
rec openrouter/a/b 0.25 "$(iso "$now")"           # A: today
rec openrouter/a/b 0.5 "$(iso "$mon")"            # B: Monday 00:00Z, first second of the week
rec openrouter/a/b 0.125 "$(iso $((mon - 1)))"    # C: Sunday 23:59:59Z, last second of the week before
rec openrouter/a/b 2 "$(iso $((m1 - 1)))"         # E: last second of the month before
rec openrouter/a/b null "$(iso "$now")"           # unknown cost: not dollars
rec anthropic/x 7 "$(iso "$now")"                 # not OpenRouter
rec openrouter/a/b 9 "2020-01-01T00:00:00Z"       # outside every window
d=250000; w=750000; m=250000
[[ "$(date -u -d "@$mon" +%F)" == "$today" ]] && d=$((d + 500000))
(( m1 - 1 >= mon )) && w=$((w + 2000000))
(( mon >= m1 )) && m=$((m + 500000)); (( mon - 1 >= m1 )) && m=$((m + 125000))
usd() { printf '%s$%d.%06d' "${2:-}" $(( $1 / 1000000 )) $(( $1 % 1000000 )); }
gap() { local g=$(( $1 - $2 )); (( g < 0 )) && usd $(( -g )) - || usd "$g"; }
mkdir -p "$HOME/.pi/agent"; printf '{"openrouter":{"type":"api_key","key":"sk-test-123"}}\n' >"$HOME/.pi/agent/auth.json"
out="$(OPENROUTER_API_BASE="$fake" "$L" spend)" || fail "spend with the fake OpenRouter failed"
for spec in "today 1500000 $d" "this week 2500000 $w" "this month 4000000 $m"; do
  set -- $spec; [[ "$1" == this ]] && { label="this $2"; shift; } || label="$1"
  want="$(printf '  %-11s %12s %12s %12s  (1 ledger calls of unknown cost)' "$label" "$(usd "$2")" "$(usd "$3")" "$(gap "$2" "$3")")"
  grep -qxF -- "$want" <<<"$out" || fail "reconcile row for $label, want '$want' in: $out"
done
grep -qF "this week from Monday 00:00Z" <<<"$out" || fail "window boundaries not stated: $out"
grep -qF sk-test-123 <<<"$out" && fail "the key was printed"
# OPENROUTER_API_KEY wins over auth.json (a wrong env key gets the fake's 401).
out="$(OPENROUTER_API_KEY=sk-wrong OPENROUTER_API_BASE="$fake" "$L" spend)" || fail "spend with a wrong key failed"
grep -qF "OpenRouter unavailable: GET $fake/key: HTTP 401" <<<"$out" || fail "wrong key not reported: $out"
grep -qF sk-wrong <<<"$out" && fail "the env key was printed"

# Unreachable endpoint and no key: the reason prints, the totals still print, exit 0.
out="$("$L" spend)" || fail "spend with OpenRouter unreachable failed"
grep -qF "OpenRouter unavailable: GET $OPENROUTER_API_BASE/key: unreachable" <<<"$out" && grep -qF "By model:" <<<"$out" || fail "unreachable: $out"
rm "$HOME/.pi/agent/auth.json"
out="$("$L" spend)" || fail "spend with no key failed"
grep -qF "OpenRouter unavailable: no OpenRouter key" <<<"$out" && grep -qF "(7 calls)" <<<"$out" || fail "no key: $out"
echo "lane-spend: ok (totals by day, lane, purpose, model, unknown cost apart; lane from space, --lane, none; append-only, 1000 concurrent lines; unwritable ledger exit 0; reconcile today/week/month with gap; wrong key, unreachable, no key)"
