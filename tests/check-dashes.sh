#!/usr/bin/env bash
# Command test for the check-dashes gate (rule and carve-outs: #121 D7; their cases, in-process:
# tests/gate/kit/test_check_dashes.py). In a throwaway git copy of the kit's tracked files, the clean
# copy passes `just check-dashes` and one planted dash fails it, naming the file and the fix.
# Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
(cd "$kit" && git ls-files -z | xargs -0 tar -cf - 2>/dev/null) | tar -xf - -C "$t"
g() { git -C "$t" -c user.name=t -c user.email=t@t "$@"; }
g init -q; g add -A; g commit -qm base
(cd "$t" && just check-dashes >/dev/null 2>&1) || { echo "check-dashes test: clean copy is not green" >&2; (cd "$t" && just check-dashes) >&2; exit 1; }
# The dashes, written as bytes so this file stays clean under the check it tests.
em="$(printf '\xe2\x80\x94')"
# run FILE TEXT: TEXT appended to FILE (new or tracked), then `just check-dashes`; sets rc, out; the copy is restored.
run() {
  local old=""; [[ -e "$t/$1" ]] && { old="$t/.run-old"; cp "$t/$1" "$old"; }
  mkdir -p "$t/$(dirname "$1")"; printf '%s\n' "$2" >> "$t/$1"; g add -f "$1"
  set +e; out="$(cd "$t" && just check-dashes 2>&1)"; rc=$?; set -e
  if [[ -n "$old" ]]; then mv "$old" "$t/$1"; g add "$1"; else g rm -qf --cached "$1"; rm -f "$t/$1"; fi
}
expect() {
  run "$@"
  [[ "$rc" != 0 ]] || { echo "check-dashes test: $1 with '$2' passed just check-dashes" >&2; exit 1; }
  grep -qF "$1" <<<"$out" || { echo "check-dashes test: $1 not named in the output" >&2; echo "$out" >&2; exit 1; }
  grep -qF "replace the em/en dashes above" <<<"$out" || { echo "check-dashes test: the fix not named in the output" >&2; echo "$out" >&2; exit 1; }
}
expect docs/wiring-probe.txt "probe $em"
[[ -z "$(g status --porcelain)" ]] || { echo "check-dashes test: cleanup left changes in the copy" >&2; g status --short >&2; exit 1; }
echo "check-dashes: ok (clean copy passes, a planted dash fails)"
