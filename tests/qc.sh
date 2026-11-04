#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qc with a fake `pi` and a fake `herdr` on PATH (no model call).
# One section of the qc sandbox test per gate item (#508): tests/qc.sh and each tests/qc-*.sh it names below.
# Proves: a same-family judge, a dirty tree, an unusable report (none, duplicate id, another head) and a judge
# that writes are refused, reports never overwrite, the pre-run proof printed, a nested qc sandbox passes its
# proof, a pane the judge spawns runs in its PID namespace and dies with it (the fake herdr; the box's real herdr
# only with QC_TEST_HERDR=real, `just qc-real-herdr`; the test prints which), and the qc recipes pass arguments as
# data.
# The other sections: qc-judge (--no-sandbox, a killed run, built and planned in one status-only commit, the judge
# from agents/qc-judge.md), qc-escapes (proof failures, every escape fails), qc-copies and qc-oauth (no judge write
# persists: credential copies, Pi files, a removed .venv), qc-mise (mise in the sandbox), qc-vendored (the warm
# vendored-skill cache, new-repo's mise trust).
# Run by `just check`; offline and bounded, in its own namespace and throwaway HOME (tests/lib/qc.sh).
# shellcheck source=tests/lib/qc.sh
source "$(dirname "$0")/lib/qc.sh"
OCTO_FEATHER_QC_MODEL=anthropic/claude-opus-5-5 run 64 mixed $st 5 acceptance-a acceptance-b   # judge of the implementer's family
echo x > dirty; run 65 mixed $st 5 acceptance-a; rm dirty                                      # dirty worktree
before="$(git rev-parse HEAD)"
run 3 garbage $st 5 acceptance-a acceptance-b                                                   # no json report
run 3 writes $st 5 acceptance-a                                                                 # judge wrote a non-ignored file
grep -q "new judge-was-here" <<< "$out" && ! grep -q scratch/fine <<< "$out" || fail "non-ignored write not listed alone: $out"
run 3 tracked $st 5 acceptance-a                                                                # judge changed and deleted tracked files
grep -q "changed .gitignore; deleted docs/specs/demo.spec.html" <<< "$out" || fail "tracked writes not listed: $out"
run 3 opaque $st 5 acceptance-a                                                                 # judge replaced a tracked dir (opaque upper dir)
grep -q "deleted docs/specs/demo.spec.html; deleted docs/specs/demo.status.json; new docs/specs/other.html" <<< "$out" || fail "opaque dir writes not listed: $out"
[[ "$(git rev-parse HEAD)" == "$before" && -z "$(git status --porcelain --ignored)" ]] || fail "refused run changed the real worktree"
[[ "$(find "$t/reports" -name "$before-*.json" | wc -l)" == 4 ]] || fail "four runs at one head must leave four reports"
grep -q "qc sandbox: ok   live Herdr unreachable" <<< "$out" || fail "no pre-run proof printed: $out"
grep -q "qc sandbox: ok   worktree $PWD is an overlay" <<< "$out" && grep -q "qc sandbox: ok   writable persistent paths: none" <<< "$out" \
  || fail "no overlay / persistent-writable proof: $out"
grep -q "qc sandbox: ok   vendored-skill cache: none on the box, nothing bound" <<< "$out" || fail "absent cache: want no bind, no failure: $out"
# issue-lifecycle#acceptance-qc-interim, #acceptance-one-head (#121 D19 D20): a duplicate id, another head.
run 3 dup $st 5 acceptance-a acceptance-b                                                       # acceptance-a judged twice
grep -q "judged more than once: acceptance-a" <<< "$out" || fail "duplicate id not named: $out"
run 3 head $st 5 acceptance-a                                                                   # report for another head
grep -q "report head '0000000000000000000000000000000000000000' is not the judged head $before" <<< "$out" || fail "wrong head not named: $out"
[[ "$(git rev-parse HEAD)" == "$before" && -z "$(git status --porcelain)" ]] || fail "unusable report changed the status file"

