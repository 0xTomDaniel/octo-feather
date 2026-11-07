#!/usr/bin/env bash
# Integration test for the kit's spend-ledger Pi extension (extensions/spend-ledger.ts, issue #187), one gate item
# per case group (#509; the fake provider, Pi environment and helpers: tests/lib/spend-ledger.sh). Cases here, on the
# ledger as tests/gate/kit/spend_ledger.py's cases agents to zero-priced leave it (seed 8):
#   qc  `just qc` (scripts/octo-feather-qc, its sandbox) in lane gh149's space, beside a classifier judge
#       call: the judge's message under gh149 and qc-judge, the lane's roles and total in `spend`'s lane and
#       purpose rows (spend#acceptance-spend-agents)
# Linux only (the sandbox needs unshare), as tests/qc.sh. Never skips on Linux: without pi, or with pi at another
# version, it fails naming the install command. Run by `just check`.
set -euo pipefail
[[ "$(uname -s)" != Darwin ]] || { echo "spend-ledger-qc: skipped, not on macOS (the qc sandbox needs Linux; CI runs it)"; exit 0; }
# shellcheck source=tests/lib/spend-ledger.sh
source "$(dirname "$0")/lib/spend-ledger.sh"
seed 8

# qc: the product judge's run in its sandbox (scripts/octo-feather-qc), in lane gh149's space, beside the lane's
# implementer spend seeded above and a classifier judge call: its one message (150 in, 10 out, $0.17) under gh149 and qc-judge
# (spec spend#acceptance-spend-agents; how: scripts/octo-feather-qc record_spend). Linux only (the sandbox needs unshare), as tests/qc.sh.
mk_qcrepo
printf '{"model":"openrouter/typesafe/jev-1.13","purpose":"judge","input_tokens":500,"output_tokens":40,"cost_usd":0.0001}\n' |
  env -i PATH="$PATH" HOME="$t/home" XDG_STATE_HOME="$t/state" HERDR_WORKSPACE_ID=w37 "$L" spend record
qc w37
[[ "$rc" == 0 && "$out" == *"PASS acceptance-a"* ]] || fail "qc: exit $rc: $out $(tail -20 "$t/err")"
calls 10
s="$(spend)"
row "$s" 'lane and purpose' 'gh149 qc-judge' 0.170000 1 0 150 10
row "$s" 'lane and purpose' 'gh149 implementer' 0.654000 6 1 707 63
row "$s" 'lane and purpose' 'gh149 judge' 0.000100 1 0 500 40
row "$s" lane gh149 0.824100 8 1 1357 113
echo "case qc: ok (the judge's call under gh149 and qc-judge, beside gh149 implementer and judge, lane gh149 \$0.8241)"

echo "spend-ledger-qc: ok (pi $v, empty HOME and environment, no provider credential)"
