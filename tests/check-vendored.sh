#!/usr/bin/env bash
# Integration test for `just check-vendored` and `just vendored-fetch`
# (scripts/check-vendored) on a throwaway copy of the kit's Skillfile, lock,
# patches and skill folders, against a copy of the warm cache:
# - the gate passes with no network namespace (it never needs to dial out);
# - the gate reads the committed folder (the copy is a git repo; run stages every change):
#   a drifted, extra or missing vendored file, a committed mode change, or a patch that
#   no longer matches, fails naming skill and file; untracked files and what git cannot
#   hold (a FIFO, an empty folder) pass (cases: #143, #121 D16);
# - a poisoned cache (a tampered upstream blob matching a tampered vendored
#   file) fails naming the skill; a missing cache fails naming `just vendored-fetch`;
# - --extract spec-chat DEST writes the fetch-only Spec Chat pin offline, exec bits kept;
#   uncached, it fails naming `just vendored-fetch` (#96);
# - a fetch GitHub refuses for credentials (a private pin) names gh auth login && gh auth setup-git (#463).
# Needs the warm cache `just vendored-fetch` makes (CI runs it before `just check`).
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
src="${XDG_CACHE_HOME:-$HOME/.cache}/octo-feather/skillfile"
[[ -d "$src/git" && -d "$src/bin" ]] || { echo "check-vendored test: no warm cache at $src; run \`just vendored-fetch\`" >&2; exit 1; }
r="$t/repo"; mkdir -p "$r/scripts" "$r/.skillfile" "$r/.agents" "$t/c/octo-feather"
cp "$kit/justfile" "$kit/Skillfile" "$kit/Skillfile.lock" "$r/"
cp "$kit/scripts/check-vendored" "$r/scripts/"
cp -r "$kit/.skillfile/patches" "$r/.skillfile/"
cp -r "$kit/.agents/skills" "$r/.agents/"
cp -r "$src" "$t/c/octo-feather/"; chmod -R u+w "$t/c"
gr() { git -C "$r" -c user.name=t -c user.email=t@t "$@"; }
gr init -q; gr add -A; gr commit -qm base
export XDG_CACHE_HOME="$t/c"
# The network-namespace proof (gate never dials out) needs Linux user namespaces:
# run it where `unshare` works, else name the skip. Every other case runs everywhere.
skipped=()
ns=(); if unshare -Un --map-current-user true 2>/dev/null; then ns=(unshare -Un --map-current-user)
  else skipped+=("offline-namespace gate runs (unshare -Un unavailable)"); fi
# Portable in-place edit: edit FILE PYTHON-EXPR-ON-s (no sed -i).
edit() { python3 -c 'import sys; p = sys.argv[1]; s = open(p).read(); s = eval(sys.argv[2]); open(p, "w").write(s)' "$1" "$2"; }
# run WANT [PREFIX...]: stage every change in the copy (as a commit records it), then the gate; stage=0 skips staging.
stage=1
run() { local want="$1"; shift; [[ $stage == 0 ]] || gr add -A; set +e; out="$("$@" just -f "$r/justfile" check-vendored 2>&1)"; rc=$?; set -e
  [[ "$rc" == "$want" ]] || { echo "check-vendored test: want exit $want, got $rc: $out" >&2; exit 1; }; }
has() { grep -qF -- "$1" <<<"$out" || { echo "check-vendored test: output lacks '$1': $out" >&2; exit 1; }; }
# Clean copy, no network at all: passes.
run 0 ${ns[@]+"${ns[@]}"}; has "vendored: ok"
# Pinned Spec Chat, written out with no network: its files, exec bits kept.
sc() { set +e; out="$(${ns[@]+"${ns[@]}"} "$r/scripts/check-vendored" --extract spec-chat "$1" 2>&1)"; rc=$?; set -e; }
sc "$t/sc"; [[ "$rc" == 0 && "$out" == "$t/sc/skill" && -x "$t/sc/skill/review-spec/scripts/review-host.py" \
  && -f "$t/sc/skill/review-spec/assets/review-serve.py" ]] || { echo "check-vendored test: --extract spec-chat: rc=$rc $out" >&2; exit 1; }
