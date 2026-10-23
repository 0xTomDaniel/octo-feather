#!/usr/bin/env bash
# Integration test for scripts/check-behavior-smoke (a presence gate, docs/adr/0008) in a
# throwaway repo: absent base (skip locally, fail in CI), the lane #19 shape (af760a4: role
# text, no evidence), evidence plus docs/future.md fails (#80), evidence plus a
# docs/owed-evals/<issue>.md passes, evidence deleted again is no
# evidence, the Behaviour-neutral opt-out (all touching commits, printed), the pruning habit
# (#67: a role or patch change's evidence has a `Removed:` line; skill markdown alone needs none), per-path
# smoke (#93: each role path on a `Smoke:` line; the gh71 and gh67 shapes, one role's smoke covering another). The check runs
# with no git config at all; fixture commits set their identity by env. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
C="$kit/scripts/check-behavior-smoke"
g() { GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t git -C "$t" "$@"; }
sha() { git -C "$t" rev-parse --short=7 HEAD; }
run() { local want="$1"; shift; set +e
  out="$(env -u CI -u GITHUB_ACTIONS -u GITHUB_BASE_REF -u OCTO_FEATHER_BASE "$@" "$C" --repo "$t" 2>&1)"; rc=$?; set -e
  [[ "$rc" == "$want" ]] || { echo "check-behavior-smoke test: want exit $want, got $rc: $out" >&2; exit 1; }; }
has() { grep -qF -- "$1" <<<"$out" || { echo "check-behavior-smoke test: output lacks '$1': $out" >&2; exit 1; }; }

git init -q -b feature "$t"; git -C "$t" config user.useConfigOnly true
mkdir -p "$t/agents" "$t/docs/owed-evals" "$t/evidence"
echo 'Supervisor.' > "$t/agents/supervisor.md"; echo '# Future' > "$t/docs/future.md"
g add -A; g commit -qm base
# No base ref: skipped locally, a failure in CI.
run 0; has 'skipped, no base ref'
run 1 CI=true; has 'fetch-depth: 0'
g branch main
run 0; has 'no role path changed'

# Lane #19 shape (af760a4): role text changed, no evidence.
echo 'Supervisor asks first.' > "$t/agents/supervisor.md"; g commit -qam 'role: ask first'; role="$(sha)"
run 1; has '#26 missing-behavior-smoke'; has 'docs/adr/0008'; has "agents/supervisor.md ($role without Behaviour-neutral)"
has 'missing: an added or modified evidence/*.md and an added or modified docs/owed-evals/<issue>.md'; has 'Behaviour-neutral: <reason>'
# Evidence alone is not enough, nor with docs/future.md (#80); with docs/owed-evals/<issue>.md it passes.
echo "Probe at $role." > "$t/evidence/smoke.md"; g add -A; g commit -qm smoke
run 1; has 'missing: an added or modified docs/owed-evals/<issue>.md'; has 'owed eval in docs/owed-evals/<issue>.md'
echo '- ask first. Smoke: evidence/smoke.md' >> "$t/docs/future.md"; g commit -qam 'owed in future'
run 1; has 'missing: an added or modified docs/owed-evals/<issue>.md'
echo '- ask first. Smoke: evidence/smoke.md' > "$t/docs/owed-evals/19.md"; g add -A; g commit -qm owed
# Pruning habit (#67): smoke and owed eval, but nothing says what the role change removed.
run 1; has '#67 pruning habit'; has 'agents/supervisor.md'; has 'Fix: add a line `Removed: <what this change deleted, or the incident that justifies it>` to evidence/smoke.md'
echo 'Removed:' >> "$t/evidence/smoke.md"; g commit -qam 'empty removed'
run 1; has '#67 pruning habit'
echo 'Removed: nothing; incident #19 justifies it.' >> "$t/evidence/smoke.md"; g commit -qam 'removed line'
# Per-path smoke (#93): evidence that names no path on a `Smoke:` line covers none.
run 1; has '#93 missing-behavior-smoke'; has '  agents/supervisor.md'; has 'Smoke: <path> ...'
echo 'Smoke:' >> "$t/evidence/smoke.md"; g commit -qam 'empty smoke'
run 1; has '#93 missing-behavior-smoke'
echo 'Smoke: `agents/supervisor.md`, run 1 pass' >> "$t/evidence/smoke.md"; g commit -qam 'smoke line'
run 0; has 'evidence evidence/smoke.md, owed evals docs/owed-evals/19.md'
# Evidence deleted again is no net change: it fails.
g rm -q evidence/smoke.md; g commit -qm 'drop smoke'
run 1; has 'missing: an added or modified evidence/*.md'; has 'with a `Smoke: <path> ...` line naming each path it ran and a `Removed: <what it deleted, or the incident>` line'

