#!/usr/bin/env bash
# Integration test for insufficient evidence (quality spec #qc-judgment, #qc-results, #acceptance-qc-insufficient),
# through `just qc` / octo-feather-qc, with a fake herdr and no model: a scratch target whose qc.toml declares two
# demos, each needing a step the qc sandbox cannot run: a tool not on the sandbox's PATH (the shell's exit 127) and
# GitHub (the sandbox's offline gh refuses, and the demo says so with exit 77). Each gets the result insufficient
# evidence naming what is missing, never fail: exit 2, not 1; both stay planned and the head is unchanged (no status
# commit when nothing flips). A rerun at the same head with the tool on the sandbox's PATH gives acceptance-a pass and
# its status-only commit. A dirty worktree is still refused. A kit-style demo (verify-octo-feather run --unreachable-exit 77)
# whose drive has an unreachable step is insufficient evidence too. The merge ask side: tests/lane-merge-ask.sh.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc-capture.sh.
set -euo pipefail
unset OCTO_FEATHER_CHECK_RUN   # a test harness, as tests/qc.sh: qc refuses only under the gate's marker
[[ "$(uname -s)" != Darwin ]] || { echo "qc-insufficient: skipped, not on macOS (just qc needs Linux; CI runs it)"; exit 0; }
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'chmod -R u+w "$t" 2>/dev/null; rm -rf "$t"' EXIT
t="$(cd "$t" && pwd -P)"
fail() { echo "qc-insufficient test: $*" >&2; exit 1; }
export HOME="$t/home" XDG_STATE_HOME="$t/state" TMPDIR="$t/tmp"
unset XDG_CONFIG_HOME XDG_CACHE_HOME GH_CONFIG_DIR HERDR_SESSION HERDR_SOCKET_PATH HERDR_BIN_PATH HERDR_ENV OCTO_FEATHER_QC_DIR OCTO_FEATHER_QC_PATH
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
mkdir -p "$HOME" "$TMPDIR" "$t/bin" "$t/tools" "$t/repo/docs/specs"
# Fake Herdr: the sandbox pins a per-run session through it (as tests/qc-capture.sh).
cat > "$t/bin/herdr" <<'EOF'
#!/usr/bin/env bash
C="${XDG_CONFIG_HOME:-$HOME/.config}/herdr"; s=default; a=()
while (($#)); do case "$1" in --session) s="$2"; shift 2;; --remote|--machine) shift 2;; *) a+=("$1"); shift;; esac; done
[[ "$s" == default ]] && sock="$C/herdr.sock" || sock="$C/sessions/$s/herdr.sock"
case "${a[*]}" in
  server) mkdir -p "${sock%/*}"; echo "$s" > "$sock"; exec sleep 600;;
  "session stop "*) rm -f "$C/sessions/${a[2]}/herdr.sock"; exit 0;;
  "session delete "*) rm -rf "${C:?}/sessions/${a[2]}"; exit 0;;
  "pane list") exit 0;;
esac
[[ -f "$sock" ]] || { echo server_not_running >&2; exit 1; }
echo "{\"session\":\"$(cat "$sock")\"}"
EOF
# The tool acceptance-a's demo needs, put on the sandbox's PATH only for the rerun.
printf '#!/bin/sh\necho "tool checks pass"\n' > "$t/tools/qc-needs-tool"
chmod +x "$t/bin/herdr" "$t/tools/qc-needs-tool"
export PATH="$t/bin:$kit/scripts:$PATH"

cd "$t/repo"; git init -q -b main .
git commit -qm accepted --allow-empty
cp "$kit/tests/fixtures/spec-status/good/demo.spec.html" docs/specs/
git add -A; git commit -qm spec
octo-feather-spec-status init docs/specs/demo.spec.html "$(git rev-parse --short HEAD)" >/dev/null
cat > qc.toml <<'EOF'
format = 1
[entry]
command = "true"
[services]
[fixture]
[values]
[demo."demo#acceptance-a"]
command = "qc-needs-tool --check"
covers = ["src/a"]
tests = ["tests/a.sh"]
[demo."demo#acceptance-b"]
command = 'gh api user >/dev/null || { echo "needs GitHub: gh api user refused in the qc sandbox" >&2; exit 77; }; echo b checks pass'
covers = ["src/b"]
tests = ["tests/b.sh"]
EOF
git add -A; git commit -qm contract
head="$(git rev-parse HEAD)"
qcrun() { set +e; out="$(timeout -k 5 120 just --justfile "$kit/justfile" qc docs/specs/demo.status.json 9 acceptance-a acceptance-b 2>"$t/err")"; rc=$?; set -e
  [[ "$rc" != 124 && "$rc" != 137 ]] || fail "qc hung: $(tail -20 "$t/err")"; }
rid='[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}'
status() { python3 -c 'import json,sys; c=json.load(open(sys.argv[1]))["criteria"]; print(c["acceptance-a"]["status"], c["acceptance-b"]["status"])' docs/specs/demo.status.json; }

# Run 1: both demos stop at a step the sandbox cannot run: insufficient evidence, naming what is missing; nothing flips.
qcrun
[[ "$rc" == 2 ]] || fail "run 1: want exit 2 (insufficient evidence, no failure), got $rc: $out $(tail -20 "$t/err")"
grep -A2 '^INSUFFICIENT EVIDENCE acceptance-a: \$ qc-needs-tool --check$' <<< "$out" | grep -A1 '^  missing: demo did not run to its end (exit 127, a command it runs was not found): .*qc-needs-tool: .*not found$' \
  | grep -qE "^  evidence incomplete; decision demo checks; record $rid$" || fail "run 1: acceptance-a not insufficient evidence naming the missing tool: $out"
