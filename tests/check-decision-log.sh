#!/usr/bin/env bash
# Command test for the check-decision-log gate (quality #acceptance-decision-log-schema; the rule's
# cases, in-process: tests/gate/kit/test_check_decision_log.py). In a throwaway git copy of the kit's
# tracked files: the clean copy (no log) passes `just check-decision-log`; a broken python3, git or
# node, or no node on PATH, fails closed; one case runs `just check` to prove the gate includes
# check-decision-log. Run by `just check`.
set -euo pipefail
# The one `just check` case in the copy runs this test there too (its tests/*.sh step): stop there, nested.
[[ -z "${CHECK_DECISION_LOG_TEST_COPY:-}" ]] || { echo "check-decision-log test: nested run in a copy (a planted log passed check-decision-log)" >&2; exit 1; }
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t" "$t.home" "$t.bin"' EXIT
(cd "$kit" && git ls-files -z | xargs -0 tar -cf - 2>/dev/null) | tar -xf - -C "$t"
g() { git -C "$t" -c user.name=t -c user.email=t@t "$@"; }
g init -q; g add -A; g commit -qm base
# A repo with no tracked decisions.jsonl passes.
set +e; out="$(cd "$t" && just check-decision-log 2>&1)"; rc=$?; set -e
[[ "$rc" == 0 ]] && grep -qF 'decision-log: ok (0 files)' <<<"$out" || { echo "check-decision-log test: clean copy with no log is not green" >&2; echo "$out" >&2; exit 1; }
# Fails closed: a broken python3 or git (a stub first on the caller's PATH, which the justfile keeps ahead of its
# tools) fails the gate, never decision-log: ok.
broken() {
  local h="$t.bin"; mkdir -p "$h"
  printf '#!/bin/sh\necho "%s: broken (check-decision-log test stub)" >&2\nexit 2\n' "$1" > "$h/$1"; chmod +x "$h/$1"
  set +e; out="$(cd "$t" && PATH="$h:$PATH" just check-decision-log 2>&1)"; rc=$?; set -e
  rm -rf "$h"
  [[ "$rc" != 0 ]] && grep -qF "$1: broken" <<<"$out" && ! grep -qF 'decision-log: ok' <<<"$out" || { echo "check-decision-log test: broken $1 passed check-decision-log" >&2; echo "$out" >&2; exit 1; }
}
broken python3
broken git
grep -qF 'git ls-files exited 2' <<<"$out" || { echo "check-decision-log test: broken git not reported as a git error" >&2; echo "$out" >&2; exit 1; }
broken node
grep -qF 'node exited 2; the check cannot pass' <<<"$out" || { echo "check-decision-log test: broken node not reported" >&2; echo "$out" >&2; exit 1; }
# No node on PATH: fails closed naming the fix.
mkdir -p "$t.bin"; ln -s "$(command -v git)" "$t.bin/git"
# Use the locked interpreter: PATH isolation removes uv too, not just node.
python="$(cd "$kit" && uv run --locked --offline --no-sync python -c 'import sys; print(sys.executable)')"
set +e; out="$(cd "$t" && PATH="$t.bin" "$python" scripts/check-decision-log 2>&1)"; rc=$?; set -e; rm -rf "$t.bin"
[[ "$rc" == 2 ]] && grep -qF 'check-decision-log: node not found on PATH: install node (Pi needs it too); the check cannot pass' <<<"$out" \
  || { echo "check-decision-log test: missing node did not fail closed" >&2; echo "$out" >&2; exit 1; }
[[ -z "$(g status --porcelain)" ]] || { echo "check-decision-log test: cleanup left changes in the copy" >&2; g status --short >&2; exit 1; }
# The gate includes check-decision-log: `just check` in the copy fails on a nested log line missing why, naming
# FILE:LINE. The copy keeps only this test of tests/*.sh, so the gate there starts no other test, and the guard
# above stops this one if the planted log ever got past check-decision-log.
# It selects only its own recipe item (PYTEST_ADDOPTS -k, pytest's own selection, #507), so no recipe before it runs.
find "$t/tests" -maxdepth 1 -name '*.sh' ! -name check-decision-log.sh -delete
# Nor any kit test module (its collection alone costs the nested pytest ~2 s CPU), nor the kit's packages: none
# is needed there, so check-tests' pnpm install installs nothing (tests/lib/no-packages.py).
find "$t/tests/gate" -name 'test_*.py' ! -path "$t/tests/gate/test_gate.py" -delete
"$kit/tests/lib/no-packages.py" "$t"; g add -A
head='"ts":"2026-10-19T00:00:00Z","agent":"implementer","phase":"handoff","decision":"ready"'
tail='"evidence":"just check","result":"pending"'
N=docs/gate/decisions.jsonl
mkdir -p "$t/docs/gate"; printf '%s\n' "{$head,\"why\":\"gate green\",$tail}" "{$head,$tail}" > "$t/$N"; g add -f "$N"
set +e; out="$(cd "$t" && env -u CI CHECK_DECISION_LOG_TEST_COPY=1 XDG_STATE_HOME="$t.home" PYTEST_ADDOPTS="--color=no -k 'test_recipe and check-decision-log'" just check 2>&1)"; rc=$?; set -e
[[ "$rc" != 0 ]] || { echo "check-decision-log test: $N missing why passed just check" >&2; exit 1; }
grep -qF "check-decision-log: $N:2: missing why" <<<"$out" || { echo "check-decision-log test: just check did not report $N:2: missing why" >&2; echo "$out" >&2; exit 1; }
# Only its own item ran (#507): pytest's own selection, through the real `just check`.
grep -qF "FAILED tests/gate/test_gate.py::test_recipe[check-decision-log]" <<<"$out" && grep -qE '^=+ 1 failed(, [0-9]+ deselected)? in ' <<<"$out" \
  || { echo "check-decision-log test: just check ran more than its own item" >&2; echo "$out" >&2; exit 1; }
echo "check-decision-log: ok (clean copy passes; a broken python3, git or node, or no node, fails closed; just check fails on a planted log line)"
