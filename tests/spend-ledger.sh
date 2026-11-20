#!/usr/bin/env bash
# gate: e2e
# Integration test for the kit's spend-ledger Pi extension (extensions/spend-ledger.ts, issue #187,
# spec spend#writer-agent), one gate item per case group (#509): tests/spend-ledger.sh and each
# tests/spend-ledger-*.sh; the fake provider, Pi environment and helpers: tests/lib/spend-ledger.sh. Cases here:
#   agents      in lane gh149's space (HERDR_WORKSPACE_ID=w37) as implementer: a prompt that calls
#               a tool reporting nested usage (tests/fixtures/spend-ledger/nested-tool.ts), then an
#               answer: 3 calls (2 model messages, 1 tool result), shown under gh149 and
#               implementer with the model, tokens and Pi's cost (spend#acceptance-spend-agents)
#   role-unset  no OCTO_FEATHER_ROLE, no Herdr space: the extension's purpose fallback, no lane
#   pi-role     the implementer role launched through scripts/pi-role (which loads the extension) as
#               a pane launch does, JSON mode, in lane gh149's space, no OCTO_FEATHER_ROLE: its message under
#               gh149 and implementer (spend#writer-agent)
#   headless    pi-role -p (issue #189), no OCTO_FEATHER_ROLE: implementer in lane gh149's space records
#               under gh149 and implementer; code-reviewer in space w99, no lane's, under no lane and
#               code-reviewer (spend#rule-lane, spend#writer-agent)
#   zero-priced fake/free, its catalog rates all 0 (rule: extensions/spend-ledger.ts header, Cost):
#               `spend` shows it at $0, its call counted under unknown cost (spend#rule-cost)
#   unwritable  the ledger is a directory: same answer and exit 0, stderr names the unrecorded spend
#               (spend#rule-write-fails)
#   inherited   pi-role agents/implementer.md -p under a parent's inherited OCTO_FEATHER_ROLE=supervisor (a
#               supervisor's headless worker): under gh149 and implementer, no supervisor row (spend#writer-agent)
# Never skips: without pi, or with pi at another version, it fails naming the install command. Run by `just check`.
# shellcheck source=tests/lib/spend-ledger.sh
source "$(dirname "$0")/lib/spend-ledger.sh"

# agents: 2 model messages (0.1 + 0.04 = $0.14; 0.15 + 0.02 = $0.17) and the tool's $0.004.
run "use the tool, then answer" HERDR_WORKSPACE_ID=w37 OCTO_FEATHER_ROLE=implementer
[[ "$rc" == 0 && "$out" == fake-answer-ok ]] || fail "agents: exit $rc, answer '$out': $(cat "$t/err")"
calls 3
s="$(spend)"
row "$s" lane gh149 0.314000 3 0 257 33
row "$s" purpose implementer 0.314000 3 0 257 33
row "$s" model fake/fake 0.310000 2 0 250 30
row "$s" model tool/nested_work 0.004000 1 0 7 3
echo "case agents: ok (3 calls under gh149 and implementer: fake/fake \$0.31 250 in 30 out, tool/nested_work \$0.004 7 in 3 out)"

# role-unset: purpose agent, no lane.
run "answer"
[[ "$rc" == 0 && "$out" == fake-answer-ok ]] || fail "role-unset: exit $rc, answer '$out': $(cat "$t/err")"
calls 4
s="$(spend)"
row "$s" lane '(no lane)' 0.170000 1 0 150 10
row "$s" purpose agent 0.170000 1 0 150 10
echo "case role-unset: ok (purpose agent, no lane)"

# pi-role: no -e here; pi-role loads the extension. Not -p: a headless pi-role run drops the Herdr
# space (scripts/pi-role HEADLESS_UNSET), a pane launch keeps it. No OCTO_FEATHER_ROLE: the role file names the purpose.
set +e
out="$(cd "$t/repo" && pienv HERDR_WORKSPACE_ID=w37 "$kit/scripts/pi-role" "$kit/agents/implementer.md" --model fake/fake \
  --no-session --mode json "answer" 2>"$t/err")"; rc=$?
