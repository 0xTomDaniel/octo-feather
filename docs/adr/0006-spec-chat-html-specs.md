# Specs are spec-chat HTML

Canonical specs are `*.spec.html` documents reviewed in spec-chat's browser loop, with no Markdown counterpart; Markdown stays for agent instructions and ADRs. Tom already works this way, and stable anchors let tickets, tests and evidence cite exact criteria. Decided by Tom, 2026-10-18.

Acceptance criteria inside a spec are Gherkin scenarios (Given / When / Then), so a driver can perform the Whens and a separate judge can check the Thens (borrowed from annotateanything). Tom, 2026-10-18.

## Considered options

- Markdown specs (Exo's proposal). Rejected: no review loop and no stable anchors.
