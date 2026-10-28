#!/usr/bin/env bash
# Integration test for `just check-ts` (#245), in a throwaway copy of the kit's tracked files:
#   empty pnpm store (a fresh store dir): fails naming the fetch command, never the network (--offline);
#   clean copy: passes;
#   a type error and a lint violation added to the extension: fails naming each file and line;
#   eslint's baseline only shrinks: one more `any` in extensions/spend-ledger.ts fails naming its line, and a fixed
#   violation leaves an unused suppression that fails naming --prune-suppressions.
# Offline: the copy installs from the box's pnpm store (CI's pnpm step fills it). Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fail() { echo "check-ts test: $1" >&2; [[ -z "${out:-}" ]] || echo "$out" >&2; exit 1; }
(cd "$kit" && git ls-files -z | xargs -0 tar -cf - 2>/dev/null) | tar -xf - -C "$t"
# run [ENV...]: just check-ts in the copy into $out and $rc.
run() { set +e; out="$(cd "$t" && env "$@" just check-ts 2>&1)"; rc=$?; set -e; }
# has TEXT...: each TEXT is in $out.
has() { for s in "$@"; do grep -qF -- "$s" <<<"$out" || fail "output lacks: $s"; done; }

run npm_config_store_dir="$t.store"; rm -rf "$t.store"
[[ "$rc" != 0 ]] || fail "passed with an empty pnpm store"
has "fetch them once, with network: pnpm install --frozen-lockfile --dir $t"

run; [[ "$rc" == 0 ]] || fail "clean copy is not green"
has "ts: ok ("

# One failing run for every red case (each run costs seconds): a type error and a lint violation in the extension,
# one more `any` in baselined spend-ledger.ts, and a fixed violation in the fixture (its suppression now unused).
ext=extensions/resume-on-error.ts; n="$(wc -l <"$t/$ext")"
printf 'export const typeProbe: number = "x";\nexport function lintProbe(x: any): unknown { return x; }\n' >>"$t/$ext"
printf 'export function probe(x: any): unknown { return x; }\n' >>"$t/extensions/spend-ledger.ts"
m="$(wc -l <"$t/extensions/spend-ledger.ts")"
sed -i 's/    async execute() {/    execute() {/' "$t/tests/fixtures/spend-ledger/nested-tool.ts"
run; [[ "$rc" != 0 ]] || fail "a type error, lint violations and an unused suppression passed"
has "$ext($((n + 1)),14): error TS2322" "check-ts: fix each tsc error above" "$t/$ext" "$t/extensions/spend-ledger.ts" "--prune-suppressions"
# line FILE N: eslint names line N of FILE (stylish output: the file's path, then its findings' line:col rows).
line() { awk -v f="$t/$1" -v n="$2" '/^\//{in_f = ($0 == f)} in_f && $1 ~ ("^" n ":") && /no-explicit-any/{ok=1} END{exit !ok}' <<<"$out" \
  || fail "eslint did not name line $2 of $1"; }
line "$ext" $((n + 2)); line extensions/spend-ledger.ts "$m"
echo "check-ts test: ok (empty store names the fetch; clean passes; type error and lint violation named by file and line; baseline only shrinks)"
