#!/usr/bin/env bash
# Integration test for scripts/check-evals' fixture duplicate refusals, pool and --sources (rule:
# .agents/skills/eval-cases/references/schema.md, Fixtures; #990, #1007), driven as a command on a scratch EVALS_DIR holding only fixtures. Run by `just check`.
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
grep -qxF "check-evals: fixtures/mid/a.txt: field base: the same file base root supplies (fixtures/root/a.txt); delete it: the base supplies it (sources: check-evals --sources mid)" <<< "$out" \
  || fail "duplicate not refused as the rule words it: $out"
rm "$F/mid/a.txt"
# A chain: top's sub/keep.txt, root's (top/keep.txt is at another path).
cp -p "$F/root/sub/keep.txt" "$F/top/keep.txt"; mkdir -p "$F/top/sub"; cp -p "$F/root/sub/keep.txt" "$F/top/sub/keep.txt"
run 1 "$C" "$t/evals"
grep -qxF "check-evals: fixtures/top/sub/keep.txt: field base: the same file base mid supplies (fixtures/root/sub/keep.txt); delete it: the base supplies it (sources: check-evals --sources top)" <<< "$out" \
  || fail "chain duplicate not refused: $out"
grep -qF "fixtures/top/keep.txt" <<< "$out" && fail "a file at another path refused: $out"
# A chain: top's sub/swap.txt, mid's.
rm -r "$F/top/sub" "$F/top/keep.txt"; mkdir -p "$F/top/sub"; cp -p "$F/mid/sub/swap.txt" "$F/top/sub/swap.txt"
run 1 "$C" "$t/evals"
grep -qxF "check-evals: fixtures/top/sub/swap.txt: field base: the same file base mid supplies (fixtures/mid/sub/swap.txt); delete it: the base supplies it (sources: check-evals --sources top)" <<< "$out" \
  || fail "duplicate of the middle base not refused: $out"
# Pool, cross-fixture and pool duplicates, --sources (schema.md, Fixtures; seam: #1007 comment 6991399341).
rm -r "$F/top/sub"; mkdir -p "$F/.pool" "$F/sib" "$F/nest" "$F/whole/cfg"
echo pooled > "$F/.pool/shared.txt"; printf '#!/bin/sh\nexit 0\n' > "$F/.pool/hook"; chmod +x "$F/.pool/hook"
echo '{"pool": {"cfg/shared.txt": "shared.txt", "hook": "hook"}}' > "$F/whole/.eval-fixture.json"; echo w > "$F/whole/w.txt"
echo '{"base": "root", "pool": {"shared.txt": "shared.txt"}}' > "$F/sib/.eval-fixture.json"
echo '{"base": "sib"}' > "$F/nest/.eval-fixture.json"; echo n > "$F/nest/n.txt"
mkdir -p "$F/sib/sub"; cp -p "$F/mid/only.txt" "$F/sib/sub/only.txt"; echo mine > "$F/whole/only.txt"; chmod +x "$F/whole/only.txt"
run 0 "$C" "$t/evals"
run 0 "$C" --sources whole "$t/evals"
[[ "$out" == $'cfg/shared.txt fixtures/.pool/shared.txt listed by whole\nhook fixtures/.pool/hook listed by whole\nonly.txt fixtures/whole/only.txt\nw.txt fixtures/whole/w.txt' ]] \
  || fail "--sources whole: $out"
run 0 "$C" --sources nest "$t/evals"
[[ "$out" == $'a.txt fixtures/root/a.txt\nn.txt fixtures/nest/n.txt\nrun.sh fixtures/root/run.sh\nshared.txt fixtures/.pool/shared.txt listed by sib\nsub/keep.txt fixtures/root/sub/keep.txt\nsub/only.txt fixtures/sib/sub/only.txt\nsub/swap.txt fixtures/root/sub/swap.txt' ]] \
  || fail "--sources nest: $out"
run 0 "$C" --export "$t/pout" "$t/evals"
[[ -x "$t/pout/whole/hook" && "$(cat "$t/pout/nest/shared.txt")" == pooled && ! -e "$t/pout/.pool" ]] || fail "--export: pool not laid: $(ls -aR "$t/pout")"
run 2 "$C" --sources; run 1 "$C" --sources nosuch "$t/evals"; grep -qF "no fixture dir $F/nosuch" <<< "$out" || fail "--sources nosuch: $out"
# A cross-fixture duplicate (schema.md, Fixtures): sib holds mid's only.txt.
cp -p "$F/mid/only.txt" "$F/sib/only.txt"
run 1 "$C" "$t/evals"
grep -qxF "check-evals: fixtures/mid/only.txt: field pool: the same file fixture sib holds (fixtures/sib/only.txt); move it to fixtures/.pool/ and list it in both (sources: check-evals --sources mid)" <<< "$out" \
  && grep -qxF "check-evals: fixtures/sib/only.txt: field pool: the same file fixture mid holds (fixtures/mid/only.txt); move it to fixtures/.pool/ and list it in both (sources: check-evals --sources sib)" <<< "$out" \
  || fail "cross-fixture duplicate not refused as the rule words it: $out"
[[ "$(grep -c 'check-evals: fixtures/' <<< "$out")" == 2 ]] || fail "a passing file refused: $out"
rm "$F/sib/only.txt"
# A pool duplicate (schema.md, Fixtures).
mkdir -p "$F/whole/deep"; cp -p "$F/.pool/shared.txt" "$F/whole/deep/x.txt"
run 1 "$C" "$t/evals"
grep -qxF "check-evals: fixtures/whole/deep/x.txt: field pool: the same file as pool file shared.txt (fixtures/.pool/shared.txt); delete it and list it in pool (sources: check-evals --sources whole)" <<< "$out" \
  || fail "pool duplicate not refused: $out"
rm -r "$F/whole/deep"
echo a > "$F/.pool/a"   # root's a.txt
for p in '{"x": "nosuch"}' '{"w.txt": "shared.txt"}' '{"../x": "shared.txt"}' '["hook"]' '{"a.txt": "a"}'; do
  echo "{\"base\": \"root\", \"pool\": $p}" > "$F/whole/.eval-fixture.json"
  run 1 "$C" "$t/evals"; grep -qF "check-evals: fixtures/whole/.eval-fixture.json: field pool: " <<< "$out" || fail "pool $p not refused: $out"
done
rm -r "$F/.pool" "$F/sib" "$F/nest" "$F/whole"
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
echo "check-evals-base-dup: ok (base duplicates refused, through a chain; pool laid, --sources names each file's source; cross-fixture and pool duplicates and malformed pools refused; differing files and new paths pass; --export writes every tree, refuses a non-empty DIR and a refused base)"
