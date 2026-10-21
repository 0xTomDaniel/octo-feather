#!/usr/bin/env bash
# Integration test for the gate-free guard (quality #acceptance-gate-no-model): in a
# throwaway git copy of the kit's tracked files, each justfile change that makes a check
# or check-* recipe reach the product judge (qc, octo-feather-qc, Jev) or the factory
# evals (qa), by dependency, transitive dependency or body, makes `just check` fail
# saying it stays deterministic and free, before any recipe runs (no qa stub output).
# Run by `just check`.
set -euo pipefail
shopt -u patsub_replacement 2>/dev/null || true  # bash 5.2: a literal & in ${x/a/b} replacements
# A planted form the guard misses would reach check-tests in the copy and rerun this test: stop there.
[[ -z "${CHECK_GATE_FREE_TEST_COPY:-}" ]] || { echo "check-gate-free test: nested run in a copy (a planted form passed the guard)" >&2; exit 1; }
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
J="$(command -v just)"
t="$(mktemp -d)"; trap 'rm -rf "$t" "$t.bin"' EXIT
(cd "$kit" && git ls-files -z | xargs -0 tar -cf - 2>/dev/null) | tar -xf - -C "$t"
g() { git -C "$t" -c user.name=t -c user.email=t@t "$@"; }
g init -q; g add -A; g commit -qm base
orig="$(cat "$t/justfile")"; checkline="$(grep '^check:' "$t/justfile")"
msg='just check stays deterministic and free'
(cd "$t" && just check-dashes >/dev/null 2>&1) || { echo "check-gate-free test: clean copy is not green" >&2; (cd "$t" && just check-dashes) >&2; exit 1; }
# Ordinary runs are unaffected: the qa stub runs as before, qc resolves (dry run, no judge).
set +e; out="$(cd "$t" && just qa 2>&1)"; rc=$?; set -e
[[ "$rc" == 2 ]] && grep -qF 'not implemented yet' <<<"$out" || { echo "check-gate-free test: plain just qa changed" >&2; echo "$out" >&2; exit 1; }
out="$(cd "$t" && just --dry-run qc x 1 a 2>&1)" && grep -qF 'octo-feather-qc' <<<"$out" || { echo "check-gate-free test: plain just qc blocked" >&2; echo "$out" >&2; exit 1; }
# plant NEWCHECK EXTRA: the justfile with its check line replaced by NEWCHECK and EXTRA appended.
plant() { printf '%s\n\n%s\n' "${orig/"$checkline"/$1}" "$2" > "$t/justfile"; }
# expect NEWCHECK EXTRA: `just check` fails with the message, before any recipe runs.
expect() {
  plant "$1" "$2"
  set +e; out="$(cd "$t" && env -u CI CHECK_GATE_FREE_TEST_COPY=1 just check 2>&1)"; rc=$?; set -e
  printf '%s\n' "$orig" > "$t/justfile"
  [[ "$rc" != 0 ]] || { echo "check-gate-free test: passed just check: $1 / $2" >&2; exit 1; }
  grep -qF "$msg" <<<"$out" || { echo "check-gate-free test: no deterministic-and-free message: $1 / $2" >&2; echo "$out" >&2; exit 1; }
  ! grep -qE 'not implemented yet|python: ok|Recipe `' <<<"$out" || { echo "check-gate-free test: a recipe ran before the guard: $1 / $2" >&2; echo "$out" >&2; exit 1; }
}
# allow EXTRA: appending EXTRA (wired into check) keeps the guard green.
allow() {
  plant "${checkline/check:/check: check-zz}" "$1"
  set +e; out="$(cd "$t" && just check-dashes 2>&1)"; rc=$?; set -e
  printf '%s\n' "$orig" > "$t/justfile"
  [[ "$rc" == 0 ]] || { echo "check-gate-free test: harmless recipe failed: $1" >&2; echo "$out" >&2; exit 1; }
}
c="$checkline"; z="${c/check:/check: check-zz}"
# Dependency forms: the QC repro, after &&, with arguments, transitive, a check-* outside check.
expect "${c/check:/check: qa}" ""
expect "$c && qa" ""
expect "${c/check:/check: (qc \"x\" \"1\" \"a\")}" ""
expect "$z" $'check-zz: helper-zz\nhelper-zz: qa'
expect "$c" $'check-zz: (qc "x" "1" "a")'
expect "$c" $'check-zz: helper-zz\nhelper-zz: deeper-zz\ndeeper-zz: (qc "x" "1" "a")'
# Body forms, in check-* recipes inside and outside check, and in a recipe they reach.
expect "$z" $'check-zz:\n    just qa'
expect "$c" $'check-zz:\n    @just --justfile "{{justfile()}}" qa --all'
expect "$c" $'check-zz:\n    octo-feather-qc x 1 a'
expect "$c" $'check-zz:\n    "{{root}}/scripts/octo-feather-qc" x 1 a'
expect "$c" $'check-zz:\n    #!/usr/bin/env bash\n    set -e\n    jev judge .'
expect "$z" $'check-zz:\n    just helper-zz\nhelper-zz:\n    octo-feather-qc x 1 a'
expect "$z" $'check-zz: helper-zz\nhelper-zz:\n    @echo hi; just qa'
# Spelling and evasion variants: case, shell quotes, interpolation, variables, defaults, arguments.
expect "$c" $'check-zz:\n    JUST QA'
expect "$c" $'check-zz:\n    Jev run'
expect "$c" $'check-zz:\n    just q\'\'a'
expect "$c" $'check-zz:\n    just "q"c x 1 a'
expect "$c" $'check-zz:\n    just {{ "q" + "a" }}'
expect "$c" $'zz_judge := "octo-feather-" + "qc"\ncheck-zz:\n    {{zz_judge}} x 1 a'
expect "$z" $'check-zz a=`just qa`:\n    echo {{a}}'
expect "$z" $'check-zz: (helper-zz `just qa`)\nhelper-zz b:\n    echo {{b}}'
# Mixed: a harmless check-* beside a bad one still fails; the harmless forms alone pass.
expect "$z" $'check-zz:\n    echo quality aqua qcow2 jevons\ncheck-yy:\n    just qa'
allow $'check-zz:\n    echo quality aqua qcow2 jevons octo-feather-qcx'
allow $'check-zz: helper-zz\nhelper-zz:\n    echo QAZ'
# From another working directory (backticks run there; the guard is the published command on PATH).
w="$t.bin"; mkdir -p "$w"
out="$(cd "$w" && PATH="$t/scripts:$PATH" just --justfile "$t/justfile" --working-directory "$w" --dry-run qc x 1 a 2>&1)" \
  && out="$(cd "$w" && PATH="$t/scripts:$PATH" just --justfile "$t/justfile" --working-directory "$w" check-dashes 2>&1)" \
  || { echo "check-gate-free test: clean justfile failed from another working directory" >&2; echo "$out" >&2; exit 1; }
