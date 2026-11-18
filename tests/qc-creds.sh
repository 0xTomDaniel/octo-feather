#!/usr/bin/env bash
# gate: e2e
# Integration test for who gets the owner's model credentials in `just qc` (owner ruling 2026-10-29, #438; docs/adr/0022,
# the sandbox paragraph), through `just qc` with the testkit's herdr and the qc judge stand-in
# (testkit/pi_agent.py, FAKE_QC=creds) at the model boundary, no model: a scratch target declares one demo
# that tries to read Pi's auth.json and models.json; a second criterion has none and goes to the agent fallback.
# The demo's sandbox holds neither file (its proof says so, its stored record shows both unreadable, no
# secret in it); the fallback judge and the advisory classify run each find both per-run copies, so they reach the model.
# The OAuth warning shows once for a run where a Pi got copies, never for a run whose sandboxes copied nothing.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc-capture.sh. Its scenario `creds`
# in tests/gate/kit/qc_sections.py.
exec python3 "$(dirname "$0")/gate/kit/qc_sections.py" creds
