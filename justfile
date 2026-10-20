# octo-feather kit commands. `just check` is the one gate (AGENTS.md).

set shell := ["bash", "-euo", "pipefail", "-c"]

root := justfile_directory()
export PATH := env_var('HOME') + "/.local/bin:" + root + "/scripts:" + root + "/.agents/skills/herdr-comms/assets:" + env_var('PATH')

default:
    @just --list

# The gate: script syntax, Pi-only and GitHub-only references, no dashes, skill frontmatter.
check: check-scripts check-refs check-dashes check-skills check-roles check-owned-rules check-behavior-smoke check-tests check-spec-status check-templates
    @echo "just check: ok"

# shellcheck when installed, else bash -n; python scripts byte-compile.
check-scripts:
    #!/usr/bin/env bash
    set -euo pipefail
    cd "{{root}}"
    files=(); py=()
    for f in scripts/* .agents/skills/herdr-comms/assets/* tests/*; do
      [[ -f "$f" ]] || continue   # tests/fixtures/ holds data, not scripts
      if head -1 "$f" | grep -q python; then py+=("$f"); else files+=("$f"); fi
    done
    for f in "${py[@]}"; do python3 -c 'import ast,sys; ast.parse(open(sys.argv[1]).read(), sys.argv[1])' "$f"; done
    echo "python: ok (${#py[@]} files)"
    if command -v shellcheck >/dev/null; then
      shellcheck -S warning "${files[@]}"; echo "scripts: shellcheck ok (${#files[@]} files)"
    else
      for f in "${files[@]}"; do bash -n "$f"; done; echo "scripts: bash -n ok (${#files[@]} files; shellcheck not installed)"
    fi
    for f in "${files[@]}" "${py[@]}"; do [[ -x "$f" ]] || { echo "not executable: $f" >&2; exit 1; }; done

# No CLAUDE.md, no .claude/.codex projections, no Linear, no octo-lite product names.
# Exempt: docs/ (ADRs name what was rejected), AGENTS.md, README.md, NOTICE,
# LICENSE, this justfile (docs/ also covers docs/specs/) and
# .skillfile/ patches, which quote the upstream lines they remove.
check-refs:
    #!/usr/bin/env bash
    set -euo pipefail
    cd "{{root}}"
    bad=0
    if git ls-files | grep -E '(^|/)(CLAUDE\.md|\.claude|\.codex)(/|$)'; then
      echo "check-refs: Claude/Codex projection files above are not allowed (docs/adr/0001)" >&2; bad=1; fi
    mapfile -t files < <(git ls-files | grep -vE '^(docs/|\.skillfile/|AGENTS\.md$|README\.md$|NOTICE$|LICENSE$|justfile$)')
    if grep -nHE '\bLinear\b' "${files[@]}"; then
      echo "check-refs: Linear references above; GitHub Issues is the tracker (docs/adr/0004)" >&2; bad=1; fi
    # Model ids (anthropic/claude-*) are a provider choice, not a runtime.
    if grep -nHiE 'claude|codex' "${files[@]}" | grep -vE 'anthropic/claude-[a-z0-9-]+'; then
      echo "check-refs: Claude/Codex references above; Pi is the only runtime (docs/adr/0001)" >&2; bad=1; fi
    # The gate and its check-* recipes never reach the product judge or factory evals.
    if awk '/^[A-Za-z]/{g = ($0 ~ /^check(-[a-z]+)?( [^:]*)?:/)} g' justfile | grep -nE '[Jj][e]v|\bq[a]\b|\bq[c]\b'; then
      echo "check-refs: the gate recipe lines above call the product judge or factory evals; just check stays deterministic and free (docs/future.md)" >&2; bad=1; fi
    # Retired words stay retired. Exempt: GLOSSARY.md (lists them), a spec anchor,
    # the corrector quoting pstack correct, and vendored skills (upstream wording).
    vend="$(awk '$1 == "github" {printf "%s|", $3}' Skillfile)"
    mapfile -t own < <(printf '%s\n' "${files[@]}" | grep -vE "^(\.agents/skills/(${vend%|})/|GLOSSARY\.md\$)")
    if grep -nHiE '\b(meta-)?operator\b|\bhumans?\b' "${own[@]}" | grep -vE '#handoff-operator|"The operator"'; then
      echo "check-refs: say director for the top agent and owner for the person (GLOSSARY.md)" >&2; bad=1; fi
    if grep -nHE 'octo-lite-|\.octo-lite|octo-lite:' "${files[@]}"; then
      echo "check-refs: octo-lite product names above; rename to octo-feather (attribution stays in NOTICE)" >&2; bad=1; fi
    [[ "$bad" == 0 ]] && echo "refs: ok (${#files[@]} files)"
    exit "$bad"

# No em or en dashes in kit text. Exempt upstream copies: docs/specs/ (Spec Chat's vendored runtime), LICENSE and
# vendored skills (the Skillfile's github entries in .agents/skills/, .skillfile/patches/),
# which keep upstream wording.
check-dashes:
    #!/usr/bin/env bash
    set -euo pipefail
    cd "{{root}}"
    vend="$(awk '$1 == "github" {printf "%s|", $3}' Skillfile)"
    mapfile -t files < <(git ls-files | grep -vE "^(docs/specs/|\.agents/skills/(${vend%|})/|\.skillfile/|LICENSE\$)")
    if grep -nHF -e "$(printf '\xe2\x80\x93')" -e "$(printf '\xe2\x80\x94')" "${files[@]}"; then
      echo "check-dashes: replace the em/en dashes above with a colon, comma or parentheses" >&2; exit 1; fi
    echo "dashes: ok (${#files[@]} files)"

# Every skill has name and description frontmatter; every role file exists.
check-skills:
    #!/usr/bin/env bash
    set -euo pipefail
    cd "{{root}}"
    n=0
    for f in .agents/skills/*/SKILL.md; do
      head -5 "$f" | grep -q '^name: ' && head -8 "$f" | grep -q '^description: ' || { echo "check-skills: $f lacks name/description frontmatter" >&2; exit 1; }
      n=$((n + 1))
    done
    for r in director supervisor implementer code-reviewer corrector; do
      [[ -f "agents/$r.md" ]] || { echo "check-skills: missing role contract agents/$r.md" >&2; exit 1; }
    done
    echo "skills: ok ($n skills, 5 roles)"

