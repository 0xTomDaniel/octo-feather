# A lane is one merge ask; tickets are vertical tracer bullets; pilot first

One supervisor is one lane is one merge ask is one parent GitHub issue, filed by the director; the supervisor's tickets are sub-issues of that parent, with `Blocked by` only where order matters. The director cuts lanes from the accepted spec: usually one spec is one lane, a big spec whose outcomes can merge independently becomes several, several small coupled specs become one, and code that must change together stays with one owner (pstack poteto-mode `playbooks/feature.md`). There is no numeric tripwire or ticket cap; the director judges size by Matt's `to-tickets` (tracer bullets, "what can I demo when this is done?") and pstack orchestrate (add a coordinator per track only when one cannot drain the work). A supervisor that finds outcomes that would merge separately escalates it as a changed ship grouping. The supervisor decides ticket count, order, cuts and the worker split, but every ticket is a vertical tracer bullet: a thin path through every layer, ending on a demo path through the app CLI, HTTP or UI, or the target's runnable script when it has none (ADR 0002, 0009), naming the acceptance criteria it serves. A layer-only ticket is never allowed, except `to-tickets`' wide-refactor expand-contract sequence. The lane's first ticket is a pilot: it runs alone through brief, one implementer, `just integrate`, `just qc` and code review (pstack orchestrate's Pilot step) and is the lane's tracer bullet; the supervisor then fixes its brief template, re-cuts the remaining tickets and fans out. Decided by Tom (owner), 2026-10-19.

## Considered options

- A ticket cap or numeric lane-size tripwire. Rejected as too prescriptive: size is a judgement the referenced guidance already frames.
- Fan out every ticket at once. Rejected: a bad brief, verify recipe or ticket size then fails in every worker at once, not in one.

## Consequences

- `agents/director.md` holds lane cutting and the parent issue; `agents/supervisor.md` holds Delivery and the Briefs ACCEPTANCE line; the implement-spec patch runs the pilot before step 4's fan-out.
