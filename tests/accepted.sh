#!/usr/bin/env bash
# Integration test for scripts/octo-feather-accepted against fixture review-host
# registries, review-page hand-offs and a throwaway repo. Run by `just check`.
#
# The pilot 1 failure (2026-10-20): the owner pressed Accept spec, the page
# wrote its hand-off, and octo-feather-accepted still exited 1 because it waited
# for a registry `accepted = true` that nothing writes. Here Accept is the
# hand-off alone, exactly as the review page writes it.
#
# Spec Chat is read only at its pin (the Skillfile fetch-only entry, `just
# vendored-fetch`), never the box's clone (#96: a clone behind origin failed this
# test locally while CI, with no clone, skipped the cross-check). With it the test checks:
# - the versions: pinned review-serve.py, run as a server, serves
#   tests/fixtures/accepted/*.spec.html with ETags V1 and V2 below (the ETag names
#   the served body, the version its events record), so a change in its version
#   rule fails here. Through its HTTP surface, never its private helpers (#104);
# - the registry: pinned Spec Chat's review-host CLI registers a spec under an
#   isolated XDG_STATE_HOME, and octo-feather-accepted finds that row and its Accept
#   (#96, director finding 47: it once read an env var Spec Chat never reads).
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
fx="$kit/tests/fixtures/accepted"
V1=9a91105876313c1c1c25cb0dbdb5244af32ea96fe36e4009b6a7373255c8991d   # a.spec.html
V2=9beb7ff92e817947ef4b7a4241d7cddf36d24f84c00cbe00058240d1610c7a86   # a-edited.spec.html
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fail() { echo "accepted test: $*" >&2; exit 1; }

sc="$("$kit/scripts/check-vendored" --extract spec-chat "$t/sc")" || fail "no pinned Spec Chat (message above)"
mkdir -p "$t/x"; cp "$fx/a.spec.html" "$fx/a-edited.spec.html" "$t/x/"
XDG_STATE_HOME="$t/xdg-serve" python3 "$sc/review-spec/assets/review-serve.py" "$t/x" --port 0 >"$t/serve.log" 2>&1 &
serve=$!; trap 'kill "$serve" 2>/dev/null || true; rm -rf "$t"' EXIT
for _ in $(seq 100); do url="$(sed -n 's|^spec-chat review-serve on \(http://[^ ]*\)$|\1|p' "$t/serve.log")"; [[ -z "$url" ]] || break; sleep 0.1; done
[[ -n "$url" ]] || fail "pinned review-serve did not start: $(cat "$t/serve.log")"
etag() { curl -sf -D - -o /dev/null "$url/$1" | tr -d '\r' | sed -n 's/^[Ee][Tt][Aa][Gg]: "\(.*\)"$/\1/p'; }
got="$(etag a.spec.html)"$'\n'"$(etag a-edited.spec.html)"
kill "$serve"; wait "$serve" 2>/dev/null || true
[[ "$got" == "$V1"$'\n'"$V2" ]] || fail "Spec Chat's served version rule changed (got $got); update scripts/octo-feather-accepted served_version and the pins here"

g() { git -c user.name=t -c user.email=t@t -c init.defaultBranch=main "$@"; }
r="$t/repo"; s=docs/specs/a.spec.html
g init -q "$r"; mkdir -p "$r/docs/specs"; cp "$fx/a.spec.html" "$r/$s"
g -C "$r" add -A; g -C "$r" commit -qm spec; c1="$(git -C "$r" rev-parse HEAD)"
cp "$fx/a-edited.spec.html" "$r/$s"; g -C "$r" commit -qam edit; c2="$(git -C "$r" rev-parse HEAD)"

