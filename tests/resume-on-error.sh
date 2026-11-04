#!/usr/bin/env bash
# Integration test for the kit's Pi extension on a run stopped by a provider error (issue #152,
# docs/adr/0023), one gate item per case group (#509): tests/resume-on-error.sh and each tests/resume-on-error-*.sh;
# setup and the RPC pane driver: tests/lib/resume-on-error.sh. Cases here:
#   recovers  2 errors then an answer: resumed twice, finished, parent not messaged
#   normal    an answer: one request, no resume, nothing sent
#   headless  pi-role -p, errors throughout: exits non-zero promptly, no resume, nothing sent
# Never skips: without pi, or with pi at another version, it fails naming the install command.
# Run by `just check` (CI installs Pi at the pin first).
# shellcheck source=tests/lib/resume-on-error.sh
source "$(dirname "$0")/lib/resume-on-error.sh"

provider 2; pane recovers 0.3,0.6,0.9
said_after 1; [[ ! -s "$t/said" ]] || fail "recovers: parent was messaged: $(cat "$t/said")"
echo "case recovers: ok ($detail, parent not messaged)"

provider 0; pane normal 0.3,0.6,0.9
said_after 1; [[ ! -s "$t/said" ]] || fail "normal: parent was messaged: $(cat "$t/said")"
echo "case normal: ok ($detail, parent not messaged)"

provider -1; s=$SECONDS
set +e; (cd "$t/repo" && pienv "${role[@]}" -p "do the task" >/dev/null 2>&1); rc=$?; set -e
dt=$((SECONDS - s))
[[ "$rc" != 0 ]] || fail "headless: exit 0 on a provider that keeps failing"
[[ "$dt" -le 10 && "$(wc -l < "$t/requests")" == 1 ]] || fail "headless: ${dt}s, $(wc -l < "$t/requests") requests; want <= 10 s and 1 (no kit resume)"
said_after 1; [[ ! -s "$t/said" ]] || fail "headless: herdr-say ran: $(cat "$t/said")"
echo "case headless: ok (pi-role -p exit $rc in ${dt}s, 1 request, no resume, nothing sent)"
echo "resume-on-error: ok (pi $v, empty HOME and environment, no provider credential)"
