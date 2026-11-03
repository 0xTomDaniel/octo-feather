#!/usr/bin/env bash
# Regression fixture for #493 (the kit installs and passes its gate under the installing user's existing mise setup,
# never editing that setup: ADR 0005): a throwaway user HOME prepared as #493's "Regression fixture" says, in its own
# user+mount+network namespace (unshare -rmn: offline, as tests/qc.sh), then #493's assertions (1)-(5) run in it.
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
# Assertions, per #493's fixture: (1) the qc sandbox proof passes (octo-feather-qc with a stub judge, no model,
# HOME moved as the gate's tests move it) and the install-check gate item passes (`just test -k install-check` in the
# kit copy); (2) the negatives still exit 66: doctor printing no JSON, JSON without dirs, an uninstalled pinned tool
# (naming mise install), and a shim of an uninstalled tool installs and writes nothing; (3) no SHADOWED line for a
# global-only tool in `just install-check`; (4) the shared install command exits 0; (5) the user's mise config,
# installs and shims byte-identical before and after, doctor's answer under the user's HOME unchanged; the entries of
# the user's mise state dir counted around the gate item and reported.
# A symptom a fix ticket has not landed yet is a strict expected fail: it must still fail with its #493 symptom, so the
# fix makes it red and that ticket turns it into a pass. Each carries one greppable marker, the ticket that flips it
# after the word EXPECTED, a dash and FAIL (grep -rn for it in tests/ lists them all); the lane's last head has none.
# `tests/user-mise.sh --gate [pytest args]` (just check-user-mise, #493 AC1): the whole gate, or the items pytest args
# choose, run inside the same fixture instead of the assertions. Run by `just check`; Linux only (unshare).
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
    USER_MISE_MISE="$(realpath "$(command -v mise)")"; USER_MISE_UVPY="$(uv python dir)"; USER_MISE_UVCACHE="$(uv cache dir)"
    USER_MISE_PY="$(cd "$kit" && uv python find --system)"; USER_MISE_PNPM="$(cd "$kit" && pnpm store path)"
    USER_MISE_VC="${XDG_CACHE_HOME:-$HOME/.cache}/octo-feather/skillfile"
    USER_MISE_UID="$(id -u)"; USER_MISE_GID="$(id -g)"; USER_MISE_NAME="$(id -un)"; USER_MISE_HOME="$(cd "$HOME" && pwd -P)";
    export USER_MISE_HOME USER_MISE_RDATA USER_MISE_RCACHE USER_MISE_RCONFIG USER_MISE_RSTATE USER_MISE_MISE USER_MISE_UVPY USER_MISE_UVCACHE USER_MISE_PY \
      USER_MISE_PNPM USER_MISE_VC USER_MISE_UID USER_MISE_GID USER_MISE_NAME
    unshare -rmn true 2>/dev/null || fail "unshare -rmn failed: the fixture runs in a user+mount+network namespace (enable unprivileged user namespaces)"
    set +e; USER_MISE_STAGE=1 timeout -k 10 "${USER_MISE_TIMEOUT:-1200}" unshare -rmn "$0" "$@"; rc=$?; set -e
    [[ "$rc" != 124 && "$rc" != 137 ]] || echo "user-mise: timed out after ${USER_MISE_TIMEOUT:-1200} s (USER_MISE_TIMEOUT), killed" >&2
    exit "$rc" ;;
1)  # Root of the namespace: the user's HOME built in $t/home, mounted over the caller's HOME, then the rest as the
    # caller's uid (a nested user namespace mapping it back).
    t="$(mktemp -d)"; t="$(cd "$t" && pwd -P)"; F="$t/home"; D="$F/.local/share/mise"; RH="$USER_MISE_HOME"
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
    if [[ -d "$USER_MISE_VC" ]]; then mkdir -p "$F/.cache/octo-feather/skillfile"; ro "$USER_MISE_VC" "$F/.cache/octo-feather/skillfile"; fi
    # The kit under the user's HOME: this checkout's files (uncommitted ones too), committed in a fresh repo (stage 2).
    (cd "$kit" && git ls-files -z --cached --others --exclude-standard | while IFS= read -r -d '' f; do [[ -e "$f" || -L "$f" ]] && printf '%s\0' "$f"; done \
      | tar --null -T - -cf -) | tar -xf - -C "$F/src/octo-feather" || fail "copy the kit"
    cd / && mount --rbind "$F" "$RH" || fail "mount the user's HOME over $RH"
    set +e; USER_MISE_STAGE=2 USER_MISE_T="$t" unshare -U --map-user="$USER_MISE_UID" --map-group="$USER_MISE_GID" "$RH/src/octo-feather/tests/user-mise.sh" "$@"; rc=$?; set -e
    exit "$rc" ;;
