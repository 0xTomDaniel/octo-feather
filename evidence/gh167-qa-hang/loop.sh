#!/usr/bin/env bash
# loop.sh N LIMIT_S OUTDIR [LOAD]: run `bash tests/qa.sh` N times, each in its own session with a LIMIT_S deadline.
# On expiry, dump the session's process tree, wchan, kernel stacks, open fds, cmdlines and `ss -xp` to OUTDIR/hang-<i>/,
# then kill the session. LOAD=1 runs 3 extra qa.sh copies alongside each run (the `just check` load).
set -uo pipefail
n="$1"; lim="$2"; od="$3"; load="${4:-0}"; mkdir -p "$od"
kit="$(cd "$(dirname "$0")/../.." && pwd -P)"
dump() {   # dump SID DIR
  local sid="$1" d="$2"; mkdir -p "$d"
  ps -eo pid,ppid,pgid,sid,stat,etimes,wchan:32,cmd --forest > "$d/ps-all.txt"
  local pids; pids=$(ps -eo pid=,sid= | awk -v s="$sid" '$2 == s {print $1}')
  # processes outside the session that descend from it (setsid'd children) are in ps-all.txt; list by name too
  for p in $pids; do
    { echo "== pid $p"; tr '\0' ' ' < /proc/$p/cmdline; echo; echo "wchan: $(cat /proc/$p/wchan 2>/dev/null)";
      echo "-- stack"; cat /proc/$p/stack 2>/dev/null || echo "(stack unreadable)";
      echo "-- status"; grep -E '^(State|PPid|NSpid|NSsid)' /proc/$p/status 2>/dev/null
      echo "-- fds"; ls -l /proc/$p/fd 2>/dev/null
      for tk in /proc/$p/task/*; do echo "-- task ${tk##*/} wchan $(cat $tk/wchan 2>/dev/null) syscall $(cat $tk/syscall 2>/dev/null | cut -d' ' -f1)"; done
    } >> "$d/procs.txt" 2>&1
    command -v py-spy >/dev/null && grep -q python <<< "$(cat /proc/$p/cmdline 2>/dev/null | tr '\0' ' ')" && py-spy dump --pid "$p" >> "$d/py-spy.txt" 2>&1
  done
  ss -xp > "$d/ss-xp.txt" 2>&1
}
pass=0
for i in $(seq 1 "$n"); do
  lp=()
  if [[ "$load" == 1 ]]; then for k in 1 2 3; do setsid bash "$kit/tests/qa.sh" > "$od/load-$i-$k.log" 2>&1 & lp+=($!); done; fi
  t0=$SECONDS
  setsid bash "$kit/tests/qa.sh" > "$od/run-$i.log" 2>&1 & p=$!
  while kill -0 "$p" 2>/dev/null && (( SECONDS - t0 < lim )); do sleep 2; done
  if kill -0 "$p" 2>/dev/null; then
    echo "run $i: HUNG after $((SECONDS - t0)) s, dumping" | tee -a "$od/loop.txt"
    dump "$p" "$od/hang-$i"
    kill -9 -- "-$p" 2>/dev/null; wait "$p" 2>/dev/null
  else
    wait "$p"; rc=$?
    echo "run $i: exit $rc in $((SECONDS - t0)) s" | tee -a "$od/loop.txt"
    [[ $rc == 0 ]] && pass=$((pass + 1))
  fi
  for q in "${lp[@]}"; do
    while kill -0 "$q" 2>/dev/null && (( SECONDS - t0 < lim )); do sleep 2; done
    if kill -0 "$q" 2>/dev/null; then echo "run $i load pid $q: HUNG, dumping" | tee -a "$od/loop.txt"; dump "$q" "$od/hang-$i-load-$q"; kill -9 -- "-$q" 2>/dev/null; fi
    wait "$q" 2>/dev/null; echo "run $i load pid $q: exit $?" >> "$od/loop.txt"
  done
done
echo "loop: $pass/$n green" | tee -a "$od/loop.txt"
