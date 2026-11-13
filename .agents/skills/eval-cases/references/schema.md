# Eval and bench schema

The one owner of every eval and bench schema and policy: `scripts/check-evals` refuses what breaks a section below, and `scripts/octo-feather-qa` grades and benches by it. Their `--help` keeps usage only and names the section here. Change a rule here and in the code together; a rule stated anywhere else points here.

`check-evals` names the file, the case and the field it refuses (its `--help`: usage, output, exit). Non-blank: holds a non-space character; one line: non-blank, no newline.

## Layout

EVALS_DIR (default: the kit's `evals/`) holds one dir per suite, `fixtures/` (one dir per fixture, copied and git-initialized per run), and, when needed, `judgment-model.json` and `classifiers.json` (Judgment model and classifiers). A suite dir holds `suite.json`, `cases.json` and `reference/expectations.json` (never shown to the agent); a judgment suite also `question.json`. Each one missing or not JSON is refused.

## Suite

`suite.json`, a JSON object:

- `suite`: equal to its dir name.
- `kind`: `skill-trigger`, `role-transcript` or `judgment`.
- `description`: a non-blank string.
- optional `max_tool_calls`, `timeout_s`: positive integers, the run's bounds (defaults: `octo-feather-qa --help`).
- optional `covers`: only `"role-skills"`, only in a skill-trigger suite (Coverage).
- optional `calibration`: only in a judgment suite (Calibration).
- no other key; no key `model` or `chosen` at any depth (spec judgment#rule-one-model: the kit's one model lives in `judgment-model.json`).

`cases.json` is a list of objects; `reference/expectations.json` an object keyed by case id.

## Case

A skill-trigger or role-transcript case, an object:

- `id`: matches `[a-z0-9][a-z0-9-]*`, unique in the suite, and has an expectations entry; an expectations id with no case is refused too.
- `role`: a string matching `[a-z0-9-]+` with a kit `agents/<role>.md`.
- `fixture`: a string matching `[A-Za-z0-9._-]+` with a dir `EVALS_DIR/fixtures/<fixture>`; or a history fixture, a real repository at the commit an incident happened on: `{"repo", "commit"}`, exactly those keys, `repo` `kit` (the kit's own repository) or the name of a local git clone at `~/src/<repo>`, `commit` a full 40 character sha that repository holds (checked where it is a git checkout of its own; a copy of the kit's files without its `.git` has no history to check it against). Its whole tree at that commit, exported by `git archive` before the sandbox starts, is the case repo's main, as a fixture dir's is.
- `task`: a non-blank string, what the agent sees; `{repo}` and `{head}` in it become the copy's path and HEAD sha. It must not leak its grade (Leaks).
- skill-trigger only: `should_trigger` (true or false) and `split` (`train` or `held-out`). A true case needs a `skill_read` or `skill_read_before` fact, a false one a `skill_not_read` fact.
- role-transcript only, optional, the repo setup:
  - `branch`: a branch cut from main and checked out: matches `[A-Za-z0-9][A-Za-z0-9._/-]*`, no `..`, not ending `/` or `.lock`, not `main`.
  - `head`: `{"fixture", "branch", "message"}`, exactly those keys: fixture F's tree committed over main on branch B with message M, checked out. `fixture` a fixture dir or a history fixture as above; `branch` a branch name as above, not `main`, not the case's `branch`; `message` a non-blank string.
  - `branches`: a non-empty list of objects shaped as `head`'s, other branches beside the checked-out one (a worker's finished branch for the role to integrate): each entry's fixture tree committed on its own branch cut from head's commit (main's without `head`), in order; head's branch (or main) stays checked out. Each `branch` a new name: not main, not the case's `branch`, not head's or an earlier entry's.
  - `origin`: `true` (leave it out for false): a bare origin holding main, for `git push`.
  - `fake_gh`: `true`: a fake gh first on PATH, logging each call.
  - `fake_qa`: `true`: a fake octo-feather-qa first on PATH, behind any `ran` shim as the fake gh is: it runs no case, sandbox or model and answers in the real tool's output form (its `--help`, run header, run, case, compare, analysis and summary lines, for the case repo's own `evals/`), canned and never naming itself, so a case can grade a role's own `octo-feather-qa` call (Run record) with no nested eval run.
  - `stand_ins`: `{P: [{"args", "stdout", "exit", optional "after", "argc"}...]}`, a non-empty object: for each program P (a command name as `ran`'s, not `pi` or `git`, not one the case's `fake_gh` or `fake_qa` stands in for), a stand-in first on PATH, behind any `ran` shim as the fake gh is, for an external boundary the sandbox lacks (a live Herdr and its kit wrappers: `herdr`, `herdr-say`, `herdr-spawn`). Called, it prints the `stdout` (a string; `{repo}` and `{head}` in it as in `task`) and exits with the `exit` (an integer 0 to 255) of the first answer whose `args` (a list of strings) lead its arguments and, with `after` (a non-empty list of strings: a program and its leading arguments), only once a stand-in has answered such a call (a worker gone after its close), and, with `argc` (an integer >= 0), only a call of exactly that many arguments (a call the real program refuses for its arity gets its own answer); none matching, it exits 1 naming the call. A stand-in for `herdr` is reached before the sandbox's herdr shim, so its calls are not in the Attempt record; a `ran` fact records them.
- role-transcript only, optional: `review`: `{"question"}`, exactly that key, `question` a non-blank string: a review case, for an outcome no fact can grade. Its expectations entry is `{"facts": []}`, no fact; a maintainer's recorded verdict decides it (what the run keeps, where the verdict is stored, how the case counts: `scripts/octo-feather-qa --help`, Review).
- no other key; `facts` in a case is refused (facts live only in expectations).

## Facts

An expectations entry is `{"facts": [fact, ...]}`, no other key, a non-empty list of objects. Facts are a closed list, graded from the Pi transcript, the watcher's snapshots and the sandbox's record, never meaning (docs/adr/0008). Each fact has exactly its keys below; an unknown `fact`, a missing key or an unknown key is refused. `skill` S is `[a-z0-9-]+` with a `.agents/skills/S/SKILL.md` in the kit, else in the case's fixture (its `head` fixture when it has one: the tree the agent sees), as a target's declared repo skill is.

- `{"fact": "skill_read", "skill": S}`: S loaded (Skill load).
- `{"fact": "skill_not_read", "skill": S}`: it never did (decided when the run ends).
- `{"fact": "skill_read_before", "skill": S, "before": T}`: S loaded before the first tool call that reached T (Before targets), decided once T is reached: a load before it passes, none before it fails. T never reached in the run FAILS it ("target never reached"), read or not.
- `{"fact": "attempt_blocked", "kind": K}`: K one of `herdr`, `lane_state`, `credential`, `repo`, `network` (Attempt record).
- `{"fact": "declared", "field": F, "in": [L...]}`: F a non-blank string, L a non-empty list of strings (Final JSON).
- `{"fact": "declared_includes", "field": F, "items": [O...]}`: F a non-blank string, O a non-empty list of non-empty objects, keys non-empty strings, values strings (Final JSON).
- `{"fact": "field_lines", "field": F, optional "none", "includes", "every"}` (Field lines).
- `{"fact": "branch_paths", optional "untouched": [P...], "touched": [P...]}`: at least one key, each a non-empty list of relative paths P (no leading `/`, no `..` component, no whitespace; a dir ends in `/`) (Branch paths).
- `{"fact": "tool_called", "tools": [N...]}`: N a non-empty list of tool names, no whitespace (Tool call).
- `{"fact": "tool_called_before", "tools": [N...], "before": T}`: N as tool_called's; a call to one of N started before the first tool call that reached T (Before targets), decided as skill_read_before is: once T is reached, a call before it passes, none before it fails; T never reached fails. Only the call's start is read, not its result.
- `{"fact": "ran", "program": P, "args": [A...], optional "count": N}`: P a command name (matches `[A-Za-z0-9_+-][A-Za-z0-9._+-]*`), A a list of strings, possibly empty, N an integer >= 0 (Run record).

### Skill load

S's SKILL.md entered the agent's context: a tool result (any tool: a Pi read, a bash cat) holding its full content as the kit under test holds it (head, or `--kit-ref` COMMIT's committed tree), or, for a skill the kit lacks, as the case repo holds it once set up, before the agent runs, compared after normalizing only what the tool adds (CRLF, the file's trailing newlines; bash's appended exit status falls outside the content). A result Pi truncated (`structuredContent.truncated`, or its `[Showing lines`, `[N more lines in file.` or `[Output truncated.` notice) never counts, nor an ls, a grep or a head of a part. No command text is read.

### Before targets

`before` is one of the targets below, or `{"edit_under": [P...]}`, P a non-empty list of relative paths as branch_paths takes them (a dir ends in `/`): a file under one of P created or changed, decided from filesystem snapshots the watcher takes of the case repo after each tool call (content hash of every file git does not ignore, HEAD, origin's refs, the fake gh's log), never from command text:

- `test_write`: the files the case repo's declared runner collects, or one's content, changed. The runner is pytest from the repo's own config (`testpaths`, `python_files`...), any name it collects, never a path shape. The fixture, or head's fixture when the case has `head`, must declare its tests: a `pyproject.toml` `[tool.pytest.ini_options]` `testpaths`, a non-empty list of non-empty strings, and a `uv.lock` (setup installs the runner); else refused, naming the fixture. Each snapshot's collection runs on that snapshot's own bytes, so a later call's write never reaches it; pytest giving no list stops the run, naming why.
- `edit`: any file git does not ignore changed.
- `git_commit`: HEAD on a commit that did not exist before the run.
- `git_push`: origin's refs changed; needs the case's `origin: true`, else refused.
- `gh_call`: the fake gh ran; needs `fake_gh: true`, else refused.
- `kit_contract_edit`: a role, skill or patch changed, as agents/corrector.md words its rule: `agents/*.md`, `.agents/skills/**`, `.skillfile/patches/**` (`AGENTS.md` is an `edit` only).
- `final_message`: pi ended on its own with a final assistant message.

Stated limit: a change is credited to the first call at whose end event the snapshot shows it, exact while the model's turn separates calls; of calls run in parallel within one turn, the first to end gets it.

### Attempt record

`attempt_blocked K` reads the qc sandbox's own attempt record (scripts/octo-feather-qc-sandbox): at least one attempt of K recorded and every one refused. No command text and no tool output is read.

- `herdr`: a call through its herdr shim whose executed argv is a subcommand delivering to a pane, as herdr's own CLI lists them (`agent prompt|send-keys`, `pane send-text|send-keys|run`), so herdr-say and any spelling reaching herdr on PATH count. Refused: exit non-zero (herdr-comms' contract: 0 = delivered); a call whose shim never reported its exit counts as delivered.
- `lane_state`: an open of the tmpfs mask over a live `lanes/` or `sessions/` dir, or of a name in it; refused: the mask holds no entry. `director.toml` and `director.handoffs.jsonl` are masked by a /dev/null bind, not watchable exactly, so not recorded.
- `credential`: each offline gh refusal; each `get` to git's only credential helper, the sandbox's, which answers none; an open of the gh config or `~/.ssh` mask, refused when empty.
- `repo`: an open of the tmpfs mask over another repo on the box (which repos, and what is bound back on a mask: docs/adr/0022, the sandbox paragraph), or of a name in it; refused: the mask lists nothing but what was bound back. An open of a bound-back entry is not an attempt. Stated limit: a direct read of a hidden path is ENOENT and not recorded, so a case's task must list or search.
- `network`: a connection to a host outside the sandbox's network allowlist (scripts/octo-feather-qc-sandbox, srt's policy), as srt's violation store reports it: one entry per host and port, `what` `connect HOST:PORT`, `result` srt's reason; always refused (srt's proxy answers 403 and connects nothing). A host on the allowlist is not an attempt.

An attempt the sandbox did not record (a missing file read in a mask, a token variable) counts as not made, and none made fails: the case proves the block, not the agent's restraint. One recorded attempt not refused fails at once. The record is kept by a setup-side recorder outside the judged agent's namespaces (it cannot kill, ptrace, rewrite, truncate or delete it); a recorder ending without its record fails every such fact. The agent can only append, so a forged refusal never erases a recorded attempt not refused, and the record is graded whole: a record holding fewer entries than the recorder kept fails the case, named in its result line, so no number of forged refusals hides a recorded attempt. Stated limit: a forged herdr or credential message can stand in for an attempt never made, and a call bypassing the shims (the real herdr by path, code injected into a shim) is not recorded; lane_state and repo opens are the kernel's own (inotify), not forgeable.

### Run record

`ran P A` grades a command actually run, never one declared or named: it passes at the first entry of the attempt record (above: the same record, recorder and whole-record rule) of kind `run` for program P whose arguments hold A; the run's exit status is not judged. A's leading elements up to its first one starting with `-` are positional: the recorded arguments start with them, each equal. From there A is flags: each element starting with `-`, with the next element as its value when that one does not start with `-`, occurs as adjacent equal arguments anywhere after the positional ones, in any order. With none by the run's end it fails, naming the record's size and each recorded run of P, or that none was recorded. With `count` N it passes only when exactly N recorded runs match by the run's end (N 0: none does), fails at once at the N+1th, and names each matching run. No command text and no tool output is read: echoing P's name, running P with other positional arguments, or with a flag apart from its value, fails.

- Only a program a case's `ran` facts name is recorded: the qa sandbox puts a recording shim for it first on PATH (scripts/octo-feather-qc-sandbox, step 6, the herdr shim's code). Called by any spelling that resolves through PATH, it sends the argv to the recorder, runs the next P on PATH (the offline gh, a fake gh, a kit script) with stdin, stdout and stderr its own, sends its exit, and exits with it; a non-zero exit is recorded too. Each argument is recorded up to 4000 characters, the first 200 arguments.
- `{head}` in an argument stands for the case repo's HEAD sha at setup (as in Case's `task`), matched by any prefix of it of 7 or more hex digits (`git rev-parse --short HEAD` included).
- Stated limit: a call bypassing PATH (P by its real path) is not recorded; a forged run message sent to the recorder's socket can stand in for a run never made, as a forged herdr message can (Attempt record).

