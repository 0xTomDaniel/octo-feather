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
# - a fetch through a stalled proxy times out within its bound, naming the fix.
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
# Network-namespace proofs (gate never dials out; stalled proxy) need Linux user namespaces:
# run them where `unshare` works, else name the skip. Every other case runs everywhere.
skipped=()
ns=(); if unshare -Un --map-current-user true 2>/dev/null; then ns=(unshare -Un --map-current-user)
  else skipped+=("offline-namespace gate runs (unshare -Un unavailable)"); fi
stallok=0; if unshare -rn sh -c 'ip link set lo up' 2>/dev/null; then stallok=1
  else skipped+=("stalled and dripping proxy fetch (needs unshare -rn and ip)"); fi
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
if [[ $stallok == 1 ]]; then
# Stalled network, two ways: a proxy that accepts and never answers (silent), and one that
# drips CONNECT response headers every 0.2 s forever (slow progress). Either way the fetch
# gives up within one total bound. Own network namespace with only loopback up, so it never
# reaches the real network, online or not.
cat > "$t/stall.sh" <<'SH'
ip link set lo up
python3 -c '
import socket, sys, threading, time
s = socket.socket(); s.bind(("127.0.0.1", 0)); s.listen(16)
open(sys.argv[1], "w").write(str(s.getsockname()[1])); held = []
def drip(c):
    try:
        c.recv(65536); c.sendall(b"HTTP/1.1 200 Connection established\r\n")
        while True: c.sendall(b"X-Drip: 1\r\n"); time.sleep(0.2)
    except OSError: pass
while True:
    c = s.accept()[0]; held.append(c)
    if sys.argv[2] == "drip": threading.Thread(target=drip, args=(c,), daemon=True).start()
' "$1/port" "$3" & lp=$!
for _ in $(seq 50); do [[ -s "$1/port" ]] && break; sleep 0.1; done
p="http://127.0.0.1:$(cat "$1/port")"
HTTPS_PROXY="$p" https_proxy="$p" OCTO_FEATHER_FETCH_TIMEOUT=2 just -f "$2/justfile" vendored-fetch; rc=$?
kill "$lp"; rm -f "$1/port"; exit "$rc"
SH
stall() { local s; s=$SECONDS; set +e; out="$(unshare -rn bash "$t/stall.sh" "$t" "$r" "$1" 2>&1)"; rc=$?; set -e
  [[ "$rc" == 1 && $((SECONDS - s)) -le 10 ]] || { echo "check-vendored test: $1 proxy fetch want exit 1 within 10s, got $rc after $((SECONDS - s))s: $out" >&2; exit 1; }
  has "rerun \`just vendored-fetch\`"; }
for mode in silent drip; do stall "$mode"; has "git fetch of mattpocock/skills@49dd158d1076134a641b33efb035946536778336 timed out after 2s"; done
rm -rf "$t/c/octo-feather/skillfile/bin"
for mode in silent drip; do stall "$mode"; has "downloading skillfile v1.9.2 from https://github.com/eljulians/skillfile/releases/download/v1.9.2/"; has "timed out after 2s"; done
fi
for x in ${skipped[@]+"${skipped[@]}"}; do echo "check-vendored test: skipped, Linux-only proof: $x"; done
ran="pinned Spec Chat written and uncached, drift, committed modes, untracked strays, symlinks, special files and empty folders not committed, poisoned and missing cache"
[[ ${#ns[@]} -gt 0 ]] && ran="offline-namespace gate, $ran"
[[ $stallok == 1 ]] && ran="$ran, silent and dripping proxy"
echo "check-vendored test: ok ($ran)"