esac

# Stage 2, the caller's uid: the user's files, then the assertions.
t="$USER_MISE_T"; H="$USER_MISE_HOME"; D="$H/.local/share/mise"; K="$H/src/octo-feather"
UP="$D/shims:$H/.local/bin:/usr/local/bin:/usr/bin:/bin"
# user CMD...: CMD with the user's environment only, in a pane of the named Herdr session.
user() { env -i HOME="$H" USER="$USER_MISE_NAME" LOGNAME="$USER_MISE_NAME" LANG="${LANG:-C.UTF-8}" TERM=dumb PATH="$UP" TMPDIR="$t/tmp" \
  HERDR_ENV=1 HERDR_SESSION=fixture HERDR_PANE_ID=wF:p1 HERDR_TAB_ID=wF:t1 HERDR_WORKSPACE_ID=wF HERDR_SOCKET_PATH="$H/.config/herdr/sessions/fixture/herdr.sock" \
  USER_MISE_FIXTURE=1 "$@"; }
pin="$(tr -d '[:space:]' <"$K/.python-version")"; minor="${pin#3.}"; minor="${minor%%.*}"
pyv="3.$(( minor == 11 ? 13 : 11 )).9"
mkdir -p "$D/installs/python/$pyv/bin" "$D/installs/erlang/27.3/bin" "$D/installs/rust/1.80.0" "$H/.cargo/bin" "$H/.rustup"
printf '#!/bin/sh\nexec %q "$@"\n' "$H/.local/share/uv/python/${USER_MISE_PY#"$USER_MISE_UVPY"/}" >"$D/installs/python/$pyv/bin/python3"; ln -s python3 "$D/installs/python/$pyv/bin/python"
printf '#!/bin/sh\necho erl\n' >"$D/installs/erlang/27.3/bin/erl"; touch "$D/installs/rust/1.80.0/.installed"
for x in cargo some-cli; do printf '#!/bin/sh\necho %s\n' "$x" >"$H/.cargo/bin/$x"; done
chmod +x "$D/installs/python/$pyv/bin/python3" "$D/installs/erlang/27.3/bin/erl" "$H/.cargo/bin/"*
# The version links mise keeps beside an install (it adds them on its first run after one: the user's are in place).
for v in "python/$pyv" erlang/27.3 rust/1.80.0; do
  x="${v#*/}"; for l in "${x%.*}" "${x%%.*}" latest; do [[ -e "$D/installs/${v%/*}/$l" ]] || ln -s "./$x" "$D/installs/${v%/*}/$l"; done
done
printf '[tools]\npython = "%s"\nerlang = "27.3"\nrust = "1.80.0"\n' "$pyv" >"$H/.config/mise/config.toml"
g() { git -c user.name=t -c user.email=t@t -c init.defaultBranch=main "$@"; }
g -C "$K" init -q; g -C "$K" add -A; g -C "$K" commit -q -m kit
(cd "$t" && user mise reshim) || fail "mise reshim in the user's HOME"

if [[ "${1:-}" == --gate ]]; then shift   # #493 AC1: the gate, or chosen items, as this user in a named session's pane
  echo "user-mise: gate in the fixture HOME $H (kit copy $K, HERDR_SESSION=fixture): just check-tests $*" >&2
  cd "$K"; set +e; user env GATE_WORKERS=1 just check-tests "$@"; exit $?
fi

