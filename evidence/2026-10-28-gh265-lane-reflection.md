# Lane reflection at archive: reflector role, vendored pstack reflect, question list (#265, pilot of #230)

Trigger: issue #265. Owed eval: docs/owed-evals/230.md.

## What changed

- `octo-feather-lane archive` runs `octo-feather-lane reflect` before moving any file; the reflection's parts live in `scripts/octo-feather-reflect` (question list, brief, run, labelled-reply parser, log lines).
- New role `agents/reflector.md` (openai/gpt-6.1-sol, high, read, grep, find, ls), loading pstack `reflect` vendored at cursor/plugins@0b8e952 with `.skillfile/patches/skills/reflect/SKILL.md.patch` (one headless agent, lenses and synthesis itself, findings only).
- Question list `reflection/questions.json`, seeded from issue #230 body and comments.
- `agents/supervisor.md` close step: archive runs the reflection; on its refusal, fix and rerun, never move files by hand; the close report names the findings count.

## Smoke

Smoke: agents/reflector.md .agents/skills/reflect/ .skillfile/patches/skills/reflect/SKILL.md.patch: live reflector run, the ticket's demo (2026-10-28, model openai/gpt-6.1-sol, thinking high; transcript session 01a18065-811b-7425-9b4b-74be565e9bf9). Scratch lane gh900 under `/tmp/gh230-demo/octo-feather/lanes/`: record, hand-off log with a spawn (session not on disk), an attempt, a blocking code-review finding `duplicated-rule`, two review rounds, integration, close; director log with `read pane w90:p3: implementer-gh901 stranded at Pi's 'Trust project folder?' prompt for 35 min; supervisor w90:p2 had not noticed` and one unrelated lane's note.

```
XDG_STATE_HOME=/tmp/gh230-demo HERDR_SESSION= scripts/octo-feather-lane archive gh900    # 1m40s, exit 0
```

The transcript shows the reflector read `.agents/skills/reflect/SKILL.md`, then the three lens templates and `references/synthesizer.md`, then the records (read, codemode only). Output:

```
reflection: lane gh900, 5 findings, questions caught-by-hand, slow-or-from-memory, undetected-rule, check-misfired, mechanical-step, writer-mistake, reflection-missed: appended to /tmp/gh230-demo/octo-feather/lanes/gh900.handoffs.jsonl
  finding stranded-startup (caught-by-hand) -> worker-spawn readiness handshake: Director manually found the worker blocked at "Trust project folder?" for 35 minutes while its supervisor had not noticed (/tmp/gh230-demo/octo-feather/director.handoffs.jsonl:1). Require startup acknowledgement with a bounded timeout that surfaces the blocked pane, without automatically granting trust.
  finding missing-gate-evidence (undetected-rule) -> integration command and gate receipts: ...
  finding missing-spend-telemetry (check-misfired) -> worker launch and spend-ledger registration: ...
  finding unavailable-transcripts (check-misfired) -> spawn, park and transcript-retention structure: ...
  finding duplicated-rule (writer-mistake) -> implementer artifact template with rule-owner reference slot: Code review blocked tests/greet.sh for restating the AGENTS.md --json rule, requiring another review round (...gh900.handoffs.jsonl:3-5). ...
archived: /tmp/gh230-demo/octo-feather/lanes/archive/gh900.toml sha256=0b628ac9...
archived: /tmp/gh230-demo/octo-feather/lanes/archive/gh900.handoffs.jsonl sha256=aea4ae7b...
```

The archived log ends with the five finding lines (`"source": "reflection"`, `"blocking": false`, question, route, summary) and `{"kind": "reflection", "findings": 5, "questions": [the seven lane ids]}`. comms#acceptance-reflect-caught-by-hand: the first finding names the director's catch by reading the pane and what would have caught it first. comms#acceptance-reflect-lane: one reflection line, one finding line per gap.

Smoke: induced failures with the real pi-role and pi (comms#acceptance-reflect-before-archive), scratch lane gh902 in the same state:

```
OCTO_FEATHER_REFLECT_ARGS="--model openai/gpt-unreachable-x" XDG_STATE_HOME=/tmp/gh230-demo HERDR_SESSION= scripts/octo-feather-lane archive gh902
octo-feather-lane archive: lane reflection of gh902 failed (reflector exited 1: OpenAI API error (400): {"code":"model_not_found",...}); nothing appended, every file left in /tmp/gh230-demo/octo-feather/lanes: fix the cause, then rerun   # exit 1, sha256 of gh902.* unchanged
HTTPS_PROXY=http://127.0.0.1:9 ... scripts/octo-feather-lane archive gh902
octo-feather-lane archive: lane reflection of gh902 failed (reflector exited 1: Connection error.); nothing appended, ...   # exit 1, lanes/ still lists gh902
```

Smoke: .agents/skills/verify-octo-feather/ drive `lane-archive` (offline: `unshare -Un`, dead Herdr socket, scratch state): `PASS refuse-unreachable`, `PASS refuse-no-record`, `UNREACHABLE reflect-live` (needs the network; covered by the demo above), `drive lane-archive PASS-with-unreachable`; evidence record id in the lane's report.

Smoke: agents/supervisor.md headless, `--no-tools --thinking low`, a closed question (lane merged, workers closed: the archive command, what it runs first, what on a refusal). Reply: "1. Command: `octo-feather-lane archive <name>` ... 2. Before moving any file, it runs the lane reflection (spec `#reflection-lane`) and appends that reflection's finding and reflection lines ... 3. If it refuses, a failed reflection included, I make the fix it names and rerun it, never moving the files by hand; once it passes, I send my close report with the reflection's findings count and terminate."

After these runs the owned-rule search replaced restated rules with pointers (agents/reflector.md: questions and class rules now point to comms `#reflection-questions`, `#reflection-output`; agents/supervisor.md: "which reflects on the lane first (spec `#reflection-lane`...)"); the behaviour the smokes exercise is unchanged, no new runs.

## Removed

Removed: `octo-feather-lane archive`'s "no hand-off log: ...; archived the record alone" branch (the reflection now writes a lane's first hand-off line, so a lane always archives a log); agents/supervisor.md's bare "on a refusal, do the fix it names" (now names the failed reflection and forbids moving files by hand); the upstream reflect skill's Task fan-out, model table, apply and approval steps (patch).

## Level

- Rung 1 (structure): the reflection runs inside the archive command, not as a role step; the question list is data with one owner.
- Rung 2 (exact): the reply's labelled fields are parsed and refused exactly (`scripts/octo-feather-reflect`), tested by tests/lane-reflect.sh with a stub pi.
- Rung 3 (structured judgment): what the reflector finds; graded by the owed eval below.
