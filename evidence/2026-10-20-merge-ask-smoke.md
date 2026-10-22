# Merge ask smoke: `octo-feather-lane verdict` and `merge-ask` (issue #48), 2026-10-20

Smoke for the merge-ask pointers in agents/supervisor.md (self-check), implement-spec step 8 and the github skill (Verdict Mutations), and the new `verdict` and `merge-ask` subcommands of `scripts/octo-feather-lane` (branch implementer-gh48, from gh40; spec issue-lifecycle `#acceptance-merge-ask-evidence`). ADR 0008 second paragraph; the owed eval is listed in docs/owed-evals/48.md. The commands themselves are proven by `tests/lane-merge-ask.sh` in `just check` (fake gh; five mutations of the checks each turn it red).

## (a) Ticket demo, real GitHub, read-only

`scripts/` on PATH, the caller's gh auth.

```
$ octo-feather-lane merge-ask 16 --status docs/specs/overview.status.json
octo-feather-lane merge-ask: PR #16 merge ask incomplete (7 items), head f5f90b85a488:
  - `## Merge ask` section: none in the PR body; add it (format: octo-feather-lane with no arguments)
  - Head: missing; add `Head: f5f90b85a48862dc7b2434b1b04df961449a2bea`
  - Checks: missing; add `Checks: <the head's checks, all passing>`
  - criterion table: missing; add `| criterion | qc verdict | evidence |` with one row per claimed criterion
  - Review verdict: missing; run `octo-feather-lane verdict 16 f5f90b85a488 <report>` and add `Review verdict: <the URL it prints>`
  - Built: missing; add `Built: <ids qc flipped to built>` (or `Built: none`)
  - Failed: missing; add `Failed: none`, or `Failed:` then one `- <id>: <triage>` line per failed criterion
