#!/usr/bin/env bash
# The qc sandbox test's credential-copies section (#508; setup tests/lib/qc.sh): no judge write persists (the
# worktree is an overlay on the run tmpfs): copies of Pi's credentials into ignored scratch/, .git, over 64 MiB,
# an intermediate refresh, token values alone, into HOME; the judge's rewrites of auth.json and models.json hit
# per-run copies, the box files byte-identical.
# Run by `just check`; offline and bounded, in its own namespace and throwaway HOME (tests/lib/qc.sh).
# shellcheck source=tests/lib/qc.sh
source "$(dirname "$0")/lib/qc.sh"
# Credential copies cannot survive anywhere: every judge write (ignored scratch/, .git, any size, a copy of an
# intermediate auth.json between two refreshes, token values alone) lives in the overlay and dies with the run.
copycase copycreds scratch/a .git/m
copycase bigcopy scratch/big
# The judge rewrites both Pi files: its per-run copies, discarded; the box files byte-identical; no OAuth warning.
copycase rewrite; piok rewrite
! grep -q "OAuth" <<< "$out" || fail "rewrite: OAuth warning without OAuth credentials: $out"
# A token refresh in place (intermediate copies anywhere discarded): discarded too, never written back.
copycase refresh scratch/oldauth .git/oldauth "$HOME/oldauth"; piok refresh
grep -q "qc sandbox: ok   writable persistent paths: none$" <<< "$out" || fail "proof must say writable persistent paths: none: $out"
copycase token scratch/tok .git/tok2; piok token
echo "qc-copies: ok (no persistent write: credential copies: >64 MiB, intermediate refresh, token only, HOME; auth.json and models.json: per-run copies rewritten, box files unchanged; offline, runs bounded)"
