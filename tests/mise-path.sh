#!/usr/bin/env bash
# Integration test for where mise's tools sit on PATH (#261): a dir the caller put first on PATH wins over a tool
# installed in a mise tool's dir, and mise's tools win over the system's. The layout CI had on eaeaf95a, rebuilt
# offline: a copy of mise's installs (links) with a `pi` installed by `npm install -g` under mise's node, and mise's
# shims rebuilt so they hold it too. Through each public path: the kit's justfile recipes (`just --command`, its
# exported PATH), a template-created repo's justfile, and a pane's PATH from `pi-role --json` ("path"). A stub pi
# first on the caller's PATH must run in each; with no stub, mise's node is still the node found (not /usr/bin's).
# Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
t="$(cd "$t" && pwd -P)"
fail() { echo "mise-path test: $1" >&2; echo "${out:-}" >&2; exit 1; }
data="$(mise doctor --json | jq -r .dirs.data)"
node_dir="$(mise -C "$kit" where node)"; node_dir="$t/mise/${node_dir#"$data"/}"
mkdir -p "$t/mise" "$t/home" "$t/mbin" "$t/stub" "$t/work" "$t/pkg/bin"
cp -rs "$data/installs" "$t/mise/installs"
ln -s "$(command -v mise)" "$t/mbin/mise"
# The real just, reached as a caller reaches it (its own PATH entry, or mise's shim, whose target `mise which` names:
# on CI just exists only through mise), linked into the same tool dir, so the justfile's own calls find it.
just="$(command -v just)"
[[ "$(realpath "$just")" != "$(realpath "$(command -v mise)")" ]] || just="$(mise -C "$kit" which just)"
ln -s "$just" "$t/mbin/just"; just="$t/mbin/just"
export HOME="$t/home" MISE_DATA_DIR="$t/mise" MISE_CACHE_DIR="$t/cache" MISE_STATE_DIR="$t/state" MISE_CONFIG_DIR="$t/config"
# The global Pi CI installed with `npm install -g` under mise's node: here a package whose `pi` prints a marker.
printf '{"name":"global-pi","version":"0.0.0","bin":{"pi":"bin/pi.js"}}\n' >"$t/pkg/package.json"
printf '#!/usr/bin/env node\nconsole.log("global pi in mise node");\n' >"$t/pkg/bin/pi.js"
PATH="$node_dir/bin:/usr/bin:/bin" npm install -g --force --offline --ignore-scripts --no-audit --no-fund --prefix "$node_dir" "$t/pkg" >/dev/null 2>&1 \
  || fail "npm install -g under mise's node failed"
[[ -x "$node_dir/bin/pi" ]] || fail "no pi in $node_dir/bin after npm install -g"
PATH="$t/mbin:/usr/bin:/bin" mise reshim
[[ -e "$t/mise/shims/pi" ]] || fail "mise reshim made no pi shim"
printf '#!/bin/sh\necho "stub pi"\n' >"$t/stub/pi"; chmod +x "$t/stub/pi"
# The box's real Pi lives in ~/.local/bin: here a fake one (and a fake herdr, a user-local tool the caller's PATH
# below lacks), never run, only resolved (`command -v`).
mkdir -p "$t/home/.local/bin"
for b in pi herdr; do printf '#!/bin/sh\necho "home %s"\n' "$b" >"$t/home/.local/bin/$b"; chmod +x "$t/home/.local/bin/$b"; done
caller="$t/stub:$t/mbin:/usr/local/bin:/usr/bin:/bin"; plain="$t/mbin:/usr/local/bin:/usr/bin:/bin"

# The kit (a copy of its tracked files) and a repo made from the TypeScript template.
mkdir -p "$t/kit"; (cd "$kit" && git ls-files -z | xargs -0 tar -cf - 2>/dev/null) | tar -xf - -C "$t/kit"
git -C "$t/kit" init -q
(cd "$t/work" && PATH="$plain" GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t \
  GIT_COMMITTER_EMAIL=t@t "$just" --justfile "$kit/justfile" new-repo typescript "$t/ts" --no-spec-chat >/dev/null)
for repo in "$t/kit" "$t/ts"; do
  out="$(cd "$repo" && PATH="$caller" "$just" --command pi 2>&1)" || fail "$repo: just --command pi failed"
  [[ "$out" == "stub pi" ]] || fail "$repo: the justfile's PATH ran $out, not the caller's stub pi"
  out="$(cd "$repo" && PATH="$plain" "$just" --command pi 2>&1)" || true
  [[ "$out" == "global pi in mise node" ]] || fail "$repo: without a stub, pi is not mise node's global (layout check)"
  out="$(cd "$repo" && PATH="$caller" "$just" --command sh -c 'command -v node')"
  [[ "$out" == "$node_dir/bin/node" ]] || fail "$repo: the justfile's node is $out, not mise's $node_dir/bin/node"
  # Every just route a caller takes (the real just, mise's just shim; inside the repo and with --justfile from
  # outside it): the stub first on the caller's PATH beats the pi in ~/.local/bin (owner ruling #261), and in the
  # kit a tool only ~/.local/bin holds is still found (the kit justfile's fallback; a template's keeps the caller's).
  want="$t/stub/pi"; [[ "$repo" != "$t/kit" ]] || want+=$'\n'"$t/home/.local/bin/herdr"
  for route in "$just" "$t/mise/shims/just"; do
    for at in "$repo" "$t/work"; do
      out="$(cd "$at" && PATH="$t/stub:$t/mise/shims:$t/mbin:/usr/local/bin:/usr/bin:/bin" "$route" --justfile "$repo/justfile" \
        --command sh -c 'command -v pi; command -v herdr || true' 2>&1)" || fail "$repo: $route --command from $at failed"
      [[ "$out" == "$want" ]] || fail "$repo: $route from $at resolves pi (and the kit's herdr) to $out, want $want"
    done
  done
done
# A pane: herdr-spawn's tab PATH is pi-role's "path" (shims placed before the system dirs).
for repo in "$t/kit" "$t/ts"; do
  p="$(cd "$repo" && PATH="$caller" "$kit/scripts/pi-role" --json "$kit/agents/implementer.md" | jq -r '.path // empty')"
  [[ -n "$p" ]] || fail "$repo: pi-role --json gave no path in a mise.toml repo"
  out="$(PATH="$p" command -v pi)"; [[ "$out" == "$t/stub/pi" ]] || fail "$repo: pane PATH finds pi at $out, not the stub"
  out="$(PATH="$p" command -v node)"; [[ "$out" == "$t/mise/shims/node" ]] || fail "$repo: pane PATH finds node at $out, not mise's shim"
done
echo "mise-path: ok (kit and template justfiles, pane PATH: the caller's stub pi beats a pi npm-installed under mise's node and the one in ~/.local/bin, through the real just and mise's just shim, in the repo and with --justfile from outside; ~/.local/bin a fallback in the kit; mise's node beats the system's)"