# Each assertion below is a condition, then want or staged reading its $?: errexit off, the assertions all run.
set +e; bad=0
ok() { echo "user-mise: ok   $*"; }
no() { echo "user-mise: FAIL $1" >&2; [[ -z "${2:-}" ]] || printf '%s\n' "$2" | tail -40 | sed 's/^/    /' >&2; bad=1; }
# staged MARKER WHAT SYMPTOM RC OUT: a strict expected fail: RC nonzero and OUT holding SYMPTOM (an ERE); a pass, or
# another failure, fails this test naming the marker the fix ticket removes.
staged() {
  if [[ "$4" != 0 ]] && grep -qE -- "$3" <<<"$5"; then echo "user-mise: expected fail ($1, still failing with its #493 symptom) $2"
  elif [[ "$4" == 0 ]]; then no "$2 now passes: the ticket of $1 turns it into a pass and removes the marker" "$5"
  else no "$2 fails, but not with its #493 symptom /$3/ ($1)" "$5"; fi; }
# want WHAT RC OUT: a pass.
want() { if [[ "$2" == 0 ]]; then ok "$1"; else no "$1" "$3"; fi; }
# A dir's own mtime is left out: mise's reshim on every install bumps the shims dir's with every shim unchanged.
snap() { find "$H/.config/mise" "$D/installs" "$D/shims" "$H/.cargo" \( -type d -printf '%p %y %s %m %l\n' \) -o -printf '%p %y %s %m %T@ %l\n' | sort
  find "$H/.config/mise" "$D/shims" "$D/installs/python" "$D/installs/erlang" "$D/installs/rust" "$H/.cargo" -type f -exec sha256sum {} + | sort; }
doc() { (cd "$t" && user env "$@" mise doctor --json 2>/dev/null); }

# Preconditions.
b="$(find "$D/installs" -mindepth 1 -maxdepth 1 ! -name python ! -name erlang ! -name rust -printf '%f\n' | sort | head -1)"
rc=0; out="$(user touch "$D/installs/$b/.user-mise-write" 2>&1)" || rc=$?
[[ "$rc" != 0 ]] && grep -q 'Read-only file system' <<<"$out"; want "a write into the box's bound kit tool installs fails (read-only)" $? "$out"
rc=0; d0="$(doc)" || rc=$?
[[ "$rc" == 0 ]]; want "mise doctor --json under the user's HOME exits 0" $? "$d0"
mkdir -p "$t/moved"; rc=0; dm="$(doc HOME="$t/moved" MISE_DATA_DIR="$D" MISE_CACHE_DIR="$H/.cache/mise" MISE_CONFIG_DIR="$H/.config/mise")" || rc=$?
[[ "$rc" == 1 && "$(jq -r '[.dirs.data, .dirs.cache, .dirs.config] | join(" ")' <<<"$dm")" == "$D $H/.cache/mise $H/.config/mise" ]]
want "mise doctor --json under a moved HOME exits 1 (stale shims: $(jq -r '.errors[0] // "none"' <<<"$dm" | tr '\n' ' ')) and still prints dirs" $? "rc $rc: $dm"
rc=0; out="$(cd "$K" && user sh -c 'command -v python3; mise which python3; mise ls --json python' 2>&1)" || rc=$?
[[ "$rc" == 0 && "$(sed -n 1p <<<"$out")" == "$D/shims/python3" && "$(sed -n 2p <<<"$out")" == "$D/installs/python/$pyv/bin/python3" ]]
want "python3 first on PATH is mise's shim of the global python $pyv (.python-version: $pin)" $? "$out"
! grep -qE '^\[\[tools\.(erlang|python|rust)\]\]' "$K/mise.lock" && (cd "$K" && user mise ls --installed erlang 2>&1 | grep -q 27.3)
want "the global tools are installed and absent from the kit's mise.lock" $? "$(cd "$K" && user mise ls 2>&1)"
s0="$(snap)"