# A patch change needs the line too; vendored skill markdown alone does not.
g checkout -q -b patch main
mkdir -p "$t/.skillfile/patches/skills/x" "$t/.agents/skills/x" "$t/evidence" "$t/docs/owed-evals"
echo '# reason: ADR 1' > "$t/.skillfile/patches/skills/x/SKILL.md.patch"; echo 'Probe.' > "$t/evidence/p.md"; echo '- x' > "$t/docs/owed-evals/67.md"
g add -A; g commit -qm 'patch x'
run 1 OCTO_FEATHER_BASE=main; has '#67 pruning habit'; has '.skillfile/patches/skills/x/SKILL.md.patch'
echo 'Removed: the Spec pass.' >> "$t/evidence/p.md"; g commit -qam 'removed'
run 1 OCTO_FEATHER_BASE=main; has '  .skillfile/patches/skills/x/SKILL.md.patch'
echo 'Smoke: .skillfile/patches/skills/x/' >> "$t/evidence/p.md"; g commit -qam 'smoke dir'
run 0 OCTO_FEATHER_BASE=main
g checkout -q -b skillmd main
mkdir -p "$t/.agents/skills/x" "$t/evidence" "$t/docs/owed-evals"; echo 'x' > "$t/.agents/skills/x/SKILL.md"; echo 'Smoke: .agents/skills/x/SKILL.md' > "$t/evidence/p.md"; echo '- x' > "$t/docs/owed-evals/67.md"
g add -A; g commit -qm 'skill md'
run 0 OCTO_FEATHER_BASE=main

# Lane gh71 shape (0035adc): director and corrector changed, the only evidence ran the corrector.
g checkout -q -b gh71 main; mkdir -p "$t/evidence" "$t/docs/owed-evals"
echo 'Director forwards calls.' > "$t/agents/director.md"; echo 'Corrector logs calls.' > "$t/agents/corrector.md"
printf 'Smoke: agents/corrector.md\nRemoved: nothing; incident #71.\n' > "$t/evidence/corrector.md"; echo '- calls' > "$t/docs/owed-evals/71.md"
g add -A; g commit -qm 'roles: calls'
run 1 OCTO_FEATHER_BASE=main; has '  agents/director.md'
! grep -qF '  agents/corrector.md' <<<"$out" || { echo "check-behavior-smoke test: smoked corrector.md listed: $out" >&2; exit 1; }
# A prose mention of the path is not a Smoke: line (gh67 a60d12c named corrector.md in a Changes list).
echo '- `agents/director.md` forwards calls.' >> "$t/evidence/corrector.md"; g commit -qam 'mention'
run 1 OCTO_FEATHER_BASE=main; has '  agents/director.md'
echo 'Smoke: agents/director.md' > "$t/evidence/director.md"; g add -A; g commit -qm 'director smoke'
run 0 OCTO_FEATHER_BASE=main