set -e
[[ "$rc" == 0 && "$out" == *fake-answer-ok* ]] || fail "pi-role: exit $rc: $(cat "$t/err")"
calls 5
s="$(spend)"
row "$s" lane gh149 0.484000 4 0 407 43
row "$s" purpose implementer 0.484000 4 0 407 43
row "$s" model fake/fake 0.650000 4 0 550 50
echo "case pi-role: ok (pi-role launch recorded under gh149 and implementer)"

# headless: pi-role -p drops HERDR_WORKSPACE_ID (#77); the spend still finds the lane. No OCTO_FEATHER_ROLE.
headless() { local space="$1" role="$2"; shift 2
  set +e
  out="$(cd "$t/repo" && pienv HERDR_WORKSPACE_ID="$space" "$@" "$kit/scripts/pi-role" "$kit/agents/$role.md" --model fake/fake \
    --no-session -p "answer" 2>"$t/err")"; rc=$?
  set -e
  [[ "$rc" == 0 && "$out" == fake-answer-ok ]] || fail "headless $role: exit $rc, answer '$out': $(cat "$t/err")"; }
headless w37 implementer
calls 6
s="$(spend)"
row "$s" lane gh149 0.654000 5 0 557 53
row "$s" purpose implementer 0.654000 5 0 557 53
headless w99 code-reviewer
calls 7
s="$(spend)"
row "$s" lane '(no lane)' 0.340000 2 0 300 20
row "$s" purpose code-reviewer 0.170000 1 0 150 10
row "$s" lane gh149 0.654000 5 0 557 53
echo "case headless: ok (implementer in w37 under gh149 and implementer; code-reviewer in w99 under no lane and code-reviewer)"

# zero-priced: fake/free answers with the same usage (150 in, 10 out); Pi reports $0, spend counts it as unknown cost.
model=fake/free run "answer" HERDR_WORKSPACE_ID=w37 OCTO_FEATHER_ROLE=implementer
[[ "$rc" == 0 && "$out" == fake-answer-ok ]] || fail "zero-priced: exit $rc, answer '$out': $(cat "$t/err")"
calls 8
s="$(spend)"
row "$s" model fake/free 0.000000 1 1 150 10
row "$s" lane gh149 0.654000 6 1 707 63
row "$s" model fake/fake 0.990000 6 0 850 70
echo "case zero-priced: ok (fake/free: \$0.000000, 1 call of unknown cost, 150 in 10 out; fake/fake priced as before)"

# unwritable: the ledger path is a directory.
mv "$ledger" "$t/ledger.bak"; mkdir "$ledger"
run "answer" HERDR_WORKSPACE_ID=w37 OCTO_FEATHER_ROLE=implementer
[[ "$rc" == 0 && "$out" == fake-answer-ok ]] || fail "unwritable: exit $rc, answer '$out' (want 0 and fake-answer-ok)"
want='octo-feather-lane spend record: spend unrecorded (1 call(s), $0.170000): cannot write'
for _ in $(seq 100); do grep -qF "$want" "$t/err" && break; sleep 0.1; done
grep -qF "$want" "$t/err" || fail "unwritable: stderr lacks '$want': $(cat "$t/err")"
echo "case unwritable: ok (exit 0, fake-answer-ok, stderr: $(grep -F "$want" "$t/err" | head -1))"
rm -r "$ledger"; mv "$t/ledger.bak" "$ledger"

# inherited: a supervisor's headless worker keeps the parent's OCTO_FEATHER_ROLE=supervisor; the role pi-role launches
# wins (spend#writer-agent). One more fake/fake answer (150 in, 10 out, $0.17) on gh149 implementer's 6 calls.
headless w37 implementer OCTO_FEATHER_ROLE=supervisor
calls 9
s="$(spend)"
row "$s" 'lane and purpose' 'gh149 implementer' 0.824000 7 1 857 73
! grep -q supervisor <<<"$s" || fail "inherited: a supervisor row: $s"
echo "case inherited: ok (pi-role implementer -p under inherited OCTO_FEATHER_ROLE=supervisor: under gh149 and implementer)"
echo "spend-ledger: ok (pi $v, empty HOME and environment, no provider credential)"
