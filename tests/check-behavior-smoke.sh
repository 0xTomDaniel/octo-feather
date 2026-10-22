#!/usr/bin/env bash
# Integration test for scripts/check-behavior-smoke (a presence gate, docs/adr/0008) in a
# throwaway repo: absent base (skip locally, fail in CI), the lane #19 shape (af760a4: role
# text, no evidence), evidence plus docs/future.md fails (#80), evidence plus a
# docs/owed-evals/<issue>.md passes, evidence deleted again is no
# evidence, the Behaviour-neutral opt-out (all touching commits, printed). The check runs
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
run 0; has 'evidence evidence/smoke.md, owed evals docs/owed-evals/19.md'
# Evidence deleted again is no net change: it fails.
g rm -q evidence/smoke.md; g commit -qm 'drop smoke'
run 1; has 'missing: an added or modified evidence/*.md'

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
echo "check-behavior-smoke: ok (no git config; absent base skips locally, fails in CI; role change without evidence or docs/owed-evals/*.md fails, docs/future.md no longer counts, with both passes, deleted evidence fails; the opt-out passes and is printed, one untagged commit or an empty reason fails)"
