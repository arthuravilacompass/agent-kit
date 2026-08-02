---
name: deepen-architecture
description: Invoke to scan a codebase for deepening opportunities — refactors that turn shallow modules into deep ones — presented as a visual HTML report, then grilled one candidate at a time. Not a diff review (use `core:review-local`) and not a pre-ticket map of current state (use `core:archaeology`).
disable-model-invocation: true
metadata: author=Matt Pocock; source=mattpocock/skills@main (skills/engineering/improve-codebase-architecture); license=MIT
---

# deepen-architecture — deepening opportunities as a visual report

> Adapted from the `improve-codebase-architecture` skill by Matt Pocock (`mattpocock/skills`, MIT).

Surface architectural friction and propose **deepening opportunities** — refactors that turn shallow modules into deep ones. The aim is testability and AI-navigability, not tidiness.

Read `core:codebase-design` **before step 1**: it holds the glossary (**module**, **interface**, **depth**, **seam**, **adapter**, **leverage**, **locality**) and the principles (the deletion test, "the interface is the test surface", "one adapter = hypothetical seam, two = real") this skill speaks in. Use those terms exactly in every candidate — don't drift into "component", "service", "API", or "boundary".

## Steps

### 1. Scope, then explore

**Scope before you scan — YAGNI.** Deepening pays off on code that keeps changing, so weight the parts that have moved recently. Decide *where* to look before looking:

- If the user named a direction — a module, a subsystem, a pain point — take it and skip the inference below.
- Otherwise, walk back a stretch of history (`git log --oneline`, `git log --format= --name-only | sort | uniq -c | sort -rn | head -30`) to find the hot spots, and let those paths pull first. Scattered changes with no hot spot → widen the net.

If the project carries a domain glossary (`CONTEXT.md` or equivalent) or an ADR store (`docs/adr/`), read the ones covering the area first — the glossary names good seams, and the ADRs record decisions this skill must not re-litigate. Neither is required; skip what the project doesn't have.

Present the scope — target paths, hot spots, and the grep/glob patterns each agent will use — and **wait for confirmation before dispatching**. Wrong scope contaminates every agent.

Then dispatch **Explore agents in parallel** (`subagent_type: "Explore"`), one per area of the confirmed scope. Don't hand them rigid heuristics — have them explore organically and report where they hit friction, with `file:line` evidence:

- Where does understanding one concept require bouncing between many small modules?
- Where are modules **shallow** — interface nearly as complex as the implementation?
- Where were pure functions extracted just for testability, while the real bugs hide in how they're called (no **locality**)?
- Where do tightly-coupled modules leak across their seams?
- Which parts are untested, or hard to test through their current interface?

Apply the **deletion test** to anything you suspect is shallow: would deleting it concentrate complexity, or just move it? "Concentrates" is the signal you want.

### 2. Present candidates as an HTML report

Cap the report at **5 candidates** — ranked, not exhaustive. A sixth candidate is a follow-up run, not a longer report.

Write a self-contained HTML file to the OS temp directory so nothing lands in the repo: resolve it from `$TMPDIR`, falling back to `/tmp` (`%TEMP%` on Windows), and write `<tmpdir>/architecture-review-<timestamp>.html` so each run gets a fresh file. Open it (`open` on macOS, `xdg-open` on Linux, `start` on Windows) and tell the user the absolute path.

Per candidate: **files**, **problem**, **solution**, **wins** (in terms of locality and leverage, and how tests improve), a **before/after diagram**, and a **recommendation strength** badge (`Strong`, `Worth exploring`, `Speculative`). End with a **Top recommendation** section — which one you'd tackle first, and why.

Full scaffold, diagram patterns, and styling: `HTML-REPORT.md` (same folder).

**Every candidate cites `file:line`.** A candidate with no citation is inference, not evidence — cut it.

**ADR conflicts**: if a candidate contradicts an existing ADR, surface it only when the friction is real enough to warrant reopening that ADR, and mark it in the card (amber callout: *"contradicts ADR-0007 — worth reopening because…"*). Don't enumerate every refactor an ADR forbids.

Do **not** propose interfaces yet. After the file is written, ask: "Which of these would you like to explore?"

### 3. Grilling loop

Once the user picks a candidate, run the `grilling` skill to walk the decision tree with them — constraints, dependencies, the shape of the deepened module, what sits behind the seam, which tests survive. Classify the candidate's dependencies first (`core:codebase-design`'s `DEEPENING.md`); the category decides how the deepened module gets tested across its seam.

Side effects happen inline, as decisions crystallize:

- **Naming a deepened module after a concept the project's glossary doesn't have?** Add the term — via `domain-modeling` if that skill is installed, by editing the glossary directly otherwise. If the project has no glossary, don't create one just for this.
- **User rejects the candidate with a load-bearing reason?** Offer to record it where the project records decisions (an ADR, or `CHANGELOG.md`), framed as: *"want this recorded so a future architecture review doesn't re-suggest it?"* Only when the reason would actually be needed by a future explorer — skip ephemeral ("not worth it right now") and self-evident ones.
- **Want to explore alternative interfaces?** Use `core:codebase-design`'s `DESIGN-IT-TWICE.md` — parallel sub-agents, each designing the interface under a different constraint.

## Inviolable rules

- **No candidate without `file:line`.** Same bar as `core:archaeology`.
- **Glossary terms are not negotiable** — module, interface, implementation, depth, deep, shallow, seam, adapter, leverage, locality. Never "component", "service", "unit" (for module), "API"/"signature" (for interface), "boundary" (for seam).
- **The report never lands in the repo** — temp dir only.
- **Proposals only.** This skill produces a report and a conversation. It does not edit source files; implementation is a separate, explicitly-requested run.

## Not this skill

- **A diff needs reviewing** → `core:review-local` / `core:review-remote`.
- **A ticket needs a map of current state before planning** → `core:archaeology`.
- **A Flutter refactor already written needs a regression pass** → `mobile:refactor-review`.
