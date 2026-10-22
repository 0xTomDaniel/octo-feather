#!/usr/bin/env bash
# Integration test for scripts/check-owned-rules in a throwaway repo, planting
# the real restatements lane #8 logged as contradictory-merge-authority
# (github skill before 9f46d9b, implement-spec before 278118c) and the
# lane-branch default of finding 22. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
C="$kit/scripts/check-owned-rules"
g() { git -C "$t" -c user.name=t -c user.email=t@t "$@"; }
git init -q "$t"; mkdir -p "$t/docs/specs" "$t/agents" "$t/.skillfile/patches/skills/x" "$t/evidence" "$t/scripts" "$t/.agents/skills/herdr-comms"
# The long-wait owner states it; the role pointer passes (issue #29).
echo 'Never hold your turn in a shell sleep or blocking wait over ~60 s.' > "$t/.agents/skills/herdr-comms/SKILL.md"
echo '- Long jobs (`just qc`, CI, workers): wait only as herdr-comms (Send a message) says.' > "$t/agents/wait.md"
# Ordinary process waits are legitimate (review of a4d8861: owned-rule-false-positive).
printf '#!/bin/sh\n# Use a blocking wait to reap the child process.\nwait "$pid"\n' > "$t/scripts/wait-child"
echo 'Reap it with `wait $pid`, or `sleep 5` before a retry.' > "$t/agents/shortwait.md"
printf '%s\n' '# A blocking wait over 30 seconds triggers the subprocess timeout.' 'printf "done rc=$?\\n"' > "$t/scripts/timeout"
# The owner may state the rule; a pointer and a dated record pass.
echo '<p data-anchor="gates-merge">After the owner says merge, ... a new merge ask.</p>' > "$t/docs/specs/issue-lifecycle.spec.html"
echo 'Merge: spec `#gates-merge`.' > "$t/agents/ok.md"
# A statement of what never matches is not a branch default (scripts/octo-feather-integrate:22).
echo '# worker branches gh<N>-* and lane gh<N>0 never match.' > "$t/agents/never.md"
# Generic words are legitimate; the check under-catches them (reviews of af760a4, 014156b).
cat > "$t/agents/generic.md" <<'TXT'
A behavior-changing spec revision requires renewed acceptance before merging.
A behavior-changing spec revision requires renewed acceptance.
After the delta review the head moved, so review the delta again.
A moved head means the code reviewer reads only the fix delta.
A failed criterion goes to an implementer; then integrate and run qc again.
The smoke log is pinned to the head it ran on.
To update a worker branch, merging main into it is fine.
TXT
echo 'owner says merge, pinned to that head' > "$t/evidence/old.md"
printf '# reason: x\n--- a/SKILL.md\n+++ b/SKILL.md\n-Any code change after QC means qc again.\n' > "$t/.skillfile/patches/skills/x/SKILL.md.patch"
g add -A
run() { local want="$1"; set +e; out="$("$C" "$t" 2>&1)"; rc=$?; set -e
  [[ "$rc" == "$want" ]] || { echo "check-owned-rules test: want exit $want, got $rc: $out" >&2; exit 1; }; }
run 0
plant() { echo "$2" > "$t/$1"; g add -A; run 1
  grep -qF "$1:1: restates the $3 rule" <<<"$out" && grep -qF "$4" <<<"$out" || { echo "check-owned-rules test: $1 not named with its fix: $out" >&2; exit 1; }
  g rm -qf "$1"; run 0; }
