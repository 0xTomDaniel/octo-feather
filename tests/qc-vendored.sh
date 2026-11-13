#!/usr/bin/env bash
# gate: e2e
# The qc sandbox test's vendored-cache section (#508; setup tests/lib/qc.sh): a warm vendored-skill cache (#69) is
# bound read-only (check-vendored green in the sandbox, writes refused); new-repo's mise trust (#428) lands in an
# empty per-run state dir, nothing persists.
# Run by `just check`; offline and bounded, in its own namespace and throwaway HOME (tests/lib/qc.sh).
# shellcheck source=tests/lib/qc.sh
source "$(dirname "$0")/lib/qc.sh"
# A warm vendored-skill cache (#69): bound back read-only after the cache tmpfs, so `just check` in the sandbox
# reaches check-vendored green; the proof names the bind; the judge cannot write it.
[[ -d "$vc0/git" && -d "$vc0/bin" ]] || fail "no warm check-vendored cache at $vc0: run just vendored-fetch"
vc="$HOME/.cache/octo-feather/skillfile"; mkdir -p "${vc%/*}"; cp -a "$vc0" "$vc"; vsum() { find "$vc" -printf '%P %s %m\n' | sort | md5sum; }; v0="$(vsum)"
run 0 vendored $st 5 acceptance-a
judge="$(jr '["stdout"]')"
grep -E 'ESCAPE|MISSING' <<< "$judge" && fail "vendored cache: $judge"
grep -q "VENDORED green" <<< "$judge" || fail "check-vendored not green in the sandbox: $judge"
grep -q "qc sandbox: ok   vendored-skill cache $vc bound read-only" <<< "$out" && grep -q "qc sandbox: ok   writable persistent paths: none$" <<< "$out" \
  || fail "no read-only cache proof: $out"
[[ "$(vsum)" == "$v0" ]] || fail "the judge changed the vendored-skill cache"
rm -rf "$HOME/.cache"
# #428: new-repo in the sandbox, mise's state dir pinned (as the kit justfile pins it) to a path the sandbox makes
# read-only: its `mise trust` lands in a per-run state dir on the run's /tmp, named by the proof; nothing persists.
# The per-run dir starts empty: the caller's trust entry for another repo never reaches the judge.
command -v mise > /dev/null || fail "no mise on PATH: the new-repo case proves its mise trust in the sandbox"
ms="$HOME/.local/state/mise"; mkdir -p "$ms/trusted-configs"; ln -s "$HOME/src/sib" "$ms/trusted-configs/src-sib-0123456789abcdef"
MISE_STATE_DIR="$ms" run 0 newrepo $st 5 acceptance-a
judge="$(jr '["stdout"]')"
grep -q "NEWREPO exit 0" <<< "$judge" && grep -q "mise.toml trusted (that file only)" <<< "$judge" || fail "new-repo in the sandbox: $judge"
grep -q "qc sandbox: ok   mise state dir per-run: /tmp/.* started empty: 0 entries" <<< "$out" && grep -q "qc sandbox: ok   writable persistent paths: none$" <<< "$out" \
  || fail "no per-run mise state proof: $out"
[[ "$(ls -A "$ms/trusted-configs")" == src-sib-0123456789abcdef ]] || fail "the run's mise trust persisted: $(ls -A "$ms/trusted-configs")"
rm -rf "$HOME/.local/state/mise"
echo "qc-vendored: ok (vendored cache read-only (check-vendored green, writes refused), new-repo's mise trust in an empty per-run state dir; offline, runs bounded)"
