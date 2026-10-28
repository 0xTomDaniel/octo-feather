#!/usr/bin/env bash
# Integration test for the director reflection (spec comms #reflection-director, #reflection-writer-route,
# #acceptance-reflect-director, #acceptance-reflect-writer-route, #acceptance-reflect-missed,
# #acceptance-reflect-daily): scripts/octo-feather-lane reflect --director and archive, and
# scripts/octo-feather-start, run as commands; the real scripts/pi-role starts agents/reflector.md, a stub pi
# first on PATH stands in for the model (it records the director brief and prints the reply the case gives).
# Proves: the brief carries the director log's lines since the last director reflection, every lane log
# (archived included) with its lane reflections, and the finding class counts by source and frequency; the
# director log gains the finding and reflection lines of spec comms #reflection-output; archive runs it after
# the lane reflection and refuses, every file in place, when it cannot run; a start runs it in the
# background when the last one is two days old, and not when it is fresh. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
L="$kit/scripts/octo-feather-lane"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
export HOME="$t/home" XDG_STATE_HOME="$t/state" HERDR_SESSION="" STUB_DIR="$t"
unset HERDR_PANE_ID PI_SESSION_FILE OCTO_FEATHER_REFLECT_ARGS
fail() { echo "director-reflect test: $*" >&2; exit 1; }
mkdir -p "$t/bin" "$HOME"
cat >"$t/bin/pi" <<'EOF'
#!/usr/bin/env python3
import os, sys, time
d = os.environ["STUB_DIR"]; who = "director" if any("Director reflection" in a for a in sys.argv) else "lane"
open(f"{d}/argv.{who}", "w").write("\0".join(sys.argv[1:]))
time.sleep(float(os.environ.get("STUB_SLEEP", "0")) if who == "director" else 0)
if who == "director" and os.environ.get("STUB_DRC", "0") != "0":
    print("Error: 503 model openai/gpt-6.1-sol unreachable", file=sys.stderr); sys.exit(1)
sys.stdout.write(open(f"{d}/reply.{who}").read())
EOF
printf '#!/bin/sh\necho "herdr: no server" >&2; exit 1\n' >"$t/bin/herdr"
chmod +x "$t/bin/pi" "$t/bin/herdr"
export PATH="$t/bin:$kit/tests/fixtures/tracker-gh:$PATH" FAKE_GH_STORE="$t/gh.json"   # the offline gh: a due correction lane files there (tests/lane-correction.sh)
state="$XDG_STATE_HOME/octo-feather"; lanes="$state/lanes"; dlog="$state/director.handoffs.jsonl"
mkdir -p "$lanes/archive"
ago() { python3 -c 'import datetime as d, sys; print((d.datetime.now(d.timezone.utc) - d.timedelta(hours=float(sys.argv[1]))).strftime("%Y-%m-%dT%H:%M:%SZ"))' "$1"; }
DQ="Questions: owner-asked, answered-from-memory, rework-decision, unblocking-first, outside-owner-gates, fact-already-recorded, writer-route, director-mechanical-step, director-reflection-missed"
LQ="Questions: caught-by-hand, slow-or-from-memory, undetected-rule, check-misfired, mechanical-step, writer-mistake, reflection-missed"
cr() { printf '{"at":"%s","kind":"finding","source":"%s","class":"%s","blocking":true,"summary":"s"}\n' "$@"; }

# Three lanes, one code-review class in each: gh1 archived after a lane reflection that found no gap,
# gh2 archived, gh3 open; gh3's review found the gap later, and a qc finding of another class.
{ cr 2026-10-20T00:00:00Z code-review duplicated-rule
  echo '{"at":"2026-10-20T01:00:00Z","kind":"reflection","findings":0,"questions":["undetected-rule"]}'; } >"$lanes/archive/gh1.handoffs.jsonl"
cr 2026-10-21T00:00:00Z code-review duplicated-rule >"$lanes/archive/gh2.handoffs.jsonl"
printf 'issue = "gh3"\nsupervisor = "w9:p2"\ngoal = "scratch"\n' >"$lanes/gh3.toml"
{ cr 2026-10-22T00:00:00Z code-review duplicated-rule; cr 2026-10-22T00:01:00Z qc bad-fixture; } >"$lanes/gh3.handoffs.jsonl"
old="$(ago 48)"
printf '%s\n' '{"at":"2026-10-19T00:00:00Z","kind":"note","text":"before-last-reflection"}' \
  '{"at":"'"$old"'","kind":"reflection","findings":0,"questions":["owner-asked"]}' \
  '{"at":"2026-10-27T00:00:00Z","kind":"finding","class":"owner-caught-stranded-worker","issue":3,"summary":"owner found implementer-gh3 stranded at a prompt"}' >"$dlog"

