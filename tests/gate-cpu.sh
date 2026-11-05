#!/usr/bin/env bash
# criterion: quality#acceptance-test-cpu-shown
# Integration test for each gate item's CPU time (tests/gate/conftest.py, the hook templates/python copies; #588): the
# kit's gate runner (tests/gate/ copied unchanged) run by pytest as a command, under xdist and without it, on a
# throwaway suite of three items: light.sh, heavy.sh (its child process burns CPU over the budget) and e2e.sh (headed
# `# gate: e2e`, burning the same), with gate-budget.toml's per-test CPU budget, test_cpu_seconds, below the burn. The
# run shows each item's CPU seconds, its own and its children's; names heavy.sh over the budget with its CPU time and
# the budget, never e2e.sh or light.sh; records cpu_s per step in its trend line; and exits 0 as before (report-only).
# Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fail() { echo "gate-cpu test: $*" >&2; exit 1; }
unset HERDR_SESSION OCTO_FEATHER_QC_CLAIMS OCTO_FEATHER_QC_CAPTURE_DIR
export XDG_STATE_HOME="$t/xdg" GATE_RECIPES=""
trend="$XDG_STATE_HOME/octo-feather/check-runs.jsonl"
mkdir -p "$t/s/tests/gate"; cp "$kit/tests/gate/conftest.py" "$kit/tests/gate/test_gate.py" "$t/s/tests/gate/"
printf '[tool.pytest.ini_options]\ntestpaths = ["tests/gate"]\naddopts = "--junitxml=.pytest_cache/junit.xml"\n' > "$t/s/pyproject.toml"
printf 'budget_seconds = 300\ntest_cpu_seconds = 0.15\n' > "$t/s/gate-budget.toml"
burn=$'import time\nt = time.process_time() + 0.3\nwhile time.process_time() < t: pass'
printf '#!/usr/bin/env bash\necho light\n' > "$t/s/tests/light.sh"
printf '#!/usr/bin/env bash\npython3 -c "$(printf %q)"\n' "$burn" > "$t/s/tests/heavy.sh"
printf '#!/usr/bin/env bash\n# gate: e2e\npython3 -c "$(printf %q)"\n' "$burn" > "$t/s/tests/e2e.sh"
chmod +x "$t/s/tests/"*.sh
node="tests/gate/test_gate.py::test_script"
n=0
for workers in 1 0; do
  (cd "$t/s" && uv run --project "$kit" --locked --offline --no-sync pytest -n "$workers" >"$t/out" 2>&1) \
    || fail "-n $workers: exit $?, want 0 (the budget only reports): $(cat "$t/out")"
  out="$(cat "$t/out")"
  for s in light heavy e2e; do
    grep -qE "^ *[0-9.]+s cpu +[0-9.]+s wall +$node\[tests/$s\.sh\]" <<<"$out" || fail "-n $workers: no CPU line for $s.sh: $out"
  done
  cpu="$(sed -nE "s|^ *([0-9.]+)s cpu .*$node\[tests/heavy\.sh\]$|\1|p" <<<"$out")"
  python3 -c "import sys; sys.exit(not 0.27 <= float(sys.argv[1]) < 3)" "$cpu" \
    || fail "-n $workers: heavy.sh shows ${cpu}s CPU, want its child's 0.3s burn counted"
  grep -qxF "OVER CPU BUDGET: $node[tests/heavy.sh] ${cpu}s CPU, budget 0.15s (report-only)" <<<"$out" \
    || fail "-n $workers: heavy.sh not named over the budget with its CPU time and the budget: $out"
  grep -qE "^OVER CPU BUDGET: .*(e2e|light)\.sh" <<<"$out" && fail "-n $workers: e2e.sh or light.sh named over the budget: $out"
  grep -qxF "cpu budget: 0.15s per non-e2e test (gate-budget.toml test_cpu_seconds): 1 over, report-only" <<<"$out" \
    || fail "-n $workers: no budget line: $out"
  n=$((n + 1)); [[ "$(wc -l <"$trend")" == "$n" ]] || fail "-n $workers: no one new trend line"
  got="$(tail -1 "$trend" | python3 -c '
import json, sys
steps = {s["name"]: s.get("cpu_s") for s in json.load(sys.stdin)["steps"] if "sh]" in s["name"]}
shown = {k: v if "heavy" in k else type(v).__name__ for k, v in steps.items()}
print(" ".join(f"{k}={v}" for k, v in sorted(shown.items())))')"
  [[ "$got" == "test_script[tests/e2e.sh]=float test_script[tests/heavy.sh]=$cpu test_script[tests/light.sh]=float" ]] \
    || fail "-n $workers: trend steps' cpu_s '$got', want heavy.sh's ${cpu}"
done
echo "gate-cpu: ok (each item's CPU shown and in the trend line, child processes counted; heavy.sh named over the budget, e2e.sh never; exit 0; xdist and not)"
