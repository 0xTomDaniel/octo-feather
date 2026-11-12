# Deepening

How to deepen a cluster of shallow modules safely, given its dependencies. Assumes the vocabulary in [SKILL.md](SKILL.md): **module**, **interface**, **seam**, **adapter**.

## Dependency categories

When assessing a candidate for deepening, classify its dependencies. The category determines how the deepened module is tested across its seam.

### 1. In-process

Pure computation, in-memory state, no I/O. Always deepenable: merge the modules and test through the new interface directly. No adapter needed.

### 2. Local-substitutable

Dependencies that have local test stand-ins (PGLite for Postgres, in-memory filesystem). Deepenable if the stand-in exists. The deepened module is tested with the stand-in running in the test suite. The seam is internal; no port at the module's external interface.

### 3. Remote but owned (Ports & Adapters)

Your own services across a network boundary (microservices, internal APIs). Define a **port** (interface) at the seam. The deep module owns the logic; the transport is injected as an **adapter**. Tests use an in-memory adapter. Production uses an HTTP/gRPC/queue adapter.

Recommendation shape: *"Define a port at the seam, implement an HTTP adapter for production and an in-memory adapter for testing, so the logic sits in one deep module even though it's deployed across a network."*

### 4. True external (Mock)

Third-party services (Stripe, Twilio, etc.) you don't control. The deepened module takes the external dependency as an injected port; tests provide a mock adapter.

## Seam discipline

- **One adapter means a hypothetical seam. Two adapters means a real one.** Don't introduce a port unless at least two adapters are justified (typically production + test). A single-adapter seam is just indirection.
- **Internal seams vs external seams.** A deep module can have internal seams (private to its implementation) as well as the external seam at its interface. Don't expose internal seams through the interface just because tests use them.

## Testing strategy: replace, don't layer

- **Deepen first, as its own step**, when no deep module with a stable interface exists at the seam a ticket's criterion needs: pin current behavior through a surface that exists today (pstack's refactoring playbook, step 1: cursor/plugins@0b8e952 `pstack/skills/poteto-mode/playbooks/refactoring.md`), deepen the module, then write the tests at the new interface. Product code changed to give a real deep interface is no test leak; a test-only flag, hook or branch still is.
- Old unit tests on shallow modules become waste once tests at the deepened module's interface exist; delete them.
- Write new tests at the deepened module's interface once it is deep and stable, at a seam written down from the ticket's criteria before any test (docs/adr/0002): both are hard requirements, never a private helper or a shallow wrapper whose interface mirrors its implementation. The **interface is the test surface**.
- Tests assert on observable outcomes through the interface, not internal state.
- Tests should survive internal refactors, since they describe behaviour, not implementation. If a test has to change when the implementation changes, it's testing past the interface.
