#!/usr/bin/env bash
# Integration test for `just new-repo LANG DEST` (scripts/octo-feather-new-repo),
# offline: no uv, pnpm or network, HOME redirected, a fake Spec Chat clone whose
# installer links skills like the real one. Each template gives a repo with
# exactly its tracked files, one commit on main, clean status; every refusal
# names its fix and creates nothing. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
t="$(cd "$t" && pwd -P)"
fail() { echo "new-repo test: $*" >&2; exit 1; }
export HOME="$t/home" XDG_STATE_HOME="$t/state" XDG_CONFIG_HOME="$t/config" GIT_CONFIG_NOSYSTEM=1
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
mkdir -p "$HOME" "$t/work"

clone="$t/clone"; mkdir -p "$clone/scripts"
for s in shape-spec review-spec repair-specs; do mkdir -p "$clone/skill/$s"; echo "# $s" > "$clone/skill/$s/SKILL.md"; done
cat > "$clone/scripts/install-spec-chat" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd -P)"
prefix=""; while [[ $# -gt 0 ]]; do [[ "$1" == --prefix ]] && { prefix="$2"; shift; }; shift; done
mkdir -p "$prefix/.agents/skills"
for p in spec-chat-shape:shape-spec spec-chat-review:review-spec repair-specs:repair-specs; do
  ln -s "$root/skill/${p#*:}" "$prefix/.agents/skills/${p%%:*}"
done
EOF
chmod +x "$clone/scripts/install-spec-chat"
export SPEC_CHAT_CLONE="$clone"

run() { (cd "$t/work" && just --justfile "$kit/justfile" new-repo "$@"); }
# tracked files of a repo, or of a template dir, sorted
tracked() { git -C "$1" ls-files | sort; }
ondisk() { (cd "$1" && find . \( -name .git -o -name .agents \) -prune -o \( -type f -o -type l \) -print | sed 's|^\./||' | sort); }

mapfile -t langs < <(git -C "$kit" ls-files -- templates | cut -d/ -f2 | sort -u)
[[ ${#langs[@]} -ge 2 ]] || fail "expected at least two templates, got: ${langs[*]}"
sha="$(git -C "$kit" rev-parse --short HEAD)"
for lang in "${langs[@]}"; do
  for mode in links none; do
    d="$t/work/$lang-$mode"
    if [[ "$mode" == links ]]; then out="$(run "$lang" "$lang-$mode" 2>&1)" || fail "$lang: $out"
    else out="$(run "$lang" "$lang-$mode" --no-spec-chat 2>&1)" || fail "$lang --no-spec-chat: $out"; fi
    want="$(tracked "$kit/templates/$lang")"
    [[ "$(tracked "$d")" == "$want" ]] || fail "$lang-$mode: tracked files differ from templates/$lang"
    [[ "$(ondisk "$d")" == "$want" ]] || fail "$lang-$mode: files on disk differ from templates/$lang: $(diff <(ondisk "$d") <(echo "$want") || true)"
    [[ -x "$d/.githooks/pre-commit" ]] || fail "$lang-$mode: hook lost its executable mode"
    [[ "$(git -C "$d" rev-list --count --all)" == 1 ]] || fail "$lang-$mode: not exactly one commit"
    [[ "$(git -C "$d" symbolic-ref --short HEAD)" == main ]] || fail "$lang-$mode: branch is not main"
    [[ "$(git -C "$d" log -1 --format=%s)" == "Initial commit from octo-feather templates/$lang @ $sha" ]] || fail "$lang-$mode: commit subject: $(git -C "$d" log -1 --format=%s)"
    [[ -z "$(git -C "$d" status --porcelain)" ]] || fail "$lang-$mode: git status not clean: $(git -C "$d" status --porcelain)"
    [[ -z "$(git -C "$d" config --get core.hooksPath || true)" ]] || fail "$lang-$mode: set core.hooksPath (that is just setup's job)"
    grep -q 'just setup' <<<"$out" && grep -q 'gh repo create' <<<"$out" || fail "$lang-$mode: next steps not printed: $out"
    if [[ "$mode" == links ]]; then
      for s in spec-chat-shape spec-chat-review repair-specs; do
        [[ -L "$d/.agents/skills/$s" ]] || fail "$lang: missing Spec Chat link $s"
        grep -qxF "/.agents/skills/$s" "$d/.git/info/exclude" || fail "$lang: link $s not ignored"
      done
    else
      [[ ! -e "$d/.agents" ]] || fail "$lang --no-spec-chat: .agents exists"
    fi
  done
done

# Refusals: non-zero, the fix named, DEST absent or unchanged.
refuse() { # name grep-pattern dest-to-check args...
  local name="$1" pat="$2" chk="$3"; shift 3
  local before; before="$(ls -A "$chk" 2>/dev/null || echo ABSENT)"
  out="$(run "$@" 2>&1)" && fail "$name: succeeded"
  grep -qE -- "$pat" <<<"$out" || fail "$name: error names no fix: $out"
  [[ "$(ls -A "$chk" 2>/dev/null || echo ABSENT)" == "$before" ]] || fail "$name: DEST changed"
}
mkdir -p "$t/work/full"; echo x > "$t/work/full/keep"
refuse "non-empty DEST" 'not empty; pass a new or empty' "$t/work/full" python full
refuse "DEST is HOME" 'HOME' "$HOME" python "$HOME"
mkdir -p "$t/work/outer"; git -c init.defaultBranch=main init -q "$t/work/outer"
refuse "inside a work tree" "inside the git work tree $t/work/outer" "$t/work/outer/sub" python outer/sub
refuse "unknown LANG" "pick one of: ${langs[*]}" "$t/work/nolang" rust nolang
refuse "missing DEST" 'usage' "$t/work" python
SPEC_CHAT_CLONE="$t/nope" refuse "missing Spec Chat clone" 'SPEC_CHAT_CLONE.*--no-spec-chat' "$t/work/noclone" python noclone

# Identity fallback, on a throwaway kit copy (the real checkout's config is shared,
# never written): no identity for DEST and none in the kit refuses; a kit-local one is used.
copy="$t/kit"; mkdir -p "$copy"
(cd "$kit" && git ls-files -z -- justfile scripts templates | tar --null -T - -cf -) | tar -xpf - -C "$copy"
git -c init.defaultBranch=main init -q "$copy"; git -C "$copy" add -A; git -C "$copy" commit -qm copy
(unset GIT_AUTHOR_NAME GIT_COMMITTER_NAME GIT_AUTHOR_EMAIL GIT_COMMITTER_EMAIL
  kit="$copy"
  refuse "no git identity" 'git config --global user.name' "$t/work/noid" python noid --no-spec-chat
  git -C "$copy" config user.name kitname; git -C "$copy" config user.email kit@example.com
  out="$(run python kitid --no-spec-chat 2>&1)" || fail "kit identity fallback: $out"
  grep -q "kitname <kit@example.com> (the kit checkout's" <<<"$out" || fail "identity used not printed: $out"
  [[ "$(git -C "$t/work/kitid" log -1 --format='%an <%ae> %cn <%ce>')" == 'kitname <kit@example.com> kitname <kit@example.com>' ]] \
    || fail "commit not by the kit identity: $(git -C "$t/work/kitid" log -1 --format='%an <%ae> %cn <%ce>')")
grep -q 't <t@t> (your git identity)' <<<"$(run python ownid --no-spec-chat 2>&1)" || fail "caller identity not used or not printed"

[[ -z "$(find "$HOME" -mindepth 1)" ]] || fail "created under HOME: $(find "$HOME" -mindepth 1)"
echo "new-repo: ok (${langs[*]}: tracked files only, one commit on main, clean status, links or none; 7 refusals create nothing; kit identity fallback; nothing in HOME)"
