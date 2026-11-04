#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape),
# driven as commands with a stub `pi` and a fake `herdr` first on PATH: no model, no live Herdr (tests/lib/qa.sh).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves: a judgment suite's bench (its extension command run for real by the stub pi under node, stub
# classifiers at the model registry): per classifier accuracy/calibration/cost train and held-out apart, classifiers.json
# lists applied (moving alias and yes/no only skipped, never called), unavailable named, the kit's model beside the best
# and its threshold, --classifier, best's tie-break, a kit model unscored fails, a dead bench command fails, its spend
# in the ledger and an unwritable ledger changes nothing.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
# shellcheck source=tests/lib/qa.sh
source "$(dirname "$0")/lib/qa.sh"
mk_jg
run 0 "$Q" --evals "$t/jg"
jl() { grep -qF -- "$1" <<< "$out" || fail "bench: no '$1' in: $out"; }
jl "bench jb: question q-ab, labels a, b; 15 cases (train 12, held-out 3); every answer is a model judgment"
jl "bench jb: classifiers available (12): stub/token, stub/first, stub/broken, stub/cheap-train, stub/cheap-total, stub/~x/y, stub/p/q-latest, stub/p/q-1.2, stub/x-latest:free, stub/p/q-1.2:free, stub/yesno, stub/ynr"
jl "bench jb: skipped: moving alias (3): stub/~x/y, stub/x-latest:free, stub/p/q-1.2:free; never called, ruling (classifiers.json owner): stub ruling, tests/qa.sh"
jl "bench jb: skipped: yes/no only stub/ynr; never called, ruling (classifiers.json yes_no_only): stub yes/no ruling; provider error (stub run): stub bool only (400)"
jl "bench jb: unclassified id (1): stub/cheap-total; benched (scored where it answered), in no list of classifiers.json"
# yesno, not listed, answers only bool questions (rule: schema.md, Bench, Unavailable); a question not a
# choice kills the stub run.
jl 'unavailable stub/yesno: listed but answered no case: Stub API error (400): {"message":"stub accepts only bool questions (question "q")"}'
! grep -E "^  stub/(yesno|ynr) |yes/no only stub/yesno|unavailable stub/ynr" <<< "$out" || fail "bench: a yes/no-only classifier scored, or skipped unlisted: $out"
[[ "$(grep -A7 '^TRAIN (12 cases' <<< "$out" | grep -E '^  stub/' | tr -s ' ')" == \
   $' stub/token 12/12 9 0.750 0.380 0.050 0.015000 0\n stub/cheap-total 12/12 6 0.500 1.000 0.500 0.024000 0\n stub/cheap-train 12/12 6 0.500 1.000 0.500 0.042000 0\n stub/first 12/12 6 0.500 1.000 0.500 0.015000 0\n stub/p/q-1.2 12/12 6 0.500 1.000 0.500 0.015000 0\n stub/p/q-latest 12/12 6 0.500 1.000 0.500 0.015000 0' ]] || fail "bench: train table wrong: $out"
[[ "$(grep -A7 '^HELD-OUT (3 cases' <<< "$out" | grep -E '^  stub/' | tr -s ' ')" == \
   $' stub/token 3/3 1 0.333 0.880 0.467 0.015000 0\n stub/cheap-total 3/3 1 0.333 1.333 0.667 0.024000 0\n stub/cheap-train 3/3 1 0.333 1.333 0.667 0.042000 0\n stub/first 3/3 1 0.333 1.333 0.667 0.015000 0\n stub/p/q-1.2 3/3 1 0.333 1.333 0.667 0.015000 0\n stub/p/q-latest 3/3 1 0.333 1.333 0.667 0.015000 0' ]] || fail "bench: held-out table wrong: $out"
# broken's provider error, over 400 characters (rule: schema.md, Bench, Unavailable).
grep -qxF "unavailable stub/broken: listed but answered no case: stub provider down $(printf 'x%.0s' {1..400}) end" <<< "$out" || fail "bench: broken's error not whole: $out"
# The kit's model (judgment-model.json: stub/first) beside the question's best-scoring classifier, token (schema.md, Bench).
[[ "$(grep -A3 '^KIT MODEL BESIDE THE BEST (best: highest train accuracy' <<< "$out" | tail -2 | tr -s ' ')" == \
   $' kit stub/first 0.500 1.000 0.333 1.333 0.015000\n best stub/token 0.750 0.380 0.333 0.880 0.015000' ]] || fail "bench: kit beside best wrong: $out"
