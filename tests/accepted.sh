#!/usr/bin/env bash
# Integration test for scripts/octo-feather-accepted against a fixture
# review-host registry and a throwaway repo. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
g() { git -c user.name=t -c user.email=t@t -c init.defaultBranch=main "$@"; }
g init -q "$t/repo"; mkdir -p "$t/repo/docs/specs"; echo spec > "$t/repo/docs/specs/a.spec.html"
g -C "$t/repo" add -A; g -C "$t/repo" commit -qm spec; c="$(git -C "$t/repo" rev-parse HEAD)"
export SPEC_CHAT_STATE="$t/state"; mkdir -p "$t/state/hosting/default" "$t/state/hosting/other"
row() { printf '[[resource]]\nid = "spec:%s:p::%s"\nslug = "%s"\nspec = "%s"\nbase = "%s"\nupdated_at = "%s"\n%s\n' "$1" "$2" "$@"; }
A="$kit/scripts/octo-feather-accepted"
run() { local want="$1"; shift; set +e; out="$("$A" "$@" --repo "$t/repo" 2>&1)"; rc=$?; set -e
  [[ "$rc" == "$want" ]] || { echo "accepted test: '$*' want exit $want, got $rc: $out" >&2; exit 1; }; }
run 1 docs/specs/a.spec.html                                       # not registered
row a-flow docs/specs/a.spec.html "$c" 2026-10-19T01:00:00Z "" > "$t/state/hosting/default/registry.toml"
run 1 docs/specs/a.spec.html                                       # registered, not accepted
row a-flow docs/specs/a.spec.html "$c" 2026-10-19T02:00:00Z "accepted = true" > "$t/state/hosting/other/registry.toml"
run 0 docs/specs/a.spec.html                                       # accepted in another session's registry
[[ "$out" == "accepted $c slug=a-flow "*" id=spec:a-flow:p::docs/specs/a.spec.html" ]] || { echo "accepted test: bad output: $out" >&2; exit 1; }
row a-flow docs/specs/a.spec.html 0123456789abcdef0123456789abcdef01234567 2026-10-19T03:00:00Z "accepted = true" > "$t/state/hosting/default/registry.toml"
run 1 docs/specs/a.spec.html                                       # newest accepted commit is not in the repo
echo "accepted: ok (unregistered, unaccepted, accepted, missing commit)"
