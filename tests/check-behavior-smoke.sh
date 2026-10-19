#!/usr/bin/env bash
# Integration test for scripts/check-behavior-smoke in a throwaway repo: the two
# shapes correction lane #26 logged as missing-behavior-smoke (lane #19 af760a4:
# no evidence; lane #8 db9e290: evidence only in the role commit itself, citing
# no branch commit), their fixes, the Behaviour-neutral opt-out, and the base
# handling (absent base: skip locally, fail in CI). Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
C="$kit/scripts/check-behavior-smoke"
g() { git -C "$t" -c user.name=t -c user.email=t@t "$@"; }
sha() { git -C "$t" rev-parse --short=7 HEAD; }
run() { local want="$1"; shift; set +e
  out="$(env -u CI -u GITHUB_ACTIONS -u GITHUB_BASE_REF -u OCTO_FEATHER_BASE "$@" "$C" --repo "$t" 2>&1)"; rc=$?; set -e
  [[ "$rc" == "$want" ]] || { echo "check-behavior-smoke test: want exit $want, got $rc: $out" >&2; exit 1; }; }
has() { grep -qF -- "$1" <<<"$out" || { echo "check-behavior-smoke test: output lacks '$1': $out" >&2; exit 1; }; }

git init -q -b feature "$t"; mkdir -p "$t/agents" "$t/docs" "$t/evidence"
echo 'Supervisor.' > "$t/agents/supervisor.md"
printf '# Future\n\n## Owed eval cases\n\nIntro.\n\n- old. Smoke: `evidence/old.md`.\n<!-- owed-evals-end -->\n' > "$t/docs/future.md"
g add -A; g commit -qm base
# No base ref at all: skipped locally, a failure in CI.
run 0; has 'skipped, no base ref'
run 1 CI=true; has 'fetch-depth: 0'
g branch main
run 0; has 'no behaviour change'                      # nothing ahead of main

# Lane #19 shape (af760a4): role text changed, no evidence.
echo 'Supervisor asks first.' > "$t/agents/supervisor.md"; g commit -qam 'role: ask first'; role="$(sha)"
run 1; has '#26 missing-behavior-smoke'; has 'docs/adr/0008'; has "$role role: ask first: agents/supervisor.md"; has 'Behaviour-neutral: <reason>'
# Lane #8 shape (db9e290): evidence and owed line in the role commit itself, citing no branch commit.
echo 'Supervisor asks first, twice.' > "$t/agents/supervisor.md"; echo 'Chain at e0843940858b.' > "$t/evidence/smoke.md"
sed -i 's|^<!-- owed-evals-end -->|- ask first. Smoke: `evidence/smoke.md`.\n&|' "$t/docs/future.md"
g add -A; g commit -qm 'role: twice, smoke noted'; role="$(sha)"
run 1; has "no evidence/*.md changed after $role"
# The fix, uncommitted: a later smoke naming the role text commit counts from the tree.
echo "Probe at $role: as designed." >> "$t/evidence/smoke.md"
run 0; has 'smoke evidence/smoke.md'
g commit -qam "evidence: smoke at $role"
run 0
# A smoke with no owed line naming it fails.
echo 'Supervisor asks first, thrice.' > "$t/agents/supervisor.md"; g commit -qam 'role: thrice'; role="$(sha)"
echo "Probe at $role." > "$t/evidence/smoke2.md"; g add -A; g commit -qm smoke2
run 1; has 'no line above'
# A merge of main bringing main's own smoke is not this branch's smoke.
g checkout -q main; mkdir -p "$t/evidence"; echo "Main probe at $role." > "$t/evidence/main.md"
sed -i '/^- old/i - main. Smoke: `evidence/main.md`.' "$t/docs/future.md"; g add -A; g commit -qm main-smoke
g checkout -q feature; g merge -q --no-edit main >/dev/null
run 1
sed -i 's|^<!-- owed-evals-end -->|- thrice. Smoke: `evidence/smoke2.md`.\n&|' "$t/docs/future.md"; g commit -qam owed
run 0

# Opt-out: a pointer-only rewrite fails without the trailer, passes with it, and the run names it.
g checkout -q -b neutral main
echo 'Supervisor: see spec #gates-merge.' > "$t/agents/supervisor.md"; g commit -qam 'role: pointer only'
run 1 OCTO_FEATHER_BASE=main
g commit -q --amend -m 'role: pointer only' -m 'Behaviour-neutral: pointer to the owner, no rule changed'
run 0 OCTO_FEATHER_BASE=main; has 'opt-out'; has 'Behaviour-neutral: pointer to the owner'

# Review of 2bcd546, repro 2: a smoke deleted after it qualified no longer counts, though the owed line names it.
g checkout -q feature; g rm -q evidence/smoke2.md; g commit -qm 'drop smoke2'
run 1; has 'still at the checked head'
g revert --no-edit HEAD >/dev/null; run 0

# Review of 2bcd546, repro 1: a conflict resolution in a merge of main writes new role behaviour.
g checkout -q -b conflict main
L='\na\nb\nc\nLine five.\n'
printf "Line one.$L" > "$t/agents/director.md"; g add -A; g commit -qm 'director file'; g branch -f main HEAD
printf "Line one, see #gates-merge.$L" > "$t/agents/director.md"
g commit -qam 'director: pointer only' -m 'Behaviour-neutral: pointer to the owner'
g checkout -q main; printf "Line one, main wording.$L" > "$t/agents/director.md"; g commit -qam 'main: reword line one'
g checkout -q conflict; g merge -q --no-edit main >/dev/null 2>&1 || true
printf "Line one: the director now merges itself.$L" > "$t/agents/director.md"; g add -A; g commit -q --no-edit
merge="$(sha)"
run 1; has "$merge Merge branch 'main' into conflict: agents/director.md"
# Resolving to one side wholesale writes nothing new: ok, the pointer commit stays an opt-out.
g reset -q --hard HEAD^; g merge -q --no-edit -X ours main >/dev/null
run 0; has 'opt-out'
# A conflict-free merge of main that changed another line of the same role file is main's, not the branch's.
g checkout -q -b clean main
printf "Line one, main wording.\na\nb\nc\nLine five, see #gates-merge.\n" > "$t/agents/director.md"
g commit -qam 'director: pointer line five' -m 'Behaviour-neutral: pointer to the owner'
g checkout -q main; printf "Line one, main again.$L" > "$t/agents/director.md"; g commit -qam 'main: line one again'
g checkout -q clean; g merge -q --no-edit main >/dev/null
grep -qxF 'Line five, see #gates-merge.' "$t/agents/director.md" && grep -qxF 'Line one, main again.' "$t/agents/director.md"
run 0; has '1 opted out'
echo "check-behavior-smoke: ok (absent base skips locally, fails in CI; lane #19 and #8 shapes, no owed line and main's smoke fail; later cited smoke with owed line, and the opt-out, pass; a deleted smoke and a merge's new conflict resolution fail; a one-side resolution and a conflict-free merge of main pass)"
