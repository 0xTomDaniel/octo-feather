#!/usr/bin/env bash
# Integration test for `just check-ts` (#245), in a throwaway copy of the kit's tracked files:
#   empty pnpm store (a fresh store dir): fails naming the fetch command, never the network (--offline);
#   clean copy: passes;
#   one pnpm store (owner ruling #422): the kit's package.json and lockfile in a dir on another filesystem than the kit
#   (/dev/shm, a tmpfs, where the box has one; else TMPDIR) install offline from the kit's store;
#   a type error and a lint violation added to the extension: fails naming each file and line;
#   eslint's baseline only shrinks: one more `any` in extensions/spend-ledger.ts fails naming its line; alone, a fixed
#   violation leaves an unused suppression that fails naming --prune-suppressions.
# Offline: the copy installs from the box's pnpm store (CI's pnpm step fills it). Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; x=""; trap 'rm -rf "$t" ${x:+"$x"}' EXIT
# One pnpm store for the kit and its test copies (owner ruling #422): pnpm keeps a store per filesystem, so a copy
# under a /tmp on another one (a tmpfs) would install from an empty store; the kit's store, named, serves it offline.
npm_config_store_dir="$(cd "$kit" && pnpm store path)"; export npm_config_store_dir
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

fs="${TMPDIR:-/tmp}"; [[ ! -d /dev/shm || "$(stat -c %d /dev/shm)" == "$(stat -c %d "$kit")" ]] || fs=/dev/shm
x="$(mktemp -d "$fs/check-ts.XXXXXX")"; cp "$t/package.json" "$t/pnpm-lock.yaml" "$x/"
out="$(cd "$x" && pnpm install --offline --frozen-lockfile 2>&1)" || fail "a copy on $fs (another filesystem than the kit's) did not install offline from the kit's store $npm_config_store_dir"

# A type error and a lint violation in the extension, and one more `any` in baselined spend-ledger.ts: one run.
ext=extensions/resume-on-error.ts; n="$(wc -l <"$t/$ext")"
printf 'export const typeProbe: number = "x";\nexport function lintProbe(x: any): unknown { return x; }\n' >>"$t/$ext"
printf 'export function probe(x: any): unknown { return x; }\n' >>"$t/extensions/spend-ledger.ts"
m="$(wc -l <"$t/extensions/spend-ledger.ts")"
run; [[ "$rc" != 0 ]] || fail "a type error and lint violations passed"
has "$ext($((n + 1)),14): error TS2322" "check-ts: fix each tsc error above"
# named FILE LINE: eslint named LINE of FILE for no-explicit-any (the parse: tests/fixtures/check-ts/eslint_names.py).
named() { python3 "$kit/tests/fixtures/check-ts/eslint_names.py" "$t/$1" "$2" @typescript-eslint/no-explicit-any <<<"$out" || fail "eslint did not name line $2 of $1"; }
named "$ext" $((n + 2)); named extensions/spend-ledger.ts "$m"
(cd "$kit" && git show HEAD:"$ext") >"$t/$ext"; (cd "$kit" && git show HEAD:extensions/spend-ledger.ts) >"$t/extensions/spend-ledger.ts"

# Only an unused suppression (a fixed violation in the fixture): fails naming --prune-suppressions.
sed -i 's/    async execute() {/    execute() {/' "$t/tests/fixtures/spend-ledger/nested-tool.ts"
run; [[ "$rc" != 0 ]] || fail "an unused suppression passed"
has "There are suppressions left that do not occur anymore" "--prune-suppressions"
echo "check-ts test: ok (empty store names the fetch; clean passes; type error and lint violation named by file and line; baseline only shrinks)"
