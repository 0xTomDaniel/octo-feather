# #754 bounded feasibility and inactive role proposal

No installation, actor, role edit, native SUT or new mechanism. This pass
inspected existing public QA/sandbox paths, uv sync help and filesystem
metadata only. No dry-run sync, copy or symlink was executed.

## Existing reuse mechanisms

Runtime reuse IS supported without copying node_modules: tests/qa-baseline.sh:18
symlinks the installed kit node_modules into the running QA kit. Sandbox
srt_js resolves that real path; setup source explicitly adds snm to bound-back
paths even when the dependency root belongs to another masked repo
(scripts/octo-feather-qc-sandbox:801-837). This corrects the earlier report's
incompleteness: no special runtime-location override is required for the
existing tested node_modules symlink arrangement. No symlink created here.
The supplying pinned package must match; no install or foreign write implied.

OCTO_FEATHER_QC_RO_BINDS and OCTO_FEATHER_QC_PATH are existing public read-only
bind/path mechanisms (scripts/octo-feather-qc:66-67,241-252). They can expose
an already-installed dependency root inside the sandbox without making it
writable. They do NOT alter fixture_copy's host-side uv sync --locked, which
runs before the sandbox. Baseline roles execute through baseline pi-role,
while sandbox machinery is the running head kit's; baseline need not install
its own node_modules merely to start that machinery.

Installed kit uv.lock and pyproject.toml git blob hashes exactly equal base:
76b07f00e0fa535e08e1f70dce6b5c4f82cc574c and
2fc4c5fbfec44a0fd6b0dd99f6f08f6e7ec48c5d respectively. This supports compatible
dependency reuse investigation, NOT a claim installed environment is current,
complete, read-only or safe to sync.

## Copy and environment constraints

History fixture export and shutil.copytree create real new files; no public
QA copy/reflink flag exists in inspected code. Source installed dependencies
are device65024, destination tmpfs device36. Hardlinks and filesystem reflinks
cannot span those filesystems. cp --reflink=auto can fall back to a full copy;
it is not a quota guarantee and QA does not use that command. A .venv symlink
to the installed environment would point mandatory sync at foreign mutable
state, so it is not a safe read-only reuse mechanism by itself.

Actual pinned uv0.13.1 sync --help exposes --link-mode clone|copy|hardlink|symlink
(UV_LINK_MODE), --active, --dry-run, --inexact and install exclusions. --locked
protects the lockfile, not environment immutability. The existing QA invocation
does not request dry-run and no setup skip/active/read-only environment option
was found. A read-only dependency bind inside the sandbox cannot protect a
host environment during the earlier sync. --dry-run would require changing
that invocation; it is not silently substituted for real setup here.

UV_LINK_MODE=symlink is a real existing alternative to copying package payloads
from cache, but it still creates a new environment and may need cache metadata,
locking, resolution or downloads. No admitted run has established its cache
completeness, exact created footprint, foreign-root nonmutation or sandbox
visibility. No claim it solves this launch yet. It must not be treated as
permission to mutate a shared environment/cache. No new shim or runner patch
is proposed.

## Quantified capacity boundary

Last point root2637414400B versus floor2637168640B, margin245760B. No root-growing
job is admissible. No external growth attribution inferred. Both worktrees
now20263248B. Base tracked tree10119808B. Three concurrent tracked-tree copies
(history export, fixture repo, baseline kit) add30359424B before git metadata.
Together50622672B, leaving16486192B under64MiB before Python setup, sandbox
scratch and all kept outputs.

Existing installed .venv297472763B and node_modules60803113B are logical size
observations, not measured fresh-copy allocations. If normal setup materializes
an environment comparable to that installed venv, the subtotal is:
20263248+30359424+297472763 =348095435B (331.97MiB), before git/setup cache,
transcripts and private sandbox writable data. Thus64MiB cannot cover that
copy-based plan. A384MiB local quota would leave54557749B for those unmeasured
costs with node_modules reused, but is a planning envelope, NOT a measured
minimum or guaranteed peak. If node_modules were copied too, subtotal408898548B
already exceeds384MiB. Interpreter payload103811373B can remain the existing
installed interpreter; copying it would raise that subtotal again.

Actual exact minimal quota remains unknown without an admitted setup smoke;
there is no honest exact minimum from directory logical sizes alone. The
structural lower bound50622672B above excludes positive mandatory setup/git
costs. Existing tmpfs has787988480B free, so384MiB total local allocation would
fit its filesystem capacity at this point, but violates the current64MiB
worktree/local-data contract unless director changes that boundary.

RAM point MemAvailable4946001920B, SwapFree3926425600B. Another~328MB of tmpfs
payload for the copy-based scenario fits that point with~4.6GB remaining,
excluding all new process RSS/private sandbox tmpfs and concurrent changes.
No new Pi RSS peak measured. Therefore physical headroom looks plausible for
one sequential native QA child, but a complete RAM admission remains the
director's resource reservation plus a setup/runtime smoke, not a certified
fit from these point samples. Preserve normal Pi VAS, mise metadata512MiB AS,
existing actors and slot discipline. No SDK substitute or weakened sandbox.

## Inactive role-local proposal, pending independent RED

These are candidate text changes in evidence only, NOT active instructions.
They extend judgment where already owned; no concurrency number or new rule
owner. Accepted spec anchors remain authoritative.

Supervisor agents/supervisor.md:61, within existing Delivery pilot/fanout bullet,
after "That is your call, not a count.":

> Judge dependencies per ready task: an exclusive runtime or integration wait
> need not hold disjoint source work or consumption of returned reports.
> Example (#754): inventory, scoped qc-escape repair and report reconciliation
> could advance on separate ownership cuts while heavy validation stayed
> serial; pilot, shared writer and failed resource/input admission still hold
> the work they actually constrain.

Director agents/director.md:47, immediately after existing "Decide everything
else yourself and notify in one line", before Merge order by leverage:

> When a supervisor is held, distinguish the blocked track from independent
> approved work and return that continuation to the supervisor. Example (#754):
> runtime retirement did not block consuming the existing audit returns;
> narrowing a probe was not a new owner-access gate. A genuine capacity,
> shared-writer or input-admission boundary still holds affected work.

Placement extends existing practical-fanout and authority judgments rather
than repeating lanes-parallel, lanes-pilot, owner acceptance or transport
contracts. Whether either sentence earns its load is contingent on frozen
baseline failures and independent maintainer review of all kept outputs.
If baseline already behaves correctly or outputs do not separate, discard
these proposed edits rather than tune a proxy or claim improvement.

No check or active instruction added, so no call is requested in this pass.
Evidence: none
Checks: none
Owners: none
Prior art: none
