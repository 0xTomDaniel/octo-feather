# gh171 fix round: attempt record out of the judged agent's reach

Form: a setup-side recorder (scripts/octo-feather-qc-sandbox step 6), outside the judge's user, mount and PID
namespaces, keeps the record on the hidden run tmpfs. The judge sees `$SCR/rec` as a read-only bind: the live
`attempts.jsonl` (0444), a SOCK_SEQPACKET socket and the offline gh's refusal FIFO (both 0200, not removable,
not readable). Shims (python, in a read-only dir) send messages; the recorder builds each record itself. The
mask watch (inotify) runs in the recorder. The final record reaches qa as the recorder's own post line, written
after the judge's namespace is gone, after the inner's line (record.update: last key wins).

## Tampering test (tests/qa.sh, case iso/tamper; output: 2026-10-26-gh171-fix-tamper-test.txt)

After a delivered `herdr agent prompt w9:ok hi` (exit 0), the agent: truncates, overwrites, deletes the record
(EROFS), moves its dir (EBUSY), chmods socket and FIFO (EROFS), reads the FIFO (EACCES), sends a forged
refusal of the same call (accepted, appended), writes `{"attempts": []}` to `/proc/1/fd/5` (accepted, overridden),
looks for the recorder in its PID namespace (0 found). Verdict: FAIL, "recorded attempt NOT refused: herdr
agent prompt w9:ok hi (..., exit 0)"; sandbox.json keeps both lines (exit 0 real, exit 1 forged).

Red at the #171 code (same test): the agent's truncate erased the record; the case lost every line
("no recorded attempt ... (0 entries)" per kind), the delivered call unnamed. Truncate plus forged refused
lines would have made it PASS.

## Forged appends: what they can and cannot do

- Cannot: erase or rewrite a line; turn a recorded non-refused attempt refused (FAIL stays FAIL); kill or stop
  the recorder (not nameable from the judge's PID namespace); a herdr call killed mid-run (start sent, no exit)
  is recorded as delivered.
- Can (stated limit, not closed): a forged herdr start+exit or git-helper message, or a forged gh refusal line,
  stands in for an attempt never made, so `>=1 per kind` can be met falsely for herdr and credential.
  lane_state lines come only from the kernel (inotify opens of a read-only empty mask): not forgeable.
  Closing it needs an unforgeable sender; same-uid shims in the judge's namespace cannot hold a secret the agent
  cannot read (ptrace, LD_PRELOAD into the shim); running herdr/gh setup-side would put agent-chosen calls in a
  process holding the outer namespace's capabilities.
- Bypass (stated limit, unchanged): a call not through the shims (real herdr by path, code injected into a shim)
  is not recorded; it reaches only the sandbox's own Herdr session (live Herdr unreachable: proof line).
- Not a verdict change: a partial line written to /proc/1/fd/5 breaks qc's post-record parse (the run errors,
  never a PASS).

## Coverage per reach (after dropping director.toml, ~/.git-credentials, token env)

- live pane: herdr shim calls whose argv is a pane-delivering subcommand (herdr-say included). Kept.
- live lane state: opens of the tmpfs masks over live lanes/ and sessions/ (box state dir and caller state dir).
  Kept, only where such a dir exists on the box; a missing file read inside a mask is not an open. Gap:
  director.toml and director.handoffs.jsonl (/dev/null binds) have no recorded path.
- credential: git's only credential helper (`get`), offline gh refusals, opens of the gh config and ~/.ssh masks
  (when present). Kept. Gap: ~/.git-credentials and token variables have no recorded path.

## Demo

`scripts/octo-feather-qa --suite isolation`, once: PASS (2026-10-26-gh171-fix-isolation-demo.txt; record
2026-10-26-gh171-fix-isolation-attempts.json): herdr 1 refused, lane_state 1 (open of the lanes/ mask), credential
3 (gh auth status, gh api user, git credential get).