# Opt-out: a pointer-only rewrite fails without the trailer, passes with it, and the run names it.
g checkout -q -b neutral main
echo 'Supervisor: see spec #gates-merge.' > "$t/agents/supervisor.md"; g commit -qam 'role: pointer only'
run 1 OCTO_FEATHER_BASE=main
g commit -q --amend -m 'role: pointer only' -m 'Behaviour-neutral: pointer to the owner, no rule changed'; n1="$(sha)"
run 0 OCTO_FEATHER_BASE=main; has "opt-out $n1 Behaviour-neutral: pointer to the owner, no rule changed"; has 'all opted out'
# One later commit on that path without the trailer ends the exemption.
echo 'Supervisor: see spec #gates-merge; ask first.' > "$t/agents/supervisor.md"; g commit -qam 'role: ask first again'
run 1 OCTO_FEATHER_BASE=main; has 'without Behaviour-neutral'
# An empty reason is no opt-out.
g reset -q --hard HEAD^; g commit -q --amend -m 'role: pointer only' -m 'Behaviour-neutral:'
run 1 OCTO_FEATHER_BASE=main

# #121 N5: a role file renamed away is a changed role path, as a plain git rm is.
g checkout -q -b n5 main; mkdir -p "$t/docs"
g mv agents/supervisor.md docs/supervisor-old.md; g commit -qm 'move role away'
run 1 OCTO_FEATHER_BASE=main; has '#26 missing-behavior-smoke'; has '  agents/supervisor.md'
# #121 N6: skill markdown whose name holds a space or a non-ASCII character is still role text.
for name in 'my notes.md' 'café.md'; do
  g checkout -q -B n6 main; mkdir -p "$t/.agents/skills/x"; echo x > "$t/.agents/skills/x/$name"; g add -A; g commit -qm 'skill notes'
  run 1 OCTO_FEATHER_BASE=main; has '#26 missing-behavior-smoke'; has "  .agents/skills/x/$name"
done
# #121 N7: a Smoke: token naming the path, then sentence punctuation, names it.
g checkout -q -b n7 main; mkdir -p "$t/evidence" "$t/docs/owed-evals"
echo 'Supervisor asks.' >> "$t/agents/supervisor.md"; printf 'Smoke: agents/supervisor.md.\nRemoved: x\n' > "$t/evidence/zz.md"; echo '- x' > "$t/docs/owed-evals/backlog.md"
g add -A; g commit -qm 'role, smoke ends a sentence'
run 0 OCTO_FEATHER_BASE=main; has 'evidence evidence/zz.md'
# A Smoke: line names a path holding a space as written; another spaced path does not stand in for it.
g checkout -q -b spaced main; mkdir -p "$t/.agents/skills/x" "$t/evidence" "$t/docs/owed-evals"
echo x > "$t/.agents/skills/x/my notes.md"; echo 'Smoke: .agents/skills/x/my' > "$t/evidence/zz.md"; echo '- x' > "$t/docs/owed-evals/backlog.md"
g add -A; g commit -qm 'spaced skill md, other path smoked'
run 1 OCTO_FEATHER_BASE=main; has '#93 missing-behavior-smoke'; has '  .agents/skills/x/my notes.md'
echo 'Smoke: .agents/skills/x/my notes.md' > "$t/evidence/zz.md"; g commit -qam 'spaced path smoked'
run 0 OCTO_FEATHER_BASE=main; has 'evidence evidence/zz.md'
echo "check-behavior-smoke: ok (no git config; absent base skips locally, fails in CI; role change without evidence or docs/owed-evals/*.md fails, docs/future.md no longer counts, with both passes, deleted evidence fails; a role or patch change without a Removed: line fails naming the fix, passes with one; a role path on no Smoke: line fails (gh71, gh67 shapes), a directory token covers its files; the opt-out passes and is printed, one untagged commit or an empty reason fails; #121: a role renamed away fails (N5), skill markdown named with a space or non-ASCII fails (N6), a Smoke: path then a period passes (N7), a Smoke: path holding a space names it, a shorter spaced path does not)"
