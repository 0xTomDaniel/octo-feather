---
name: verify-octo-feather
description: "Drive the octo-feather kit's own commands (just new-repo, just install-check, octo-feather-contract, octo-feather-evidence, octo-feather-lane archive, octo-feather-lane report, pi-role --json, just qc on a scratch target and its merge-ask, a browser demo's headless shell inside it, its agent fallback for a criterion with no demo, its advisory model judgment with the classifier stubbed, octo-feather-spec-status show naming a built criterion stale, octo-feather-integrate's gate tiers on a scratch lane and just fast on a kit copy, merge-ask refusing a lane head with no recorded full gate pass a brownfield target's own gate run in full, a template-born repo's just fast, just check and git hook, the factory report's and the merge ask's gate time against a gate-time budget: short-lived CLIs, no server) the way an owner or agent runs them, in scratch only, and keep the proof in the kit's evidence store. Use to prove a change to a kit command works before handoff, to check a kit criterion's behavior, or when a kit command looks off."
---

# verify-octo-feather

The kit is a target of its own lanes (quality spec `#verify-skill-what`). Its user surface is its commands: the `just` recipes in the kit's `justfile` and the published commands in `scripts/`, each a short-lived process. There is no server, browser or interactive mode. The helper runs each command on the real user path, through the contract's entry, as a subprocess, in its own empty working directory, against scratch only: new repos, scratch targets and scratch state live in the run state folder, and no drive reaches a live lane, Herdr, `gh` or the network. The one exception: a command whose behaviour is a role's model run (the `lane-archive` drive's `reflect-live`, the real reflector) reaches the deployment's model, nothing else; that case fails when the model is unreachable. A drive whose command may file a tracker issue (a reflection's correction lane) runs with the tracker faked: the kit's offline gh (`tests/fixtures/tracker-gh`) first on PATH, its store in the scratch. A drive whose report reads GitHub (factory-report's gate budget case) runs the kit's fake gh (`tests/fixtures/lane-report/gh`) over a scratch store. A drive whose command reads a PR (merge-ask-proof) runs the kit's offline read-only gh (`.agents/skills/github-pr/scripts/gh`) first on PATH, its snapshot written in the scratch. A drive that runs `just qc`, which asks the kit's judgment model for an advisory answer, runs with the classifier faked: the kit's stub `pi` (`tests/fixtures/classify-stub/pi`) first on the qc sandbox's PATH, never a real model; its answer unset, every advisory answer shows unavailable, and the qc-advisory drive sets it. A drive whose `just qc` starts a qc judge (the qc-fallback drive) runs the kit's stub judge (`tests/fixtures/qc-judge/pi`) first on the qc sandbox's PATH (`OCTO_FEATHER_QC_PATH`), so no model runs.

Helper (an executable Python script, `python3` 3.11+, standard library only: `tomllib` reads the contract):

```
.agents/skills/verify-octo-feather/scripts/verify-octo-feather launch|doctor|drive <feature>|cleanup|run [--unreachable-exit N] [feature]
```

`run [feature]` does launch, doctor, `drive <feature>` (default `new-repo`), cleanup, then lists the evidence folder to show it survived. Exit 0 means every step passed or, for a `PASS-with-unreachable` drive, every case but the named unreachable steps passed. With `--unreachable-exit N`, a `PASS-with-unreachable` run exits N instead and prints its `UNREACHABLE` lines last on stderr: the kit's `qc.toml` demos pass 77, which `just qc` reads as a demo that did not run to its end (`schemas/qc.v1.schema.json`, demo `command`).

## Contract

[`qc.toml`](../../../qc.toml) at the kit root is the kit's driver contract (quality spec `#qc-contract`); what it declares is that spec section's, not repeated here. The helper invokes only what it declares; edit the contract, never the helper, to change any of it. How the helper uses each key:

