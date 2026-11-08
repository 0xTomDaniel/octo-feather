# #576 CI prerequisites correction

## Session and baseline

Actual session record: `/home/exedev/.pi/agent/sessions/--home-exedev-src-octo-feather-gh576-w689--/2026-11-08T17-39-05-084Z_9c6fc99f-2305-4384-abff-cab11dd24f4b.jsonl`, model_change `0b8c1154`, provider `openai`, modelId `gpt-6.1-sol`.

Worker branch `implementer-gh689` fast-forwarded from e4628b2 to integration head 6e2ee8af1a842d7d324fe3c0fd545b56c29ad454 before edits. Integration branch not written.

## Facts read, not runtime proof

- Installed srt source `node_modules/@anthropic-ai/sandbox-runtime/dist/sandbox/sandbox-manager.js:1216` defines `checkDependenciesCommon`; line 1229 reports missing ripgrep. Supervisor supplied upstream failure at exact head 4d97857377bacbe24a23d6c078b9c81e0277d490, run 42504969341: 75 failed, 145 passed. No claim that these changes explain every failure.
- Read-only installer audit `/tmp/gh576-eval/herdr-installer-audit.sh`: official installer reads `https://herdr.dev/latest.json`, requires an asset SHA256, computes the downloaded binary checksum, and refuses mismatch before installing. Defaults to `$HOME/.local/bin`; no version override. Workflow reuses this installer and prints the installed binary's public `--version`. No new pin or installer policy.
- Actual CI installed Herdr version: PENDING. Actual manifest/checksum verification during install: PENDING. No install executed in this session.
- Supervisor completed the `remote#host-tools` rg fact/call change at 4fcbb3835ae4f7ae57f3ffa0012145847bfd3bc4. Worker imported that exact integration head with `git merge --ff-only gh576` on resume; no worker spec or ADR edit.

## Change and safety boundary

Existing install-check dependency loop adds rg and its `sudo apt install ripgrep` fix. Existing box test exercises the public command with fixture rg present, absent, and restored; shared fixture hides the host rg. CI adds ripgrep to existing apt provisioning and installs real Herdr before the offline gate. Feature map points to this coverage.

Safety fact: workload, isolation policy, CPU scope and five literal <.8 assertions remain unchanged. Focused diagnostic proves rg present/absent/restored and installed real-Herdr selection through public tests; the resumed normal fast gate passed 200 tests, including shared install-check coverage. Full sandbox cost/isolation acceptance remains UNPROVEN here: no cost timing run or exact-head CI provisioning performed.

## Validation

RUN: `git diff --check`, `bash -n tests/install-check-box.sh tests/lib/install-check.sh`, `just --summary >/dev/null`: passed.

RUN: direct `shellcheck tests/install-check-box.sh tests/lib/install-check.sh`: reports existing SC2015/SC2016 info diagnostics in unchanged lines. No unrelated cleanup.

RUN: `just --fmt --check`: refused because --fmt requires --unstable. No formatting applied.

Original invocation performed static checks only. Supervisor's subsequent dirty-tree diagnostic passed both selected tests in 12.70s: `tests/gate/test_gate.py::test_script[tests/install-check-box.sh]` (11.472s CPU, 11.82s wall) and `tests/gate/kit/test_qc_sandbox_cost.py::test_installed_herdr` (.061s CPU, .115s wall). Read stdout and exit record in `/tmp/gh576-eval/ci-prerequisites-diagnostic/`: pre=0 probes=0 post=0. Over-10s CPU is report-only. No test_cost/timing ran. Diagnostic base was 6e2ee8af1a842d7d324fe3c0fd545b56c29ad454, aggregate a301e805077e34e654a89518130086c44a0ca4f5609ca4bf3ee35eca3925fab1; original manifest preserved as `/tmp/gh576-eval/ci-prerequisites-candidate-diagnostic.json`. This is dirty-tree diagnostic proof only, not clean-head acceptance or CI provisioning proof. New base/evidence changes require a regenerated candidate manifest; old aggregate does not cover them.

Resume authorization: only normal `env -u OCTO_FEATHER_QC_CLAIMS just fast` and normal commit/hooks. Before gate, slot status showed gh576 heavy grant (17:47:38Z, expires 19:47:38Z), no active heavy/eval holder; process inspection found no conflicting gate and seven Pi processes. Latest actual session model_change still openai/gpt-6.1-sol. Handoff gate result: PASS, exit 0, 200 passed in 247.97s; command `env -u OCTO_FEATHER_QC_CLAIMS just fast`, combined stdout/stderr log `/tmp/gh576-eval/ci-prerequisites-handoff-gate.log`. Standard fast selection, no custom exclusions. Gate ran against candidate aggregate 5ff8fca0d911289d5a92495bbcfce53918c947ba953aac5c197ff477eec066da at base 4fcbb3835ae4f7ae57f3ffa0012145847bfd3bc4; subsequent edits only record this result, and the candidate manifest is regenerated rather than reusing that aggregate.

At that earlier handoff the verify drive was PENDING; it is now completed in the live smoke section below. Fresh exact-ref integration/full gate, real CI Herdr version/checksum observation, fresh review, affected QC and exact-new-head GitHub Actions full check remain PENDING. No installer run authorized or performed.