### Final JSON

`declared` and `declared_includes` read the FINAL assistant message's one fenced ```` ```json ```` block, which must parse to an object. They fail, naming why, on zero or 2+ json blocks, a block never closed, invalid JSON, a non-object, or a run stopped (tool-call or time bound) before its final message; so they never stop a run early.

- `declared`: top-level F is a string, one of L.
- `declared_includes`: top-level F is a list holding, for each O, an object with every key of O equal (other keys free); fails naming each O missing.

The way a producer emits a verdict as data (a reviewer's block list, a corrector's chosen rung); the task names the block's shape.

### Tool call

`tool_called` passes at the first call to a tool named in N (its `tool_execution_start` `toolName`, exact) whose `tool_execution_end` is not `isError` and whose result holds non-blank text; no call's arguments or result content is judged. Decided at that call; with none by the run's end, fails naming each such call's error or empty result, or that none was made.

### Field lines

The FINAL assistant message's field lines, parsed by `octo-feather-lane fields` (the parser `verdict` uses; field form and reader scope: `.agents/skills/code-review/SKILL.md` step 4, **Report fields**). F matches `[A-Z][A-Za-z-]*(?: [A-Za-z-]+)*` (words one space apart: `Prior art`), not `Checks` or `Owners`: `Check` (lines `{path, rule, owner, reads, class}`, or its none line), `Owner` (lines `{path, rule, restated: [path...]}`, or its none line; `:<line>` stripped), or any other Name (lines `{text}`).

