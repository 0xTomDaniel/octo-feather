#!/usr/bin/env bash
# Integration test for scripts/review-host (issue #65) through its CLI, over the
# real Spec Chat clone ($SPEC_CHAT_CLONE, default ~/src/spec-chat): on a spawned
# pane's PATH, --help passes through, register refuses a page with no Spec Chat
# runtime, and re-registering at a new commit keeps the link and leaves only the
# registry's own review-serve, also where review-host.py cannot see the live
# server (no /proc, as on macOS: register runs in a user+mount namespace with
# /proc covered, `ps` reading the real one, as macOS ps reads the kernel), and a
# process that only names the registry is never stopped. Only --test rows in a
# temp state dir with a space in its path, on loopback; every process it starts
# is stopped. No Spec Chat file is copied or changed. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
clone="${SPEC_CHAT_CLONE:-$HOME/src/spec-chat}"
if [[ ! -f "$clone/skill/review-spec/scripts/review-host.py" ]]; then
  echo "review-host: skipped (no Spec Chat clone at $clone)"; exit 0
fi
clone="$(cd "$clone" && pwd -P)"; server="$clone/skill/review-spec/assets/review-serve.py"
t="$(mktemp -d)"
state="$t/state space"; registry="$state/registry.toml"
# Real review-serve processes on this registry: a python whose argv runs $server on it.
serve_pids() { ps -Aww -o pid=,args= | awk -v s="$server --registry $registry --bind " \
  '{p=index($0, s)} p && substr($0, 1, p-1) ~ /^ *[0-9]+ [^ ]*python[0-9.]* $/ {print $1}' | sort; }
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

# 4. A process that only names this registry is never stopped, even by a register that then fails:
#    the reviewed repro, one passing the real script path as a plain argument, one running another review-serve.py.
mkdir -p "$t/pids" "$t/other"
bg() { local name="$1"; shift; setsid sh -c 'echo $$ > "$1"; shift; exec "$@"' sh "$t/pids/$name" "$@" >/dev/null 2>&1 & }
printf 'import time\ntime.sleep(90)\n' > "$t/other/review-serve.py"
bg sleeper python3 -c "import time; time.sleep(90)" review-serve.py --registry "$registry"
bg lookalike python3 -c "import time; time.sleep(90)" "$server" --registry "$registry" --bind 127.0.0.1 --port 1 --host 127.0.0.1
bg otherscript python3 "$t/other/review-serve.py" --registry "$registry" --bind 127.0.0.1 --port 1 --host 127.0.0.1
plain="$t/plain"  # the reviewed repro word for word: a state path without a space
bg plainsleeper python3 -c "import time; time.sleep(90)" review-serve.py --registry "$plain/registry.toml"
for _ in $(seq 50); do [[ -s "$t/pids/sleeper" && -s "$t/pids/lookalike" && -s "$t/pids/otherscript" && -s "$t/pids/plainsleeper" ]] && break; sleep 0.1; done
set +e; out="$("$kit/scripts/review-host" register --state-dir "$plain" --test --slug w65 --owner test/w65 \
  --base HEAD docs/specs/missing.spec.html 2>&1)"; rc=$?; set -e
[[ "$rc" != 0 ]] || fail "register of a missing spec passed: $out"
kill -0 "$(cat "$t/pids/plainsleeper")" 2>/dev/null || fail "failing register stopped the repro sleeper: $out"
kill -- "-$(cat "$t/pids/plainsleeper")"; rm "$t/pids/plainsleeper"
alive() { local n; for n in sleeper lookalike otherscript; do kill -0 "$(cat "$t/pids/$n")" 2>/dev/null || fail "$1: $n was stopped: $out"; done; }
set +e; out="$("$kit/scripts/review-host" register --state-dir "$state" --test --slug w65 --owner test/w65 \
  --base HEAD docs/specs/missing.spec.html 2>&1)"; rc=$?; set -e
[[ "$rc" != 0 ]] || fail "register of a missing spec passed: $out"
alive "failing register"
page v3 "$script"; reg; [[ "$rc" == 0 && "$(link)" == "$first" ]] || fail "register v3: $out"
alive "register"
[[ "$(grep -c 'left pid .* running: it names' <<<"$out")" == 3 ]] || fail "lookalikes not reported: $out"
for n in sleeper lookalike otherscript; do kill -- "-$(cat "$t/pids/$n")"; rm "$t/pids/$n"; done
check_link v3

# 5. A real review-serve on this registry that the registry does not own is stopped by the next register.
bg stray python3 "$server" --registry "$registry" --bind 127.0.0.1 --port 0 --host 127.0.0.1
for _ in $(seq 50); do [[ "$(serve_pids | wc -l)" == 2 ]] && break; sleep 0.1; done
[[ "$(serve_pids | wc -l)" == 2 ]] || fail "stray review-serve did not start"
stray="$(cat "$t/pids/stray")"
page v4 "$script"; reg; [[ "$rc" == 0 && "$(link)" == "$first" ]] || fail "register v4: $out"
[[ "$out" == *"stopped review-serve pid $stray,"* ]] || fail "stray $stray not reported stopped: $out"
check_link v4

# 6. Where review-host.py cannot see its live server (no /proc, as on macOS), the link holds and the old server
#    is gone: register runs in a user+mount namespace with tmpfs over /proc; `ps` (macOS-style, args joined by
#    spaces) reads the real /proc, bound aside before it is covered.
mkdir -p "$t/realproc" "$t/psbin"
cat > "$t/psbin/ps" <<'PY'
#!/usr/bin/env python3
import os
proc = os.environ["FAKE_PS_PROC"]
for pid in filter(str.isdigit, os.listdir(proc)):
    try:
        argv = open(f"{proc}/{pid}/cmdline", "rb").read().rstrip(b"\0").split(b"\0")
        uid = os.stat(f"{proc}/{pid}").st_uid
    except OSError:
        continue
    if argv != [b""]:
        print(pid, uid, b" ".join(argv).decode(errors="replace"))
PY
chmod +x "$t/psbin/ps"
noproc() { unshare -rm sh -c 'mount --rbind /proc "$1" && mount -t tmpfs none /proc && shift && exec "$@"' sh "$t/realproc" "$@"; }
if ! noproc sh -c '! test -e /proc/self' 2>/dev/null; then
  echo "review-host: ok (no-/proc case skipped: unshare -rm cannot cover /proc here)"
else
  before="$(serve_pids)"
  page v5 "$script"
  set +e; out="$(FAKE_PS_PROC="$t/realproc" PATH="$t/psbin:$PATH" noproc "$kit/scripts/review-host" register \
    --state-dir "$state" --test --slug w65 --owner test/w65 --base HEAD docs/specs/x.spec.html 2>&1)"; rc=$?; set -e
  [[ "$rc" == 0 ]] || fail "register v5 without /proc: $out"
  [[ "$(link)" == "$first" ]] || fail "without /proc the link moved: $first -> $(link)"
  [[ "$(serve_pids)" != "$before" ]] || fail "without /proc the old server was not replaced"
  check_link v5
fi
echo "review-host: ok (pane PATH, --help passes through, no <script> and no runtime.js refused, re-register keeps link and only the owned server, lookalikes left running and reported, stray stopped, no-/proc link kept; state path with a space)"
