# Existing install-check native lifecycle ABI presence, CODEPREP

DRAFT / UNVERIFIED. New isolated branch gh653-native-abi-presence in
/home/exedev/src/octo-feather-gh653-native-abi-presence, based on immutable
31b5973110e79756663da651070c59bd7a866e8e. Both worktree path and branch were
absent before exclusive Git worktree creation with core.hooksPath=/dev/null.
Original B31b, controla643 and main77835 remain frozen. No dependency links,
installations, patch application, manifest/lock/status changes or commit into
those trees. Only existing justfile install-check block plus this evidence change.

## Existing ownership and observable compatibility

quality#acceptance-qc-sandbox-maintained and existing install-check presence owner
cover this missing capability. This is the #682 presence follow-up, NOT a claim
that a criterion is built or accepted. Read full native scope/wiring audit and
compatibility disclosure before edit. A version-correct STOCK0.0.81 installation
previously passing presence now fails this capability check, as production31b
already refuses it before initialize. This is observable and must accompany the
final merge ask; no new public SDK compatibility/platform promise or spec edit.

Reuse SAME SandboxManager.nativeBridgeLifecycleABI numeric1 tested by production
scripts/octo-feather-qc-sandbox:209. No new checker executable, flag, registry,
format, source-code grep/lint, SDK replacement or mutable global fallback. This
is the kit-only SRT consumer that AGENTS/ADR0022 already place in root package/
lock; it is not a new target/template dependency.

## Actual source change

Retain root package.json exact devDependency pin and installed package.version
comparison. Only matching versions proceed to capability probing. Missing/wrong
version still fails and does not evaluate the SDK.

Resolve the same lexical root/node_modules package CLI entry with realpath, then
its two-parent physical package root/dist/index.js, matching production srt_js
selection rather than independently selecting another index through NODE_PATH,
a global import name or another clone. Missing CLI refuses without invoking Node.

Existing bounded run helper invokes existing PATH node with --input-type=module
and inline ESM. node:url pathToFileURL encodes the absolute index filename, so
spaces/URL characters do not create a different package import. Import the actual
public SandboxManager export; strict nativeBridgeLifecycleABI !==1 sets65.
Only strict numeric1 emits receipt1. Overall ok requires BOTH rc0 AND stdout1,
not just an import that exits0 before the capability read. Missing/wrong ABI
(including absent,0,string1) fails; missing export/import/Node/CLI/timeout or absent
receipt fails unreadable. No SDK initialize/wrap/checkDependencies/reset/native
bridge/CLI is called by the capability probe. Existing30s run bound remains;
exceptions/timeouts return failure, not ok. No stdout/stderr from dependency
initialization is printed as raw proof or secret-bearing diagnostics.

The existing installed-version missing display uses a double-quoted Python
fallback before interpolation, preserving its none text without introducing an
unquoted name through the enclosing shell single-quoted Python command.

ABI1 presence is NOT proof every method or native path works, that bytes came
from pnpm, that consumer metadata agrees, or that cleanup/accounting is complete.
Existing other tool/pin and pnpm-lock equality checks remain unchanged; lock
freshness alone remains insufficient for ABI presence.

## Import-time side-effect trace and limits

The actual source was read as DATA, never imported/evaluated:
- installed dist/index.js reexports SandboxManager from sandbox-manager.js.
- private reviewed draft exposes manager property from the Linux seam constant,
  not a manager-only disconnected marker. Draft/apply state unchanged here.
- manager export is a static object containing initialize as a function reference;
  reading the marker does not invoke it or registerCleanup.
- observed manager top-level SandboxViolationStore, SentinelRegistry, AwsPairRegistry
  and MaskedFileStore constructors create arrays/Maps/Sets; masked files are lazy,
  not written by the constructor.
- manager top-level createResolvedAddressGuard constructs BlockList rule sets;
  local-interface/DNS lookup lives in returned request-time functions, not that
  construction. It does not start a listener or native bridge there.
- platform getWslVersion is a function; whichSync subprocess launch is inside its
  callable function. Linux bridge spawning/dependency probes and manager cleanup
  registration are callable initialization paths, not called by this probe.

