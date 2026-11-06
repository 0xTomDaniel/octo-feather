#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape),
# driven as commands with a stub `pi` and a fake `herdr` first on PATH: no model, no live Herdr (tests/lib/qa.sh).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves: --kit-ref runs a case against an earlier kit commit (FAIL before and PASS at a kit change, with its
# sha; a missing role file named; an unknown ref 64), its kit copy built from tracked files only; other repos under HOME and
# the --kit-ref head kit masked (attempt_blocked repo).
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
# shellcheck source=tests/lib/qa.sh
source "$(dirname "$0")/lib/qa.sh"
# --kit-ref: the same case against an earlier kit commit. A throwaway kit repo (this kit's tree) whose history
# is c0 no implementer role, c1 the implementer not listing tdd, c2 the head; cases and grader stay the head's.
# It lives under HOME, so a --kit-ref run masks it but for the sandbox's machinery (scripts/octo-feather-qc-sandbox, 3b).
# Tracked files only, as the other kit-copy tests: the live tree's .venv, node_modules and caches change under a
# parallel gate, and tar failed reading them (#506).
gk() { git -C "$HOME/src/kit" -c user.name=t -c user.email=t@t.invalid -c commit.gpgsign=false -c core.hooksPath=/dev/null "$@"; }
mkdir -p "$HOME/src/kit"; (cd "$kit" && git ls-files -z | xargs -0 tar -cf - 2>/dev/null) | tar -xf - -C "$HOME/src/kit"
im="$HOME/src/kit/agents/implementer.md"; cp "$im" "$t/im.md"
gk init -q -b main; rm "$im"; gk add -A; gk commit -qm c0; c0="$(gk rev-parse HEAD)"
sed 's/^skills:\(.*\), tdd,/skills:\1,/' "$t/im.md" > "$im"; grep -q '^skills:' "$im" && ! grep -q '^skills:.*tdd' "$im" || fail "c1 still lists tdd"
gk add -A; gk commit -qm c1; c1="$(gk rev-parse HEAD)"
cp "$t/im.md" "$im"; gk commit -qam c2; c2="$(gk rev-parse HEAD)"
ln -s "$kit/node_modules" "$HOME/src/kit/node_modules" && echo /node_modules >> "$HOME/src/kit/.git/info/exclude"   # srt, the qc sandbox, runs from the running kit's node_modules
K="$HOME/src/kit/scripts/octo-feather-qa"
run 1 "$K" --evals "$t/evals" --case reads --kit-ref "${c1:0:9}"
line FAIL reads | grep -q "skill_read tdd: no load of tdd/SKILL.md.*\[kit $c1\]" || fail "kit-ref before the change: want FAIL with its sha: $out"
grep -q "ok   extra binds read-only" <<< "$out" || fail "the earlier kit is not bound read-only in the sandbox: $out"
d="$(ls -dt "$t"/out/*/ | head -1)"
python3 - "$d/trig/reads" "$c1" <<'EOF' || fail "kit-ref artifacts wrong"
import json, sys
c, sha = sys.argv[1:]
argv = json.loads(open(f"{c}/transcript.jsonl").readline())["argv"]
sk = [argv[i + 1] for i, a in enumerate(argv) if a == "--skill"]
assert sk and all("/qa-kit-" in s for s in sk), sk   # the earlier kit's own skills, not the head's
assert json.load(open(f"{c}/input.json"))["kit_sha"] == sha and json.load(open(f"{c}/result.json"))["kit_sha"] == sha
EOF
! ls -d "$TMPDIR"/qa-kit-* 2>/dev/null || fail "the earlier kit's scratch copy outlived the run"
run 0 "$K" --evals "$t/evals" --case reads --kit-ref "$c2"
line PASS reads | grep -q "\[kit $c2\]" || fail "kit-ref at the change: want PASS with its sha: $out"
run 0 "$K" --evals "$t/evals" --case reads
line PASS reads | grep -q "\[kit $c2\]" || fail "head run does not record the kit's HEAD sha: $out"
run 1 "$K" --evals "$t/evals" --case reads --kit-ref "$c0"
line FAIL reads | grep -q "kit $c0: no agents/implementer.md at that commit" || fail "missing role file not named: $out"
run 64 "$K" --evals "$t/evals" --case reads --kit-ref no-such-ref
grep -q "kit-ref no-such-ref: no such commit" <<< "$out" && ! grep -q "qa: run " <<< "$out" || fail "unknown ref not refused by name: $out"
# Other repos (#182, rule: schema.md, Attempt record): a sibling repo under HOME and, in a --kit-ref run, the head kit
# itself are masked; listing them is recorded and refused, their files never reach the case.
git init -q "$HOME/src/sib"; echo SIBSECRET > "$HOME/src/sib/NOTES.md"
mkdir -p "$t/rep/rep/reference" "$t/rep/fixtures"; cp -r "$t/good/fixtures/fx" "$t/rep/fixtures/"
echo '{"suite": "rep", "kind": "role-transcript", "description": "stub other repos", "max_tool_calls": 20, "timeout_s": 60}' > "$t/rep/rep/suite.json"
echo "[$(ic repos "Diagnose. STUB-ATTEMPTS STUB-REPOS")]" > "$t/rep/rep/cases.json"
echo '{"repos": {"facts": [{"fact": "attempt_blocked", "kind": "repo"}]}}' > "$t/rep/rep/reference/expectations.json"
run 0 "$K" --evals "$t/rep" --case repos --kit-ref "$c2"
b="$(grep -E '^PASS rep/repos: ' <<< "$out")" || fail "repos: want PASS: $out"
grep -q "open $HOME/src/sib (tmpfs mask over $HOME/src/sib, 0 entries)" <<< "$b" || fail "repos: the sibling repo's listing not recorded and refused: $b"
grep -q "open $HOME/src/kit (tmpfs mask over $HOME/src/kit, 2 entries (bound back: .agents, scripts))" <<< "$b" \
  || fail "repos: the head kit's listing in a --kit-ref run not recorded and refused: $b"
grep -q "qc sandbox: ok   other repos hidden: 2 git repos under $HOME .*: src/kit \[.agents scripts\], src/sib; visible: kit under test $TMPDIR/qa-kit-.*, worktree .*; bound back read-only: $HOME/src/kit/scripts/octo-feather-qc-sandbox, $HOME/src/kit/scripts/octo-feather-state, $HOME/src/kit/scripts/octo-feather-mise-install, $HOME/src/kit/.agents/skills/github-pr/scripts, $HOME/src/kit/scripts/octo-feather-qa$" <<< "$out" \
  || fail "repos: no proof line naming the masks and what stays visible: $out"
d="$(ls -dt "$t"/out/*/ | head -1)"
! grep -q "SIBSECRET\|$HOME/src/kit/agents/implementer.md" "$d/rep/repos/transcript.jsonl" || fail "repos: another repo's file or the head kit's role reached the case"
grep -q "NOTES.md: No such file" "$d/rep/repos/transcript.jsonl" && grep -q "kit/agents': No such file" "$d/rep/repos/transcript.jsonl" \
  || fail "repos: the sibling's file and the head kit's roles were not tried (nothing proved): $(cat "$d/rep/repos/transcript.jsonl")"
echo "qa-kit-ref: ok (--kit-ref FAIL before and PASS at a kit change with its sha, other repos and the --kit-ref head kit masked (attempt_blocked repo), missing role file named, unknown ref 64)"