rc=1
```

This lane's PR #49 at head c281ed9 (before its merge ask is written; a multi-spec lane: comms for #46, issue-lifecycle for #48):

```
$ octo-feather-lane merge-ask 49 --status docs/specs/issue-lifecycle.status.json --status docs/specs/comms.status.json
octo-feather-lane merge-ask: PR #49 merge ask incomplete (7 items), head c281ed9c4c47:
  (the same 7 items as PR #16, for head c281ed9c4c47718830af7c146621f22ff50c6e65)
rc=1
```

It passes only once the supervisor writes the final `## Merge ask` section and posts the verdict comment.

## (b) Scratch PR body on PR #49's real data, through the qc judge's offline gh

`gh pr view 49 --json number,body,headRefOid,statusCheckRollup,comments,commits` (real: head c281ed9, check `check` COMPLETED SUCCESS, commits including `qc: built acceptance-lane-archive (judged 241fd3ee875f)`) saved into a snapshot dir laid out as `octo-feather-qc-ghsnap` writes it, with a scratch `## Merge ask` section appended to the body and a scratch verdict comment (marker, `Head: c281ed9...`, `Verdict: clear`) added. Run with `OCTO_FEATHER_GHSNAP=<snap> PATH=scripts/qc-bin:$PATH`, so every read went through the offline gh, never the network.

```
$ octo-feather-lane merge-ask 49 --status docs/specs/issue-lifecycle.status.json --status docs/specs/comms.status.json
## Merge ask

Head: c281ed9c4c47
Checks: check (CI) SUCCESS on c281ed9c4c47
| criterion | qc verdict | evidence |
|---|---|---|
| comms#acceptance-lane-archive | pass | qc report gh40-comms/241fd3ee875f.json, tests/lane-archive.sh |
Review verdict: https://github.com/0xTomDaniel/octo-feather/pull/49#issuecomment-9000000001
Built: comms#acceptance-lane-archive
Failed: none
rc=0
```

The same with the comment's verdict set to blocking:

```
octo-feather-lane merge-ask: PR #49 merge ask incomplete (1 item), head c281ed9c4c47:
  - Review verdict: blocking, not clear; fix the blocking findings, qc and review again
rc=1
```

The clear one again, without `--status docs/specs/comms.status.json`:

```
octo-feather-lane merge-ask: PR #49 merge ask incomplete (4 items), head c281ed9c4c47:
  - criterion row: comms#acceptance-lane-archive: spec comms has no --status file (pass --status docs/specs/comms.status.json)
  - criterion table: no rows; add one per claimed criterion
  - Built: comms#acceptance-lane-archive: spec comms has no --status file (pass --status docs/specs/comms.status.json)
  - Built: lists none, the PR's `qc: built` commits passed acceptance-lane-archive; list exactly those, or run just qc again on the claimed criteria (acceptance-lane-archive in no --status file: pass --status for its spec)
rc=1
```

### (b2) Judged column, after review of 39515df

Code review of gh40 39515df found two blocking defects, which this branch fixes. (1) class verdict-parsing: `verdict` took the first `Verdict:` line anywhere, so a fenced, quoted `Verdict: clear` beat a final `Verdict: blocking`. Now only `^Verdict: (clear|blocking)$` lines outside fenced blocks count, and lines that disagree are refused. (2) class unverified-merge-ask: any historical `qc: built` commit satisfied the check, so a code commit after qc still passed. Now each criterion row has a `judged <sha>` cell (`| criterion | qc verdict | judged | evidence |`). That sha must be a commit of the PR, and only `qc: built ... (judged <sha>)` commits may follow it (spec `#lanes-one-head`). The (b) run above predates this format.

Same method as (b), on PR #49's real data at head 39515df (`gh pr view 49 --json ...`, offline gh, scratch verdict comment naming 39515df clear). Its only qc commit is 21566b5 `qc: built acceptance-lane-archive (judged 241fd3ee875f)`, and code commits followed it. A scratch section whose row names that judged head:

```
octo-feather-lane merge-ask: PR #49 merge ask incomplete (1 item), head 39515dfea54f:
  - criterion row comms#acceptance-lane-archive: judged 241fd3ee875f, but 18 non-qc commits came after it (259ad4b85354 'fix(lane): a failed archive leaves no partial archive'): stale; rerun just qc on the head 39515dfea54f, then update the row
rc=1
```

The same row with `judged 39515dfea54f` stands for a qc rerun at the exact head with nothing to flip. It passes and prints the section (rc=0). It is scratch: no such qc run exists yet. Before this fix, the stale variant passed.

Found on the way: GitHub cuts `messageHeadline` at about 70 characters with an ellipsis and starts `messageBody` with the rest (4 of PR #16's 6 qc commits). `merge-ask` joins them; the test covers it. `verdict` was not run against GitHub: it writes, and no scratch PR was opened (the test's fake gh records its create and update calls).

## (c) Headless supervisor probe, before and after

The real supervisor role, headless, `env -u OCTO_FEATHER_PARENT -u HERDR_PANE_ID -u HERDR_TAB_ID -u HERDR_WORKSPACE_ID -u HERDR_SOCKET_PATH scripts/pi-role agents/supervisor.md -p "<scenario>"`. Before: a `git archive` of gh40 (c281ed9) in /tmp/gh48b. After: this branch. Both ran in parallel, with the role's own model. Cost was not recorded. The scenario does not name the command: "Dry run: run nothing, no herdr-say, no gh, no git; answer on stdout only. You are supervisor-gh7 for lane #7 (PR #7, one spec docs/specs/demo.spec.html). just qc on the integrated head passed acceptance-a and failed acceptance-b (a code fault); a repair implementer fixed it, qc then passed both and left head 1a2b3c4. A fresh code reviewer judged 1a2b3c4 and its report, verdict clear, is at /tmp/review-1a2b3c4.md. CI is green on 1a2b3c4. List, in order, the exact shell commands you run from here up to and including sending the merge ask, and say where the merge ask text lives and what exactly you send."

- Before: a list of 14 hand checks (`gh pr view`, `git show --stat`, `jq` on the qc report), then `herdr-say --parent "<merge ask text>"`. Verbatim: "No kit file holds it. The kit sets no path for it, so the text is just the message argument of `herdr-say --parent` and it ends up in the director's pane." The review verdict is a /tmp path, not on the PR.
- After, verbatim steps: "4. Post the review verdict and note the URL it prints: `octo-feather-lane verdict 7 1a2b3c4 /tmp/review-1a2b3c4.md`"; it writes the `## Merge ask` section (Head, Checks, the criterion table, `Review verdict: <URL from step 4>`, Built, `Failed: none`) into the PR body with `gh pr edit 7 --body-file`; "7. Run the self-check: `octo-feather-lane merge-ask 7 --status docs/specs/demo.status.json > /tmp/merge-ask-7.md` If it exits 1, I fix each item it lists on stderr and rerun steps 6 and 7 until it passes." Then: "The real copy is the `## Merge ask` section of PR #7's body." It sends "Only the section `octo-feather-lane merge-ask` printed on a pass, word for word, and nothing else."

Result: pass. The role moved the merge ask onto the PR and put the command gate in front of the send. One small slip: the after run read the spec with `sed` once, which is read-only. Not covered: the after run judged `Failed: none` correct because the final qc passed both criteria. A lane whose final qc still fails a criterion is the owed eval's case.

Teardown: `rm -rf /tmp/gh48b /tmp/gh48-before.txt /tmp/gh48-after.txt`; the snapshot scratch dir was removed after (b).
