# QC sandbox with GitHub evidence: smoke (docs/adr/0022, #34), 2026-10-19

Smoke for the #34 behaviour change (ADR 0008, until `just qa` exists): the sandboxed `just qc` judge reads GitHub through a per-run read-only snapshot and the offline `gh`. Real judge: `openai/gpt-6.1-sol` through `pi-role agents/code-reviewer.md -p`, no model override, in the sandbox.

Target: `/tmp/gh34-smoke`, a scratch clone of this kit at `implementer-gh34` 4be9bde with `origin` set to `https://github.com/0xTomDaniel/octo-feather.git` (kit on kit: the kit is the judged worktree). A throwaway `docs/specs/qc-smoke.spec.html` with two criteria and its status file from `octo-feather-spec-status init` (both planned), committed as 2f4a59f:
- `acceptance-gh-evidence`: issue #32 is open with the title "just qc runs its judge in an isolated sandbox with read-only GitHub evidence", and PR #35 is a draft (needs GitHub evidence).
- `acceptance-status-check`: `scripts/octo-feather-spec-status check docs/specs` exits 0 and prints a line starting "spec-status: ok" (CLI demo path).

A first run (head 9894cc8, report `.../qc/9894cc89e083...-2fefa3.json`) aborted before the judge (exit 66) on `FAIL HOME, /var/tmp and the kit read-only`: the #33 proof assumed the kit is never the judged worktree. Fixed in 4be9bde (the proof names the kit-on-kit case; `tests/qc-gh.sh` covers it); the run below is the rerun.

```
$ just qc docs/specs/qc-smoke.status.json 35 acceptance-gh-evidence acceptance-status-check
qc: github: snapshot of 0xTomDaniel/octo-feather at 2026-10-19T22:08:01Z (10.8 s): issues 22, prs 13, runs 49, branches 4, full views 35
qc sandbox: ok   /tmp is private (nothing the judge writes there outlives the run)
qc sandbox: ok   judge holds no capabilities (CapEff 0000000000000000), no_new_privs 1, uid 1000
qc sandbox: ok   masks locked: umount of the Herdr mask exits 32, after its own unshare -rm 32
qc sandbox: ok   HOME, /var/tmp read-only; the kit is the judged worktree (writable; any change fails the run)
qc sandbox: ok   live Herdr unreachable: raw herdr --session default workspace list exits 1
qc sandbox: ok   herdr shim pins sandbox session qc-2f4a59f3eccd-a63976 despite --session default --remote --machine
qc sandbox: ok   Herdr config shows only the sandbox session: [qc-2f4a59f3eccd-a63976]
qc sandbox: ok   no gh or git creds: tokens 0, gh config entries 0, git-credentials 0 bytes, gh auth status exits 1
qc sandbox: ok   parent route unset: 0 of OCTO_FEATHER_PARENT/SESSION_ID/ROLE, HERDR_PANE/TAB/WORKSPACE_ID, HERDR_ENV set
qc sandbox: ok   state dir is per-run scratch: /tmp/.qc-qc-2f4a59f3eccd-a63976/state/octo-feather/sessions/qc-2f4a59f3eccd-a63976
qc sandbox: ok   history read-only (2 of 2 bound: archive 18 files, director log 100 lines); live records masked (6 paths, 0 bytes or entries visible)
qc sandbox: ok   extra binds read-only
qc sandbox: ok   github: snapshot of 0xTomDaniel/octo-feather at 2026-10-19T22:08:01Z (10.8 s): issues 22, prs 13, runs 49, branches 4, full views 35; read-only, served by the offline gh (/tmp/gh34-smoke/scripts/qc-bin/gh), which refuses writes
qc sandbox: ok   worktree clean at 2f4a59f3eccd
qc sandbox: cleanup: agents started 0 (headless pi 0, Herdr panes 0); leftover processes killed 0, left 0 (the kernel kills those as PID 1 exits); session qc-2f4a59f3eccd-a63976 stopped and deleted; offline gh refusals 0
qc: worktree scan: 0 Pi credential copies removed
PASS acceptance-gh-evidence: $ gh issue view 32 --repo 0xTomDaniel/octo-feather --json number,title,state && gh pr view 35 --repo 0xTomDaniel/octo-feather --json number,isDraft
  history only: the read-only GitHub snapshot shows issue #32 open with the exact required title and PR #35 draft.
PASS acceptance-status-check: $ scripts/octo-feather-spec-status check docs/specs
  The command exited 0 and printed a line starting "spec-status: ok".
qc: 2/2 passed at 2f4a59f3eccd; offline gh refusals 0; head now 5aab33c9ad6f; report /home/exedev/.local/state/octo-feather/qc/2f4a59f3eccd8b58f0e431f8931ead9f423fc443-20261019T220801Z-a63976.json
```

Result:
- Pre-run proof: the github line names the repo, snapshot time and counts (issues 22, PRs 13, runs 49, branches 4, 35 full views, nothing capped), fetched outside in 10.8 s; every check ok.
- Verdicts: both PASS. The judge read #32 and #35 through the offline gh (`{"number":32,"title":"just qc runs its judge in an isolated sandbox with read-only GitHub evidence","state":"OPEN"}`, `{"number":35,"isDraft":true}`) and marked that verdict `history only:` as the brief asks; it ran the status check itself (`spec-status: ok (8 status files)`).
- Post-run cleanup line: agents started 0, leftovers killed 0, left 0, session stopped and deleted, offline gh refusals 0. Report `gh_misses` 0.
- One commit, `5aab33c qc: built acceptance-gh-evidence acceptance-status-check (judged 2f4a59f3eccd)`, touching only the status file. The snapshot scratch was gone afterwards (`/tmp/qc-ghsnap-*` absent).
- Report: `~/.local/state/octo-feather/qc/2f4a59f3eccd8b58f0e431f8931ead9f423fc443-20261019T220801Z-a63976.json`. Judge run 32 s.

Refusals (writes, misses), the no-remote skip, fetch failure (exit 67), `--no-github` and PR 0 are covered without network by `tests/qc-gh.sh` in `just check`.
