# octo-feather

Lightweight agentic development kit built on octo-lite (`varelaseb/octo-lite`, Apache-2.0): one director over one supervisor per work item, Pi workers in Herdr panes, a spec-chat HTML spec, and a validation gate tight enough that sloppy code cannot land.

This file governs work on the kit itself. Terms (director, supervisor, worker, work item, lane) are defined in [GLOSSARY.md](GLOSSARY.md). Target repos get their own `AGENTS.md` from `templates/`.

Repo skills: verify-octo-feather, typescript, python

## Rules

- Pi is the only agent runtime. No Claude/Codex config, no `CLAUDE.md` (what counts: docs/adr/0001).
- `AGENTS.md` is the only instruction file in any repo the kit touches.
- Agents hand off to each other through Herdr (`.agents/skills/herdr-comms`). No workflow engine, no tracker, no daemon.
- Tests are integration and end-to-end only; no unit tests of internals (docs/adr/0002, quality spec `#acceptance-public-surfaces`). An integration test drives the interface of a deep module with a stable interface, public or internal, at a seam written down from the ticket's criteria before any test; both are hard requirements, never a private helper or a shallow wrapper. No such seam: deepen the product code first, as its own step. End-to-end tests and QC/QA demos drive only a public interface the product offers its users (its CLI, HTTP, UI, MCP or another public protocol): a kit end-to-end test or demo runs a script as a command and feeds it inputs, never loads or reads it; review judges this (docs/adr/0008 rung 3).
- The kit and every template have a gate of two tiers, `just fast` and `just check`: what each runs and who runs it, quality spec `#recipes-table` (templates spec `#tpl-gate`, `#tpl-hooks`); when a lane runs the full tier, issue-lifecycle spec `#lanes-checkpoints`; the one a hand-off needs green, quality spec `#acceptance-gate-green`.
- Where each artifact lives, spec-first change and fixing only seen problems: docs/adr/0024.
- Shell is for thin glue: calling commands, environment setup, mounts. Logic, parsing and rules go in Python.
- Every kit mechanism is built for any target repo; a kit-only piece states why.
- The ladder: docs/adr/0008.
- Vendored skills are pinned in `Skillfile` and `Skillfile.lock`, materialized into `.agents/skills/`, and changed only through patches in `.skillfile/patches/`. Upstream license and attribution live in `NOTICE`.
- Infrastructure (what counts, what fits, and the `Prior art:` line that reports the choice: the `code-review` skill, Verdict step, **Prior art**) comes from a popular, well-maintained, pinned library or the real tool. A library that is broken is patched in place with a committed patch, as the kit patches vendored skills (`Skillfile`, `.skillfile/patches/`), never replaced with a hand-written one. Hand-writing one needs its reason stated where it lives (a comment, the spec). Ask the tool itself (`just --summary`, `--help`, `--json` output) rather than modelling its command line. The kit's own scripts stay Python-stdlib-only where the standard library covers the job (`tomllib`, `json`, `argparse`): that is their stated reason, and it holds for kit scripts only, never templates or products. Failure examples: a hand-written TOML parser in templates/typescript (`toml.ts`, #136; smol-toml exists), a custom test runner with its own timing (#204, replaced by pytest + pytest-xdist), hand-written ECMA regex and Markdown parsers (#121, three review rounds until the real engines).

## Layout

- `agents/` role files; frontmatter and launcher: `scripts/pi-role` (docs/adr/0013). Role launch details: `scripts/pi-role --help`.
- `docs/specs/` the kit's Spec Chat HTML specs (`*.spec.html`, index `docs/specs/index.spec.html`), with Spec Chat's runtime and style in `.viz/` and `.style/`. Role contracts cite their anchors as spec `#anchor`; the index maps each anchor to its spec. `docs/adr/` wins where they differ.
- `reflection/questions.json` the reflection question list (comms spec `#reflection-questions`); `agents/reflector.md` owns the reflector role.
- `extensions/` kit Pi extensions; loading and web configuration: `scripts/pi-role`, `web-mcp.json` (docs/specs/roles.spec.html#launch-web). `pi-version` the Pi pin (docs/adr/0023 Consequences); `mise.toml`, `mise.lock`, `mise-version` the native tool pins.
- `.agents/skills/` every kit skill, vendored (`Skillfile` github entries) or local (docs/adr/0018). Vendored sources and pins: `Skillfile`, `Skillfile.lock`; patches: `.skillfile/patches/`. Role files stay in `agents/`.
- `.agents/skills/verify-octo-feather/` the kit's own verify skill (quality spec `#verify-skill-what`); its feature map in `features/`. `qc.toml` the kit's driver contract (quality spec `#qc-contract`).
- `templates/python`, `templates/typescript` starter target repos; each template's `AGENTS.md` describes its layout. Dependency owners: Python's `pyproject.toml` and `uv.lock`, TypeScript's `package.json` and `pnpm-lock.yaml`.
- `scripts/` published commands on every agent's `PATH`; each script owns its command details: read its source, and its `--help` where supported.
- `justfile` owns kit recipes, listed by `just --list`; `just fast` and `just check` are the gate's tiers (quality spec `#recipes-table`). Gate runner: `tests/gate/`; dependencies and pins: `pyproject.toml`, `uv.lock`.
- `tests/` the kit's tests: `tests/*.sh`, and pytest kit tests in `tests/gate/kit/` (how each is a gate item: `scripts/octo-feather-gate --help`, select; their shared stand-ins, scratch dirs, fixture loading and scenario runner: `tests/gate/kit/testkit/`, its docstring). `tests/parity/` the parity lever a rewritten test is proved by (`tests/parity/lever.py --help`).
- `NOTICE`, `LICENSE` Apache-2.0 attribution for the octo-lite-derived files.
- `docs/kickoff-brief.md` the brief the owner sends the director with `build <spec>` (docs/adr/0021).
- `evals/` factory eval suites (`<suite>/suite.json`, `cases.json`, hidden `reference/expectations.json`) and their `fixtures/`; shape: `scripts/check-evals --help`.
- `docs/adr/` ADRs, Matt's format (what they own: docs/specs/index.spec.html `#context`); `docs/future.md` deferred ideas; `docs/owed-evals/<issue>.md` owed eval cases (docs/adr/0008).
