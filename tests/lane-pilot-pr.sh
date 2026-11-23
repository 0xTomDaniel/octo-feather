#!/usr/bin/env bash
# gate: e2e
# criterion: issue-lifecycle#acceptance-pilot-pr
# End-to-end test of a lane's pilot recorded on its draft PR (the rule: issue-lifecycle #lanes, its pilot paragraph;
# #lanes-one-head), through the kit's commands only, offline: GitHub is the kit's fake gh (tests/fixtures/tracker-gh)
# over a local bare origin, the qc judge's classifier the stub tests/fixtures/classify-stub/pi. A scratch target
# whose qc.toml declares a passing demo for acceptance-a and a failing one for acceptance-b: octo-feather-integrate
# lands the pilot's worker branch on lane gh12 (head J), the lane is pushed and its draft PR opened, `just qc` names
# both criteria, its head pushed, and `octo-feather-lane verdict` posts the review verdict for J. Then the PR head is
# a status-only commit after J, marking acceptance-a built in that PR and acceptance-b planned, and the verdict
# comment names J. Needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh.
set -euo pipefail
unset OCTO_FEATHER_CHECK_RUN OCTO_FEATHER_QC_CLAIMS   # a test harness, as tests/qc-carry.sh
[[ "$(uname -s)" != Darwin ]] || { echo "lane-pilot-pr: skipped, not on macOS (the qc sandbox needs Linux; CI runs it)"; exit 77; }
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'chmod -R u+w "$t" 2>/dev/null; rm -rf "$t"' EXIT
t="$(cd "$t" && pwd -P)"
for d in data cache config; do v="MISE_${d^^}_DIR"; [[ -n "${!v:-}" ]] || export "$v=$(mise doctor --json | jq -r --arg d "$d" '.dirs[$d]')"; done
fail() { echo "lane-pilot-pr test: $*" >&2; exit 1; }
export HOME="$t/home" XDG_STATE_HOME="$t/state" TMPDIR="$t/tmp" FAKE_GH_STORE="$t/gh.json" GH_REPO=o/r
unset XDG_CONFIG_HOME XDG_CACHE_HOME GH_CONFIG_DIR HERDR_SESSION HERDR_SOCKET_PATH HERDR_BIN_PATH HERDR_ENV OCTO_FEATHER_QC_DIR
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
mkdir -p "$HOME" "$TMPDIR" "$t/qcpath" "$t/repo/docs/specs"
ln -s "$kit/tests/fixtures/classify-stub/pi" "$t/qcpath/pi"
export PATH="$kit/tests/fixtures/tracker-gh:$kit/scripts:$PATH" OCTO_FEATHER_QC_PATH="$t/qcpath"

# The target: main on a bare origin, its spec's two criteria planned, a demo each, its own one-recipe gate.
git init -q --bare "$t/origin.git"
cd "$t/repo"; git init -q -b main .; git remote add origin "$t/origin.git"
git commit -qm accepted --allow-empty
cp "$kit/tests/fixtures/spec-status/good/demo.spec.html" docs/specs/
git add -A; git commit -qm spec
octo-feather-spec-status init docs/specs/demo.spec.html "$(git rev-parse --short HEAD)" >/dev/null
printf 'format = 2\n[entry]\ncommand = "true"\n[services]\n[fixture]\n[values]\n%s%s' \
  '[demo."demo#acceptance-a"]'$'\n''command = "echo demo checks pass"'$'\n''covers = ["src"]'$'\n' \
  '[demo."demo#acceptance-b"]'$'\n''command = "echo demo checks fail >&2; exit 1"'$'\n''covers = ["src"]'$'\n' > qc.toml
printf 'check:\n    @echo own-gate ran\n' > justfile
git add -A; git commit -qm target; git push -q origin main
git worktree add -q -b gh12 "$t/lane"; git -C "$t/lane" push -q -u origin gh12
git worktree add -q -b gh12-pilot "$t/pilot" gh12
mkdir "$t/pilot/src"; echo pilot > "$t/pilot/src/app"; git -C "$t/pilot" add -A; git -C "$t/pilot" commit -qm "feat: pilot"

# The pilot integrated (J), the lane pushed, its draft PR opened.
out="$(octo-feather-integrate 12 gh12-pilot 2>&1)" || fail "integrate: $out"
cd "$t/lane"; J="$(git rev-parse HEAD)"; git push -q
printf 'Closes #12\n\n## Summary\n\npilot\n\n## Validation\n\njust check\n' > "$t/body"
url="$(gh pr create --draft --base main --head gh12 --title "gh12: pilot" --body-file "$t/body")" || fail "pr create"
PR="${url##*/}"

# just qc on the pilot's criteria at J, its status commit pushed; the review verdict for J posted.
set +e; out="$(timeout -k 5 300 just --justfile "$kit/justfile" qc docs/specs/demo.status.json "$PR" acceptance-a acceptance-b 2>&1)"; rc=$?; set -e
[[ "$rc" == 1 ]] || fail "qc: want exit 1 (acceptance-b fails), got $rc: $out"
git push -q
printf 'Findings: none blocking.\nChecks: none\nVerdict: clear\nRange: %s..%s\n' "$(git rev-parse origin/main)" "$J" > "$t/report"
out="$(octo-feather-lane verdict "$PR" "$J" "$t/report" 2>&1)" || fail "verdict: $out"

# The PR head H follows J by one commit changing only the status file: a built in this PR, b planned.
H="$(gh pr view "$PR" --json headRefOid | jq -r .headRefOid)"
[[ "$H" != "$J" && "$(git rev-parse "$H^")" == "$J" ]] || fail "PR head $H is not one commit after J $J"
[[ "$(git diff --name-only "$J" "$H")" == docs/specs/demo.status.json ]] || fail "H changes more than the status file: $(git diff --name-only "$J" "$H")"
git show "$H:docs/specs/demo.status.json" | jq -e --argjson pr "$PR" \
  '.criteria["acceptance-a"] | .status == "built" and .pr == $pr' >/dev/null || fail "acceptance-a not built in PR $PR: $(git show "$H:docs/specs/demo.status.json")"
git show "$H:docs/specs/demo.status.json" | jq -e '.criteria["acceptance-b"].status == "planned"' >/dev/null || fail "acceptance-b not planned"
body="$(gh pr view "$PR" --json comments | jq -r '.comments[] | select(.body | startswith("<!-- octo-feather-review-verdict -->")) | .body')"
for want in "Head: $J" "PR head: $H" "Verdict: clear"; do
  grep -qx "$want" <<<"$body" || fail "verdict comment lacks '$want' (J $J, PR head $H): $body"
done
echo "lane-pilot-pr: ok (pilot integrated at ${J:0:12}, draft PR #$PR, qc's status-only commit ${H:0:12} marks acceptance-a built in #$PR and acceptance-b planned, the review verdict names ${J:0:12}, the head it follows)"
