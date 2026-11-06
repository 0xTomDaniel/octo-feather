#!/usr/bin/env bash
# The fake qc judge's pane step (judge.py, FAKE_QC=pane; as tests/lib/qc.sh's): spawns a pane through the sandbox
# herdr, which reports what it sees and then tries to outlive the run, holding a shared flock on $HOME/pane.lock (read
# only; the scenario made it) for as long as it lives; prints the judge's and the pane's PID namespace and the pane's
# findings. The pane says it is done on the scratch/ready pipe, read blocking under a 10 s cap: no polling.
mkdir -p scratch; rm -f scratch/pane.txt scratch/ready; mkfifo scratch/ready
cat > scratch/pane.sh <<'P'
{ echo "pane pidns $(readlink /proc/self/ns/pid)"
  for h in $(type -ap herdr); do for s in default qclive; do
    "$h" --session "$s" workspace list 2>/dev/null | grep -q '"default"\|QCLIVE' && echo "ESCAPE pane reached Herdr $s via $h"; done; done
  cat "$HOME/.config/herdr/herdr.sock" "$HOME/.config/gh/hosts.yml" "$HOME/.git-credentials" 2>/dev/null | grep -q 'SECRET\|default' \
    && echo "ESCAPE pane creds or live socket"
  env | grep -q SECRET && echo "ESCAPE pane token in env"
  exec 9< "$HOME/pane.lock" && flock -s 9 && echo "PANE locked"
  echo "PANE done"; } > "$1.tmp"; mv "$1.tmp" "$1"
echo done > "$2"
exec sleep 3600
P
id=$(herdr workspace create --cwd "$PWD" --no-focus | grep -o '"pane_id":"[^"]*"' | head -1 | cut -d'"' -f4)
herdr pane run "$id" "bash $PWD/scratch/pane.sh $PWD/scratch/pane.txt $PWD/scratch/ready" > /dev/null
timeout 10 sh -c 'read -r _ < scratch/ready' || echo "MISSING pane ready (pane $id)"
echo "judge pidns $(readlink /proc/self/ns/pid)"; cat scratch/pane.txt 2>/dev/null || echo "MISSING pane output (pane $id)"
