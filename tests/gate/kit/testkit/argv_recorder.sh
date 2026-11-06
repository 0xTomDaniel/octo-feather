#!/bin/sh
# A stand-in at the justfile recipe boundary only, put first by a scenario itself (testkit's
# docstring) as a kit command a recipe calls (octo-feather-shape, -spec-chat, -integrate, -start,
# -qc, -new-repo): it records the name it was run as, its physical cwd and its exact argv, each
# NUL-terminated, to $ARGV_LOG (one call: the file overwritten), and exits 0. It never answers as
# the command.
#
# Why a stand-in of a kit-owned command (an exception to never mocking what the kit owns, flagged
# to the director): the fact under test is the recipe's argv and cwd (#61: arguments and the
# invocation directory reach the command as data, nothing expanded), which no real command
# reports. Shell, not Python: one per recipe call, so the lightest start.
printf '%s\0' "${0##*/}" "$(pwd -P)" "$@" >"$ARGV_LOG"
