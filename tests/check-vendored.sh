#!/usr/bin/env bash
# Integration test for `just check-vendored` (scripts/check-vendored) on a throwaway
# copy of the kit's Skillfile, lock, patches and skill folders: the clean copy
# passes; a drifted, extra or missing vendored file fails naming skill and file;
# a cold cache with no network fails naming the pins. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
r="$t/repo"; mkdir -p "$r/scripts" "$r/.skillfile"
cp "$kit/justfile" "$kit/Skillfile" "$kit/Skillfile.lock" "$r/"
cp "$kit/scripts/check-vendored" "$r/scripts/"
cp -r "$kit/.skillfile/patches" "$r/.skillfile/"
mkdir -p "$r/.agents"; cp -r "$kit/.agents/skills" "$r/.agents/"
run() { local want="$1"; set +e; out="$(just -f "$r/justfile" check-vendored 2>&1)"; rc=$?; set -e
  [[ "$rc" == "$want" ]] || { echo "check-vendored test: want exit $want, got $rc: $out" >&2; exit 1; }; }
has() { grep -qF -- "$1" <<<"$out" || { echo "check-vendored test: output lacks '$1': $out" >&2; exit 1; }; }
run 0; has "vendored: ok"
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
cp "$kit/.skillfile/patches/skills/sharpen/SKILL.md.patch" "$r/.skillfile/patches/skills/sharpen/"
# Cold upstream cache, no network: loud failure naming the pin, never a skip.
c="$t/cache/octo-feather/skillfile"; mkdir -p "$c"
cp -r "${XDG_CACHE_HOME:-$HOME/.cache}/octo-feather/skillfile/bin" "$c/"
set +e; out="$(XDG_CACHE_HOME="$t/cache" unshare -rn just -f "$r/justfile" check-vendored 2>&1)"; rc=$?; set -e
[[ "$rc" == 1 ]] || { echo "check-vendored test: cold offline want exit 1, got $rc: $out" >&2; exit 1; }
has "upstream not cached for tdd (mattpocock/skills@49dd158d1076134a641b33efb035946536778336 skills/engineering/tdd)"
echo "check-vendored test: ok"
