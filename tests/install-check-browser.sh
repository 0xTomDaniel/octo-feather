#!/usr/bin/env bash
# gate: e2e
# Integration test for `just install-check`, its browser section (#508; setup tests/gate/kit/testkit/install_check.py):
#   browser target (qc.toml [browser] playwright pin, spec remote#acceptance-install-browser), no browser folder:
#     browser MISSING naming the pin, the box folder and the install command, exit 1; a fake headless shell in
#     the folder at that pin: ok, exit 0; the folder under the cache folder the qc sandbox masks: refused, exit 1;
#     GitHub target (no qc.toml [browser]): no browser line. No browser is downloaded: the folder is faked.
#   agent-browser (spec remote#acceptance-install-agent-browser), a stub: at 0.40.0 ok; 0.39.4 WRONG VERSION; none on
#     PATH: MISSING naming 0.40.0 and the npm install, exit 1.
#   PATH (#422) in the kit itself: a stale node in a system dir before mise's shims only a NOTE, exit 0; one in a
#     dir ahead of mise's SHADOWED, exit 1; shims first ok (the kit's [browser] pin is the fake shell).
# Run by `just check`: its scenario `browser` in tests/gate/kit/install_check.py, whose box is tests/gate/kit/testkit/install_check.py.
exec python3 "$(dirname "$0")/gate/kit/install_check.py" browser
