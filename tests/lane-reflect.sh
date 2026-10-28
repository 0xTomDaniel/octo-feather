#!/usr/bin/env bash
# Integration test for the lane reflection at archive (spec comms #acceptance-reflect-lane,
# #acceptance-reflect-before-archive, #reflection-output): scripts/octo-feather-lane archive and reflect run
# as commands, the real scripts/pi-role starting agents/reflector.md, a stub pi first on PATH standing in
# for the model (it records its argv and prints the reply the case gives), a stub herdr that is unreachable.
# Proves: the archived hand-off log holds the lane's lines unchanged, then the finding and reflection lines
# of spec comms #reflection-output; the brief names the director log's lines about the lane, the factory
# report's lane lines and the transcripts; a reflector that cannot run, or replies outside the form, refuses
# the archive naming the failed reflection with every file left in place. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
L="$kit/scripts/octo-feather-lane"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
export HOME="$t/home" XDG_STATE_HOME="$t/state" HERDR_SESSION="" STUB_ARGV="$t/argv" STUB_REPLY="$t/reply"
unset HERDR_PANE_ID PI_SESSION_FILE OCTO_FEATHER_REFLECT_ARGS
fail() { echo "lane-reflect test: $*" >&2; exit 1; }
mkdir -p "$t/bin" "$HOME"
cat >"$t/bin/pi" <<'EOF'
#!/usr/bin/env python3
import os, sys
if not any("Director reflection" in a for a in sys.argv):
    open(os.environ["STUB_ARGV"], "w").write("\0".join(sys.argv[1:]))
if os.environ.get("STUB_RC", "0") != "0":
    print("Error: 503 model openai/gpt-6.1-sol unreachable", file=sys.stderr); sys.exit(int(os.environ["STUB_RC"]))
if any("Director reflection" in a for a in sys.argv):   # the director reflection archive runs next: tests/director-reflect.sh
    print("Questions: owner-asked, answered-from-memory, rework-decision, unblocking-first, outside-owner-gates, fact-already-recorded, writer-route, director-mechanical-step, director-reflection-missed\nFindings: none"); sys.exit()
sys.stdout.write(open(os.environ["STUB_REPLY"]).read())
EOF
printf '#!/bin/sh\necho "herdr: no server" >&2; exit 1\n' >"$t/bin/herdr"
chmod +x "$t/bin/pi" "$t/bin/herdr"
export PATH="$t/bin:$PATH"
state="$XDG_STATE_HOME/octo-feather"; lanes="$state/lanes"; mkdir -p "$lanes"
Q="Questions: caught-by-hand, slow-or-from-memory, undetected-rule, check-misfired, mechanical-step, writer-mistake, reflection-missed"

# A merged lane: a review finding, a worker spawn with its session, and a director-log stranded-worker catch.
session=0b5e7a1c-0000-4000-8000-00000000c0de
mkdir -p "$HOME/.pi/agent/sessions/--w--"; tr="$HOME/.pi/agent/sessions/--w--/2026-10-28T00-00-00-000Z_$session.jsonl"; echo '{}' >"$tr"
seed() { # NAME
  printf 'issue = "gh%s"\nsupervisor = "w9:p2"\ngoal = "scratch"\n' "${1#gh}" >"$lanes/$1.toml"
  printf '%s\n' '{"at":"2026-10-28T00:00:00Z","kind":"spawn","name":"implementer-gh900","pane":"w9:p3","role":"implementer","session":"'"$session"'"}' \
    '{"at":"2026-10-28T00:10:00Z","kind":"finding","source":"code-review","class":"duplicated-rule","blocking":true,"summary":"restated rule"}' >"$lanes/$1.handoffs.jsonl"
}
printf '%s\n' '{"at":"2026-10-28T00:20:00Z","kind":"note","issue":900,"text":"read pane w9:p3: implementer-gh900 stranded at a trust prompt"}' \
  '{"at":"2026-10-28T00:21:00Z","kind":"note","issue":7,"text":"unrelated lane"}' >"$state/director.handoffs.jsonl"

# acceptance-reflect-lane: two gaps, each a finding line, then one reflection line.
seed gh900; before="$(cat "$lanes/gh900.handoffs.jsonl")"
printf '%s\n' "$Q" \
  'Finding: class: stranded-worker-by-hand | question: caught-by-hand | route: agents/supervisor.md goal check-in | summary: director found implementer-gh900 stranded by reading pane w9:p3 (director log); a herdr agent get status check at the goal check-in would have caught it first' \
  'Finding: class: restated-rule | question: writer-mistake | route: .agents/skills/code-review | summary: review finding duplicated-rule (hand-off log line 2)' >"$STUB_REPLY"
out="$("$L" archive gh900 2>&1)" || fail "archive gh900 failed: $out"
a="$lanes/archive/gh900.handoffs.jsonl"
[[ -f "$a" && ! -e "$lanes/gh900.toml" && ! -e "$lanes/gh900.handoffs.jsonl" ]] || fail "gh900 not archived: $out"
grep -qF "reflection: lane gh900, 2 findings" <<<"$out" || fail "no reflection summary: $out"
python3 - "$a" "$before" <<'EOF' || fail "archived log wrong: $(cat "$a")"
import json, sys
lines = open(sys.argv[1]).read().splitlines()
assert lines[:2] == sys.argv[2].splitlines(), "lane lines changed"
f1, f2, r = (json.loads(l) for l in lines[2:])
assert len(lines) == 5, len(lines)
for f in (f1, f2):
    assert f["kind"] == "finding" and f["source"] == "reflection" and f["blocking"] is False, f
    assert set(f) == {"at", "kind", "source", "class", "blocking", "question", "route", "summary"}, f
