#!/usr/bin/env bash
# Integration test for octo-feather-contract (quality spec #qc-contract): run as a command on
# copies of each template's qc.toml. A valid contract prints ok; a missing format version, an
# unsupported one, a missing, unknown or mistyped key, bad TOML and no qc.toml each fail naming
# the field or the fix. Then the TypeScript template's verify-app drives what its qc.toml declares:
# a changed value and setup are followed with no helper edit. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
t="$(cd "$t" && pwd -P)"
fail() { echo "contract test: $*" >&2; exit 1; }
cmd="$kit/scripts/octo-feather-contract"

# run DIR-OR-FILE: sets out and rc
run() { set +e; out="$("$cmd" "$@" 2>&1)"; rc=$?; set -e; }
# bad NAME EXPECTED-TEXT: the qc.toml in $t/NAME fails with exit 1 naming EXPECTED-TEXT
bad() {
  run "$t/$1"
  [[ "$rc" == 1 ]] && grep -qF -- "$2" <<<"$out" || fail "$1: want exit 1 naming '$2', got exit $rc: $out"
}
# variant NAME SED-SCRIPT: $t/NAME/qc.toml, the python template's contract edited by SED-SCRIPT
variant() { mkdir -p "$t/$1"; sed -e "$2" "$kit/templates/python/qc.toml" >"$t/$1/qc.toml"; }

for lang in python typescript; do
  mkdir -p "$t/$lang"; cp "$kit/templates/$lang/qc.toml" "$t/$lang/"
  run "$t/$lang"
  [[ "$rc" == 0 && "$out" == "octo-feather-contract: $t/$lang/qc.toml: ok (format 1)" ]] || fail "$lang template contract not ok (exit $rc): $out"
  run "$t/$lang/qc.toml"
  [[ "$rc" == 0 ]] || fail "$lang: a path to the file itself not ok: $out"
done
(cd "$t/python" && "$cmd" >/dev/null) || fail "no argument does not read ./qc.toml"

variant no-format '/^format = /d'
bad no-format "qc.toml: missing format (the contract's format version; supported: 1)"
variant format-2 's/^format = 1/format = 2/'
bad format-2 "qc.toml: format 2 is not a supported format version (supported: 1)"
variant format-str 's/^format = 1/format = "1"/'
bad format-str 'qc.toml: format must be an integer'
variant no-entry '/^\[entry\]/,/^command/d'
bad no-entry 'qc.toml: missing entry'
variant no-command '/^command = /d'
bad no-command 'qc.toml: entry: missing command'
variant no-services '/^\[services\]/d'
bad no-services 'qc.toml: missing services'
variant extra 's/^setup = /colour = "red"\nsetup = /'
bad extra 'qc.toml: unknown key colour'
variant value-int 's/^name = "Ada"/name = 7/'
bad value-int 'qc.toml: values.name must be a string'
variant service-no-command 's/^\[services\]/[services.web]\nready = "\/"/'
bad service-no-command 'qc.toml: services.web: missing command'
variant fixture-extra 's/^\[fixture\]/[fixture.seed]\nreset = "true"\nseed = 1/'
bad fixture-extra 'qc.toml: fixture.seed: unknown key seed'
variant empty-setup 's/^setup = .*/setup = ""/'
bad empty-setup 'qc.toml: setup must not be empty'
variant bad-toml 's/^format = 1/format = /'
bad bad-toml 'qc.toml: not TOML:'
# [browser]: the verify skill drives a headless browser at a Playwright release pin (remote spec #host-tools).
variant browser '$a [browser]\nplaywright = "1.64.1"'
run "$t/browser"; [[ "$rc" == 0 ]] || fail "a contract with [browser] playwright = 1.64.1 not ok (exit $rc): $out"
variant browser-latest '$a [browser]\nplaywright = "latest"'
bad browser-latest 'qc.toml: browser.playwright must match ^[0-9]+\.[0-9]+\.[0-9]+$'
variant browser-no-pin '$a [browser]'
bad browser-no-pin 'qc.toml: browser: missing playwright'
mkdir -p "$t/none"
bad none "no qc.toml at $t/none/qc.toml"
run "$t/python" "$t/python"
[[ "$rc" == 2 ]] && grep -qF 'usage: octo-feather-contract [REPO-OR-QC.TOML]' <<<"$out" || fail "two arguments not refused with usage (exit $rc): $out"