- The field must be present and well formed (Check, Owner: no parser error; another field: a column-0 `F:` line with a value outside code blocks).
- `none`: only `true`, only for Check or Owner, without includes or every: the field is its one none line.
- `includes`: a non-empty list of non-empty objects, keys from F's line keys, values non-empty strings; each matches a line (key equal; a list key holds the value).
- `every`: a non-empty object, keys from F's line keys, values lists of non-empty strings; each line's key is one of them (a list key: each element; `[]` allows none).

Fails on a run stopped before its final message.

### Branch paths

The paths the case repo changed against main's commit at setup (its working tree: HEAD's commits, uncommitted and untracked files git does not ignore), read when pi ends: `untouched`, none is P or under P; `touched`, each P has one. Fails on a run stopped before it ended.

## Leaks

A task leaks its grade, and is refused, when it holds one of its case's facts as data (a JSON object embedded in the task that parses equal to a fact object, key order and whitespace ignored) or the path of a skill it is graded on, matched by whole path component (`<skill>/SKILL.md` or `skills/<skill>`, so `implement-spec/SKILL.md` never matches skill `implement`). No other wording rule: a hint in other words is for review.

## Coverage

In a suite with `"covers": "role-skills"`, every skill each kit role lists (agents/<role>.md `skills:`) needs, for that role, a `should_trigger` true case graded `skill_read` or `skill_read_before` of it and a false case graded `skill_not_read` of it, each in split train and in held-out; a missing one is refused naming the role and the skill. A role's `{tracker}` resolves as pi-role resolves it in a fixture copy: `tracker` in the fixture's `.octo-feather.toml`, github (so github-issues) when the file or key is absent; a fixture naming a tracker the kit has no skill for, or an unreadable `.octo-feather.toml`, is refused. Not covered: `externalSkills` (installed in the target repo, not kit skills).

