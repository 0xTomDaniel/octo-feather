#!/usr/bin/env bash
# gate: e2e
# Integration test for scripts/octo-feather-qc with the qc judge stand-in as `pi` and the testkit's `herdr`
# on PATH (no model call).
# One section of the qc sandbox test per gate item (#508): tests/qc.sh and each tests/qc-*.sh it names below.
# Proves: a same-family judge, a dirty tree, an unusable report (none, duplicate id, another head) and a judge
# that writes are refused, reports never overwrite, the pre-run proof printed, and the qc recipes pass arguments as
# data.
# The other sections: qc-namespace (a nested qc sandbox passes its proof, a judge's pane in its PID namespace), qc-judge (--no-sandbox, a killed run, built and planned in one status-only commit, the judge
# from agents/qc-judge.md), qc-escapes (proof failures, every escape fails), qc-copies and qc-oauth (no judge write
# persists: credential copies, Pi files, a removed .venv), qc-mise (mise in the sandbox), qc-vendored (the warm
# vendored-skill cache, new-repo's mise trust), qc-uv-cache (uv's cache an overlay).
# Run by `just check`; offline and bounded, in its own namespace and throwaway HOME (tests/gate/kit/testkit/qc_box.py):
# its scenario `qc` in tests/gate/kit/qc_sections.py.
exec python3 "$(dirname "$0")/gate/kit/qc_sections.py" qc
