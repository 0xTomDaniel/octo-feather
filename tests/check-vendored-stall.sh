#!/usr/bin/env bash
# gate: e2e
# End-to-end test for `just vendored-fetch` (scripts/check-vendored) through a stalled proxy, on a throwaway copy of
# the kit's justfile, Skillfile and check-vendored, against a copy of the warm cache: a fetch through a stalled proxy
# times out within its bound, naming the fix. A real network namespace and wall-clock bounds (quality #test-kinds).
# Needs the warm cache `just vendored-fetch` makes (CI runs it before `just check`).
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
src="${XDG_CACHE_HOME:-$HOME/.cache}/octo-feather/skillfile"
[[ -d "$src/git" && -d "$src/bin" ]] || { echo "check-vendored-stall test: no warm cache at $src; run \`just vendored-fetch\`" >&2; exit 1; }
# The proof needs Linux user namespaces: where `unshare` or `ip` is missing, name the skip (exit 77).
unshare -rn sh -c 'ip link set lo up' 2>/dev/null \
  || { echo "check-vendored-stall test: skipped, Linux-only proof: stalled and dripping proxy fetch (needs unshare -rn and ip)"; exit 77; }
r="$t/repo"; mkdir -p "$r/scripts" "$t/c/octo-feather"
cp "$kit/justfile" "$kit/Skillfile" "$r/"
cp "$kit/scripts/check-vendored" "$r/scripts/"
cp -r "$src" "$t/c/octo-feather/"; chmod -R u+w "$t/c"
export XDG_CACHE_HOME="$t/c"
has() { grep -qF -- "$1" <<<"$out" || { echo "check-vendored-stall test: output lacks '$1': $out" >&2; exit 1; }; }
rm -rf "$t/c/octo-feather/skillfile/git"
# Stalled network, two ways: a proxy that accepts and never answers (silent), and one that
# drips CONNECT response headers every 0.2 s forever (slow progress). Either way the fetch
# gives up within one total bound. Own network namespace with only loopback up, so it never
# reaches the real network, online or not.
cat > "$t/stall.sh" <<'SH'
ip link set lo up
python3 -c '
import socket, sys, threading, time
s = socket.socket(); s.bind(("127.0.0.1", 0)); s.listen(16)
open(sys.argv[1], "w").write(str(s.getsockname()[1])); held = []
def drip(c):
    try:
        c.recv(65536); c.sendall(b"HTTP/1.1 200 Connection established\r\n")
        while True: c.sendall(b"X-Drip: 1\r\n"); time.sleep(0.2)
    except OSError: pass
while True:
    c = s.accept()[0]; held.append(c)
    if sys.argv[2] == "drip": threading.Thread(target=drip, args=(c,), daemon=True).start()
' "$1/port" "$3" & lp=$!
for _ in $(seq 50); do [[ -s "$1/port" ]] && break; sleep 0.1; done
p="http://127.0.0.1:$(cat "$1/port")"
HTTPS_PROXY="$p" https_proxy="$p" OCTO_FEATHER_FETCH_TIMEOUT=2 just -f "$2/justfile" vendored-fetch; rc=$?
kill "$lp"; rm -f "$1/port"; exit "$rc"
SH
stall() { local s; s=$SECONDS; set +e; out="$(unshare -rn bash "$t/stall.sh" "$t" "$r" "$1" 2>&1)"; rc=$?; set -e
  [[ "$rc" == 1 && $((SECONDS - s)) -le 10 ]] || { echo "check-vendored-stall test: $1 proxy fetch want exit 1 within 10s, got $rc after $((SECONDS - s))s: $out" >&2; exit 1; }
  has "rerun \`just vendored-fetch\`"; }
for mode in silent drip; do stall "$mode"; has "git fetch of mattpocock/skills@49dd158d1076134a641b33efb035946536778336 timed out after 2s"; done
rm -rf "$t/c/octo-feather/skillfile/bin"
for mode in silent drip; do stall "$mode"; has "downloading skillfile v1.9.2 from https://github.com/eljulians/skillfile/releases/download/v1.9.2/"; has "timed out after 2s"; done
echo "check-vendored-stall test: ok (silent and dripping proxy)"
