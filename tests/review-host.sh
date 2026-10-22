#!/usr/bin/env bash
# Integration test for scripts/review-host (issue #65) through its CLI, over the
# real Spec Chat clone ($SPEC_CHAT_CLONE, default ~/src/spec-chat): on a spawned
# pane's PATH, --help passes through, register refuses a page with no Spec Chat
# runtime, and re-registering at a new commit keeps the link and leaves only the
# registry's own review-serve, also where review-host.py cannot see the live
# server (macOS has no /proc: a test copy of the clone stands in). Only --test
# rows in a temp state dir on loopback; every server it starts is stopped.
# Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
clone="${SPEC_CHAT_CLONE:-$HOME/src/spec-chat}"
if [[ ! -f "$clone/skill/review-spec/scripts/review-host.py" ]]; then
  echo "review-host: skipped (no Spec Chat clone at $clone)"; exit 0
fi
t="$(mktemp -d)"
state="$t/state"; registry="$state/registry.toml"
serve_pids() { ps -Ao pid=,args= | awk -v r="$registry" '/review-serve\.py/ && index($0, "--registry " r) {print $1}' | sort; }
cleanup() {
  local p
  for p in $(serve_pids); do kill "$p" 2>/dev/null || true; done
  for p in "$t"/pids/*; do [[ -f "$p" ]] && { kill -- "-$(cat "$p")" 2>/dev/null || true; }; done
  rm -rf "$t"
}
trap cleanup EXIT
fail() { echo "review-host test: $*" >&2; exit 1; }
unset HERDR_SESSION
export XDG_STATE_HOME="$t/xdg" SPEC_CHAT_APPROVED_INGRESS_PORTS=""   # loopback, any free port

# 1. A spawned pane's PATH resolves review-host to the kit script; --help passes through.
mkdir -p "$t/bin" "$t/cwd" "$t/spawn"
cat > "$t/bin/herdr" <<EOF
#!/usr/bin/env bash
[[ "\$1 \${2:-}" != "tab create" ]] || printf '%s\n' "\$@" > "$t/spawn/tab-args"
exec "$kit/tests/fixtures/herdr-spawn/herdr" "\$@"
EOF
chmod +x "$t/bin/herdr"
env FAKE_HERDR_DIR="$t/spawn" PATH="$t/bin:$PATH" XDG_CACHE_HOME="$t/cache" HERDR_PANE_ID=w9:p0 \
  "$kit/.agents/skills/herdr-comms/assets/herdr-spawn" --workspace w9 --name t1 --role implementer \
  --cwd "$t/cwd" >/dev/null 2>&1 || fail "herdr-spawn failed"
pane_path="$(sed -n 's/^PATH=//p' "$t/spawn/tab-args")"
[[ -n "$pane_path" ]] || fail "spawned pane got no PATH"
[[ "$(PATH="$pane_path" command -v review-host)" == "$kit/scripts/review-host" ]] \
  || fail "review-host on the pane's PATH is '$(PATH="$pane_path" command -v review-host || true)'"
help="$(PATH="$pane_path" review-host --help)" || fail "review-host --help exited non-zero"
[[ "$help" == *"usage: review-host.py"*"register"* ]] || fail "--help did not pass through: $help"

# A target repo with a spec; its page shows its version in <h1>.
g() { git -c user.name=t -c user.email=t@t -c init.defaultBranch=main "$@"; }
g init -q "$t/repo"; mkdir -p "$t/repo/docs/specs"; cd "$t/repo"
page() { # $1: version, $2: head
  printf '<!doctype html><html><head>%s</head><body><article class="spec"><h1>%s</h1></article></body></html>\n' \
    "$2" "$1" > docs/specs/x.spec.html
  g add -A; g commit -qm "$1"
}
script='<script defer src="./.viz/runtime.js"></script>'
reg() { set +e; out="$("$kit/scripts/review-host" register --state-dir "$state" --test --slug w65 --owner test/w65 \
  --base HEAD docs/specs/x.spec.html 2>&1)"; rc=$?; set -e; }
link() { sed -n 's/.* URL: \(http[^ ]*\) .*/\1/p' <<<"$out"; }

# 2. Refused: no runtime <script>, then a <script> whose .viz/runtime.js is missing. Nothing registered.
page v0 ""
reg
[[ "$rc" != 0 && "$out" == *"no Spec Chat runtime <script>"*"$script"*"preflight.py"* ]] || fail "no <script>: rc=$rc $out"
[[ ! -e "$registry" ]] || fail "no <script>: registered anyway"
page v0 "$script"
reg
[[ "$rc" != 0 && "$out" == *"$t/repo/docs/specs/.viz/runtime.js is missing; run python3 "*"preflight.py"* ]] \
  || fail "no runtime.js: rc=$rc $out"
[[ ! -e "$registry" ]] || fail "no runtime.js: registered anyway"

# 3. Re-register at a new commit: the earlier link answers 200 with the new version; only the owned server runs.
cp -r "$clone/skill/review-spec/assets/viz" docs/specs/.viz
page v1 "$script"; reg; [[ "$rc" == 0 ]] || fail "register v1: $out"
first="$(link)"; [[ -n "$first" ]] || fail "register v1 printed no link: $out"
page v2 "$script"; reg; [[ "$rc" == 0 ]] || fail "register v2: $out"
[[ "$(link)" == "$first" ]] || fail "re-register moved the link: $first -> $(link)"
owned() { sed -n 's/^pid = //p' "$registry"; }
check_link() { # $1: version
  local body code; code="$(curl -s -o "$t/body" -w '%{http_code}' "$first")"; body="$(cat "$t/body")"
  [[ "$code" == 200 && "$body" == *"<h1>$1</h1>"* ]] || fail "$first answered $code without $1"
  [[ "$(serve_pids)" == "$(owned)" ]] || fail "review-serve pids [$(serve_pids | xargs)] != registry's [$(owned)]"
}
check_link v2

# 4. A review-serve on this registry that the registry does not own is stopped by the next register.
mkdir -p "$t/pids"
setsid sh -c 'echo $$ > "$1"; shift; exec "$@"' sh "$t/pids/stray" python3 "$clone/skill/review-spec/assets/review-serve.py" \
  --registry "$registry" --bind 127.0.0.1 --port 0 --host 127.0.0.1 >/dev/null 2>&1 &
for _ in $(seq 50); do [[ "$(serve_pids | wc -l)" == 2 ]] && break; sleep 0.1; done
[[ "$(serve_pids | wc -l)" == 2 ]] || fail "stray review-serve did not start"
page v3 "$script"; reg; [[ "$rc" == 0 && "$(link)" == "$first" ]] || fail "register v3: $out"
check_link v3

# 5. Where review-host.py cannot see its live server (no /proc, as on macOS), the link still holds and the
#    old server is gone. A copy of the clone whose process_cmdline finds nothing stands in.
mkdir -p "$t/mac/skill"; cp -r "$clone/skill/review-spec" "$t/mac/skill/"
python3 - "$t/mac/skill/review-spec/scripts/review-host.py" <<'EOF'
import sys; p = sys.argv[1]; s = open(p).read()
assert "def process_cmdline(pid: int) -> list[str] | None:\n" in s, "Spec Chat's process_cmdline changed; update this stand-in"
s = s.replace("def process_cmdline(pid: int) -> list[str] | None:\n", "def process_cmdline(pid: int) -> list[str] | None:\n    return None\n", 1)
open(p, "w").write(s)
EOF
before="$(serve_pids)"
page v4 "$script"; SPEC_CHAT_CLONE="$t/mac" reg; [[ "$rc" == 0 ]] || fail "register v4 without /proc: $out"
[[ "$(link)" == "$first" ]] || fail "without /proc the link moved: $first -> $(link)"
[[ "$(serve_pids)" != "$before" ]] || fail "without /proc the old server was not replaced"
check_link v4
echo "review-host: ok (pane PATH, --help passes through, no <script> and no runtime.js refused, re-register keeps link and only the owned server, stray stopped, no-/proc link kept)"
