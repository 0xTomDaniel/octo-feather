#!/usr/bin/env bash
# Integration test for `just check-vendored` and `just vendored-fetch`
# (scripts/check-vendored) on a throwaway copy of the kit's Skillfile, lock,
# patches and skill folders, against a copy of the warm cache:
# - the gate passes with no network namespace (it never needs to dial out);
# - a drifted, extra or missing vendored file, or a patch that no longer
#   matches, fails naming skill and file;
# - a poisoned cache (a tampered upstream blob matching a tampered vendored
#   file) fails naming the skill; a missing cache fails naming `just vendored-fetch`;
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
export XDG_CACHE_HOME="$t/c"
run() { local want="$1"; shift; set +e; out="$("$@" just -f "$r/justfile" check-vendored 2>&1)"; rc=$?; set -e
  [[ "$rc" == "$want" ]] || { echo "check-vendored test: want exit $want, got $rc: $out" >&2; exit 1; }; }
has() { grep -qF -- "$1" <<<"$out" || { echo "check-vendored test: output lacks '$1': $out" >&2; exit 1; }; }
# Clean copy, no network at all: passes.
run 0 unshare -Un --map-current-user; has "vendored: ok"
# One drifted line in a patched file.
cp "$r/.agents/skills/tdd/SKILL.md" "$t/keep"
sed -i '0,/^$/s//drift/' "$r/.agents/skills/tdd/SKILL.md"
run 1; has "check-vendored: tdd: .agents/skills/tdd/SKILL.md differs from upstream mattpocock/skills@49dd158"
cp "$t/keep" "$r/.agents/skills/tdd/SKILL.md"; run 0
# An extra file and a missing upstream file.
echo x > "$r/.agents/skills/sharpen/EXTRA.md"; mv "$r/.agents/skills/tdd/mocking.md" "$t/"
run 1; has "check-vendored: sharpen: .agents/skills/sharpen/EXTRA.md is not in upstream"
has "check-vendored: tdd: .agents/skills/tdd/mocking.md is missing"
rm "$r/.agents/skills/sharpen/EXTRA.md"; mv "$t/mocking.md" "$r/.agents/skills/tdd/"; run 0
# A patch that no longer matches its committed file.
sed -i 's/^-disable-model/ disable-model/' "$r/.skillfile/patches/skills/sharpen/SKILL.md.patch"
run 1; has "check-vendored: sharpen: .agents/skills/sharpen/SKILL.md differs"
cp "$kit/.skillfile/patches/skills/sharpen/SKILL.md.patch" "$r/.skillfile/patches/skills/sharpen/"; run 0
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
run 1 unshare -Un --map-current-user; has "is not cached at"; has "run \`just vendored-fetch\`"
# Stalled network: a proxy that accepts and never answers; the fetch gives up within its bound.
# Own network namespace with only loopback up, so it never reaches the real network, online or not.
cat > "$t/stall.sh" <<'SH'
ip link set lo up
python3 -c '
import socket, sys
s = socket.socket(); s.bind(("127.0.0.1", 0)); s.listen(16)
open(sys.argv[1], "w").write(str(s.getsockname()[1])); held = []
while True: held.append(s.accept()[0])
' "$1/port" & lp=$!
for _ in $(seq 50); do [[ -s "$1/port" ]] && break; sleep 0.1; done
p="http://127.0.0.1:$(cat "$1/port")"
HTTPS_PROXY="$p" https_proxy="$p" OCTO_FEATHER_FETCH_TIMEOUT=2 just -f "$2/justfile" vendored-fetch; rc=$?
kill "$lp"; rm -f "$1/port"; exit "$rc"
SH
stall() { local s; s=$SECONDS; set +e; out="$(unshare -rn bash "$t/stall.sh" "$t" "$r" 2>&1)"; rc=$?; set -e
  [[ "$rc" == 1 && $((SECONDS - s)) -le 15 ]] || { echo "check-vendored test: stalled fetch want exit 1 within 15s, got $rc after $((SECONDS - s))s: $out" >&2; exit 1; }; }
stall; has "git fetch of mattpocock/skills@49dd158d1076134a641b33efb035946536778336 timed out after 2s"; has "rerun \`just vendored-fetch\`"
rm -rf "$t/c/octo-feather/skillfile/bin"
stall; has "downloading skillfile v1.9.2"; has "failed after at most 2s"; has "rerun \`just vendored-fetch\`"
echo "check-vendored test: ok (offline gate, drift, poisoned and missing cache, stalled fetch)"
