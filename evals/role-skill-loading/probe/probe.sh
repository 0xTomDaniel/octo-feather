#!/usr/bin/env bash
# gh107 probes: one isolated headless Pi role run on a fixture repo, then a deterministic transcript grade.
# Usage: probe.sh KIT ROLE FIXTURE_DIR BRIEF_FILE OUT_DIR
# Isolation: env -i; PATH = a bin holding only pi, then /usr/local/bin:/usr/bin:/bin (no herdr, no herdr-say,
# no kit scripts); sandbox HERDR_SESSION; HOME and PI_CODING_AGENT_DIR are temp copies (auth/models/extensions
# only, no sessions); --session-dir in OUT_DIR, so nothing lands in ~/.pi/agent/sessions.
set -euo pipefail
kit=$1 role=$2 fix=$3 brief=$4 out=$5
mkdir -p "$out"/home "$out"/bin "$out"/sessions
ln -sf "$(command -v pi)" "$out/bin/pi"
[ -n "${FAKEBIN:-}" ] && cp "$FAKEBIN"/* "$out/bin/"   # optional stubs (fake gh), first on PATH
a=$out/home/.pi/agent; mkdir -p "$a"
for f in settings.json models.json auth.json exe-dev-llm-integration.json; do cp "$HOME/.pi/agent/$f" "$a/"; done
cp -r "$HOME/.pi/agent/extensions" "$a/"
cp "$HOME/.gitconfig" "$out/home/" 2>/dev/null || printf '[user]\n\tname = probe\n\temail = probe@example.invalid\n' > "$out/home/.gitconfig"
# Box rule: launch only with >= 2500 MB available and < 500 MB swap used.
until read -r av su < <(free -m | awk '/^Mem:/{a=$7} /^Swap:/{s=$3} END{print a, s}'); (( av >= 2500 && su < 500 )); do
  echo "probe: waiting for memory (available ${av} MB, swap used ${su} MB)" >&2; sleep 30; done
cd "$fix"
env -i HOME="$out/home" PATH="$out/bin:/usr/local/bin:/usr/bin:/bin" TERM=dumb LANG=C.UTF-8 \
  HERDR_SESSION="gh107-probe-sandbox" FAKE_GH_LOG="$out/gh.log" PI_CODING_AGENT_DIR="$a" XDG_CACHE_HOME="$out/home/.cache" \
  UV_CACHE_DIR="$HOME/.cache/uv" \
  timeout 1800 python3 "$kit/scripts/pi-role" "$kit/agents/$role.md" --session-dir "$out/sessions" -p "$(cat "$brief")" \
  > "$out/final.txt" 2> "$out/stderr.txt" || echo "pi exit $?" >> "$out/stderr.txt"
ls "$out"/sessions/*/*.jsonl "$out"/sessions/*.jsonl 2>/dev/null | head -1 > "$out/session-path.txt" || true