# A qc sandbox nested in the judge's (outer /proc submounts covered by its own /proc) passes its proof.
run 0 nested $st 5 acceptance-a
judge="$(jr '["stdout"]')"
grep -E 'ESCAPE|MISSING' <<< "$judge" && fail "nested qc: $judge"
grep -q "NESTED exit 3" <<< "$judge" || fail "nested qc: want the inner judge to run (exit 3, unusable report): $judge"

# A pane the judge spawns through the sandbox herdr runs in the judge's PID namespace (the sandbox
# server started inside it), sees no live Herdr socket and no creds, and dies with the run.
pp="$t/bin:$t/fakeherdr:$kit/scripts:$PATH"
if [[ "$mode" == real ]]; then   # a real "live" Herdr session under the throwaway HOME
  pp="$base"
  setsid sh -c 'echo $$ > "$1"; exec "$2" --session qclive server' _ "$t/pids/qclive" "$real" < /dev/null > /dev/null 2>&1 &
  for _ in $(seq 50); do "$real" --session qclive workspace list > /dev/null 2>&1 && break; sleep 0.2; done
  "$real" --session qclive workspace create --label QCLIVE --cwd "$t" --no-focus > /dev/null || fail "real herdr: live test session did not start"
fi
PATH="$pp" run 0 pane $st 5 acceptance-a
judge="$(jr '["stdout"]')"
grep -E 'ESCAPE|MISSING' <<< "$judge" && fail "sandbox pane escape ($mode herdr): $judge"
grep -q "PANE done" <<< "$judge" || fail "pane never ran ($mode herdr): $judge"
[[ "$(grep 'judge pidns' <<< "$judge" | cut -d' ' -f3)" == "$(grep 'pane pidns' <<< "$judge" | cut -d' ' -f3)" \
  && "$(grep 'pane pidns' <<< "$judge" | cut -d' ' -f3)" != "$(readlink /proc/self/ns/pid)" ]] \
  || fail "pane not in the judge's PID namespace ($mode herdr): $judge"
[[ "$(jr '["sandbox"]["herdr_panes"]')" == 1 ]] || fail "pane not counted ($mode herdr): $(jr '["sandbox"]')"
sleep 0.3; ! pgrep -fx "sleep 303031$tok" > /dev/null || fail "judge's pane survived the run ($mode herdr)"
if [[ "$mode" == real ]]; then
  "$real" --session qclive workspace list > /dev/null 2>&1 || fail "the run hurt the live Herdr session"
  [[ "$(ls "$HOME/.config/herdr/sessions")" == qclive ]] || fail "sandbox session left: $(ls "$HOME/.config/herdr/sessions")"
fi
[[ ! -e scratch ]] || fail "pane run's scratch survived"

# The qc recipes pass arguments as data, never as shell source.
for jf in "$kit/justfile" "$kit/templates/python/justfile" "$kit/templates/typescript/justfile"; do
  set +e; o="$(bounded just --justfile "$jf" --working-directory "$t/repo" qc "$st" 5 'acceptance-a$(touch pwned)' 'x;touch pwned2' 2>&1)"; rc=$?; set -e; hung "$rc" "$jf qc" "$o"
  [[ "$rc" != 0 && ! -e pwned && ! -e pwned2 && ! -e "$kit/pwned" ]] || fail "$jf qc ran its arguments as shell (exit $rc): $o"
  grep -q 'not in docs/specs/demo.status.json: acceptance-a$(touch pwned) x;touch pwned2' <<< "$o" || fail "$jf qc mangled its arguments: $o"
done
echo "qc: ok (same family, dirty, unusable report, judge wrote (non-ignored, tracked), unique reports, nested sandbox, judge pane in the sandbox ($mode herdr), recipe args as data; offline, runs bounded)"
