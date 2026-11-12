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
export HOME="$t/home" XDG_STATE_HOME="$t/state" HERDR_SESSION="" STUB_ARGV="$t/argv" STUB_REPLY="$t/reply" REFLECT_READER="$kit/tests/fixtures/reflection-input"
unset HERDR_PANE_ID PI_SESSION_FILE OCTO_FEATHER_REFLECT_ARGS
fail() { echo "lane-reflect test: $*" >&2; exit 1; }
mkdir -p "$t/bin" "$HOME"
cat >"$t/bin/pi" <<'EOF'
#!/usr/bin/env python3
import os, sys, time, subprocess, json, pathlib
prompt = sys.stdin.read()
inputs = subprocess.check_output([sys.executable, os.environ['REFLECT_READER']], input=prompt, text=True)
if 'Director reflection' not in prompt:
    open(os.environ['STUB_ARGV'] + '.inputs', 'w').write(inputs)
    manifest = json.loads(inputs.splitlines()[0])
    binding_mutation = os.environ.get('STUB_BIND_MUTATE')
    if binding_mutation:
        record_path = pathlib.Path(next(s['original'] for s in manifest['sources'] if s['identity'] == 'director record'))
        open(os.environ['STUB_ARGV'] + '.phase', 'w').write(json.dumps({'binding': manifest['director'], 'record_before': record_path.read_text()}))
        if binding_mutation == 'pane':
            record = pathlib.Path(next(s['original'] for s in manifest['sources'] if s['identity'] == 'director record'))
            record.write_text('pane = "changed-pane"\n')
        else:
            source = pathlib.Path(next(s['original'] for s in manifest['sources'] if s['identity'].startswith('director w')))
            source.write_text('{"type":"session","id":"changed-header","cwd":"/synthetic/director"}\n')
    mutation = os.environ.get('STUB_MUTATE')
    if mutation:
        path = pathlib.Path(next(s['original'] for s in manifest['sources'] if s['identity'].startswith('supervisor') and s['available']))
        if mutation == 'disappear': path.unlink()
        elif mutation == 'rewrite': path.write_text('{"changed":true}\n')
        elif mutation == 'truncate': path.write_bytes(b'')
        elif mutation == 'replace':
            replacement = path.with_suffix('.replacement')
            replacement.write_bytes(path.read_bytes())
            replacement.replace(path)
        else:
            with path.open('a') as out: out.write('{"later":"EXCLUDED-APPEND"}\n')
if "Director reflection" not in prompt:
    open(os.environ["STUB_ARGV"], "w").write("\0".join([*sys.argv[1:], prompt]))
time.sleep(float(os.environ.get("STUB_SLEEP", "0")))
if os.environ.get("STUB_RC", "0") != "0":
    print("Error: 503 model openai/gpt-6.1-sol unreachable", file=sys.stderr); sys.exit(int(os.environ["STUB_RC"]))
if "Director reflection" in prompt:   # the director reflection archive runs next: tests/director-reflect.sh
    print("Questions: owner-asked, answered-from-memory, rework-decision, unblocking-first, outside-owner-gates, fact-already-recorded, writer-route, director-mechanical-step, director-reflection-missed\nFindings: none"); sys.exit()
sys.stdout.write(open(os.environ["STUB_REPLY"]).read())
EOF
export REFLECT_DIRECTOR_FILE="$t/director-source.jsonl"
cp "$kit/tests/fixtures/reflection-director" "$t/bin/herdr"
python3 "$kit/tests/fixtures/reflection-director" seed "$XDG_STATE_HOME/octo-feather"
chmod +x "$t/bin/pi" "$t/bin/herdr"
export PATH="$t/bin:$kit/tests/fixtures/tracker-gh:$PATH" FAKE_GH_STORE="$t/gh.json"   # the offline gh: a due correction lane files there (tests/lane-correction.sh)
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
argv="$(tr '\0' '\n' <"$STUB_ARGV"; cat "$STUB_ARGV.inputs")"
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
grep -qF "supervisor w9:p2: $own" "$STUB_ARGV.inputs" || fail "sources lack the supervisor's own transcript"

