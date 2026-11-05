#!/usr/bin/env bash
# Integration test for `octo-feather-lane report` (docs/specs/comms.spec.html#factory-report, issue #248),
# no network: fake gh and herdr from tests/fixtures/lane-report/ on PATH, fixture state in a temp XDG_STATE_HOME.
# Proves comms#acceptance-report-lanes, #acceptance-report-any-target, #acceptance-report-unreadable,
# #acceptance-report-owner-queue, #acceptance-report-owner-caught, #acceptance-report-lane-numbers (lane-a: started
# line's age is its wall time, 2 review rounds, $1.7500 and 2 calls of unknown cost), #acceptance-report-gate-time
# (lane-a: its PR's last gate run beside o/a main's last; lane-b: a subset run on its PR head never stands in for a
# gate run, and o/b main's line with no tier, written before runners recorded one, counts), #acceptance-report-reflection (none ran, then one two days ago), #acceptance-report-owner-caught-headline (both
# weeks' counts on the line after the first, before any lane),
# #acceptance-report-gate-budget (o/a: its latest passed full run, 280.25s, over its 240s budget and grown 12.1% over the
# median 250s of the 3 passed full runs before it, a share of 10%, with the trend and slowest items; a failed full run
# and a subset run stay out of the trend; within budget and share, no budget file, an invalid one; no gate on timing:
# the report exits 0 either way),
# #acceptance-report-skill-reach (Pi session files in a temp PI_CODING_AGENT_DIR, their RECENT times set to a day ago,
# OLD to nine days ago: implementers offered tdd and commit, tdd read by three (one inside a codemode batch, one in a
# session started nine days ago), commit by one (a read nine days ago not counted); a codemode batch counted only from
# the nestedCalls Pi recorded for it; no read: a sed script naming a/SKILL.md, a batch grepping tdd/SKILL.md and reading
# only README.md, an aborted batch whose source names tracker/SKILL.md, failed reads of a SKILL.md (top level and
# nested), a batch with no nestedCalls record, an edit, a grep and a write; a code reviewer reading tdd, not offered to it, counted apart; a supervisor's linked skill counted
# by its offered name; a session wholly from 2026-10-01 left out; an unreadable session file named under unread:, and
# the session files unchanged).
# The kit's own budget file is gate-budget.toml at the repo root (its form: octo-feather-lane --help, report).
# Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
fx="$kit/tests/fixtures/lane-report"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fail() { echo "lane-report test: $*" >&2; exit 1; }
unset HERDR_SESSION
export HOME="$t/home" XDG_STATE_HOME="$t/xdg" FAKE_GH_PRS="$fx/pr" FAKE_HERDR_AGENTS="$fx/agents.json" PI_CODING_AGENT_DIR="$t/pi"
S="$XDG_STATE_HOME/octo-feather"
mkdir -p "$HOME" "$t/bin" "$S" "$t/pi"; cp -r "$fx/state/." "$S/"
cp -r "$fx/sessions" "$t/pi/"
day="$(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S.000Z)"
old="$(date -u -d '9 days ago' +%Y-%m-%dT%H:%M:%S.000Z)"
find "$t/pi/sessions" -name '*.jsonl' -exec sed -i "s/\"RECENT\"/\"$day\"/g; s/\"OLD\"/\"$old\"/g" {} +
cp "$fx/gh" "$fx/herdr" "$t/bin/"; chmod +x "$t/bin/"*; export PATH="$t/bin:$PATH"
snap() { for d in "$S" "$t/pi"; do (cd "$d" && find . -printf '%p %y %s %T@ %m\n' | sort && find . -type f -readable -exec sha256sum {} + | sort); done; }
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

# gate budget: within the budget and the share, no budget file, an invalid one (a report fact, the exit stays 0)
budget() { # FILE_TEXT|-: o/a's gate-budget.toml (- none), then the report's o/a gate budget block
  if [[ "$1" == - ]]; then rm -f "$t/pr/o__a/gate-budget.toml"; else printf '%s\n' "$1" > "$t/pr/o__a/gate-budget.toml"; fi
  FAKE_GH_PRS="$t/pr" "$kit/scripts/octo-feather-lane" report >"$t/out" || fail "gate budget $1: exit non-zero"
  sed -n '/^gate budget o\/a:/,/^gate budget o\/b:/p' "$t/out" | sed -E 's/\(([0-9]+d)?([0-9]+h)?[0-9]+m ago\)/(AGE ago)/'
}
cp -r "$fx/pr" "$t/pr"
run_line='  full gate: 280.25s, head aaaa5aaaa5aa, started 2026-10-20T10:00:00Z (AGE ago)'
out="$(budget $'budget_seconds = 300\ngrowth_share = 0.125\ntrend_runs = 2')"
grep -qxF "$run_line: within budget, 19.75s to spare (budget 300s)" <<<"$out" \
  && grep -qxF "  growth: +9.7% over the trend's median 255.375s (the 2 passed full runs before it); set share 12.5%: within" <<<"$out" \
  && grep -qxF '  trend: 250s 0000a0000a00 2026-10-19T12:00:00Z, 260.75s 1111a1111a11 2026-10-20T07:00:00Z, 280.25s aaaa5aaaa5aa 2026-10-20T10:00:00Z (passed full runs, oldest first)' <<<"$out" \
  || fail "within budget and share: $out"