jl "kit model stub/first (judgment-model.json): proposed threshold (for the director to accept; until met, the judge stays advisory): held-out accuracy >= 0.254 and held-out brier <= 1.591"
jl "held-out now: accuracy 0.333 (1/3 of 3), brier 1.333, ece 0.667: meets the proposed threshold"
! grep -q "^chosen" <<< "$out" || fail "bench: a per-question choice named: $out"
jl "DONE bench jb: kit model stub/first, best stub/token"
grep -q "qc sandbox: ok   live Herdr unreachable" <<< "$out" || fail "bench: not run in the qa sandbox: $out"
d="$(ls -dt "$t"/out/*/ | head -1)"
for f in input.json extension.js stdout.txt stderr.txt sandbox.json answers.json bench.json report.txt; do [[ -e "$d/jb/$f" ]] || fail "bench artifact $f missing"; done
! grep -q SECRET-REASON "$d/jb/input.json" "$d/jb/extension.js" "$d/jb/stdout.txt" || fail "bench: the expectations reached the classifier side"
python3 - "$d" <<'EOF' || fail "bench artifacts wrong"
import json, sys
d = sys.argv[1]
a = json.load(open(f"{d}/jb/answers.json"))
assert len(a["answers"]) == 120 and all(x["judgment"].startswith("model judgment") for x in a["answers"]), a["answers"][:2]
s = json.load(open(f"{d}/summary.json"))
assert s["benches"][0]["best"]["model"] == "stub/token" and s["benches"][0]["verdict"] == "DONE", s["benches"]
k = s["benches"][0]["kit_model"]
assert k["model"] == "stub/first" and k["scored"] and k["threshold"] == {"accuracy_min": 0.254, "brier_max": 1.591} and k["held_out"] == {"accuracy": 0.333, "brier": 1.333}, k
assert "choice" not in s["benches"][0], s["benches"][0]
b = json.load(open(f"{d}/jb/bench.json"))   # per-model cost and the run total (token, first, p/q-1.2, p/q-latest 0.015 each; cheap 0.042 + 0.024)
assert {m["model"]: round(m["cost_usd"], 6) for m in b["models"]}["stub/cheap-train"] == 0.042 and round(b["cost_usd"], 6) == 0.126, b
assert b["skipped"] == ["stub/~x/y", "stub/x-latest:free", "stub/p/q-1.2:free", "stub/ynr"] and {"stub/p/q-1.2", "stub/p/q-latest"} <= set(b["benched"]), b
assert b["skipped_yes_no_only"] == {"stub/ynr": {"ruling": "stub yes/no ruling", "error": "stub bool only (400)", "evidence": "stub run"}}, b
assert b["skipped_ruling"] == "stub ruling, tests/qa.sh" and b["unclassified"] == ["stub/cheap-total"] and "stub/cheap-total" in b["benched"], b
assert not set(b["skipped"]) & ({x["model"] for x in a["answers"]} | {m["model"] for m in b["models"]}), b
y = next(m for m in b["models"] if m["model"] == "stub/yesno")
assert "skipped_yes_no" not in b and not y["available"] and y["first_error"] == 'Stub API error (400): {"message":"stub accepts only bool questions (question "q")"}', (b, y)
# No agent: one pi, no tools, no chat model, no session; only the bench extension loaded.
argv = json.loads(open(f"{d}/jb/stdout.txt").readline())["argv"]
for x in ("--no-tools", "--no-extensions", "--no-session", "--no-skills", "--no-mcp"):
    assert x in argv, (x, argv)
assert "--model" not in argv and "--mode" not in argv and "--tools" not in argv, argv
assert argv[argv.index("-p") + 1].startswith("/octo-feather-bench "), argv
EOF
# spec spend#acceptance-spend-bench: 8 benched x 15 cases = 120 calls, $0.126 as bench.json above; broken and yesno (30)
# report no usage, the 90 others 1 in, 1 out each.
spend_row() { # TITLE KEY USD CALLS UNKNOWN IN OUT: that row under "By TITLE:" in `octo-feather-lane spend` (tests/spend-out)
  local r; r="$("$kit/tests/spend-out" row "$@" <<< "$spent")" || fail "spend: $r in: $spent"; }
