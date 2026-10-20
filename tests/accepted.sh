#!/usr/bin/env bash
# Integration test for scripts/octo-feather-accepted against fixture review-host
# registries, review-page hand-offs and a throwaway repo. Run by `just check`.
#
# The Fieldnote failure (2026-10-20): the owner pressed Accept spec, the page
# wrote its hand-off, and octo-feather-accepted still exited 1 because it waited
# for a registry `accepted = true` that nothing writes. Here Accept is the
# hand-off alone, exactly as the review page writes it.
#
# The versions are Spec Chat's own: review-serve.py `_spec_page` (spec-chat
# 183f3ee) computed them for tests/fixtures/accepted/*.spec.html. When a Spec Chat
# clone is present ($SPEC_CHAT_CLONE, default ~/src/spec-chat), the test also
# recomputes them with it, so a change in Spec Chat's version rule fails here.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
fx="$kit/tests/fixtures/accepted"
V1=9a91105876313c1c1c25cb0dbdb5244af32ea96fe36e4009b6a7373255c8991d   # a.spec.html
V2=9beb7ff92e817947ef4b7a4241d7cddf36d24f84c00cbe00058240d1610c7a86   # a-edited.spec.html
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fail() { echo "accepted test: $*" >&2; exit 1; }

clone="${SPEC_CHAT_CLONE:-$HOME/src/spec-chat}"; crossed=""
if [[ -f "$clone/skill/review-spec/assets/review-serve.py" ]]; then
  got="$(python3 - "$clone/skill/review-spec/assets" "$fx" "$t/x" <<'EOF'
import importlib.util, os, shutil, sys
assets, fx, scratch = sys.argv[1:]
sys.path.insert(0, assets)
s = importlib.util.spec_from_file_location("review_serve", os.path.join(assets, "review-serve.py"))
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
os.makedirs(scratch)
for f in ("a.spec.html", "a-edited.spec.html"):
    p = os.path.join(scratch, f); shutil.copy(os.path.join(fx, f), p); print(m._spec_page(p)[2])
EOF
)" || fail "could not compute versions with Spec Chat at $clone"
  [[ "$got" == "$V1"$'\n'"$V2" ]] || fail "Spec Chat's served version rule changed (got $got); update scripts/octo-feather-accepted served_version and the pins here"
  crossed=", versions crossed with Spec Chat"
fi

g() { git -c user.name=t -c user.email=t@t -c init.defaultBranch=main "$@"; }
r="$t/repo"; s=docs/specs/a.spec.html
g init -q "$r"; mkdir -p "$r/docs/specs"; cp "$fx/a.spec.html" "$r/$s"
g -C "$r" add -A; g -C "$r" commit -qm spec; c1="$(git -C "$r" rev-parse HEAD)"
cp "$fx/a-edited.spec.html" "$r/$s"; g -C "$r" commit -qam edit; c2="$(git -C "$r" rev-parse HEAD)"

export SPEC_CHAT_STATE="$t/state"; mkdir -p "$t/state/hosting/default" "$t/state/hosting/other"
SPOOL_SIDE=human; spool="$r/$s.review/$SPOOL_SIDE"   # Spec Chat's owner side of the spool
row() { # base updated_at [extra line]
  printf '[[resource]]\nid = "spec:a-flow:p::%s"\nslug = "a-flow"\nroot = "%s"\nspec = "%s"\nbase = "%s"\nupdated_at = "%s"\n%s\n' \
    "$s" "$r" "$s" "$1" "$2" "${3:-}"; }
# One hand-off as the review page writes it: stamp, id, version, and an events list for comments.
handoff() { # stamp id version [events-json]
  mkdir -p "$spool"
  local ev=""; [[ -z "${4:-}" ]] || ev=", \"events\": $4"
  printf '{"id": "%s", "event": "handoff", "anchorId": "", "actor": "%s", "createdAt": "2026-10-20T15:%02d:00.000Z", "schemaVersion": 1, "version": "%s"%s}\n' \
    "$2" "$SPOOL_SIDE" "$(( ${1: -2} % 60 ))" "$3" "$ev" > "$spool/$1-handoff-$2.json"; }
A="$kit/scripts/octo-feather-accepted"
run() { local want="$1"; shift; set +e; out="$("$A" "$@" --repo "$r" 2>&1)"; rc=$?; set -e
  [[ "$rc" == "$want" ]] || fail "'$*' want exit $want, got $rc: $out"; }

run 1 "$s"                                                           # not registered
row "$c1" 2026-10-20T15:00:00Z > "$t/state/hosting/default/registry.toml"
run 1 "$s"; [[ "$out" == *"no hand-off"* ]] || fail "registered, no hand-off: $out"
row "$c1" 2026-10-20T15:00:00Z "accepted = true" > "$t/state/hosting/default/registry.toml"
run 1 "$s"                                                           # a hand-written registry key is not an Accept
row "$c1" 2026-10-20T15:00:00Z > "$t/state/hosting/default/registry.toml"
handoff 1792509686764211101 acc1 "$V1"
run 0 "$s"                                                           # Fieldnote: register, press Accept, exit 0
[[ "$out" == "accepted $c1 slug=a-flow at=2026-10-20T15:"*" session=default id=spec:a-flow:p::$s handoff=acc1" ]] || fail "bad output: $out"
handoff 1792509686764211102 com1 "$V1" '[{"id": "c1"}]'
run 1 "$s"; [[ "$out" == *"sends comments"* ]] || fail "newer comment hand-off: $out"
handoff 1792509686764211103 acc2 "$V1"
row "$c2" 2026-10-20T15:10:00Z > "$t/state/hosting/default/registry.toml"
run 1 "$s"; [[ "$out" == *"not on the spec at registered commit"* ]] || fail "stale Accept: $out"   # base moved to an edited spec
handoff 1792509686764211104 acc3 "$V2"
run 0 "$s"; [[ "$out" == "accepted $c2 "* ]] || fail "re-accepted at the new base: $out"
printf '{"id": "ag1", "event": "handoff", "actor": "agent", "createdAt": "2026-10-20T15:59:00.000Z", "version": "%s"}\n' "$V1" \
  > "$spool/1792509686764211199-handoff-ag1.json"
run 0 "$s"; [[ "$out" == "accepted $c2 "*"handoff=acc3" ]] || fail "an agent-actor hand-off counted: $out"
row 0123456789abcdef0123456789abcdef01234567 2026-10-20T16:00:00Z > "$t/state/hosting/other/registry.toml"
run 0 "$s"; [[ "$out" == "accepted $c2 "*"session=default"* ]] || fail "a missing commit in another session hid the accepted row: $out"
row 0123456789abcdef0123456789abcdef01234567 2026-10-20T16:00:00Z > "$t/state/hosting/default/registry.toml"
run 1 "$s"; [[ "$out" == *"is not in"* ]] || fail "registered commit missing from the repo: $out"
echo "accepted: ok (unregistered, no hand-off, hand-written key, Accept at base, newer comments, stale base, re-accept, agent actor, missing commit$crossed)"