out="$(budget -)"
grep -qxF "$run_line: no budget (gate-budget.toml: none)" <<<"$out" \
  && grep -qxF "  growth: +12.1% over the trend's median 250s (the 3 passed full runs before it); no set share (gate-budget.toml: none)" <<<"$out" \
  && grep -qx 'unread: none' "$t/out" || fail "no budget file: $out"
out="$(budget 'budget_seconds = "fast"')"
grep -qxF "$run_line: no budget (gate-budget.toml: budget_seconds 'fast' is not a number of the right range; growth_share None is not a number of the right range; trend_runs None is not a number of the right range)" <<<"$out" \
  && grep -qx 'unread: gate-budget.toml (o/a)' "$t/out" || fail "invalid budget file: $out $(tail -1 "$t/out")"
# the headline (comms #report-owner-caught): a director log of owner-caught findings 2, 3 (fractional seconds, an
# offset) and 9 days ago, one with no readable at; the
# report's line after its first, before any lane, counts each week
nine="$(date -u -d '9 days ago' +%Y-%m-%dT%H:%M:%SZ)"
three="$(date -u -d '3 days ago' +%Y-%m-%dT%H:%M:%S.123456+00:00)"   # ISO 8601 with fractional seconds and an offset
printf '{"at": "%s", "kind": "finding", "class": "owner-caught-x", "summary": "a"}\n{"at": "%s", "kind": "finding", "class": "owner-caught-y", "summary": "b"}\n{"at": "%s", "kind": "finding", "class": "owner-caught-x", "summary": "c"}\n{"at": "soon", "kind": "finding", "class": "owner-caught-x", "summary": "d"}\n{"at": "%s", "kind": "finding", "class": "owner-caught-z", "summary": "e"}\n' \
  "$two" "$two" "$nine" "$three" >"$S/director.handoffs.jsonl"; before="$(snap)"
"$kit/scripts/octo-feather-lane" report >"$t/out" || fail "headline: exit non-zero"
[[ "$(sed -n 2p "$t/out")" == "owner-caught (headline, director.handoffs.jsonl): 3 in the last 7 days, 1 in the 7 days before; 1 with no readable at, not counted" ]] \
  || fail "headline: want it second, before any lane: $(head -3 "$t/out")"
grep -qx '  class owner-caught-x: count 3, last seen .*' "$t/out" && grep -qx "  class owner-caught-z: count 1, last seen ${three%.*}Z (.* ago)" "$t/out" || fail "headline: the per-class block changed: $(cat "$t/out")"
[[ "$(snap)" == "$before" ]] || fail "the report changed the state dir"

# no spend ledger and no gate run trend: said per lane, nothing else changes
rm "$S/spend.jsonl" "$S/check-runs.jsonl"; before="$(snap)"
"$kit/scripts/octo-feather-lane" report >"$t/out" || fail "no ledger: exit non-zero"
[[ "$(grep -c '^  spend: no spend recorded (spend.jsonl: none)$' "$t/out")" == 4 \
  && "$(grep -c '^  gate time: no gate run recorded (check-runs.jsonl: none)$' "$t/out")" == 4 ]] \
  && grep -qx 'gate budget o/a: no gate run recorded (check-runs.jsonl: none)' "$t/out" \
  && grep -qx 'unread: none' "$t/out" || fail "no ledger: $(cat "$t/out")"
[[ "$(snap)" == "$before" ]] || fail "the report changed the state dir"

# no read alone: the session of the sed script, the grep, the aborted batch and the failed reads reads none
mkdir -p "$t/pi-mention/sessions/--w-b--"; cp "$t/pi/sessions/--w-b--/impl-3.jsonl" "$t/pi-mention/sessions/--w-b--/"
PI_CODING_AGENT_DIR="$t/pi-mention" "$kit/scripts/octo-feather-lane" report >"$t/out" || fail "mentions: exit non-zero"
[[ "$(sed -n '/^skill reach/,/^unread:/p' "$t/out")" == "skill reach (Pi sessions active in the last 7 days; per role: skill read/offered, sessions):
  implementer (1 session): commit 0/1, tdd 0/1
unread: none" ]] || fail "mentions counted as reads: $(sed -n '/^skill reach/,$p' "$t/out")"

# an unreadable Pi session file: named under unread:, the rest of the skill reach still counted
chmod 000 "$t/pi/sessions/--w-b--/review-1.jsonl"; before="$(snap)"
"$kit/scripts/octo-feather-lane" report >"$t/out" || fail "unreadable session: exit non-zero"
grep -qx '  unread: Pi session --w-b--/review-1.jsonl: .*Permission denied.*' "$t/out" \
  && grep -qx '  implementer (4 sessions): commit 1/4, tdd 3/4' "$t/out" && ! grep -q '^  code reviewer' "$t/out" \
  && grep -qx 'unread: Pi session --w-b--/review-1.jsonl' "$t/out" || fail "unreadable session: $(sed -n '/^skill reach/,$p' "$t/out")"
[[ "$(snap)" == "$before" ]] || fail "the report changed the state dir or a session file"
echo "lane-report test: ok"
