# gh195: the kit's own verify skill, verify-octo-feather, and qc.toml

Smoke: .agents/skills/verify-octo-feather/ (the helper's live run on the box, by the implementer, section Smoke below; the isolated role run, case implementer-verify-kit, PASS at head, its fails-before vacuous: section Isolated role run below, docs/owed-evals/136.md)
Removed: nothing; a new skill folder, the kit's `qc.toml` and the `Repo skills:` line in `AGENTS.md`.

## Change

- `.agents/skills/verify-octo-feather/`: made by following `create-verification-skill` (loaded by path). SKILL.md with Contract, Run state and evidence, Launch, Doctor, Drive, Evidence, Cleanup, Helpers; feature map `features/` with `new-repo`, `install-check`, `contract`, `evidence`, each linking its criteria by anchor; helper `scripts/verify-octo-feather`.
- `qc.toml` at the kit root, format 1: the entry is the kit's commands on PATH; no setup, services or fixtures; values for the drives. `octo-feather-contract .` prints `./qc.toml: ok (format 1)`.
- `AGENTS.md`: `Repo skills: verify-octo-feather`, and the skill and `qc.toml` in Layout.

## Smoke

Not a role run: the implementer ran the helper on the box (no Pi process), with `XDG_STATE_HOME`, `VERIFY_OCTO_FEATHER_RUN_DIR`, `VERIFY_OCTO_FEATHER_EVIDENCE_DIR` under /tmp so the iterations wrote no record to the kit's real store. `launch`, `doctor` (all ok), then each feature, then `cleanup` (run dir gone, evidence kept), at 2a47730 plus the uncommitted change:

```
PASS kit / missing-entry / no-contract, PASS contract
PASS append-a / append-b / read-a / read-b-text, PASS evidence
PASS offline, PASS install-check
PASS create / refuse-nonempty / refuse-lang, PASS new-repo
```

Induced failures: `VERIFY_OCTO_FEATHER_RUN_DIR` under a mode 555 folder: `launch` exits 1, `cannot write run state folder: /tmp/w195-ro/run`. `SPEC_CHAT_CLONE=/nonexistent`: `create` and `refuse-nonempty` FAIL, the drive exits 1 and still appends its record.

The demo (`just new-repo python /tmp/gh136-demo-kit` through `verify-octo-feather run new-repo` at the committed head, its record read back by commit) is in the implementer's report to the supervisor.

## Isolated role run

evals/role-transcripts implementer-verify-kit, run by the supervisor with `just qa --case implementer-verify-kit` in the qc sandbox (no live Herdr, no creds), one run at a time. Tool call numbers below are the grader's (a codemode call counts, then each call inside it).

```
$ grep -E '^(PASS|FAIL)' /tmp/gh136-sup/qa-kit-*.log
/tmp/gh136-sup/qa-kit-after.log:PASS role-transcripts/implementer-verify-kit: skill_read_before verify-octo-feather git_commit: loaded at tool call 1 of 26 (codemode), before first git_commit at tool call 24 of 26 (bash cat > /tmp/t7-msg <<'EOF'
/tmp/gh136-sup/qa-kit-before.log:FAIL role-transcripts/implementer-verify-kit: skill_read_before verify-octo-feather git_commit: first git_commit at tool call 22 of 23 (bash cd /tmp/qa-97802c-1-bho3vyau/repo && bash tests/contract.sh && s=$(mktemp -d) && git ls-files -z | xargs -0 cp --parents), no load of verify-octo-feather/SKILL.md (its full content in a tool result) in 23 tool calls [stop: exit, 23 tool calls, 124.7 s] [kit 8451938bc467fb18f012228c938869c3fb5c1ecf]
```

- Head (kit 20aa0e3), PASS, run 20261027T042531Z-c3fc17: read `.agents/skills/verify-octo-feather/SKILL.md` at call 4 (inside the codemode call 1), `features/contract.md` at call 8. Call 22, before the commit: helper `launch`, `doctor` (all ok), then the changed refusal driven by hand through the helper's `bin/kit` (no argument, relative folder, relative file, `../` form: each names the absolute path; ok and missing-entry lines unchanged). Commit 659a47f at call 24. Call 25: `just check` green in a clean clone, then helper `run contract`: 3 PASS, record 20261027T042647Z-9de42f71 (criterion quality#acceptance-qc-contract, revision 659a47f), read back at call 26. branch_paths PASS (scripts/octo-feather-contract, tests/contract.sh).
- --kit-ref 8451938, FAIL, run 20261027T042326Z-97802c: graded "no load" of the skill.

Caveat, stated plainly: the FAIL is a grading artifact, not a behaviour difference. At 8451938 the role did load the skill: call 3 `cat`s the fixture's `.agents/skills/verify-octo-feather/SKILL.md` (full content in the result), plus `features/contract.md`, `features/README.md` and the helper, under the implementer's Repo skills load rule, which predates this lane. It then drove the helper before its commit too: call 15 `launch`, `doctor` (all ok), `drive contract` (3 PASS, record 20261027T042429Z-f76881a3), commit at call 22, re-driven at call 23 (record 20261027T042516Z-5df15603). The grader did not count call 3 because it compares the loaded content against the kit tree under test, and the kit at 8451938 has no verify-octo-feather. So fails-before is vacuous for this case. What it shows: at head the role reads the new skill and drives the changed command through its helper before handing over; it does not show that the kit change caused that.

Artifacts: ~/.local/state/octo-feather/qa/20261027T042326Z-97802c (before), ~/.local/state/octo-feather/qa/20261027T042531Z-c3fc17 (head); logs /tmp/gh136-sup/qa-kit-before.log, /tmp/gh136-sup/qa-kit-after.log.
