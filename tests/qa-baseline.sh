#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals), driven as a command with a stub `pi` and a fake
# `herdr` first on PATH: no model, no live Herdr (tests/lib/qa.sh; its stub reports usage on each assistant message).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves spec quality#acceptance-qa-cost and quality#acceptance-qa-baseline through --runs and --baseline (what they
# do: octo-feather-qa --help): a case's time and tokens as mean and spread; a baseline kit where the case fails beside a
# current kit where it passes, in one run id, interleaved, with the difference; exit by the current kit; bad ref 64.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
# shellcheck source=tests/lib/qa.sh
source "$(dirname "$0")/lib/qa.sh"
# A throwaway kit repo (this kit's tracked files): c1 the implementer not listing tdd, c2 the head (as qa-kit-ref.sh).
gk() { git -C "$HOME/src/kit" -c user.name=t -c user.email=t@t.invalid -c commit.gpgsign=false -c core.hooksPath=/dev/null "$@"; }
mkdir -p "$HOME/src/kit"; (cd "$kit" && git ls-files -z | xargs -0 tar -cf - 2>/dev/null) | tar -xf - -C "$HOME/src/kit"
im="$HOME/src/kit/agents/implementer.md"; cp "$im" "$t/im.md"
sed 's/^skills:\(.*\), tdd,/skills:\1,/' "$t/im.md" > "$im"; ! grep -q '^skills:.*tdd' "$im" || fail "c1 still lists tdd"
gk init -q -b main; gk add -A; gk commit -qm c1; c1="$(gk rev-parse HEAD)"
cp "$t/im.md" "$im"; gk commit -qam c2; c2="$(gk rev-parse HEAD)"
K="$HOME/src/kit/scripts/octo-feather-qa"
last() { ls -dt "$t"/out/*/ | head -1; }

# Cost: two runs; the stub's runs 1 and 2 report 220 and 240 tokens (2 assistant messages before the read decides).
run 0 "$K" --evals "$t/evals" --case reads --runs 2
grep -q "^  cost trig/reads: time s [0-9.]* +/- [0-9.]*; tokens 230 +/- 14$" <<< "$out" || fail "no cost line with time and tokens mean +/- spread: $out"
python3 - "$(last)" <<'PY' || fail "cost fields wrong"
import json, sys
d = sys.argv[1]; r = json.load(open(f"{d}/trig/reads/result.json"))
assert [x["usage"]["total"] for x in r["runs"]] == [220, 240] and r["tokens"] == {"mean": 230, "stddev": 14.1421}, r
assert r["cost_usd"] == {"mean": 0.002, "stddev": 0.0} and set(r["time"]) == {"mean", "stddev"}, r
assert r["runs"][0]["facts"][0]["status"] == "pass" and "evidence" not in r["runs"][0]["facts"][0], r["runs"][0]
assert json.load(open(f"{d}/summary.json"))["cases"][0]["tokens"]["mean"] == 230
PY

# Baseline c1 (fails: no tdd) beside the head c2 (passes): one evaluation, runs interleaved, the table, exit 0.
run 0 "$K" --evals "$t/evals" --case reads --runs 2 --baseline "${c1:0:9}"
[[ "$(grep -c '^qa: run ' <<< "$out")" == 1 ]] && grep -q "; baseline kit $c1 (--baseline ${c1:0:9}), runs interleaved;" <<< "$out" \
  || fail "not one evaluation naming the baseline: $out"
[[ "$(grep -oE '^  (baseline|current) run [0-9]/2: (PASS|FAIL)' <<< "$out" | tr '\n' '|')" == \
   "  baseline run 1/2: FAIL|  current run 1/2: PASS|  baseline run 2/2: FAIL|  current run 2/2: PASS|" ]] || fail "runs not interleaved: $out"
line PASS reads | grep -q "^PASS trig/reads: 2/2 runs passed .*\[kit $c2\]$" || fail "current case line: $out"
grep -q "^  baseline FAIL trig/reads: 0/2 runs passed (pass rate 0.00, stddev 0.00); run 1: skill_read tdd: no load.* \[kit $c1\]$" <<< "$out" \
  || fail "baseline case line: $out"
want="  compare trig/reads: baseline kit ${c1:0:12} beside current kit ${c2:0:12}
               baseline             current              difference
    pass rate  0.00 +/- 0.00        1.00 +/- 0.00        +1.00"
grep -qF "$want" <<< "$out" || fail "no side by side table head: $out"
grep -qE "^    time s     [0-9.]+ \+/- [0-9.]+ +[0-9.]+ \+/- [0-9.]+ +[+-][0-9.]+$" <<< "$out" || fail "no time row: $out"
grep -qE "^    tokens     230 \+/- 14 +230 \+/- 14 +\+0$" <<< "$out" || fail "no tokens row: $out"
grep -qE "^    cost usd   0.0020 \+/- 0.0000 +0.0020 \+/- 0.0000 +\+0.0000$" <<< "$out" || fail "no cost row: $out"
python3 - "$(last)" "$c1" "$c2" <<'PY' || fail "baseline fields wrong"
import json, os, sys
d, c1, c2 = sys.argv[1:]; c = f"{d}/trig/reads"; r = json.load(open(f"{c}/result.json"))
for side, sha in (("baseline", c1), ("current", c2)):
    for k in (1, 2):
        x = json.load(open(f"{c}/{side}/run-{k}/result.json"))
        assert (x["config"], x["run"], x["kit_sha"]) == (side, k, sha), x
b = r["baseline"]
assert (r["verdict"], r["kit_sha"], b["verdict"], b["kit_sha"], b["pass_rate"]) == ("PASS", c2, "FAIL", c1, 0.0), r
assert [x["dir"] for x in b["runs"]] == ["baseline/run-1", "baseline/run-2"] and b["runs"][0]["facts"][0]["status"] == "fail", b["runs"]
assert r["delta"]["pass_rate"] == 1.0 and r["delta"]["tokens"] == 0.0, r["delta"]
s = json.load(open(f"{d}/summary.json"))
assert s["baseline"]["kit_sha"] == c1 and s["kit_sha"] == c2 and (s["passed"], s["total"]) == (1, 1), s
PY

# The exit status follows the current kit only: the change side c1 fails beside a passing baseline c2.
run 1 "$K" --evals "$t/evals" --case reads --kit-ref "$c1" --baseline "$c2"
line FAIL reads > /dev/null; grep -q "^  baseline PASS trig/reads: 1/1 runs passed" <<< "$out" || fail "reverse comparison: $out"
grep -q "^qa: 0/1 passed" <<< "$out" || fail "the baseline counted toward the result: $out"
# An unknown baseline: 64 before any run.
run 64 "$K" --evals "$t/evals" --case reads --baseline no-such-ref
grep -q "baseline no-such-ref: no such commit" <<< "$out" && ! grep -q "qa: run " <<< "$out" || fail "unknown baseline not refused: $out"
run 64 "$K" --evals "$t/evals" --baseline
echo "qa-baseline: ok (time and tokens mean +/- spread per case, baseline beside current in one interleaved evaluation with the difference, exit by the current kit, unknown baseline 64)"
