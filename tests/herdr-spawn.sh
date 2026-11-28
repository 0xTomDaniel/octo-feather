#!/usr/bin/env bash
# Integration test for herdr-spawn and pi-role vs Pi's project trust dialog
# (issue #3): drives herdr-spawn's CLI with a fake herdr first on PATH
# (tests/fixtures/herdr-spawn/) and pi-role headless with a fake pi. Resuming a
# parked agent through herdr-say (issue #9): tests/herdr-say-resume.sh. A trust
# dialog that opens anyway: tests/herdr-spawn-dialog.sh. No real
# herdr, pi or state dir. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
# ident DIR: the commit identity a role launch needs (#665) in state dir DIR: set once through pi-role --set-identity,
# its file copied for each later DIR (one Python start, not one per case: the CPU budget).
ident() {
  [[ -f "$t/ident/octo-feather/onboarding.toml" ]] || XDG_STATE_HOME="$t/ident" "$kit/scripts/pi-role" --set-identity t t@t >/dev/null
  mkdir -p "$1/octo-feather"; cp "$t/ident/octo-feather/onboarding.toml" "$1/octo-feather/"
}
export XDG_STATE_HOME="$t/state"; ident "$t/state"
mkdir -p "$t/bin" "$t/cwd" "$t/cache"
# mise's state its own, also run bare outside the gate: mise in $t/cwd's mise.toml records it there, never in the caller's (#664).
export MISE_STATE_DIR="$t/mise-state"
cp "$kit/tests/fixtures/herdr-spawn/"* "$t/bin/"
cp "$kit/tests/gate/kit/testkit/systemd.py" "$t/bin/busctl"; cp "$kit/tests/gate/kit/testkit/systemd.py" "$t/bin/systemctl"   # systemd stood in: the scope is e2e
chmod +x "$t/bin/herdr"
fail() { echo "herdr-spawn test: $*" >&2; exit 1; }
# A failing-read case is vacuous unless herdr-spawn read up to the armed
# boundary: fewer reads than READS_OK means the failing read was never reachable.
# Reads past it must be recorded failures (the fake's failed-reads).
armed() { # $1: case dir, $2: READS_OK
  local r f=0; r="$(wc -l <"$t/$1/reads")"
  [[ ! -f "$t/$1/failed-reads" ]] || f="$(wc -l <"$t/$1/failed-reads")"
  ((r >= $2)) || fail "$1: $r pane reads < READS_OK=$2; the failing read was never reached, so this case proves nothing"
  ((r == $2 || f >= 1)) || fail "$1: $r reads past READS_OK=$2 but no failed read recorded"
}

spawn() { # $1: case dir; rest: env assignments
  local c="$t/$1"; shift; mkdir -p "$c"; rc=0
  env FAKE_HERDR_DIR="$c" PATH="$t/bin:$PATH" XDG_CACHE_HOME="$t/cache" HERDR_PANE_ID=w9:p0 \
    HERDR_SPAWN_TRUST_RETRIES=3 HERDR_SPAWN_READY_RETRIES=2 "$@" \
    "$kit/.agents/skills/herdr-comms/assets/herdr-spawn" --workspace w9 --name t1 --role implementer \
    --cwd "$t/cwd" >"$c/out" 2>"$c/err" || rc=$?
}

# 1. A plain spawn launches Pi with --approve, so no dialog opens and it succeeds. Its caller has no LINEAR_API_KEY
#    (1c's unset case reads its tab env).
unset LINEAR_API_KEY; spawn ok
grep -qx -- --approve "$t/ok/start-argv" || fail "agent start argv lacks --approve: $(tr '\n' ' ' <"$t/ok/start-argv")"
# The implementer lists web: its tab gets the kit's web list, not --no-mcp (#262, roles#launch-web).
for f in --no-skills --octo-feather-web-servers; do grep -qx -- "$f" "$t/ok/start-argv" || fail "pi-role --json args lost $f beside --approve"; done
[[ "$rc" == 0 ]] || fail "spawn exited $rc: $(cat "$t/ok/err")"
grep -q 'tab=w9:t1 pane=w9:p1' "$t/ok/out" || fail "spawn printed no tab and pane: $(cat "$t/ok/out")"
[[ ! -s "$t/ok/keys" ]] || fail "keys sent to a ready pane: $(cat "$t/ok/keys")"

