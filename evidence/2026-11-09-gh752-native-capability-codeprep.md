# Native retained-capability CODEPREP, DRAFT / UNWIRED / UNRUN

Base51bfb7f0eea31e5f155daf142c0bdef7abff1664. Distinct30min source authority:
`/tmp/gh653/brief-native-capability-codeprep.md`, cap07:42:33 UTC. Full A native
capability and selected-SRT repair reports read before edits. Implement-spec
coverage checked/sent before edits: generic maintained-library lifecycle API and
same-Recorder authenticated operations explicitly authorized under the existing
owned-process rule, no new criterion or accepted-text change shaped.

## Exact source artifacts

- scripts/octo-feather-qc-sandbox: explicit authenticated lifecycle extension,
  same-command one-shot clients, pre-initialize ABI refusal, consumer adapter,
  independently owned Node/lease/adopted-child completion.
- patches/sandbox-runtime-0.0.81-native-lifecycle.draft.patch: REAL Git diff from
  indexed original PRIVATE copies at `/tmp/gh653/native-capability-src-B`.
- This evidence. RootQC51, all existing tests/SCM observer assertions, specs,
  package/lock/workspace files, prepared alias/store/dependencies unchanged.

The selected package distributes dist JS/declarations/maps, NOT src TS. Maps
name src TS but contain NO sourcesContent. Draft therefore patches the actual
four distributed JS/declaration files, not imagined upstream TS. Stale source-map
references removed from edited files rather than publishing incorrect mappings.
No upstream checkout, replacement library, manager, FFI, daemon, listener or
second transport introduced. No installed package patched or draft applied.

Draft patch SHA256:
ee8431ab597d9eb50dc0b68a7d5e97edd44fad6dfff9c892ee854947b50904f1

Private input -> output SHA256:

| File under dist/sandbox | Original input | Private draft output |
|---|---|---|
| linux-sandbox-utils.js | 3880ba176ec09e5fdda364b1135fbccd291df5dcd9dd1c3c70da02e15f4f6621 | 03472886b8563e25e19d817274695380507067cc4c531eabfaa1c3113db677f2 |
| sandbox-manager.js | 03bd1f22e0b7a5fa401ef8f164390b8bfe8972885856ea8dce0657fa57a31114 | 5b5eb36bc7a4d07f126402ac331fd0f808ecb558e63edb5cfc89b55347c308c0 |
| linux-sandbox-utils.d.ts | d0ef48a1f34162144b68d28b086f50f33d340ca7da84c15a9a69e5533a47bf8c | df84066b1ac015dd368916dccad3661ab50c3d8d4de8ab8b888231d2daf1b3e5 |
| sandbox-manager.d.ts | 96150373de437c11c84232e95712b29d905e67c07fcddbe1f18fde0eadb7ac8d | e4aa68f7a58a1491b0b3c879fa339390d1d70731dd237349da82cb19a09e7ca6 |

All10 original A candidate hashes AND original CLI hash rechecked unchanged at
07:35:58. This is byte metadata, not source/runtime validation or immutable
provenance. Shared main77/store/alias bytes only read.

## Generic private consumer ABI1

`SandboxManager.nativeBridgeLifecycleABI` is exported from the patched Linux
seam's `NATIVE_BRIDGE_LIFECYCLE_ABI`, not merely an unrelated manager constant.
Missing patched Linux export refuses module loading; stock SDK has no ABI and
SRT_SHIM explicitly rejects it BEFORE initialize/native bridge spawn.

Fourth initialize options adds optional `nativeBridgeLifecycle`:

- abi: literal1
- start(file, actual string argv, actual SpawnOptions): {child: REAL ChildProcess,
  lease: opaque unknown}
- ready(lease): Promise<void>, only exec-crossing plus retained-task LIVE
- stop(lease): Promise<void>, only actual retained-task EXITED

SDK stores distinct actual child/lease/close completion locally in that existing
bridge initialization, not an independent process registry. Equal mux ports
alias the same child and yield one lease. All configured startup/readiness/second
spawn failures await the same stop path; reset uses the same stop closure, never
configured numeric fallback. stop attempts all handles even one fails and also
waits real Node ChildProcess close, bounded5s. A signal attempt/timer alone is
not success. Existing default library behavior for callers WITHOUT this private
adapter remains unchanged. Manager validates adapter before initialization.

Actual socket readiness and real exit/error records remain. At readiness, SDK
also queries the retained capability LIVE after relay exec-channel EOF; exec
error/actual death refuses. EOF alone is never evidence successful exec. The
actual socat still creates its original UNIX sockets with original argv/env and
stdio; no substitute readiness file/proxy/model/fixture switch.

## Explicit authentication and identity flow

Production Recorder previously had NO nonce/UID auth. This change adds it only
for lifecycle messages on the SAME existing SOCK_SEQPACKET endpoint, leaving
ordinary attempts/masks/hello semantics unchanged. Each lifecycle message checks
peer UID (not PID lookup), per-run64hex secret,64hex lease, supported operation,
exact message fields and descriptor count. Registration validates actual pidfd
operations through the kernel; duplicate/malformed/closing registrations refuse.

