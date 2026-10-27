#!/usr/bin/env bash
# Integration test for `octo-feather-lane report` (docs/specs/comms.spec.html#factory-report, issue #248),
# no network: fake gh and herdr from tests/fixtures/lane-report/ on PATH, fixture state in a temp XDG_STATE_HOME.
# Proves comms#acceptance-report-lanes, #acceptance-report-any-target, #acceptance-report-unreadable,
# #acceptance-report-owner-queue, #acceptance-report-owner-caught.
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
run() { # expected-file; runs the report, normalizes now, state dir and ages, diffs
  local rc=0
  "$kit/scripts/octo-feather-lane" report >"$t/out" 2>"$t/err" || rc=$?
  [[ $rc == 0 ]] || fail "exit $rc: $(cat "$t/err" "$t/out")"
  sed -E "1s/^report at [0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:]{8}Z/report at NOW/; s#$S#STATE#; s/\(([0-9]+d)?([0-9]+h)?[0-9]+m ago\)/(AGE ago)/g" "$t/out" >"$t/norm"
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
echo "lane-report test: ok"
