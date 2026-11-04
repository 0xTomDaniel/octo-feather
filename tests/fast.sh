#!/usr/bin/env bash
# Integration test for `just fast` (quality #acceptance-fast-affected; what the fast tier runs: quality #recipe-fast)
# and `just fast-map`, the coverage map it selects from, and `just fast-list`, its dry run, through the commands
# only. A throwaway git copy of the kit's tracked files without its tests/*.sh, holding five test items: a.sh and
# b.sh each run their own Python script, c.sh (`# gate: e2e`) runs a's, d.sh runs a bash script coverage cannot
# see, e.sh runs b's and fails while the file $FAST_RAN.fail exists (the mapping run). The static checks are cut
# to one with just's own command-line override (`just --set GATE_RECIPES check-dashes`); the map is built from
# the test items (`just fast-map -k test_script`). Each item appends its name to FAST_RAN, the record of what ran.
# Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; export FAST_RAN="$t.ran"; trap 'rm -rf "$t" "$FAST_RAN" "$FAST_RAN.fail"' EXIT
(cd "$kit" && git ls-files -z | grep -zv '^tests/[^/]*\.sh$' | xargs -0 tar -cf - 2>/dev/null) | tar -xf - -C "$t"
g() { git -C "$t" -c user.name=t -c user.email=t@t "$@"; }
for n in a b; do
  printf '#!/usr/bin/env python3\nprint("%s ran")\n' "$n" > "$t/scripts/fixture-$n"
  printf '#!/usr/bin/env bash\nset -euo pipefail\necho %s >> "$FAST_RAN"\n"$(dirname "$0")/../scripts/fixture-%s"\n' "$n" "$n" > "$t/tests/$n.sh"
done
printf '#!/usr/bin/env bash\n# gate: e2e\nset -euo pipefail\necho c >> "$FAST_RAN"\n"$(dirname "$0")/../scripts/fixture-a"\n' > "$t/tests/c.sh"
printf '#!/usr/bin/env bash\necho d ran\n' > "$t/scripts/fixture-d"
printf '#!/usr/bin/env bash\nset -euo pipefail\necho d >> "$FAST_RAN"\n"$(dirname "$0")/../scripts/fixture-d"\n' > "$t/tests/d.sh"
printf '#!/usr/bin/env bash\nset -euo pipefail\necho e >> "$FAST_RAN"\n"$(dirname "$0")/../scripts/fixture-b"\n[[ ! -e "$FAST_RAN.fail" ]]\n' > "$t/tests/e.sh"
chmod +x "$t"/scripts/fixture-? "$t"/tests/?.sh
g init -q; g add -A; g commit -qm base
# fast WANT: just fast, green, ran exactly the static check plus the items WANT (sorted, space-separated).
fast() { : > "$FAST_RAN"; set +e; out="$(cd "$t" && just --set GATE_RECIPES check-dashes fast 2>&1)"; rc=$?; set -e
  [[ "$rc" == 0 ]] || { echo "fast test: just fast exited $rc: $out" >&2; exit 1; }
  local got n; got="$(sort "$FAST_RAN" | paste -sd' ' -)"; n=$(( $(wc -w <<<"$1") + 1 ))
  [[ "$got" == "$1" && "$out" == *"=== $n passed in "* ]] || { echo "fast test: want the static check and items '$1', ran '$got': $out" >&2; exit 1; }; }
# The mapping run with e.sh failing: red, yet the map is written from the items that passed, e.sh left out.
touch "$FAST_RAN.fail"; set +e; map="$(cd "$t" && just fast-map -k test_script 2>&1)"; rc=$?; set -e; rm "$FAST_RAN.fail"
[[ "$rc" != 0 && "$map" == *"fast-map: 3 test items mapped at"* && "$map" == *"fast-map: tests/e.sh did not pass: left out of the map"* ]] \
  || { echo "fast test: a mapping run with tests/e.sh failing: want it red, 3 items mapped and e.sh named left out (exit $rc): $map" >&2; exit 1; }
# Nothing changed: only the items with no recorded coverage, the unmapped one and the one that did not pass.
fast 'd e'
[[ "$out" == *"fast: tests/e.sh: did not pass the mapping run at"* ]] || { echo "fast test: e.sh not named as not passed: $out" >&2; exit 1; }
# One script changed: the static check, the item whose recorded coverage reaches it, and the unmapped items, each
# named; the e2e item named skipped. The dry run names the same and runs nothing.
echo '# changed' >> "$t/scripts/fixture-a"
: > "$FAST_RAN"; list="$(cd "$t" && just --set GATE_RECIPES check-dashes fast-list 2>&1)"
[[ ! -s "$FAST_RAN" && "$list" == *"fast: selected 4 of 6 gate items (1 static, 3 of 5 test items)"* ]] \
  || { echo "fast test: just fast-list ran an item or did not count 4 of 6 selected: $list" >&2; exit 1; }
fast 'a d e'
for want in "fast: check-dashes: static check" "fast: tests/a.sh: recorded coverage reaches scripts/fixture-a" \
  "fast: tests/d.sh: no recorded coverage in the map at" "fast: tests/c.sh: e2e" \
  "fast: tests/e.sh: did not pass the mapping run at" "fast: selected 4 of 6 gate items"; do
  [[ "$out" == *"$want"* && "$list" == *"$want"* ]] || { echo "fast test: '$want' not in the just fast and just fast-list output: $out --- $list" >&2; exit 1; }
done
# A listed path no coverage reaches (the list itself): every non-e2e item.
(cd "$t" && git checkout -q scripts/fixture-a); echo '# changed' >> "$t/shared-machinery.txt"
fast 'a b d e'
[[ "$out" == *"fast: all 4 non-e2e test items: shared-machinery.txt on shared-machinery.txt"* ]] \
  || { echo "fast test: a listed unreached change not named as running every non-e2e item: $out" >&2; exit 1; }
echo "fast: ok (a mapping run with one failing item writes the map without it, selected on every diff; one-script change: static check, the covering item and the unmapped items, each named, e2e named skipped, the dry run the same and running nothing; listed unreached change: every non-e2e item)"
