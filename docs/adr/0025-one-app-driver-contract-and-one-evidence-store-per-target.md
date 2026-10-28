# One app-driver contract and one evidence store per target

Each target repository has one app-driver contract, `qc.toml` at its root: structured, versioned data naming how the app is entered, the services it needs and their readiness, its fixtures and their reset, and the values criteria refer to. Its keys follow annotateanything's `qa.toml` where they fit. The file is named for QC because the kit calls control of the product QC (quality spec `#split`). The verify skill (ADR 0009) documents and invokes the contract and never restates its commands.

Evidence has one pipeline: a declared demo is captured deterministically at an exact head into one append-only evidence store per target, outside git in the box's local state, each record tied to the code revision, the criterion's text and the contract and fixture versions; the record format is versioned data in the kit. Agents, qc and the owner read that one store. qc only judges what the store holds; insufficient evidence is a result, and it blocks; a classifier's answer is advisory until it is calibrated against owner labels. Contract and records are local now and plain versioned data, shaped so another agent or box can later exchange them (A2A). The rules: quality spec `#driver-evidence`.

Decided by Tom (owner), 2026-10-26 (issue #136), after review found the verify skill and annotateanything's QA capture each starting the app, holding drive values and keeping evidence their own way.

## Considered options

- Split by reader: the verify skill for agents and qc, annotateanything's QA bundle for the owner, `qa.toml` holding start-up and values. Rejected: two evidence pipelines, and two files a reader must reconcile.
- The verify skill as the only contract, its commands in prose. Rejected: prose is not structured data a deterministic capture or another agent can read.
- Evidence committed to git. Rejected: captured outputs grow with every run and would churn every branch; the record format, not the records, belongs in the repo.

## Consequences

- `just qc` moves onto the contract and store: deterministic capture, judgment over stored evidence only (docs/adr/0022 changes with it).
- Template-born repositories ship a `qc.toml`; a repository the kit did not create gains one with its verify skill.
