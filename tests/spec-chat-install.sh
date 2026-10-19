#!/usr/bin/env bash
# Integration test for `just spec-chat REPO` (scripts/octo-feather-spec-chat),
# offline: a fake Spec Chat clone whose installer stub records its argv and links
# skills like the real one. Links land in REPO/.agents/skills, ignored in
# info/exclude once, nothing under HOME, no provider dirs. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
t="$(cd "$t" && pwd -P)"
fail() { echo "spec-chat-install test: $*" >&2; exit 1; }
export HOME="$t/home" XDG_STATE_HOME="$t/state"; mkdir -p "$HOME"

clone="$t/clone"; mkdir -p "$clone/scripts"
for s in shape-spec review-spec repair-specs; do mkdir -p "$clone/skill/$s"; echo "# $s" > "$clone/skill/$s/SKILL.md"; done
cat > "$clone/scripts/install-spec-chat" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd -P)"
printf '%s\n' "$@" > "$root/argv"
prefix=""; while [[ $# -gt 0 ]]; do [[ "$1" == --prefix ]] && { prefix="$2"; shift; }; shift; done
mkdir -p "$prefix/.agents/skills" "$XDG_STATE_HOME/spec-chat"
for p in spec-chat-shape:shape-spec spec-chat-review:review-spec repair-specs:repair-specs; do
  [[ -L "$prefix/.agents/skills/${p%%:*}" ]] || ln -s "$root/skill/${p#*:}" "$prefix/.agents/skills/${p%%:*}"
done
echo 'status = "pending"' > "$XDG_STATE_HOME/spec-chat/onboarding.toml"
echo "fake installer: linked into $prefix"
EOF
chmod +x "$clone/scripts/install-spec-chat"

repo="$t/work/repo"; mkdir -p "$repo"; git -c init.defaultBranch=main init -q "$repo"
# A committed link elsewhere is the repo's own: never ignored.
mkdir -p "$repo/.agents/skills"; ln -s /tmp "$repo/.agents/skills/own"
git -C "$repo" add -A; git -C "$repo" -c user.name=t -c user.email=t@t commit -qm init

run() { (cd "$t/work" && SPEC_CHAT_CLONE="$1" just --justfile "$kit/justfile" spec-chat "$2"); }

for i in 1 2; do
  out="$(run "$clone" repo 2>&1)" || fail "run $i failed: $out"
  grep -q "fake installer: linked into $repo" <<<"$out" || fail "installer output not passed through: $out"
done
want=$'--agents-only\n--prefix\n'"$repo"
[[ "$(cat "$clone/argv")" == "$want" ]] || fail "installer argv: $(tr '\n' ' ' < "$clone/argv")"
for s in spec-chat-shape spec-chat-review repair-specs; do
  [[ -L "$repo/.agents/skills/$s" && -f "$repo/.agents/skills/$s/SKILL.md" ]] || fail "missing link $s"
done
[[ -z "$(git -C "$repo" status --porcelain)" ]] || fail "git status not clean: $(git -C "$repo" status --porcelain)"
excl="$repo/.git/info/exclude"
for s in spec-chat-shape spec-chat-review repair-specs; do
  [[ "$(grep -cxF "/.agents/skills/$s" "$excl")" == 1 ]] || fail "exclude line for $s not exactly once"
done
! grep -q 'skills/own' "$excl" || fail "repo's own link was ignored"
[[ -z "$(find "$HOME" -mindepth 1)" ]] || fail "created under HOME: $(find "$HOME" -mindepth 1)"
# No provider link dirs: the repo top holds only what it had.
[[ "$(ls -A "$repo" | tr '\n' ' ')" == ".agents .git " ]] || fail "repo top changed: $(ls -A "$repo")"

mkdir -p "$t/work/plain"
out="$(run "$clone" plain 2>&1)" && fail "non-git REPO succeeded"
grep -q 'git init' <<<"$out" || fail "non-git error names no fix: $out"
out="$(run "$t/nope" repo 2>&1)" && fail "missing clone succeeded"
grep -q 'SPEC_CHAT_CLONE' <<<"$out" || fail "missing-clone error names no fix: $out"
out="$(cd "$t/work" && env -u SPEC_CHAT_CLONE just --justfile "$kit/justfile" spec-chat repo 2>&1)" && fail "default clone absent but succeeded"
grep -q "$HOME/src/spec-chat" <<<"$out" || fail "default clone not ~/src/spec-chat: $out"
echo "spec-chat-install: ok (agents-only links, ignored once, clean status, nothing in HOME, both errors)"
