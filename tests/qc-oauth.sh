#!/usr/bin/env bash
# gate: e2e
# The qc sandbox test's OAuth and overlay section (#508; setup tests/lib/qc.sh): OAuth credentials on the box warn
# once and are never written back; removing an ignored dir the real worktree holds (#395) succeeds in the overlay,
# all discarded.
# Run by `just check`; offline and bounded, in its own namespace and throwaway HOME (tests/lib/qc.sh).
# shellcheck source=tests/lib/qc.sh
source "$(dirname "$0")/lib/qc.sh"
# OAuth credentials on the box (type oauth, or only a refresh token field): one warning line, the run proceeds.
cp -p "$pa" "$t/auth-plain"
for a in '{"anthropic": {"type": "oauth", "refresh": "SECRET-pi-oauth-r", "access": "SECRET-pi-oauth-a", "expires": 1}}' \
         '{"p": {"refresh_token": "SECRET-pi-oauth-r"}}'; do
  echo "$a" > "$pa"; cp -p "$pa" "$t/auth0"
  copycase rewrite; piok oauth
  [[ "$(grep -c '^qc: warning: auth.json has OAuth credentials: a token refresh during this run is discarded$' <<< "$out")" == 1 ]] \
    || fail "oauth: want one warning line: $out"
  ! grep -q 'SECRET-pi-oauth' <<< "$out" || fail "oauth: credential value printed"
done
cp -p "$t/auth-plain" "$pa"
# #395: removing an ignored directory the real worktree holds (a .venv with a nested dir and file) succeeds in the
# overlay (userxattr: whiteouts and opaque dirs on the tmpfs upper), and recreating it works; all discarded.
echo .venv/ >> .git/info/exclude; mkdir -p .venv/lib/x.dist-info; echo real > .venv/lib/x.dist-info/RECORD
run 0 venv $st 5 acceptance-a
judge="$(jr '["stdout"]')"
grep -q "VENV rm exit 0" <<< "$judge" && grep -q "VENV recreated" <<< "$judge" || fail "venv: removing an ignored lower dir failed in the sandbox: $judge"
[[ "$(jr '["worktree_writes"]')" == "[]" && "$(jr '["discarded_writes"]')" -gt 0 ]] || fail "venv: want ignored writes discarded, none listed: $(jr '["worktree_writes"]')"
[[ "$(cat .venv/lib/x.dist-info/RECORD)" == real && "$(find .venv | wc -l)" == 4 && -z "$(git status --porcelain)" ]] || fail "venv: real worktree changed"
echo "qc test: venv: rm -rf of an ignored lower dir exits 0, recreated, $(jr '["discarded_writes"]') writes discarded" >&2
rm -rf .venv; sed -i '/^\.venv\/$/d' .git/info/exclude
echo "qc-oauth: ok (OAuth warned once, never written back; an ignored .venv removed and recreated in the overlay, discarded; offline, runs bounded)"
