#!/usr/bin/env bash
# gate: e2e
# Integration test for the kit's spend-ledger Pi extension (extensions/spend-ledger.ts, issue #187), one gate item
# per case group (#509; the fake provider, Pi environment and helpers: tests/lib/spend-ledger.sh). Case here:
#   qc-unwritable the ledger is a directory: `just qc` (scripts/octo-feather-qc, its sandbox) in lane gh149's space
#                 gives the same verdict and exit 0, stderr names the unrecorded spend (spend#rule-write-fails)
# Linux only (the sandbox needs unshare), as tests/qc.sh. Never skips on Linux: without pi, or with pi at another
# version, it fails naming the install command. Run by `just check`.
set -euo pipefail
[[ "$(uname -s)" != Darwin ]] || { echo "spend-ledger-qc-unwritable: skipped, not on macOS (the qc sandbox needs Linux; CI runs it)"; exit 0; }
# shellcheck source=tests/lib/spend-ledger.sh
source "$(dirname "$0")/lib/spend-ledger.sh"
mk_qcrepo

mkdir "$ledger"
want='octo-feather-lane spend record: spend unrecorded (1 call(s), $0.170000): cannot write'
# qc-unwritable: the same qc run with the ledger unwritable (its path a directory): the same verdict and exit, stderr names the unrecorded call
# (spec spend#rule-write-fails).
qc w37
[[ "$rc" == 0 && "$out" == *"PASS acceptance-a"* ]] || fail "qc-unwritable: exit $rc (want 0 and PASS acceptance-a): $out"
grep -qF "$want" "$t/err" || fail "qc-unwritable: stderr lacks '$want': $(cat "$t/err")"
echo "case qc-unwritable: ok (exit 0, PASS acceptance-a, stderr: $(grep -F "$want" "$t/err" | head -1))"
echo "spend-ledger-qc-unwritable: ok (pi $v, empty HOME and environment, no provider credential)"
