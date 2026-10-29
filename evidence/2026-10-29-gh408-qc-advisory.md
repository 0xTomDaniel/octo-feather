# gh408: just qc shows the judgment model's advisory answer beside each recorded result; verify-octo-feather drives it (qc-advisory)

Change: `just qc` asks the kit's one judgment model the criterion-evidence question (evals/judgment-criterion-evidence) per result with an evidence record, through octo-feather-qa's classify path, and shows the answer and confidence beside the result, labelled an advisory model judgment; no verdict, status or exit reads it (6f970ee). The verify-octo-feather skill gains the `qc-advisory` feature: features/qc-advisory.md (Drive criterion line `quality#acceptance-qc-advisory`), its features/README.md line, the SKILL.md description, and the rule that every `just qc` drive runs with the kit's stub classifier, never a real model (behavioural, 1bc4191); its drive and the stub in the qc-capture and qc-browser drives (6f970ee, b8c6167); SKILL.md Contract and Drive list pointers (Behaviour-neutral, f904aeb).

Smoke: .agents/skills/verify-octo-feather/SKILL.md (description and the faked classifier; runs below)
Smoke: .agents/skills/verify-octo-feather/features/README.md (index line for qc-advisory; run below)
Smoke: .agents/skills/verify-octo-feather/features/qc-advisory.md (the recipe the first run below follows)
Smoke: .agents/skills/verify-octo-feather/features/qc-capture.md (the advisory line unavailable; second run)
Smoke: .agents/skills/verify-octo-feather/features/qc-browser.md (the advisory line unavailable; third run)
Removed: nothing.

How the induced answer is made: the kit's stub `pi`, `tests/fixtures/classify-stub/pi`, symlinked into the drive's scratch `bin/` and put first on the qc sandbox's PATH through `OCTO_FEATHER_QC_PATH` (the kit justfile puts `~/.local/bin`, the box's real pi, before a caller's PATH, so a plain PATH prepend does not reach it). It runs the kit's real classify extension command under node with a stub model registry listing only the kit's judgment model (`evals/judgment-model.json`), whose every answer is `STUB_ANSWER=does-not-show` at `STUB_CONFIDENCE=0.91`. No real model is called; tests/qc-advisory.sh uses the same stub.

## Recorded live runs at head 1bc4191

Clean tree at 1bc4191 (implementer-gh408 on gh127 251aebc), run and evidence folders in scratch (`VERIFY_OCTO_FEATHER_RUN_DIR`, `VERIFY_OCTO_FEATHER_EVIDENCE_DIR` under mktemp), drive records to the kit's real store.

### qc-advisory

```
.agents/skills/verify-octo-feather/scripts/verify-octo-feather run qc-advisory
```

Exit 0, `verify-octo-feather: run PASS`. `verify-octo-feather: ready: ... rev=1bc4191`. summary.txt:

```
qc-advisory @ rev 1bc4191, 2026-10-29T21:07:07Z
PASS qc: XDG_STATE_HOME=<run>/scratch/qc-advisory/state OCTO_FEATHER_QC_PATH=<run>/scratch/qc-advisory/bin STUB_ANSWER=does-not-show STUB_CONFIDENCE=0.91 env -C <run>/scratch/qc-advisory/repo just --justfile <kit>/justfile qc docs/specs/demo.status.json 7 acceptance-a
PASS qc-advisory
```

`qc` stdout (scratch target head 9d4e746f9dcf):

```
PASS acceptance-a: $ echo demo checks pass
  demo exit status 0
  evidence complete; decision demo checks; record 20261029T210710Z-24f5a156
  advisory model judgment (no gate reads it): does-not-show, confidence 0.910 (criterion-evidence by openrouter/typesafe/jev-1.13; uncalibrated)
qc: 1/1 passed at 9d4e746f9dcf; offline gh refusals 0; head now 14c7fc6a6a09; report <run>/scratch/qc-advisory/state/octo-feather/qc/9d4e746f...-20261029T210708Z-f3dd60.json
```

`qc` stderr: 40 `qc sandbox: ok` lines (the demo's sandbox and the classify sandbox), 0 `FAIL`, and `qc: advisory criterion-evidence question to openrouter/typesafe/jev-1.13 for 1 recorded criteria (no gate reads it)`. The report's result for acceptance-a: `verdict` pass, status file `built`, and

```
{"judgment": "model judgment (classifier output, advisory: no gate reads it)", "question": "criterion-evidence", "model": "openrouter/typesafe/jev-1.13", "calibration": null, "answer": "does-not-show", "confidence": 0.91}
```

The drive's own record: `20261029T210712Z-48276458`, quality#acceptance-qc-advisory, revision 1bc4191eed87, text from spec, contract qc.toml format 1, 9 outputs.

### qc-capture and qc-browser (their advisory line, stub classifier)

`verify-octo-feather run qc-capture`: exit 0, run PASS; 4 result lines followed by `advisory model judgment unavailable (criterion-evidence by openrouter/typesafe/jev-1.13): stub: provider error; the result stands as decided`, the results as before. Records `20261029T210734Z-067a2868` (quality#acceptance-qc-capture), `20261029T210734Z-bca28a47` (quality#acceptance-qc-same-verdict).

`verify-octo-feather run qc-browser`: exit 0, run PASS; 1 such unavailable line. Record `20261029T210740Z-e522d9b8` (quality#acceptance-qc-capture-browser).

Agent run (a role reading the skill and choosing this drive): no `just qa` case; owed, with the reason (#419), in docs/owed-evals/408.md.
