# octo-feather

Lightweight agentic development kit built on octo-lite (`varelaseb/octo-lite`, Apache-2.0): one director over one supervisor per work item, Pi workers in Herdr panes, a spec-chat HTML spec, and a validation gate tight enough that sloppy code cannot land.

This file governs work on the kit itself. Terms (director, supervisor, worker, work item, lane) are defined in [GLOSSARY.md](GLOSSARY.md). Target repos get their own `AGENTS.md` from `templates/`.

## Rules

- Pi is the only agent runtime. No Claude/Codex config, no `CLAUDE.md` (what counts: docs/adr/0001).
- `AGENTS.md` is the only instruction file in any repo the kit touches.
- Agents hand off to each other through Herdr (`.agents/skills/herdr-comms`). No workflow engine, no tracker, no daemon.
- Tests are integration and end-to-end only, driven through public surfaces (app CLI, HTTP, UI; an integration test may also enter through a public library function, docs/adr/0002). No unit tests of internals. A kit test runs a script as a command and feeds it inputs, never loads or reads it; review judges this (docs/adr/0008 rung 3).
- Every template exposes one gate command, `just check`, used identically by agents, git hooks and CI. A red gate blocks handoff.
- Where each artifact lives, spec-first change and fixing only seen problems: docs/adr/0024.
- Fix a lesson on the highest rung of the ladder in docs/adr/0008; only what its rung 2 allows becomes a check.
- Vendored skills are pinned in `Skillfile` and `Skillfile.lock`, materialized into `.agents/skills/`, and changed only through patches in `.skillfile/patches/`. Upstream license and attribution live in `NOTICE`.

## Layout

- `agents/` role files, our frontmatter format read by `scripts/pi-role` (docs/adr/0013): director, supervisor, implementer, code-reviewer, corrector, qc-judge. Integration is a script, not an agent: `just integrate TICKET REF...` (`scripts/octo-feather-integrate`, docs/adr/0017). Every agent launches through `scripts/pi-role`: in a Herdr pane via `herdr-spawn --role`, or headless with `-p`. `.agents/skills/` holds the skillfile-managed upstream skills (mattpocock/skills and pstack; each patch's first line gives its reason).
- `docs/specs/` the kit's Spec Chat HTML specs (`*.spec.html`, index `docs/specs/index.spec.html`), with Spec Chat's runtime and style in `.viz/` and `.style/`. Role contracts cite their anchors as spec `#anchor`; the index maps each anchor to its spec. `docs/adr/` wins where they differ.
- `extensions/` kit Pi extensions, loaded into every role by `scripts/pi-role`: `resume-on-error.ts` (docs/adr/0023). `pi-version` the Pi pin (docs/adr/0023 Consequences).
- `.agents/skills/` every kit skill, vendored (Skillfile `github` entries) or local (docs/adr/0018). Role files stay in `agents/`.
- `templates/python`, `templates/typescript` starter target repos: app CLI with `--json`, integration and E2E tests through it, `just check` (also run by `.githooks/pre-commit` and CI), `just integrate` and `just qc` (both templates define them and `check-templates` enforces it; a repo the kit did not create never gets them, docs/adr/0017), and an `AGENTS.md` with a `Repo skills:` line. Copy one, then `just setup`.
- `scripts/` published commands on every agent's `PATH`: `octo-feather-start` (director or lane workspace), `octo-feather-state` (state dir), `octo-feather-integrate` (`just integrate`), `octo-feather-accepted` (kickoff check: is a spec accepted at an exact commit), `octo-feather-spec-status` (per-criterion status file beside a spec, docs/adr/0021), `octo-feather-qc` (`just qc`), `octo-feather-qa` (`just qa`: each eval case's role run headless in the qc sandbox, PASS/FAIL from transcript facts), `check-evals` (eval case shape, in `just check`), `octo-feather-shape` (`just shape`), `octo-feather-exclude` (keeps Spec Chat review state out of a target's git), `review-host` (Spec Chat's `review-host.py`; `register` refuses a page with no Spec Chat runtime and stops review-serve processes its registry does not own), `octo-feather-lane` (lane bookkeeping: `archive` a closed lane's record, `verdict` posts the PR's review verdict comment, `merge-ask` checks the PR's merge ask, `tickets` checks a parent's tickets through the tracker skill, `done` moves a closed lane's parent and tickets to done).
- `justfile` kit commands: `just check` (the gate), `just install-check`, `just start`, `just supervise TICKET`, `just integrate TICKET REF...`, `just shape` (run in a target repo: the owner's shaping chat, Pi with only the shaping skills, not a factory role), `just state`, `just qc STATUS PR ID...` (interim product judge, docs/adr/0022) and `just qa [--suite S] [--case ID] [--kit-ref COMMIT]` (factory evals; `--kit-ref` runs them against the kit at an earlier commit); neither runs inside `just check`.
- `NOTICE`, `LICENSE` Apache-2.0 attribution for the octo-lite-derived files.
- `docs/kickoff-brief.md` the brief the owner sends the director with `build <spec>` (docs/adr/0021).
- `evals/` factory eval suites (`<suite>/suite.json`, `cases.json`, hidden `reference/expectations.json`) and their `fixtures/`; shape: `scripts/check-evals --help`.
- `docs/adr/` lasting decisions (Matt's ADR format); `docs/future.md` deferred ideas; `docs/owed-evals/<issue>.md` owed eval cases (docs/adr/0008).
