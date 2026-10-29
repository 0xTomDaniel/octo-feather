# gh407: just qc sends only undeclared criteria to a time-capped agent fallback; verify-octo-feather drives it (qc-fallback)

Change: the verify-octo-feather skill gains the `qc-fallback` feature: features/qc-fallback.md (Drive criterion line `quality#acceptance-qc-fallback`), its features/README.md index line, the SKILL.md description naming the agent fallback and the stub qc judge as the second allowed fake (behavioural, commit 7274398); SKILL.md Contract and Drive list pointers and the qc-capture.md link (Behaviour-neutral, b487943); the drive in scripts/verify-octo-feather, the kit qc.toml demo, the stub judge tests/fixtures/qc-judge/pi and `just qc`'s per-criterion fallback itself (4d4f4db).

Smoke: .agents/skills/verify-octo-feather/SKILL.md (description names the agent fallback, stub judge lines; run below)
Smoke: .agents/skills/verify-octo-feather/features/README.md (index line for qc-fallback; run below)
Smoke: .agents/skills/verify-octo-feather/features/qc-fallback.md (the recipe the run below follows)
Removed: nothing.

## Recorded live run at head 7274398

Clean tree at 7274398 (implementer-gh407 on gh127 251aebc, the lane tip; `git merge gh127`: already up to date), run and evidence folders in scratch (`VERIFY_OCTO_FEATHER_RUN_DIR`, `VERIFY_OCTO_FEATHER_EVIDENCE_DIR` under mktemp), drive record to the kit's real store. The judge is the stub `tests/fixtures/qc-judge/pi` on the qc sandbox's PATH (`OCTO_FEATHER_QC_PATH`), as features/qc-fallback.md says: no model ran in this run. Command, as SKILL.md and features/qc-fallback.md give it:

```
.agents/skills/verify-octo-feather/scripts/verify-octo-feather run qc-fallback
```

Exit 0, `verify-octo-feather: run PASS`. `verify-octo-feather: ready: ... rev=7274398`. summary.txt:

```
qc-fallback @ rev 7274398, 2026-10-29T21:13:17Z
PASS qc: XDG_STATE_HOME=<run>/scratch/qc-fallback/state OCTO_FEATHER_QC_PATH=<kit>/tests/fixtures/qc-judge env -C <run>/scratch/qc-fallback/repo just --justfile <kit>/justfile qc docs/specs/demo.status.json 7 acceptance-a acceptance-b
PASS read: XDG_STATE_HOME=<run>/scratch/qc-fallback/state OCTO_FEATHER_QC_PATH=<kit>/tests/fixtures/qc-judge octo-feather-evidence read --repo <run>/scratch/qc-fallback/repo --criterion 'demo#acceptance-b' --commit aab97f0a205ed020e40f64d3b126c70d7b8a3265
PASS qc-fallback
```

`qc` stdout (scratch target head aab97f0a205e; acceptance-a declares a demo, acceptance-b none):

```
PASS acceptance-a: $ echo demo checks pass
  demo exit status 0
  evidence complete; decision demo checks; record 20261029T211320Z-f06ed2f3
PASS acceptance-b: $ judge acceptance-b
  why acceptance-b
  evidence complete; decision agent fallback; record 20261029T211322Z-70d13831
qc: 2/2 passed at aab97f0a205e; offline gh refusals 0; head now cd548fc36b83; report <run>/scratch/qc-fallback/state/octo-feather/qc/aab97f0a205ed020e40f64d3b126c70d7b8a3265-20261029T211318Z-bdfbdf.json
```

`qc` stderr, the fallback's lines: `qc: agent fallback demo#acceptance-b: a fresh qc judge, time cap 900 s`, its own sandbox session `qc-aab97f0a205e-bdfbdf-j0` (the demo's: `-d0`). The report: `cap_s` 900, `fallback` holding acceptance-b alone, its judge's parent `timeout --foreground -k 10 900 <kit>/scripts/pi-role <kit>/agents/qc-judge.md ...`, its brief's one criterion line `- acceptance-b: Given a user, When acceptance-b runs, then it prints ok.`, record `20261029T211322Z-70d13831`. `read`: one record at aab97f0a205e holding `judge.exit`, `judge.report.json`, `judge.stdout`.

Drive record: `verify-octo-feather: evidence record 20261029T211322Z-839ac525 (criterion quality#acceptance-qc-fallback; ...)`; `octo-feather-evidence read --criterion quality#acceptance-qc-fallback --commit 7274398` reads it back at revision 72743981d295, 16 outputs.

## The real judge, once, by accident

A first trial drive (uncommitted tree, kit state in scratch) put the stub only on PATH; `just` here is a mise shim whose node prefix holds the box's real Pi, so the real qc judge (`openai/gpt-6.1-sol`) ran the fallback for acceptance-b: in its own sandbox under the cap, it reported `fail` ("Cannot exercise acceptance-b: no executable, runnable script or declared demo exists"), and that report read back as acceptance-b's record (`judge.report.json`, `judge.stdout`). The drive now uses `OCTO_FEATHER_QC_PATH` (features/qc-fallback.md, Gotchas). Its spend went to that trial's scratch state ledger, not the box's.
