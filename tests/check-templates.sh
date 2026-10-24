#!/usr/bin/env bash
# Integration test for the check-templates gate (owner: docs/specs/templates.spec.html#acceptance-same-gate,
# #118): the hook and CI workflow lines it reads. In a throwaway copy of
# the kit's tracked files, each edited line makes `just check-templates` fail or pass. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
(cd "$kit" && git ls-files -z | xargs -0 tar -cf - 2>/dev/null) | tar -xf - -C "$t"
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
expect() {
  run "$@"
  [[ "$rc" != 0 ]] || { echo "check-templates test: $1 with '$3' passed just check-templates" >&2; exit 1; }
  grep -qF 'must run just check' <<<"$out" || { echo "check-templates test: $1 with '$3' did not report: must run just check" >&2; echo "$out" >&2; exit 1; }
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
echo "check-templates: ok (#118 cases: commented and real just check lines in the hook and CI)"
