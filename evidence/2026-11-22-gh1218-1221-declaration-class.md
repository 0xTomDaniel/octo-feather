# gh1218 / #1221: a declaration-only check is classed declaration and shown apart in the merge ask

Spec: issue-lifecycle `#lanes-one-head` (last sentence), `#acceptance-declaration-check-shown` (commit 76820638; call 3 in docs/specs/issue-lifecycle.calls.jsonl, the owner rules on it at merge). Design: #1218 comment 7082233269, term 3.

Change: the Check field's class takes a third value, `class: exact|proxy|declaration` (code-review skill, Verdict step, Report fields: one patch hunk of `.skillfile/patches/skills/code-review/SKILL.md.patch`, two changed lines, materialized in `.agents/skills/code-review/SKILL.md`; docs/adr/0008 rung 2, one sentence). `octo-feather-lane verdict` and `fields` accept it, a declaration line does not block; `merge-ask` on a pass prints such lines under `Declaration checks (stopgaps; owner rules at merge): <n>`, apart from `Review check classes`, pass or fail unchanged.

Smoke: .agents/skills/code-review/ .skillfile/patches/skills/code-review/SKILL.md.patch

Removed: no rule deleted; two patch lines are rewritten in place: the Check line form `class: exact|proxy` becomes `class: exact|proxy|declaration`, and "`exact` and `proxy` are as docs/adr/0008 rung 2 defines them" becomes "`exact`, `proxy` and `declaration` are ...". Incident: PR #1216 review round 2 classed `test-commit trailer declarations recorded before commit (#1215 declaration stopgap)` as `class: exact`, and nothing showed the owner it was a stopgap (#1218 term 3).

## Smoke: one live headless code-reviewer run on a fixture diff (2026-11-22)

Fixture: a scratch repo `/tmp/cr-smoke-1221` (a `bin/check-commit` CLI; AGENTS.md: a behaviour change ships with a CLI test, owner ruling issue #4): main 51663986, lane commit b53cc8f4 adds a refusal of any commit with no `Tested: <test path>` trailer, a check whose only input is the writer's declared trailer, and its CLI test. The brief names a full round and never the class:

```
$ scripts/pi-role agents/code-reviewer.md -p "Review lane gh4 in this repo (branch lane, main is the base): the whole lane from main 51663986 up to HEAD b53cc8f4. Report as your role requires."     # cwd /tmp/cr-smoke-1221, this worktree's kit
```

Final message (stdout, exit 0, 82s), verbatim:

```
Verdict: clear
Range: 51663986cb57e9b8fae17583e048ac0b36fd233f..b53cc8f4bcc8240cd5072f80fa966beaecfcbd77
Check: bin/check-commit: behaviour changes ship with a CLI test run (AGENTS.md Rules, issue #4) | reads: producer-declared Tested commit trailer | class: declaration
Owners: none

No blocking findings.

- **Note, class: declaration-check:** `bin/check-commit:12-15` verifies the writer’s declaration, not test existence, coverage or execution. ADR 0008 explicitly permits declaration checks; show separately to the owner.
- **Note, class: unavailable-review-context:** No remote or gh4 handoff log available. Ticket comments and writer prior-art claims remain unaudited. Seam verification exited 2, unchecked. `AGENTS.md` explicitly authorizes the CLI seam used.

Validation: CLI test passed; `git diff --check` passed. Reviewed the full diff, documented standards, test assertions and seams. Reuses Git’s trailer parser.

**Report delivery failed:** `herdr-say --parent` exited 64, “no parent recorded for this pane.” Nothing delivered. Next step requires restoring the parent association before resending.
```

The report classes the trailer check `class: declaration` at column 0 in the verdict reader's scope, with `Verdict: clear`; `octo-feather-lane fields` reads it as `{"path": "bin/check-commit", ..., "class": "declaration"}`, no errors. (Its herdr-say failure is the headless run's: no parent pane.) One observed run, not comparative eval proof: the eval case is owed (docs/owed-evals/1221.md).

## Demo: the recorded PR #1216 (tests/gate/kit/lane_verdict_rounds.py, declaration_shown)

Round 2's recorded report with its trailer line classed declaration (Range 6eaf8c7b..ffba6ee7), then round 3 (clear, Range ffba6ee7..2dc6f718), posted with `verdict`; `octo-feather-lane merge-ask 1216 --base origin/main` exits 0 and prints:

```
Review check classes (from the verdict comment, docs/adr/0008):
- Check: scripts/octo-feather-lane: rule-only seam record and timing (ADR 0002; #1214) | reads: ticket acceptance items, notes, Git author time | class: exact

Declaration checks (stopgaps; owner rules at merge): 1
- Check: scripts/octo-feather-lane: test-commit trailer declarations recorded before commit (#1215 declaration stopgap) | reads: worker commits, paths, interpret-trailers, ticket notes, handoff log | class: declaration

Review rounds (from the verdict comment, issue-lifecycle #lanes-one-head):
- Round 1: 6eaf8c7b98f3..ffba6ee7e78f full, verdict blocking
  - Check: scripts/octo-feather-lane: rule-only seam record and timing (ADR 0002; #1214) | reads: ticket acceptance items, notes, Git author time | class: exact
  - Check: scripts/octo-feather-lane: test-commit trailer declarations recorded before commit (#1215 declaration stopgap) | reads: worker commits, paths, interpret-trailers, ticket notes, handoff log | class: declaration
- Round 2: ffba6ee7e78f..2dc6f718805b delta, verdict clear
  - Checks: none
```

`declaration_verdict`: the same report, `Verdict: clear`, its trailer line classed `proxy` is refused (a proxy check blocks) and classed `stopgap` is refused naming `class: exact`, `class: proxy` or `class: declaration`, nothing written; classed declaration it posts one full round and merge-ask passes, showing it under the heading.