# The TypeScript template's verify-app invokes only what qc.toml declares: its setup (here a marker)
# and its entry, driven with the contract's value. It reads qc.toml with the TOML package smol-toml:
# with the repo's packages not installed, launch fails naming it and `just setup`, before any setup;
# then the packages are installed offline from the pnpm store, as `just setup` installs them.
repo="$t/ts-app"; mkdir -p "$repo"
(cd "$kit/templates/typescript" && git ls-files -z | xargs -0 cp --parents -t "$repo")
git -C "$repo" init -q && git -C "$repo" -c user.name=t -c user.email=t@t commit -qm init --allow-empty
sed -i -e 's/^setup = .*/setup = "echo declared > \\"$QC_REPO\/setup-ran\\""/' "$repo/qc.toml"
set +e; vout="$(VERIFY_APP_RUN_DIR="$t/va0/run" VERIFY_APP_EVIDENCE_DIR="$t/va0/evidence" "$repo/.agents/skills/verify-app/scripts/verify-app" launch 2>&1)"; rc=$?; set -e
[[ "$rc" == 1 ]] && grep -qF 'cannot load the TOML reader smol-toml' <<<"$vout" && grep -qF 'just setup' <<<"$vout" && [[ ! -e "$repo/setup-ran" ]] \
  || fail "launch with the packages not installed did not fail naming smol-toml and just setup (exit $rc): $vout"
(cd "$repo" && pnpm install --offline --frozen-lockfile --silent) \
  || fail "pnpm install --offline failed: fill the pnpm store first (pnpm fetch in templates/typescript)"
sed -i -e 's/^name = "Ada"/name = "Grace"/' -e 's/^greeting = .*/greeting = "Hello, Grace"/' "$repo/qc.toml"
run "$repo"; [[ "$rc" == 0 ]] || fail "edited ts contract not ok: $out"
# Its drive appends an evidence record: to a throwaway store, never the box's.
export VERIFY_APP_RUN_DIR="$t/va/run" VERIFY_APP_EVIDENCE_DIR="$t/va/evidence" XDG_STATE_HOME="$t/state" PATH="$kit/scripts:$PATH"
set +e; vout="$("$repo/.agents/skills/verify-app/scripts/verify-app" run 2>&1)"; rc=$?; set -e
[[ "$rc" == 0 ]] || fail "verify-app run on the edited contract failed (exit $rc): $vout"
[[ "$(cat "$repo/setup-ran")" == declared ]] || fail "verify-app did not run the declared setup"
[[ "$(cat "$VERIFY_APP_EVIDENCE_DIR/hello/json.stdout")" == '{"name":"Grace","text":"Hello, Grace"}' ]] \
  || fail "drive did not follow values.name and values.greeting: $(cat "$VERIFY_APP_EVIDENCE_DIR/hello/json.stdout")"
# A contract declaring a service this CLI helper cannot start: launch refuses, naming it, before setup.
rm "$repo/setup-ran"; printf '[services.web]\ncommand = "true"\n' >>"$repo/qc.toml"
sed -i '/^\[services\]$/d' "$repo/qc.toml"
set +e; vout="$("$repo/.agents/skills/verify-app/scripts/verify-app" launch 2>&1)"; rc=$?; set -e
[[ "$rc" != 0 ]] && grep -qF 'qc.toml declares services (web)' <<<"$vout" && [[ ! -e "$repo/setup-ran" ]] \
  || fail "a declared service was not refused before setup (exit $rc): $vout"
echo "contract: ok (both templates' qc.toml valid; missing or unsupported format, missing, unknown, mistyped or empty keys, a [browser] without a release pin, bad TOML and no file fail naming the field; ts verify-app names the missing install, then follows qc.toml's setup and values)"
