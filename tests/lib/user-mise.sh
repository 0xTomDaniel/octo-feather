# shellcheck shell=bash
# Sourced by tests/user-mise.sh and each tests/user-mise-<section>.sh (the #493 regression fixture, one gate item per
# section, #508), never run itself: in tests/lib/ so the gate's tests/*.sh glob does not collect it. Each item builds
# its own fixture user HOME in its own user+mount+network namespace (unshare -rmn: offline), then runs its section of
# tests/fixtures/user-mise/check.py's assertions there: `check.py assert $USER_MISE_SECTION`, which the item exports.
#   The user: HOME a fresh dir mounted over the caller's HOME (the same path: the qc sandbox keeps /tmp private, so a
#   HOME under it would vanish there, unlike any user's); mise's data dir there, the box's kit tool installs bound into it read-only (a write
#   into one fails: asserted); a global ~/.config/mise/config.toml naming tools installed there but absent from the
#   kit's mise.lock: erlang (a fake install dir), a python of another minor than .python-version (a fake install dir
#   whose python3 runs the gate's Python), so the python3 first on PATH is its mise shim, and rust, whose cargo and
#   some-cli live in ~/.cargo/bin, so their shims go stale once HOME moves: `mise doctor --json` exits 0 under the
#   user's HOME and 1 under a moved HOME while still printing its dirs (asserted). The kit checked out under that HOME
#   (a copy of this checkout's files, committed in a fresh repo), so the moved-HOME parent walk sees the global config.
#   The environment a pane of a named Herdr session gives (HERDR_SESSION=fixture and the other HERDR_* variables), no
#   real Herdr. uv's Pythons and cache and pnpm's store are the box's, bound in where they sit under a HOME.
#   Real mise dirs of the box are bound read-only over themselves in the namespace: nothing here can write them.
# This file is the glue (namespaces, mounts, the user's environment, test doubles); the user's files and every
# assertion are tests/fixtures/user-mise/check.py's, run as a command. Each section ends with (5): the user's mise
# config, installs and shims byte-identical across it, doctor's answer under the user's HOME unchanged.
# `tests/user-mise.sh --gate [pytest args]` (just check-user-mise, #493 AC1): the whole gate, or the items pytest args
# choose, run inside the same fixture instead of the assertions, with the caller's GATE_WORKERS (default 1), in the
# named session's pane, or with USER_MISE_HERDR=none outside Herdr (no HERDR_* variable at all); the assertions always
# run in the pane. Linux only (unshare).
set -euo pipefail
[[ "$(uname -s)" != Darwin ]] || { echo "user-mise: skipped, not on macOS (unshare; CI runs it)"; exit 0; }
[[ -z "${USER_MISE_FIXTURE:-}" ]] || { echo "user-mise: skipped inside its own fixture"; exit 0; }
fail() { echo "user-mise: $*" >&2; exit 1; }
kit="$(cd "$(dirname "$0")/.." && pwd -P)"

