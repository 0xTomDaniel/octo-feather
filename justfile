# octo-feather kit commands. `just check` is the one gate (AGENTS.md).

set shell := ["bash", "-euo", "pipefail", "-c"]
# Recipe arguments reach the shell as "$@"/"$1", never as pasted text (#61).
set positional-arguments

# Exported so recipes use "$root" as data, never pasted text (#61).
export root := justfile_directory()
# macOS: GNU coreutils and util-linux (realpath -m, readlink -f, timeout, setsid, uuidgen),
# Homebrew's bash 5 and python3, and mise's shims, ahead of the system's; missing dirs are skipped by the shell.
# The running just's own dir comes first so recipes and tests find it without a mise shim.
mac_path := if os() == "macos" { "/opt/homebrew/opt/coreutils/libexec/gnubin:/usr/local/opt/coreutils/libexec/gnubin:/opt/homebrew/opt/util-linux/bin:/usr/local/opt/util-linux/bin:/opt/homebrew/bin:/usr/local/bin:" + env_var('HOME') + "/.local/share/mise/shims:" } else { "" }
export PATH := env_var('HOME') + "/.local/bin:" + root + "/scripts:" + root + "/.agents/skills/herdr-comms/assets:" + parent_directory(just_executable()) + ":" + mac_path + env_var('PATH')
# The gate never reaches the product judge or factory evals (quality #acceptance-gate-no-model). just evaluates
# this before any recipe runs, so a check or check-* recipe reaching qa, qc or Jev, by dependency or body, fails
# every run before one starts. Anything but the script's exact ok line fails closed; the one other value is the
# backtick's own text, which `just --dry-run` substitutes without running it (or any recipe).
# Backticks run in --working-directory when given: there the guard is the published command on PATH.
gate_free_out := `f=scripts/check-gate-free; [[ -x "$f" ]] || f=check-gate-free; exec "$f"`
# The scan cannot see into the repo scripts a recipe runs: a check run also exports a marker (the outermost check
# run's just pid) that nested just runs and tools inherit; qa and octo-feather-qc refuse under it (check-gate-free --refuse).
export OCTO_FEATHER_CHECK_RUN := `f=scripts/check-gate-free; [[ -x "$f" ]] || f=check-gate-free; exec "$f" --run`
gate_free := if gate_free_out == "gate-free: ok" { "ok" } else if gate_free_out == "`f=scripts/check-gate-free; [[ -x \"$f\" ]] || f=check-gate-free; exec \"$f\"`" { "dry run" } else { error("check-gate-free did not pass (message above); just check stays deterministic and free") }

default:
    @just --list

# The gate: script syntax, Pi-only references, no dashes, skill frontmatter, decision logs, vendored skills.
check: check-scripts check-refs check-dashes check-skills check-decision-log check-roles check-behavior-smoke check-vendored check-tests check-spec-status check-templates
    @echo "just check: ok"

# shellcheck when installed, else bash -n; python scripts byte-compile.
check-scripts:
    #!/usr/bin/env bash
    set -euo pipefail
    cd "$root"
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

