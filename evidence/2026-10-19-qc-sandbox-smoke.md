# QC sandbox with GitHub evidence: smoke (docs/adr/0022, #34), 2026-10-19

Smoke for the #34 behaviour change (ADR 0008, until `just qa` exists): the sandboxed `just qc` judge reads GitHub through a per-run read-only snapshot and the offline `gh`. Real judge: `openai/gpt-6.1-sol` through `pi-role agents/code-reviewer.md -p`, no model override, in the sandbox.

This run supersedes the earlier 4be9bde run (before #33 rounds 4-7: worktree overlay on a hidden run tmpfs, per-run discarded auth.json/models.json copies, worktree cred scan dropped, OAuth warning).

Target: `/tmp/gh32-smoke`, a scratch clone of this kit at gh32 550372c (the lane's final code) with `origin` set to `https://github.com/0xTomDaniel/octo-feather.git` (kit on kit: the kit is the judged worktree). A throwaway `docs/specs/qc-smoke.spec.html` with two criteria (0f491c9) and its status file from `octo-feather-spec-status init` (both planned), committed as 298aa9b:
- `acceptance-gh-evidence`: issue #32 is open with the title "just qc runs its judge in an isolated sandbox with read-only GitHub evidence", and PR #35 is a draft (needs GitHub evidence).
- `acceptance-status-check`: `scripts/octo-feather-spec-status check docs/specs` exits 0 and prints a line starting "spec-status: ok" (CLI demo path).

Kit-on-kit note: an earlier first run (head 9894cc8) aborted before the judge (exit 66) on `FAIL HOME, /var/tmp and the kit read-only`, since the #33 proof assumed the kit is never the judged worktree; fixed in 4be9bde (the proof names the kit-on-kit case; `tests/qc-gh.sh` covers it).

```
$ just qc docs/specs/qc-smoke.status.json 35 acceptance-gh-evidence acceptance-status-check
qc: github: snapshot of 0xTomDaniel/octo-feather at 2026-10-19T23:03:18Z (12.7 s): issues 23, prs 14, runs 59, branches 5, full views 37
qc sandbox: ok   /tmp is private (nothing the judge writes there outlives the run)
qc sandbox: ok   judge holds no capabilities (CapEff 0000000000000000), no_new_privs 1, uid 1000
qc sandbox: ok   masks locked: umount of the Herdr mask exits 32, after its own unshare -rm 32
qc sandbox: ok   HOME, /var/tmp read-only; the kit is the judged worktree (on the overlay: writes discarded, a tracked change fails the run)
qc sandbox: ok   worktree /tmp/gh32-smoke is an overlay, upper dir on the run tmpfs and hidden from the judge
qc sandbox: ok   writable persistent paths: none
qc sandbox: ok   live Herdr unreachable: raw herdr --session default workspace list exits 1
qc sandbox: ok   herdr shim pins sandbox session qc-298aa9bebaaa-ff6508 despite --session default --remote --machine
qc sandbox: ok   Herdr config shows only the sandbox session: [qc-298aa9bebaaa-ff6508]
qc sandbox: ok   no gh or git creds: tokens 0, gh config entries 0, git-credentials 0 bytes, gh auth status exits 1
qc sandbox: ok   parent route unset: 0 of OCTO_FEATHER_PARENT/SESSION_ID/ROLE, HERDR_PANE/TAB/WORKSPACE_ID, HERDR_ENV set
qc sandbox: ok   state dir is per-run scratch: /tmp/.qc-qc-298aa9bebaaa-ff6508/state/octo-feather/sessions/qc-298aa9bebaaa-ff6508
qc sandbox: ok   history read-only (2 of 2 bound: archive 18 files, director log 107 lines); live records masked (6 paths, 0 bytes or entries visible)
qc sandbox: ok   extra binds read-only
qc sandbox: ok   github: snapshot of 0xTomDaniel/octo-feather at 2026-10-19T23:03:18Z (12.7 s): issues 23, prs 14, runs 59, branches 5, full views 37; read-only, served by the offline gh (/tmp/gh32-smoke/scripts/qc-bin/gh), which refuses writes
qc sandbox: ok   worktree clean at 298aa9bebaaa
qc sandbox: cleanup: agents started 0 (headless pi 0, Herdr panes 0); leftover processes killed 0, left 0 (the kernel kills those as PID 1 exits); session qc-298aa9bebaaa-ff6508 stopped and deleted; offline gh refusals 0
qc: worktree overlay: 0 judge writes discarded with the run, 0 outside ignored paths
PASS acceptance-gh-evidence: $ gh issue view 32 --repo 0xTomDaniel/octo-feather --json number,state,title && gh pr view 35 --repo 0xTomDaniel/octo-feather --json number,isDraft
  history only: the read-only GitHub snapshot shows issue #32 open with the exact required title and PR #35 marked draft.
PASS acceptance-status-check: $ scripts/octo-feather-spec-status check docs/specs
  Ran in this worktree; exited 0 and printed a line starting "spec-status: ok".
qc: 2/2 passed at 298aa9bebaaa; offline gh refusals 0; head now ab82bd02cbe8; report ~/.local/state/octo-feather/qc/298aa9bebaaad0dc1dda10f287196f679d658df2-20261019T230318Z-ff6508.json
```

Result:
- Pre-run proof: every check ok, including `writable persistent paths: none` and the overlay line (worktree on an overlay, upper dir on the run tmpfs, hidden from the judge). The github line names the repo, snapshot time and counts (issues 23, PRs 14, runs 59, branches 5, 37 full views, nothing capped), fetched outside in 12.7 s. No OAuth warning line: the box auth.json holds no OAuth entry.
- Verdicts: both PASS. The judge read #32 and #35 through the offline gh (`{"number":32,"state":"OPEN","title":"just qc runs its judge in an isolated sandbox with read-only GitHub evidence"}`, `{"number":35,"isDraft":true}`) and marked that verdict `history only:`; it ran the status check itself (`spec-status: ok (8 status files)`).
- Post-run cleanup line: agents started 0, leftovers killed 0, left 0, session stopped and deleted, offline gh refusals 0. Overlay: 0 judge writes discarded, 0 outside ignored paths. Report `gh_misses` 0, `discarded_writes` 0.
- One commit, `ab82bd0 qc: built acceptance-gh-evidence acceptance-status-check (judged 298aa9bebaaa)`, touching only the status file. The snapshot scratch was gone afterwards (`/tmp/qc-ghsnap-*` absent).
- Report: `~/.local/state/octo-feather/qc/298aa9bebaaad0dc1dda10f287196f679d658df2-20261019T230318Z-ff6508.json`. Judge run 28 s.

Refusals (writes, misses), the no-remote skip, fetch failure (exit 67), `--no-github` and PR 0 are covered without network by `tests/qc-gh.sh` in `just check`.