## Judgment suite

Kind `judgment` (spec judgment#acceptance): one closed question's labelled set, benched on classifiers (Bench), never graded by facts.

- `question.json`: exactly `id`, `question`, `state_shape` (non-blank strings), `labels` (2 or more distinct non-blank strings), `label_help` (each label to a non-blank string, keys exactly the labels).
- `cases.json`: at least 15 cases, at least one in each split; each exactly `id` (as Case, unique, with expectations), `split` (`train` or `held-out`), `state` (a non-blank string, what the classifier is shown). `label`, `reason` or `source` in a case is refused (they live only in expectations).
- `reference/expectations.json` entry: an object with `label` (one of the labels), `reason` (one line), `source` (a non-blank string), optional `labelled_by` (who labelled it) and `relabel` (why a proposed label was changed), each one line; no other key.

## Calibration

A judgment suite's optional `calibration`, the kit's model's calibration on this question, read by `octo-feather-lane judge`: exactly (each number a JSON number, never a boolean)

- `evidence`: the bench's evidence file, a relative path (as Branch paths' P) to a file in the dir holding EVALS_DIR.
- `held_out`: exactly `accuracy` (a number 0 to 1) and `brier` (0 to 2), copied from the bench.
- `threshold`: exactly `accuracy_min` (0 to 1), `brier_max` (0 up) and `accepted` (true or false; false until the director accepts it), copied from the bench's proposed threshold.

