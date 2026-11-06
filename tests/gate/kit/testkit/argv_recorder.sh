#!/bin/sh
# A stand-in at the justfile recipe boundary only, put first by a scenario itself (testkit's
# docstring) as a kit command a recipe calls whose real run would launch agents or external
# systems (octo-feather-shape: a Pi agent; -start: Herdr panes and agents; -qc: a model judge;
# -integrate: a lane's full gate): it records the name it was run as, its physical cwd and its
# exact argv, each NUL-terminated, to $ARGV_LOG (one call: the file overwritten), and exits 0. It
# reproduces no logic and never answers as the command.
#
# Owner ruling (owner, 2026-11-06, lane gh653 #674): argv_recorder is allowed as a NARROW
# exception: only where the fact under test is the argv a caller passes AND the real callee would
# launch agents or external systems; it records and exits, reproducing no logic. Not a class
# precedent: integration tests run our own code through its public surface with real internal
# paths, stand-ins only at seams to systems we do not control (model providers, GitHub, Herdr
# sessions, browsers, registries); real external systems are e2e, tagged, full tier only. A
# recipe whose callee is cheap and local runs the real command (tests/gate/kit/recipe_args.py:
# spec-chat and new-repo).
#
# Shell, not Python: one per recipe call, so the lightest start.
printf '%s\0' "${0##*/}" "$(pwd -P)" "$@" >"$ARGV_LOG"
