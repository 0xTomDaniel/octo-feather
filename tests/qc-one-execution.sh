#!/usr/bin/env bash
# Integration test for one execution for suite and QC (quality spec #qc-capture, #qc-judgment; #acceptance-one-execution,
# #acceptance-one-execution-incomplete), through commands: a scratch target whose gate is the kit's runner
# (tests/gate/ copied unchanged) has one test tagged `# criterion: demo#acceptance-a`, one tagged
# demo#acceptance-b that skips (exit 77), and one untagged. Its full gate, told the claims (OCTO_FEATHER_QC_CLAIMS),
# runs each tagged test once in the qc sandbox and appends one record per criterion naming each case and its
# outcome; `just qc` then judges acceptance-a pass from that record and acceptance-b insufficient evidence naming the
# skipped case, reruns nothing (no new record, no demo, no judge). A gate without claims captures nothing; a claim
# naming no criterion stops the gate before any test runs. Fake herdr, a pi that only logs: no model.
# Needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh.
set -euo pipefail
unset OCTO_FEATHER_CHECK_RUN OCTO_FEATHER_QC_CLAIMS   # a test harness, as tests/qc.sh: the scratch gate sets its own
[[ "$(uname -s)" != Darwin ]] || { echo "qc-one-execution: skipped, not on macOS (the qc sandbox needs Linux; CI runs it)"; exit 77; }
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'chmod -R u+w "$t" 2>/dev/null; rm -rf "$t"' EXIT
t="$(cd "$t" && pwd -P)"
UV_CACHE_DIR="$(uv cache dir)"; export UV_CACHE_DIR   # the kit's locked pytest, offline, where the kit's own gate finds it
# The box's mise installs, pinned before HOME moves (as tests/lib/qc.sh): the sandbox installs nothing.
for d in data cache config; do v="MISE_${d^^}_DIR"; [[ -n "${!v:-}" ]] || export "$v=$(mise doctor --json | jq -r --arg d "$d" '.dirs[$d]')"; done
fail() { echo "qc-one-execution test: $*" >&2; exit 1; }
export HOME="$t/home" XDG_STATE_HOME="$t/state" TMPDIR="$t/tmp" KIT="$kit"
unset XDG_CONFIG_HOME XDG_CACHE_HOME GH_CONFIG_DIR HERDR_SESSION HERDR_SOCKET_PATH HERDR_BIN_PATH HERDR_ENV OCTO_FEATHER_QC_DIR
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
mkdir -p "$HOME" "$TMPDIR" "$t/bin" "$t/repo/docs/specs" "$t/repo/tests/gate"
# Fake Herdr (the sandbox pins a per-run session through it); a pi that only logs, so any judge or model call shows.
cat > "$t/bin/herdr" <<'EOF'
#!/usr/bin/env bash
C="${XDG_CONFIG_HOME:-$HOME/.config}/herdr"; s=default; a=()
while (($#)); do case "$1" in --session) s="$2"; shift 2;; --remote|--machine) shift 2;; *) a+=("$1"); shift;; esac; done
[[ "$s" == default ]] && sock="$C/herdr.sock" || sock="$C/sessions/$s/herdr.sock"
case "${a[*]}" in
  server) mkdir -p "${sock%/*}"; echo "$s" > "$sock"; exec sleep 600;;
  "session stop "*) rm -f "$C/sessions/${a[2]}/herdr.sock"; exit 0;;
  "session delete "*) rm -rf "${C:?}/sessions/${a[2]}"; exit 0;;
  "pane list") exit 0;;
esac
[[ -f "$sock" ]] || { echo server_not_running >&2; exit 1; }
echo "{\"session\":\"$(cat "$sock")\"}"
EOF
printf '#!/usr/bin/env bash\n[[ "${1:-}" == --version ]] && exit 0\necho "$*" >> %q\nexit 2\n' "$t/pi.log" > "$t/bin/pi"
chmod +x "$t/bin/herdr" "$t/bin/pi"
export PATH="$t/bin:$kit/scripts:$PATH"

