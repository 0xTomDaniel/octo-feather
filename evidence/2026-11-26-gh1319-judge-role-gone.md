# #1319: the QC judge role goes from the kit

ADR 0035 Consequences: the QC judge role and its launch path in the qc sandbox go (#1318 removed the launch from
`scripts/octo-feather-qc`). This change deletes the role file and every role list, stub and eval case that named it.

Removed: agents/qc-judge.md (the QC judge role, ADR 0035), its stub fixture tests/fixtures/qc-judge, and its eval
cases role-transcripts qc-judge-demo-path, qc-judge-no-reviewer-skills, qc-judge-drives-app and skill-triggers
qc-prove-greet-plain, qc-prove-greet-json, qc-prove-near-list-ids, qc-prove-near-app-command.

Smoke: agents/qc-judge.md .agents/skills/verify-octo-feather/features/role-launch.md .agents/skills/github-pr/SKILL.md

Live runs on this branch (head 802626ac):

- `agents/qc-judge.md`: `scripts/pi-role agents/qc-judge.md` fails as `scripts/pi-role agents/nope.md` does
  (exit 1, `FileNotFoundError: ... 'agents/qc-judge.md'`); `scripts/check-roles`: `roles: ok (8 role files, reviewer
  family openai != implementer anthropic)`; `scripts/check-evals`: `evals: ok (20 suites, 526 cases)`.
- `features/role-launch.md`: `verify-octo-feather run role-launch`: PASS, each role's launch (`director`,
  `supervisor`, `implementer`, `general-worker`, `corrector`, `code-reviewer`, `shaper`), other-mcp, list-once and
  identity cases; evidence records 20261126T062413Z-77fcb189, -49a0d5a4, -97868f4b, -05164615.
- `github-pr/SKILL.md` (Offline gh section, wording: the offline gh the kit's tests use and the qc sandbox also
  runs): `verify-octo-feather run merge-ask-proof`, which puts that offline gh (`.agents/skills/github-pr/scripts/gh`)
  first on PATH over a scratch snapshot: PASS; evidence records 20261126T062419Z-e9076150, -7d1e8473, -f881f61d.
