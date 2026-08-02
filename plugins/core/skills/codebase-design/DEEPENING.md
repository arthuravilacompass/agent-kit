# Deepening

How to deepen a cluster of shallow modules safely, given its dependencies. Assumes the vocabulary in `SKILL.md` — **module**, **interface**, **seam**, **adapter**.

## Dependency categories

Classify a candidate's dependencies before proposing how it gets deepened — the category decides how the deepened module is tested across its seam.

| # | Category | What it is | Testing shape |
|---|---|---|---|
| 1 | **In-process** | Pure computation, in-memory state, no I/O | Always deepenable. Merge the modules, test through the new interface. No adapter. |
| 2 | **Local-substitutable** | Dependencies with local test stand-ins (PGLite for Postgres, in-memory filesystem) | Deepenable if the stand-in exists. The stand-in runs in the suite; the seam is internal, no port at the external interface. |
| 3 | **Remote but owned** (ports & adapters) | Your own services across a network boundary — microservices, internal APIs | Define a **port** at the seam. The deep module owns the logic; the transport is injected. In-memory adapter in tests, HTTP/gRPC/queue adapter in production. |
| 4 | **True external** (mock) | Third-party services you don't control (Stripe, Twilio) | Injected port; tests provide a mock adapter. |

Recommendation shape for category 3: *"Define a port at the seam, implement an HTTP adapter for production and an in-memory adapter for testing, so the logic sits in one deep module even though it's deployed across a network."*

## Seam discipline

- **One adapter means a hypothetical seam. Two adapters means a real one.** Don't introduce a port unless at least two adapters are justified — typically production + test. A single-adapter seam is just indirection.
- **Internal seams vs external seams.** A deep module can have internal seams, private to its implementation and used by its own tests, alongside the external seam at its interface. Don't expose an internal seam through the interface just because tests use it.

## Testing strategy: replace, don't layer

- Old unit tests on the shallow modules become waste once tests exist at the deepened module's interface — delete them.
- Write the new tests at that interface. The **interface is the test surface**.
- Assert on observable outcomes through the interface, not internal state.
- Tests should survive internal refactors — they describe behavior, not implementation. A test that has to change when the implementation changes is testing past the interface.
