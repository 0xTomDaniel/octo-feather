#!/usr/bin/env bash
# Integration test for scripts/check-evals' base duplicate refusal (rule: .agents/skills/eval-cases/references/schema.md,
# Fixtures, #990), driven as a command on a scratch EVALS_DIR holding only fixtures. Run by `just check`.
set -euo pipefail
C="$(cd "$(dirname "$0")/.." && pwd -P)/scripts/check-evals"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
F="$t/evals/fixtures"
fail() { echo "check-evals-base-dup: $*" >&2; exit 1; }
run() { local want="$1"; shift; set +e; out="$("$@" 2>&1)"; local rc=$?; set -e; [[ "$rc" == "$want" ]] || fail "exit $rc, want $want: $out"; }
# root whole; mid over root; top over mid (a chain).
mkdir -p "$F/root/sub" "$F/mid/sub" "$F/top"
echo a > "$F/root/a.txt"; echo keep > "$F/root/sub/keep.txt"; echo old > "$F/root/sub/swap.txt"
printf '#!/bin/sh\n' > "$F/root/run.sh"; chmod +x "$F/root/run.sh"
echo '{"base": "root"}' > "$F/mid/.eval-fixture.json"; echo '{"base": "mid"}' > "$F/top/.eval-fixture.json"
# Passes: files that differ from the base's (bytes, exec bit), one at a path the base lacks.
echo new > "$F/mid/sub/swap.txt"; printf '#!/bin/sh\n' > "$F/mid/run.sh"; echo mine > "$F/mid/only.txt"; echo top > "$F/top/top.txt"
run 0 "$C" "$t/evals"
# A base duplicate (schema.md, Fixtures): mid's a.txt.
cp -p "$F/root/a.txt" "$F/mid/a.txt"
run 1 "$C" "$t/evals"
grep -qxF "check-evals: fixtures/mid/a.txt: field base: the same file base root supplies (fixtures/root/a.txt); delete it: the base supplies it" <<< "$out" \
  || fail "duplicate not refused as the rule words it: $out"
rm "$F/mid/a.txt"
# A chain: top's sub/keep.txt, root's (top/keep.txt is at another path).
cp -p "$F/root/sub/keep.txt" "$F/top/keep.txt"; mkdir -p "$F/top/sub"; cp -p "$F/root/sub/keep.txt" "$F/top/sub/keep.txt"
run 1 "$C" "$t/evals"
grep -qxF "check-evals: fixtures/top/sub/keep.txt: field base: the same file base mid supplies (fixtures/root/sub/keep.txt); delete it: the base supplies it" <<< "$out" \
  || fail "chain duplicate not refused: $out"
grep -qF "fixtures/top/keep.txt" <<< "$out" && fail "a file at another path refused: $out"
# A chain: top's sub/swap.txt, mid's.
rm -r "$F/top/sub" "$F/top/keep.txt"; mkdir -p "$F/top/sub"; cp -p "$F/mid/sub/swap.txt" "$F/top/sub/swap.txt"
run 1 "$C" "$t/evals"
grep -qxF "check-evals: fixtures/top/sub/swap.txt: field base: the same file base mid supplies (fixtures/mid/sub/swap.txt); delete it: the base supplies it" <<< "$out" \
  || fail "duplicate of the middle base not refused: $out"
# --export (seam: #990 comment 6990555891): every fixture's tree, a non-empty DIR, a refused base.
run 0 "$C" --export "$t/out" "$t/evals"
[[ "$(cat "$t/out/top/a.txt" "$t/out/top/sub/swap.txt" "$t/out/top/sub/keep.txt" "$t/out/top/top.txt")" == $'a\nnew\nkeep\ntop' ]] \
  || fail "--export: top is not root, mid and top laid over each other: $(ls -R "$t/out/top")"
[[ -x "$t/out/root/run.sh" && ! -x "$t/out/top/run.sh" && ! -e "$t/out/top/.eval-fixture.json" ]] || fail "--export: exec bit or base file wrong"
[[ "$(cat "$t/out/mid/only.txt" "$t/out/root/sub/swap.txt")" == $'mine\nold' ]] || fail "--export: mid or root wrong: $(ls -R "$t/out")"
run 2 "$C" --export "$t/out" "$t/evals"; grep -qF "exists and is not an empty dir" <<< "$out" || fail "--export over a non-empty dir: $out"
echo '{"base": "nosuch"}' > "$F/mid/.eval-fixture.json"
run 1 "$C" --export "$t/out2" "$t/evals"
grep -qF "check-evals: fixtures/mid/.eval-fixture.json: field base: no fixture dir $F/nosuch" <<< "$out" || fail "--export: refused base not named: $out"
echo "check-evals-base-dup: ok (base duplicates refused, through a chain; differing files and new paths pass; --export writes every tree, refuses a non-empty DIR and a refused base)"
