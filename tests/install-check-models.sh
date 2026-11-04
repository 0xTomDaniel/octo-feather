#!/usr/bin/env bash
# Integration test for `just install-check`, its review service and models section (#508; setup
# tests/lib/install-check.sh):
#   Review service (#462): systemctl a stub: active and enabled ok; inactive, failed or no systemctl named with Spec
#     Chat's installer --public <vm>.exe.xyz --service, exit 1; a models MANUAL line names just install-check-models
#     and no install-check run calls pi -p. just install-check-models: the stub tests/fixtures/install-check/pi, asserted
#     first on PATH, plays the proxy: right keys ok per role model with its roles and for the judgment model (a classify
#     call); a key with trailing terminal characters REJECTED; a proxy not answering UNREACHABLE; a judgment model Pi does
#     not list FAILED; the key never printed nor on pi's command line.
# Run by `just check`; setup tests/lib/install-check.sh.
# shellcheck source=tests/lib/install-check.sh
source "$(dirname "$0")/lib/install-check.sh"
# The review service (spec remote#review-service, #review-setup): active and enabled ok; inactive or not installed
# NOT RUNNING, no systemctl MISSING, each naming Spec Chat's installer with --public <vm>.exe.xyz --service, exit 1.
review_fix="$t/home/src/spec-chat/scripts/install-spec-chat --review $kit/docs/specs/index.spec.html --public \S+\.exe\.xyz --service \(remote#review-setup\)"
check 0 "$gh_target" ""
grep -qx "review ok  spec-chat-review.service active, enabled (Spec Chat's review service, systemd --user)" <<<"$out" || fail "review service up: no ok line: $out"
# The model check is its own recipe (spec remote#host-models): one line names it, and no run above called a model.
grep -qx 'models MANUAL not checked here (no model call); at box setup and after a model key change: just install-check-models' <<<"$out" \
  || fail "no line naming just install-check-models: $out"
nomodel
printf 'ActiveState=inactive\nUnitFileState=\n' >"$t/unit"; check 1 "$gh_target" ""
grep -qxE "review NOT RUNNING spec-chat-review\.service is inactive, not installed \(want active, enabled: the systemd user service box setup installs\); $review_fix" <<<"$out" \
  || fail "review service not installed: no NOT RUNNING line naming the installer: $out"
printf 'ActiveState=failed\nUnitFileState=enabled\n' >"$t/unit"; check 1 "$gh_target" ""
grep -qxE "review NOT RUNNING spec-chat-review\.service is failed, enabled .*; $review_fix" <<<"$out" || fail "review service failed: not named: $out"
printf 'ActiveState=active\nUnitFileState=enabled\n' >"$t/unit"
mv "$t/bin/systemctl" "$t/systemctl"; saved="$clean"; clean="$(hide systemctl "$saved")"
check 1 "$gh_target" ""; clean="$saved"; mv "$t/systemctl" "$t/bin/systemctl"
grep -qxE "review MISSING no systemctl: the review service runs as a systemd user service \(spec-chat-review\.service\); on a systemd box: $review_fix" <<<"$out" \
  || fail "no systemctl: no MISSING line naming the installer: $out"
# just install-check-models (spec remote#host-models): the stub pi (tests/fixtures/install-check/pi) plays the model
# proxy; it is first on PATH, which the recipe's own pi line proves before any probe case. Each model a role file names
# answers one print-mode call, the judgment model (evals/judgment-model.json) one classify call through octo-feather-qa's
# bench extension: right keys ok; a key with trailing terminal characters REJECTED (a role model's in models.json, the
# judgment model's in auth.json); a proxy that does not answer UNREACHABLE; a judgment model Pi does not list FAILED;
# each with its users and the fix, the key never printed nor on a command line.
mkdir -p "$t/mbin" "$t/pi-agent"; cp "$kit/tests/fixtures/install-check/pi" "$t/mbin/pi"
issued="sk-proxy-0123456789abcdefghijklmnopqrstuv"; printf '%s' "$issued" >"$t/issued"
judge="$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))["model"])' "$kit/evals/judgment-model.json")"
jprov="${judge%%/*}"
keys() { # ANTHROPIC_KEY OPENAI_BASE JUDGE_KEY: Pi's provider config (models.json) and stored key (auth.json)
  python3 -c 'import json, sys; json.dump({"providers": {"anthropic": {"baseUrl": "https://proxy.example/", "apiKey": sys.argv[1]}, "openai": {"baseUrl": sys.argv[3], "apiKey": sys.argv[2]}}}, open(sys.argv[4], "w")); json.dump({sys.argv[7]: {"type": "api_key", "key": sys.argv[5]}}, open(sys.argv[6], "w"))' \
    "$1" "$issued" "$2" "$t/pi-agent/models.json" "$3" "$t/pi-agent/auth.json" "$jprov"; }
