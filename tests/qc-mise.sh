#!/usr/bin/env bash
# The qc sandbox test's mise section (#508; setup tests/lib/qc.sh): mise in the sandbox (#437): a bare just through
# mise's shim runs, a tool not installed fails at its shim with no install, a caller with no mise installs fails
# the proof.
# Run by `just check`; offline and bounded, in its own namespace and throwaway HOME (tests/lib/qc.sh).
# shellcheck source=tests/lib/qc.sh
source "$(dirname "$0")/lib/qc.sh"
# mise in the sandbox (#437, docs/adr/0022): a bare just call through mise's shim with HOME moved runs, the caller's
# first pi beating ~/.local/bin's; a tool not installed fails at its shim with no install; a caller whose HOME holds no
# mise installs (its dirs not pinned) fails the proof naming `mise install --locked`, the judge never started.
run 0 misepath $st 5 acceptance-a
judge="$(jr '["stdout"]')"
grep -q "MISEPATH exit 0" <<< "$judge" && grep -q "MISEPATH stub first" <<< "$judge" || fail "mise's just shim in the sandbox: $judge"
# The tools judged, each dir's own config only: the test repo pins none, the kit its mise.toml's (#493 AC3).
grep -qE "^qc sandbox: ok   mise offline, auto-install off; tools of the worktree and the kit installed in $MISE_DATA_DIR; judged, each from its own mise config only: [^;]+: none; $kit: ([^ ;]+@[^ ;]+ )*just@[0-9.]+( [^ ;]+@[^ ;]+)*$" <<< "$out" \
  || fail "no mise proof: $out"
run 0 misemissing $st 5 acceptance-a
judge="$(jr '["stdout"]')"
grep -E 'ESCAPE|MISSING' <<< "$judge" && fail "missing mise tool: $judge"
grep -qE "NOTINSTALLED exit [1-9]" <<< "$judge" || fail "a tool not installed ran through its shim: $judge"
# XDG_DATA_HOME too: mise falls back to XDG_DATA_HOME/mise, so a caller exporting it kept its installs (env-coupled, as #422 item 10).
(unset MISE_DATA_DIR MISE_CACHE_DIR MISE_CONFIG_DIR XDG_DATA_HOME; run 66 mixed $st 5 acceptance-a
  grep -q "qc sandbox: FAIL mise offline, auto-install off; tools of the worktree and the kit installed in $HOME/.local/share/mise (NOT installed: $kit: .*just@.*; the sandbox installs nothing: run outside it: .*octo-feather-mise-install $kit)" <<< "$out" \
    || fail "no mise installs: the proof did not fail naming mise install --locked: $out"
  [[ ! -e "$HOME/.local/share/mise/installs" && ! -e "$HOME/.cache/mise" ]] || fail "the run wrote mise installs or cache: $(find "$HOME/.local/share/mise" "$HOME/.cache/mise" 2>&1 | head)")
echo "qc-mise: ok (mise's just shim, a tool not installed, no installs refused; offline, runs bounded)"
