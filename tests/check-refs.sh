#!/usr/bin/env bash
# Integration test for the check-refs gate (overview #acceptance-retired-words,
# #acceptance-pi-only): in a throwaway git copy of the kit's tracked files, each
# planted bad file makes `just check-refs` fail with the message naming the fix (#207: the recipe under test, not
# the whole gate per case); one case runs `just check` to prove the gate includes check-refs. Run by `just check`.
set -euo pipefail
# The one `just check` case in the copy runs this test there too (its tests/*.sh step): stop there, nested.
[[ -z "${CHECK_REFS_TEST_COPY:-}" ]] || { echo "check-refs test: nested run in a copy (a planted file passed check-refs)" >&2; exit 1; }
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t" "$t.home"' EXIT
(cd "$kit" && git ls-files -z | xargs -0 tar -cf - 2>/dev/null) | tar -xf - -C "$t"
g() { git -C "$t" -c user.name=t -c user.email=t@t "$@"; }
g init -q; g add -A; g commit -qm base
(cd "$t" && just check-refs >/dev/null 2>&1) || { echo "check-refs test: clean copy is not green" >&2; (cd "$t" && just check-refs) >&2; exit 1; }
# The retired words and runtime file names, split so this file stays clean under the check it tests.
op="op""erator"; hu="hu""man"; cl="CLA""UDE.md"; cx=".co""dex/AGENTS.md"
words='use director for the top agent and owner for the person'
pi='Pi is the only runtime'
# expect FILE CONTENT MESSAGE: FILE (new, or a tracked file CONTENT is appended to)
# makes `just check-refs` fail naming MESSAGE; the copy is restored after.
expect() {
  local old=""; [[ -e "$t/$1" ]] && { old="$t/.expect-old"; cp "$t/$1" "$old"; printf '\n' >> "$t/$1"; }
  mkdir -p "$t/$(dirname "$1")"; printf '%s\n' "$2" >> "$t/$1"; g add -f "$1"
  set +e; out="$(cd "$t" && just check-refs 2>&1)"; rc=$?; set -e
  if [[ -n "$old" ]]; then mv "$old" "$t/$1"; g add "$1"
  else g rm -qf --cached "$1"; rm -rf "${t:?}/$1"; [[ "$1" == */* ]] && rmdir "$t/$(dirname "$1")" 2>/dev/null || true; fi
  [[ "$rc" != 0 ]] || { echo "check-refs test: $1 with '$2' passed just check-refs" >&2; exit 1; }
  grep -qF "$3" <<<"$out" || { echo "check-refs test: $1 did not report: $3" >&2; echo "$out" >&2; exit 1; }
  grep -qF "$1" <<<"$out" || { echo "check-refs test: $1 not named in the output" >&2; exit 1; }
}
# allow FILE CONTENT: FILE (new, or a tracked file CONTENT is appended to) keeps check-refs green; the copy is restored after.
allow() {
  local old=""; [[ -e "$t/$1" ]] && { old="$t/.allow-old"; cp "$t/$1" "$old"; }
  mkdir -p "$t/$(dirname "$1")"; printf '%s\n' "$2" >> "$t/$1"; g add -f "$1"
  set +e; out="$(cd "$t" && just check-refs 2>&1)"; rc=$?; set -e
  if [[ -n "$old" ]]; then mv "$old" "$t/$1"; g add "$1"
  else g rm -qf --cached "$1"; rm -rf "${t:?}/$1"; rmdir -p "$t/$(dirname "$1")" 2>/dev/null || true; fi
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
expect docs/specs/comms.spec.html "uses the retired word $op or $hu" "$words"
expect docs/x.md "<table data-anchor=\"handoff-$op\">" "$words"
expect docs/x.md "<tr data-anchor=\"map-handoff-$op\"><td><code>#handoff-$op</code></td></tr>" "$words"
expect agents/x.md "spec \`#handoff-$op\`" "$words"
expect docs/x.md "\"anchors\": [\"handoff-$op\"]" "$words"
# In its own file only the exact quote is exempt: a retired word beside it fails (QC retired-word-line-exemption).
expect agents/director.md "See spec \`#handoff-$op\`: the $op spawns supervisors and the $hu approves merges." "$words"
expect docs/specs/comms.spec.html "<div data-anchor=\"handoff-$op-wrap\">the $op</div>" "$words"
expect docs/specs/index.spec.html "<a href=\"./comms.spec.html#handoff-$op\">the $hu</a>" "$words"
expect docs/specs/comms.calls.jsonl "{\"anchors\": [\"handoff-$op\"], \"what\": \"the $op\"}" "$words"
expect docs/x.md "uses the retired word $op or $hu" "$words"
expect docs/specs/overview.spec.html "uses the retired word $op or $hu; ask the $hu." "$words"
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
# A tracked file the scan cannot read is a scanner error, not no match: it fails closed, never refs: ok.
ln -s missing "$t/agents/x.md"; g add -f agents/x.md
set +e; out="$(cd "$t" && just check-refs 2>&1)"; rc=$?; set -e
g rm -qf --cached agents/x.md; rm "$t/agents/x.md"
[[ "$rc" != 0 ]] && grep -qF 'check-refs: retired-words scanner error:' <<<"$out" && ! grep -qF 'refs: ok' <<<"$out" || { echo "check-refs test: unreadable file not reported as a scanner error" >&2; echo "$out" >&2; exit 1; }
# A word character before the word is no word boundary (grep's in C.UTF-8): no retired word.
allow docs/x.md $'caf\xc3\xa9'"$op"
# Pinned, not fixed (#1117): a tracked binary file (a NUL byte, or invalid UTF-8 on the line) is not scanned for
# retired words; a lane branch default in one still fails, naming the file.
allow docs/x.md $'caf\xff: the '"$op"
printf 'the %s\0\n' "$op" > "$t/docs/x.md"; g add -f docs/x.md
set +e; out="$(cd "$t" && just check-refs 2>&1)"; rc=$?; set -e
g rm -qf --cached docs/x.md; rm "$t/docs/x.md"
[[ "$rc" == 0 ]] && grep -qF 'refs: ok' <<<"$out" || { echo "check-refs test: a NUL file's retired word failed check-refs" >&2; echo "$out" >&2; exit 1; }
printf 'Cut branch gh<N>%s\0\n' "-<slug>" > "$t/agents/x.md"; g add -f agents/x.md
set +e; out="$(cd "$t" && just check-refs 2>&1)"; rc=$?; set -e
g rm -qf --cached agents/x.md; rm "$t/agents/x.md"
[[ "$rc" != 0 ]] && grep -qF 'docs/adr/0011' <<<"$out" && grep -qF agents/x.md <<<"$out" || { echo "check-refs test: a NUL file's lane branch default not reported" >&2; echo "$out" >&2; exit 1; }
# The lane branch default, split so this file stays clean: a role restating it fails, its pointer passes.
expect agents/x.md "Cut branch gh<N>""-<slug> for the lane." "docs/adr/0011"
expect agents/x.md "else \`octo-feather/""gh<issue-number>""-<slug>\`." "docs/adr/0011"
# The #71 token shapes in kit files, docs/adr/0011 the one exempt (#121 N1 N2).
expect agents/x.md "Cut branch gh<issue>""-<slug> for the lane." "docs/adr/0011"
expect scripts/octo-feather-state "# lane branch gh<issue>""-<slug>" "docs/adr/0011"
expect agents/x.md "Worker branch gh<N>""-<worker>." "docs/adr/0011"
expect README.md "Cut branch gh<N>""-<slug> for the lane." "docs/adr/0011"
expect AGENTS.md "Cut branch gh<N>""-<slug> for the lane." "docs/adr/0011"
expect docs/guide/x.md "Cut branch gh<N>""-<slug> for the lane." "docs/adr/0011"
expect docs/adr/0017-integration-is-a-script.md "Cut branch gh<N>""-<slug> for the lane." "docs/adr/0011"
expect docs/x.md "Branch \`octo-feather/""gh<N>\`." "docs/adr/0011"
expect justfile "# lane branch gh<N>""-<slug>" "docs/adr/0011"
allow docs/adr/0011-herdr-layout.md "Rejected: \`octo-feather/""gh<issue>""-<slug>\` and gh<N>""-<slug>."
allow agents/supervisor.md "The lane branch is \`gh<N>\`: see docs/adr/0011. Worker branches gh<N>-* never match."
allow README.md "Worker branches gh<N>-* and gh<issue>-*, never the lane."
# Judgment suites' label data quote frozen history: only cases.json, reference/expectations.json and REPORT.md
# of evals/judgment-*/ skip the retired-words and lane-branch scans; the suite's other files and other suites do not.
lb="Cut branch gh<N>""-<slug> for the lane."
for f in cases.json reference/expectations.json REPORT.md; do
  allow "evals/judgment-x/$f" "\"state\": \"calls the top agent $op or the person $hu\""
  allow "evals/judgment-x/$f" "\"state\": \"$lb\""
done
for f in evals/judgment-x/suite.json evals/judgment-x/question.json evals/judgment-x/sources/t/x.sh evals/role-x/cases.json evals/judgment-x/cases.md; do
  expect "$f" "\"state\": \"calls the top agent $op\"" "$words"
  expect "$f" "\"state\": \"$lb\"" "docs/adr/0011"
done
expect "$cl" "" "$pi"
expect "$cx" "" "$pi"
[[ -z "$(g status --porcelain)" ]] || { echo "check-refs test: cleanup left changes in the copy" >&2; g status --short >&2; exit 1; }
# The gate includes check-refs: `just check` in the copy fails on a planted retired word, naming the message and
# the file. The copy keeps only this test of tests/*.sh, so the gate there starts no other test, and the guard
# above stops this one if the planted word ever got past check-refs.
# It selects only its own recipe item (PYTEST_ADDOPTS -k, pytest's own selection, #507), so no recipe before it runs.
find "$t/tests" -maxdepth 1 -name '*.sh' ! -name check-refs.sh -delete; g add -A
printf '%s\n' "Ask the $hu before merging." > "$t/docs/x.md"; g add -f docs/x.md
set +e; out="$(cd "$t" && env -u CI CHECK_REFS_TEST_COPY=1 XDG_STATE_HOME="$t.home" PYTEST_ADDOPTS="--color=no -k 'test_recipe and check-refs'" just check 2>&1)"; rc=$?; set -e
[[ "$rc" != 0 ]] || { echo "check-refs test: docs/x.md with a retired word passed just check" >&2; exit 1; }
grep -qF "$words" <<<"$out" && grep -qF docs/x.md <<<"$out" || { echo "check-refs test: just check did not report docs/x.md: $words" >&2; echo "$out" >&2; exit 1; }
# Only its own item ran (#507): pytest's own selection, through the real `just check`.
grep -qF "FAILED tests/gate/test_gate.py::test_recipe[check-refs]" <<<"$out" && grep -qE '^=+ 1 failed(, [0-9]+ deselected)? in ' <<<"$out" \
  || { echo "check-refs test: just check ran more than its own item" >&2; echo "$out" >&2; exit 1; }
echo "check-refs: ok (retired words in docs/ and root; exemptions per file and exact quote; root and nested projection files name Pi; a broken scanner fails closed; judgment label data exempt, the rest of the suite scanned)"
