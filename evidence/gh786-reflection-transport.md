# gh786 reflection transport

Basis: owner-authorized factory repair, issue #786. Existing contracts: comms
`#acceptance-reflect-before-archive`, `#reflection-director`. No criterion added.

## Correction

Class: oversized reflection input exceeds process argument limits. The canonical
archive refusal recorded in feather's gh154 handoff log reports Linux E2BIG before
pi-role started, with provisional lane findings rolled back and no correction issue
filed. No private transcript is copied here. Findings in active and archived lane
logs were searched for this class; none persisted for this incident. ADR0010 and
recent commits were inspected. This is an explicit owner correction, not an
inferred two-lane repeat.

ADR0020 routing: every changed file belongs to this kit worktree. ADR0008 rung 1:
stdin removes the argv size constraint structurally. Pi's installed README,
`docs/cli.md` and `docs/cli-integration.md` document piped stdin and print mode.
The same pi-role, reflector role, options, complete brief, text stdout, timeout and
parser remain. No check or instruction was added.

## Red and green

Before the production edit, `bash tests/director-reflect.sh` exited 1 with
`reflector did not start ([Errno 7] Argument list too long: '.../scripts/pi-role')`.
The test generates synthetic UTF-8 evidence larger than 131072 bytes through the
published `octo-feather-lane reflect --director` command. After the edit, the same
command passes and the model boundary receives the entire generated evidence
exactly once, including its beginning, multibyte body and end. Existing assertions
also verify the role/model/options, brief records and question/output semantics.

`tests/lane-reflect.sh` covers unchanged state on nonzero model exit, malformed
replies, timeout and a failed model executable launch. `tests/director-reflect.sh`
covers director nonzero exit, malformed reply and timeout after the lane reflection,
requiring byte-identical state rollback. `tests/lane-archive.sh` and
`tests/lane-correction.sh` cover archive and correction transaction behavior.
These tests run scripts as public commands, never load or inspect their source.

## Small real pipeline smoke

Before running the regression batch, a synthetic scratch lane was reflected through
this worktree's public command, with the approved GPT wrapper first on PATH:

```
cd /tmp/gh786-smoke/cwd
PATH=<approved gpt-only/bin>:$PATH XDG_STATE_HOME=/tmp/gh786-smoke/state \
HERDR_SESSION= GOMAXPROCS=2 NODE_OPTIONS=--max-old-space-size=1536 \
OCTO_FEATHER_REFLECT_TIMEOUT=120 \
OCTO_FEATHER_REFLECT_ARGS='--thinking off --session-dir /tmp/gh786-smoke/sessions' \
timeout --kill-after=10 150 <worktree>/scripts/octo-feather-lane reflect gh900
```

Exit 0: `reflection: lane gh900, 0 findings`, all seven questions appended;
`correction lanes: none filed`. Session
`01a1cbcc-2bfa-74a4-b1a4-00e56e880189` has five new assistant entries with
provider `openai`, model `gpt-6.1-sol`, API `openai-responses`, independently
verified by the supervisor. Scratch sessions retained outside git. This smoke
proved the existing small pipeline before the transport edit, not large real-model
input. Final public verify drives belong to the supervisor's integrated head.

## Offline gate setup recovery

The first full gate failed: 99 failed, 129 passed, 189 seconds. Distinct setup
causes were missing socat, missing rg under the HOME-masked user-mise fixture,
uncached pinned Python template dependencies (filelock 4.2.9 and pytest-testmon
2.3.0), and the approved GPT wrapper overriding credential-free local fake-provider
fixtures' model/provider flags. No reflection regression failed. The first scratch
job callback also used unsupported `herdr-say --pane`; corrected to documented
`herdr-say --parent`. A harmless completion callback was received by the supervisor.

Supervisor-authorized setup, no source/test/auth/global configuration changes:

```
# Official Debian trixie package, extracted, never installed system-wide:
# https://deb.debian.org/debian/pool/main/s/socat/socat_1.8.0.3-1+deb13u1_amd64.deb
dpkg-deb -x <downloaded-deb> /tmp/gh786-deps
cp -L "$HOME/.local/bin/rg" /tmp/gh786-deps/usr/bin/rg
mkdir -p /tmp/gh786-deps/local-bin
cp -a /usr/local/bin/. /tmp/gh786-deps/local-bin/
cp /tmp/gh786-deps/usr/bin/{socat,rg} /tmp/gh786-deps/local-bin/
# Copy templates/python/{pyproject.toml,uv.lock,src} into owned ignored scratch,
# then uv sync --locked --project <scratch> to warm its declared dependencies.
# JOB_PATH is inherited PATH with ONLY the approved gpt-only/bin entry removed,
# prefixed with /tmp/gh786-deps/usr/bin. Only for this OFFLINE gate:
PATH="$JOB_PATH" GOMAXPROCS=2 NODE_OPTIONS=--max-old-space-size=1536 \
unshare -rm bash -euc '
  mount --bind /tmp/gh786-deps/local-bin /usr/local/bin
  exec just check
'
```

Actual versions: socat 1.8.0.3, rg 14.1.1. Before another full batch, the public
sandbox scenario `tests/gate/kit/qc_sandbox.py by_hand` passed, the existing
credential-free fake-provider `tests/skills-loaded.sh` passed, frozen template
`uv sync` passed, and `tests/user-mise.sh` passed inside that namespace. The last
sample exercised the nested sandbox and every section's positive/negative case.
After namespace exit, host `/usr/local/bin/socat` and `/usr/local/bin/rg` remained
absent. Actual factory agents and real reflection QA still use approved
wrapper-first routing; only the offline gate fixtures use installed Pi directly.

## Final provisioning and portability correction

The root-mapped setup above was superseded. Its full gate returned 7 failed,
221 passed: uid0 bypassed the lane-report and TypeScript read-only cases; nested
sandbox namespace creation failed EPERM; cleanup's third sleep was missing.
A current-user namespace with capabilities dropped fixed all five in the public
selected-seven gate. Its two remaining failures were fixture setup, not weakened
assertions: the nested browser fixture hid `/usr/local/bin`, losing socat, and the
cost fixture hardlinked the real driver across filesystems.

The browser cause was captured through the supported
`USER_MISE_HERDR=none tests/user-mise.sh --gate -k install-check-browser` command:
`socat MISSING`. A namespace-local `/usr/bin` overlay preserves every system tool
and adds only actual extracted socat and rg. The public user-mise-ic case then
passed. Host `/usr/bin/socat` remained absent after namespace exit.

Canonical `justfile` check-tests creates `/tmp/gate.XXXXXX` explicitly, overriding
inherited TMPDIR. A same-filesystem bind still fails Linux's cross-mount hardlink
restriction (both paths st_dev 2050, `ln` EXDEV). The director authorized the minimal
cost fixture portability repair in #786: `shutil.copy2` of the same regular driver
replaces `os.link`, preserving bytes and mode. The real command, workload and all
assertions are unchanged. No new criterion, oracle waiver or production change.

Final reproducible job setup (no `/tmp` bind required):

```
mkdir -p .venv/native/overlay-upper .venv/native/overlay-work
cp /tmp/gh786-deps/usr/bin/{socat,rg} .venv/native/overlay-upper/
PATH="$JOB_PATH" GOMAXPROCS=2 NODE_OPTIONS=--max-old-space-size=1536 \
unshare --map-current-user --mount --keep-caps bash -euc '
  mount -t overlay overlay -o "lowerdir=/usr/bin,upperdir=$PWD/.venv/native/overlay-upper,workdir=$PWD/.venv/native/overlay-work" /usr/bin
  exec setpriv --inh-caps=-all --ambient-caps=-all bash -euc '\''
    test "$(id -u)" = 1000
    for cap in CapInh CapPrm CapEff CapAmb; do
      grep -q "^${cap}:[[:space:]]*0000000000000000$" /proc/self/status
    done
    exec just check
  '\''
'
```

Only namespace-local mounts are changed. Gate entry asserts uid1000 and zero
inheritable, permitted, effective and ambient capability sets. Each job has an
independent deadline, owned process group, awaited cleanup and a verified
`herdr-say --parent` completion callback. No host tool, auth or configuration edit.

With this final setup and the copy2 repair, the canonical selected cost and
user-mise-ic cases both passed: 2 passed in 28.87 seconds, exit 0. All earlier
reflection regression cases also passed. Final full-gate outcome is reported to
the supervisor separately so this evidence is fixed before that gate runs.