# 1b. pi-role runs in --cwd, not the caller's directory: the tracker skill is the target's
#     (spec skills#tracker). A caller in a jira target spawning into $t/cwd (no config) gets
#     github-issues; spawning into the jira target from $t/cwd is refused before any tab.
mkdir -p "$t/jira"; git -C "$t/jira" init -q; echo 'tracker = "jira"' > "$t/jira/.octo-feather.toml"
spawn_from() { # $1: case dir, $2: caller dir, $3: --cwd
  local c="$t/$1"; mkdir -p "$c"; rc=0
  (cd "$2" && env FAKE_HERDR_DIR="$c" PATH="$t/bin:$PATH" XDG_CACHE_HOME="$t/cache" HERDR_PANE_ID=w9:p0 \
    HERDR_SPAWN_TRUST_RETRIES=3 HERDR_SPAWN_READY_RETRIES=2 \
    "$kit/.agents/skills/herdr-comms/assets/herdr-spawn" --workspace w9 --name t1 --role implementer \
    --cwd "$3" >"$c/out" 2>"$c/err") || rc=$?
}
spawn_from cwd-target "$t/jira" "$t/cwd"
[[ "$rc" == 0 ]] || fail "spawn into a no-config target from a jira caller: exit $rc: $(cat "$t/cwd-target/err")"
grep -q '/github-issues$' "$t/cwd-target/start-argv" || fail "spawn into a no-config target lacks github-issues: $(tr '\n' ' ' <"$t/cwd-target/start-argv")"
spawn_from cwd-jira "$t/cwd" "$t/jira"
[[ "$rc" == 65 ]] && grep -q "unknown tracker 'jira'" "$t/cwd-jira/err" || fail "spawn into a jira target: exit $rc: $(cat "$t/cwd-jira/err")"
[[ ! -s "$t/cwd-jira/start-argv" ]] || fail "spawn into a jira target started an agent"

# 1c. remote#acceptance-linear-key-panes: LINEAR_API_KEY set in the caller reaches the tab's env (the fake
#     herdr's tab-env), no file the spawn writes (home, state, cache, worktree) holds it, and a ticket filed
#     from that env through the linear skill's issue-create reaches the testkit's Linear stand-in (tape
#     tests/fixtures/linear-herdr-spawn), which answers it only with the key. Unset in the caller: not set
#     in the tab.
key="lin-test-$(od -An -N8 -tx8 /dev/urandom | tr -d ' ')"
lk="$t/lk"; mkdir -p "$lk/home" "$lk/state" "$lk/lbin"; ident "$lk/state"
spawn key LINEAR_API_KEY="$key" HOME="$lk/home" XDG_STATE_HOME="$lk/state"
[[ "$rc" == 0 ]] || fail "spawn with LINEAR_API_KEY: exit $rc: $(cat "$t/key/err")"
grep -qxF "LINEAR_API_KEY=$key" "$t/key/tab-env" || fail "tab env lacks LINEAR_API_KEY: $(cut -d= -f1 "$t/key/tab-env" | tr '\n' ' ')"
hits="$(grep -rlF -- "$key" "$lk" "$t/cache" "$t/cwd" "$t/key/out" "$t/key/err" 2>/dev/null || true)"
[[ -z "$hits" ]] || fail "files written by the spawn hold the Linear key: $hits"
printf '#!/usr/bin/env bash\n[[ "${LINEAR_API_KEY:-}" == %q ]] || { echo "linear: no API key" >&2; exit 1; }\nexec %q "$@"\n' \
  "$key" "$kit/tests/gate/kit/testkit/linear/linear" >"$t/key/linear"; chmod +x "$t/key/linear"
mkdir "$t/key/fl"; cp "$kit/tests/fixtures/linear-herdr-spawn/tape.json" "$t/key/fl/"
mapfile -t tabenv <"$t/key/tab-env"
filed="$(echo body | env -i "${tabenv[@]}" PATH="$t/key:$(sed -n 's/^PATH=//p' "$t/key/tab-env")" \
  FAKE_LINEAR="$t/key/fl" "$kit/.agents/skills/linear/scripts/issue-create" --title T --body-file -)" \
  || fail "issue-create from the tab env failed"
[[ "$filed" == ENG-1 && "$(cat "$t/key/fl/log")" == '[["issue", "create", "--title", "T", "--description-file", "-", "--no-input"], "body\n"]' ]] \
  || fail "ticket did not reach the Linear stand-in: $filed $(cat "$t/key/fl/log")"
