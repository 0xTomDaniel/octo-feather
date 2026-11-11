#!/usr/bin/env bash
# Integration test for the correction lanes the reflection files (spec comms #reflection-correction,
# #acceptance-reflect-files-correction; issue-lifecycle #lanes-correction, #acceptance-reflection-missed-lane,
# #acceptance-writer-route-lane): scripts/octo-feather-lane archive and reflect --director run as commands, the
# real scripts/pi-role starting agents/reflector.md under a stub pi (it prints the reply the case gives), and the
# offline fake gh (tests/fixtures/tracker-gh) under the real github-issues scripts; nothing reaches GitHub.
# Proves each case below against the rule as issue-lifecycle #lanes-correction owns it (what counts, when a class is
# due, refiling, reflection-missed, owner-caught), and comms #reflection-correction (where it files, what it quotes).
# Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
L="$kit/scripts/octo-feather-lane"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
export HOME="$t/home" XDG_STATE_HOME="$t/state" HERDR_SESSION="" STUB_DIR="$t" FAKE_GH_STORE="$t/gh.json"
unset HERDR_PANE_ID PI_SESSION_FILE OCTO_FEATHER_REFLECT_ARGS GH_REPO
fail() { echo "lane-correction test: $*" >&2; exit 1; }
mkdir -p "$t/bin" "$HOME"
cat >"$t/bin/pi" <<'EOF'
#!/usr/bin/env python3
import os, sys
who = "director" if "Director reflection" in sys.stdin.read() else "lane"
sys.stdout.write(open(f"{os.environ['STUB_DIR']}/reply.{who}").read())
EOF
export REFLECT_DIRECTOR_FILE="$t/director-source.jsonl"
cp "$kit/tests/fixtures/reflection-director" "$t/bin/herdr"
python3 "$kit/tests/fixtures/reflection-director" seed "$XDG_STATE_HOME/octo-feather"
chmod +x "$t/bin/pi" "$t/bin/herdr"
export PATH="$t/bin:$kit/tests/fixtures/tracker-gh:$PATH"
state="$XDG_STATE_HOME/octo-feather"; lanes="$state/lanes"; dlog="$state/director.handoffs.jsonl"
mkdir -p "$lanes/archive"; : >"$dlog"; cd "$t"
DQ="Questions: owner-asked, answered-from-memory, rework-decision, unblocking-first, outside-owner-gates, fact-already-recorded, writer-route, director-mechanical-step, director-reflection-missed"
LQ="Questions: caught-by-hand, slow-or-from-memory, undetected-rule, check-misfired, mechanical-step, writer-mistake, reflection-missed"
none() { printf '%s\nFindings: none\n' "$LQ" >"$t/reply.lane"; printf '%s\nFindings: none\n' "$DQ" >"$t/reply.director"; }
cr() { printf '{"at":"%s","kind":"finding","source":"code-review","class":"%s","blocking":true,"summary":"%s"}\n' "$@"; }
lane() { # NAME FINDING-LINE...: an open lane on target o/t
  printf 'issue = "%s"\nrepository = "o/t"\nsupervisor = "w9:p2"\ngoal = "scratch"\n' "$1" >"$lanes/$1.toml"
  local n="$1"; shift; printf '%s\n' "$@" >"$lanes/$n.handoffs.jsonl"
}
issues() { python3 -c 'import json,sys; print(json.dumps(json.load(open(sys.argv[1]))["issues"]))' "$FAKE_GH_STORE" 2>/dev/null || echo '[]'; }
count() { python3 -c 'import json,sys; print(len(json.loads(sys.argv[1])))' "$(issues)"; }
close() { # NUMBER CLOSED-AT
  python3 - "$FAKE_GH_STORE" "$@" <<'EOF'
import json, sys
db = json.load(open(sys.argv[1]))
for i in db["issues"]:
    if i["number"] == int(sys.argv[2]): i.update(state="CLOSED", closedAt=sys.argv[3])
json.dump(db, open(sys.argv[1], "w"))
EOF
}

# acceptance-reflect-files-correction, -writer-route-lane: gh1 (archived) logged one dup-rule; gh2's review the second;
# the director reflection routes the class.
cr 2026-10-20T00:00:00Z dup-rule "gh1 restated the merge rule" >"$lanes/archive/gh1.handoffs.jsonl"
lane gh2 "$(cr 2026-10-21T00:00:00Z dup-rule "gh2 restated the gate rule")"
none; printf '%s\n%s\n' "$DQ" 'Finding: class: dup-rule | question: writer-route | route: agents/implementer.md Rules | summary: 2 code-review findings in gh1, gh2' >"$t/reply.director"
out="$("$L" archive gh2 2>&1)" || fail "archive gh2 failed: $out"
grep -qE '^correction lane: filed 901 in github-issues o/t for dup-rule \(2 findings; route: agents/implementer.md Rules\)$' <<<"$out" \
  || fail "archive printed no filed key: $out"
