#!/usr/bin/env bash
# gate: e2e
# The qc sandbox test's uv-cache section (#508; setup tests/gate/kit/testkit/qc_box.py; the bind: scripts/octo-feather-qc-sandbox,
# step 5): uv's cache, as `uv cache dir` names it, is an overlay in the sandbox. A judge there runs an offline
# `uv sync --locked` of a package held only in that cache (its find-links wheel removed after the host's sync) and
# writes a file into the cache: both succeed, the proof names the overlay and its upper dir, and afterwards the host's
# cache is byte-identical (a sha256 manifest of every entry) and that upper dir is gone.
# Run by `just check`; offline and bounded, in its own namespace and throwaway HOME (tests/gate/kit/testkit/qc_box.py):
# its scenario `uv_cache` in tests/gate/kit/qc_sections.py.
exec python3 "$(dirname "$0")/gate/kit/qc_sections.py" uv_cache