# Known source records exercise literal LF citation spans through the public command.
for boundary in final-lf no-final-lf two-records-final-lf multiwindow; do
  python3 - "$own" "$boundary" <<'PY'
import pathlib, sys
cases = {
    'final-lf': b'{}\n',
    'no-final-lf': b'{}\n{}',
    'two-records-final-lf': b'{}\n{}\n',
    'multiwindow': b'{}\n{"text":"' + b'x' * 70000 + b'"}\n{}\n',
}
pathlib.Path(sys.argv[1]).write_bytes(cases[sys.argv[2]])
PY
  out="$(HERDR_PANE_ID=w9:p2 PI_SESSION_FILE="$own" "$L" reflect gh901 2>&1)" || fail "literal LF $boundary failed: $out"
  python3 - "$STUB_ARGV.inputs" "$own" <<'PY'
import hashlib, json, pathlib, sys
inputs = pathlib.Path(sys.argv[1]).read_text()
manifest = json.loads(inputs.splitlines()[0])
source = next(s for s in manifest['sources'] if s['original'] == sys.argv[2])
assert source['sha256'] == hashlib.sha256(pathlib.Path(sys.argv[2]).read_bytes()).hexdigest()
assert f"Known literal LF spans: {source['presentation']['source_id']}\n" in inputs
PY
done

# Public presentation: astral worst-case JSON escaping, >2000 physical source lines,
# and a capture ending mid-UTF8 codepoint all reconstruct byte-for-byte through bounded windows.
python3 - "$own" <<'PY'
import json, pathlib, sys
pathlib.Path(sys.argv[1]).write_bytes(
    (json.dumps({'text': '🚀' * 3072}, ensure_ascii=False) + '\n' * 2100).encode()
    + b'\xf0\x9f'
)
PY
out="$(HERDR_PANE_ID=w9:p2 PI_SESSION_FILE="$own" "$L" reflect gh901 2>&1)" || fail "partial UTF8 windows failed: $out"
python3 - "$STUB_ARGV.inputs" "$own" <<'PY'
import json, pathlib, sys
manifest = json.loads(pathlib.Path(sys.argv[1]).read_text().splitlines()[0])
source = next(s for s in manifest['sources'] if s['original'] == sys.argv[2])
raw = pathlib.Path(sys.argv[2]).read_bytes()
assert source['bytes'] == len(raw) and raw.endswith(b'\xf0\x9f')
assert source['presentation']['count'] == 2
assert not pathlib.Path(source['presentation']['pattern']).parent.exists()
PY

# Appending after capture is excluded; changing/removing a captured prefix refuses before append.
for mutation in append rewrite truncate replace disappear; do
  printf '{}' >"$own" # partial final line: later bytes still cannot leak into snapshot
  before_log="$(cat "$lanes/gh901.handoffs.jsonl")"
  set +e
  out="$(HERDR_PANE_ID=w9:p2 PI_SESSION_FILE="$own" STUB_MUTATE="$mutation" "$L" reflect gh901 2>&1)"; rc=$?
  set -e
  if [[ "$mutation" == append ]]; then
    [[ "$rc" == 0 ]] || fail "append beyond cutoff refused: $out"
    ! grep -qF EXCLUDED-APPEND "$STUB_ARGV.inputs" || fail "snapshot exposed later append"
  else
    [[ "$rc" == 1 ]] && grep -qF 'source prefix changed or unavailable' <<<"$out" || fail "mutation not refused: $out"
    [[ "$(cat "$lanes/gh901.handoffs.jsonl")" == "$before_log" ]] || fail "mutation appended reflection"
  fi
  python3 - "$STUB_ARGV.inputs" <<'PY'