spent="$("$kit/scripts/octo-feather-lane" spend)" || fail "spend failed: $spent"
grep -qF "Spend ledger: $HOME/.local/state/octo-feather/spend.jsonl (120 calls)" <<< "$spent" || fail "spend: not 120 calls: $spent"
spend_row purpose bench 0.126000 120 30 90 90
spend_row lane '(no lane)' 0.126000 120 30 90 90
spend_row 'day (UTC)' "$(date -u +%F)" 0.126000 120 30 90 90
spend_row model stub/cheap-train 0.042000 15 0 15 15
spend_row model stub/cheap-total 0.024000 15 0 15 15
spend_row model stub/token 0.015000 15 0 15 15
spend_row model stub/broken 0.000000 15 15 0 0
spend_row model stub/yesno 0.000000 15 15 0 0
# spec spend#rule-write-fails, a directory in the ledger's place: the same report and exit.
ledger="$HOME/.local/state/octo-feather/spend.jsonl"; mv "$ledger" "$t/ledger"; mkdir "$ledger"
run 0 "$Q" --evals "$t/jg"
mv "$(ls -dt "$t"/out/*/ | head -1)/jb/report.txt" "$t/report-unwritable"
rmdir "$ledger"; mv "$t/ledger" "$ledger"
cmp -s "$d/jb/report.txt" "$t/report-unwritable" || fail "spend: an unwritable ledger changed the bench report: $(diff "$d/jb/report.txt" "$t/report-unwritable")"
jl "DONE bench jb: kit model stub/first, best stub/token"
jl 'octo-feather-lane spend record: spend unrecorded (120 call(s), $0.126000 + 30 of unknown cost): cannot write '
run 0 "$Q" --evals "$t/jg" --classifier stub/first --classifier stub/nope
jl "bench jb: benched only --classifier stub/first, stub/nope (not available: stub/nope)"
jl "DONE bench jb: kit model stub/first, best stub/first"
# A --classifier naming a listed moving alias or yes/no only (rule: schema.md, Bench, Classes; a call kills the stub run).
run 0 "$Q" --evals "$t/jg" --classifier stub/p/q-latest --classifier stub/p/q-1.2:free --classifier stub/p/q-1.2 --classifier stub/ynr
jl "bench jb: benched only --classifier stub/p/q-latest, stub/p/q-1.2:free, stub/p/q-1.2, stub/ynr"
jl "bench jb: skipped: yes/no only stub/ynr; never called"
jl "bench jb: skipped: moving alias (1): stub/p/q-1.2:free; never called"
! grep -q "unclassified id" <<< "$out" || fail "bench: an unclassified flag with every benched id pinned: $out"
grep -qE "^  kit +stub/first +not scored: not benched$" <<< "$out" || fail "bench: kit model not benched not shown: $out"
jl "DONE bench jb: kit model stub/first not scored (not benched), best stub/p/q-1.2"
! grep -q "not available" <<< "$out" || fail "bench: a skipped alias named not available: $out"
python3 -c "import json,sys; b=json.load(open(sys.argv[1])); assert b['skipped'] == ['stub/p/q-1.2:free', 'stub/ynr'] and b['benched'] == ['stub/p/q-latest', 'stub/p/q-1.2'] and b['unclassified'] == [], b" \
  "$(ls -dt "$t"/out/*/ | head -1)/jb/bench.json" || fail "bench: --classifier aliases not recorded skipped"
# Best's tie-break (schema.md, Bench): cheap-train costs less on train, more in all.
run 0 "$Q" --evals "$t/jg" --classifier stub/cheap-total --classifier stub/cheap-train
jl "DONE bench jb: kit model stub/first not scored (not benched), best stub/cheap-train"
# The kit's model benched but unscored (schema.md, Bench: a bench FAILS) (broken: every case refused;
# yesno: cannot accept the question's form, every case refused).
echo '{"model": "stub/broken", "evidence": "evidence/jb.md"}' > "$t/jg/judgment-model.json"
run 1 "$Q" --evals "$t/jg"
jl "FAILED bench jb: the kit's judgment model stub/broken was not scored (answered 0 of 12 train cases, first error: stub provider down $(printf 'x%.0s' {1..400}) end)"
echo '{"model": "stub/yesno", "evidence": "evidence/jb.md"}' > "$t/jg/judgment-model.json"
run 1 "$Q" --evals "$t/jg" --classifier stub/yesno --classifier stub/first
jl "FAILED bench jb: the kit's judgment model stub/yesno was not scored (answered 0 of 12 train cases, first error: Stub API error (400): "
cp "$t/jg-good/judgment-model.json" "$t/jg/judgment-model.json"
# A classifier that answers some cases (rule: schema.md, Bench, Unavailable): first refuses a
# STUB-REFUSE state.
python3 -c "import json,sys; p=sys.argv[1]; c=json.load(open(p)); c[0]['state'] += ' STUB-REFUSE'; json.dump(c, open(p, 'w'))" "$t/jg/jb/cases.json"
run 1 "$Q" --evals "$t/jg" --classifier stub/first
grep -A3 '^TRAIN (12 cases' <<< "$out" | grep -qE '^  stub/first +11/12 ' || fail "bench: a partly answering classifier not scored: $out"
jl "errors stub/first: 1 case(s) unanswered, first: stub refused this state"
! grep -q "unavailable stub/first" <<< "$out" || fail "bench: a partly answering classifier listed unavailable: $out"
cp "$t/jg-good/jb/cases.json" "$t/jg/jb/cases.json"
# A pi that dies before the command prints its result: the bench fails, naming it.
python3 -c "import json,sys; p=sys.argv[1]; c=json.load(open(p)); c[0]['state'] += ' STUB-DIE'; json.dump(c, open(p, 'w'))" "$t/jg/jb/cases.json"
run 1 "$Q" --evals "$t/jg" --classifier stub/first
jl "FAILED bench jb: the bench command printed no bench result:"
jl "(pi exit 3)"
echo "qa-bench: ok (judgment bench: per classifier accuracy/calibration/cost train and held-out apart, classifiers.json lists applied (schema.md, Bench; catalogue and --classifier; moving alias and yes/no only skipped, never called), a classifier that cannot accept the question's form listed unavailable with the real question's provider error (no probe), one answering some cases scored, unavailable named, the kit's model beside the best (train) and its threshold, --classifier, best's tie-break, a kit model unscored fails, a dead bench command fails, spend recorded)"
