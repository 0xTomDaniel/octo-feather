#!/usr/bin/env bash
# Command test for the check-refs gate (overview #acceptance-retired-words, #acceptance-pi-only; the
# rules and their cases, in-process: tests/gate/kit/test_check_refs.py). In a throwaway git copy of the
# kit's tracked files, the clean copy passes `just check-refs` and one planted retired word fails it,
# naming the file and the fix; one case runs `just check` to prove the gate includes check-refs.
# Run by `just check`.
set -euo pipefail
# The one `just check` case in the copy runs this test there too (its tests/*.sh step): stop there, nested.
[[ -z "${CHECK_REFS_TEST_COPY:-}" ]] || { echo "check-refs test: nested run in a copy (a planted file passed check-refs)" >&2; exit 1; }
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t" "$t.home"' EXIT
(cd "$kit" && git ls-files -z | xargs -0 tar -cf - 2>/dev/null) | tar -xf - -C "$t"
g() { git -C "$t" -c user.name=t -c user.email=t@t "$@"; }
g init -q; g add -A; g commit -qm base
(cd "$t" && just check-refs >/dev/null 2>&1) || { echo "check-refs test: clean copy is not green" >&2; (cd "$t" && just check-refs) >&2; exit 1; }
# The retired words, split so this file stays clean under the check it tests.
op="op""erator"; hu="hu""man"
words='use director for the top agent and owner for the person'
# One planted retired word fails `just check-refs`, naming the file and the fix; the copy is restored after.
mkdir -p "$t/docs/notes"; printf '%s\n' "The ${op}s merge their own lanes." > "$t/docs/notes/y.md"; g add -f docs/notes/y.md
set +e; out="$(cd "$t" && just check-refs 2>&1)"; rc=$?; set -e
g rm -qf --cached docs/notes/y.md; rm -rf "$t/docs/notes"
[[ "$rc" != 0 ]] || { echo "check-refs test: docs/notes/y.md with a retired word passed just check-refs" >&2; exit 1; }
grep -qF "docs/notes/y.md:1:" <<<"$out" && grep -qF "$words" <<<"$out" || { echo "check-refs test: docs/notes/y.md not reported: $words" >&2; echo "$out" >&2; exit 1; }
[[ -z "$(g status --porcelain)" ]] || { echo "check-refs test: cleanup left changes in the copy" >&2; g status --short >&2; exit 1; }
# The gate includes check-refs: `just check` in the copy fails on a planted retired word, naming the message and
# the file. The copy keeps only this test of tests/*.sh, so the gate there starts no other test, and the guard
# above stops this one if the planted word ever got past check-refs.
# It selects only its own recipe item (PYTEST_ADDOPTS -k, pytest's own selection, #507), so no recipe before it runs.
find "$t/tests" -maxdepth 1 -name '*.sh' ! -name check-refs.sh -delete
# Nor any kit test module (its collection alone costs the nested pytest ~2 s CPU), nor the kit's packages: none
# is needed there, so check-tests' pnpm install installs nothing (tests/lib/no-packages.py).
find "$t/tests/gate" -name 'test_*.py' ! -path "$t/tests/gate/test_gate.py" -delete
"$kit/tests/lib/no-packages.py" "$t"; g add -A
printf '%s\n' "Merge once the ${hu}s agree." > "$t/docs/gate.md"; g add -f docs/gate.md
set +e; out="$(cd "$t" && env -u CI CHECK_REFS_TEST_COPY=1 XDG_STATE_HOME="$t.home" PYTEST_ADDOPTS="--color=no -k 'test_recipe and check-refs'" just check 2>&1)"; rc=$?; set -e
[[ "$rc" != 0 ]] || { echo "check-refs test: docs/gate.md with a retired word passed just check" >&2; exit 1; }
grep -qF "$words" <<<"$out" && grep -qF docs/gate.md <<<"$out" || { echo "check-refs test: just check did not report docs/gate.md: $words" >&2; echo "$out" >&2; exit 1; }
# Only its own item ran (#507): pytest's own selection, through the real `just check`.
grep -qF "FAILED tests/gate/test_gate.py::test_recipe[check-refs]" <<<"$out" && grep -qE '^=+ 1 failed(, [0-9]+ deselected)? in ' <<<"$out" \
  || { echo "check-refs test: just check ran more than its own item" >&2; echo "$out" >&2; exit 1; }
echo "check-refs: ok (clean copy passes, a planted retired word fails just check-refs and just check)"