import json, pathlib, sys
manifest = json.loads(open(sys.argv[1]).readline())
assert all(not pathlib.Path(s['snapshot']).exists() for s in manifest['sources'] if s['available'])
assert all(not pathlib.Path(s['presentation']['pattern']).parent.exists() for s in manifest['sources'] if s['available'])
assert all(not pathlib.Path(s['presentation']['pattern']).parent.exists() for s in manifest['derived'].values())
PY
done

# Oversized lane evidence and history beyond400 remain at source, not in launch text.
python3 - "$lanes/gh901.handoffs.jsonl" <<'PY'
import json, sys
with open(sys.argv[1], 'a') as source:
    source.write(json.dumps({'kind': 'note', 'text': 'EARLY-LANE-RECORD'}) + '\n')
    for i in range(410):
        source.write(json.dumps({'kind': 'note', 'text': f'history-{i}'}) + '\n')
    source.write(json.dumps({'kind': 'note', 'text': 'LARGE-LANE-' + 'é reference | ' * 20000}, ensure_ascii=False) + '\n')
PY
out="$("$L" reflect gh901 2>&1)" || fail "oversized lane failed: $out"
python3 - "$STUB_ARGV" "$lanes/gh901.handoffs.jsonl" <<'PY'
import hashlib, json, pathlib, sys
launch = pathlib.Path(sys.argv[1]).read_text().split('\0')[-1]
inputs = pathlib.Path(sys.argv[1] + '.inputs').read_text()
assert len(launch.encode()) < 10000 and 'LARGE-LANE-' not in launch
assert inputs.count('LARGE-LANE-') == 1 and 'EARLY-LANE-RECORD' in inputs
reflection = json.loads(pathlib.Path(sys.argv[2]).read_text().splitlines()[-1])
assert reflection['inputs']['scope']['lane'] == 'gh901'
for source in reflection['inputs']['sources']:
    if source['available']:
        data = pathlib.Path(source['original']).read_bytes()[:source['bytes']]
        assert hashlib.sha256(data).hexdigest() == source['sha256']
        assert not pathlib.Path(source['snapshot']).exists()
PY

# Explicit director binding wins over unrelated newer sessions in the same cwd directory.
director_session=0b5e7a1c-0000-4000-8000-00000000d1ec
director_trace="$HOME/.pi/agent/sessions/--w--/old_$director_session.jsonl"
echo '{"type":"session","id":"'$director_session'","cwd":"/synthetic/director","fact":"EXACT-DIRECTOR-ONLY"}' >"$director_trace"
echo '{"fact":"WRONG-NEWEST-SESSION"}' >"$HOME/.pi/agent/sessions/--w--/newest_other.jsonl"
printf 'pane = "director-pane"\n' >"$state/director.toml"
out="$(REFLECT_NATIVE=0 REFLECT_DIRECTOR_PANE=director-pane HERDR_PANE_ID=director-pane PI_SESSION_ID="$director_session" PI_SESSION_FILE="$director_trace" "$L" reflect gh901 2>&1)" || fail "explicit director binding failed: $out"
grep -qF EXACT-DIRECTOR-ONLY "$STUB_ARGV.inputs" || fail "explicit director source missing"
! grep -qF WRONG-NEWEST-SESSION "$STUB_ARGV.inputs" || fail "guessed newest cwd session"
# A path is insufficient: runtime session id must agree with the session header.
set +e
out="$(REFLECT_NATIVE=0 REFLECT_DIRECTOR_PANE=director-pane HERDR_PANE_ID=director-pane PI_SESSION_ID=wrong-session PI_SESSION_FILE="$director_trace" "$L" reflect gh901 2>&1)"; rc=$?
set -e
[[ "$rc" == 1 ]] && grep -qF 'header/session identity unavailable or mismatched' <<<"$out" || fail "mismatched header not refused: $out"