# acceptance-reflect-writer-route, -missed: reflect --director on its own.
printf '%s\n' "$DQ" \
  'Finding: class: duplicated-rule | question: writer-route | route: agents/implementer.md Rules | summary: 3 code-review findings in 3 lanes (gh1, gh2, gh3); writers restate rules' \
  'Finding: class: reflection-missed | question: director-reflection-missed | route: reflection/questions.json undetected-rule | summary: gh1 reflection found no gap; gh3 review found duplicated-rule; reword undetected-rule' >"$t/reply.director"
b="$(wc -l <"$dlog")"
out="$("$L" reflect --director 2>&1)" || fail "reflect --director failed: $out"
grep -qF "reflection: director, 2 findings, questions owner-asked," <<<"$out" || fail "no reflection summary: $out"
python3 - "$dlog" "$b" <<'EOF' || fail "director log wrong: $(cat "$dlog")"
import json, sys
lines = [json.loads(l) for l in open(sys.argv[1]).read().splitlines()]
f1, f2, r = lines[int(sys.argv[2]):]
for f in (f1, f2):
    assert set(f) == {"at", "kind", "source", "class", "question", "route", "summary"} and f["source"] == "reflection", f
assert (f1["class"], f1["question"], f1["route"]) == ("duplicated-rule", "writer-route", "agents/implementer.md Rules"), f1
assert "3 code-review findings in 3 lanes" in f1["summary"], f1
assert (f2["class"], f2["question"]) == ("reflection-missed", "director-reflection-missed"), f2
assert r["kind"] == "reflection" and r["findings"] == 2 and len(r["questions"]) == 9, r
EOF
argv="$(tr '\0' '\n' <"$t/argv.director")"
for want in "openai/gpt-6.1-sol" "$kit/.agents/skills/reflect" "last director reflection ($old)" \
  "owner-caught-stranded-worker" "class duplicated-rule, source code-review: 3 findings in 3 lanes (gh1, gh2, gh3), last 2026-10-22T00:00:00Z" \
  "class bad-fixture, source qc: 1 finding in 1 lane (gh3)" "gh1: $lanes/archive/gh1.handoffs.jsonl; lane reflections: 2026-10-20T01:00:00Z 0 findings" \
  "gh3: $lanes/gh3.handoffs.jsonl; lane reflections: none" "report at " "- writer-route: Which code-review"; do
  grep -qF -- "$want" <<<"$argv" || fail "director brief lacks '$want': $argv"
done
! grep -qF "before-last-reflection" <<<"$argv" || fail "brief quoted a line from before the last director reflection"
! grep -qF -- "- caught-by-hand:" <<<"$argv" || fail "director brief asked a lane question"

# --due: the last director reflection ran just now, so a due run does nothing.
rm -f "$t/argv.director"
out="$("$L" reflect --director --due 2>&1)" || fail "--due failed: $out"
grep -qF "director reflection: not due, last ran" <<<"$out" && [[ ! -e "$t/argv.director" ]] || fail "--due ran a fresh one: $out"

# acceptance-reflect-director: archiving a merged lane runs the lane, then the director reflection.
printf 'issue = "gh4"\nsupervisor = "w9:p2"\ngoal = "scratch"\n' >"$lanes/gh4.toml"; cr 2026-10-28T00:00:00Z code-review x >"$lanes/gh4.handoffs.jsonl"
echo '{"at":"2026-10-28T00:30:00Z","kind":"finding","class":"owner-caught-merge-order","summary":"owner asked why the unblocking fix was not merged first"}' >>"$dlog"
printf '%s\nFindings: none\n' "$LQ" >"$t/reply.lane"
printf '%s\n%s\n' "$DQ" 'Finding: class: merge-order-by-hand | question: owner-asked | route: agents/director.md Merge order | summary: owner asked why the unblocking fix was not first (director log owner-caught-merge-order); a blocked-by count in octo-feather-lane report would have caught it first' >"$t/reply.director"
b="$(grep -c '"kind": "reflection"' "$dlog" || true)"
out="$("$L" archive gh4 2>&1)" || fail "archive gh4 failed: $out"
[[ -f "$lanes/archive/gh4.toml" && ! -e "$lanes/gh4.toml" ]] || fail "gh4 not archived: $out"
grep -qF "reflection: lane gh4" <<<"$out" && grep -qF "reflection: director, 1 finding" <<<"$out" || fail "archive did not run both reflections: $out"
[[ "$(grep -c '"kind": "reflection"' "$dlog")" == "$((b + 1))" ]] || fail "director log did not gain one reflection line: $(cat "$dlog")"
tail -2 "$dlog" | head -1 | grep -qF '"question": "owner-asked"' || fail "no owner-asked finding: $(tail -2 "$dlog")"
grep -qF "owner-caught-merge-order" <(tr '\0' '\n' <"$t/argv.director") || fail "director brief lacks the owner-caught line"
grep -qF "gh4: $lanes/gh4.handoffs.jsonl" <(tr '\0' '\n' <"$t/argv.director") || fail "director brief lacks the archiving lane's log"

