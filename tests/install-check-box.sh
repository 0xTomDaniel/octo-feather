#!/usr/bin/env bash
# gate: e2e
# Integration test for `just install-check`, its box facts section (#508; setup tests/gate/kit/testkit/install_check.py):
#   Box facts (#461), each probe a stub on PATH (uname -r, unshare, agent-browser doctor, ffmpeg) or a folder the test
#     makes (XDG_STATE_HOME, OCTO_FEATHER_KIT_INSTALL), never this box's values: kernel 6.12 ok, 6.1 TOO OLD naming the
#     upgrade; unshare -rm ok, refused FAILED naming its error; the state folder's lanes/ ok, absent MISSING naming
#     mkdir -p; the kit install clone on main ok (detached on main too), on another branch NOT ON MAIN naming git switch
#     main, no clone named with the fix; a detached worktree at main ok (the box's layout, also with
#     OCTO_FEATHER_KIT_INSTALL unset: the kit dir, octo-feather-lane's kit_install()), on a branch or off main NOT ON MAIN; agent-browser's Chrome outside the cache folder ok, under it
#     UNREADABLE IN THE QC SANDBOX, none MISSING, both naming agent-browser install; ffmpeg ok, absent OPTIONAL with
#     exit 0; the sharing MANUAL step always. herdr, gh, jq and git absent: MISSING with each install command, exit 1.
# Run by `just check`: its scenario `box` in tests/gate/kit/install_check.py, whose box is tests/gate/kit/testkit/install_check.py.
# Each install-check fact runs once per platform (#1200): on Linux tests/user-mise-ic-box.sh runs this item inside the
# user-mise fixture (USER_MISE_FIXTURE set), so here it skips (exit 77); on macOS, where user-mise skips, it runs here.
[[ "$(uname -s)" == Darwin || -n "${USER_MISE_FIXTURE:-}" ]] || { echo "install-check-box: skipped on Linux, tests/user-mise-ic-box.sh runs it inside the user-mise fixture"; exit 77; }
exec python3 "$(dirname "$0")/gate/kit/install_check.py" box