case "${USER_MISE_STAGE:-0}" in
0)  # The box's paths, asked before anything moves: mise's dirs (a throwaway state dir, so mise records nothing in the
    # box's), uv's Python installs and cache, pnpm's store, the gate's Python, the check-vendored cache.
    command -v mise >/dev/null || fail "no mise on PATH"
    ms="$(mktemp -d)"; md="$(cd "$kit" && MISE_STATE_DIR="$ms" mise doctor --json 2>/dev/null)" || true; rm -rf "$ms"
    d() { jq -r --arg k "$1" '.dirs[$k] // empty' <<<"$md"; }
    USER_MISE_RDATA="$(d data)"; USER_MISE_RCACHE="$(d cache)"; USER_MISE_RCONFIG="$(d config)"; USER_MISE_RSTATE="$(d state)"
    [[ -d "$USER_MISE_RDATA/installs" ]] || fail "mise's data dir has no installs ($USER_MISE_RDATA): run mise install --locked in the kit"
    USER_MISE_MISE="$(realpath "$(command -v mise)")"; USER_MISE_UVPY="$(uv --color never python dir)"; USER_MISE_UVCACHE="$(uv --color never cache dir)"
    USER_MISE_PY="$(cd "$kit" && uv --color never python find --system)"; USER_MISE_PNPM="$(cd "$kit" && pnpm store path)"
    USER_MISE_VC="${XDG_CACHE_HOME:-$HOME/.cache}/octo-feather/skillfile"; USER_MISE_PI="$(command -v pi || true)"
    USER_MISE_UID="$(id -u)"; USER_MISE_GID="$(id -g)"; USER_MISE_NAME="$(id -un)"; USER_MISE_HOME="$(cd "$HOME" && pwd -P)";
    export USER_MISE_HOME USER_MISE_RDATA USER_MISE_RCACHE USER_MISE_RCONFIG USER_MISE_RSTATE USER_MISE_MISE USER_MISE_UVPY USER_MISE_UVCACHE USER_MISE_PY \
      USER_MISE_PNPM USER_MISE_VC USER_MISE_PI USER_MISE_UID USER_MISE_GID USER_MISE_NAME
    unshare -rmn true 2>/dev/null || fail "unshare -rmn failed: the fixture runs in a user+mount+network namespace (enable unprivileged user namespaces)"
    # --gate in the fixture's pane: this run, in the caller's env and lane, holds the heavy slot for its items (#668;
    # octo-feather-slot --help, hold); the gate in the fixture's pane runs nested under it, the box's slots dir bound in.
    if [[ "${1:-}" == --gate && "${USER_MISE_HERDR:-fixture}" == fixture ]]; then
      n="$(cd "$kit" && just test --collect-only -q "${@:2}" 2>/dev/null | grep -c '::')" || true
      coproc "$kit/scripts/octo-feather-slot" hold --kind heavy --items "${n:-0}"
      read -r said <&"${COPROC[0]}" || true
      [[ "$said" == @(held|free|nested):* ]] || { { printf '%s\n' "$said"; cat <&"${COPROC[0]}"; } >&2; exit 75; }
      echo "user-mise: heavy slot: $said" >&2
      USER_MISE_SLOTS="${XDG_STATE_HOME:-$HOME/.local/state}/octo-feather/slots"; export USER_MISE_SLOTS
    fi
    set +e; USER_MISE_STAGE=1 timeout -k 10 "${USER_MISE_TIMEOUT:-1200}" unshare -rmn "$0" "$@"; rc=$?; set -e
    [[ "$rc" != 124 && "$rc" != 137 ]] || echo "user-mise: timed out after ${USER_MISE_TIMEOUT:-1200} s (USER_MISE_TIMEOUT), killed" >&2
    exit "$rc" ;;
