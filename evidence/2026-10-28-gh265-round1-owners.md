# Lane reflection, review round 1: point to the owners; reflect-live driven (#265, pilot of #230)

Trigger: PR #279 review round 1 (two blocking duplicated-rule findings) and qc at 9867b71 (FAIL comms#acceptance-reflect-lane, comms#acceptance-reflect-caught-by-hand: live reflection not exercised, a judging fault). Owed eval: docs/owed-evals/230.md.

## What changed

- Reflect patch and materialized skill (steps 2 and 5), agents/reflector.md Rules: the question and finding requirements now point to comms spec `#reflection-questions`, `#reflection-output`.
- agents/director.md Correction lanes, docs/adr/0020 trigger: point to issue-lifecycle spec `#lanes-correction` and comms spec `#reflection-correction`; ADR trigger sentence corrected in place (Decided by Tom (owner), 2026-10-28 (issue #230)).
- verify-octo-feather `lane-archive`: `reflect-live` is a drive case (the real reflector through pi-role on the seeded gh900 lane with the stranded-worker director note); SKILL.md states the one exception to offline.
- `octo-feather-lane --help` and tests/lane-reflect.sh header point to `#reflection-output`.

## Smoke

Smoke: .agents/skills/verify-octo-feather/ agents/reflector.md .agents/skills/reflect/ .skillfile/patches/skills/reflect/SKILL.md.patch: `verify-octo-feather drive lane-archive` at committed head d2664b8, reflector at its role defaults (thinking high), 1m15s, exit 0, evidence record 20261028T034548Z-a3c9cdb7:

```
PASS refuse-unreachable: ... unshare -Un --map-current-user octo-feather-lane archive gh900
PASS refuse-no-record: ... octo-feather-lane reflect gh404
PASS reflect-live: ... OCTO_FEATHER_REFLECT_ARGS=--no-session OCTO_FEATHER_REFLECT_TIMEOUT=1800 octo-feather-lane archive gh900
    stdout: reflection: lane gh900, 3 findings, questions caught-by-hand, slow-or-from-memory, undetected-rule, check-misfired, mechanical-step, writer-mistake, reflection-missed: appended to .../lanes/gh900.handoffs.jsonl
    stdout:   finding worker-startup-stall (caught-by-hand) -> worker launch command with readiness acknowledgement and timeout: director.handoffs.jsonl:1 records implementer-gh901 stranded at "Trust project folder?" for 35 minutes, unnoticed by its supervisor; ...
    stdout:   finding duplicated-rule (writer-mistake) -> writer template rule-ownership field, following docs/adr/0008-prose-last.md rung 1: ...
    stdout:   finding missing-session-provenance (undetected-rule) -> lane and director startup commands, persistent session metadata: ...
    archived log: {... "kind": "finding", "source": "reflection", "class": "worker-startup-stall", "blocking": false, "question": "caught-by-hand", ...}
    archived log: {... "kind": "reflection", "findings": 3, "questions": [the seven lane ids]}
verify-octo-feather: drive lane-archive PASS
```

comms#acceptance-reflect-lane: one reflection line, one finding line per gap, each source reflection with class, question and route. comms#acceptance-reflect-caught-by-hand: the caught-by-hand finding names the director's stranded-worker catch and what would have caught it first. Earlier cheap smoke of the same drive (`OCTO_FEATHER_REFLECT_ARGS="--thinking off"`, working tree): PASS lane-archive, 2 findings, record 20261028T033535Z-4b2e9b84.

Smoke: agents/reflector.md .agents/skills/reflect/ (the pointers followed): `octo-feather-lane reflect gh900` on a scratch copy of the same lane, session kept (transcript 01a1809d-7c62-712e-945c-ccd842ed7924), exit 0, 2 findings (stranded-worker caught-by-hand, duplicated-rule writer-mistake). Tool calls: read `.agents/skills/reflect/SKILL.md`, codemode over the three lens templates and `references/synthesizer.md`, the records, then read `docs/specs/comms.spec.html` lines 1-220 (holds `#reflection-questions` 207, `#reflection-output` 208).

Smoke: agents/director.md headless, `--no-tools --thinking low --no-session`, a closed question (a close report naming reflection-filed correction issue #301; an owner spec-call denial at merge; where "due" is defined; does it count classes itself). Reply, abridged: "1. Start it: yes. The archive reflection already filed the issue (comms spec `#reflection-correction`), so I don't file a new parent ticket ... from #301 as named in the close report ... 2. A denial is an owner correction at a gate, so a correction lane is due. I start it like any lane: File the parent ticket with the tracker skill's `issue-create` ... Where 'due' is defined: spec `#lanes-correction` for both (docs/adr/0020) ... Count finding classes myself? No. My role file gives me no command or counting step."

## Removed

Removed: agents/director.md's jq class count after each merge ask and its retrigger rule (now spec `#lanes-correction`, filed by the reflection, comms `#reflection-correction`); docs/adr/0020's two-case trigger and "the director counts classes across lanes after each merge ask"; agents/reflector.md's answer-every-question, evidence and routing rules; the reflect patch's restated question and finding requirements (steps 2 and 5); the lane-archive drive's `UNREACHABLE reflect-live` step.
