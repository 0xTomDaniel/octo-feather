# factory-report

Criteria:

- [comms#acceptance-report-reflection](../../../../docs/specs/comms.spec.html#acceptance-report-reflection)
- [comms#acceptance-report-gate-budget](../../../../docs/specs/comms.spec.html#acceptance-report-gate-budget)
- [comms#acceptance-report-owner-caught-headline](../../../../docs/specs/comms.spec.html#acceptance-report-owner-caught-headline)
- [comms#acceptance-report-skill-reach](../../../../docs/specs/comms.spec.html#acceptance-report-skill-reach)

Drive criterion: `comms#acceptance-report-reflection`
Drive criterion: `comms#acceptance-report-gate-budget`
Drive criterion: `comms#acceptance-report-owner-caught-headline`
Drive criterion: `comms#acceptance-report-skill-reach`

## Sub-features

- `reflection-never` the report over a director log with no reflection line: says the director reflection never ran.
- `reflection-two-days` the report over a director log whose latest reflection line is two days old: shows that time, the log unchanged.
- `gate-budget-over` the report with one open lane on o/r whose latest passed full gate run is over o/r's gate-time budget and grown past its share: shows that repository's block flagged `OVER BUDGET` and `GROWN`, with the trend and slowest items, the trend file unchanged.
- `owner-caught-headline` the report over a director log with owner-caught findings two days and nine days ago: its line after the first, before any lane, counts each week.
- `skill-reach` the report over scratch Pi session files: per role, each skill's sessions read/offered (a codemode batch's read counted from the nestedCalls Pi recorded; a session started nine days ago with a read today counted, its read nine days ago not; a sed script or grep naming a SKILL.md, and a batch whose source names tracker/SKILL.md aborted before reading it, no read), a read of a skill the role was not offered counted apart, a session wholly nine days old left out, the session files unchanged.

## How to get to it (user POV)

- The director runs `octo-feather-lane report` before each status answer to the owner. What it shows and its output lines: `octo-feather-lane --help` (report).

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive factory-report`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/factory-report/`.

The drive seeds a scratch state (`XDG_STATE_HOME` under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/factory-report/state`) with no open lane for the reflection cases, so they call no `gh`; `HERDR_SOCKET_PATH` points at no server; `PI_CODING_AGENT_DIR` is a scratch folder, so no case reads the box's own Pi sessions. The gate-budget case adds one lane record on `o/r` with no PR and reads GitHub through the kit's fake gh (`tests/fixtures/lane-report/gh`, through a scratch `bin/gh` wrapper first on PATH, `FAKE_GH_PRS` a scratch store holding o/r's default-branch commits and `gate-budget.toml`), never the network.

- **Never ran** (`reflection-never`). The director log holds one note line. Run `octo-feather-lane report`. Observe exit 0 and one `director reflection:` line, `never ran (director.handoffs.jsonl)`.
- **Gate budget over** (`gate-budget-over`). Seed `check-runs.jsonl` with three passed full runs on o/r's main commits (200, 220, 210 s), then one at 330 s and a later subset run; o/r's `gate-budget.toml`: 300 s, share 0.2, 3 trend runs. Run `octo-feather-lane report`. Observe exit 0 and the block `gate budget o/r: ...`, `full gate: 330s ...: OVER BUDGET by 30s (budget 300s)`, `growth: +57.1% over the trend's median 210s (the 3 passed full runs before it); set share 20%: GROWN`, the trend line (the subset run left out) and `slowest: tests/slow.sh 270s, tests/mid.sh 40s, check-lint 2.5s`.
- **Two days ago** (`reflection-two-days`). Append an older reflection line, then one two days old. Run `octo-feather-lane report`. Observe exit 0 and one `director reflection: last ran <the latter's at> (2d0h<m>m ago)` line, the director log unchanged.

- **Headline** (`owner-caught-headline`). Append owner-caught findings: two two days ago, one nine days ago. Run `octo-feather-lane report`. Observe exit 0 and the report's second line `owner-caught (headline, director.handoffs.jsonl): 2 in the last 7 days, 1 in the 7 days before`.
- **Skill reach** (`skill-reach`). Write scratch Pi session files, every line timestamped, each tool call followed by its result (a codemode batch's carrying `nestedCalls`, as Pi records them): implementers offered commit and tdd, one whose batch's nested calls read tdd, one reading commit, one started nine days ago reading commit then and tdd today, one reading none (a sed script naming `a/SKILL.md`, a batch grepping tdd's, a batch whose source names `tracker/SKILL.md` but whose nested calls stop at a failed read before it), and one wholly nine days old reading tdd; a code reviewer offered code-review reading tdd. Run `octo-feather-lane report`. Observe exit 0, the block `skill reach (...)`, `  code reviewer (1 session): code-review 0/1; read, not offered: tdd 1`, `  implementer (4 sessions): commit 1/4, tdd 2/4` (no skill `a`, no tracker), and the session files' hashes unchanged.

## Gotchas

- Herdr unreachable prints `unread: Herdr` as the report's last line: expected, the drive reaches no Herdr.
- The lane fields, owner queue and the owner-caught block by class are proven by `tests/gate/kit/test_lane_report.py` with the testkit's gh and herdr; this drive covers the reflection line, the gate budget block, the owner-caught headline and the skill reach block. What counts as offered and as a read: `octo-feather-lane --help` (report).
- Which trend lines count toward the gate budget, and the budget file's form: `octo-feather-lane --help` (report).
