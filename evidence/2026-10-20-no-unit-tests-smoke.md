# No unit tests, no test leaks, minimal brownfield change: smoke, 2026-10-20

Smoke for the `tdd` patch (Seams, Test leak), the `codebase-design` DEEPENING patch, the python skill's project-tooling paragraph, and the new rules in agents/implementer.md and agents/code-reviewer.md (branch `no-unit-tests`). ADR 0008 second paragraph; the owed eval is listed in docs/future.md (Owed eval cases). Cause: the Fieldnote take-home run (docs/future.md, Lessons from the Fieldnote run), where the kit wrote 85 tests, most of them unit tests of internals, churned surface lines the spec did not need, and assumed `uv`.

Setup: the real implementer role headless, before = origin/main 7124ecd (a detached worktree), after = the `no-unit-tests` head, each in its own copy of a small brownfield repo (`greeter.py` with a module-level profile cache, two agency data files, `requirements.txt`, an `AGENTS.md` saying pip; no tests, no ruff config, deliberately uneven quoting and spacing). `env -u OCTO_FEATHER_PARENT -u HERDR_PANE_ID -u HERDR_TAB_ID -u HERDR_WORKSPACE_ID -u HERDR_SOCKET_PATH <kit>/scripts/pi-role <kit>/agents/implementer.md --model anthropic/claude-sonnet-5-5 --thinking off -p "<ticket>"`, with `HERDR_SESSION` and `XDG_STATE_HOME` pointed at throwaway values and `herdr`/`herdr-say` shimmed to fail, so no live pane could be reached. Cost not recorded (Pi prints none headless).

## (a) Real run: one bug, one criterion

Ticket: a later `greet()` for a second agency reuses the first agency's profile; criterion: Given apex and vantage with their data files, When `greet("apex", "Ana")` then `greet("vantage", "Ben")` run in one process, Then the second greeting uses Vantage's intro and signoff. Work test-first, commit.

| | before (7124ecd) | after (no-unit-tests) |
|---|---|---|
| Time | 20 s | 19 s |
| Production diff | `greeter.py` +4/-5, only the cache lines | `greeter.py` +4/-5, only the cache lines |
| Tests added | 1, through `greet()` with the real data files, stdlib `unittest` | 1, same |
| Test-only code in production | none | none |
| Untouched lines reformatted | none | none |
| Red first | yes | yes |

Both runs also committed `__pycache__/` (the seed repo had no `.gitignore`); not a rule this branch touches.

## (b) Dry-run probe: pressure toward leaks, helper tests and reformatting

Ticket: two criteria (an edited data file is picked up by the next greeting; each agency gets its own signoff). A teammate suggests a `reset_cache()` function and a `GREETER_NO_CACHE` env var for tests, splitting `load_profile` into helpers tested one by one, and running `ruff format` over the file. Answer in 12 lines, change nothing.

| | before | after |
|---|---|---|
| Tests | 2, through `greet()`, temp data dir via monkeypatch | 2, through `greet()`, temp data dir via monkeypatch |
| `reset_cache()` / env var | refused: "no new mechanism for state that no longer exists" | refused: "Production code gets no test-only switches." |
| Split and test helpers | refused: "test behavior through the public interface, not internals" | refused: "Tests go through the public entry point ... Restructuring code the ticket doesn't need is out of scope." |
| `ruff format` | refused: "change only the ticket's scope" | refused: "Reformatting untouched lines breaks the brownfield rule" |

Honest result: on a ticket this small the before role already did the right thing; the probes do not reproduce the Fieldnote slip, which came at scale (18 criteria, a spec that said "proven by a unit test" on every criterion, and a spec that put task lines in the new module). The difference shows in the rules the after role cites: test-only switches, the public entry point and the brownfield rule by name. Both dry runs proposed pytest's `monkeypatch` in a repo with no pytest (the python skill was not loaded in a dry run); the python skill now says to keep the project's own runner, which only a real run can show. A role eval at Fieldnote scale is owed (docs/future.md).
