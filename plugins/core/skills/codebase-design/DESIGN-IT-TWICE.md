# Design it twice

When the user wants to explore alternative interfaces for a chosen module, use this parallel sub-agent pattern. From Ousterhout: your first idea is unlikely to be the best. Uses the vocabulary in `SKILL.md` — **module**, **interface**, **seam**, **adapter**, **leverage**.

## 1. Frame the problem space

Before dispatching, write a user-facing explanation for the chosen candidate:

- The constraints any new interface must satisfy
- The dependencies it relies on and which category they fall into (`DEEPENING.md`)
- A rough illustrative code sketch to make the constraints concrete — not a proposal, just grounding

Show it to the user, then proceed immediately to step 2: they read and think while the sub-agents work in parallel.

## 2. Dispatch parallel sub-agents

Propose the fan-out, then dispatch 3+ agents in parallel, each producing a **radically different** interface for the module.

Each gets a separate technical brief — file paths, coupling detail, dependency category, what sits behind the seam — independent of the user-facing framing from step 1. Include both the `SKILL.md` glossary and the project's own domain vocabulary in the brief, so names stay consistent with the architecture language and the domain language at once.

Give each agent a different design constraint:

- **Minimize the interface** — 1–3 entry points max, maximum leverage per entry point.
- **Maximize flexibility** — many use cases, room for extension.
- **Optimize for the most common caller** — make the default case trivial.
- **Ports & adapters** — when cross-seam dependencies are category 3 or 4.

Each agent outputs:

1. The interface — types, methods, params, plus invariants, ordering, error modes
2. A usage example showing how callers use it
3. What the implementation hides behind the seam
4. Dependency strategy and adapters (`DEEPENING.md`)
5. Trade-offs — where leverage is high, where it's thin

## 3. Present and compare

Present the designs sequentially so each one lands, then compare them in prose on **depth** (leverage at the interface), **locality** (where change concentrates), and **seam placement**.

Close with your own recommendation: which is strongest and why. If elements from different designs combine well, propose the hybrid. Be opinionated — the user wants a read, not a menu.
