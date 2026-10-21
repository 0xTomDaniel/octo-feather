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

# A removed criterion needs a weakens call, an added one an adds call.
git -C "$r" checkout -q -- docs/specs; rm -f "$L"
perl -ni -e 'print unless /data-anchor="acceptance-b"/' "$d/demo.spec.html"
perl -0pi -e 's/,\s*"acceptance-b": \{[^}]*\}//' "$d/demo.status.json"
call clarifies acceptance-b acceptance-b >"$L"
run "$r"; want 1 "removed criterion, clarifies" "criterion acceptance-b removed since accepted_commit" "kind weakens"
call weakens acceptance-b acceptance-b >"$L"
run "$r"; want 0 "removed criterion, weakens"
git -C "$r" checkout -q -- docs/specs; rm -f "$L"
perl -pi -e 'print s/acceptance-b/acceptance-c/gr if /data-anchor="acceptance-b"/' "$d/demo.spec.html"
perl -0pi -e 's/("acceptance-b": \{[^}]*\})/$1, "acceptance-c": {"status": "planned", "pr": null}/' "$d/demo.status.json"
call clarifies acceptance-c acceptance-c >"$L"
run "$r"; want 1 "added criterion, clarifies" "criterion acceptance-c added since accepted_commit" "kind adds"
call adds acceptance-c acceptance-c >"$L"
run "$r"; want 0 "added criterion, adds"

# Each log rule fails naming file, line and fix.
git -C "$r" checkout -q -- docs/specs
bad() { { call clarifies acceptance-a acceptance-a; printf '%s\n' "$1"; } >"$L"; run "$r"; want 1 "$2" "demo.calls.jsonl:2: " "fix: " "$3"; }
bad '{"at": ' "bad JSON" "not a JSON object"
bad "$(call clarifies acceptance-a acceptance-a | perl -pe 's/"why": "y", //')" "missing field" "missing or empty field why"
bad "$(call clarifies acceptance-a acceptance-a | perl -pe 's/"supervisor"/"implementer"/')" "role" "role 'implementer'"
bad "$(call clarifies acceptance-a acceptance-a | perl -pe 's/: false/: true/')" "passes_as_written" "passes_as_written must be false"
bad "$(call tweaks acceptance-a acceptance-a)" "kind" "kind 'tweaks' is not one of"
bad "$(call clarifies acceptance-a acceptance-q)" "unknown criterion" "criterion acceptance-q is in neither"

# An accepted_commit missing from the repo is named.
perl -pi -e 's/"accepted_commit": "[0-9a-f]+"/"accepted_commit": "deadbee"/' "$d/demo.status.json"; rm -f "$L"
run "$r"; want 1 "missing accepted_commit" "accepted_commit deadbee is not in this repo" "fetch full history"
echo "spec-status: ok (good, bad, init, built; guard: unlogged, logged, denied, weakens, adds, log rules, missing commit)"
