#!/usr/bin/env bash
# gate: e2e
# Integration test for `just install-check` per target (spec remote#host-tools, #acceptance-install-linear), offline:
# the kit's justfile run in a target (`just -f KIT/justfile install-check`, or TARGET as the argument).
# One section of the `just install-check` test per gate item (#508): tests/install-check.sh and each tests/install-check-*.sh (mise, browser, box, models).
#   Linear target (tests/fixtures/install-check/linear), no linear on PATH: exit 1, linear listed missing with the
#     pinned v3.1.0 and the install path (release binary, or npx @schpet/linear-cli);
#   the testkit's Linear stand-in on PATH answering `linear --version` from a tape
#     (tests/fixtures/linear-install-check): at the pin, linear ok, exit 0; another release (3.0.0): listed with the
#     wanted v3.1.0, exit 1;
#   GitHub target (no config): linear never checked;
#   pi at the kit's pin (pi-version): its version line ok; pi reporting another release: WRONG VERSION naming
#     the pin and the npm install command, exit 1;
#   PATH (#422 item 10): linear is hidden alone (its dir mirrored minus it), so a mise sharing its dir stays ok.
#   Python (owner ruling #422, #261): the gate's Python at the kit's .python-version, found through uv: ok with venv and
#     pidfd_open; none installed: MISSING naming `uv python install --no-bin`, exit 1, and `just check` in a copy of the
#     kit refuses, naming it. The box python3 at 3.11 or later ok; a python3 reporting 3.10: WRONG VERSION, exit 1.
#     Uses the box's uv Python installs (UV_PYTHON_INSTALL_DIR kept while HOME is a fresh dir); installs nothing.
# Run by `just check`: its scenario `tracker` in tests/gate/kit/install_check.py, whose box is tests/gate/kit/testkit/install_check.py.
exec python3 "$(dirname "$0")/gate/kit/install_check.py" tracker
