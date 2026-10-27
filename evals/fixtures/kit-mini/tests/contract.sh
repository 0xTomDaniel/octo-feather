#!/usr/bin/env bash
# Integration test for octo-feather-contract: run as a command. The kit's own qc.toml is ok; a missing key and a
# folder with no qc.toml each fail naming it. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
t="$(cd "$t" && pwd -P)"
fail() { echo "contract test: $*" >&2; exit 1; }
cmd="$kit/scripts/octo-feather-contract"
run() { set +e; out="$("$cmd" "$@" 2>&1)"; rc=$?; set -e; }

run "$kit"
[[ "$rc" == 0 && "$out" == "octo-feather-contract: $kit/qc.toml: ok (format 1)" ]] || fail "kit contract not ok (exit $rc): $out"
mkdir -p "$t/no-entry"; sed -e '/^\[entry\]/,/^command/d' "$kit/qc.toml" >"$t/no-entry/qc.toml"
run "$t/no-entry"
[[ "$rc" == 1 ]] && grep -qF 'qc.toml: missing entry' <<<"$out" || fail "no entry: exit $rc: $out"
mkdir -p "$t/none"
run "$t/none"
[[ "$rc" == 1 ]] && grep -qF "no qc.toml at $t/none/qc.toml" <<<"$out" || fail "no contract: exit $rc: $out"
echo "contract test: ok"