# Unset in the caller: 1's spawn (ok), whose caller had none.
! grep -q '^LINEAR_API_KEY=' "$t/ok/tab-env" || fail "LINEAR_API_KEY set in a tab whose caller had none"
# 1d. #261: in a repo with its own mise.toml the tab's PATH is the kit dirs, then the caller's PATH with mise's
#     shims dir (as pi-role reports it, "path") just before its first system dir; in a repo without one (the cases
#     above: a repo the kit did not create) or with no mise on PATH, the caller's PATH as it was. In each, the stash
#     guard's dir ($g) where pi-role places it (pi-role --help, Stash guard).
shims="$(mise doctor --json | jq -r .dirs.shims)"; g="$kit/scripts/stash-guard"
kitpath="$kit/.agents/skills/herdr-comms/assets:$kit/scripts"; ub="$HOME/.local/bin"   # ub: the fallback, last
grep -qF ":$g:" "$t/ok/tab-env" || fail "tab PATH in a repo without mise.toml lacks the stash guard $g: $(grep ^PATH= "$t/ok/tab-env")"
# A caller PATH that already holds $g (a gate under an agent's launch PATH: CI's) has it moved, not added (#1322).
bare=":$PATH:"; bare="${bare//:$g:/:}"; bare="${bare#:}"; bare="${bare%:}"
grep -qxF "PATH=$kitpath:$t/bin:$bare:$ub" <(sed "s|:$g:|:|" "$t/ok/tab-env") || fail "tab PATH in a repo without mise.toml changed: $(grep ^PATH= "$t/ok/tab-env")"
mkdir -p "$t/mbin"; ln -sf "$(command -v mise)" "$t/mbin/mise"; ln -sf "$(command -v jq)" "$t/mbin/jq"
printf '[tools]\n' >"$t/cwd/mise.toml"
spawn made PATH="$t/bin:$t/mbin:/usr/local/bin:/usr/bin:/bin"
[[ "$rc" == 0 ]] || fail "spawn in a mise.toml repo: exit $rc: $(cat "$t/made/err")"
grep -qxF "PATH=$kitpath:$t/bin:$t/mbin:$g:$shims:/usr/local/bin:/usr/bin:/bin:$ub" "$t/made/tab-env" \
  || fail "tab PATH in a mise.toml repo lacks mise's shims $shims before the system dirs, after the caller's: $(grep ^PATH= "$t/made/tab-env")"
spawn nomise PATH="$t/bin:/usr/bin:/bin"
[[ "$rc" == 0 ]] || fail "spawn without mise: exit $rc: $(cat "$t/nomise/err")"
grep -qxF "PATH=$kitpath:$t/bin:$g:/usr/bin:/bin:$ub" "$t/nomise/tab-env" || fail "tab PATH without mise changed: $(grep ^PATH= "$t/nomise/tab-env")"
rm "$t/cwd/mise.toml"
# 1e. Owner ruling #261 (#437): a stub pi first on the caller's PATH beats the box's pi in ~/.local/bin in the tab's
#     PATH (a fake one under a throwaway HOME); a tool only ~/.local/bin holds is still found there (its fallback).
#     Resolved only (`command -v`), never run.
uh="$t/uh"; mkdir -p "$uh/.local/bin" "$t/stub"
for b in pi only-home; do printf '#!/bin/sh\necho "home %s"\n' "$b" >"$uh/.local/bin/$b"; chmod +x "$uh/.local/bin/$b"; done
printf '#!/bin/sh\necho "stub pi"\n' >"$t/stub/pi"; chmod +x "$t/stub/pi"
for mt in "" mise; do   # without and with a mise.toml (pi-role's "path")
  [[ -z "$mt" ]] || printf '[tools]\n' >"$t/cwd/mise.toml"
  spawn "stub$mt" HOME="$uh" PATH="$t/bin:$t/stub:$t/mbin:/usr/bin:/bin"
  [[ "$rc" == 0 ]] || fail "spawn with a stub pi${mt:+ in a mise.toml repo}: exit $rc: $(cat "$t/stub$mt/err")"
  tp="$(sed -n 's/^PATH=//p' "$t/stub$mt/tab-env")"
  [[ "$(PATH="$tp" command -v pi)" == "$t/stub/pi" ]] || fail "tab PATH${mt:+ (mise.toml)} finds pi at $(PATH="$tp" command -v pi), not the caller's stub: $tp"
  [[ "$(PATH="$tp" command -v only-home)" == "$uh/.local/bin/only-home" ]] || fail "tab PATH${mt:+ (mise.toml)} lost the ~/.local/bin fallback: $tp"
  rm -f "$t/cwd/mise.toml"
done

# 3. Headless pi-role passes --approve too (fake pi records its argv).
printf '#!/usr/bin/env bash\nprintf "%%s\\n" "$@" >"%s/pi-argv"\n' "$t" >"$t/bin/pi"; chmod +x "$t/bin/pi"
(cd "$t/cwd" && PATH="$t/bin:$PATH" "$kit/scripts/pi-role" "$kit/agents/implementer.md" -p brief)
grep -qx -- --approve "$t/pi-argv" || fail "headless pi-role argv lacks --approve"

echo "herdr-spawn: ok (pane and headless launch carry --approve; pi-role runs in --cwd (its tracker, not the caller's); LINEAR_API_KEY reaches the tab only from the caller's env, mise's shims before the system dirs on the tab's PATH in a mise.toml repo (none elsewhere or without mise), the caller's stub pi before ~/.local/bin's (its fallback, last), in no written file, files a ticket in the Linear stand-in)"
