#!/usr/bin/env bash
# The qc sandbox test's judge section (#508; setup tests/lib/qc.sh): --no-sandbox prints, writes its report and never
# commits; a run killed mid-judge leaves no scratch; a passed criterion becomes built and a failed one stays planned
# in one status-only commit; the judge launches from its own role file (agents/qc-judge.md), its model read there.
# Run by `just check`; offline and bounded, in its own namespace and throwaway HOME (tests/lib/qc.sh).
# shellcheck source=tests/lib/qc.sh
source "$(dirname "$0")/lib/qc.sh"
before="$(git rev-parse HEAD)"
# --no-sandbox: printed, report written, status never changes.
run 1 mixed $st 5 acceptance-a acceptance-b --no-sandbox
grep -q UNSANDBOXED <<< "$out" || fail "--no-sandbox not printed: $out"
[[ "$(git rev-parse HEAD)" == "$before" && -z "$(git status --porcelain)" ]] || fail "--no-sandbox changed the status file"
[[ "$(report '["sandbox"]')" == False ]] || fail "--no-sandbox report must record sandbox false"
! jr '["stdout"]' | grep -q "LINEAR KEY IN JUDGE ENV" || fail "--no-sandbox judge got LINEAR_API_KEY"
# A run killed mid-judge (as a timeout kills it: SIGTERM to its process group) leaves no scratch behind.
FAKE_QC=hang timeout -k 5 "$lim" "$Q" $st 5 acceptance-a --no-sandbox > /dev/null 2>&1 & hp=$!; echo "$hp" > "$t/pids/run"
for _ in $(seq 100); do compgen -G "$TMPDIR/qc-ghmiss-*" > /dev/null && break; sleep 0.1; done
compgen -G "$TMPDIR/qc-ghmiss-*" > /dev/null || fail "hang run: no scratch before the judge (nothing to prove)"
kill -TERM "$hp"; set +e; wait "$hp"; rc=$?; set -e; rm -f "$t/pids/run"
[[ "$rc" != 0 ]] || fail "hang run exited 0"
sleep 0.2; [[ -z "$(ls -A "$TMPDIR")" ]] || fail "killed run left scratch: $(ls -A "$TMPDIR")"
! pgrep -fx "sleep 3040$tok" > /dev/null || fail "killed run's judge survived"

run 1 mixed $st 5 acceptance-a acceptance-b                                                     # a passes, b fails
python3 - "$st" "$before" <<'EOF'
import json, re, sys
c = json.load(open(sys.argv[1]))["criteria"]
a = c["acceptance-a"]   # built by the agent fallback: its record, captured at the judged head, no declared tests
assert re.fullmatch(r"\d{8}T\d{6}Z-[0-9a-f]{8}", a.pop("record", "")), c
assert a == {"status": "built", "pr": 5, "commit": sys.argv[2], "tests": []}, c
assert c["acceptance-b"] == {"status": "planned", "pr": None}, c
EOF
[[ "$(git diff --name-only "$before" HEAD)" == "$st" && "$(git rev-list --count "$before"..HEAD)" == 1 ]] \
  || fail "expected one commit touching only the status file"

# The judge launches from its own role file (agents/qc-judge.md), its model read from there: never code-reviewer.md.
run 0 argv $st 5 acceptance-a
judge="$(jr '["stdout"]')"
python3 - "$kit/agents/qc-judge.md" "$judge" <<'EOF' || fail "judge not launched from agents/qc-judge.md: ${judge:0:600}"
import json, os, re, sys
fm, body = re.match(r"---\n(.*?)\n---\n?(.*)", open(sys.argv[1]).read(), re.S).groups()
fm = dict(l.split(": ", 1) for l in fm.splitlines())
a = json.loads(next(l for l in sys.argv[2].splitlines() if l.startswith("ARGV "))[5:])
val = lambda f: [a[i + 1] for i, x in enumerate(a) if x == f]
assert val("--append-system-prompt") == [body.strip()], "role prompt is not qc-judge.md's body"
assert set(val("--model")) == {fm["model"]}, f"model {val('--model')} != {fm['model']}"
assert sorted(os.path.basename(s) for s in val("--skill")) == sorted(s.strip() for s in fm["skills"].split(",")), val("--skill")
EOF
echo "qc-judge: ok (--no-sandbox, killed run leaves no scratch, pass flips built, fail stays planned, status-only commit, judge from agents/qc-judge.md; offline, runs bounded)"
