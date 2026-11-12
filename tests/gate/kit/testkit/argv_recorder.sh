#!/bin/sh
# A stand-in at a caller's command boundary, put first by a scenario itself (testkit's docstring) as
# a command the caller runs, recording the name it was run as, its physical cwd and its exact argv,
# each NUL-terminated, then a newline, appended to $ARGV_LOG (one record per call, in call order),
# and exits 0. It reproduces no logic and never answers as the command. Two uses: (1) under the
# owner's narrow exception below, a kit command a justfile recipe calls whose real run would
# launch agents (octo-feather-shape: a Pi agent; -start: Herdr panes and agents; -qc: a model
# judge); (2) a plain seam stand-in for an external system the kit does not own, where the fact is
# the call: post-merge's refresh `uv sync` and `pnpm install`, which reach the package registries
# (tests/gate/kit/lane_post_merge.py), no exception needed.
#
# Owner ruling (owner, 2026-11-06, lane gh653 #674): argv_recorder is allowed as a NARROW
# exception: only where the fact under test is the argv a caller passes AND the real callee would
# launch agents or external systems; it records and exits, reproducing no logic. Not a class
# precedent: integration tests run our own code through its public surface with real internal
# paths, stand-ins only at seams to systems we do not control (model providers, GitHub, Herdr
# sessions, browsers, registries); real external systems are e2e, tagged, full tier only. A
# recipe whose callee is our own local code runs the real command (tests/gate/kit/recipe_args.py:
# spec-chat, integrate and new-repo).
#
# Shell, not Python: one per recipe call, so the lightest start.
printf '%s\0' "${0##*/}" "$(pwd -P)" "$@" >>"$ARGV_LOG"
echo >>"$ARGV_LOG"