cd "$t/repo"; git init -q -b main .
git commit -qm accepted --allow-empty
cp "$kit/tests/fixtures/spec-status/good/demo.spec.html" docs/specs/
cp "$kit/tests/gate/conftest.py" "$kit/tests/gate/test_gate.py" tests/gate/
printf '.pytest_cache/\n__pycache__/\n' > .gitignore
printf '[pytest]\ntestpaths = tests/gate\naddopts = --strict-markers --junitxml=.pytest_cache/junit.xml\n' > pytest.ini
printf 'format = 1\n[entry]\ncommand = "true"\n[services]\n[fixture]\n[values]\n' > qc.toml
cat > justfile <<'EOF'
set positional-arguments
export GATE_RECIPES := "check-ok"
export OCTO_FEATHER_CHECK_RUN := `check-gate-free --run`
check: check-tests
check-ok:
    @true
check-tests *args:
    uv run --project "$KIT" --locked --offline --no-sync pytest -n 2 "$@"
EOF
cat > tests/accept.sh <<'EOF'
#!/usr/bin/env bash
# criterion: demo#acceptance-a
echo "RAN-accept: acceptance-a prints ok; home writable: $([[ -w "$HOME" ]] && echo yes || echo no)"
EOF
cat > tests/skip.sh <<'EOF'
#!/usr/bin/env bash
# criterion: demo#acceptance-b
echo "skip: needs a GPU, none here" >&2; exit 77
EOF
printf '#!/usr/bin/env bash\necho plain ran\n' > tests/plain.sh
chmod +x tests/*.sh
git add -A; git commit -qm target
octo-feather-spec-status init docs/specs/demo.spec.html "$(git rev-parse --short HEAD)" >/dev/null
git add -A; git commit -qm status
head="$(git rev-parse HEAD)"
records() { octo-feather-evidence read --repo . --json | python3 -c 'import json,sys; print(len(json.load(sys.stdin)))'; }
gate() { set +e; out="$(timeout -k 5 300 env "$@" just check 2>&1)"; rc=$?; set -e; }

# A claim naming no criterion: refused before any test runs.
gate OCTO_FEATHER_QC_CLAIMS="demo#acceptance-nope"
[[ "$rc" != 0 ]] && grep -q "names no criterion" <<< "$out" && ! grep -q "RAN-accept\|passed\|skipped" <<< "$out" \
  || fail "a claim naming no criterion: want the gate refused before any test, got $rc: $out"
[[ "$(records)" == 0 ]] || fail "a refused gate appended records"

# The final full gate with the lane's claims: green (a skip is no failure), one record per criterion, cases named.
gate OCTO_FEATHER_QC_CLAIMS="demo#acceptance-a demo#acceptance-b"
[[ "$rc" == 0 ]] || fail "capturing gate: want exit 0, got $rc: $out"
rid='[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}'
a="$(sed -nE "s/^qc capture: demo#acceptance-a: record ($rid), 1 case\(s\): tests\/accept.sh passed$/\1/p" <<< "$out")"
b="$(sed -nE "s/^qc capture: demo#acceptance-b: record ($rid), 1 case\(s\): tests\/skip.sh skipped$/\1/p" <<< "$out")"
[[ -n "$a" && -n "$b" ]] || fail "capturing gate: want one record each, naming its case and outcome: $out"
[[ "$(records)" == 2 ]] || fail "capturing gate: want 2 records, got $(records)"
octo-feather-evidence read --repo . --commit "$head" --json | python3 -c '
import json, os, sys
head, a, b = sys.argv[1:]
recs = {x["record"]["id"]: x for x in json.load(sys.stdin)}
for rid, cid, test, outcome in ((a, "demo#acceptance-a", "tests/accept.sh", "passed"), (b, "demo#acceptance-b", "tests/skip.sh", "skipped")):
    x = recs[rid]; r = x["record"]; out = os.path.join(x["dir"], "outputs")
    assert r["criterion"]["id"] == cid and r["revision"] == head and r["dirty"] is False, r
    cap = json.load(open(os.path.join(out, "test.capture.json")))
    assert cap["gate"]["head_at_start"] == head and cap["gate"]["clean_at_start"] is True and cap["gate"]["gate_config"], cap["gate"]
    [c] = cap["cases"]
    assert (c["case"], c["test"], c["outcome"]) == (f"tests/gate/test_gate.py::test_script[{test}]", test, outcome), c
    assert c["sandbox"]["proof"], c   # it ran in the qc sandbox: the proof came back
text = open(os.path.join(recs[a]["dir"], "outputs", "test.output")).read()
assert text.count("RAN-accept") == 1 and "home writable: no" in text, text   # once, and HOME read-only: the sandbox
assert "needs a GPU" in open(os.path.join(recs[b]["dir"], "outputs", "test.output")).read()
' "$head" "$a" "$b" || fail "records: $(octo-feather-evidence read --repo . --commit "$head")"

# Judgment refuses inside a check run, whatever the capture does there.
set +e; OCTO_FEATHER_CHECK_RUN='{"just":1}' octo-feather-qc docs/specs/demo.status.json 9 acceptance-a >/dev/null 2>&1; rc=$?; set -e
[[ "$rc" == 70 ]] || fail "judgment under the check marker: want 70, got $rc"

# just qc at that head: judged from the gate's records, nothing rerun, no judge.
set +e; out="$(timeout -k 5 120 just --justfile "$kit/justfile" qc docs/specs/demo.status.json 9 acceptance-a acceptance-b 2>"$t/err")"; rc=$?; set -e
[[ "$rc" == 2 ]] || fail "qc: want exit 2 (none failed, one insufficient), got $rc: $out $(tail -20 "$t/err")"
grep -A2 '^PASS acceptance-a: ' <<< "$out" | grep -qx "  evidence complete; decision tagged test assertions; record $a" \
  || fail "qc: want acceptance-a PASS from record $a: $out"
grep -A2 '^INSUFFICIENT EVIDENCE acceptance-b: ' <<< "$out" | grep -q "missing: case tests/skip.sh (tests/gate/test_gate.py::test_script\[tests/skip.sh\]) skipped: skip: needs a GPU, none here" \
  || fail "qc: want acceptance-b insufficient evidence naming the skipped case: $out"
grep -A3 '^INSUFFICIENT EVIDENCE acceptance-b: ' <<< "$out" | grep -qx "  evidence incomplete; decision tagged test assertions; record $b" \
  || fail "qc: want acceptance-b judged from record $b: $out"
[[ "$(records)" == 2 ]] || fail "qc reran something: $(records) records"
! grep -q 'agent fallback\|qc: demo ' "$t/err" || fail "qc ran a demo or the fallback: $(cat "$t/err")"
! grep -q 'qc-judge' "$t/pi.log" 2>/dev/null || fail "an agent judge ran: $(cat "$t/pi.log")"
rep="$(ls -t "$XDG_STATE_HOME"/octo-feather/qc/"$head"-*.json | head -1)"
python3 -c 'import json,sys; r=json.load(open(sys.argv[1])); assert r["captures"] == [] and "fallback" not in r, r' "$rep" \
  || fail "qc report: want no capture and no fallback: $(cat "$rep")"
python3 -c 'import json,sys; c=json.loads(sys.argv[1])["criteria"]; sys.exit(c["acceptance-a"] != {"status": "built", "pr": 9, "record": sys.argv[2], "commit": sys.argv[3], "tests": ["tests/accept.sh"]} or c["acceptance-b"] != {"status": "planned", "pr": None})' \
  "$(git show HEAD:docs/specs/demo.status.json)" "$a" "$head" || fail "status: $(git show HEAD:docs/specs/demo.status.json)"

# Without claims the gate runs as before: green, the tagged tests too, no record.
gate
[[ "$rc" == 0 ]] && ! grep -q "qc capture" <<< "$out" || fail "plain gate: want exit 0 and no capture, got $rc: $out"
[[ "$(records)" == 2 ]] || fail "plain gate appended records"

# A tagged criterion with no claims gate record at the judged head: insufficient evidence, never its demo or the fallback.
cat >> qc.toml <<'EOF'
[demo."demo#acceptance-a"]
command = "echo DEMO-RAN"
covers = ["tests"]
tests = ["tests/accept.sh"]
EOF
git commit -qam "a demo beside the tagged test"
h2="$(git rev-parse HEAD)"
set +e; out="$(timeout -k 5 120 just --justfile "$kit/justfile" qc docs/specs/demo.status.json 9 acceptance-a 2>"$t/err")"; rc=$?; set -e
[[ "$rc" == 2 ]] || fail "strict: want exit 2, got $rc: $out $(tail -20 "$t/err")"
grep -A1 '^INSUFFICIENT EVIDENCE acceptance-a: ' <<< "$out" | grep -q "missing: no claims gate record at ${h2:0:12}: tagged tests/gate/test_gate.py::test_script\[tests/accept.sh\]" \
  || fail "strict: want insufficient evidence naming the missing claims gate record and the tagged case: $out"
! grep -q 'DEMO-RAN\|agent fallback\|qc: demo ' <<< "$out$(cat "$t/err")" || fail "strict: the demo or the fallback ran: $out $(cat "$t/err")"
[[ "$(records)" == 2 ]] || fail "strict: qc appended a record"

# Partial capture: acceptance-a gains a second tagged test. A narrowed gate run with claims is refused before any test
# runs; a record holding only part of the criterion's tagged cases is insufficient evidence naming the missing case.
printf '#!/usr/bin/env bash\n# criterion: demo#acceptance-a\necho RAN-accept2\n' > tests/accept2.sh; chmod +x tests/accept2.sh
git add -A; git commit -qm "a second tagged test"
h3="$(git rev-parse HEAD)"
set +e; out="$(timeout -k 5 300 env OCTO_FEATHER_QC_CLAIMS=demo#acceptance-a just check-tests 'tests/gate/test_gate.py::test_script[tests/accept.sh]' 2>&1)"; rc=$?; set -e
[[ "$rc" != 0 ]] && grep -q "needs the full gate" <<< "$out" && ! grep -q "RAN-accept\|qc capture:" <<< "$out" \
  || fail "partial: want a narrowed capturing run refused before any test, got $rc: $out"
[[ "$(records)" == 2 ]] || fail "partial: a narrowed run appended a record"
partial() { set +e; out="$(timeout -k 5 120 just --justfile "$kit/justfile" qc docs/specs/demo.status.json 9 acceptance-a 2>"$t/err")"; rc=$?; set -e
  [[ "$rc" == 2 ]] && grep -A1 '^INSUFFICIENT EVIDENCE acceptance-a: ' <<< "$out" | grep -q "missing: $1" \
    && ! grep -q 'DEMO-RAN\|agent fallback' <<< "$out$(cat "$t/err")" || fail "partial: want insufficient evidence, missing: $1; got $rc: $out"; }
partial "no claims gate record at ${h3:0:12}"
# A record of only tests/accept.sh at h3, through the capture's store command: qc finds tests/accept2.sh missing.
python3 - "$t/session.json" "$h3" <<'EOF'
import json, sys
n = "tests/gate/test_gate.py::test_script[tests/accept.sh]"
json.dump({"claims": ["demo#acceptance-a"], "plan": {n: {"criteria": ["demo#acceptance-a"], "source": "tests/accept.sh"}},
           "reports": {n: {"phases": {w: {"outcome": "passed", "why": ""} for w in ("setup", "call", "teardown")}, "output": "RAN-accept\n", "seconds": 0.1}},
           "notes": {n: {"command": ["tests/accept.sh"], "ran": True, "exit": 0, "said": "RAN-accept", "sandbox": {"proof": ["ok"]}, "shots": []}},
           "head_at_start": sys.argv[2], "clean_at_start": True, "argv": ["-n", "2"], "tier": "full", "exit": 0}, open(sys.argv[1], "w"))
EOF
octo-feather-qc --capture-store "$t/session.json" | grep -q "1 case(s): tests/accept.sh passed" || fail "partial: the store did not record the session"
partial "case tests/gate/test_gate.py::test_script\[tests/accept2.sh\] tagged at ${h3:0:12}, not in the record"
echo "qc-one-execution: ok"
