#!/usr/bin/env bash
# check-loop.sh N LIMIT_S OUTDIR: run `just check` N times, each in its own session with a LIMIT_S deadline;
# on expiry dump the session's processes (loop.sh's dump), then kill it.
set -uo pipefail
n="$1"; lim="$2"; od="$3"; mkdir -p "$od"
kit="$(cd "$(dirname "$0")/../.." && pwd -P)"
eval "$(sed -n '/^dump() {/,/^}/p' "$(dirname "$0")/loop.sh")"
pass=0
for i in $(seq 1 "$n"); do
  t0=$SECONDS
  (cd "$kit" && exec setsid just check) > "$od/check-$i.log" 2>&1 & p=$!
  while kill -0 "$p" 2>/dev/null && (( SECONDS - t0 < lim )); do sleep 5; done
  if kill -0 "$p" 2>/dev/null; then
    echo "check $i: HUNG after $((SECONDS - t0)) s, dumping" | tee -a "$od/loop.txt"
    dump "$p" "$od/hang-$i"; kill -9 -- "-$p" 2>/dev/null; wait "$p" 2>/dev/null
  else
    wait "$p"; rc=$?; echo "check $i: exit $rc in $((SECONDS - t0)) s" | tee -a "$od/loop.txt"
    [[ $rc == 0 ]] && pass=$((pass + 1))
  fi
done
echo "check-loop: $pass/$n green" | tee -a "$od/loop.txt"
