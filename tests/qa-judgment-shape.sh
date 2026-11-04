#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape),
# driven as commands with a stub `pi` and a fake `herdr` first on PATH: no model, no live Herdr (tests/lib/qa.sh).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves: a judgment suite's shape names case and field: labeller record labelled_by/relabel,
# calibration (evidence file, held_out and threshold shape, judgment suites only), no suite names a model;
# judgment-model.json and classifiers.json shape (schema.md).
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
# shellcheck source=tests/lib/qa.sh
source "$(dirname "$0")/lib/qa.sh"
mk_jg
# The judgment shape (rule: schema.md, Judgment suite).
bad 'del e["t3"]["reason"]' "jb/reference/expectations.json case t3: field reason: missing" "$t/jg-good" jb
bad 'del e["t3"]["source"]' "jb/reference/expectations.json case t3: field source: missing" "$t/jg-good" jb
bad 'e["t3"]["label"] = "c"' "jb/reference/expectations.json case t3: field label: must be one of ['a', 'b'], got 'c'" "$t/jg-good" jb
bad 'e["t3"]["reason"] = "two\nlines"' "jb/reference/expectations.json case t3: field reason: must be one non-empty line" "$t/jg-good" jb
bad 'del c[2]["split"]' "jb/cases.json case t2: field split: missing" "$t/jg-good" jb
bad 'c[2]["label"] = "a"' "jb/cases.json case t2: field label: unknown field; label, reason and source live only" "$t/jg-good" jb
bad 'del c[0]; del e["t0"]' "jb/cases.json: 14 cases; a judgment set needs at least 15" "$t/jg-good" jb
bad 'c[:] = [dict(x, split="train") for x in c]' "jb/cases.json: no case in split held-out" "$t/jg-good" jb
# The labeller record, labelled_by and relabel, and an extra field (rule: schema.md, Judgment suite).
rm -rf "$t/evals"; cp -r "$t/jg-good" "$t/evals"
python3 -c "import json,sys; p=sys.argv[1]; e=json.load(open(p)); e['t3'].update(labelled_by='director', relabel='was b'); json.dump(e, open(p, 'w'))" \
  "$t/evals/jb/reference/expectations.json"
run 0 "$C" "$t/evals"
bad 'e["t3"]["labelled_by"] = " "' "jb/reference/expectations.json case t3: field labelled_by: must be one non-empty line" "$t/jg-good" jb
bad 'e["t3"]["relabel"] = "two\nlines"' "jb/reference/expectations.json case t3: field relabel: must be one non-empty line" "$t/jg-good" jb
bad 'e["t3"]["note"] = "x"' "jb/reference/expectations.json case t3: field note: unknown field" "$t/jg-good" jb
# A judgment suite's calibration (rule: schema.md, Calibration).
rm -rf "$t/evals"; cp -r "$t/jg-good" "$t/evals"
python3 -c "import json,sys; p=sys.argv[1]; s=json.load(open(p)); s['calibration']={'evidence': 'evidence/jb.md', 'held_out': {'accuracy': 0.5, 'brier': 0.6}, 'threshold': {'accuracy_min': 0.7, 'brier_max': 0.39, 'accepted': True}}; json.dump(s, open(p, 'w'))" \
  "$t/evals/jb/suite.json"
run 0 "$C" "$t/evals"
ok_cal='s["calibration"] = {"evidence": "evidence/jb.md", "held_out": {"accuracy": 1, "brier": 0}, "threshold": {"accuracy_min": 0.699, "brier_max": 2.403, "accepted": False}}'
bad "$ok_cal"'; s["calibration"]["why"] = "x"' "jb/suite.json: field calibration.why: unknown field" "$t/jg-good" jb
bad "$ok_cal"'; del s["calibration"]["evidence"]' "jb/suite.json: field calibration.evidence: missing" "$t/jg-good" jb
bad 's["calibration"] = "stub/p/q-1.2"' "jb/suite.json: field calibration: must be an object {evidence, held_out, threshold}" "$t/jg-good" jb
bad "$ok_cal"'; s["calibration"]["evidence"] = "evidence/none.md"' "jb/suite.json: field calibration.evidence: no file evidence/none.md beside evals/" "$t/jg-good" jb
bad "$ok_cal"'; s["calibration"]["evidence"] = "../evidence/jb.md"' "jb/suite.json: field calibration.evidence: must be a relative path inside the repo" "$t/jg-good" jb
# A model or chosen key in suite.json, nested and top-level (rule: schema.md, Suite).
one="a suite names no model; the kit's one judgment model is judgment-model.json"
bad "$ok_cal"'; s["calibration"]["model"] = "stub/first"' "jb/suite.json: field calibration.model: $one" "$t/jg-good" jb
bad "$ok_cal"'; s["calibration"]["held_out"]["model"] = "stub/first"' "jb/suite.json: field calibration.held_out.model: $one" "$t/jg-good" jb
bad 's["chosen"] = {"model": "stub/p/q-1.2", "evidence": "evidence/jb.md"}' "jb/suite.json: field chosen: $one" "$t/jg-good" jb
bad 's["model"] = "stub/first"' "jb/suite.json: field model: $one" "$t/jg-good" jb
# Its calibration record (copied from the evidence file); shape: .agents/skills/eval-cases/references/schema.md, Calibration.
for k in held_out threshold; do
  bad "$ok_cal"'; del s["calibration"]["'$k'"]' "jb/suite.json: field calibration.$k: missing" "$t/jg-good" jb
  bad "$ok_cal"'; s["calibration"]["'$k'"] = 0.7' "jb/suite.json: field calibration.$k: must be an object {" "$t/jg-good" jb
  bad "$ok_cal"'; s["calibration"]["'$k'"]["n"] = 7' "jb/suite.json: field calibration.$k.n: unknown field" "$t/jg-good" jb
