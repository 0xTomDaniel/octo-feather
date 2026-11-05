#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals), driven as a command with a stub `pi` and a fake
# `herdr` first on PATH: no model, no live Herdr (tests/lib/qa.sh).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves spec quality#acceptance-qa-analyst through the analysis and --analyze (rules: octo-feather-qa --help,
# Analysis): a stub comparison holding one case per flag, each flag on its case and fact, in output and summary.json;
# a run with no baseline; the rerun on a stored run dir, the same analysis, no Pi started.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
# shellcheck source=tests/lib/qa.sh
source "$(dirname "$0")/lib/qa.sh"
# A throwaway kit repo (this kit's tracked files): c1 the implementer not listing tdd, c2 the head (as qa-baseline.sh).
gk() { git -C "$HOME/src/kit" -c user.name=t -c user.email=t@t.invalid -c commit.gpgsign=false -c core.hooksPath=/dev/null "$@"; }
mkdir -p "$HOME/src/kit"; (cd "$kit" && git ls-files -z | xargs -0 tar -cf - 2>/dev/null) | tar -xf - -C "$HOME/src/kit"
im="$HOME/src/kit/agents/implementer.md"; cp "$im" "$t/im.md"
sed 's/^skills:\(.*\), tdd,/skills:\1,/' "$t/im.md" > "$im"; ! grep -q '^skills:.*tdd' "$im" || fail "c1 still lists tdd"
gk init -q -b main; gk add -A; gk commit -qm c1; c1="$(gk rev-parse HEAD)"
cp "$t/im.md" "$im"; gk commit -qam c2
K="$HOME/src/kit/scripts/octo-feather-qa"
# One case per flag. same: passes on both kits. facts: fails on c1 (no tdd) and passes on c2, its skill_not_read pull
# fact passing on both. alt: fails on c1, alternates on c2. costly: passes on both, 3 more messages' tokens on c2.
mkdir -p "$t/an/an/reference"; cp -r "$t/good/fixtures" "$t/an/"
echo '{"suite": "an", "kind": "role-transcript", "description": "stub analysis", "max_tool_calls": 10, "timeout_s": 60}' > "$t/an/an/suite.json"
echo "[$(ic same "Only look."), $(ic facts "Build it. STUB-READ-TDD"), $(ic alt "Build it. STUB-READ-TDD STUB-ALTERNATE"), $(ic costly "Only look. STUB-COSTLY")]" > "$t/an/an/cases.json"
nt='{"fact": "skill_not_read", "skill": "tdd"}'; rt='{"fact": "skill_read", "skill": "tdd"}'; np='{"fact": "skill_not_read", "skill": "pull"}'
echo "{\"same\": {\"facts\": [$nt]}, \"facts\": {\"facts\": [$rt, $np]}, \"alt\": {\"facts\": [$rt]}, \"costly\": {\"facts\": [$np]}}" > "$t/an/an/reference/expectations.json"
block() { sed -n '/^qa: analysis /,/^qa: [0-9]/p' <<< "$out" | grep -v '^qa: [0-9]'; }

run 1 "$K" --evals "$t/an" --runs 2 --baseline "$c1"
want="qa: analysis (deterministic, no model; rules: octo-feather-qa --help, --analyze):
  non-discriminating case an/same: every run on both kits passed
  non-discriminating fact an/facts: skill_not_read pull: pass in every run on both kits
  high variance an/alt: current kit pass rate 0.50 +/- 0.71
  cost tradeoff an/costly: pass rate 1.00 on both kits; tokens mean 230.0 to 575.0"
got="$(block)"; [[ "$got" == "$want" ]] || fail "analysis: want
$want
got
$got
in: $out"
d="$(ls -dt "$t"/out/*/ | head -1)"
python3 - "$d" <<'PY' || fail "summary.json analysis wrong"
import json, sys
a = json.load(open(f"{sys.argv[1]}/summary.json"))["analysis"]
assert a["threshold"] == 0.5, a
assert a["non_discriminating_cases"] == [{"case": "an/same", "pass_rate": 1.0}], a
assert a["non_discriminating_facts"] == [{"case": "an/facts", "fact": {"fact": "skill_not_read", "skill": "pull"}, "status": "pass"}], a
assert a["high_variance"] == [{"case": "an/alt", "kit": "current", "pass_rate": 0.5, "stddev": 0.7071}], a
assert a["cost_tradeoffs"] == [{"case": "an/costly", "pass_rate": 1.0, "tokens": {"baseline": 230.0, "current": 575.0}}], a
PY

# The rerun on the stored run dir: the same analysis, from summary.json alone; a poison pi first on PATH never starts.
mkdir -p "$t/poison"; printf '#!/bin/sh\ntouch %q\nexit 99\n' "$t/poison/ran" > "$t/poison/pi"; chmod +x "$t/poison/pi"
PATH="$t/poison:$PATH" run 0 "$K" --analyze "$d"
[[ "$(sed -n '/^qa: analysis /,$p' <<< "$out")" == "$want" ]] || fail "rerun: not the same analysis: $out"
[[ ! -e "$t/poison/ran" ]] && ! grep -q "qc sandbox" <<< "$out" || fail "rerun started pi or a sandbox: $out"
run 64 "$K" --analyze "$t/nowhere"
run 64 "$K" --analyze "$d" --runs 2

# No baseline: no comparison flags, high variance still.
run 1 "$K" --evals "$t/an" --runs 2 --case alt --case same
got="$(block)"; [[ "$got" == $'qa: analysis (deterministic, no model; rules: octo-feather-qa --help, --analyze):\n  high variance an/alt: pass rate 0.50 +/- 0.71' ]] \
  || fail "no baseline: want only high variance: $got"
echo "qa-analyst: ok (four flags on their case and fact in output and summary.json, no baseline: high variance only, --analyze reruns it with no pi)"
