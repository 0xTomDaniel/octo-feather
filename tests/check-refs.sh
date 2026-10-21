#!/usr/bin/env bash
# Integration test for the check-refs gate (overview #acceptance-retired-words,
# #acceptance-pi-only): in a throwaway git copy of the kit's tracked files, each
# planted bad file makes `just check` fail with the message naming the fix.
# check-refs runs before check-tests, so a red copy never recurses. Run by `just check`.
set -euo pipefail
# A bad file the gate misses would reach check-tests in the copy and rerun this test: stop there.
[[ -z "${CHECK_REFS_TEST_COPY:-}" ]] || { echo "check-refs test: nested run in a copy (a planted file passed check-refs)" >&2; exit 1; }
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
# expect FILE CONTENT MESSAGE: FILE (new, or a tracked file CONTENT is appended to)
# makes `just check` fail naming MESSAGE; the copy is restored after.
expect() {
  local old=""; [[ -e "$t/$1" ]] && { old="$t/.expect-old"; cp "$t/$1" "$old"; printf '\n' >> "$t/$1"; }
  mkdir -p "$t/$(dirname "$1")"; printf '%s\n' "$2" >> "$t/$1"; g add -f "$1"
  set +e; out="$(cd "$t" && env -u CI CHECK_REFS_TEST_COPY=1 just check 2>&1)"; rc=$?; set -e
  if [[ -n "$old" ]]; then mv "$old" "$t/$1"; g add "$1"
  else g rm -qf --cached "$1"; rm -rf "${t:?}/$1"; [[ "$1" == */* ]] && rmdir "$t/$(dirname "$1")" 2>/dev/null || true; fi
  [[ "$rc" != 0 ]] || { echo "check-refs test: $1 with '$2' passed just check" >&2; exit 1; }
  grep -qF "$3" <<<"$out" || { echo "check-refs test: $1 did not report: $3" >&2; echo "$out" >&2; exit 1; }
  grep -qF "$1" <<<"$out" || { echo "check-refs test: $1 not named in the output" >&2; exit 1; }
}
# allow FILE CONTENT: appending CONTENT to tracked FILE keeps check-refs green; the copy is restored after.
allow() {
  cp "$t/$1" "$t/.allow-old"; printf '%s\n' "$2" >> "$t/$1"
  set +e; out="$(cd "$t" && just check-refs 2>&1)"; rc=$?; set -e
  mv "$t/.allow-old" "$t/$1"
  [[ "$rc" == 0 ]] || { echo "check-refs test: $1 with '$2' failed check-refs" >&2; echo "$out" >&2; exit 1; }
}
expect docs/x.md "The $op spawns one supervisor per lane." "$words"
expect docs/x.md "Ask the $hu before merging." "$words"
expect README.notes.md "${hu^}s review it." "$words"
# Each exemption is a (file, exact quote) pair (QC unscoped-quote-exemption):
# the same quote in any other kit file fails (QC repro first).
expect docs/x.md "The $op spawns supervisors." "$words"
expect agents/x.md "\"The $op\" spawns lanes." "$words"
expect docs/x.md "\"The $op\" there is the owner" "$words"
expect agents/director.md "\"The $op\" there is the owner" "$words"
expect docs/x.md "agents/director.md (was agents/meta-$op.md)" "$words"
expect docs/x.md "calls the top agent $op or the person $hu" "$words"
expect docs/specs/comms.spec.html "calls the top agent $op or the person $hu" "$words"
expect docs/x.md "<table data-anchor=\"handoff-$op\">" "$words"
expect docs/x.md "<tr data-anchor=\"map-handoff-$op\"><td><code>#handoff-$op</code></td></tr>" "$words"
expect agents/x.md "spec \`#handoff-$op\`" "$words"
# In its own file only the exact quote is exempt: a retired word beside it fails (QC retired-word-line-exemption).
expect agents/director.md "See spec \`#handoff-$op\`: the $op spawns supervisors and the $hu approves merges." "$words"
expect docs/specs/comms.spec.html "<div data-anchor=\"handoff-$op-wrap\">the $op</div>" "$words"
expect docs/specs/index.spec.html "<a href=\"./comms.spec.html#handoff-$op\">the $hu</a>" "$words"
expect docs/specs/overview.spec.html "calls the top agent $op or the person $hu; ask the $hu." "$words"
expect agents/corrector.md "\"The $op\" there is the owner; the $op spawns lanes." "$words"
expect NOTICE "agents/director.md (was agents/meta-$op.md), written by the $op" "$words"
# Spec Chat's on-disk spool side name is exempt only as the SPOOL_SIDE value in the two files that set it.
allow scripts/octo-feather-accepted "SPOOL_SIDE = \"$hu\"  # Spec Chat's owner side"
allow tests/accepted.sh "SPOOL_SIDE=$hu; spool=x"
expect docs/x.md "SPOOL_SIDE = \"$hu\"" "$words"
expect agents/x.md "SPOOL_SIDE=$hu" "$words"
expect tests/accepted.sh "SPOOL_SIDE=$hu # SPOOL_SIDE: the $hu approves" "$words"
expect scripts/octo-feather-accepted "SPOOL_SIDE = \"$hu\"  # the $hu approves" "$words"
expect scripts/octo-feather-accepted "# SPOOL_SIDE ... the $hu approves" "$words"
expect "$cl" "" "$pi"
expect "$cx" "" "$pi"
[[ -z "$(g status --porcelain)" ]] || { echo "check-refs test: cleanup left changes in the copy" >&2; g status --short >&2; exit 1; }
echo "check-refs: ok (retired words in docs/ and root; exemptions per file and exact quote; root and nested projection files name Pi)"
