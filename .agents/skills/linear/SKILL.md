---
name: linear
description: The tracker skill for a target whose tickets live in Linear; read, file, comment on and finish tickets, and name lane keys, only through its scripts.
---

# Linear tracker

Be extremely concise. No em-dashes or en-dashes. Ever.

The target's tickets live in Linear (`tracker = "linear"` in its
`.octo-feather.toml`; docs/adr/0004). Every lane ticket operation (view,
create, comment, done, lane key, PR line) goes only through the scripts below,
by path: `<this skill's folder>/scripts/<name>`. Each wraps one `linear` CLI
command (schpet/linear-cli), prints only its output, and on failure exits
non-zero with the reason. For any other read, read the vendored `linear-cli`
skill's references by path: `<this skill's folder>/../linear-cli/references/`
(`issue.md` for issues, `api.md` for raw GraphQL). Never write a ticket another
way, and never file a GitHub issue for a Linear target.

A key is the team key and number, `ENG-123`; the lane key is it lowercased.
The `linear` CLI reads its key, `LINEAR_API_KEY`, from the environment that
started the factory (herdr-spawn passes it into every pane), never from a
file: never write it into a file, brief, message, log or pull request.

The CLI is schpet/linear-cli at the release in `cli-version` (v3.1.0, the
vendored `linear-cli` skill's pin). `scripts/install-check`, run by the kit's
`just install-check` for a Linear target, checks `linear --version` against it
and names the install path when missing: the release binary on `PATH` as
`linear`, or a `linear` on `PATH` that runs `npx @schpet/linear-cli@3.1.0`.

| Script | Does | Prints |
| --- | --- | --- |
| `lane-key ID` | Lane key for an issue as the owner writes it (`ENG-123`, `eng-123`, its URL) | `eng-123` |
| `key-from-branch BRANCH` | Parent issue of a lane branch or a worker branch named after it | `ENG-123` |
| `issue-view KEY` | Reads one issue | JSON: `key`, `title`, `body`, `state` (`open` or `done`), `url`, `parent` (key or null), `children` (its sub-issues' keys), `blocked_by` (keys) |
| `issue-create --title T --body-file F\|- [--parent KEY] [--blocked-by KEY]...` | Files an issue (in the parent's team, else the configured team), optionally a sub-issue of a parent and blocked by others | The new key |
| `issue-comment KEY [--body-file F\|-]` | Adds a comment (standard input by default) | The comment's url |
| `issue-done KEY` | Moves the issue to its team's Done (first `completed` state); one already done (completed, canceled or duplicate) stays as it is | Nothing |
| `pr-line KEY` | The line a lane PR body starts with for its parent issue | `Tracks ENG-123` |

Tracker writes are only these: a ticket filed, commented on, and moved to
done. No other state change and no label. Writes need consent (the
`github-pr` skill's Consent section).
