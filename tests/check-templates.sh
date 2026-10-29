#!/usr/bin/env bash
# Integration test for the check-templates gate (owner: docs/specs/templates.spec.html#acceptance-same-gate,
# #118, #362, #261 review 5): each template's git hook, run against a recording just (it must call exactly
# `just check` and exit with its status; text that merely names it fails), check-languages in each template's
# gate, each template's mise pins (files present, the kit's mise-version, shared tools at the kit's versions) and templates/python's
# byte copy of the kit's trend hook. In a throwaway git repo of the kit's tracked files,
# each edit makes `just check-templates` fail or pass. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
(cd "$kit" && git ls-files -z | xargs -0 tar -cf - 2>/dev/null) | tar -xf - -C "$t"
(cd "$t" && git init -q && git add -A)
(cd "$t" && just check-templates >/dev/null 2>&1) || { echo "check-templates test: clean copy is not green" >&2; (cd "$t" && just check-templates) >&2; exit 1; }
hook=templates/python/.githooks/pre-commit
# run FILE OLD NEW: the line OLD in FILE replaced by NEW, then `just check-templates`; sets rc, out; FILE is restored.
run() {
  cp "$t/$1" "$t/.run-old"
  OLD="$2" NEW="$3" perl -i -pe 's/^\Q$ENV{OLD}\E$/$ENV{NEW}/' "$t/$1"
  ! cmp -s "$t/$1" "$t/.run-old" || { echo "check-templates test: '$2' not found in $1" >&2; exit 1; }
  set +e; out="$(cd "$t" && just check-templates 2>&1)"; rc=$?; set -e
  mv "$t/.run-old" "$t/$1"
}
# expect FILE OLD NEW [REPORT]: the edit fails just check-templates, its output naming REPORT.
expect() {
  local want="${4:-must run \`just check\` and exit with its status}"
  run "$1" "$2" "$3"
  [[ "$rc" != 0 ]] || { echo "check-templates test: $1 with '$3' passed just check-templates" >&2; exit 1; }
  grep -qF "$want" <<<"$out" || { echo "check-templates test: $1 with '$3' did not report: $want" >&2; echo "$out" >&2; exit 1; }
}
allow() {
  run "$@"
  [[ "$rc" == 0 ]] || { echo "check-templates test: $1 with '$3' failed just check-templates" >&2; echo "$out" >&2; exit 1; }
}
# The hook runs the gate, judged by running it: text naming `just check` is not enough (review 5's repro).
expect "$hook" 'exec just check' 'echo "just check"'
expect "$hook" 'exec just check' '# exec just check'
expect "$hook" 'exec just check' 'exec just check-scripts'
expect "$hook" 'exec just check' 'just check; just check'
expect "$hook" 'exec just check' 'just check; exit 0' 'with just exiting 1 it exited 0'
allow "$hook" 'exec just check' '  exec just check  # the gate'
allow "$hook" 'exec just check' 'just check'
pj=templates/python/justfile; tj=templates/typescript/justfile
expect "$pj" 'export GATE_RECIPES := "check-languages check-scripts check-lint check-format check-types check-imports"' \
  'export GATE_RECIPES := "check-scripts check-lint check-format check-types check-imports"' 'the gate never runs check-languages'
expect "$tj" 'check: check-languages check-scripts check-ts check-arch check-dead-code check-tests' \
  'check: check-scripts check-ts check-arch check-dead-code check-tests' 'the gate never runs check-languages'
expect templates/python/mise-version "$(cat "$t/mise-version")" '2000.1.1' "templates/python/mise-version is 2000.1.1, the kit's is $(cat "$t/mise-version")"
expect templates/typescript/mise.toml 'just = "1.21.0"' 'just = "1.20.0"' "templates/typescript/mise.toml pins just 1.20.0, the kit 1.21.0: set just = '1.21.0' there, then mise lock"
mv "$t/templates/python/mise.lock" "$t/.lock-old"
set +e; out="$(cd "$t" && just check-templates 2>&1)"; rc=$?; set -e
mv "$t/.lock-old" "$t/templates/python/mise.lock"
[[ "$rc" != 0 ]] && grep -qF "templates/python/mise.lock is missing" <<<"$out" || { echo "check-templates test: a missing mise.lock passed or was not named" >&2; echo "$out" >&2; exit 1; }
# The template's trend hook drifts from the kit's: one appended line, nothing read from the source.
copy=templates/python/tests/conftest.py
cp "$t/$copy" "$t/.copy-old"; printf '# copy drift\n' >> "$t/$copy"
set +e; out="$(cd "$t" && just check-templates 2>&1)"; rc=$?; set -e
mv "$t/.copy-old" "$t/$copy"
[[ "$rc" != 0 ]] && grep -qF "$copy differs from the kit's tests/gate/conftest.py; fix: cp" <<<"$out" || { echo "check-templates test: a drifted $copy passed or was not named" >&2; echo "$out" >&2; exit 1; }
echo "check-templates: ok (hook run against a recording just: echo-only, commented, wrong recipe, called twice, exit swallowed fail; #362 check-languages in each gate, mise files and versions, trend hook copy)"