done
for f in accuracy brier; do bad "$ok_cal"'; del s["calibration"]["held_out"]["'$f'"]' "jb/suite.json: field calibration.held_out.$f: missing" "$t/jg-good" jb; done
for f in accuracy_min brier_max accepted; do bad "$ok_cal"'; del s["calibration"]["threshold"]["'$f'"]' "jb/suite.json: field calibration.threshold.$f: missing" "$t/jg-good" jb; done
bad "$ok_cal"'; s["calibration"]["held_out"]["accuracy"] = 1.2' "jb/suite.json: field calibration.held_out.accuracy: must be a number from 0 to 1, got 1.2" "$t/jg-good" jb
bad "$ok_cal"'; s["calibration"]["held_out"]["accuracy"] = "0.9"' "jb/suite.json: field calibration.held_out.accuracy: must be a number from 0 to 1, got '0.9'" "$t/jg-good" jb
bad "$ok_cal"'; s["calibration"]["held_out"]["brier"] = 2.1' "jb/suite.json: field calibration.held_out.brier: must be a number from 0 to 2, got 2.1" "$t/jg-good" jb
bad "$ok_cal"'; s["calibration"]["threshold"]["accuracy_min"] = True' "jb/suite.json: field calibration.threshold.accuracy_min: must be a number from 0 to 1, got True" "$t/jg-good" jb
bad "$ok_cal"'; s["calibration"]["threshold"]["brier_max"] = -0.1' "jb/suite.json: field calibration.threshold.brier_max: must be a number from 0 up, got -0.1" "$t/jg-good" jb
bad "$ok_cal"'; s["calibration"]["threshold"]["accepted"] = "no"' "jb/suite.json: field calibration.threshold.accepted: must be true or false, got 'no'" "$t/jg-good" jb
bad 's["calibration"] = {"evidence": "evidence/jb.md"}' "trig/suite.json: field calibration: only in a judgment suite"
# The one place (EVALS/judgment-model.json, spec judgment#rule-one-model; shape: schema.md, Judgment model and classifiers).
badm() {   # badm PY_EDIT WANT: edit a fresh judgment copy's judgment-model.json (m), expect WANT
  rm -rf "$t/evals"; cp -r "$t/jg-good" "$t/evals"
  python3 -c 'import json,sys; p=sys.argv[1]; m=json.load(open(p)); exec(sys.argv[2]); json.dump(m, open(p, "w"))' "$t/evals/judgment-model.json" "$1"
  run 1 "$C" "$t/evals"; grep -qF "$2" <<< "$out" || fail "model file check missed: want '$2', got: $out"
}
rm -rf "$t/evals"; cp -r "$t/jg-good" "$t/evals"; rm "$t/evals/judgment-model.json"
run 1 "$C" "$t/evals"; grep -qF "$t/evals/judgment-model.json: missing; it holds the kit's one judgment model {model, evidence}" <<< "$out" || fail "no model file: $out"
badm 'del m["model"]' "judgment-model.json: field model: missing"
badm 'del m["evidence"]' "judgment-model.json: field evidence: missing"
badm 'm["why"] = "x"' "judgment-model.json: field why: unknown field"
for m in stub/~x/y stub/p/q-1.2:free; do
  badm 'm["model"] = "'"$m"'"' "judgment-model.json: field model: $m is a moving alias in classifiers.json (owner: stub ruling, tests/qa.sh)"
