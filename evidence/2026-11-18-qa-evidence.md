# gh995: a stored eval run's evidence block, generated, never transcribed

Change: `octo-feather-qa --analyze RUN_DIR --evidence` prints a stored run's markdown evidence block (rule: `octo-feather-qa --help`, Evidence; owner ruling 2026-11-18 #978). The eval-cases skill's step 4 says to put that output in the evidence file. The verify skill gains the qa-evidence feature and its drive.

Smoke: .agents/skills/eval-cases/SKILL.md (step 4 wording; the command it names, run below on gh840's final run; no model run)
Smoke: .agents/skills/verify-octo-feather/ (the qa-evidence feature file, its listing in SKILL.md and features/README.md, and its drive; no model run)

## The drive

`.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive qa-evidence` at 7e6619d6 (clean): PASS block, again, pin; evidence record 20261118T200410Z-324834fb (criterion quality#acceptance-qc-eval-verdict).

## Demo (gh840's final run, kit 4c7e2433, baseline b20ee656)

`scripts/octo-feather-qa --analyze ~/.local/state/octo-feather/qa/20261117T151829Z-60554a --evidence` twice: exit 0, 1033 lines, the two outputs byte-identical (sha256 e0002c4d5f012cc6b997c7c75030bc43c26e02d5b4490582a03acf9adeca4d73 each), 23 pin lines, one per case. Its head:

```text
## Eval evidence: run 20261117T151829Z-60554a

Generated from the stored run alone by `octo-feather-qa --analyze <qa dir>/20261117T151829Z-60554a --evidence`; never edited by hand.

- run: 20261117T151829Z-60554a, 3 run(s) per case
- current kit: 4c7e243369812d9acf1dc68e5a1a004aae023f50 (kit ref HEAD)
- baseline kit: b20ee656e6fa17ed19f4a617b9962ffb5fc0770f (--baseline b20ee656e6fa17ed19f4a617b9962ffb5fc0770f)
- cases passed: 18/23

### supervisor-autonomy/local-repair-and-ready-work
```