Node starts a one-shot mode of the SAME qc-sandbox command. Relay opens pidfd on
ITSELF, transfers SCM_RIGHTS, receives authenticated acceptance, then execs the
actual resolved executable with original argv/env/stdio. Receiver duplicates and
retains that exact kernel handle. Peer numeric PID, nonce and lease text are
NEVER process identity or signal targets. Python sockets/self-pidfds and receiver
duplicates are non-inheritable. On exec error relay explicitly reports before
closing; native is never executed after registration refusal/timeout.

Secret exists only Recorder memory and private setup/Node/client environment,
not jenv/run.json/settings/proof/attempt logs/argv/judge. INPUTS scrubs authority
names; Node captures and removes them from process.env BEFORE initialization and
wrapped payload; relay removes them before actual native exec. Control clients
are short-lived SAME-command clients, not Node FFI/net stream or new listener.

SDK stop uses native-control: Recorder TERM then1.5s escalation to KILL, same
retained fd, actual readiness poll until5s. Only actual exit ACK succeeds. Node
ALSO requires actual ChildProcess close. native-ready checks exec crossing plus
kernel liveness, not JS pid/.killed. All accepted handles remain owned across
Node death; setup finalizes independently before Recorder closes, then existing
orphans/ECHILD accounts inherited socat fork descendants. Parent pidfd alone is
not all-descendant completion. Setup retains its directly owned Node pidfd BEFORE
wait; exception cleanup uses that handle/unreaped direct-root fallback, never a
post-reap numeric group probe. Late recorded exec/cleanup errors still fail66.

Existing SRT_SHIM shell SIGINT/TERM child.kill was another numeric path. The
actual default Linux `/bin/sh -c <same wrapped command>` now also starts through
the SAME relay/capability channel with real inherited stdio. Signal forwarding
uses native-signal and exact original SIGINT/TERM. Its ACK is delivery ONLY (or
not-signallable), never death. Original real ChildProcess exit still drives
cleanup/reset and original code/signal mapping. Node22 public docs confirm Unix
spawn shell:true defaults to /bin/sh and shell understands -c:
https://nodejs.org/docs/v22.11.0/api/child_process.html
This does not change bwrap/proc/network isolation or fabricate completion.

## Remaining source/validation limits

DRAFT, not independent source closure. No JS parser, TypeScript checker, Node,
SDK, relay, native, helper, test or gate executed. Python source AST only cannot
prove names, behavior, Node event ordering, protocol completion, typing or CPU.
Private declaration/runtime alignment and consumer application need review.

Pre-registration cancellation/early stop may reach an unknown lease and FAIL;
there is no numeric fallback. Relay cannot native-exec without acceptance. Setup
closing rejects late registration, retains accepted fds, and owns unregistered
relay/control children through adoption/ECHILD. Protocol/client timeout, failed
spawn, exec failure and live-task timeout remain failures, not cleanup proof.
Real client rc categories include unavailable executable69, registration70,
request71, transport74, timeout75 and exec127, not forged socat exit values.

Setup's new Node enrollment is after Popen returns. An abrupt setup death during
its partial creation relies on the EXISTING outer QC51 owned-root/subreaper
fallback, not standalone setup certification or an unsafe preexec/signal mask.
Recorder thread/protocol/descriptor failures, initialization rejection, repeated
signals, Node abrupt exit and inherited fork-descendant paths all need exact-head
independent source review and later finite public proof. Cleanup deadlines are
fatal when completion is unproved, not a guarantee against uninterruptible tasks
or external SIGKILL. No blanket Node/import/native/backend audit or clearance.
A/E independent scope/profile/wiring work is not this implementation's review.

## Observable compatibility and downstream wiring disclosure

Supervisor determination `/tmp/gh653/native-compatibility-disclosure.md` and A's
`/tmp/gh653/report-native-scope-wiring-audit.md` read. No spec edit needed now:
existing criteria attainable, no new public SDK support promise. Stock-version
ABI refusal is OBSERVABLE, not internal-only: install-check must name the missing
consumer capability and the exact REAL tool-generated fix after materialization.
51's TERM143/HUP129 and cancelled/ran-null scratch note are observable too; this
is not a global evidence-store nullable Boolean promise. Carry these disclosures
in final merge ask. New promises/conflicts require supervisor's logged spec call
BEFORE adoption, not same-PR permission.

Shell relay consumes NO payload stdin during authentication: all bootstrap is
through the private socket. Actual fd0/1/2 are inherited unchanged, then survive
exec; only private lifecycle environment keys are stripped. Payload signal ACK
is delivery/not-signallable only, never stop completion or EOF evidence.