1)  # Root of the namespace: the user's HOME built in $t/home, mounted over the caller's HOME, then the rest as the
    # caller's uid (a nested user namespace mapping it back).
    t="$(mktemp -d)"; t="$(cd "$t" && pwd -P)"; F="$t/home"; D="$F/.local/share/mise"; RH="$USER_MISE_HOME"
    ip link set lo up || fail "loopback up in the network namespace (offline, but local servers answer, as on the box)"
    [[ "$t/" != "$RH/"* ]] || fail "TMPDIR $t is under HOME $RH: the fixture's HOME is mounted over HOME"
    # $F a mount of its own, so one recursive unmount takes every bind under it before the removal: the uv cache and
    # pnpm store binds are the box's own, never removed through the fixture (--one-file-system stops at any left).
    mkdir -p "$F" && mount --bind "$F" "$F" || fail "bind $F"
    trap 'cd /; umount -R "$RH" 2>/dev/null; umount -R "$F" || umount -R -l "$F"; rm -rf --one-file-system "$t" || echo "user-mise: could not remove $t" >&2' EXIT
    ro() { mount --bind "$1" "$2" && mount -o remount,bind,ro "$2"; }
    for r in "$USER_MISE_RDATA" "$USER_MISE_RCACHE" "$USER_MISE_RCONFIG" "$USER_MISE_RSTATE"; do
      [[ -z "$r" || ! -d "$r" ]] || ro "$r" "$r" || fail "bind the box's $r read-only"
    done
    mkdir -p "$D/installs" "$D/shims" "$F/.config/mise" "$F/.local/bin" "$F/src/octo-feather" "$t/tmp"
    for x in "$USER_MISE_RDATA"/installs/*; do   # the kit's tools; the fixture's own global tools are its fakes
      case "${x##*/}" in python|erlang|rust) continue ;; esac
      mkdir "$D/installs/${x##*/}"; ro "$x" "$D/installs/${x##*/}" || fail "bind $x read-only"
    done
    touch "$F/.local/bin/mise"; ro "$USER_MISE_MISE" "$F/.local/bin/mise" || fail "bind mise"
    mkdir -p "$F/.local/share/uv/python" "$F/.cache/uv" "$F/.local/share/pnpm/store"
    ro "$USER_MISE_UVPY" "$F/.local/share/uv/python" && mount --bind "$USER_MISE_UVCACHE" "$F/.cache/uv" \
      && mount --bind "$(dirname "$USER_MISE_PNPM")" "$F/.local/share/pnpm/store" || fail "bind uv's and pnpm's dirs"
    if [[ -n "${USER_MISE_SLOTS:-}" ]]; then mkdir -p "$F/.local/state/octo-feather/slots"; ro "$USER_MISE_SLOTS" "$F/.local/state/octo-feather/slots" || fail "bind the box's slots"; fi
    if [[ -d "$USER_MISE_VC" ]]; then mkdir -p "$F/.cache/octo-feather/skillfile"; ro "$USER_MISE_VC" "$F/.cache/octo-feather/skillfile"; fi
    # The box's pi, read-only where it sits under HOME: the command on PATH, what it resolves to, Pi's install dir.
    for p in "$USER_MISE_PI" "$(realpath -m -- "${USER_MISE_PI:-/}")" "$RH/.local/pi"; do
      [[ -e "$p" && "$p/" == "$RH/"* && ! -e "$F/${p#"$RH"/}" ]] || continue
      if [[ -d "$p" ]]; then mkdir -p "$F/${p#"$RH"/}"; else mkdir -p "$(dirname "$F/${p#"$RH"/}")"; touch "$F/${p#"$RH"/}"; fi
      ro "$p" "$F/${p#"$RH"/}" || fail "bind $p read-only"
    done
    # The kit under the user's HOME: a clone of this checkout (its history, as a user's checkout has), with this
    # checkout's files over it (uncommitted ones too), committed in stage 2.
    git clone -q --no-hardlinks "$kit" "$F/src/octo-feather" || fail "clone the kit"
    (cd "$kit" && git ls-files -z --cached --others --exclude-standard | while IFS= read -r -d '' f; do [[ -e "$f" || -L "$f" ]] && printf '%s\0' "$f"; done \
      | tar --null -T - -cf -) | tar -xf - -C "$F/src/octo-feather" || fail "copy the kit"
    # The clone's own JavaScript packages (gitignored, so not copied), offline from the box's pnpm store (named: on another disk pnpm picks its own): srt, the qc sandbox, runs from them.
    pnpm install --offline --frozen-lockfile --silent --store-dir "$USER_MISE_PNPM" --dir "$F/src/octo-feather" || fail "pnpm install --offline --frozen-lockfile in the kit clone"
    cd / && mount --rbind "$F" "$RH" || fail "mount the user's HOME over $RH"
    set +e; USER_MISE_STAGE=2 USER_MISE_T="$t" unshare -U --map-user="$USER_MISE_UID" --map-group="$USER_MISE_GID" "$RH/src/octo-feather/tests/${0##*/}" "$@"; rc=$?; set -e
    exit "$rc" ;;
esac

# Stage 2, the caller's uid: the user's environment and test doubles here; the user's files and the assertions in
# tests/fixtures/user-mise/check.py, run with the gate's Python (uv's, bound into the fixture HOME).
t="$USER_MISE_T"; H="$USER_MISE_HOME"; K="$H/src/octo-feather"
UP="$H/.local/share/mise/shims:$H/.local/bin:/usr/local/bin:/usr/bin:/bin"
USER_MISE_GATE_PY="$H/.local/share/uv/python/${USER_MISE_PY#"$USER_MISE_UVPY"/}"; export USER_MISE_GATE_PY
# $t/user CMD...: CMD with the user's environment only, by default in a pane of the named Herdr session (the
# assertions always; --gate with USER_MISE_HERDR=none: outside Herdr, no HERDR_* variable).
pane=(HERDR_ENV=1 HERDR_SESSION=fixture HERDR_PANE_ID=wF:p1 HERDR_TAB_ID=wF:t1 HERDR_WORKSPACE_ID=wF HERDR_SOCKET_PATH="$H/.config/herdr/sessions/fixture/herdr.sock")
mode="in a pane of the named Herdr session fixture"
if [[ "${1:-}" == --gate ]]; then
  case "${USER_MISE_HERDR:-fixture}" in
    fixture) ;;
    none) mode="outside Herdr"; pane=() ;;
    *) fail "USER_MISE_HERDR must be fixture (a named session's pane, the default) or none (outside Herdr), got '$USER_MISE_HERDR'" ;;
  esac
