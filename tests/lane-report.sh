#!/usr/bin/env bash
# Integration test for `octo-feather-lane report` (docs/specs/comms.spec.html#factory-report, issue #248),
# no network: fake gh and herdr from tests/fixtures/lane-report/ on PATH, fixture state in a temp XDG_STATE_HOME.
# Proves comms#acceptance-report-lanes, #acceptance-report-any-target, #acceptance-report-unreadable,
# #acceptance-report-owner-queue, #acceptance-report-owner-caught, #acceptance-report-lane-numbers (lane-a: started
# line's age is its wall time, 2 review rounds, $1.7500 and 2 calls of unknown cost), #acceptance-report-gate-time
# (lane-a: its PR's last gate run beside o/a main's last), #acceptance-report-reflection (none ran, then one two days ago), #acceptance-report-owner-caught-headline (both
# weeks' counts on the line after the first, before any lane).
# Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
fx="$kit/tests/fixtures/lane-report"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fail() { echo "lane-report test: $*" >&2; exit 1; }
unset HERDR_SESSION
export HOME="$t/home" XDG_STATE_HOME="$t/xdg" FAKE_GH_PRS="$fx/pr" FAKE_HERDR_AGENTS="$fx/agents.json"
S="$XDG_STATE_HOME/octo-feather"
mkdir -p "$HOME" "$t/bin" "$S"; cp -r "$fx/state/." "$S/"
cp "$fx/gh" "$fx/herdr" "$t/bin/"; chmod +x "$t/bin/"*; export PATH="$t/bin:$PATH"
snap() { (cd "$S" && find . -printf '%p %y %s %T@ %m\n' | sort && find . -type f -exec sha256sum {} + | sort); }
before="$(snap)"
run() { # expected-file; runs the report, normalizes now, state dir, ages and the headline's counts (they move with the date), diffs
  local rc=0
  "$kit/scripts/octo-feather-lane" report >"$t/out" 2>"$t/err" || rc=$?
  [[ $rc == 0 ]] || fail "exit $rc: $(cat "$t/err" "$t/out")"
  sed -E "1s/^report at [0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:]{8}Z/report at NOW/; s#$S#STATE#; s/\(([0-9]+d)?([0-9]+h)?[0-9]+m ago\)/(AGE ago)/g; 2s/: [0-9]+ in the last 7 days, [0-9]+ in the 7 days before$/: COUNTS/" "$t/out" >"$t/norm"
  diff -u "$1" "$t/norm" || fail "report differs from $(basename "$1")"
  [[ "$(snap)" == "$before" ]] || fail "the report changed the state dir"
}

run "$fx/expected.txt"

FAKE_GH_FAIL=1 run "$fx/expected-unread.txt"

FAKE_HERDR_FAIL=1 "$kit/scripts/octo-feather-lane" report >"$t/out" || fail "Herdr failing: exit non-zero"
[[ "$(grep -c '^  running: unread: Herdr: herdr agent list failed (error: could not connect to herdr server)$' "$t/out")" == 4 ]] \
  && grep -qx 'unread: Herdr' "$t/out" && grep -qx '  waits: owner gate merge asked 2026-10-22T14:00:00Z (.*)' "$t/out" \
  || fail "Herdr failing: $(cat "$t/out")"
[[ "$(snap)" == "$before" ]] || fail "the report changed the state dir"

# the director log's latest reflection line two days old: the report shows when it ran
two="$(date -u -d '2 days ago' +%Y-%m-%dT%H:%M:%SZ)"
printf '{"at": "2026-10-01T09:00:00Z", "kind": "reflection", "findings": 0, "questions": ["owner-asked"]}\n{"at": "%s", "kind": "reflection", "findings": 1, "questions": ["owner-asked"]}\n' "$two" \
  >>"$S/director.handoffs.jsonl"; before="$(snap)"
"$kit/scripts/octo-feather-lane" report >"$t/out" || fail "director reflection: exit non-zero"
grep -qx "director reflection: last ran $two (2d0h[0-9]m ago)" "$t/out" && [[ "$(grep -c '^director reflection' "$t/out")" == 1 ]] \
  || fail "director reflection two days ago: $(grep '^director reflection' "$t/out")"
[[ "$(snap)" == "$before" ]] || fail "the report changed the state dir"

# the headline (comms #report-owner-caught): a director log of owner-caught findings 2 days and 9 days ago, one with no
# readable at; the
# report's line after its first, before any lane, counts each week
nine="$(date -u -d '9 days ago' +%Y-%m-%dT%H:%M:%SZ)"
printf '{"at": "%s", "kind": "finding", "class": "owner-caught-x", "summary": "a"}\n{"at": "%s", "kind": "finding", "class": "owner-caught-y", "summary": "b"}\n{"at": "%s", "kind": "finding", "class": "owner-caught-x", "summary": "c"}\n{"at": "soon", "kind": "finding", "class": "owner-caught-x", "summary": "d"}\n' \
  "$two" "$two" "$nine" >"$S/director.handoffs.jsonl"; before="$(snap)"
"$kit/scripts/octo-feather-lane" report >"$t/out" || fail "headline: exit non-zero"
[[ "$(sed -n 2p "$t/out")" == "owner-caught (headline, director.handoffs.jsonl): 2 in the last 7 days, 1 in the 7 days before; 1 with no readable at, not counted" ]] \
  || fail "headline: want it second, before any lane: $(head -3 "$t/out")"
grep -qx '  class owner-caught-x: count 3, last seen .*' "$t/out" || fail "headline: the per-class block changed: $(cat "$t/out")"
[[ "$(snap)" == "$before" ]] || fail "the report changed the state dir"

# no spend ledger and no gate run trend: said per lane, nothing else changes
rm "$S/spend.jsonl" "$S/check-runs.jsonl"; before="$(snap)"
"$kit/scripts/octo-feather-lane" report >"$t/out" || fail "no ledger: exit non-zero"
[[ "$(grep -c '^  spend: no spend recorded (spend.jsonl: none)$' "$t/out")" == 4 \
  && "$(grep -c '^  gate time: no gate run recorded (check-runs.jsonl: none)$' "$t/out")" == 4 ]] \
  && grep -qx 'unread: none' "$t/out" || fail "no ledger: $(cat "$t/out")"
[[ "$(snap)" == "$before" ]] || fail "the report changed the state dir"
echo "lane-report test: ok"
