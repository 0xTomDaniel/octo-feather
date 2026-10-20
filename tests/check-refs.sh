#!/usr/bin/env bash
# Integration test for the check-refs gate (overview #acceptance-retired-words,
# #acceptance-pi-only): in a throwaway git copy of the kit's tracked files, each
# planted bad file makes `just check` fail with the message naming the fix.
# check-refs runs before check-tests, so a red copy never recurses. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
(cd "$kit" && git ls-files -z | xargs -0 tar -cf - 2>/dev/null) | tar -xf - -C "$t"
g() { git -C "$t" -c user.name=t -c user.email=t@t "$@"; }
g init -q; g add -A; g commit -qm base
(cd "$t" && just check-refs >/dev/null 2>&1) || { echo "check-refs test: clean copy is not green" >&2; (cd "$t" && just check-refs) >&2; exit 1; }
# The retired words and runtime file names, split so this file stays clean under the check it tests.
op="op""erator"; hu="hu""man"; cl="CLA""UDE.md"; cx=".co""dex/AGENTS.md"
words='use director for the top agent and owner for the person'
pi='Pi is the only runtime'
# expect FILE CONTENT MESSAGE: tracked FILE makes `just check` fail naming MESSAGE.
expect() {
  mkdir -p "$t/$(dirname "$1")"; printf '%s' "$2" > "$t/$1"; g add -f "$1"
  set +e; out="$(cd "$t" && env -u CI just check 2>&1)"; rc=$?; set -e
  g rm -qf --cached "$1"; rm -rf "${t:?}/$1"; [[ "$1" == */* ]] && rmdir "$t/$(dirname "$1")" 2>/dev/null || true
  [[ "$rc" != 0 ]] || { echo "check-refs test: tracked $1 passed just check" >&2; exit 1; }
  grep -qF "$3" <<<"$out" || { echo "check-refs test: $1 did not report: $3" >&2; echo "$out" >&2; exit 1; }
  grep -qF "$1" <<<"$out" || { echo "check-refs test: $1 not named in the output" >&2; exit 1; }
}
expect docs/x.md "The $op spawns one supervisor per lane." "$words"
expect docs/x.md "Ask the $hu before merging." "$words"
expect README.notes.md "${hu^}s review it." "$words"
expect "$cl" "" "$pi"
expect "$cx" "" "$pi"
(cd "$t" && git ls-files | grep -qx docs/x.md) && { echo "check-refs test: cleanup left docs/x.md tracked" >&2; exit 1; }
echo "check-refs: ok (retired words in docs/ and root; root and nested projection files name Pi)"
