#!/usr/bin/env bash
# Integration test for scripts/octo-feather-spec-status: one good and one bad
# fixture (tests/fixtures/spec-status/), then init and built on a copy. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
S="$kit/scripts/octo-feather-spec-status"; F="$kit/tests/fixtures/spec-status"
"$S" check "$F/good" >/dev/null || { echo "spec-status test: good fixture failed" >&2; exit 1; }
set +e; out="$("$S" check "$F/bad" 2>&1)"; rc=$?; set -e
[[ "$rc" == 1 ]] || { echo "spec-status test: bad fixture passed" >&2; exit 1; }
for want in "missing criterion acceptance-b" "extra criterion acceptance-z" "duplicate key 'acceptance-a'" \
            "duplicate criterion id acceptance-c" "status must be planned or built" "a built criterion names the PR"; do
  grep -qF "$want" <<<"$out" || { echo "spec-status test: bad fixture did not report: $want" >&2; echo "$out" >&2; exit 1; }
done
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
cp "$F/good/demo.spec.html" "$t/"
"$S" init "$t/demo.spec.html" 0123abc >/dev/null
"$S" built "$t/demo.status.json" 7 acceptance-a
"$S" check "$t" >/dev/null || { echo "spec-status test: init + built produced a bad file" >&2; exit 1; }
grep -q '"pr": 7' "$t/demo.status.json" || { echo "spec-status test: built did not record the PR" >&2; exit 1; }
echo "spec-status: ok (good, bad: missing, extra, duplicate, bad status, built without PR; init, built)"