# (1), (2): the qc sandbox proof, HOME moved as the gate's tests move it (tests/qc.sh), mise's dirs pinned as they set
# them, a stub judge ($t/judge/pi) and a fake herdr first on the sandbox's PATH; no model, no network. The judge first
# runs, as tests/qc.sh's misemissing judge, a tool not installed through its mise shim (a link to mise named just, in a
# dir pinning just 0.0.1): it must fail, try no install and write nothing to mise's data or cache dir (one PROBE line);
# then the kit's stub judge (tests/fixtures/qc-judge/pi) reports on the brief's criterion.
mkdir -p "$t/fake" "$t/judge" "$t/reports" "$t/qchome"
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
sed -i "s#@KIT@#$K#" "$t/judge/pi"; chmod +x "$t/judge/pi"
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
chmod +x "$t/fake/herdr"
target() { # DIR [MISE_TOML]: a scratch target repo under the user's HOME with the demo spec's status file
  mkdir -p "$1/docs/specs"; cp "$K/tests/fixtures/spec-status/good/demo.spec.html" "$1/docs/specs/"
  (cd "$1" && g init -q . && g add -A && g commit -qm accepted && user env PATH="$K/scripts:$UP" octo-feather-spec-status init docs/specs/demo.spec.html "$(git rev-parse --short HEAD)" >/dev/null \
    && { [[ -z "${2:-}" ]] || printf '%s' "$2" >mise.toml; } && echo scratch/ >.gitignore && g add -A && g commit -qm spec); }
target "$H/src/target"; target "$H/src/pinned" $'[tools]\njust = "0.0.1"\n'
pinned=(MISE_DATA_DIR="$D" MISE_CACHE_DIR="$H/.cache/mise" MISE_CONFIG_DIR="$H/.config/mise")
qc() { # DIR PATH_FIRST ENV...: octo-feather-qc on the target in DIR; exit in $rc, stdout and stderr in $out
  local dir="$1" first="$2"; shift 2; rc=0
  out="$(cd "$dir" && user env HOME="$t/qchome" PATH="$first$t/fake:$K/scripts:$UP" OCTO_FEATHER_QC_PATH="$t/judge" OCTO_FEATHER_QC_DIR="$t/reports" \
    GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t "$@" timeout -k 5 180 octo-feather-qc docs/specs/demo.status.json 5 acceptance-a --no-github 2>&1)" || rc=$?; }