# No CLAUDE.md, no .claude/.codex projections, no octo-lite product names, no lane branch default.
# Exempt: docs/ (ADRs name what was rejected), AGENTS.md, README.md, NOTICE,
# LICENSE, this justfile (docs/ also covers docs/specs/) and
# .skillfile/ patches, which quote the upstream lines they remove.
check-refs:
    #!/usr/bin/env bash
    set -euo pipefail
    cd "$root"
    bad=0
    if git ls-files | grep -iE '(^|/)(CLAUDE(\.local)?\.md|AGENTS\.override\.md|\.claude|\.codex)(/|$)'; then
      echo "check-refs: Claude/Codex instruction files or projections above are not allowed; Pi is the only runtime, AGENTS.md the only instruction file (docs/adr/0001)" >&2; bad=1; fi
    mapfile -t files < <(git ls-files | grep -vE '^(docs/|\.skillfile/|AGENTS\.md$|README\.md$|NOTICE$|LICENSE$|justfile$)')
    # Model ids (anthropic/claude-*) are a provider choice, not a runtime.
    if grep -nHiE 'claude|codex' "${files[@]}" | grep -vE 'anthropic/claude-[a-z0-9-]+'; then
      echo "check-refs: Claude/Codex references above; Pi is the only runtime (docs/adr/0001)" >&2; bad=1; fi
    # Retired words stay retired in all kit text, docs/ and this justfile included
    # (the pattern brackets a letter so it does not match itself). Exempt files:
    #   GLOSSARY.md: lists the retired words.
    #   vendored skills (Skillfile github entries) and .skillfile/: upstream wording and quotes of it.
    #   docs/specs/.viz/, docs/specs/.style/: Spec Chat's vendored runtime and style (NOTICE).
    #   LICENSE: the upstream Apache-2.0 text.
    # Exempt quotes of frozen or upstream text, not kit naming: each a (file, exact quote)
    # pair in the table below, removed only in that file, then the rest of its line is scanned.
    vend="$(awk '$1 == "github" {printf "%s|", $3}' Skillfile)"
    mapfile -t own < <(git ls-files | grep -vE "^(\.agents/skills/(${vend%|})/|\.skillfile/|docs/specs/\.(viz|style)/|GLOSSARY\.md\$|LICENSE\$)")
    # Fails closed: grep exit 0 or 1 and perl exit 0 are the only scans; match is perl output, no match none,
    # any other exit a scanner error that fails the check.
    retired='\b(meta-)?[o]perators?\b|\b[h]umans?\b'
    rc=0; hits="$(grep -nHiE "$retired" "${own[@]}")" || rc=$?
    if (( rc > 1 )); then
      echo "check-refs: retired-words scanner error: grep exited $rc (message above); fix the scan, the check cannot pass" >&2; bad=1; hits=""; fi
    rc=0; found="$(RETIRED="$retired" perl -ne '
        BEGIN { %ok = (
          # Frozen spec anchor kept from octo-lite (docs/adr/0021): its definition, the index map, its one citer.
          "docs/specs/comms.spec.html"    => [qr{data-anchor="handoff-[o]perator(-wrap)?"}],
          "docs/specs/index.spec.html"    => [qr{data-anchor="map-handoff-[o]perator"}, qr{#handoff-[o]perator(?=[<"])}],
          "agents/director.md"            => [qr{`#handoff-[o]perator`}],
          # The frozen #acceptance-retired-words criterion names the words it retires.
          "docs/specs/overview.spec.html" => [qr{calls the top agent [o]perator or the person [h]uman}],
          # The corrector quotes vendored pstack correct.
          "agents/corrector.md"           => [qr{"The [o]perator" there is the owner}],
          # NOTICE attribution names the octo-lite file the director came from.
          "NOTICE"                        => [qr{\(was agents/meta-[o]perator\.md\)}],
          # Spec Chat names the owner side of a spool (its directory and event actor) so on disk: the one SPOOL_SIDE value per file.
          "scripts/octo-feather-accepted" => [qr{^SPOOL_SIDE = "[h]uman"(?=\s)}],
          "tests/accepted.sh"             => [qr{^SPOOL_SIDE=[h]uman(?=;)}],
        ) }
        my ($f, $s) = /^(.*?):\d+:(.*)$/s;
        $s =~ s/$_//g for @{ $ok{$f} || [] };
        if ($s =~ /$ENV{RETIRED}/i) { print }' <<<"$hits")" || rc=$?
    if (( rc != 0 )); then
      echo "check-refs: retired-words scanner error: perl exited $rc (message above); fix the scan, the check cannot pass" >&2; bad=1
    elif [[ -n "$found" ]]; then
      printf '%s\n' "$found"
      echo "check-refs: retired words above; use director for the top agent and owner for the person (GLOSSARY.md)" >&2; bad=1; fi
    # The lane branch is stated once, in docs/adr/0011: fixed strings of a slugged branch default, no regex (docs/adr/0008).
    if grep -nHF -e 'octo-feather/gh<' -e 'gh<N>-<' "${files[@]}"; then
      echo "check-refs: lane branch default above; the lane branch is \`gh<N>\`: write only a pointer, docs/adr/0011" >&2; bad=1; fi
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
    cd "$root"
    vend="$(awk '$1 == "github" {printf "%s|", $3}' Skillfile)"
    mapfile -t files < <(git ls-files | grep -vE "^(docs/specs/|\.agents/skills/(${vend%|})/|\.skillfile/|LICENSE\$)")
    if grep -nHF -e "$(printf '\xe2\x80\x93')" -e "$(printf '\xe2\x80\x94')" "${files[@]}"; then
      echo "check-dashes: replace the em/en dashes above with a colon, comma or parentheses" >&2; exit 1; fi
    echo "dashes: ok (${#files[@]} files)"

# Every skill opens with a --- frontmatter block with non-empty name and description; every role file exists.
check-skills:
    @python3 "$root/scripts/check-skills"

# Every tracked decisions.jsonl, anywhere in the repo: each line one JSON object matching schemas/decision-log.schema.json (quality #decision-log, docs/adr/0010).
check-decision-log:
    @python3 "$root/scripts/check-decision-log"

# Every template wires the same gate: AGENTS.md with a `Repo skills:` line, a
# justfile with `check` and `integrate`, a git hook and CI that run `just check`.
# Structure only; each template's own `just check` runs in its repo (deterministic, no network here).
check-templates:
    #!/usr/bin/env bash
    set -euo pipefail
    cd "$root"
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
    # macOS: mktemp paths under the /var symlink would not match the tests' pwd -P paths.
    TMPDIR="$(cd "${TMPDIR:-/tmp}" && pwd -P)"; export TMPDIR
    for t in "$root"/tests/*.sh; do "$t"; done

# Every docs/specs/*.status.json names exactly its spec's criterion ids, planned or built, and every spec change
# since its accepted_commit is named by a call in <slug>.calls.jsonl (docs/adr/0021, issue-lifecycle #gates-spec-calls).
check-spec-status:
    @python3 "$root/scripts/octo-feather-spec-status" check "$root/docs/specs"

# Each vendored skill folder equals upstream at its Skillfile pin plus its patches (skills spec #acceptance-patch-only).
# No network: reads the authenticated pin-SHA cache `just vendored-fetch` fills; a missing cache fails naming it.
check-vendored:
    @python3 "{{root}}/scripts/check-vendored"

# Fill the check-vendored cache: pinned skillfile binary, each Skillfile pin commit (fetch-only Spec Chat included, #96), every call time-bounded. Never inside `just check`.
vendored-fetch:
    @python3 "{{root}}/scripts/check-vendored" --fetch

# Owner shaping chat in the target repo: Pi with only the shaping skills, not a factory role (docs/adr/0021).
[no-cd]
shape *args:
    octo-feather-shape "$@"

# Spec Chat's skills into REPO/.agents/skills as git-ignored links into $SPEC_CHAT_CLONE (default ~/src/spec-chat); no provider links (docs/adr/0001).
[no-cd]
spec-chat repo:
    octo-feather-spec-chat "$1"

# Integrate worker commits onto the lane's branch (its lane key: gh12, eng-123 for ENG-123), then its `just check`; non-zero on any conflict (docs/adr/0017).
[no-cd]
integrate issue +refs:
    octo-feather-integrate "$@"

# Role files: only fields pi-role honours, skills resolve, allowed models (docs/adr/0013).
check-roles:
    @python3 "$root/scripts/check-roles"

# A role path changed on this branch needs evidence/*.md and docs/owed-evals/*.md in the same diff, or Behaviour-neutral commits (docs/adr/0008, correction lane #26). Base: origin/main or the CI PR base; none: skips locally, fails in CI.
check-behavior-smoke:
    @python3 "$root/scripts/check-behavior-smoke"

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
    octo-feather-start --director --cwd "$1"

# Start one supervisor for a ticket as the tracker writes it (12, ENG-123) in workspace named by its lane key (gh12, eng-123), tab `supervisor`.
supervise issue cwd=invocation_directory():
    octo-feather-start --issue "$1" --cwd "$2"

# Product QC: a fresh cross-family judge runs each claimed criterion; passed ones become built (docs/adr/0022). Never inside `just check`.
# Arguments reach bash as "$@" and exported variables, never as interpolated source (#30, #61).
[no-cd]
qc $status $pr +$ids:
    octo-feather-qc "$@"

# Factory QA: evals of the kit's own agents and loop. Not implemented yet (docs/future.md); never inside `just check`.
qa *args:
    @[[ "$(check-gate-free --refuse 'just qa (factory evals)')" == "gate-free: ok" ]]
    @echo "just qa: not implemented yet (factory evals, docs/future.md)" >&2; exit 2

# Print this Herdr session's octo-feather state directory.
state:
    @octo-feather-state

# New target repo at DEST from templates/LANG: tracked files, one commit on main, Spec Chat links unless --no-spec-chat; never `just setup` or GitHub (#21).
# Arguments reach bash as "$@" and exported variables, never as interpolated source (#61).
[no-cd]
new-repo $lang $dest *$flags:
    octo-feather-new-repo "$@"

# Opt-in, never part of `just check`: tests/qc.sh with the box's real herdr (QC_TEST_HERDR=real) for the
# sandbox pane proof: a judge's pane runs in its PID namespace, reaches no live session and dies with the run.
# Offline like the gate; a throwaway HOME with its own "live" session, the box's sessions untouched. Needs herdr on PATH.
qc-real-herdr:
    QC_TEST_HERDR=real "$root/tests/qc.sh"