# Another caller's PI_SESSION_FILE is never the director's provenance.
set +e
out="$(HERDR_PANE_ID=another-pane PI_SESSION_FILE="$director_trace" "$L" reflect gh901 2>&1)"; rc=$?
set -e
[[ "$rc" == 1 ]] && grep -qF 'director sourcegap' <<<"$out" || fail "unknown required source not refused: $out"
python3 "$kit/tests/fixtures/reflection-director" seed "$state"

tree() { (cd "$XDG_STATE_HOME" && find . -printf '%p %y %s\n' | sort && find . -type f -print0 | sort -z | xargs -0r sha256sum); }
# Missing native provenance refuses; explicit handoff reaches BOTH archive reflections.
seed gh904
b="$(tree)"
set +e; out="$(REFLECT_NATIVE=0 "$L" archive gh904 2>&1)"; rc=$?; set -e
[[ "$rc" == 1 ]] && grep -qF sourcegap <<<"$out" || fail "missing required source not refused: $out"
[[ "$(tree)" == "$b" ]] || fail "sourcegap changed archive state"
for variant in wrongpane missing header cwd nativeconflict nativeidconflict; do
  pane=w9:p99; file="$t/explicit.jsonl"; native=0
  cp "$REFLECT_DIRECTOR_FILE" "$file"
  case "$variant" in
    wrongpane) pane=wrong-pane ;;
    missing) file="$t/no-such-source" ;;
    header) printf '{"type":"message","id":"not-session"}\n' >"$file" ;;
    cwd) printf '{"type":"session","id":"wrong-cwd","cwd":"/another/cwd"}\n' >"$file" ;;
    nativeconflict) native=1 ;;
    nativeidconflict) native=id; printf '{"type":"session","id":"wrong-native-id","cwd":"/synthetic/director"}\n' >"$file" ;;
  esac
  set +e; out="$(REFLECT_NATIVE="$native" "$L" archive gh904 --director-source "$pane" "$file" 2>&1)"; rc=$?; set -e
  [[ "$rc" == 1 ]] && grep -qF 'invalid --director-source' <<<"$out" || fail "$variant explicit not refused: $out"
  [[ "$(tree)" == "$b" ]] || fail "$variant changed archive state"
done
for mutation in pane header; do
  rm -f "$STUB_ARGV.phase"
  before_log="$(cat "$lanes/gh904.handoffs.jsonl")"
  before_director="$(cat "$state/director.handoffs.jsonl")"
  set +e; out="$(STUB_BIND_MUTATE="$mutation" "$L" archive gh904 --director-source w9:p99 "$REFLECT_DIRECTOR_FILE" 2>&1)"; rc=$?; set -e
  python3 - "$STUB_ARGV.phase" <<'PY'
import json, sys
phase = json.load(open(sys.argv[1]))
assert phase['binding']['mode'] == 'explicit-director-handoff'
assert phase['binding']['pane'] == 'w9:p99'
assert phase['binding']['session'] == 'synthetic-director'
assert phase['record_before'] == 'pane = "w9:p99"\n'
PY
  if [[ "$mutation" == pane ]]; then want='director source pane does not match director.toml'; else want='director source binding changed'; fi
  [[ "$rc" == 1 ]] && grep -qF "$want" <<<"$out" || fail "changed $mutation not refused: $out"
  [[ "$(cat "$lanes/gh904.handoffs.jsonl")" == "$before_log" && "$(cat "$state/director.handoffs.jsonl")" == "$before_director" ]] || fail "changed binding appended reflection"
  [[ -f "$lanes/gh904.toml" && ! -f "$lanes/archive/gh904.toml" ]] || fail "changed binding moved lane"
  python3 "$kit/tests/fixtures/reflection-director" seed "$state"
