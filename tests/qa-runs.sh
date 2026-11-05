#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape),
# driven as commands with a stub `pi` and a fake `herdr` first on PATH: no model, no live Herdr (tests/lib/qa.sh).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves spec quality#acceptance-qa-repeats through --runs (what it does: octo-feather-qa --help): an alternating stub
# case, an every-run-passes case, run-<k> artifacts, result.json and summary.json fields, the default one run, a bad
# value, --help.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
# shellcheck source=tests/lib/qa.sh
source "$(dirname "$0")/lib/qa.sh"
# The trig suite plus alt, whose stub reads tdd on odd runs only (STUB-ALTERNATE).
cp -r "$t/good" "$t/alt"
python3 - "$t/alt/trig" <<'EOF'
import json, sys
d = sys.argv[1]; c = json.load(open(f"{d}/cases.json")); e = json.load(open(f"{d}/reference/expectations.json"))
c.append({"id": "alt", "role": "implementer", "fixture": "fx", "should_trigger": True, "split": "train",
          "task": "Build it. STUB-READ-TDD STUB-ALTERNATE"})
e["alt"] = {"facts": [{"fact": "skill_read", "skill": "tdd"}]}
json.dump(c, open(f"{d}/cases.json", "w")); json.dump(e, open(f"{d}/reference/expectations.json", "w"))
EOF

# Some runs pass, some fail: 2/3, FAIL, exit 1; each run's own line first, the failing run's facts named.
run 1 "$Q" --evals "$t/alt" --case alt --runs 3
grep -q "^qa: run .*: 1 case(s), 3 runs each; kit " <<< "$out" || fail "run header does not say the runs: $out"
for k in 1 3; do grep -q "^  run $k/3: PASS trig/alt: skill_read tdd: loaded at" <<< "$out" || fail "run $k: want an indented PASS line: $out"; done
grep -q "^  run 2/3: FAIL trig/alt: skill_read tdd: no load of tdd/SKILL.md" <<< "$out" || fail "run 2: want an indented FAIL line: $out"
line FAIL alt | grep -q "^FAIL trig/alt: 2/3 runs passed (pass rate 0.67, stddev 0.58); run 2: skill_read tdd: no load of tdd/SKILL.md.* \[kit [0-9a-f]\{40\}\]$" \
  || fail "alt: want FAIL with 2/3, pass rate, spread and run 2's fact: $out"
grep -q "^qa: 0/1 passed" <<< "$out" || fail "a case failing one run counted as passed: $out"
d="$(ls -dt "$t"/out/*/ | head -1)"
python3 - "$d" <<'EOF' || fail "runs artifacts or result fields wrong"
import json, os, sys
d = sys.argv[1]; c = f"{d}/trig/alt"
for k in (1, 2, 3):
    for f in ("prompt.md", "input.json", "transcript.jsonl", "sandbox.json", "grading.json", "result.json"):
        assert os.path.exists(f"{c}/run-{k}/{f}"), (k, f)
    r = json.load(open(f"{c}/run-{k}/result.json"))
    assert (r["run"], r["of"], r["verdict"]) == (k, 3, "FAIL" if k == 2 else "PASS"), r
    assert json.load(open(f"{c}/run-{k}/input.json"))["run"] == k
r = json.load(open(f"{c}/result.json"))
assert r["verdict"] == "FAIL" and (r["runs_passed"], r["pass_rate"], r["stddev"]) == (2, 0.6667, 0.5774), r
assert [(x["run"], x["dir"], x["verdict"]) for x in r["runs"]] == [(1, "run-1", "PASS"), (2, "run-2", "FAIL"), (3, "run-3", "PASS")], r["runs"]
assert {"suite", "id", "verdict", "deciding", "model", "seconds", "stop", "tool_calls", "kit_sha"} <= set(r), r
s = json.load(open(f"{d}/summary.json"))
assert (s["passed"], s["total"], s["runs"]) == (0, 1, 3) and s["cases"][0]["pass_rate"] == 0.6667, s
EOF

# Every run passes: PASS, 2/2, exit 0.
run 0 "$Q" --evals "$t/alt" --case reads --runs 2
line PASS reads | grep -q "^PASS trig/reads: 2/2 runs passed (pass rate 1.00, stddev 0.00); run 1: skill_read tdd: loaded at" \
  || fail "reads: want PASS 2/2: $out"

# One run (default): no run lines, artifacts in the case dir, result.json with one run.
run 0 "$Q" --evals "$t/alt" --case reads
! grep -q "^  run \|runs each\|runs passed" <<< "$out" || fail "one run printed run lines: $out"
d="$(ls -dt "$t"/out/*/ | head -1)"
python3 - "$d/trig/reads" <<'EOF' || fail "one run's result fields wrong"
import json, os, sys
c = sys.argv[1]; r = json.load(open(f"{c}/result.json"))
assert not os.path.exists(f"{c}/run-1") and "run" not in r, r
assert (r["verdict"], r["runs_passed"], r["pass_rate"], r["stddev"]) == ("PASS", 1, 1.0, 0.0) and [x["dir"] for x in r["runs"]] == ["."], r
EOF

# Usage: a bad value exits 64 before any run; --help documents it.
for v in 0 -1 two; do run 64 "$Q" --evals "$t/alt" --runs "$v"; grep -q "runs needs a positive integer" <<< "$out" && ! grep -q "qa: run " <<< "$out" || fail "--runs $v: $out"; done
run 64 "$Q" --evals "$t/alt" --runs
run 0 "$Q" --help; grep -q "^  --runs N  " <<< "$out" || fail "--help does not document --runs: $out"
echo "qa-runs: ok (--runs: 2/3 with pass rate and stddev FAILS exit 1, 2/2 PASSES exit 0, run-<k> artifacts, result.json and summary.json runs/pass_rate/stddev, one run unchanged, bad value 64, --help)"
