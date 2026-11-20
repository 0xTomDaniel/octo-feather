#!/usr/bin/env bash
# gate: e2e
# Integration test for `just install-check`, its review service and models section (#508; setup
# tests/gate/kit/testkit/install_check.py):
#   Review service (#462): systemctl a stub: active and enabled ok; inactive, failed or no systemctl named with Spec
#     Chat's installer --public <vm>.exe.xyz --service, exit 1; a models MANUAL line names just install-check-models
#     and no install-check run calls pi -p. just install-check-models: the stub tests/fixtures/install-check/pi, asserted
#     first on PATH, plays the proxy: right keys ok per role model with its roles and for the judgment model (a classify
#     call); a key with trailing terminal characters REJECTED; a proxy not answering UNREACHABLE; a judgment model Pi does
#     not list FAILED; the key never printed nor on pi's command line.
# Run by `just check`: its scenario `models` in tests/gate/kit/install_check.py, whose box is tests/gate/kit/testkit/install_check.py.
exec python3 "$(dirname "$0")/gate/kit/install_check.py" models