grep -A2 '^INSUFFICIENT EVIDENCE acceptance-b: ' <<< "$out" | grep -A1 '^  missing: demo did not run to its end (exit 77, a step it needs could not run here): needs GitHub: gh api user refused in the qc sandbox$' \
  | grep -qE "^  evidence incomplete; decision demo checks; record $rid$" || fail "run 1: acceptance-b not insufficient evidence naming GitHub: $out"
! grep -q '^FAIL ' <<< "$out" || fail "run 1: an insufficient criterion was reported as a failure: $out"
grep -q 'insufficient evidence, never a failure to triage: acceptance-a acceptance-b' <<< "$out" || fail "run 1: summary does not name them apart from failures: $out"
[[ "$(git rev-parse HEAD)" == "$head" && -z "$(git status --porcelain)" && "$(status)" == "planned planned" ]] \
  || fail "run 1: want both planned, no commit, clean worktree: $(git log --oneline -1) $(status) $(git status --porcelain)"
rep="$(ls -t "$XDG_STATE_HOME"/octo-feather/qc/"$head"-*.json | head -1)"
python3 - "$rep" "$head" <<'EOF' || fail "run 1: report results: $(cat "$rep")"
import json, sys
rep, head = sys.argv[1:]
d = json.load(open(rep)); r = {x["id"]: x for x in d["results"]}
assert d["spec"] == "demo" and sorted(r) == ["acceptance-a", "acceptance-b"], d
for i, code in (("acceptance-a", 127), ("acceptance-b", 77)):
    x = r[i]
    assert (x["verdict"], x["evidence"], x["decision"], x["head"]) == ("insufficient evidence", "incomplete", "demo checks", head), x
    assert x["record"] and any(m.startswith(f"demo did not run to its end (exit {code},") for m in x["missing"]), x
EOF

# A dirty worktree is still refused before anything runs.
echo stray > stray.txt; qcrun; rm stray.txt
[[ "$rc" == 65 ]] && grep -q 'worktree is dirty' "$t/err" || fail "dirty worktree: want exit 65, got $rc: $(cat "$t/err")"

# Run 2, the same head, the tool now on the sandbox's PATH: acceptance-a passes and is built; acceptance-b stays insufficient.
OCTO_FEATHER_QC_PATH="$t/tools" qcrun
[[ "$rc" == 2 ]] || fail "run 2: want exit 2, got $rc: $out $(tail -20 "$t/err")"
grep -A2 '^PASS acceptance-a: \$ qc-needs-tool --check$' <<< "$out" | grep -qE "^  evidence complete; decision demo checks; record $rid$" \
  && grep -q '^INSUFFICIENT EVIDENCE acceptance-b: ' <<< "$out" || fail "run 2: want acceptance-a pass from the rerun, acceptance-b insufficient: $out"
[[ "$(git log -1 --format=%s)" == "qc: built acceptance-a (judged ${head:0:12})" && "$(git diff --name-only "$head" HEAD)" == docs/specs/demo.status.json \
  && "$(status)" == "built planned" ]] || fail "run 2: status commit: $(git log -1 --format=%s) $(git diff --name-only "$head" HEAD) $(status)"
# A kit demo as the kit's qc.toml declares one: verify-octo-feather run --unreachable-exit 77, here the new-repo drive with
# no Spec Chat installer (its spec-chat-link step unreachable): insufficient evidence naming that step, never a pass.
git rm -q qc.toml; printf '%s\n' 'format = 1' '[entry]' 'command = "true"' '[services]' '[fixture]' '[values]' '[demo."demo#acceptance-b"]' \
  "command = \"$kit/.agents/skills/verify-octo-feather/scripts/verify-octo-feather run --unreachable-exit 77 new-repo\"" \
  'covers = ["src/b"]' 'tests = ["tests/b.sh"]' > qc.toml
git add qc.toml; git commit -qm "kit-style demo"
set +e; out="$(SPEC_CHAT_CLONE="$t/no-spec-chat" timeout -k 5 300 just --justfile "$kit/justfile" qc docs/specs/demo.status.json 9 acceptance-b 2>"$t/err")"; rc=$?; set -e
[[ "$rc" == 2 ]] || fail "kit-style demo: want exit 2, got $rc: $out $(tail -30 "$t/err")"
grep -A1 '^INSUFFICIENT EVIDENCE acceptance-b: ' <<< "$out" \
  | grep -q '^  missing: demo did not run to its end (exit 77, a step it needs could not run here): verify-octo-feather: UNREACHABLE spec-chat-link: ' \
  || fail "kit-style demo: want insufficient evidence naming the unreachable step: $out"
echo "qc-insufficient: ok (a verify-octo-feather drive with an unreachable step under --unreachable-exit 77 is insufficient evidence naming it; a demo stopped by a missing tool (127) and by GitHub refused in the sandbox (77): insufficient evidence naming each, exit 2, never FAIL, both planned, no commit, the report's results; dirty worktree refused; a rerun with the tool gives pass and a status-only commit)"
