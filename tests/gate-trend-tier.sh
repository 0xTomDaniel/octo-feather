#!/usr/bin/env bash
# Integration test for the trend line's tier (tests/gate/conftest.py, the hook templates/python copies; #536): pytest,
# run as a command on a throwaway suite holding a copy of the hook, appends one check-runs.jsonl line per run whose
# tier is `full` only when the invocation narrowed nothing (no paths or node ids, -k, -m, --lf, --deselect,
# --ignore), xdist or not, else `subset`. The gate-time budget counts full runs only (comms #report-field-gate-time).
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
n=0
expect() { # TIER ITEMS PYTEST_ARGS...: one more trend line, with that tier and that many steps
  local want="$1" items="$2"; shift 2
  (cd "$t/s" && uv run --project "$kit" --locked --offline --no-sync pytest -q "$@" >"$t/out" 2>&1) || fail "pytest $*: $(cat "$t/out")"
  n=$((n + 1)); [[ "$(wc -l <"$trend")" == "$n" ]] || fail "pytest $*: no one new trend line"
  got="$(tail -1 "$trend" | python3 -c 'import json, sys; d = json.load(sys.stdin); print(d.get("tier"), len(d["steps"]))')"
  [[ "$got" == "$want $items" ]] || fail "pytest $*: tier and steps '$got', want '$want $items'"
}
expect full 3
expect full 3 -n 2
expect subset 2 tests/test_ab.py
expect subset 1 tests/test_ab.py::test_a
expect subset 1 -k test_c
expect subset 1 -n 2 -k test_c
expect subset 2 --deselect tests/test_c.py::test_c
expect subset 2 --ignore tests/test_c.py
expect subset 3 -m "not slow"
echo "gate-trend-tier: ok (full with no narrowing, xdist too; subset for a path, a node id, -k, -k under xdist, --deselect, --ignore, -m)"