# The director reflection cannot run: archive refuses naming it, every file as it was.
tree() { (cd "$XDG_STATE_HOME" && find . -printf '%p %y %s\n' | sort && find . -type f -print0 | sort -z | xargs -0r sha256sum); }
printf 'issue = "gh5"\nsupervisor = "w9:p2"\ngoal = "scratch"\n' >"$lanes/gh5.toml"; cr 2026-10-28T00:00:00Z code-review x >"$lanes/gh5.handoffs.jsonl"
before="$(tree)"
set +e; out="$(STUB_DRC=1 "$L" archive gh5 2>&1)"; rc=$?; set -e
[[ "$rc" == 1 ]] && grep -qF "director reflection failed (reflector exited 1: Error: 503" <<<"$out" || fail "archive did not refuse naming the director reflection ($rc): $out"
! grep -q Traceback <<<"$out" || fail "traceback: $out"
after="$(tree)"; [[ "$after" == "$before" ]] || fail "refusal changed files: $(diff <(echo "$before") <(echo "$after"))"
rm "$lanes/gh5.toml" "$lanes/gh5.handoffs.jsonl"

# acceptance-reflect-daily: a lane start when the last director reflection ran two days ago runs one in the
# background; the start returns before the reflector does.
mkdir -p "$t/hbin"; cp "$kit/tests/fixtures/herdr-say/herdr" "$t/hbin/"; chmod +x "$t/hbin/herdr"
git -c init.defaultBranch=main init -q "$t/target"
echo '{"at":"'"$(ago 48)"'","kind":"reflection","findings":0,"questions":["owner-asked"]}' >>"$dlog"
b="$(grep -c '"kind": "reflection"' "$dlog")"; rm -f "$t/argv.director"
printf '%s\nFindings: none\n' "$DQ" >"$t/reply.director"
start() { mkdir -p "$t/h$1"; env -u HERDR_WORKSPACE_ID -u OCTO_FEATHER_PARENT -u OCTO_FEATHER_ROLE PATH="$t/hbin:$PATH" FAKE_HERDR_DIR="$t/h$1" \
  XDG_CACHE_HOME="$t/cache" HERDR_SPAWN_READY_RETRIES=2 STUB_SLEEP=8 "$kit/scripts/octo-feather-start" --issue "$1" --cwd "$t/target"; }
s=$SECONDS; out="$(start 12 2>&1)" || fail "start failed: $out"
(( SECONDS - s < 8 )) || fail "start waited on the reflection ($((SECONDS - s))s)"
[[ "$(grep -c '"kind": "reflection"' "$dlog")" == "$b" ]] || fail "reflection line before the reflector returned"
# The reflector appends the log line, then prints its report line: wait for both observables, bounded.
for _ in $(seq 80); do [[ "$(grep -c '"kind": "reflection"' "$dlog")" == "$((b + 1))" ]] && grep -qF "reflection: director, 0 findings" "$state/director-reflection.out" 2>/dev/null && break; sleep 0.5; done
[[ "$(grep -c '"kind": "reflection"' "$dlog")" == "$((b + 1))" ]] || fail "start ran no director reflection: $(cat "$state/director-reflection.out" 2>/dev/null)"
grep -qF "reflection: director, 0 findings" "$state/director-reflection.out" || fail "no output in director-reflection.out"
# Fresh now: a second start runs none.
rm -f "$t/argv.director"; out="$(start 13 2>&1)" || fail "second start failed: $out"
for _ in $(seq 20); do grep -qF "not due, last ran" "$state/director-reflection.out" && break; sleep 0.5; done
grep -qF "director reflection: not due, last ran" "$state/director-reflection.out" && [[ ! -e "$t/argv.director" ]] || fail "a fresh reflection ran again: $(cat "$state/director-reflection.out")"
echo "director-reflect: ok (writer-route counts by source in 3 lanes, reflection-missed, lines since the last reflection, director log lines; --due skips a fresh one; archive runs lane then director reflection; director failure refuses with every file in place; start runs a two-day-old one in the background, not a fresh one)"