[[ -f "$lanes/archive/gh2.toml" ]] || fail "gh2 not archived: $out"
python3 - "$(issues)" <<'EOF' || fail "issue wrong: $(issues)"
import json, sys
(i,) = json.loads(sys.argv[1])
assert i["repo"] == "o/t" and "[correction-lane dup-rule]" in i["title"], i
for want in ("Class: dup-rule", "Route: agents/implementer.md Rules", "gh1 restated the merge rule", "gh2 restated the gate rule"):
    assert want in i["body"], (want, i["body"])
assert "question list" not in i["body"], i["body"]
EOF

# Its issue open: a third finding files nothing.
lane gh3 "$(cr 2026-10-22T00:00:00Z dup-rule "gh3 again")"; none
out="$("$L" archive gh3 2>&1)" || fail "archive gh3 failed: $out"
[[ "$(count)" == 1 ]] && grep -qxF "correction lanes: none filed" <<<"$out" || fail "open issue: filed again: $out $(issues)"

# Closed after the class's latest finding: nothing; closed before a newer finding: files again.
close 901 2099-01-01T00:00:00Z
lane gh4 "$(cr 2026-10-23T00:00:00Z dup-rule "gh4 again")"; none
out="$("$L" archive gh4 2>&1)" || fail "archive gh4 failed: $out"
[[ "$(count)" == 1 ]] || fail "closed after the latest finding: filed again: $out"
close 901 2026-10-23T12:00:00Z
lane gh5 "$(cr 2026-10-24T00:00:00Z dup-rule "gh5 after the close")"; none
out="$("$L" archive gh5 2>&1)" || fail "archive gh5 failed: $out"
grep -qF "correction lane: filed 902 in github-issues o/t for dup-rule" <<<"$out" || fail "closed before the latest finding: not filed: $out"

# acceptance-reflection-missed-lane: one lane reflection-missed finding files at once in the target; a director one in
# the kit's repo; owner-caught classes twice in the director log file nothing.
printf '%s\n' '{"at":"2026-10-25T00:00:00Z","kind":"finding","class":"owner-caught-stale-pr","summary":"a"}' \
  '{"at":"2026-10-25T01:00:00Z","kind":"finding","class":"owner-caught-stale-pr","summary":"b"}' >>"$dlog"
lane gh6
printf '%s\n%s\n' "$LQ" 'Finding: class: reflection-missed | question: reflection-missed | route: reflection/questions.json undetected-rule | summary: gh1 reflection found no gap; gh6 review found the rule broken; reword undetected-rule' >"$t/reply.lane"
printf '%s\n%s\n' "$DQ" 'Finding: class: reflection-missed | question: director-reflection-missed | route: reflection/questions.json owner-asked | summary: owner caught a stale PR after the last reflection; add a stale-PR question' >"$t/reply.director"
out="$("$L" archive gh6 2>&1)" || fail "archive gh6 failed: $out"
grep -qE '^correction lane: filed 903 in github-issues o/t for reflection-missed ' <<<"$out" || fail "lane reflection-missed not filed: $out"
grep -qE '^correction lane: filed 904 in github-issues 0xTomDaniel/octo-feather for reflection-missed ' <<<"$out" || fail "director reflection-missed not filed: $out"
python3 - "$(issues)" <<'EOF' || fail "reflection-missed issues wrong: $(issues)"
import json, sys
by = {i["number"]: i for i in json.loads(sys.argv[1])}
assert len(by) == 4, by.keys()
for n, quote in ((903, "reword undetected-rule"), (904, "add a stale-PR question")):
    i = by[n]
    assert "[correction-lane reflection-missed " in i["title"], i
    assert "Changes: the question list, reflection/questions.json" in i["body"] and quote in i["body"], i["body"]
assert not any("owner-caught" in i["title"] for i in by.values()), by
EOF

# Each reflection-missed finding files once: the director reflection alone, no new finding, files nothing.
none; out="$("$L" reflect --director 2>&1)" || fail "reflect --director failed: $out"
[[ "$(count)" == 4 ]] && grep -qxF "correction lanes: none filed" <<<"$out" || fail "refiled: $out $(issues)"

# Every due subject files, whichever lane's reflection runs: archived gh1 and gh2 hold one dup-rule finding each, the
# archive of unrelated gh3 files the class in gh1/gh2's target quoting both; a further archive files nothing.
fresh() { export XDG_STATE_HOME="$t/$1" FAKE_GH_STORE="$t/$1.gh.json"; state="$XDG_STATE_HOME/octo-feather"; lanes="$state/lanes"
  dlog="$state/director.handoffs.jsonl"; mkdir -p "$lanes/archive"; : >"$dlog"
  python3 "$kit/tests/fixtures/reflection-director" seed "$state"; }
