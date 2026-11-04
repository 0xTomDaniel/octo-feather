#!/usr/bin/env bash
# Integration test for `just fast` (quality #acceptance-fast-affected; what the fast tier runs: quality #recipe-fast)
# and `just fast-map`, the coverage map it selects from, through the commands only. A throwaway git copy of the
# kit's tracked files without its tests/*.sh, holding four test items: a.sh and b.sh each run their own Python
# script, c.sh (`# gate: e2e`) runs a's, d.sh runs a bash script coverage cannot see. The static checks are cut
# to one with just's own command-line override (`just --set GATE_RECIPES check-dashes`); the map is built from
# the test items (`just fast-map -k test_script`). Each item appends its name to FAST_RAN, the record of what ran.
# Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; export FAST_RAN="$t.ran"; trap 'rm -rf "$t" "$FAST_RAN"' EXIT
(cd "$kit" && git ls-files -z | grep -zv '^tests/[^/]*\.sh$' | xargs -0 tar -cf - 2>/dev/null) | tar -xf - -C "$t"
g() { git -C "$t" -c user.name=t -c user.email=t@t "$@"; }
for n in a b; do
  printf '#!/usr/bin/env python3\nprint("%s ran")\n' "$n" > "$t/scripts/fixture-$n"
  printf '#!/usr/bin/env bash\nset -euo pipefail\necho %s >> "$FAST_RAN"\n"$(dirname "$0")/../scripts/fixture-%s"\n' "$n" "$n" > "$t/tests/$n.sh"
done
printf '#!/usr/bin/env bash\n# gate: e2e\nset -euo pipefail\necho c >> "$FAST_RAN"\n"$(dirname "$0")/../scripts/fixture-a"\n' > "$t/tests/c.sh"
printf '#!/usr/bin/env bash\necho d ran\n' > "$t/scripts/fixture-d"
printf '#!/usr/bin/env bash\nset -euo pipefail\necho d >> "$FAST_RAN"\n"$(dirname "$0")/../scripts/fixture-d"\n' > "$t/tests/d.sh"
chmod +x "$t"/scripts/fixture-? "$t"/tests/?.sh
g init -q; g add -A; g commit -qm base
# fast WANT: just fast, green, ran exactly the static check plus the items WANT (sorted, space-separated).
fast() { : > "$FAST_RAN"; set +e; out="$(cd "$t" && just --set GATE_RECIPES check-dashes fast 2>&1)"; rc=$?; set -e
  [[ "$rc" == 0 ]] || { echo "fast test: just fast exited $rc: $out" >&2; exit 1; }
  local got n; got="$(sort "$FAST_RAN" | paste -sd' ' -)"; n=$(( $(wc -w <<<"$1") + 1 ))
  [[ "$got" == "$1" && "$out" == *"=== $n passed in "* ]] || { echo "fast test: want the static check and items '$1', ran '$got': $out" >&2; exit 1; }; }
(cd "$t" && just fast-map -k test_script >/dev/null 2>&1) || { echo "fast test: just fast-map failed" >&2; (cd "$t" && just fast-map -k test_script) >&2; exit 1; }
# One script changed: the static check, the item whose recorded coverage reaches it, and the unmapped item, each
# named; the e2e item named skipped.
echo '# changed' >> "$t/scripts/fixture-a"
fast 'a d'
for want in "fast: check-dashes: static check" "fast: tests/a.sh: recorded coverage reaches scripts/fixture-a" \
  "fast: tests/d.sh: no recorded coverage in the map at" "fast: tests/c.sh: e2e"; do
  [[ "$out" == *"$want"* ]] || { echo "fast test: '$want' not in the output: $out" >&2; exit 1; }
done
# A listed path no coverage reaches (the list itself): every non-e2e item.
(cd "$t" && git checkout -q scripts/fixture-a); echo '# changed' >> "$t/shared-machinery.txt"
fast 'a b d'
[[ "$out" == *"fast: all 3 non-e2e test items: shared-machinery.txt on shared-machinery.txt"* ]] \
  || { echo "fast test: a listed unreached change not named as running every non-e2e item: $out" >&2; exit 1; }
echo "fast: ok (one-script change: static check, the covering item and the unmapped item, each named, e2e named skipped; listed unreached change: every non-e2e item)"
