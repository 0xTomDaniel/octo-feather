#!/usr/bin/env bash
# Integration test for the trend line's tier (tests/gate/conftest.py, the hook templates/python copies; #536): pytest,
# run as a command on a throwaway suite holding a copy of the hook, appends one check-runs.jsonl line per run whose
# tier is `full` only when the invocation narrowed nothing (no paths or node ids, -k, -m, --lf, --deselect,
# --ignore) and, where the root's justfile declares GATE_RECIPES, the run carries exactly that value (a bare pytest
# skips the gate's static steps), xdist or not, else `subset`. The gate-time budget counts full runs only (comms #report-field-gate-time).
# One run under xdist (its controller writes the one line, a worker none), the rest without workers: a worker pool
# costs a run more than all the rest of it (#1293). Each line's tier and steps are read at the end, in one parse.
# Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fail() { echo "gate-trend-tier test: $*" >&2; exit 1; }
unset HERDR_SESSION
export XDG_STATE_HOME="$t/xdg"
trend="$XDG_STATE_HOME/octo-feather/check-runs.jsonl"
mkdir -p "$t/s/tests"; cp "$kit/tests/gate/conftest.py" "$t/s/tests/conftest.py"
printf '[tool.pytest.ini_options]\ntestpaths = ["tests"]\naddopts = "--junitxml=.pytest_cache/junit.xml"\n' > "$t/s/pyproject.toml"
printf 'def test_a():\n    pass\n\n\ndef test_b():\n    pass\n' > "$t/s/tests/test_ab.py"
printf 'def test_c():\n    pass\n' > "$t/s/tests/test_c.py"
n=0; want=()
expect() { # TIER ITEMS PYTEST_ARGS...: one more trend line, checked at the end for that tier and that many steps
  local tier="$1" items="$2"; shift 2
  (cd "$t/s" && uv run --project "$kit" --locked --offline --no-sync pytest -q "$@" >"$t/out" 2>&1) || fail "pytest $*: $(cat "$t/out")"
  n=$((n + 1)); [[ "$(wc -l <"$trend")" == "$n" ]] || fail "pytest $*: no one new trend line"
  want+=("pytest $*: $tier $items")
}
expect full 3
expect subset 2 tests/test_ab.py
expect subset 1 tests/test_ab.py::test_a
expect subset 1 -k test_c
expect subset 2 --deselect tests/test_c.py::test_c
expect subset 2 --ignore tests/test_c.py
expect subset 3 -m "not slow"
# A justfile declaring the gate's static steps (GATE_RECIPES): full only when the run carries exactly that value, so a
# bare pytest, which skips them (the template's tests/test_gate.py), records subset.
printf 'export GATE_RECIPES := "check-a check-b"\n' > "$t/s/justfile"
expect subset 3
GATE_RECIPES="check-a" expect subset 3
GATE_RECIPES="check-a check-b" expect full 3
GATE_RECIPES="check-a check-b" expect full 3 -n 2
# Each run's line, in order: its tier and its count of steps, as the run's case wants.
printf '%s\n' "${want[@]}" | python3 -c '
import json, sys
want = sys.stdin.read().splitlines()
with open(sys.argv[1]) as f:
    lines = [json.loads(ln) for ln in f]
for i, (w, d) in enumerate(zip(want, lines, strict=True), 1):
    case, tier = w.rsplit(": ", 1)
    got = "%s %d" % (d.get("tier"), len(d["steps"]))
    if got != tier:
        sys.exit("gate-trend-tier test: run %d, %s: tier and steps %s, want %s" % (i, case, got, tier))
' "$trend"
echo "gate-trend-tier: ok (full with no narrowing, xdist too; subset for a path, a node id, -k, --deselect, --ignore, -m, and without the justfile's GATE_RECIPES)"
