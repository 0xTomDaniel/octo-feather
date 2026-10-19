#!/usr/bin/env bash
# Integration test for scripts/check-owned-rules in a throwaway repo, planting
# the real restatements lane #8 logged as contradictory-merge-authority
# (github skill before 9f46d9b, implement-spec before 278118c) and the
# lane-branch default of finding 22. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
C="$kit/scripts/check-owned-rules"
g() { git -C "$t" -c user.name=t -c user.email=t@t "$@"; }
git init -q "$t"; mkdir -p "$t/docs/specs" "$t/agents" "$t/.skillfile/patches/skills/x" "$t/evidence"
# The owner may state the rule; a pointer and a dated record pass.
echo '<p data-anchor="gates-merge">After the owner says merge, ... a new merge ask.</p>' > "$t/docs/specs/issue-lifecycle.spec.html"
echo 'Merge: spec `#gates-merge`.' > "$t/agents/ok.md"
echo 'owner says merge, pinned to that head' > "$t/evidence/old.md"
printf '# reason: x\n--- a/SKILL.md\n+++ b/SKILL.md\n-Any code change after QC means qc again.\n' > "$t/.skillfile/patches/skills/x/SKILL.md.patch"
g add -A
run() { local want="$1"; set +e; out="$("$C" "$t" 2>&1)"; rc=$?; set -e
  [[ "$rc" == "$want" ]] || { echo "check-owned-rules test: want exit $want, got $rc: $out" >&2; exit 1; }; }
run 0
plant() { echo "$2" > "$t/$1"; g add -A; run 1
  grep -qF "$1:1: restates the $3 rule" <<<"$out" && grep -qF "$4" <<<"$out" || { echo "check-owned-rules test: $1 not named with its fix: $out" >&2; exit 1; }
  g rm -qf "$1"; run 0; }
plant agents/github.md 'Mechanical rebases onto accepted main do not require renewed acceptance when behavior and scope are unchanged.' merge-authority 'spec `#gates-merge`'
plant agents/impl.md 'Any code change after QC means `just qc` and a fresh review again, on the new head.' merge-authority 'spec `#gates-merge`'
plant agents/push.md '2. Verify the branch matches the target repo convention, else `octo-feather/gh<issue-number>-<slug>`.' lane-branch 'docs/adr/0011'
# A patch's added line is ours, so it is checked.
printf '# reason: x\n--- a/SKILL.md\n+++ b/SKILL.md\n+Main moving does not move the head.\n' > "$t/.skillfile/patches/skills/x/SKILL.md.patch"; g add -A; run 1
grep -qF 'SKILL.md.patch:4: restates the merge-authority rule' <<<"$out" || { echo "check-owned-rules test: patch line not named: $out" >&2; exit 1; }
echo "check-owned-rules: ok (owner, pointer, record pass; 3 past restatements and a patch line fail with their fix)"
