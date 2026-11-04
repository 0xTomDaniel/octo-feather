#!/usr/bin/env bash
# gate: e2e
# Integration test for the kit's Pi extension on a run stopped by a provider error (issue #152,
# docs/adr/0023), one gate item per case group (#509): tests/resume-on-error.sh and each tests/resume-on-error-*.sh;
# setup and the RPC pane driver: tests/lib/resume-on-error.sh. Cases here:
#   takeover  a prompt sent mid-backoff runs at once; no scheduled resume follows, nothing sent
# Never skips: without pi, or with pi at another version, it fails naming the install command.
# Run by `just check` (CI installs Pi at the pin first).
# shellcheck source=tests/lib/resume-on-error.sh
source "$(dirname "$0")/lib/resume-on-error.sh"

provider 1; pane takeover 3
said_after 1; [[ ! -s "$t/said" ]] || fail "takeover: parent was messaged: $(cat "$t/said")"
echo "case takeover: ok ($detail, parent not messaged)"
echo "resume-on-error-takeover: ok (pi $v, empty HOME and environment, no provider credential)"
