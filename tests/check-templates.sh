#!/usr/bin/env bash
# Integration test for the check-templates gate (owner: docs/specs/templates.spec.html#acceptance-same-gate,
# #118, #362): the hook and CI workflow lines it reads, each template's language gate wiring and
# templates/python's byte copy of the kit checker. In a throwaway git repo of the kit's tracked files,
# each edit makes `just check-templates` fail or pass. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
(cd "$kit" && git ls-files -z | xargs -0 tar -cf - 2>/dev/null) | tar -xf - -C "$t"
(cd "$t" && git init -q && git add -A)
(cd "$t" && just check-templates >/dev/null 2>&1) || { echo "check-templates test: clean copy is not green" >&2; (cd "$t" && just check-templates) >&2; exit 1; }
hook=templates/python/.githooks/pre-commit; ci=templates/typescript/.github/workflows/check.yml
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
  local want="${4:-must run just check}"
  run "$1" "$2" "$3"
  [[ "$rc" != 0 ]] || { echo "check-templates test: $1 with '$3' passed just check-templates" >&2; exit 1; }
  grep -qF "$want" <<<"$out" || { echo "check-templates test: $1 with '$3' did not report: $want" >&2; echo "$out" >&2; exit 1; }
}
allow() {
  run "$@"
  [[ "$rc" == 0 ]] || { echo "check-templates test: $1 with '$3' failed just check-templates" >&2; echo "$out" >&2; exit 1; }
}
expect "$hook" 'exec just check' '# exec just check'
expect "$hook" 'exec just check' '  #exec just check'
expect "$hook" 'exec just check' 'true # exec just check'
expect "$hook" 'exec just check' 'exec just check-scripts'
allow "$hook" 'exec just check' '  exec just check  # the gate'
expect "$ci" '      - run: just check' '      # - run: just check'
expect "$ci" '      - run: just check' '# run: just check'
expect "$ci" '      - run: just check' '      - run: echo ok # run: just check'
expect "$ci" '      - run: just check' '      - run: just check-scripts'
allow "$ci" '      - run: just check' '      - run: just check  # the gate'
pj=templates/python/justfile; tj=templates/typescript/justfile
expect "$pj" '    @python3 scripts/check-languages' '    @echo python3 scripts/check-languages' 'check-languages must be exactly `@python3 scripts/check-languages`'
expect "$tj" '    @node scripts/check-languages.ts run check-scripts' '    @echo node scripts/check-languages.ts run check-scripts' 'altered binding; use the complete invocation @node scripts/check-languages.ts run check-scripts'
expect "$pj" 'export GATE_RECIPES := "install-check check-languages check-scripts check-lint check-format check-types check-imports"' 'export GATE_RECIPES := "install-check check-scripts check-lint check-format check-types check-imports"' 'add check-languages to GATE_RECIPES'
expect "$tj" 'export GATE_RECIPES := "install-check check-languages check-scripts check-ts check-arch check-dead-code"' 'export GATE_RECIPES := "install-check check-languages check-ts check-arch check-dead-code"' 'shellcheck: bind check-scripts in the reachable gate'
expect templates/typescript/languages.json '        "shellcheck"' '' 'shell lists no tool'
expect templates/python/scripts/language_support.py 'LAUNCHERS = (' 'LAUNCHERS = (  # drifted' 'templates/python/scripts/language_support.py differs from the kit'"'"'s scripts/language_support.py; fix: cp'
# A tracked file of no declared language in a template.
printf 'package main\n' > "$t/templates/typescript/main.go"; (cd "$t" && git add templates/typescript/main.go)
set +e; out="$(cd "$t" && just check-templates 2>&1)"; rc=$?; set -e
[[ "$rc" != 0 ]] && grep -qF 'main.go: unknown type; declare its language or reasoned exemption' <<<"$out" || { echo "check-templates test: a tracked main.go passed or was not named" >&2; echo "$out" >&2; exit 1; }
echo "check-templates: ok (#118 hook and CI lines; #362 language bindings, gate reachability, shellcheck coverage, checker copy, unknown file)"
