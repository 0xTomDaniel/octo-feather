# QC judge's own role file: skills loaded before and after (issue #67 item 1, ticket #85)

Live smoke of the role change (docs/adr/0008): `scripts/octo-feather-qc` launches the judge from `agents/qc-judge.md` instead of `agents/code-reviewer.md`. Owed eval: docs/owed-evals/67.md.

## Setup

- Kit: worktree on `implementer-gh85`. Before: the launcher as on origin/main (`scripts/octo-feather-qc`, `agents/code-reviewer.md` unchanged on the branch at that point). After: the branch's committed launcher and `agents/qc-judge.md`.
- Target: a fresh copy of `templates/python` at `/tmp/qcj-fixture`, `uv sync`, with `docs/specs/greet.spec.html` holding three criteria and its status file from `octo-feather-spec-status init` (all planned). Two are built in the template CLI. One is not (`app bye` does not exist). No GitHub remote. Both runs judge the same head, e60a11ff9140 (the fixture was reset between runs).
- Probe: a throwaway `pi` wrapper first on the judge's PATH (`OCTO_FEATHER_QC_PATH`, not committed). It logs the model, the role prompt's first line, the `--skill` args and every SKILL.md read to the judge's stderr (kept in the report), runs the real pi with `--mode json`, and prints the final message as `-p` would.
- Box: 5 live Pi, 6.6 GB available. Herdr ids and `OCTO_FEATHER_PARENT` stripped:

```
cd /tmp/qcj-fixture && env -u OCTO_FEATHER_PARENT -u HERDR_PANE_ID -u HERDR_TAB_ID -u HERDR_WORKSPACE_ID \
  -u HERDR_ENV -u HERDR_SESSION -u HERDR_SOCKET_PATH -u HERDR_BIN_PATH OCTO_FEATHER_QC_PATH=/tmp/qcj-probe/bin \
  timeout 1500 <kit>/scripts/octo-feather-qc docs/specs/greet.status.json 1 \
  acceptance-greet-json acceptance-greet-blank acceptance-bye-json
```

Smoke first: the wrapper around `pi-role agents/code-reviewer.md --thinking off -p` on a one-line task, unsandboxed. It printed the probe lines and the right answer, rc 0.

## Before (main's launcher, judge from agents/code-reviewer.md)

Sandboxed, every proof line ok. 34 s, exit 1 (one fail).

```
probe: model ['openai/gpt-6.1-sol', 'openai/gpt-6.1-sol'] thinking ['high'] tools ['read,grep,find,ls,bash']
probe: skills offered ['blast-radius', 'code-review', 'github', 'principle-prove-it-works']
probe: role prompt first line: # Code reviewer
probe: skill read <kit>/.agents/skills/code-review/SKILL.md
probe: skill read <kit>/.agents/skills/principle-prove-it-works/SKILL.md
probe: tool calls 12, pi exit 0
```

The judge read `code-review` even though the brief told it to skip that skill's diff passes.

```
PASS acceptance-greet-json: $ app hello Ada --json
PASS acceptance-greet-blank: $ app hello "" --json
FAIL acceptance-bye-json: $ app bye Ada --json
  The CLI rejects bye; no farewell JSON was printed and the exit code was 2.
qc: 2/3 passed at e60a11ff9140; offline gh refusals 0; head now b749b6625b46
```

## After (this branch, judge from agents/qc-judge.md)

Sandboxed, every proof line ok. 32 s, exit 1 (one fail).

```
probe: model ['openai/gpt-6.1-sol', 'openai/gpt-6.1-sol'] thinking ['high'] tools ['read,grep,find,ls,bash']
probe: skills offered ['principle-prove-it-works']
probe: role prompt first line: # QC judge
probe: skill read <kit>/.agents/skills/principle-prove-it-works/SKILL.md
probe: tool calls 11, pi exit 0
```

Report as printed:

```
PASS acceptance-greet-json: $ PYTHONDONTWRITEBYTECODE=1 .venv/bin/app hello Ada --json; printf 'exit=%s\n' "$?"
  Printed one JSON object whose text greets Ada; exited 0.
PASS acceptance-greet-blank: $ PYTHONDONTWRITEBYTECODE=1 .venv/bin/app hello '' --json; printf 'exit=%s\n' "$?"
  Empty name produced a JSON object with an error field; exited non-zero.
FAIL acceptance-bye-json: $ PYTHONDONTWRITEBYTECODE=1 .venv/bin/app bye Ada --json; printf 'exit=%s\n' "$?"
  CLI rejects bye; no farewell JSON object and exit was 2.
qc: 2/3 passed at e60a11ff9140; offline gh refusals 0; head now f40e3bdbeb0f; report $(octo-feather-state)/qc/e60a11ff...-20261022T190345Z-3531bc.json
```

Outputs from the report: `{"name": "Ada", "text": "Hello, Ada"}` exit 0; `{"error": "name must not be empty"}` exit 2; `app: error: argument command: invalid choice: 'bye' (choose from 'hello')` exit 2. The new head's only change is `docs/specs/greet.status.json` (two criteria built, pr 1; `acceptance-bye-json` planned). The judge wrote nothing (0 overlay writes).

## Result

- Skills offered: 4 before, 1 after (`principle-prove-it-works`, now on the role's skills line instead of a launcher `--skill`). Skills read: code-review and principle-prove-it-works before, only principle-prove-it-works after.
- Same verdicts, same outputs, about the same time (34 s vs 32 s), one tool call fewer.
- Removed: the brief's "product judge, not a code reviewer: skip the code-review skill's diff passes" (nothing to skip now), plus its read-only, no-message, /tmp-scratch and demo-path method lines, which moved to `agents/qc-judge.md`. Also removed the launcher's extra `--skill principle-prove-it-works`, and code-reviewer.md's QC-run output sentence.