assert (f1["class"], f1["question"], f1["route"]) == ("stranded-worker-by-hand", "caught-by-hand", "agents/supervisor.md goal check-in"), f1
assert "stranded by reading pane w9:p3" in f1["summary"], f1
assert (f2["class"], f2["question"]) == ("restated-rule", "writer-mistake"), f2
assert r["kind"] == "reflection" and r["findings"] == 2, r
assert r["questions"] == ["caught-by-hand", "slow-or-from-memory", "undetected-rule", "check-misfired", "mechanical-step", "writer-mistake", "reflection-missed"], r
EOF
# The reflector ran as agents/reflector.md (its model, thinking, tools, reflect skill) on a brief naming its inputs.
argv="$(tr '\0' '\n' <"$STUB_ARGV")"
for want in "openai/gpt-6.1-sol" "high" "read,grep,find,ls,codemode" "$kit/.agents/skills/reflect" \
  "read pane w9:p3: implementer-gh900 stranded" "spawn implementer-gh900 implementer w9:p3: $tr" "lane gh900: issue gh900" \
  "$lanes/gh900.handoffs.jsonl" "- caught-by-hand: What did anyone"; do
  grep -qF -- "$want" <<<"$argv" || fail "reflector argv lacks '$want': $argv"
done
! grep -qF "unrelated lane" <<<"$argv" || fail "brief quoted another lane's director line"

# No gap: the reflection line alone, findings 0; `reflect` alone appends and moves nothing; the
# supervisor's own transcript when run from its pane.
seed gh901; printf '%s\nFindings: none\n' "$Q" >"$STUB_REPLY"
own="$t/own.jsonl"; echo '{}' >"$own"
out="$(HERDR_PANE_ID=w9:p2 PI_SESSION_FILE="$own" "$L" reflect gh901 2>&1)" || fail "reflect gh901 failed: $out"
[[ -f "$lanes/gh901.toml" ]] || fail "reflect moved the record"
[[ "$(tail -1 "$lanes/gh901.handoffs.jsonl" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["kind"], d["findings"], len(d["questions"]))')" == "reflection 0 7" ]] \
  || fail "no-gap reflection line wrong: $(tail -1 "$lanes/gh901.handoffs.jsonl")"
[[ "$(wc -l <"$lanes/gh901.handoffs.jsonl")" == 3 ]] || fail "no-gap reflection appended a finding"
grep -qF "supervisor w9:p2: $own" <(tr '\0' '\n' <"$STUB_ARGV") || fail "brief lacks the supervisor's own transcript"

tree() { (cd "$XDG_STATE_HOME" && find . -printf '%p %y %s\n' | sort && find . -type f -print0 | sort -z | xargs -0r sha256sum); }
refuse() { # WANT: archive gh902 refuses saying WANT, every file left as it was, lane still listed
  local b a out rc
  seed gh902; b="$(tree)"
  set +e; out="$("$L" archive gh902 2>&1)"; rc=$?; set -e
  [[ "$rc" == 1 ]] || fail "archive did not refuse ($rc): $out"
  grep -qF "lane reflection of gh902 failed" <<<"$out" && grep -qF -- "$1" <<<"$out" || fail "refusal does not name the failed reflection and '$1': $out"
  ! grep -q Traceback <<<"$out" || fail "traceback: $out"
  a="$(tree)"; [[ "$a" == "$b" ]] || fail "refusal changed files: $(diff <(echo "$b") <(echo "$a"))"
  [[ -f "$lanes/gh902.toml" && -f "$lanes/gh902.handoffs.jsonl" ]] || fail "lanes/ no longer lists gh902"
}
# acceptance-reflect-before-archive: the reflector's model unreachable (pi exits non-zero).
STUB_RC=1 refuse "reflector exited 1: Error: 503 model openai/gpt-6.1-sol unreachable"
# Replies outside the form: nothing appended either.
printf 'Looks fine to me.\n' >"$STUB_REPLY"; refuse "0 Questions lines"
printf 'Questions: caught-by-hand\nFindings: none\n' >"$STUB_REPLY"; refuse "want each of"
printf '%s\nFinding: class: owner-caught-x | question: caught-by-hand | route: r | summary: s\n' "$Q" >"$STUB_REPLY"; refuse "owner-caught-"
printf '%s\nFinding: class: x | question: nope | route: r | summary: s\n' "$Q" >"$STUB_REPLY"; refuse "question 'nope'"
printf '%s\n' "$Q" >"$STUB_REPLY"; refuse "no Finding line and no"
echo "lane-reflect: ok (archive: lane lines unchanged + 2 finding lines + reflection line; brief names role, director line, report, transcripts; no gap; reflect alone; refusals: model unreachable, no Questions, wrong questions, owner-caught class, unknown question, empty reply)"