## Remaining proof and historical command plan

The resumed invocation ran only the authorized normal fast gate. The following original plan is retained for context; focused diagnostic and fast coverage above are now complete. The verify drive is now complete below; provisioning observation, full integration/review/QC and exact-head CI remain PENDING, supervisor-owned.

- `bash tests/install-check-box.sh` and `for t in tests/install-check.sh tests/install-check-*.sh; do bash "$t" || exit; done`
- `.agents/skills/verify-octo-feather/scripts/verify-octo-feather run install-check`
- Authorized prerequisite provisioning as encoded in `.github/workflows/check.yml`, then `rg --version` and `herdr --version`; retain official installer output as actual checksum verification evidence.
- `just fast`, then commit, then supervisor-owned `just integrate --full 576 implementer-gh689` with lane QC claims, fresh review and affected QC.
- Real GitHub Actions full check at the resulting exact new head, not a rerun of an old head or status-only skip.

Original patch commit: ed02a893e3dd3b4613e7616da66ac5704420a06e. Prior-art cross-family investigation remains separately BLOCKED, untouched.

## Live smoke correction, 2026-11-08

Supervisor integrate11 of ed02a893 failed, actual rc 2: one failure, `tests/gate/test_gate.py::test_recipe[check-behavior-smoke]`, 219 passed in 290.55s. Log `/tmp/gh576-eval/integrate11.log` names this feature map's missing Smoke line. Integration rolled back to 4fcbb3835ae4f7ae57f3ffa0012145847bfd3bc4. Historical integrated-but-rolled-back test_cost and test_installed_herdr PASS are not fresh acceptance; no per-run CPU maxima are asserted. Earlier precommit fast did not cover the uncommitted feature-map change in merge-base..HEAD. This failure is not relabelled green.

Read `.agents/skills/verify-octo-feather/SKILL.md` and the complete install-check feature file before driving. Actual session's latest model_change remains event 0b8c1154, openai/gpt-6.1-sol. Initial HEAD ed02a893 was clean. Before drive, heavy slot grant was gh576 (18:10:34Z to 20:10:34Z), no active conflicting run; eight Pi processes observed.

Smoke: .agents/skills/verify-octo-feather/features/install-check.md exercised its documented public path with `env VERIFY_OCTO_FEATHER_RUN_DIR=/tmp/gh576-eval/ci-prerequisites-smoke/run VERIFY_OCTO_FEATHER_EVIDENCE_DIR=/tmp/gh576-eval/ci-prerequisites-smoke/evidence .agents/skills/verify-octo-feather/scripts/verify-octo-feather run install-check` at clean ed02a893e3dd3b4613e7616da66ac5704420a06e; wrapper exit 0, run PASS, offline and models-offline PASS. Complete log `/tmp/gh576-eval/ci-prerequisites-smoke/drive.log`, rc `/tmp/gh576-eval/ci-prerequisites-smoke/drive.exit`; outputs `/tmp/gh576-eval/ci-prerequisites-smoke/evidence/install-check/`. Supported wrapper performed launch, doctor, drive, cleanup and retained evidence.

Evidence: install-check 20261108T181248Z-73e2b4a5
Evidence: install-check 20261108T181248Z-d9561adc

Read THIS checkout's stored `offline.cmd` and `offline.stdout`: command `unshare -Un --map-current-user just --justfile /home/exedev/src/octo-feather-gh576-w689/justfile install-check /home/exedev/src/octo-feather-gh576-w689`; output includes `rg ok (srt, the qc sandbox, needs it)` and `herdr  ok  /home/exedev/.local/bin/herdr`. These prove local executable/tool reporting only, not CI installer execution, Herdr version or checksum provenance. Offline command exit 1 is the documented expected result (including gh not authenticated and worktree kit NOT ON MAIN), not a wrapper failure. Empty `.files` and `.kit-status` records show no cwd or checkout side effects.

The models-offline case retained `unshare -Un --map-current-user`, exit 1 as expected, every named provider UNREACHABLE and `models spend 0.0000 USD (3 calls, Pi usage cost)`; no provider could be reached in the namespace. No key/credential validity is proved. No new real model, judge or eval worker was spawned. No installer, full integration, QC or cost timing run was performed in this correction turn.

Safety boundary: only this evidence file changes in the correction. Source, feature map, sandbox policy, workload, CPU accounting and all assertions remain untouched. Live verify smoke establishes the local documented install-check surface, not universal performance or CI provisioning.

Normal evidence-only commit/hooks next, followed by exactly one `env -u OCTO_FEATHER_QC_CLAIMS just fast` on the committed correction HEAD. Gate status in this committed document is PENDING until completion; complete log `/tmp/gh576-eval/ci-prerequisites-smoke/handoff-gate.log`, rc `/tmp/gh576-eval/ci-prerequisites-smoke/handoff-gate.exit`. Actual result and exact clean HEAD will be reported on stdout without modifying the judged commit. Fresh exact-ref full gate, review, affected QC, real exact-head CI full check and CI-installed Herdr version/checksum verification remain PENDING.