export XDG_STATE_HOME="$t/xdg"; state="$t/xdg/spec-chat"   # fixture rows; the real registry case is last
mkdir -p "$state/hosting/default" "$state/hosting/other"
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
row "$c1" 2026-10-20T15:00:00Z > "$state/hosting/default/registry.toml"
run 1 "$s"; [[ "$out" == *"no hand-off"* ]] || fail "registered, no hand-off: $out"
row "$c1" 2026-10-20T15:00:00Z "accepted = true" > "$state/hosting/default/registry.toml"
run 1 "$s"                                                           # a hand-written registry key is not an Accept
row "$c1" 2026-10-20T15:00:00Z > "$state/hosting/default/registry.toml"
handoff 1792509686764211101 acc1 "$V1"
run 0 "$s"                                                           # pilot 1: register, press Accept, exit 0
[[ "$out" == "accepted $c1 slug=a-flow at=2026-10-20T15:"*" session=default id=spec:a-flow:p::$s handoff=acc1" ]] || fail "bad output: $out"
handoff 1792509686764211102 com1 "$V1" '[{"id": "c1"}]'
run 1 "$s"; [[ "$out" == *"sends comments"* ]] || fail "newer comment hand-off: $out"
handoff 1792509686764211103 acc2 "$V1"
row "$c2" 2026-10-20T15:10:00Z > "$state/hosting/default/registry.toml"
run 1 "$s"; [[ "$out" == *"not on the spec at registered commit"* ]] || fail "stale Accept: $out"   # base moved to an edited spec
handoff 1792509686764211104 acc3 "$V2"
run 0 "$s"; [[ "$out" == "accepted $c2 "* ]] || fail "re-accepted at the new base: $out"
# gh#64: the same Accept is found however SPEC_PATH is given.
run 0 "$r/$s"; [[ "$out" == "accepted $c2 "* ]] || fail "absolute SPEC_PATH: $out"
run 0 "./$s"; [[ "$out" == "accepted $c2 "* ]] || fail "./ SPEC_PATH: $out"
set +e; out="$(cd "$r/docs" && "$A" specs/a.spec.html 2>&1)"; rc=$?; set -e
[[ "$rc" == 0 && "$out" == "accepted $c2 "* ]] || fail "SPEC_PATH relative to a subdirectory cwd: rc=$rc $out"
run 1 docs/specs/missing.spec.html
[[ "$out" == *"SPEC_PATH docs/specs/missing.spec.html"*"tried docs/specs/missing.spec.html"*"registered: $s"* ]] || fail "unregistered reason: $out"
set +e; out="$("$A" 2>&1)"; rc=$?; set -e
[[ "$rc" == 64 && "$(head -n1 <<<"$out")" == *SPEC_PATH* ]] || fail "no argument: rc=$rc $out"
printf '{"id": "ag1", "event": "handoff", "actor": "agent", "createdAt": "2026-10-20T15:59:00.000Z", "version": "%s"}\n' "$V1" \
  > "$spool/1792509686764211199-handoff-ag1.json"
run 0 "$s"; [[ "$out" == "accepted $c2 "*"handoff=acc3" ]] || fail "an agent-actor hand-off counted: $out"
row 0123456789abcdef0123456789abcdef01234567 2026-10-20T16:00:00Z > "$state/hosting/other/registry.toml"
run 0 "$s"; [[ "$out" == "accepted $c2 "*"session=default"* ]] || fail "a missing commit in another session hid the accepted row: $out"
row 0123456789abcdef0123456789abcdef01234567 2026-10-20T16:00:00Z > "$state/hosting/default/registry.toml"
run 1 "$s"; [[ "$out" == *"is not in"* ]] || fail "registered commit missing from the repo: $out"
# The registry pinned Spec Chat's review-host writes (no --state-dir, no Herdr session),
# under its own XDG_STATE_HOME: octo-feather-accepted finds the row, then its Accept.
host="$sc/review-spec/scripts/review-host.py"; r0="$t/r0"
g init -q "$r0"; mkdir -p "$r0/docs/specs"; cp "$fx/a.spec.html" "$r0/$s"
g -C "$r0" add -A; g -C "$r0" commit -qm spec; c0="$(git -C "$r0" rev-parse HEAD)"
export XDG_STATE_HOME="$t/xdg-host" SPEC_CHAT_APPROVED_INGRESS_PORTS=""; unset HERDR_SESSION
trap '(cd "$r0" && python3 "$host" stop >/dev/null 2>&1) || true; rm -rf "$t"' EXIT
out="$(cd "$r0" && python3 "$host" register --owner t --slug a-flow --base "$c0" "$s" 2>&1)" || fail "pinned review-host register: $out"
real() { set +e; out="$("$A" "$s" --repo "$r0" 2>&1)"; rc=$?; set -e; }
real; [[ "$rc" == 1 && "$out" == *"a-flow: no hand-off"* ]] || fail "row review-host wrote not found: rc=$rc $out"
spool="$r0/$s.review/$SPOOL_SIDE"; handoff 1792509686764211301 real1 "$V1"
real; [[ "$rc" == 0 && "$out" == "accepted $c0 slug=a-flow "*" session=default "*"handoff=real1" ]] || fail "Accept on the registered row: rc=$rc $out"
(cd "$r0" && python3 "$host" stop >/dev/null) || fail "pinned review-host stop"
echo "accepted: ok (unregistered, no hand-off, hand-written key, Accept at base, newer comments, stale base, re-accept, absolute/./subdir SPEC_PATH, unregistered reason, no argument, agent actor, missing commit; versions and registry from pinned Spec Chat: review-host register, then Accept)"