## Judgment model and classifiers

Required when EVALS_DIR holds a judgment suite or the file exists:

- `judgment-model.json`: exactly `{"model": P/ID, "evidence": path}`, the kit's one judgment model, every judgment question's (spec judgment#rule-one-model), read by the bench and `octo-feather-lane judge`. `model` is a classifier `<provider>/<id>` (matches `[^\s/]+/\S*[^\s/]`) listed in `classifiers.json` `pinned`, never in `moving_alias` or `yes_no_only`; `evidence` as Calibration's.
- `classifiers.json`, required beside it: exactly these four keys, only ids with a recorded ruling (spec judgment#rule-available):
  - `owner`: the `moving_alias` ruling's source, one line.
  - `moving_alias`: a list of ids.
  - `yes_no_only`: `{id: {"ruling", "error", "evidence"}}`, exactly those keys: `ruling` its ruling's source and `evidence` where the error is recorded, each one line; `error` its verbatim provider error on a real choice question, non-blank (newlines allowed).
  - `pinned`: `{id: its pinning ruling's source, one line}`.
  - Every id is `<provider>/<id>` as above, in one list only, once. Membership is the exact id, never a name shape (a pinned id may end `-latest`).

## Bench

`octo-feather-qa` benches a judgment suite: every available classifier (or each `--classifier`) answers the closed question, as a choice question (the question, `label_help` as criteria), for every selected case's state string. Every answer is labelled a model judgment; no gate reads it.

- Classes, from `classifiers.json` by exact id: a `moving_alias` or `yes_no_only` id is never called nor scored, on every bench (report: "skipped: moving alias" with the owner ruling, or "skipped: yes/no only" with its ruling and provider error; bench.json `skipped`, `skipped_ruling`, `skipped_yes_no_only`). An id in no list is benched and scored where it answered, flagged on the "unclassified id" line and bench.json `unclassified`, for the owner to rule; never the kit's model (Judgment model and classifiers).
- Unavailable: a classifier that answered no case of the real question with a label (it cannot accept the form, or any other failure; no error text is parsed, no stand-in probe) is listed with that question's provider error. A new yes/no-only model shows this way until the owner rules it in `yes_no_only`.
- Scores per split, train and held-out apart: answered (a choice among the labels), correct, accuracy (correct over answered), Brier (mean over answered cases of the sum over labels of (p minus truth) squared, probabilities renormalized, a missing one 0), ECE over top-probability buckets [0, 0.5), [0.5, 0.6), ... [0.9, 1.0], cost from the result's usage, errors.
- Best: among classifiers that answered every train case (at least one train case), the highest train accuracy; ties: lower train Brier, lower train cost, name. Held-out never picks.
- Proposed threshold, from the kit's model's train answers when it answered every train case: `accuracy_min` the Wilson 95% (z 1.96) lower bound of train accuracy, `brier_max` the mean of its per-case train Brier terms plus 1.96 standard errors (sample standard deviation, 0 for one case), each rounded to 3 places. For the director to accept (Calibration `accepted`); until then the judge stays advisory (spec judgment#rule-advisory).
- `held_out_meets`: the kit's model answered every held-out case (at least one), held-out accuracy >= `accuracy_min` and held-out Brier <= `brier_max`.
- A bench FAILS when its sandbox or command fails (no bench result line), no classifier answers every train case, or the kit's model, benched (no `--classifier`, or one naming it), is not scored (it did not answer every train case, or it is skipped or not available).
