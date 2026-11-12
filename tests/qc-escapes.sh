#!/usr/bin/env bash
# The qc sandbox test's escapes section (#508; setup tests/lib/qc.sh): a failed proof check (live Herdr reachable,
# a Linear key re-entering the judge's env, a repo mask that cannot be set up) aborts before the judge; a judge
# trying each escape (#33) fails at every one, masks cannot be unmounted, leftovers are killed and agents counted,
# another repo's listing is recorded and refused, and no live record is written.
# Run by `just check`; offline and bounded, in its own namespace and throwaway HOME (tests/lib/qc.sh).
# Explicit public cancellation demo; normal gate case below remains unchanged.
if [[ "${1:-}" == --running-cancel ]]; then
  exec python3 "$(dirname "$0")/gate/kit/qc_sandbox.py" running_cancel "${2:-SIGINT}"
fi
# The observer owns this invocation before the harness enters its existing namespaces.
if [[ "$(uname -s)" != Darwin && -z "${QC_ESCAPE_SOCKET:-}" ]]; then
  exec python3 "$(dirname "$0")/gate/kit/testkit/qc_escape_observer.py" supervise bash "$0" "$@"
fi
# shellcheck source=tests/lib/qc.sh
source "$(dirname "$0")/lib/qc.sh"
# A failed proof check aborts before the judge: here raw herdr still reaches a live session.
FAKE_HERDR_LEAK=1 run 66 escape $st 5 acceptance-a
grep -q "FAIL live Herdr unreachable" <<< "$out" || fail "leaking Herdr not caught by the proof: $out"
[[ "$(jr '.get("stdout", "none")')" == none ]] || fail "judge started after a failed proof"

# remote#acceptance-linear-key-qc: a Linear key re-entering the judge's env (here a BASH_ENV that exports it
# again after the scrub) fails the proof, so the judge never starts; the plain run below proves it absent.
printf 'export LINEAR_API_KEY=SECRET-linear-leak\n' > "$t/bin/leak.env"
BASH_ENV="$t/bin/leak.env" run 66 escape $st 5 acceptance-a
grep -q "FAIL no tracker credential: LINEAR_API_KEY set 1 times" <<< "$out" || fail "leaking Linear key not caught by the proof: $out"
[[ "$(jr '.get("stdout", "none")')" == none ]] || fail "judge started with a Linear key in its env"

# A mask over another repo that cannot be set up (here a path to bind back on it is missing) aborts before the judge.
OCTO_FEATHER_QC_RO_BINDS="$HOME/src/sib/missing" run 66 escape $st 5 acceptance-a
grep -q "qc sandbox: FAIL bind back $HOME/src/sib/missing on the mask over $HOME/src/sib" <<< "$out" || fail "a failed repo mask not named: $out"
[[ "$(jr '.get("stdout", "none")')" == none ]] || fail "judge started after a failed repo mask"

# Every escape fails; leftovers killed, agents counted, credential copies gone, live records untouched.
run 0 escape $st 5 acceptance-a
judge="$(jr '["stdout"]')"
grep -E 'ESCAPE|MISSING|LINEAR KEY' <<< "$judge" && fail "sandbox escape: $judge"
grep -q "qc sandbox: ok   no tracker credential: LINEAR_API_KEY set 0 times" <<< "$out" || fail "no Linear key proof: $out"
grep -q "qc sandbox: ok   parent route unset: 0 of OCTO_FEATHER_PARENT/SESSION_ID/ROLE/SPEND_SPACE," <<< "$out" || fail "no route proof naming the spend space: $out"
grep -q "qc sandbox: ok   other repos hidden: 1 git repos under $HOME .*: src/sib; visible: kit under test $kit, worktree $PWD$" <<< "$out" \
  || fail "no other-repos proof naming the mask and what stays visible: $out"
jr '["sandbox"]["attempts"]' | grep -q "'kind': 'repo', 'attempt': True, 'refused': True, 'what': 'open $HOME/src/sib'" \
  || fail "the listing of another repo not recorded and refused: $(jr '["sandbox"]')"
grep -q "cleanup: agents started 1 (headless pi 1, Herdr panes 0)" <<< "$out" || fail "no agent count: $out"
[[ "$(jr '["sandbox"]["left_after_kill"]')" == 0 && "$(jr '["worktree_writes"]')" == "[]" ]] \
  || fail "cleanup record: $(jr '["sandbox"]')"
for p in "sleep 3012" "sleep 302921"; do
  jr '["sandbox"]["killed"]' | grep -q "$p" || fail "leftover '$p' not killed and counted: $(jr '["sandbox"]')"
done
python3 "$QC_ESCAPE_HELPER" check || fail "sandbox processes survived the run"
[[ ! -e "$HOME/qc-saved" ]] || fail "judge wrote into HOME"
ls -d /tmp/qc-escape-* 2>/dev/null && fail "judge's /tmp writes survived"
[[ ! -e "$live/lanes/escaped" && "$(cat "$live/lanes/archive/gh1.toml")" == ARCHIVED && "$(wc -l < "$live/director.handoffs.jsonl")" == 1 ]] \
  || fail "judge wrote live state"
[[ ! -e "$HOME/.config/herdr/sessions" ]] || fail "sandbox Herdr session left in the real config dir"
grep -q 'advisory model judgment (no gate reads it): shows, confidence ' <<< "$out" \
  || fail "classifier continuation did not answer through its extension seam: $out"
echo "qc-escapes: ok (proof abort, sandbox escapes, other repos masked (listing recorded and refused; a failed mask aborts), cleanup count, live state untouched; offline, runs bounded)"
