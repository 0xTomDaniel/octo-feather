#!/usr/bin/env bash
# Integration test: kit and template justfile recipes pass their arguments and
# the invocation directory to the called command as data (#61). Each recipe runs
# through `just` from a cwd whose path holds `$`, a backtick, both quotes and a
# space, with arguments holding the same; stub octo-feather-* commands record
# the exact cwd and argv; nothing expands. Offline, HOME redirected. The kit justfile puts its own scripts/ first
# on PATH, so its recipes run from a copy of it whose scripts/ holds the stubs (the rest linked to the kit's).
# Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
t="$(cd "$t" && pwd -P)"
fail() { echo "recipe-args test: $*" >&2; exit 1; }
export HOME="$t/home" XDG_STATE_HOME="$t/state" XDG_CONFIG_HOME="$t/config"
stubs="$t/stubs"; mkdir -p "$stubs"
log="$t/log"; export RECIPE_ARGS_LOG="$log"
cat > "$stubs/stub" <<'EOF'
#!/usr/bin/env bash
{ printf 'cmd %s\ncwd %s\n' "${0##*/}" "$(pwd -P)"; printf '[%s]\n' "$@"; } > "$RECIPE_ARGS_LOG"
EOF
chmod +x "$stubs/stub"
for c in shape spec-chat integrate start qc new-repo; do ln -s stub "$stubs/octo-feather-$c"; done
export PATH="$stubs:$PATH"   # the templates' justfiles keep the caller's PATH
k="$t/kit"; mkdir -p "$k/scripts"; cp "$kit/justfile" "$k/"; ln -s "$kit"/scripts/* "$k/scripts/"
for c in shape spec-chat integrate start qc new-repo; do ln -sf "$stubs/stub" "$k/scripts/octo-feather-$c"; done

w="$t/a \$b \`c\` 'd\" e/w"; mkdir -p "$w"
a1='x $y'; a2='$(touch pwned)'; a3='`touch pwned2`'; a4="q'r\"s"; a5='z w'

# check RECIPE CMD CWD ARG...: CMD ran once in exactly CWD with exactly ARG...
check() {
  local name="$1" cmd="$2" cwd="$3"; shift 3
  local want; want="$(printf 'cmd %s\ncwd %s\n' "$cmd" "$cwd"; printf '[%s]\n' "$@")"
  [[ -f "$log" ]] || fail "$name: $cmd never ran: $out"
  [[ "$(cat "$log")" == "$want" ]] || fail "$name: got"$'\n'"$(cat "$log")"$'\n'"want"$'\n'"$want"
  rm -f "$log"
}
kj() { out="$(cd "$w" && just --justfile "$k/justfile" "$@" 2>&1)" || fail "just $1 failed: $out"; }

kj shape "$a1" "$a2" "$a3" "$a4" "$a5";     check shape octo-feather-shape "$w" "$a1" "$a2" "$a3" "$a4" "$a5"
kj shape;                                    check 'shape (no args)' octo-feather-shape "$w"
kj spec-chat "$a4 $a2";                      check spec-chat octo-feather-spec-chat "$w" "$a4 $a2"
kj integrate 59 "$a1" "$a5" "$a2" "$a3";    check integrate octo-feather-integrate "$w" 59 "$a1" "$a5" "$a2" "$a3"
kj start;                                    check 'start (default cwd)' octo-feather-start "$k" --director --cwd "$w"
kj start "$a4 $a2";                          check start octo-feather-start "$k" --director --cwd "$a4 $a2"
kj supervise 61;                             check 'supervise (default cwd)' octo-feather-start "$k" --issue 61 --cwd "$w"
kj supervise "$a1" "$a3";                    check supervise octo-feather-start "$k" --issue "$a1" --cwd "$a3"
kj qc "$a4" 7 "$a1" "$a5" "$a2";            check qc octo-feather-qc "$w" "$a4" 7 "$a1" "$a5" "$a2"
kj new-repo python "$a1" --no-spec-chat "$a5" "$a2"; check new-repo octo-feather-new-repo "$w" python "$a1" --no-spec-chat "$a5" "$a2"
kj new-repo "$a3" "$a4";                     check 'new-repo (no flags)' octo-feather-new-repo "$w" "$a3" "$a4"

# Each template's justfile sits at a target repo's root; its recipes run there.
for lang in python typescript; do
  r="$w/$lang"; mkdir -p "$r"; cp "$kit/templates/$lang/justfile" "$r/justfile"
  tj() { out="$(cd "$r" && just "$@" 2>&1)" || fail "$lang: just $1 failed: $out"; }
  tj integrate 59 "$a1" "$a5" "$a2" "$a3"; check "$lang integrate" octo-feather-integrate "$r" 59 "$a1" "$a5" "$a2" "$a3"
  tj qc "$a4" 7 "$a1" "$a5" "$a3";         check "$lang qc" octo-feather-qc "$r" "$a4" 7 "$a1" "$a5" "$a3"
done

found="$(find "$t" "$kit" -maxdepth 4 -name 'pwned*' -print)"
[[ -z "$found" ]] || fail "an argument ran as shell: $found"
echo "recipe-args: ok (kit shape, spec-chat, integrate, start, supervise, qc, new-repo; python and typescript integrate, qc; exact cwd and argv, nothing expanded)"
