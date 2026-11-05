#!/usr/bin/env bash
# gate: e2e
# Integration test for the kit's Pi extension on a run stopped by a provider error (issue #152,
# docs/adr/0023), one gate item per case group (#509): tests/resume-on-error.sh and each tests/resume-on-error-*.sh;
# setup and the RPC pane driver: tests/lib/resume-on-error.sh. Cases here:
#   idle      mid-backoff Pi is idle (get_state isStreaming false), an abort is answered at once and
#             Pi stays usable; the resume still fires after the backoff (docs/adr/0023 Takeover)
# Never skips: without pi, or with pi at another version, it fails naming the install command.
# Run by `just check` (CI installs Pi at the pin first).
# shellcheck source=tests/lib/resume-on-error.sh
source "$(dirname "$0")/lib/resume-on-error.sh"

provider -1; pane idle 3,30
said_after 1; [[ ! -s "$t/said" ]] || fail "idle: parent was messaged: $(cat "$t/said")"
echo "case idle: ok ($detail)"
echo "resume-on-error-idle: ok (pi $v, empty HOME and environment, no provider credential)"
