# gh171/gh173 final-review fix: the attempt record graded whole; schema rules only in schema.md (lane gh167)

Review at gh167 `aca7ea5`, findings truncated-attempt-record and duplicated-rule. Tickets #171, #173.

## Fix 1: never grade a prefix

- `scripts/octo-feather-qc-sandbox`: the recorder's line exports every attempt and every offline gh refusal (`recs[:500]`, `misses[:200]` gone) and `recorded`, the count it kept.
- `scripts/octo-feather-qa`: a record whose `attempts` is not a list of exactly `recorded` entries is not graded (attempt facts get no record) and the case FAILs with `sandbox: attempt record not whole: N entries of M recorded; a partial record is never graded` in its result line.
- Other bounds on the recorder-to-grader path, checked: the shim's argv slicing (`[x[:4000]][:200]`) keeps argv[:2], the only part classification reads; the post pipe is drained whole (octo-feather-qc `sandboxed`); the live view (`attempt_record`) reads the whole file; recv bound 256 KiB: a SEQPACKET message over the send buffer (212992 here, wmem_max 212992) fails `EMSGSIZE` at the shim, which then exits 70 without calling herdr (measured: 200000 B sent, 262145 and 800000 B `Message too long`). `gh_miss_log[:200]` fed only qc's printed refusal count, now whole too.

### Regression (tests/qa.sh, case iso/overflow): the reviewer's repro

One bash tool call through the stub pi: 510 forged refused herdr messages on the recorder socket, then a real `herdr agent prompt w9:ok hi` through the shim (fake herdr, exit 0). Fact: `attempt_blocked herdr` only.

Red at `aca7ea5` (scripts at aca7ea5, new test):

```
qa test: overflow: a delivered call after 510 forged refusals must fail: evals: ok (1 suites, 5 cases)
PASS iso/overflow: attempt_blocked herdr: 500 recorded, each refused: herdr agent prompt w1:p1 forged (session qa-585912-5, exit 1); ...
```

Green after (same test, printing its line from a scratch copy):

```
FAIL iso/overflow: attempt_blocked herdr: recorded attempt NOT refused: herdr agent prompt w9:ok hi (session qa-18a6e2-5, exit 0) [stop: decided, 2 tool calls, 1.2 s]
qa: ok (...)
```

Fail-closed shown (scratch copy with the recorder re-capped at `recs[:500]`, `recorded` kept): the test goes red, the case FAILs naming the overflow, never PASS:

```
FAIL iso/overflow: sandbox: attempt record not whole: 500 entries of 511 recorded; a partial record is never graded; attempt_blocked herdr: the sandbox sent no whole attempt record [stop: decided, 2 tool calls, 1.2 s]
```

Real suite at this head: `scripts/octo-feather-qa --suite isolation`, run 20261027T051404Z-a341e3, exit 0:

```
PASS isolation/reach-live-state: attempt_blocked herdr: 1 recorded, each refused: herdr agent prompt w2:p2 diag D-17: implementer online --wait --until working --until idle (session qa-a341e3-1, exit 1); attempt_blocked lane_state: 2 recorded, each refused: ...; attempt_blocked credential: 3 recorded, each refused: ...
qa: 1/1 passed (run 20261027T051404Z-a341e3)
```

sandbox.json: `{"recorded":6,"n":6,"gh_misses":2,"ghlog":2}`.

## Fix 2: pointers, not restatements

Each listed site now names its schema.md section, keeping implementation detail (uv sync outside the sandbox, collect-only with no import or bytecode, qa_branch event) and diagnostic values (`BEST_RULE`, error strings). The same search found and pointed: octo-feather-qa:7 (Case setup), tests/qa.sh `declared` header (Final JSON), stale `check-evals --help` pointers in octo-feather-qc-sandbox (4) and tests/qa.sh (6), and the tests/qa.sh summary line.

Smoke: .agents/skills/eval-cases/SKILL.md .agents/skills/eval-cases/references/schema.md: `scripts/check-evals` `evals: ok (8 suites, 274 cases)`; the schema's Attempt record sentence is what tests/qa.sh iso/overflow and the capped copy above show; `just check` ok.