No observed marker access requires unsafe initialization; none is added to make
the check pass. This is a bounded source trace, NOT an exhaustive transitive
SDK/third-party/native import graph certificate. index has other reexports, and
module evaluation does execute top-level code. The future exact privately resolved
profile and approved Node environment must still be closed before any actual
probe run; if its import requires unsafe initialization/startup, STOP that run,
not silently accept, initialize or replace the SDK. No read/execute clearance for
arbitrary replacement packages or NODE_OPTIONS is inferred.

## Accurate remediation while generated wiring is pending

Failure prints the missing exact capability plus: restore the generated pinned
consumer lock/patch inputs for this kit revision, then the EXISTING owner command
pnpm install --frozen-lockfile --dir ROOT. It explicitly says a revision without
generated consumer patch wiring remains incomplete and stock version alone is
insufficient. There is NO automatic install/network access and no claim reinstalling
current unwired STOCK lock magically repairs it.

Actual pinned pnpm HELP/materialization/generated inputs are separate pending
work. No patch flags, patch layout, generated lock syntax or private-store options
are guessed. The existing tracked draft is not pnpm-generated/applied. This
CODEPREP cannot provide a verified exact one-shot consumer repair before those
inputs exist; that remaining remediation/materialization prerequisite is explicit.
Official pnpm patch/patch-commit remain the future metadata owner, not a handwritten
lock resolver. Copy/subset/archive/parity/install-check integration still needs
actual generated input/profile reconciliation in its separately scoped unit.

## Owed actual public verification, NOT RUN

No fixture or test was changed. Existing install-check integration tests enter
through real public recipe/script and require a properly materialized baseline;
current stock/unwired installation is intentionally no longer a passing baseline.
Do not add a fixture that forges the ABI probe result merely to retain exit0.

After exact private profile and NEW authority, drive existing public just
install-check against version-correct stock, missing/wrong/string marker, missing
entry/import/Node, and actual patched ABI1 consumer. Observe overall failure,
capability/remediation lines, preserved version/lock failures and ordinary ABI1
continuation. Verify no native initialization/bridge launch at the actual import
boundary. Exercise path-with-spaces/physical entry selection and missing receipt
failure through real process inputs, not internal loading or source-text tests.
Existing verify-octo-feather install-check drive and gate remain owed/unrun; same
entry/feature, no new public command/control route introduced. No map or gate
assertion is silently weakened to bless the draft.

Safety fact: source only adds a static capability read in the existing presence
owner after exact version checks, using production physical package selection;
no call to sandbox initialization is added. Extent source lines/control flow only,
blast2/3 at most; actual import safety, JS/Python/shell syntax, SDK/native behavior,
CPU and public readiness UNPROVEN. No gate-green/source-safe/self-review/acceptance.
Declared repo skills loaded: verify-octo-feather, typescript, python from source
units; nodejs/typescript/pnpm and implement-spec loaded for this step. No test edits.
Evidence: none
Check: justfile:install-check: require the production retained native lifecycle ABI before reporting pinned SRT present (quality#acceptance-qc-sandbox-maintained; existing install-check presence owner) | reads: exact pinned/installed version, physical CLI/index, actual SandboxManager.nativeBridgeLifecycleABI and bounded Node exit/receipt | class: exact
Owners: none
Prior art: @anthropic-ai/sandbox-runtime 0.0.81 | released: not reverified in CODEPREP | activity: not reverified in CODEPREP | adoption: not measured | license: Apache-2.0 | reason: existing maintained sandbox and real static capability export reused, no SDK/manager replacement
Prior art: Node.js 22.23.3 | released: not reverified in CODEPREP | activity: not reverified in CODEPREP | adoption: not measured | license: not rechecked | reason: existing pinned runtime and node:url ESM loader reuse; actual probe execution and environment remain unverified
Prior art: pnpm 10.7.0 | released: not reverified in CODEPREP | activity: not reverified in CODEPREP | adoption: not measured | license: not rechecked | reason: existing frozen install remediation retained; official patch tools own future generated consumer inputs, no guessed layout/flags or handwritten resolver
Validation: source/text/Git diff only. NO Node/pnpm/just/mise/SDK/helper/module import,
AST/JS parser/eval, project/native/model/tests/gates/statics/install/patch/runtime,
full/map/parity or new grant/capacity. Hooks explicitly bypassed for CODEPREP.
Blockers: actual HELP/generated private consumer inputs and exact import/profile
closure, real public cases/verify/gates remain pending. CODEPREP UNVERIFIED.