Exact pending sites, NOT edited in this unit:
- justfile:514-520 version-only install-check/presence needs finalized ABI and
  supported remediation; :719-723 lock equality cannot substitute for ABI.
- tests/gate/kit/check_ts.py:68-69 other_fs subset must carry actual tool-emitted
  patch/config inputs, not only package.json/pnpm-lock.yaml.
- justfile:329 pre-fanout and :285 check-ts preparation plus CI root frozen
  install must consume generated tracked metadata/patch, no new cache registry.
- Existing tracked Copy/build_kit_repo and QA Git archive carry committed inputs;
  kit_deps linked ROOT must resolve private patched bytes. Fresh per-run prepared
  roots required. Parity copies need coherent current patch/config/lock and must
  not combine historical SDK consumer files with a current patch silently.

These are later exact-scope obligations, not permission to widen this diff.

## Exact pending REAL pnpm wiring, NOT EXECUTED

Official maintained mechanism: https://pnpm.io/10.x/cli/patch and
https://pnpm.io/10.x/cli/patch-commit. Repo pin is pnpm10.7.0 and SDK0.0.81.

1. Separately authorize private dependency/store materialization; current scoped
   node_modules alias MUST NOT be modified/patched through. Need an owned private
   directory/store with copied imports and no hardlink writes to shared bytes.
2. First ask actual pinned tool `pnpm patch --help`, `pnpm patch-commit --help`
   and `pnpm install --help`. Actual local help/options/outputs NOT verified here.
3. Official documented extraction form, still locally UNVERIFIED:
   `pnpm patch @anthropic-ai/sandbox-runtime@0.0.81 --edit-dir <private-edit-dir>`.
   Reconcile exact extracted originals with four input hashes above before any
   edit. Apply reviewed draft only inside the authorized private extraction.
4. Official documented commit form, still locally UNVERIFIED:
   `pnpm patch-commit <private-edit-dir>`. It may install/apply; treat as real
   execution under its own preparation grant. Let tool generate actual patch,
   patchedDependencies/config and lock, never hand-invent YAML/manifest/lock.
5. Actual help determines supported options for frozen lock, scripts disabled,
   private store and copy import method. Flag spellings/real output not invented
   here. Re-materialize privately, reconcile tool-emitted patch/hash/version and
   all actual JS/types/native selection paths. Preserve this draft/input record
   until the real tool output is compared, not silently relabelled generated.
6. A owns downstream helper/install-check/parity wiring audit. Any additional
   file/spec/accepted-text change requires precise scope/spec call first. Same
   PR is NOT scope authority. No existing checker weakened to accept a draft.

Current consumer remains STOCK and must refuse ABI preflight; package/lock not
wired, no real SDK repair deployed. Actual helper/toolhelp/output verification
and independent exact patched-profile source closure are pending blockers.

## Public proof proposal, NOT AUTHORIZED/RUN

After proper private materialization, exact hash/profile/source closure and NEW
owned native HOLD/held ACK/START, keep public capture-case + qc-escapes and actual
cancelled_capture target. First small finite smoke before any larger run. Preserve
all SAME3 LIVE-before/EXITED-after and every original isolation/advisory/mask/
cleanup assertion at original points, before outer teardown. Positive only, NOT
cleanup-fault RED. Separate finite public phase cases must cover pre-registration,
exec/readiness refusal, stop deadline and abrupt Node completion using actual
same relay/native capabilities and actual owning completion receipts, not an
unrelated sleeper, fixture product hook or fabricated records. Those phase cases
are proposed scope, not secretly implemented tests in this source unit.

Safety fact: signals route retained child-origin capabilities and actual death/
close/ECHILD distinguish identity, termination and accounting; stock cannot pass
ABI before native initialize. Extent: SOURCE TRACE only, blast-radius steps2/3;
runtime UNPROVEN. No green, acceptance, final review or source-safe verdict.

Declared repo skills loaded: python, verify-octo-feather, typescript; nodejs,
pnpm, codebase-design and implement-spec loaded for this step.
Evidence: none
Check: scripts/octo-feather-qc-sandbox: require retained lifecycle ABI before SDK initialization (accepted owned-native rule) | reads: imported SDK lifecycle ABI and private setup authority availability | class: exact
Check: scripts/octo-feather-qc-sandbox: authenticate lifecycle operations before capability registration/signaling (authorized same-Recorder extension) | reads: peer UID, private secret, lease, operation, fields and received descriptors | class: exact
Owners: none
Prior art: none
Existing maintained SRT/Node/pnpm and kit-stdlib Recorder/JSON/SCM/pidfd/selector/
subreaper mechanisms extended, not replaced or newly selected infrastructure.
Validation: readonly inputs/hash/source, real private Git diff, Python AST only.
Hooks bypassed for CODEPREP. No installs, actual pnpm application, manifests/lock
edits, reviewed project/helper/library/model/native execution, tests/statics/
gates/full/map/parity or old baseline. Remains DRAFT/UNWIRED/UNRUN.
