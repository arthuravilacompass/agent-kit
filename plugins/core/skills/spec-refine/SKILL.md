---
name: spec-refine
description: Invoke to stress-test a spec or design doc before it becomes an implementation plan — exposes gaps, ambiguous states, missing error paths, and unwritten invariants, one focused question at a time. Run after `core:tech-breakdown` (if available) and before `superpowers:writing-plans`.
disable-model-invocation: true
---

# spec-refine — Adversarial Spec Refinement

## Project config

This skill lets the consumer project optionally define:
- **Additional domain checks** for Step 2 — e.g. i18n/l10n coverage for new strings, stack-specific async concurrency patterns (mutations outside an atomic section after an `await`), external contract (API/BFF) fields guarded against null/absent. If the project defines nothing, Step 2 runs with only the 7 generic categories in the table below.

Stress-test a feature spec before it enters planning. Acts as a skeptical senior engineer who exposes gaps, ambiguous states, missing error paths, and unwritten invariants — one focused question at a time.

## When to Use

Run **after** `core:tech-breakdown` (if available in this kit) produces a spec and **before** `superpowers:writing-plans` turns it into an implementation plan. This is the adversarial second pass that catches what the first pass misses.

Also usable standalone: paste any spec or design doc and run this skill.

## Steps

1. **Receive the spec**

   The user either:
   - Runs this right after `core:tech-breakdown` — in which case the spec is already in context
   - Pastes a spec directly into the chat

   If neither, ask: "Please paste the spec or design you'd like stress-tested."

2. **Analyze silently first**

   Before asking any questions, read the spec and identify candidates for each of these gap categories:

   | Category | What to look for |
   |---|---|
   | **Error paths** | Actions that can fail but have no stated failure handling |
   | **Empty/null states** | Data that could be absent, empty list, or null with no defined behavior |
   | **Concurrent operations** | Multiple actions that could race (double-tap, fast navigation, background refresh) |
   | **State transitions** | Implicit transitions — what triggers X to become Y? Is it reversible? |
   | **Scope boundaries** | "This screen" without defining what happens when user navigates away mid-flow |
   | **External dependencies** | Fields assumed present in an external contract but not guaranteed by it |
   | **Invariants** | Assumptions stated as "always" or "never" without enforcement mechanism |

   If the project defined domain-specific checks (see **Project config**), treat each as an additional category.

   Prioritize: ask about gaps where an unstated assumption would cause a real user-facing bug first.

3. **Ask questions one at a time**

   Ask the highest-priority question first. Wait for the answer before asking the next.

   For each question:
   - State the gap category briefly: `[Error path]`, `[Empty state]`, `[Concurrent ops]`, etc.
   - Name the specific section or component the gap is in
   - Ask a single, focused question
   - Provide your recommended answer (what you'd do if you had to implement this today)

   Example format:
   ```
   [Error path] Repository layer — `loadAddresses()`

   If the backend returns a 503 during checkout, the spec doesn't define whether the user
   sees an error state, a retry button, or falls back to manual input.

   Recommended: show an inline error with a retry CTA; do not clear any previously loaded
   data. What's the intended behavior?
   ```

4. **Continue until no more gaps**

   Ask 5–8 questions covering different categories. Avoid asking about the same category twice unless a previous answer introduced a new gap.

   If the user says "enough" or "done" or "looks good", stop questioning and move to step 5.

5. **Produce gap summary**

   After all questions are answered, output a **Gap Summary**:

   ```
   ## Spec Gaps Resolved — <Feature Name>

   ### Decisions Made
   | Gap | Decision |
   |---|---|
   | [Error path] loadAddresses failure | Show inline error + retry; retain existing addresses |
   | [Empty state] cart items on first load | Show empty-state illustration, not error |
   | ... | ... |

   ### Assumptions Still in Spec (Accepted Risk)
   - <assumption> — user accepted, no change to spec
   - ...

   ### Spec Sections to Update Before Planning
   - Section X: add failure handling for [scenario]
   - Section Y: define empty-state behavior
   ```

6. **Ask how to proceed**

   > "Gap summary is ready. Options:
   > - `update spec` — I'll incorporate the decisions into the spec document now
   > - `proceed to plan` — move directly to `superpowers:writing-plans` with these decisions as addenda
   > - `done` — keep the gap summary in context only"

## Fat signals to cut

Before finalizing the artifact, re-read it looking for:

- **Background duplicating the card/ticket** — if it's on the card, no need to repeat it here.
- **"Alternatives Considered" with no decision** — if you didn't choose, don't encode it.
- **Code examples that will be in the diff** — reference the diff, don't duplicate it.
- **File lists with no "why"** — an entrypoint with no reason to touch it is noise.
- **Redundant "Background" + "Motivation" + "Context" sections** — pick one.

If 2+ signals appear, there's probably ~30% cuttable fat. Whether to cut or justify keeping it is your call.

## Important

- Ask questions that expose **user-visible bugs**, not style preferences.
- Every question must include a recommended answer — the goal is to close the gap, not just surface it.
- Do not ask more than 8 questions unless the spec is unusually large (>500 lines). Depth beats breadth.
- Do not ask about implementation choices already resolved in the spec — only gaps.
- Domain-specific checks defined in **Project config** count as first-class gap categories, not an afterthought.
