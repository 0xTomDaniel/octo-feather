# shape

Criteria:

- [roles#acceptance-shaper-launch](../../../../docs/specs/roles.spec.html#acceptance-shaper-launch)

Drive criterion: `roles#acceptance-shaper-launch`

## Sub-features

- `spec-chat-link` `just spec-chat <target>` in a scratch git target: Spec Chat's skills linked into its `.agents/skills`, ignored, `git status` clean.
- `shape` `just shape` in that target, headless against a fake provider: Pi offers exactly `agents/shaper.md`'s `skills:` (from the kit) and `externalSkills:` (from the target's `.agents/skills`, Spec Chat's `repair-specs` included), none from the private home's seeded skills folders, and no request leaves for anything but the fake provider.

## How to get to it (user POV)

- The owner, in a target repo with Spec Chat linked (`just spec-chat <repo>`), runs `just shape` there and chats with the shaper; the role's skills and when each is read: `agents/shaper.md`. The launch: `scripts/octo-feather-shape` (`just shape --json` prints it); the rules: [skills#loading-shape](../../../../docs/specs/skills.spec.html#loading-shape), [skills#loading-external](../../../../docs/specs/skills.spec.html#loading-external). The director can also start it in a tab (`herdr-spawn --role shaper`), the same `pi-role` launch.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.
- `pi` on PATH (the kit's pin, `pi-version`); `unshare -Urn` and `ip` (a private network namespace with its own loopback).
- Spec Chat's installer at `$SPEC_CHAT_CLONE/scripts/install-spec-chat` (default `~/src/spec-chat`). Absent: `spec-chat-link` must refuse naming it, and the drive reports `UNREACHABLE shape` with that prerequisite (`PASS-with-unreachable`).

Run: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive shape` (or `run shape`). Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/shape/`. Records: [features/README.md#feature-entry-contract](./README.md#feature-entry-contract), the same folder as outputs. Scratch: `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/shape/` (target, home, agent dir, fake provider and its request log).

- **Spec Chat link** (`spec-chat-link`). `just --justfile <kit>/justfile spec-chat <target>`, `XDG_STATE_HOME` scratch. Observe exit 0, a link per `externalSkills:` entry in `obs.links`, the target's `git status` empty.
- **Shape** (`shape`). Home decoys first: a `SKILL.md` for every skill the role lists, and `home-decoy`, in each of the private home's `.agents/skills`, `.pi/agent/skills` and the agent dir's `skills` (`obs.home-decoys`). Then, under `unshare -Urn` (loopback only), the fake provider starts in its own session with its pid in `fake.pid`, and from the target `env -i PATH=... HOME=<private> PI_CODING_AGENT_DIR=<private> ... PI_OFFLINE=1 just --justfile <kit>/justfile shape --model fake/fake --no-session -p go` runs; the provider is stopped through `fake.pid` (by the drive if the case did not). Observe exit 0 and `fake-done`; `obs.requests` (each request Pi sent), every one for model `fake`; `obs.offered` (name and location from the first request's system prompt) equal to `obs.role-skills`, read from `agents/shaper.md` at drive time: each `skills:` entry at `<kit>/.agents/skills/<name>/SKILL.md`, each `externalSkills:` entry at `<target>/.agents/skills/<name>/SKILL.md`, none under the private home or agent dir; `obs.links` (the namespace's interfaces holding an address) only `lo`; `obs.fake-stopped`.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged.

## Gotchas

- `--model fake/fake` is the one launch change: it follows pi-role's own `--model`, so the role's model, thinking and tools are as `just shape` gives them, and only the provider is fake. That the launch names the role file's model, thinking and tools is tests/gate/kit/test_shape_launch.py's (`just shape --json`) and the role-launch drive's `shaper` case.
- The expected list is read from `agents/shaper.md` on each drive, never written in the helper: a skill added to the role (as `repair-specs` was, #607) is expected with no drive edit, and fails the drive until the target has it.
- The shaper lists `web`: its web servers are registered at session start and fail to connect inside the namespace, which the run survives. The namespace, not a stub, keeps every request but the fake provider's from leaving.
- The kit's `just` is mise-shimmed: under a private HOME mise would try to install it, so the drive passes mise's own data dir (`mise doctor --json`) and a scratch `MISE_STATE_DIR`.
- A pass proves what Pi offers the model, not that the shaper reads a skill at its step: that is an eval case's (`just qa`).