archived() { lane "$@"; mv "$lanes/$1.toml" "$lanes/$1.handoffs.jsonl" "$lanes/archive/"; }
fresh other
archived gh1 "$(cr 2026-10-20T00:00:00Z dup-rule "gh1 restated the merge rule")"
archived gh2 "$(cr 2026-10-21T00:00:00Z dup-rule "gh2 restated the gate rule")"
lane gh3; none
out="$("$L" archive gh3 2>&1)" || fail "other lane: archive gh3 failed: $out"
grep -qE '^correction lane: filed 901 in github-issues o/t for dup-rule \(2 findings; route: none given by a reflection\)$' <<<"$out" \
  || fail "other lane: due class not filed: $out"
[[ -f "$lanes/archive/gh3.toml" ]] || fail "other lane: gh3 not archived: $out"
python3 - "$(issues)" <<'EOF' || fail "other lane: issue wrong: $(issues)"
import json, sys
(i,) = json.loads(sys.argv[1])
assert i["repo"] == "o/t" and "[correction-lane dup-rule]" in i["title"], i
for want in ("gh1 restated the merge rule", "gh2 restated the gate rule"):
    assert want in i["body"], (want, i["body"])
EOF
lane gh4; none
out="$("$L" archive gh4 2>&1)" || fail "other lane: archive gh4 failed: $out"
[[ "$(count)" == 1 ]] && grep -qxF "correction lanes: none filed" <<<"$out" || fail "other lane: refiled: $out $(issues)"

# acceptance-writer-route-lane through reflect --director: the class's findings in lanes, the director routes it.
fresh routed
archived gh1 "$(cr 2026-10-20T00:00:00Z stale-check "gh1 check missed a stale doc")"
archived gh2 "$(cr 2026-10-21T00:00:00Z stale-check "gh2 check missed a stale doc")"
none; printf '%s\n%s\n' "$DQ" 'Finding: class: stale-check | question: writer-route | route: agents/code-reviewer.md Rules | summary: 2 code-review findings in gh1, gh2' >"$t/reply.director"
out="$("$L" reflect --director 2>&1)" || fail "routed: reflect --director failed: $out"
grep -qE '^correction lane: filed 901 in github-issues o/t for stale-check \(2 findings; route: agents/code-reviewer.md Rules\)$' <<<"$out" \
  || fail "routed: not filed: $out"
python3 - "$(issues)" <<'EOF' || fail "routed: issue wrong: $(issues)"
import json, sys
(i,) = json.loads(sys.argv[1])
assert i["repo"] == "o/t" and "Route: agents/code-reviewer.md Rules" in i["body"], i
EOF

# What counts: two reflection findings of a class in two lanes, two blocking ones in one lane, a non-blocking review
# finding beside a blocking one, or the director log's: none due; a blocking product-judge (qc) finding counts.
fresh counts
rf() { printf '{"at":"%s","kind":"finding","source":"reflection","class":"%s","blocking":false,"question":"undetected-rule","route":"r","summary":"%s"}\n' "$@"; }
archived gh1 "$(rf 2026-10-20T00:00:00Z refl-only "gh1 reflection")" "$(cr 2026-10-20T00:00:00Z one-lane "gh1 a")" "$(cr 2026-10-20T01:00:00Z one-lane "gh1 b")" \
  "$(cr 2026-10-20T02:00:00Z judged "gh1 review")"
archived gh2 "$(rf 2026-10-21T00:00:00Z refl-only "gh2 reflection")" \
  '{"at":"2026-10-21T01:00:00Z","kind":"finding","source":"code-review","class":"one-lane","blocking":false,"summary":"gh2 note"}' \
  '{"at":"2026-10-21T02:00:00Z","kind":"finding","source":"qc","class":"judged","blocking":true,"summary":"gh2 judge"}'
printf '%s\n' '{"at":"2026-10-22T00:00:00Z","kind":"finding","class":"one-lane","summary":"director saw it"}' >>"$dlog"
lane gh3; none
out="$("$L" archive gh3 2>&1)" || fail "counts: archive gh3 failed: $out"
grep -qE '^correction lane: filed 901 in github-issues o/t for judged \(2 findings; ' <<<"$out" && [[ "$(count)" == 1 ]] \
  || fail "counts: want only judged filed: $out $(issues)"

echo "lane-correction: ok (only blocking code-review or qc findings in two lanes count, reflection, one-lane and director findings make none due; every due subject files whichever lane reflects, in its own lane's target; director-routed lane class files naming the route; second finding files in the lane's repo with findings and route, key printed; open or closed-after files nothing, closed-before refiles; reflection-missed files at once, lane's in the target, director's in the kit, naming the question list; owner-caught not filed)"