plant agents/github.md 'Mechanical rebases onto accepted main do not require renewed acceptance when behavior and scope are unchanged.' merge-authority 'spec `#gates-merge`'
plant agents/impl.md 'Any code change after QC means `just qc` and a fresh review again, on the new head.' merge-authority 'spec `#gates-merge`'
plant agents/sleep.md 'Never hold your turn in a sleep over a minute; background `just qc` and end the turn.' long-wait 'herdr-comms (Send a message)'
plant agents/steer.md 'While a sleep runs, messages queue unread as "Steering".' long-wait 'herdr-comms (Send a message)'
# Spec-call rules (issue #63): a role paraphrasing them fails; its pointer and the check's own message pass.
echo '- Never edit a spec: ask your supervisor with the change and its evidence (rules: spec `#gates-spec-calls`).' > "$t/agents/calls-ok.md"
echo 'passes_as_written must be false: if the criteria pass as written there is no edit' > "$t/scripts/calls-msg"
g add -A; run 0
plant agents/calls.md 'Each call cites a failing command or an error. No evidence, no call.' spec-calls 'spec `#gates-spec-calls`'
plant agents/adds.md 'Additions are proposals, not calls: a new feature goes to docs/future.md.' spec-calls 'spec `#gates-spec-calls`'
# Loudness and denial (review of f3bd790: owned-rule-restatement): the role pointers pass, each copied clause fails.
cat > "$t/agents/loud-ok.md" <<'TXT'
Send each call spec `#gates-call-loudness` has the director tell the owner at once to the director with `herdr-say --parent`, naming the call. Handle a denial the director relays as spec `#gates-call-decision` says, setting the call's `denied` field in the commit that acts on it.
Spec calls (rules: spec `#gates-spec-calls`; when the owner hears a call and what a denial means: `#gates-call-loudness`, `#gates-call-decision`): pass each call message a supervisor sends you to the owner, naming the lane and the call. At merge, relay each call the owner denies to that lane's supervisor (`herdr-say <supervisor pane>`).
Do not wait for a reply from CI; poll it with `gh run watch`.
TXT
g add -A; run 0
plant agents/loud.md "A call that weakens or removes a criterion, and your lane's fourth call, go to the director at once." spec-calls '`#gates-call-loudness`'
plant agents/loud2.md "Tell the owner at once, naming the lane and the call; nothing waits on the reply and the lane keeps running." spec-calls '`#gates-call-loudness`'
plant agents/noreply.md "Send it with \`herdr-say --parent\`, naming the call; do not wait for a reply, keep working." spec-calls '`#gates-call-loudness`'
plant agents/deny.md "A denial the director relays is rework: undo or revise that change and set the call's \`denied\` field in the same commit." spec-calls '`#gates-call-decision`'
plant agents/deny2.md "At merge, relay each call the owner denies to that lane's supervisor as rework (\`herdr-say <supervisor pane>\`)." spec-calls '`#gates-call-decision`'
plant agents/lane.md 'Cut branch gh<N>-<slug> for the lane.' lane-branch 'docs/adr/0011'
plant agents/push.md '2. Verify the branch matches the target repo convention, else `octo-feather/gh<issue-number>-<slug>`.' lane-branch 'docs/adr/0011'
# A patch's added line is ours, so it is checked.
printf '# reason: x\n--- a/SKILL.md\n+++ b/SKILL.md\n+Main moving does not move the head.\n' > "$t/.skillfile/patches/skills/x/SKILL.md.patch"; g add -A; run 1
grep -qF 'SKILL.md.patch:4: restates the merge-authority rule' <<<"$out" || { echo "check-owned-rules test: patch line not named: $out" >&2; exit 1; }
g rm -qf .skillfile/patches/skills/x/SKILL.md.patch; run 0  # clean fixture: only the planted entry can fail
# Each RULES entry proves itself on its own examples before scanning (issue #36).
# Plant each failure mode in a copy of the script; the error names the entry and the fix.
selfcheck() { local name="$1" old="$2" new="$3" want="$4" c="$t/check-copy"
  python3 - "$C" "$c" "$old" "$new" <<'PY'
import sys
src, dst, old, new = sys.argv[1:]
s = open(src).read()
assert s.count(old) == 1, f"selfcheck anchor not unique in check-owned-rules: {old!r}"
open(dst, "w").write(s.replace(old, new))
PY
  set +e; out="$(python3 "$c" "$t" 2>&1)"; rc=$?; set -e
  [[ "$rc" == 1 ]] && grep -qF "$want" <<<"$out" && ! grep -q 'owned rules: ok' <<<"$out" \
    || { echo "check-owned-rules test: $name: want exit 1 and '$want', got $rc: $out" >&2; exit 1; }; }
selfcheck 'missing negatives' 'negatives=[  # gh19 handoffs 19:12Z' 'negatives_=[  # gh19 handoffs 19:12Z' \
  "RULES['lane-branch'] has no negatives: add a non-empty \`negatives\` list"
selfcheck 'missing positives' 'positives=[
            "Never hold' 'positives=[] and [
            "Never hold' \
  "RULES['long-wait'] has no positives: add a non-empty \`positives\` list"
selfcheck 'negative matched' '|mechanical rebase|' '|mechanical rebase|renewed acceptance|' \
  "RULES['merge-authority'] matches its own negative 'A behavior-changing spec revision requires renewed acceptance.' (\"renewed acceptance\"): narrow \`pattern\`"
selfcheck 'negative matched (wait)' 'hold(s|ing)? (your|its|their) turn|' 'hold(s|ing)? (your|its|their) turn|blocking wait|done rc|' \
  "RULES['long-wait'] matches its own negative 'A blocking wait over 30 seconds triggers the subprocess timeout.'"
selfcheck 'positive missed' '|change after (just )?qc' '' \
  "RULES['merge-authority'] misses its own positive 'Any code change after QC means \`just qc\` and a fresh review again, on the new head.': widen \`pattern\`"
# Shape, not truthiness (review of b73b115: unvalidated-input).
selfcheck 'bare-string negatives' 'negatives=[  # gh19 handoffs 19:17Z' 'negatives=("Mechanical rebase"), _n=[  # gh19 handoffs 19:17Z' \
  "RULES['merge-authority']['negatives'] is a str, not a list: write \`negatives=[...]\`"
selfcheck 'iterator positives' 'positives=[
            "Cut branch' 'positives=iter([]), _p=[
            "Cut branch' \
  "RULES['lane-branch']['positives'] is a list_iterator, not a list"
selfcheck 'iterator negatives' 'negatives=[  # gh28 handoffs' 'negatives=iter([]), _n=[  # gh28 handoffs' \
  "RULES['long-wait']['negatives'] is a list_iterator, not a list"
selfcheck 'empty tuple positives' 'positives=[
            "Mechanical rebases' 'positives=(), _p=[
            "Mechanical rebases' \
  "RULES['merge-authority'] has no positives: add a non-empty \`positives\` list"
selfcheck 'non-str element' '"The lane branch is `gh<N>`: see docs/adr/0011.",' '"The lane branch is `gh<N>`: see docs/adr/0011.", 42,' \
  "RULES['lane-branch']['negatives'][3] is 42 (int), not a non-empty str"
selfcheck 'empty-str element' '"The lane branch is `gh<N>`: see docs/adr/0011.",' '"The lane branch is `gh<N>`: see docs/adr/0011.", "",' \
  "RULES['lane-branch']['negatives'][3] is '' (str), not a non-empty str"
rm -f "$t/check-copy"
echo "check-owned-rules: ok (examples gate: missing positives/negatives, a matched negative and a missed positive fail naming the entry and fix; owner, pointer, record, generic words and short process waits pass; 3 past restatements, 2 long-wait copies, 7 spec-call copies, a slug default and a patch line fail with their fix)"