plant "${c/check:/check: qa}" ""
set +e; out="$(cd "$w" && PATH="$t/scripts:$PATH" CHECK_GATE_FREE_TEST_COPY=1 just --justfile "$t/justfile" --working-directory "$w" check 2>&1)"; rc=$?; set -e
printf '%s\n' "$orig" > "$t/justfile"; rm -rf "$w"
[[ "$rc" != 0 ]] && grep -qF "$msg" <<<"$out" && ! grep -qF 'not implemented yet' <<<"$out" || { echo "check-gate-free test: check: qa passed from another working directory" >&2; echo "$out" >&2; exit 1; }
# Fails closed: a broken just (error exit, bad JSON) or a silent guard interpreter never reads as ok.
# stub NAME BODY: an executable NAME first on the PATH the guard runs with; the outer just is the real one.
stub() {
  local b="$t.bin"; mkdir -p "$b"; printf '#!/bin/sh\n%s\n' "$2" > "$b/$1"; chmod +x "$b/$1"
  set +e; out="$(cd "$t" && PATH="$b:$PATH" CHECK_GATE_FREE_TEST_COPY=1 "$J" check 2>&1)"; rc=$?; set -e
  rm -rf "$b"
  [[ "$rc" != 0 ]] || { echo "check-gate-free test: stub $1 ($2) passed just check" >&2; exit 1; }
  grep -qF "$3" <<<"$out" || { echo "check-gate-free test: stub $1 ($2) did not report: $3" >&2; echo "$out" >&2; exit 1; }
  ! grep -qE 'python: ok|just check: ok' <<<"$out" || { echo "check-gate-free test: stub $1 let a recipe run" >&2; exit 1; }
}
stub just 'echo "just: broken (test stub)" >&2; exit 2' 'check-gate-free: error: just --dump exited 2'
stub just 'echo "{}"' 'check-gate-free: error: unexpected just --dump JSON'
stub just 'echo "not json"' 'check-gate-free: error: unexpected just --dump JSON'
stub python3 'exit 0' "$msg"
[[ "$(cat "$t/justfile")" == "$orig" && -z "$(g status --porcelain)" ]] || { echo "check-gate-free test: cleanup left changes in the copy" >&2; g status --short >&2; exit 1; }
echo "check-gate-free: ok (dependency, transitive, after-&&, argument and body forms; spelling and evasion variants; mixed inputs; fails closed)"