# Every template wires the same gate: AGENTS.md with a `Repo skills:` line, a
# justfile with `check` and `integrate`, a git hook and CI that run `just check`.
# Structure only; each template's own `just check` runs in its repo (deterministic, no network here).
check-templates:
    #!/usr/bin/env bash
    set -euo pipefail
    cd "{{root}}"
    n=0
    for t in templates/*/; do
      t="${t%/}"
      grep -q '^Repo skills:' "$t/AGENTS.md" || { echo "check-templates: $t/AGENTS.md lacks a 'Repo skills:' line" >&2; exit 1; }
      grep -q '^check:' "$t/justfile" && grep -q '^integrate ' "$t/justfile" && grep -q '^q[c] ' "$t/justfile" || { echo "check-templates: $t/justfile needs check, integrate and product-judge recipes (docs/adr/0022)" >&2; exit 1; }
      [[ -x "$t/.githooks/pre-commit" ]] && grep -q 'just check' "$t/.githooks/pre-commit" || { echo "check-templates: $t/.githooks/pre-commit must run just check" >&2; exit 1; }
      grep -q 'run: just check' "$t/.github/workflows/check.yml" || { echo "check-templates: $t CI must run just check" >&2; exit 1; }
      n=$((n + 1))
    done
    echo "templates: ok ($n)"

# Integration tests of the kit scripts, each in a throwaway repo (tests/*.sh).
check-tests:
    #!/usr/bin/env bash
    set -euo pipefail
    for t in "{{root}}"/tests/*.sh; do "$t"; done

# Every docs/specs/*.status.json names exactly its spec's criterion ids, planned or built (docs/adr/0021).
check-spec-status:
    @python3 "{{root}}/scripts/octo-feather-spec-status" check "{{root}}/docs/specs"

# Owner shaping chat in the target repo: Pi with only the shaping skills, not a factory role (docs/adr/0021).
shape *args:
    cd "{{invocation_directory()}}" && octo-feather-shape {{args}}

# Spec Chat's skills into REPO/.agents/skills as git-ignored links into $SPEC_CHAT_CLONE (default ~/src/spec-chat); no provider links (docs/adr/0001).
spec-chat repo:
    cd "{{invocation_directory()}}" && octo-feather-spec-chat "{{repo}}"

# Integrate worker commits onto lane gh<N>'s branch, then its `just check`; non-zero on any conflict (docs/adr/0017).
integrate issue +refs:
    cd "{{invocation_directory()}}" && octo-feather-integrate "{{issue}}" {{refs}}

# Role files: only fields pi-role honours, skills resolve, allowed models (docs/adr/0013).
check-roles:
    @python3 "{{root}}/scripts/check-roles"

# Each owned rule (merge authority, lane branch) is stated once, in its owner; elsewhere only a pointer (correction lane #19).
check-owned-rules:
    @python3 "{{root}}/scripts/check-owned-rules"

# A role path changed on this branch needs evidence/*.md and docs/future.md in the same diff, or Behaviour-neutral commits (docs/adr/0008, correction lane #26). Base: origin/main or the CI PR base; none: skips locally, fails in CI.
check-behavior-smoke:
    @python3 "{{root}}/scripts/check-behavior-smoke"

# Verify the runtime tools on this box (octo-lite's install --check equivalent).
install-check:
    #!/usr/bin/env bash
    set -uo pipefail
    bad=0
    for t in herdr pi gh jq git just python3; do
      if p="$(command -v "$t")"; then printf '%-6s ok  %s\n' "$t" "$p"
      else printf '%-6s MISSING\n' "$t"; bad=1; fi
    done
    gh auth status >/dev/null 2>&1 && echo "gh     authenticated" || { echo "gh     NOT authenticated (gh auth login)"; bad=1; }
    exit "$bad"

# Start the director in Herdr workspace `director` (docs/adr/0011).
start cwd=invocation_directory():
    octo-feather-start --director --cwd "{{cwd}}"

# Start one supervisor for GitHub issue N in workspace gh<N>, tab `supervisor`.
supervise issue cwd=invocation_directory():
    octo-feather-start --issue "{{issue}}" --cwd "{{cwd}}"

# Product QC: a fresh cross-family judge runs each claimed criterion; passed ones become built (docs/adr/0022). Never inside `just check`.
qc status pr +ids:
    cd "{{invocation_directory()}}" && octo-feather-qc "{{status}}" "{{pr}}" {{ids}}

# Factory QA: evals of the kit's own agents and loop. Not implemented yet (docs/future.md); never inside `just check`.
qa *args:
    @echo "just qa: not implemented yet (factory evals, docs/future.md)" >&2; exit 2

# Print this Herdr session's octo-feather state directory.
state:
    @octo-feather-state

# New target repo at DEST from templates/LANG: tracked files, one commit on main, Spec Chat links unless --no-spec-chat; never `just setup` or GitHub (#21).
# Arguments reach bash as exported variables, never as interpolated source.
new-repo $lang $dest *$flags:
    cd "{{invocation_directory()}}" && octo-feather-new-repo "$lang" "$dest" $flags