done
badm 'm["model"] = "stub/ynr"' "judgment-model.json: field model: stub/ynr is yes/no only in classifiers.json (ruling: stub yes/no ruling)"
badm 'm["model"] = "stub/cheap-total"' "judgment-model.json: field model: stub/cheap-total is not in classifiers.json pinned"
for m in stub/p/q-latest stub/m-current; do   # pinned ids named -latest and -current (rule: schema.md, Judgment model and classifiers)
  rm -rf "$t/evals"; cp -r "$t/jg-good" "$t/evals"
  python3 -c 'import json,sys; p=sys.argv[1]; m=json.load(open(p)); m["model"]=sys.argv[2]; json.dump(m, open(p, "w"))' "$t/evals/judgment-model.json" "$m"
  run 0 "$C" "$t/evals"
done
# classifiers.json shape (rule: schema.md, Judgment model and classifiers).
badc() {   # badc PY_EDIT WANT: edit a fresh judgment copy's classifiers.json (o), expect WANT
  rm -rf "$t/evals"; cp -r "$t/jg-good" "$t/evals"
  python3 -c 'import json,sys; p=sys.argv[1]; o=json.load(open(p)); exec(sys.argv[2]); json.dump(o, open(p, "w"))' "$t/evals/classifiers.json" "$1"
  run 1 "$C" "$t/evals"; grep -qF "$2" <<< "$out" || fail "classifiers check missed: want '$2', got: $out"
}
rm -rf "$t/evals"; cp -r "$t/jg-good" "$t/evals"; rm "$t/evals/classifiers.json"
run 1 "$C" "$t/evals"; grep -qF "$t/evals/classifiers.json: missing; it holds every catalogue classifier ruled" <<< "$out" || fail "no classifiers file: $out"
for k in owner moving_alias yes_no_only pinned; do badc 'del o["'$k'"]' "classifiers.json: field $k: missing"; done
badc 'o["why"] = "x"' "classifiers.json: field why: unknown field"
badc 'o["owner"] = " "' "classifiers.json: field owner: must be the ruling's source, one non-empty line"
badc 'o["pinned"]["stub"] = "r"' "classifiers.json: field pinned.stub: must be a classifier <provider>/<id>, got 'stub'"
badc 'o["pinned"]["stub/first"] = " "' "classifiers.json: field pinned.stub/first: must be its pinning ruling's source, one non-empty line"
badc 'o["pinned"] = list(o["pinned"])' "classifiers.json: field pinned: must be an object {<provider>/<id>: its ruling's source}"
badc 'o["moving_alias"] = "stub/~x/y"' "classifiers.json: field moving_alias: must be a list of classifier ids"
badc 'o["pinned"]["stub/~x/y"] = "r"' "classifiers.json: field pinned.stub/~x/y: stub/~x/y already listed in moving_alias"
badc 'o["moving_alias"].append("stub/~x/y")' "classifiers.json: field moving_alias[3]: stub/~x/y already listed in moving_alias"
badc 'o["yes_no_only"] = ["stub/ynr"]' "classifiers.json: field yes_no_only: must be an object {<provider>/<id>: {ruling, error, evidence}}"
badc 'o["yes_no_only"]["stub"] = o["yes_no_only"]["stub/ynr"]' "classifiers.json: field yes_no_only.stub: must be a classifier <provider>/<id>, got 'stub'"
badc 'o["yes_no_only"]["stub/~x/y"] = o["yes_no_only"]["stub/ynr"]' "classifiers.json: field yes_no_only.stub/~x/y: stub/~x/y already listed in moving_alias"
badc 'o["pinned"]["stub/ynr"] = "r"' "classifiers.json: field pinned.stub/ynr: stub/ynr already listed in yes_no_only"
badc 'o["yes_no_only"]["stub/ynr"] = "r"' "classifiers.json: field yes_no_only.stub/ynr: must be an object {ruling, error, evidence}, got 'r'"
for k in ruling error evidence; do
  badc 'del o["yes_no_only"]["stub/ynr"]["'$k'"]' "classifiers.json: field yes_no_only.stub/ynr.$k: missing"
  badc 'o["yes_no_only"]["stub/ynr"]["'$k'"] = " "' "classifiers.json: field yes_no_only.stub/ynr.$k: must be"
done
badc 'o["yes_no_only"]["stub/ynr"]["why"] = "x"' "classifiers.json: field yes_no_only.stub/ynr.why: unknown field"
for m in stub 'stub/' '/x' 'stub/a b' ''; do
  badm 'm["model"] = "'"$m"'"' "judgment-model.json: field model: must be a classifier <provider>/<id>, got '$m'"
done
badm 'm["evidence"] = "evidence/none.md"' "judgment-model.json: field evidence: no file evidence/none.md beside evals/"
echo "qa-judgment-shape: ok (judgment shape names case and field, labeller record labelled_by/relabel, calibration: evidence file, held_out and threshold shape, judgment suites only, no suite names a model; judgment-model.json and classifiers.json shape (schema.md))"