# One drifted line in a patched file.
cp "$r/.agents/skills/tdd/SKILL.md" "$t/keep"
edit "$r/.agents/skills/tdd/SKILL.md" 's.replace("\n\n", "\ndrift\n", 1)'
run 1; has "check-vendored: tdd: .agents/skills/tdd/SKILL.md differs from upstream mattpocock/skills@49dd158"
cp "$t/keep" "$r/.agents/skills/tdd/SKILL.md"; run 0
# An extra file and a missing upstream file.
echo x > "$r/.agents/skills/sharpen/EXTRA.md"; mv "$r/.agents/skills/tdd/mocking.md" "$t/"
run 1; has "check-vendored: sharpen: .agents/skills/sharpen/EXTRA.md is not in upstream"
has "check-vendored: tdd: .agents/skills/tdd/mocking.md is missing"
rm "$r/.agents/skills/sharpen/EXTRA.md"; mv "$t/mocking.md" "$r/.agents/skills/tdd/"; run 0
# A patch that no longer matches its committed file.
edit "$r/.skillfile/patches/skills/sharpen/SKILL.md.patch" 's.replace("\n-disable-model", "\n disable-model", 1)'
run 1; has "check-vendored: sharpen: .agents/skills/sharpen/SKILL.md differs"
cp "$kit/.skillfile/patches/skills/sharpen/SKILL.md.patch" "$r/.skillfile/patches/skills/sharpen/"; run 0
# #143, #121 D16 cases: mode change on the disk (chmod +x) or in the index only (update-index --chmod), then reverted.
chmod +x "$r/.agents/skills/tdd/SKILL.md"
run 1; has "check-vendored: tdd: .agents/skills/tdd/SKILL.md has git mode 100755, upstream mattpocock/skills@49dd158"
chmod -x "$r/.agents/skills/tdd/SKILL.md"; run 0
gr update-index --chmod=+x .agents/skills/grilling/SKILL.md
stage=0 run 1; has "check-vendored: grilling: .agents/skills/grilling/SKILL.md has git mode 100755"
gr update-index --chmod=-x .agents/skills/grilling/SKILL.md; run 0
# #143: an untracked stray file, then committed.
echo x > "$r/.agents/skills/tdd/STRAY.md"
stage=0 run 0; has "vendored: ok"
run 1; has "check-vendored: tdd: .agents/skills/tdd/STRAY.md is not in upstream"
rm "$r/.agents/skills/tdd/STRAY.md"; run 0
# #143: a committed folder symlink, file symlink, and the skill folder itself as a symlink; a FIFO or an
# empty folder git cannot commit.
ln -s ../grilling "$r/.agents/skills/tdd/EXTRA"
run 1; has "check-vendored: tdd: .agents/skills/tdd/EXTRA is a symlink (to ../grilling)"
rm "$r/.agents/skills/tdd/EXTRA"; ln -s SKILL.md "$r/.agents/skills/tdd/LINK.md"
run 1; has "check-vendored: tdd: .agents/skills/tdd/LINK.md is a symlink (to SKILL.md)"
rm "$r/.agents/skills/tdd/LINK.md"; mv "$r/.agents/skills/tdd/tests.md" "$t/"; ln -s "$t/tests.md" "$r/.agents/skills/tdd/tests.md"
run 1; has "check-vendored: tdd: .agents/skills/tdd/tests.md is a symlink"
rm "$r/.agents/skills/tdd/tests.md"; mv "$t/tests.md" "$r/.agents/skills/tdd/"
mkfifo "$r/.agents/skills/tdd/PIPE"
run 0; has "vendored: ok"   # git cannot commit a FIFO: not the skill
rm "$r/.agents/skills/tdd/PIPE"; mkdir -p "$r/.agents/skills/tdd/empty/deeper"
run 0; has "vendored: ok"   # nor an empty folder
rm -r "$r/.agents/skills/tdd/empty"; mv "$r/.agents/skills/sharpen" "$t/sharpen"; ln -s "$t/sharpen" "$r/.agents/skills/sharpen"
run 1; has "check-vendored: sharpen: .agents/skills/sharpen is a symlink"
rm "$r/.agents/skills/sharpen"; mv "$t/sharpen" "$r/.agents/skills/"; run 0
# Poisoned cache: grilling's upstream blob rewritten to match an edited vendored file.
g="$t/c/octo-feather/skillfile/git/mattpocock/skills/49dd158d1076134a641b33efb035946536778336.git"
mkdir "$t/pack"; mv "$g"/objects/pack/* "$t/pack/"
for p in "$t"/pack/*.pack; do git --git-dir "$g" unpack-objects -q < "$p"; done
oid="$(git --git-dir "$g" rev-parse 49dd158d1076134a641b33efb035946536778336:skills/productivity/grilling/SKILL.md)"
echo "poisoned line" >> "$r/.agents/skills/grilling/SKILL.md"
python3 - "$g/objects/${oid:0:2}/${oid:2}" "$r/.agents/skills/grilling/SKILL.md" <<'PY'
import os, sys, zlib
body = open(sys.argv[2], "rb").read()
os.chmod(sys.argv[1], 0o644)
open(sys.argv[1], "wb").write(zlib.compress(b"blob %d\0" % len(body) + body))
PY
run 1; has "check-vendored: grilling: cached upstream mattpocock/skills@49dd158d1076134a641b33efb035946536778336 skills/productivity/grilling fails authentication"
has "just vendored-fetch"
# Missing cache: fails fast naming the fetch step, never a skip.
rm -rf "$t/c/octo-feather/skillfile/git"
run 1 ${ns[@]+"${ns[@]}"}; has "is not cached at"; has "run \`just vendored-fetch\`"
sc "$t/sc2"; [[ "$rc" == 1 ]] || { echo "check-vendored test: uncached --extract want exit 1, got $rc: $out" >&2; exit 1; }
has "extract: spec-chat: 0xTomDaniel/spec-chat@"; has "run \`just vendored-fetch\`"
# GitHub asks for credentials (a private pin, git not signed in; #463): a stub git answers the fetch as git does with
# prompts off. Named with the sign-in fix, never "check network".
mkdir -p "$t/authbin"
printf '#!/bin/sh\nfor a; do [ "$a" = fetch ] && { echo "fatal: could not read Username for '"'"'https://github.com'"'"': terminal prompts disabled" >&2; exit 128; }; done\nexec "%s" "$@"\n' "$(command -v git)" >"$t/authbin/git"; chmod +x "$t/authbin/git"
rm -rf "$t/c/octo-feather/skillfile/git"
set +e; out="$(PATH="$t/authbin:$PATH" just -f "$r/justfile" vendored-fetch 2>&1)"; rc=$?; set -e
[[ $rc == 1 ]] || { echo "check-vendored test: fetch refused for credentials: want exit 1, got $rc: $out" >&2; exit 1; }
has "could not read Username"; has "GitHub wants credentials (a private pin): sign in and let git use gh: gh auth login && gh auth setup-git, then rerun \`just vendored-fetch\`"
! grep -qF "check network" <<<"$out" || { echo "check-vendored test: credential refusal blamed on the network: $out" >&2; exit 1; }
for x in ${skipped[@]+"${skipped[@]}"}; do echo "check-vendored test: skipped, Linux-only proof: $x"; done
ran="pinned Spec Chat written and uncached, credentials refused named with gh auth setup-git, drift, committed modes, untracked strays, symlinks, special files and empty folders not committed, poisoned and missing cache"
[[ ${#ns[@]} -gt 0 ]] && ran="offline-namespace gate, $ran"
echo "check-vendored test: ok ($ran)"
