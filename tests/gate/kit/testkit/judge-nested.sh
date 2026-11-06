#!/usr/bin/env bash
# The fake qc judge's nested step (judge.py, FAKE_QC=nested; as tests/lib/qc.sh's): `octo-feather-qc` in a clone of
# the judged worktree (the outer overlay covered there), fresh HOME and state, the judge's PATH as is (`herdr` there
# the outer sandbox's shim) after the fake pi's own dir ($1): a qc sandbox nested in the judge's gets past its proof.
h="$(mktemp -d)"; git clone -q "$PWD" "$h/repo"
o="$(cd "$h/repo" && env -u XDG_STATE_HOME -u HERDR_SESSION -u HERDR_SOCKET_PATH -u HERDR_BIN_PATH HOME="$h" PATH="$1:$PATH" \
  FAKE_QC=garbage octo-feather-qc docs/specs/demo.status.json 5 acceptance-a 2>&1)"; echo "NESTED exit $?"
grep -q 'qc sandbox: ok   writable persistent paths: none$' <<< "$o" && grep -q 'qc sandbox: ok   [1-9][0-9]* writable mounts covered' <<< "$o" \
  || echo "MISSING nested proof: $o"
grep -q 'qc sandbox: ok   live Herdr unreachable: raw herdr --session default workspace list exits 1$' <<< "$o" \
  && grep -q 'qc sandbox: ok   herdr shim pins sandbox session' <<< "$o" && grep -q 'qc sandbox: ok   Herdr config shows only the sandbox session' <<< "$o" \
  || echo "MISSING nested Herdr proof (real binary, not the outer shim): $o"
