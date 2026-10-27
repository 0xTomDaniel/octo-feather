# Each artifact has one home; behavior changes start in the spec; we fix problems we have seen

This ADR owns the first principles below that no other file owned. Each part another file owns is a pointer here, never a restatement: one owner per fact and a term's owner (docs/adr/0008 rung 1), who builds what and the eval question (docs/adr/0008, Who builds what and its eval paragraph), where a correction goes (docs/adr/0020, Where the fix goes), calibrated advisory judgment (judgment spec `#rule-calibration`, `#rule-advisory`). Decided by Tom (owner), 2026-10-26 (issue #190), as worded here by the director's rulings of 2026-10-27 (ticket #192).

**Where each artifact lives.**

- **Spec** owns behavior, intent, boundaries and protocols. Its format and anchors: docs/adr/0006; its acceptance and later calls: docs/adr/0021. A spec is kept as long as the behavior it states exists, never thrown away after merge; retiring the behavior retires the spec and its status file (docs/future.md, "Status file deleted beside its spec").
- **ADRs** (`docs/adr/`) own decisions and why.
- **Code** owns how.
- **Dependency manifests** own dependencies and their pins: in the kit `Skillfile` and `Skillfile.lock` (AGENTS.md Rules) and `pi-version` (docs/adr/0023 Consequences); in each template its package manifest and lock file (`templates/python/pyproject.toml` and `uv.lock`, `templates/typescript/package.json` and `pnpm-lock.yaml`).
- **Glossary**: GLOSSARY.md (docs/adr/0008 rung 1).
- **Architecture diagrams** of code structure are generated from code when needed, never hand-kept. Figures inside a spec that show behavior or the org (overview `#org-chart`, comms `#escalation`, roles `#herdr-layout`) are spec content, owned and kept by the spec.
- **Plans** (a build plan, a ticket breakdown) are thrown away after use. Before one goes, each lasting line in it has another owner from this list.
- **Tests and evidence** are the link from spec to code: a test or evidence file cites the criterion it proves by its anchor (docs/adr/0006). Mapping each criterion to its tests is issue #127.

**Spec-first change.** A behavior change starts as an accepted spec change, and agents propagate it to code. How a spec is accepted and changed after Accept, and why spec and code never diverge: docs/adr/0021 and issue-lifecycle `#gates-spec-calls`. Code-first fixes are the exception: work whose behavior main's spec already states (docs/adr/0021), and a ticket that serves no criterion and names its rule and owner (issue-lifecycle `#lanes-tickets`).

**Fix problems we have seen.** We fix problems we have actually seen, as evidence over intent (docs/adr/0008, the eval question). The exception is a silent failure whose first occurrence is invisible: it is guarded before it happens. Examples: a forged Accept (docs/adr/0021 Consequences, a registry `accepted` key counts for nothing) and a stranded agent (docs/adr/0023). An idea for a problem not yet seen and not silent goes to docs/future.md.

## Considered options

- Keep `docs/plan.md` as a lasting build plan. Rejected: each of its lasting lines already had another owner (role files for models; docs/adr/0013, 0015, 0016, 0022; comms `#wake-provider-rule`; `Skillfile`, `NOTICE`; the scripts and tests it listed as built), and the rest was the finished 2026-10-18 build.
- A hand-kept architecture diagram of code. Rejected: nothing keeps it in step with the code it draws.
- Guard every imaginable problem up front. Rejected: each guard is prose or a check no incident justifies (docs/adr/0008).

## Consequences

- `docs/plan.md` is deleted; README.md, AGENTS.md and the `herdr-wake` comment point at the live owners instead (issue #192).
