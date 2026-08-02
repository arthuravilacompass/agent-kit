---
name: codebase-design
description: Invoke when designing or improving a module's interface, deciding where a seam goes, judging whether a module is deep or shallow, or making code more testable and AI-navigable — a shared vocabulary and set of principles, not a workflow. Also read by `core:deepen-architecture`. Triggers — "where should this seam go", "is this abstraction earning its keep", "how should this interface look", "this module feels shallow".
metadata: author=Matt Pocock; source=mattpocock/skills@main (skills/engineering/codebase-design); license=MIT
---

# codebase-design — vocabulary for deep modules

> Adapted from the `codebase-design` skill by Matt Pocock (`mattpocock/skills`, MIT).

Design **deep modules**: a lot of behavior behind a small interface, placed at a clean seam, testable through that interface. Use this language and these principles wherever code is being designed or restructured. The aim is leverage for callers, locality for maintainers, testability for everyone.

This is a corpus to read, not a conductor — it holds terms and principles to apply inside whatever workflow is already running. Two extensions live beside it: `DEEPENING.md` (dependency categories, seam discipline, how to test a deepened module) and `DESIGN-IT-TWICE.md` (parallel sub-agents designing the same interface several ways).

## Glossary

Use these terms exactly. Consistent language is the whole point.

**Module** — anything with an interface and an implementation. Deliberately scale-agnostic: a function, class, package, or tier-spanning slice. *Avoid*: unit, component, service.

**Interface** — everything a caller must know to use the module correctly: the type signature, but also invariants, ordering constraints, error modes, required configuration, and performance characteristics. *Avoid*: API, signature — both too narrow, they name only the type-level surface.

**Implementation** — what's inside a module, its body of code. Distinct from **adapter**: a thing can be a small adapter with a large implementation (a Postgres repo) or a large adapter with a small implementation (an in-memory fake). Reach for "adapter" when the seam is the topic; "implementation" otherwise.

**Depth** — leverage at the interface: how much behavior a caller (or test) can exercise per unit of interface they must learn. **Deep** = a lot of behavior behind a small interface. **Shallow** = interface nearly as complex as the implementation.

**Seam** *(Michael Feathers)* — a place where you can alter behavior without editing in that place; the *location* at which a module's interface lives. Where the seam goes is its own design decision, distinct from what goes behind it. *Avoid*: boundary — overloaded with DDD's bounded context.

**Adapter** — a concrete thing that satisfies an interface at a seam. Names a *role* (which slot it fills), not substance (what's inside).

**Leverage** — what callers get from depth: more capability per unit of interface learned. One implementation pays back across N call sites and M tests.

**Locality** — what maintainers get from depth: change, bugs, knowledge, and verification concentrate in one place instead of spreading across callers. Fix once, fixed everywhere.

## Deep vs shallow

```
deep                        shallow (avoid)
┌───────────────────┐       ┌───────────────────────────────┐
│  small interface  │       │       large interface         │
├───────────────────┤       ├───────────────────────────────┤
│                   │       │  thin implementation          │
│  deep             │       └───────────────────────────────┘
│  implementation   │
└───────────────────┘
```

Designing an interface, ask: can I cut methods? Can I simplify parameters? Can I hide more complexity inside?

## Principles

- **Depth is a property of the interface, not the implementation.** A deep module can be internally composed of small, swappable parts — they just aren't part of the interface. A module can have **internal seams** (private to its implementation, used by its own tests) alongside the **external seam** at its interface.
- **The deletion test.** Imagine deleting the module. If complexity vanishes, it was a pass-through. If complexity reappears across N callers, it was earning its keep.
- **The interface is the test surface.** Callers and tests cross the same seam. Wanting to test *past* the interface means the module is probably the wrong shape.
- **One adapter means a hypothetical seam. Two adapters means a real one.** Don't introduce a seam unless something actually varies across it.

## Designing for testability

1. **Accept dependencies, don't create them** — `processOrder(order, paymentGateway)`, not `processOrder(order)` constructing a `StripeGateway` inside.
2. **Return results, don't produce side effects** — `calculateDiscount(cart): Discount`, not `applyDiscount(cart): void` mutating the cart.
3. **Small surface area** — fewer methods means fewer tests; fewer params means simpler setup.

## Relationships

- A **module** has exactly one **interface** — the surface it presents to callers and tests.
- **Depth** is a property of a module, measured against its interface.
- A **seam** is where a module's interface lives; an **adapter** sits at a seam and satisfies the interface.
- Depth produces **leverage** for callers and **locality** for maintainers.

## Rejected framings

- **Depth as a ratio of implementation-lines to interface-lines** (Ousterhout): rewards padding the implementation. Use depth-as-leverage.
- **"Interface" as the TypeScript `interface` keyword or a class's public methods**: too narrow — interface here includes every fact a caller must know.
- **"Boundary"**: overloaded with DDD's bounded context. Say **seam** or **interface**.

## Phrasings that fit

- "The Order intake module is shallow — interface nearly matches the implementation."
- "Pricing leaks across the seam."
- "Deepen: one interface, one place to test."
- "Two adapters justify the seam: HTTP in prod, in-memory in tests."

Name gains in glossary terms — *"locality: bugs concentrate in one module"*, *"leverage: one interface, N call sites"*, *"interface shrinks; implementation absorbs the wrappers"*. Never *"easier to maintain"* or *"cleaner code"*: those aren't in the glossary and don't earn their place.

## Going deeper

- **Deepening a cluster given its dependencies** — `DEEPENING.md` (same folder): dependency categories, seam discipline, replace-don't-layer testing.
- **Exploring alternative interfaces** — `DESIGN-IT-TWICE.md` (same folder): parallel sub-agents designing the interface several radically different ways, then compared on depth, locality, and seam placement.
- **Finding candidates across a whole codebase** — `core:deepen-architecture`, which scans for shallow modules and reports them visually.