- `format`: the helper reads format 1.
- `setup`: none declared; `launch` runs it when one is.
- `entry.command`: `launch` writes it as `bin/kit` in the run state; every case, the doctor's probes and the evidence record run that with the command a user types appended.
- `services`: none. The helper starts no service: `launch` fails naming any declared one.
- `fixture`: none. `drive` runs each declared `reset` before its cases.
- `values`: `lang` is the new-repo drive's template; `scratch_criterion` and `scratch_criterion_text` are the evidence drive's scratch criterion; `web_roles` and `web_servers` are the role-launch drive's expected web roles and web list servers; `qc_demo_pass` and `qc_demo_fail` are the qc-capture drive's scratch demos (`qc_demo_pass` also the qc-fallback drive's declared demo, the qc-advisory drive's and the qc-stale drive's two demos); `qc_demo_browser` is the qc-browser drive's scratch browser demo; `qc_demo_insufficient` is the qc-insufficient drive's. The gate-tiers drive takes no value: its scratch target and kit copy are its own. The merge-ask-proof drive takes none either: its scratch target and PR snapshot are its own; nor the template-tiers drive: its created repos are its own.
- `demo`: the kit's own criteria's demos, which `just qc` runs (quality spec `#qc-capture`); the helper does not read them.
- `browser.playwright`: the pin the qc-browser drive's scratch target declares, whose headless shell `just install-check` checks on the box.

What each key means and how its commands run: `schemas/qc.v1.schema.json`. Validate the contract: `octo-feather-contract .` (prints ok, or names the missing or wrong key).

## Run state and evidence

- `VERIFY_OCTO_FEATHER_RUN_DIR`: run state (the `state` file, the `bin/kit` command, the `created` list, scratch cwds, repos and state). Default `${TMPDIR:-/tmp}/verify-octo-feather.<uid>.<checkout-hash>/run`.
- `VERIFY_OCTO_FEATHER_EVIDENCE_DIR`: proof. Default `${TMPDIR:-/tmp}/verify-octo-feather.<uid>.<checkout-hash>/evidence`.
- `VERIFY_OCTO_FEATHER_NEW_REPO_DEST`: where the new-repo drive creates its repo (default under the run state). It must be new or empty and outside any git work tree; cleanup removes it.
- Both folders default outside the git dir, so the helper runs unchanged where HOME and the git dir are read-only and /tmp is private. `launch` prints the resolved paths.
- `launch` exits non-zero naming the folder when it cannot write the run state or evidence folder. It never reports ready without a written state file, and starts no process.
- Isolation: two checkouts get different defaults. Two runs of the same checkout at once must set distinct run and evidence folders.

## Launch

`verify-octo-feather launch` checks both folders are writable, reads the contract (fails on any declared service), runs its `setup` if any, writes the kit command (the contract's entry) to `$VERIFY_OCTO_FEATHER_RUN_DIR/bin/kit`, then records in `$VERIFY_OCTO_FEATHER_RUN_DIR/state` the contract as read, that command, the kit root and the git rev. Ready is the line `verify-octo-feather: ready: kit=<path> entry=<entry.command> rev=<rev>`. No process is left running.

## Doctor

`verify-octo-feather doctor` (read-only) answers "is this checkout worth driving?": the recorded kit command exists; `just`, `git`, `python3` on PATH; `octo-feather-new-repo`, `octo-feather-contract`, `octo-feather-evidence`, `pi-role` resolve through the entry to this checkout's `scripts/`; the kit `justfile` lists `new-repo` and `install-check`; the kit's own `qc.toml` validates; the checkout is still at the launch rev (WARN means relaunch); the Spec Chat installer new-repo needs (WARN when absent); a network namespace for install-check (WARN when absent); the scratch dir. Exit non-zero on any FAIL. Run it first whenever a drive result looks wrong.

## Drive

`verify-octo-feather drive <feature>` resets the contract's fixtures, then runs every case of one feature from [features/](features/README.md) (`new-repo`, `install-check`, `contract`, `evidence`, `lane-archive`, `director-reflection`, `correction-lane`, `factory-report`, `role-launch`, `qc-capture`, `qc-browser`, `qc-fallback`, `qc-advisory`, `qc-insufficient`, `qc-stale`, `gate-tiers`, `merge-ask-proof`, `template-tiers`) with the contract's values. Each case:

- runs `bin/kit <command>` with cwd an empty `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/cwd/<case>`, the `just` recipes as `just --justfile <kit>/justfile <recipe> ...`;
- writes `<case>.cmd` (the command as typed, with any scratch env or `unshare` wrapper), `<case>.stdout`, `<case>.stderr`, `<case>.exit`, `<case>.files` (files left in its cwd; must be empty), `<case>.kit-status` (change to the kit's `git status`; must be empty) and `<case>.obs.<key>` (facts observed after it) to `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/<feature>/`;
- appends `PASS|FAIL <case>: <cmd>` to `<feature>/summary.txt` and prints it with the case's stdout, stderr and exit code; the summary's last line is `PASS|FAIL <feature>`, or `PASS-with-unreachable <feature> (unreachable: <step>...)` when every case passed and a step this box cannot reach was printed and recorded as `UNREACHABLE <step>: <prerequisite and route attempted>`.

To drive one command by hand, the same way: after `launch`, `cd "$(mktemp -d)" && <run state>/bin/kit octo-feather-contract <kit>; echo "exit $?"`. Keep scratch only: a DEST under `/tmp`, `XDG_STATE_HOME` under the run state for commands that write box state, `unshare -Un --map-current-user` before anything that would reach `gh` or the network.

## Evidence

Proof standards:

- Exercise the kit's commands as a user types them, through the contract's entry; never source a script or call its functions.
- Capture the action (`.cmd`) and the resulting state (stdout, stderr, exit code, observed facts), not just a PASS line.
- Check side effects: the files a command wrote where it should (the new repo's commit, files and status), nothing in its cwd, no change to the kit's `git status`.
- No mocks, but for the faked tracker, the stub qc judge and the faked classifier above. The network is cut with a namespace, not stubbed: install-check's real `gh` runs and reports what it sees offline.
- Report a skipped case as skipped, never as proved through a different case.

Evidence lives at `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR`: `doctor.txt` (from `run`) and one folder per driven feature. That folder is scratch: the next drive of the feature replaces it.

The kept record is the kit's evidence store (quality spec `#evidence-store`), outside the repo and both folders above: every `drive`, passed or failed, appends its records (how many: [features/README.md#feature-entry-contract](features/README.md#feature-entry-contract)) through `octo-feather-evidence`, entered by the contract, and prints `verify-octo-feather: evidence record <id> (criterion <spec>#<anchor>; ...)` for each. The record holds the feature folder's files as outputs and names the commit (and whether the tree was dirty), the criterion with its text hash from the kit's own spec, the contract and fixture versions.

- The criterion is the one the feature file's `Drive criterion:` line names; records per line: [features/README.md#feature-entry-contract](features/README.md#feature-entry-contract).
- Read a criterion's records at a commit: `octo-feather-evidence read --criterion <spec>#<anchor> --commit <rev>` (`--json` for data). Where the store lives and the record format: `octo-feather-evidence --help`.
- Drive at a committed head for a record that names it clean.

## Cleanup

`verify-octo-feather cleanup` removes every path listed in the run state's `created` file (the repos the new-repo drive made, `VERIFY_OCTO_FEATHER_NEW_REPO_DEST` included), the scratch dirs (scratch repos and stores), the `bin/kit` command and the state file, then the run dir if empty. Nothing is killed: no process outlives its case, and nothing is killed by name. Evidence is never removed, and the kit's evidence store is never touched; cleanup prints where the evidence folder stays. Run cleanup after every failed attempt too.

## Helpers

- `scripts/verify-octo-feather`: the one helper, a Python script; its usage line is above, and running it with no argument prints it.
- Every subcommand prints what it did; `launch` prints the folders, `drive` the record id.

## Features

See [features/README.md](features/README.md). The map is the maintained verification source; keep it honest with the `maintain-verification-skill` skill.
