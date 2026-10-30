#!/usr/bin/env bash
# Integration test for scripts/octo-feather-spec-status: one good and one bad
# fixture (tests/fixtures/spec-status/), then init and built on a copy, then the
# call log and the guard on a spec changed since its accepted commit
# (issue-lifecycle #gates-spec-calls). Each runs in a throwaway git repo whose
# accepted_commit is real. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
S="$kit/scripts/octo-feather-spec-status"; F="$kit/tests/fixtures/spec-status"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
fail() { echo "spec-status test: $*" >&2; exit 1; }
# repo NAME FIXTURE: a git repo holding FIXTURE's files in docs/specs, committed; accepted_commit names that commit.
repo() {
  local r="$t/$1"; mkdir -p "$r/docs/specs"; cp "$F/$2"/* "$r/docs/specs/"
  git init -q "$r"; git -C "$r" add -A; git -C "$r" commit -qm accepted
  local sha; sha="$(git -C "$r" rev-parse --short HEAD)"
  perl -pi -e "s/0123abc/$sha/" "$r"/docs/specs/*.status.json; git -C "$r" commit -qam status
}
run() { set +e; out="$("$S" check "$1/docs/specs" 2>&1)"; rc=$?; set -e; }
want() { [[ "$rc" == "$1" ]] || fail "$2: exit $rc, want $1: $out"; shift 2
  for w in "$@"; do grep -qF -- "$w" <<<"$out" || fail "did not report: $w"$'\n'"$out"; done; }

repo good good
"$S" check "$t/good/docs/specs" >/dev/null || fail "good fixture failed"
repo bad bad
run "$t/bad"
[[ "$rc" == 1 ]] || fail "bad fixture passed"
for w in "missing criterion acceptance-b" "extra criterion acceptance-z" "duplicate key 'acceptance-a'" \
         "duplicate criterion id acceptance-c" "status must be planned or built" "a built criterion names the PR"; do
  grep -qF "$w" <<<"$out" || fail "bad fixture did not report: $w"$'\n'"$out"
done
i="$t/init"; mkdir -p "$i"; cp "$F/good/demo.spec.html" "$i/"
git init -q "$i"; git -C "$i" add -A; git -C "$i" commit -qm spec
"$S" init "$i/demo.spec.html" "$(git -C "$i" rev-parse HEAD)" >/dev/null
"$S" built "$i/demo.status.json" 7 acceptance-a
"$S" check "$i" >/dev/null || fail "init + built produced a bad file"
grep -q '"pr": 7' "$i/demo.status.json" || fail "built did not record the PR"

# Guard: an anchored paragraph changed since accepted_commit with no call fails, naming spec and anchor.
r="$t/guard"; repo guard good; d="$r/docs/specs"; L="$d/demo.calls.jsonl"
perl -pi -e 's/then it prints ok\.(<\/span><\/p>)$/then it prints done.$1/ if /acceptance-a/' "$d/demo.spec.html"
run "$r"; want 1 "unlogged change" "demo.spec.html: anchor acceptance-a changed since accepted_commit" "calls.jsonl"
call() { # call KIND ANCHOR CRITERION [EXTRA_JSON]
  printf '{"at": "2026-10-21T10:00:00Z", "lane": "gh62", "role": "supervisor", "kind": "%s", "anchors": ["%s"], "criteria": ["%s"], "what": "w", "why": "y", "passes_as_written": false, "evidence": "e"%s}\n' "$1" "$2" "$3" "${4:-}"; }
call clarifies acceptance-a acceptance-a >"$L"
run "$r"; want 0 "logged change"
call clarifies acceptance-a acceptance-a ', "denied": {"at": "2026-10-21T11:00:00Z", "note": "no"}' >"$L"
run "$r"; want 1 "denied call" "anchor acceptance-a changed"

# A removed criterion needs a weakens call, an added one an adds call; its parent section changed too.
git -C "$r" checkout -q -- docs/specs; rm -f "$L"
perl -ni -e 'print unless /data-anchor="acceptance-b"/' "$d/demo.spec.html"
perl -0pi -e 's/,\s*"acceptance-b": \{[^}]*\}//' "$d/demo.status.json"
call clarifies acceptance-b acceptance-b >"$L"
run "$r"; want 1 "removed criterion, clarifies" "criterion acceptance-b removed since accepted_commit" "kind weakens"
call weakens 'acceptance-b", "acceptance' acceptance-b >"$L"
run "$r"; want 0 "removed criterion, weakens"
git -C "$r" checkout -q -- docs/specs; rm -f "$L"
perl -pi -e 'print s/acceptance-b/acceptance-c/gr if /data-anchor="acceptance-b"/' "$d/demo.spec.html"
perl -0pi -e 's/("acceptance-b": \{[^}]*\})/$1, "acceptance-c": {"status": "planned", "pr": null}/' "$d/demo.status.json"
call clarifies acceptance-c acceptance-c >"$L"
run "$r"; want 1 "added criterion, clarifies" "criterion acceptance-c added since accepted_commit" "kind adds"
call adds 'acceptance-c", "acceptance' acceptance-c >"$L"
run "$r"; want 0 "added criterion, adds"

# Each log rule fails naming file, line and fix.
git -C "$r" checkout -q -- docs/specs
bad() { { call clarifies acceptance-a acceptance-a; printf '%s\n' "$1"; } >"$L"; run "$r"; want 1 "$2" "demo.calls.jsonl:2: " "fix: " "$3"; }
bad '{"at": ' "bad JSON" "not a JSON object"
bad "$(call clarifies acceptance-a acceptance-a | perl -pe 's/"why": "y", //')" "missing field" "missing or empty field why"
# #acceptance-call-evidence: an empty or missing evidence fails, naming that call (line 2, lane gh77, its anchors).
bad "$(call clarifies acceptance-a acceptance-a | perl -pe 's/gh62/gh77/; s/"evidence": "e"/"evidence": ""/')" \
  "empty evidence" "demo.calls.jsonl:2: call (lane gh77; anchors acceptance-a): missing or empty field evidence"
bad "$(call clarifies acceptance-a acceptance-a | perl -pe 's/gh62/gh77/; s/, "evidence": "e"//')" \
  "missing evidence" "demo.calls.jsonl:2: call (lane gh77; anchors acceptance-a): missing or empty field evidence"
# Whitespace-only counts as empty, for evidence and every other required string.
bad "$(call clarifies acceptance-a acceptance-a | perl -pe 's/gh62/gh77/; s/"evidence": "e"/"evidence": "  \\n\\t"/')" \
  "blank evidence" "demo.calls.jsonl:2: call (lane gh77; anchors acceptance-a): missing or empty field evidence"
bad "$(call clarifies acceptance-a acceptance-a | perl -pe 's/"what": "w"/"what": " \\t"/')" "blank what" "missing or empty field what"
bad "$(call clarifies ' ' acceptance-a)" "blank anchor" "missing or empty field anchors"
bad "$(call clarifies acceptance-a acceptance-a | perl -pe 's/"supervisor"/"implementer"/')" "role" "role 'implementer'"
bad "$(call clarifies acceptance-a acceptance-a | perl -pe 's/: false/: true/')" "passes_as_written" "passes_as_written must be false"
bad "$(call tweaks acceptance-a acceptance-a)" "kind" "kind 'tweaks' is not one of"
bad "$(call clarifies acceptance-a acceptance-q)" "unknown criterion" "criterion acceptance-q is in neither"
# lane is a lane key of either tracker (roles spec #lane-key): eng-123 passes like gh62; a ticket as written,
# or a key with a suffix, is no lane key.
call clarifies acceptance-a acceptance-a | perl -pe 's/gh62/eng-123/' >"$L"; run "$r"; want 0 "Linear lane key"
for l in ENG-123 62 gh62-x eng-123-x; do
  bad "$(call clarifies acceptance-a acceptance-a | perl -pe "s/gh62/$l/")" "lane $l" "lane '$l' is not a lane key"
done

# #acceptance-call-guard, structure: moving an unchanged criterion between anchored sections, or
# reordering two anchored siblings, changes the parents, so it needs a call naming them.
m="$t/move"; mkdir -p "$m/docs/specs"; md="$m/docs/specs"; ML="$md/demo.calls.jsonl"
crit() { printf '<p data-acceptance-criterion data-anchor="%s">Given a user, When %s runs, then it prints ok.</p>\n' "$1" "$1"; }
mspec() { # mspec REQUIRED_CRITERIA... -- OPTIONAL_CRITERIA...
  printf '<!doctype html>\n<html><body><article data-spec-contract="shaped-sections-v1">\n'
  printf '<section data-anchor="acceptance-required"><h2>Required</h2>\n'
  while [[ $# -gt 0 && "$1" != -- ]]; do crit "$1"; shift; done; shift
  printf '</section>\n<section data-anchor="acceptance-optional"><h2>Optional</h2>\n'
  for c in "$@"; do crit "$c"; done
  printf '</section>\n</article></body></html>\n'; }
mspec acceptance-a acceptance-b -- >"$md/demo.spec.html"
git init -q "$m"; git -C "$m" add -A; git -C "$m" commit -qm accepted
printf '{"spec": "demo.spec.html", "accepted_commit": "%s", "criteria": {"acceptance-a": {"status": "planned", "pr": null}, "acceptance-b": {"status": "planned", "pr": null}}}\n' \
  "$(git -C "$m" rev-parse --short HEAD)" >"$md/demo.status.json"; git -C "$m" add -A; git -C "$m" commit -qm status
run "$m"; want 0 "structured spec unchanged"
mspec acceptance-b -- acceptance-a >"$md/demo.spec.html"
run "$m"; want 1 "moved criterion, no call" "anchor acceptance-optional changed since accepted_commit" \
  "anchor acceptance-required changed since accepted_commit"
grep -qF "anchor acceptance-a " <<<"$out" && fail "unchanged moved criterion reported as changed: $out"
call clarifies 'acceptance-required", "acceptance-optional' acceptance-a >"$ML"
run "$m"; want 0 "moved criterion, call names both sections"
rm -f "$ML"; mspec acceptance-b acceptance-a -- >"$md/demo.spec.html"
run "$m"; want 1 "reordered siblings, no call" "anchor acceptance-required changed since accepted_commit"
call clarifies acceptance-required acceptance-a >"$ML"
run "$m"; want 0 "reordered siblings, call names the parent"

# An accepted_commit missing from the repo is named.
perl -pi -e 's/"accepted_commit": "[0-9a-f]+"/"accepted_commit": "deadbee"/' "$d/demo.status.json"; rm -f "$L"
run "$r"; want 1 "missing accepted_commit" "accepted_commit deadbee is not in this repo" "fetch full history"
# `calls` (#acceptance-call-listed, -added, -weakens, -many, -denied): the lane's calls since its
# base, grouped weakens, adds, clarifies as #gates-call-loudness orders them; a call already
# at the base is not the lane's, even once denied; a fourth call prints the more-than-three line.
c="$t/calls"; repo calls good; cs="$c/docs/specs"; CL="$cs/demo.calls.jsonl"
lcall() { # lcall KIND WHAT LANE [EXTRA_JSON]
  printf '{"at": "2026-10-21T10:00:00Z", "lane": "%s", "role": "supervisor", "kind": "%s", "anchors": ["acceptance-a"], "criteria": ["acceptance-a"], "what": "%s", "why": "why-%s", "passes_as_written": false, "evidence": "ev-%s"%s}\n' \
    "$3" "$1" "$2" "$2" "$2" "${4:-}"; }
lcall clarifies old-call gh50 >"$CL"; git -C "$c" add -A; git -C "$c" commit -qm "earlier lane"
base="$(git -C "$c" rev-parse HEAD)"
list() { set +e; out="$(cd "$c" && "$S" calls "$@" 2>&1)"; rc=$?; set -e; }
line() { grep -nF -- "$1" <<<"$out" | head -1 | cut -d: -f1; }
{ perl -pe 's/\}$/, "denied": {"at": "2026-10-22T09:00:00Z", "note": "old"}}/' "$CL"
  lcall clarifies what-clar gh63
  lcall adds what-add gh63
  lcall weakens what-weak gh63 ', "denied": {"at": "2026-10-22T10:00:00Z", "note": "keep it"}'; } >"$CL.new"; mv "$CL.new" "$CL"
list --since "$base" docs/specs; want 0 "calls listing" "3 calls (1 weakens, 1 adds, 1 clarifies; 1 denied)." \
  "weakens DENIED (2026-10-22T10:00:00Z: keep it): docs/specs/demo.spec.html, lane gh63, role supervisor" \
  "   why: why-what-weak" "   evidence: ev-what-add" "   anchors: acceptance-a" "   criteria: acceptance-a"
grep -qF old-call <<<"$out" && fail "a call at the base was listed: $out"
grep -qF "more than three" <<<"$out" && fail "three calls printed the more-than-three line: $out"
prev=0; for w in "Weakens or removes" what-weak "Adds scope" what-add "Clarifies or adds detail" what-clar; do
  n="$(line "$w")"; [[ -n "$n" && "$n" -gt "$prev" ]] || fail "calls not grouped weakens, adds, clarifies at '$w': $out"; prev="$n"; done
lcall clarifies what-four gh63 >>"$CL"
list --since "$base"; want 0 "fourth call" "4 calls" "Lane gh63 made 4 calls, more than three: the director tells the owner"
# Default base: the merge base with origin/main; none is an error naming the fix.
list; want 1 "no origin/main" "no merge base with origin/main" "--since REF"
git -C "$c" update-ref refs/remotes/origin/main "$base"
list; want 0 "default base" "4 calls"

# Evidence links (quality #qc-results, #acceptance-built-links): built names its record, the commit it was captured at
# and its demo's tests; check accepts that shape and a legacy built row, and refuses a partial or malformed link.
# Staleness (#qc-stale, #acceptance-evidence-stale): `show` names each built criterion current or stale.
e="$t/stale"; mkdir -p "$e/docs/specs" "$e/src" "$e/tests"; es="$e/docs/specs"; ES="$es/demo.status.json"
cp "$F/good/demo.spec.html" "$es/"
printf 'format = 1\n[entry]\ncommand = "true"\n[services]\n[fixture]\n[values]\n[demo."demo#acceptance-a"]\ncommand = "true"\ncovers = ["src/a"]\ntests = ["tests/a.sh"]\n[demo."demo#acceptance-b"]\ncommand = "true"\ncovers = ["src/b"]\ntests = ["tests/b.py::test_b"]\n' >"$e/qc.toml"
for f in src/a src/b tests/a.sh tests/b.py README; do echo "$f v1" >"$e/$f"; done
git init -q "$e"; git -C "$e" add -A; git -C "$e" commit -qm accepted
cap="$(git -C "$e" rev-parse HEAD)"
"$S" init "$es/demo.spec.html" "$cap" >/dev/null
"$S" built "$ES" 7 acceptance-a --record 20261029T100000Z-0a0a0a0a --commit "$cap" --test tests/a.sh
"$S" built "$ES" 7 acceptance-b --record 20261029T100000Z-0b0b0b0b --commit "$cap" --test tests/b.py::test_b
git -C "$e" add -A; git -C "$e" commit -qm "qc: built acceptance-a acceptance-b (judged ${cap:0:12})"
python3 - "$ES" "$cap" <<'EOF' || fail "built did not write the evidence link: $(cat "$ES")"
import json, sys
c = json.load(open(sys.argv[1]))["criteria"]
assert c["acceptance-a"] == {"status": "built", "pr": 7, "record": "20261029T100000Z-0a0a0a0a", "commit": sys.argv[2], "tests": ["tests/a.sh"]}, c
EOF
run "$e"; want 0 "built with an evidence link"
show() { set +e; out="$(cd "$e" && "$S" show 2>&1)"; rc=$?; set -e; }
crit_line() { grep -F -- "  $1: " <<<"$out" || fail "show: no line for $1: $out"; }
show; want 0 "show, nothing changed" "acceptance-a: built (PR #7), current: record 20261029T100000Z-0a0a0a0a captured at ${cap:0:12}"
crit_line acceptance-b | grep -qF "current" || fail "acceptance-b not current: $out"
echo v2 >"$e/README"; git -C "$e" commit -qam "unrelated change"
echo v2 >"$e/src/a"; git -C "$e" commit -qam "change a's code"; ch="$(git -C "$e" rev-parse --short=12 HEAD)"
show; want 0 "covered path changed" \
  "acceptance-a: built (PR #7), STALE: record 20261029T100000Z-0a0a0a0a captured at ${cap:0:12}; covered path src/a changed since ${cap:0:12} by $ch change a's code"
crit_line acceptance-b | grep -qF ", current: " || fail "an unrelated change made acceptance-b stale: $out"
grep -qF "2 built: 1 current, 1 stale, 0 no evidence link" <<<"$out" || fail "show summary: $out"
# A named test file edited or gone since capture makes it stale (owner ruling #409: the selector maps to its file).
echo v2 >"$e/tests/a.sh"; git -C "$e" commit -qam "edit a's test"; ta="$(git -C "$e" rev-parse --short=12 HEAD)"
show; crit_line acceptance-a | grep -qF "; test file tests/a.sh changed since ${cap:0:12} by $ta edit a's test" \
  || fail "edited test file not stale: $out"
git -C "$e" rm -q tests/b.py; git -C "$e" commit -qm "drop b's test"; tb="$(git -C "$e" rev-parse --short=12 HEAD)"
show; crit_line acceptance-b | grep -qF "STALE: record 20261029T100000Z-0b0b0b0b captured at ${cap:0:12}; test file tests/b.py (tests/b.py::test_b) gone since ${cap:0:12} by $tb drop b's test" \
  || fail "gone test not stale: $out"
git -C "$e" checkout -q "$cap" -- tests/b.py; git -C "$e" commit -qm "b's test back"
perl -pi -e 's/then it prints ok\./then it prints done./ if /acceptance-b/' "$es/demo.spec.html"
show; crit_line acceptance-b | grep -qF "STALE: record 20261029T100000Z-0b0b0b0b captured at ${cap:0:12}; criterion text changed since ${cap:0:12}" \
  || fail "changed text not stale: $out"
git -C "$e" checkout -q -- docs/specs
# A fallback-built criterion (record, no declared demo): no covers or tests, so only its text makes it stale.
perl -0pi -e 's/\[demo."demo#acceptance-b"\].*//s' "$e/qc.toml"; git -C "$e" commit -qam "no demo for b"; fb="$(git -C "$e" rev-parse HEAD)"
"$S" built "$ES" 7 acceptance-b --record 20261029T100000Z-0c0c0c0c --commit "$fb"; git -C "$e" commit -qam "qc: built acceptance-b (judged ${fb:0:12})"
echo v3 >"$e/src/b"; git -C "$e" commit -qam "change b's code"
show; crit_line acceptance-b | grep -qF "current: record 20261029T100000Z-0c0c0c0c captured at ${fb:0:12} by the agent fallback" \
  || fail "fallback-built not current: $out"
# A legacy built row (status and PR only) passes check and shows as no evidence link, never stale.
"$S" built "$ES" 7 acceptance-b; run "$e"; want 0 "legacy built row"
show; crit_line acceptance-b | grep -qF "acceptance-b: built (PR #7), no evidence link" || fail "legacy row: $out"
grep -qF "2 built: 0 current, 1 stale, 1 no evidence link" <<<"$out" || fail "show summary: $out"
# check refuses a partial or malformed link, and a planned criterion with one.
link() { perl -0pi -e "s/\"acceptance-b\": \\{[^}]*\\}/\"acceptance-b\": $1/" "$ES"; run "$e"; want 1 "$2" "demo.status.json: acceptance-b: $3"; git -C "$e" checkout -q -- docs/specs; }
link '{"status": "built", "pr": 7, "record": "20261029T100000Z-0a0a0a0a"}' "partial link" "names record without commit, tests"
link "{\"status\": \"built\", \"pr\": 7, \"record\": \"r1\", \"commit\": \"$cap\", \"tests\": []}" "bad record" "record must be an evidence record id"
link '{"status": "built", "pr": 7, "record": "20261029T100000Z-0a0a0a0a", "commit": "HEAD", "tests": []}' "bad commit" "commit must be a commit sha"
link "{\"status\": \"built\", \"pr\": 7, \"record\": \"20261029T100000Z-0a0a0a0a\", \"commit\": \"$cap\", \"tests\": \"t\"}" "bad tests" "tests must be a list"
link "{\"status\": \"planned\", \"pr\": null, \"record\": \"20261029T100000Z-0a0a0a0a\", \"commit\": \"$cap\", \"tests\": []}" "planned with a link" "a planned criterion names no evidence"

echo "spec-status: ok (good, bad, init, built, evidence links, show current and stale; guard: unlogged, logged, denied, weakens, adds, log rules, evidence, blank fields, move, reorder, missing commit; calls: grouped, denied, base, more than three)"