done
# Native id and path forms both bind through their published schema, not cwd/newest guesses.
out="$(REFLECT_NATIVE=id "$L" reflect gh904 --director-source w9:p99 "$REFLECT_DIRECTOR_FILE" 2>&1)" || fail "native id binding failed: $out"
# Native absent: a declared older same-cwd session is accepted as DECLARATION, not currentness proof.
cp "$REFLECT_DIRECTOR_FILE" "$t/declared-old.jsonl"
touch -d '2000-01-01' "$t/declared-old.jsonl"
out="$(REFLECT_NATIVE=0 "$L" archive gh904 --director-source w9:p99 "$t/declared-old.jsonl" 2>&1)" || fail "declared handoff archive failed: $out"
python3 - "$lanes/archive/gh904.handoffs.jsonl" "$state/director.handoffs.jsonl" "$t/declared-old.jsonl" <<'PY'
import json, pathlib, sys
for path in sys.argv[1:3]:
    reflection = json.loads(pathlib.Path(path).read_text().splitlines()[-1])
    inputs = reflection['inputs']
    assert inputs['director']['mode'] == 'explicit-director-handoff'
    assert any(s['original'] == sys.argv[3] and s['available'] for s in inputs['sources'])
PY

refuse() { # WANT: archive gh902 refuses saying WANT, every file left as it was, lane still listed
  local b a out rc
  seed gh902; b="$(tree)"
  set +e; out="$("$L" archive gh902 2>&1)"; rc=$?; set -e
  [[ "$rc" == 1 ]] || fail "archive did not refuse ($rc): $out"
  grep -qF "lane reflection of gh902 failed" <<<"$out" && grep -qF -- "$1" <<<"$out" || fail "refusal does not name the failed reflection and '$1': $out"
  ! grep -q Traceback <<<"$out" || fail "traceback: $out"
  a="$(tree)"; [[ "$a" == "$b" ]] || fail "refusal changed files: $(diff <(echo "$b") <(echo "$a"))"
  [[ -f "$lanes/gh902.toml" && -f "$lanes/gh902.handoffs.jsonl" ]] || fail "lanes/ no longer lists gh902"
  python3 - "$STUB_ARGV.inputs" <<'PY'
import json, pathlib, sys
manifest = json.loads(open(sys.argv[1]).readline())
assert all(not pathlib.Path(s['snapshot']).exists() for s in manifest['sources'] if s['available'])
assert all(not pathlib.Path(s['presentation']['pattern']).parent.exists() for s in manifest['sources'] if s['available'])
assert all(not pathlib.Path(s['presentation']['pattern']).parent.exists() for s in manifest['derived'].values())
PY
}
# acceptance-reflect-before-archive: the reflector's model unreachable (pi exits non-zero).
STUB_RC=1 refuse "reflector exited 1: Error: 503 model openai/gpt-6.1-sol unreachable"
# Launch and timeout failures also leave every state byte unchanged.
printf '%s\nFindings: none\n' "$Q" >"$STUB_REPLY"
STUB_SLEEP=2 OCTO_FEATHER_REFLECT_TIMEOUT=0.2 refuse "reflector ran past"
mv "$t/bin/pi" "$t/bin/pi.saved"
printf '#!/missing-gh786-python\n' >"$t/bin/pi"; chmod +x "$t/bin/pi"
refuse "reflector exited"
mv "$t/bin/pi.saved" "$t/bin/pi"
# Replies outside the form: nothing appended either.
printf 'Looks fine to me.\n' >"$STUB_REPLY"; refuse "0 Questions lines"
printf 'Questions: caught-by-hand\nFindings: none\n' >"$STUB_REPLY"; refuse "want each of"
printf '%s\nFinding: class: owner-caught-x | question: caught-by-hand | route: r | summary: s\n' "$Q" >"$STUB_REPLY"; refuse "owner-caught-"
printf '%s\nFinding: class: x | question: nope | route: r | summary: s\n' "$Q" >"$STUB_REPLY"; refuse "question 'nope'"
printf '%s\n' "$Q" >"$STUB_REPLY"; refuse "no Finding line and no"
echo "lane-reflect: ok (archive: lane lines unchanged + 2 finding lines + reflection line; brief names role, director line, report, transcripts; no gap; reflect alone; refusals: model unreachable, no Questions, wrong questions, owner-caught class, unknown question, empty reply)"