qc "$H/src/target" "" "${pinned[@]}"
# The proof's mise line names the tools it judged per dir: the kit's own, never the global ones the parent walk finds (#493 AC3).
ml="$(grep '^qc sandbox: ok   mise offline' <<<"$out")"
[[ "$rc" == 0 && -n "$ml" && "$ml" == *"$K: "*node@* ]] && ! grep -qE '(erlang|python|rust)@' <<<"$ml"
want "(1) the qc sandbox proof passes with doctor exiting 1 under the moved HOME, judging only the kit's and worktree's own tools (no global erlang, python, rust), the stub judge runs (exit $rc)" $? "$out"
# mise's config dir not pinned: the moved HOME's parent walk from the kit finds the user's global config as a local one.
qc "$H/src/target" "" MISE_DATA_DIR="$D" MISE_CACHE_DIR="$H/.cache/mise"
ml="$(grep '^qc sandbox: ok   mise offline' <<<"$out")"
[[ "$rc" == 0 && -n "$ml" && "$ml" == *"$K: "*node@* ]] && ! grep -qE '(erlang|python|rust)@' <<<"$ml"
want "(1) the same, mise's config dir not pinned (the parent walk finds the global config): still no global tool judged (exit $rc)" $? "$out"
judge="$(python3 -c 'import json, sys, glob, os; f = max(glob.glob(sys.argv[1] + "/*.json"), key=os.path.getmtime); print(json.load(open(f))["fallback"]["acceptance-a"].get("stdout", "no judge stdout"))' "$t/reports" 2>&1)" || judge="no report"
grep -q '^PROBE ok ' <<<"$judge"; want "(2) a shim of a tool not installed, in the sandbox: fails, installs and writes nothing" $? "$judge"$'\n'"$out"
mkdir -p "$t/nojson" "$t/nodirs"
printf '#!/bin/sh\n[ "$1" = doctor ] && exit 1\nexec %q "$@"\n' "$H/.local/bin/mise" >"$t/nojson/mise"
printf '#!/bin/sh\n[ "$1" = doctor ] && { echo "{\\"errors\\": []}"; exit 1; }\nexec %q "$@"\n' "$H/.local/bin/mise" >"$t/nodirs/mise"; chmod +x "$t/nojson/mise" "$t/nodirs/mise"
qc "$H/src/target" "$t/nojson:" "${pinned[@]}"
[[ "$rc" == 66 ]] && grep -q 'qc sandbox: FAIL .*mise doctor' <<<"$out"; want "(2) doctor printing no JSON: exit 66 naming mise doctor (exit $rc)" $? "$out"
qc "$H/src/target" "$t/nodirs:" "${pinned[@]}"
[[ "$rc" == 66 ]] && grep -q 'qc sandbox: FAIL .*mise doctor' <<<"$out"; want "(2) doctor JSON without dirs: exit 66 naming mise doctor (exit $rc)" $? "$out"
qc "$H/src/pinned" "" "${pinned[@]}"
[[ "$rc" == 66 ]] && grep -qF "run outside it: octo-feather-mise-install $H/src/pinned)" <<<"$out" \
  && grep -qE 'qc sandbox: FAIL mise .*NOT installed: .*just@0\.0\.1' <<<"$out"
want "(2) a pinned tool not installed: exit 66 naming it and mise install (exit $rc)" $? "$out"

# (1), (3): the install-check gate item in the kit copy, from the named session's pane; the user's mise state dir
# entries counted around it (#493 AC7).
n0="$(find "$H/.local/state/mise" -mindepth 2 -maxdepth 2 2>/dev/null | wc -l)"
rc=0; out="$(cd "$K" && user env GATE_WORKERS=1 just test -k install-check 2>&1)" || rc=$?
n1="$(find "$H/.local/state/mise" -mindepth 2 -maxdepth 2 2>/dev/null | wc -l)"
want "(1) HERDR_SESSION=fixture just test -k install-check passes in the kit under the user's HOME (exit $rc)" "$rc" "$out"
echo "user-mise: the fixture user's mise state dir ($H/.local/state/mise, inside the fixture HOME mounted over $H) entries: $n0 before the install-check item, $n1 after"
[[ "$n1" == "$n0" ]]; staged 'EXPECTED-FAIL #498' "(5) the install-check item leaves the user's mise state dir entries as they were ($n0, then $n1)" \
  'grew' $? "$( ((n1 > n0)) && echo grew || echo shrank)"
(cd "$t" && user python3 -m venv "$t/venv") || fail "python3 -m venv through the user's python3"
rc=0; out="$(cd "$K" && user env PATH="$t/venv/bin:$UP" just install-check 2>&1)" || rc=$?
globals="$(find "$D/installs/python/$pyv/bin" "$D/installs/erlang/27.3/bin" "$H/.cargo/bin" -mindepth 1 -printf '%f\n' | sort -u | paste -sd '|')"
! grep -qE "^path   ($globals|pip[0-9.]*) SHADOWED" <<<"$out"
want "(3) just install-check, a venv first on the pane PATH: no SHADOWED line for a global-only tool" $? "$out"

# (4) the shared install command (README, install-check's fix lines) in the kit.
# README's install step, the command as it stands there (install-check's fix lines print the same: tests/install-check.sh).
cmd="$(grep -m1 '^scripts/octo-feather-mise-install' "$K/README.md" | sed 's/   #.*//')"
rc=0; out="$( [[ -n "$cmd" ]] && cd "$K" && user sh -c "$cmd" 2>&1)" || rc=$?
want "(4) README's install step ($cmd) in the kit exits 0 with the user's global tools installed (exit $rc)" "$rc" "$out"

# (5) the user's mise setup untouched.
[[ "$(snap)" == "$s0" ]]; want "(5) the user's mise config, installs and shims byte-identical before and after" $? "$(diff <(echo "$s0") <(snap) | head -20)"
rc=0; d1="$(doc)" || rc=$?
[[ "$rc" == 0 && "$(jq -c '[.dirs, .errors, .warnings]' <<<"$d1")" == "$(jq -c '[.dirs, .errors, .warnings]' <<<"$d0")" ]]
want "(5) mise doctor under the user's HOME unchanged (exit $rc)" $? "$d1"
[[ "$bad" == 0 ]] || fail "failed (lines above)"
echo "user-mise: ok (fixture HOME: kit installs bound read-only, global tools absent from the kit lock, python3 a mise shim, stale shims; every #493 assertion passes or still fails with its symptom, each marked with its fix ticket)"