models() { # WANT: run the recipe from $t with the stub first on PATH; output in $out
  local rc=0; : >"$t/pi-calls"
  out="$(cd "$t" && PI_CODING_AGENT_DIR="$t/pi-agent" PI_STUB_LOG="$t/pi-calls" PI_STUB_ISSUED="$t/issued" PI_STUB_CLASSIFIERS="${avail-$judge}" HOME="$t/home" PATH="$t/mbin:$PATH" \
    just -f "$kit/justfile" install-check-models 2>&1)" || rc=$?
  [[ "$rc" == "$1" ]] || fail "install-check-models: want exit $1, got $rc: $out"
  ! grep -qF "$issued" <<<"$out" && ! grep -qF "$issued" "$t/pi-calls" || fail "a key was printed or passed on a command line: $out $(cat "$t/pi-calls")"
}
[[ "$(PATH="$t/mbin:$PATH" command -v pi)" == "$t/mbin/pi" ]] || fail "stub pi is not first on PATH"
roles() { grep -lx "model: $1" "$kit"/agents/*.md | xargs -n1 basename | sed 's/\.md$//' | paste -sd, - | sed 's/,/, /g'; }
ra="$(roles anthropic/claude-opus-5-5)"; ro="$(roles openai/gpt-6.1-sol)"
[[ -n "$ra" && -n "$ro" && -n "$judge" && -z "$(roles "$judge")" ]] \
  || fail "the role files no longer name anthropic/claude-opus-5-5 and openai/gpt-6.1-sol, or name the judgment model $judge: update this test"
jwho="judgment model (evals/judgment-model.json): the advisory judge, judgment benches"
keys "$issued" "https://proxy.example/v1" "$issued"; models 0
grep -qx "models pi $t/mbin/pi (one short call per role model and the judgment model, no tools; Pi reads each key from $t/pi-agent/models.json, $t/pi-agent/auth.json or its environment)" <<<"$out" \
  || fail "install-check-models did not resolve the stub pi first: $out"
calls() { python3 -c 'import json, sys; [print(" ".join(json.loads(l))) for l in open(sys.argv[1])]' "$t/pi-calls"; }
grep -qx "model  anthropic/claude-opus-5-5 ok (roles $ra)" <<<"$out" && grep -qx "model  openai/gpt-6.1-sol ok (roles $ro)" <<<"$out" \
  && grep -qxF "model  $judge ok ($jwho)" <<<"$out" \
  && [[ "$(calls | grep -c '^-p --mode json ')" == 2 && "$(calls | grep -c ' -p /octo-feather-bench ')" == 1 && "$(wc -l <"$t/pi-calls")" == 3 ]] \
  || fail "right keys: not one ok line and one call per role model and the judgment model: $out $(cat "$t/pi-calls")"
keys "$issued"$'\e[201~' "https://proxy.example/v1" "$issued"; models 1
grep -qx "model  anthropic/claude-opus-5-5 REJECTED key (401) for roles $ra (the key there ends in or holds whitespace or terminal characters); put the key the model proxy issued for provider anthropic in $t/pi-agent/models.json (providers.anthropic.apiKey) or its environment, exactly, no trailing characters, then rerun just install-check-models" <<<"$out" \
  && grep -qx "model  openai/gpt-6.1-sol ok (roles $ro)" <<<"$out" || fail "key with trailing junk: no REJECTED line with roles and fix: $out"
keys "$issued" "https://proxy.example/v1" "$issued"$'\n'; models 1
grep -qxF "model  $judge REJECTED key (401) for $jwho (the key there ends in or holds whitespace or terminal characters); put the key the model proxy issued for provider $jprov in $t/pi-agent/auth.json ($jprov.key) or its environment, exactly, no trailing characters, then rerun just install-check-models" <<<"$out" \
  || fail "judgment model key with a trailing newline: no REJECTED line with its users and fix: $out"
keys "$issued" "https://unreachable.example/v1" "$issued"; models 1
grep -qx "model  openai/gpt-6.1-sol UNREACHABLE (Connection error.) for roles $ro; the model proxy for provider openai did not answer: check this box reaches https://unreachable.example/v1 ($t/pi-agent/models.json, providers.openai.baseUrl) and the proxy is up, then rerun just install-check-models" <<<"$out" \
  || fail "proxy not answering: no UNREACHABLE line with roles and fix: $out"
keys "$issued" "https://proxy.example/v1" "$issued"; avail="" models 1
grep -qxF "model  $judge FAILED (Pi lists no classifier $judge: no key for its provider, or not in Pi catalog) for $jwho; run pi --model $judge -p ok by hand for the full error Pi gives, then rerun just install-check-models" <<<"$out" \
  || fail "judgment model Pi does not list: no FAILED line: $out"
echo "install-check-models: ok (review service ok, NOT RUNNING and no systemctl MISSING naming the installer; models MANUAL naming just install-check-models, no model call; install-check-models with a stub pi first on PATH: role models and the judgment model ok, trailing-junk keys REJECTED (models.json, auth.json), proxy UNREACHABLE, judgment model not listed FAILED, key never printed)"
