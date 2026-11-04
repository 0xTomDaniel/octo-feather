#!/usr/bin/env bash
# Integration test for the kit's Pi extension on a run stopped by a provider error (issue #152,
# docs/adr/0023), one gate item per case group (#509): tests/resume-on-error.sh and each tests/resume-on-error-*.sh;
# setup and the RPC pane driver: tests/lib/resume-on-error.sh. Cases here:
#   down      errors throughout: 3 resume rounds then stop; exactly one --parent line naming
#             agent, pane, error and "stopped"
# Never skips: without pi, or with pi at another version, it fails naming the install command.
# Run by `just check` (CI installs Pi at the pin first).
# shellcheck source=tests/lib/resume-on-error.sh
source "$(dirname "$0")/lib/resume-on-error.sh"

provider -1; pane down 0.3,0.6,0.9
said_after 3; [[ -s "$t/said" ]] || fail "down: parent got no message"
sleep 0.5
[[ "$(wc -l < "$t/said")" == 1 ]] || fail "down: want exactly one message, got: $(cat "$t/said")"
line="$(cat "$t/said")"
for w in "--parent " implementer fake:p9 "fake upstream overloaded" stopped; do
  [[ "$line" == *"$w"* ]] || fail "down: message lacks '$w': $line"
done
echo "case down: ok ($detail; one parent line: $line)"
echo "resume-on-error-down: ok (pi $v, empty HOME and environment, no provider credential)"
