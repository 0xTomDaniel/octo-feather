#!/usr/bin/env bash
# Integration test for scripts/check-test-surface (#104): a kit test that loads a script as a module fails,
# naming the line and the public-surface fix; the kit's own tests pass. The real past mistake is
# tests/fixtures/test-surface/accepted-d6adb2a.sh, verbatim from #96. The loader forms live in fixtures
# so this file stays clean under the check it tests. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
C="$kit/scripts/check-test-surface"; F="$kit/tests/fixtures/test-surface"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fail() { echo "check-test-surface test: $*" >&2; exit 1; }
run() { local want="$1"; shift; set +e; out="$("$C" "$@" 2>&1)"; rc=$?; set -e
  [[ "$rc" == "$want" ]] || fail "'$*' want exit $want, got $rc: $out"; }
fix="test it through its public surface: run the script as a command or server"

run 0; [[ "$out" == "test surface: ok ("* ]] || fail "kit tests: $out"
run 1 "$F/accepted-d6adb2a.sh"
[[ "$out" == *"accepted-d6adb2a.sh:4: loads code as a module ("*"); $fix"* ]] || fail "#96 module load not named: $out"
[[ "$out" == *"ETag of a running review-serve.py"* ]] || fail "fix example missing: $out"
# A comment, a dot dir, a path run as a command and a stdlib import pass; each loader form fails on its own line.
run 0 "$F/good.sh"
while IFS= read -r bad; do
  printf 'ok=1\n%s\n' "$bad" >"$t/x.sh"
  run 1 "$t/x.sh"; [[ "$out" == "$t/x.sh:2: loads code as a module ("*"); $fix"* ]] || fail "not caught: $bad: $out"
done <"$F/bad-forms.txt"
run 2 "$t/missing.sh"
echo "check-test-surface: ok (kit tests pass; the #96 fixture and $(wc -l <"$F/bad-forms.txt") loader forms fail naming the fix; comments, dot paths, commands and stdlib imports pass)"