fi
{ echo '#!/usr/bin/env bash'
  printf 'exec env -i HOME=%q USER=%q LOGNAME=%q LANG=%q TERM=dumb PATH=%q TMPDIR=%q' "$H" "$USER_MISE_NAME" "$USER_MISE_NAME" "${LANG:-C.UTF-8}" "$UP" "$t/tmp"
  ((${#pane[@]} == 0)) || printf ' %q' "${pane[@]}"
  echo ' USER_MISE_FIXTURE=1 "$@"'; } >"$t/user"
chmod +x "$t/user"
"$USER_MISE_GATE_PY" "$K/tests/fixtures/user-mise/check.py" setup || exit 1

if [[ "${1:-}" == --gate ]]; then shift   # #493 AC1: the gate, or chosen items, as this user, in a pane or outside Herdr
  echo "user-mise: gate in the fixture HOME $H (kit copy $K), $mode (${#pane[@]} HERDR_* variables), GATE_WORKERS=${GATE_WORKERS:-1}: just check-tests $*" >&2
  cd "$K" && exec "$t/user" env GATE_WORKERS="${GATE_WORKERS:-1}" just check-tests "$@"
fi

# Test doubles for the qc runs (check.py's sandbox()): the stub judge ($t/judge/pi) first runs, as tests/lib/qc.sh's
# misemissing judge, a tool not installed through its mise shim (a link to mise named just, in a dir pinning just
# 0.0.1): it must fail, try no install and write nothing to mise's data or cache dir (one PROBE line); then the kit's
# stub judge (tests/fixtures/qc-judge/pi) reports on the brief's criterion. A fake herdr; and mise whose doctor prints
# no JSON ($t/nojson) or JSON without dirs ($t/nodirs), the rest the real mise.
mkdir -p "$t/fake" "$t/judge" "$t/nojson" "$t/nodirs"
cat >"$t/judge/pi" <<'EOF'
#!/usr/bin/env bash
[[ "${1:-}" == --version ]] && exit 0
d="$(mktemp -d)"; mkdir "$d/shim"; ln -s "$(command -v mise)" "$d/shim/just"; printf '[tools]\njust = "0.0.1"\n' > "$d/mise.toml"
ls0="$(find "$MISE_DATA_DIR" "$MISE_CACHE_DIR" 2>/dev/null | sort | md5sum)"
o="$(cd "$d" && "$d/shim/just" --version 2>&1)"; rc=$?
if [[ "$rc" == 0 ]]; then echo "PROBE ESCAPE the shim of a tool not installed ran: $o"
elif grep -qiE 'installing|failed to install' <<< "$o"; then echo "PROBE ESCAPE mise tried to install: $o"
elif [[ "$(find "$MISE_DATA_DIR" "$MISE_CACHE_DIR" 2>/dev/null | sort | md5sum)" != "$ls0" ]]; then echo "PROBE ESCAPE mise wrote to its data or cache dir"
else echo "PROBE ok shim of a tool not installed: exit $rc, no install, nothing written"; fi
exec @KIT@/tests/fixtures/qc-judge/pi "$@"
EOF
sed -i "s#@KIT@#$K#" "$t/judge/pi"
cat >"$t/fake/herdr" <<'EOF'
#!/usr/bin/env bash
C="${XDG_CONFIG_HOME:-$HOME/.config}/herdr"; s=default; a=()
while (($#)); do case "$1" in --session) s="$2"; shift 2;; --remote|--machine) shift 2;; *) a+=("$1"); shift;; esac; done
[[ "$s" == default ]] && sock="$C/herdr.sock" || sock="$C/sessions/$s/herdr.sock"
case "${a[*]}" in
  server) mkdir -p "${sock%/*}"; echo "$s" > "$sock"; exec sleep 600;;
  "session stop "*) rm -f "$C/sessions/${a[2]}/herdr.sock"; exit 0;;
  "session delete "*) rm -rf "${C:?}/sessions/${a[2]}"; exit 0;;
  "pane list") exit 0;;
esac
[[ -f "$sock" ]] || { echo server_not_running >&2; exit 1; }
echo "{\"session\":\"$(cat "$sock")\"}"
EOF
printf '#!/bin/sh\n[ "$1" = doctor ] && exit 1\nexec %q "$@"\n' "$H/.local/bin/mise" >"$t/nojson/mise"
printf '#!/bin/sh\n[ "$1" = doctor ] && { echo "{\\"errors\\": []}"; exit 1; }\nexec %q "$@"\n' "$H/.local/bin/mise" >"$t/nodirs/mise"
chmod +x "$t/judge/pi" "$t/fake/herdr" "$t/nojson/mise" "$t/nodirs/mise"
exec "$USER_MISE_GATE_PY" "$K/tests/fixtures/user-mise/check.py" assert "$USER_MISE_SECTION"
