# Native → Flutter migration lessons (destination-side, pre-skill corpus)

> Not a `SKILL.md` — this file carries no frontmatter on purpose. It isn't an invocable skill
> draft, just preserved reference material; giving it skill frontmatter would misstate what it is.

**Status: raw material, not a skill.** This is a preserved set of concrete incidents from a
native→Flutter migration pipeline, each with its discriminator and the process fix it earned —
kept as seed material for a future downstream skill, not yet designed as one. `apk-archaeology`
covers the **origin** side of a migration (APK → catalog → purpose-scoped backlog) and stops at
the backlog; these lessons are about the **destination** side (backlog → real Flutter code) —
a different boundary, which is why they don't live inside that skill's chain. Promotion trigger:
a second capability, distinct from the one these lessons came from, completing all 4 phases
(Brainstorming → Spec-Refine → Writing-Plans → Executing-Plans) of a migration pipeline — only
one capability has done that so far (twice), and distilling a method from a single family would
repeat the exact mistake the last lesson below describes.

One related lesson is not repeated here because it is already wired: a correction must sweep
every other finding anchored to the same underlying artifact, not just the one that motivated the
correction. That is `apk-archaeology`'s Relational Fidelity Gate (`plugins/mobile/skills/apk-archaeology/references/method.md`,
post-correction trigger) — it lives there because it's about verifying a *catalog*, which is
squarely that skill's own subject.

## Process-fidelity lessons — within the migration pipeline itself

### 1. An interface can be complete for this user story and still block the next one

**Fix (Brainstorming phase)**: when defining a public interface, run a 3-question checklist:
1. Who consumes this interface in *this* user story?
2. Who consumes it in the *next* one (one-story lookahead)?
3. Does the interface expose enough for (2) without modification?

If (3) is no, expand the interface now. The cost of adding it later is a rename plus a breaking
change plus a new package version — strictly more expensive than getting it right the first time.

### 2. "Plan" and "execute" get silently conflated mid-session

**Fix (session start)**: declare the session's mode explicitly before starting work:

```
Mode: RUN (execute phases with human-in-the-loop decisions)
Mode: DESCRIBE (document what each phase would do, without running it)
```

Suggested default: the first user story of a capability runs in RUN mode (to prove the method
works); subsequent stories default to DESCRIBE unless the tech lead asks for RUN. Within a RUN
story, each phase can still independently be RUN or DESCRIBE.

### 3. Converging on an approach before ever opening the target codebase

**Fix (Brainstorming phase)**: a mandatory sub-phase before any approach gets proposed:

```
Phase 1a — Exploration (~15 min)
  - List existing dependency-injection patterns (how the team registers singletons)
  - Read one complete existing feature end to end (datasource → repository → usecase → state)
  - Identify naming conventions (suffixes, prefixes, barrel exports)
  - Identify existing dependencies already in the manifest

Phase 1b — Proposals (only after 1a)
  - Propose approaches grounded in the patterns found in 1a
```

Skipping 1a produces generic proposals, and the receiving team rejects them — reliably, not
occasionally.

### 4. Literal 1:1 translation from the source language, structural not just syntactic

**Fix (structural)**: the target codebase's own cognitive sequence — its idiomatic step order for
turning a native construct into an idiomatic one, not a transliteration — is the *first* content
a migration methodology states, never an appendix or a closing section: any implementation
session that opens the methodology doc finds it before any phase description. The exit gate that
greps for leftover source-language names is folded into every implementation-plan phase as a
mandatory check before marking anything complete, not offered as a suggestion.

### 5. The same content gets restated, and drifts, across every generated artifact

**Fix (artifact production)**: a fixed rule for where each kind of content lives, so no plan ever
re-authors it:

| Content | Lives in | Plans reference it with |
|---|---|---|
| The cognitive sequence | The methodology doc's own invariant section | A link + "see methodology" |
| The exit gate | The methodology doc's own phase section | Only the command itself (a few lines) |
| The handoff protocol | The methodology doc's own phase section | "Same protocol" |
| User-story-specific decisions/trade-offs | That story's own plan doc | Nowhere else — unique to that plan |

### 6. The second user story in a capability gets a thinner plan than the first

**Fix**: a minimum required skeleton for every per-story plan doc:

```markdown
# Plan: <Capability> migration — Story NN
> Status | Dependency | Input artifacts | Methodology reference

## TL;DR (2-3 lines)
## Prerequisites
## Brainstorming (with trade-offs for discarded alternatives)
## Spec-Refine (gap summary table)
## Writing-Plans (phases with code, deps, gate)
## Requirement-to-phase mapping
## Executing-Plans (session table + gate + handoff)
## Risks
## Out of scope
```

An empty section is declared "N/A" explicitly — never omitted silently.

### 7. Reconnect logic ships without re-subscribe logic

**Fix (Spec-Refine phase)**: a new checklist category, **[Lifecycle completeness]** — for every
state transition the system can go through (connect, disconnect, **reconnect**, login, logout,
kill, resume), ask explicitly what starts, what stops, and specifically **what re-executes on
reconnect**. If any transition has no clear answer in the spec, that's a gap. A spec that says
"reconnects automatically" without saying "and re-subscribes" is a silent *functional* gap — the
most dangerous kind, because it reads as covered.

## Internal artifact-fidelity lessons — generalize to any capability the pipeline migrates

> The four lessons below are not specific to whichever capability first surfaced them — they are
> lessons about the *pipeline's own artifacts* (specs, plans, catalogs), and apply to every future
> migration this method runs, not only the one that exposed the gap.

### 8. A spec's local rule numbering doesn't declare its mapping to the catalog's real ID

**Anti-pattern**: per-story specs numbered their own local rule IDs with an inconsistent offset
against the composite catalog ID each rule actually anchored to — in the worst observed case, a
spec's locally-numbered rule pointed at a composite ID that **existed and described a different
mechanism entirely**. A reader following the local number naively lands on the wrong rule, with
no warning that anything is off.

**Fix (Writing-Plans phase, and in every generated spec)**: every spec that numbers local rule IDs
declares, explicitly and on the rule's own line, the mapping to the catalog's real composite ID.
Never let the reader infer the correspondence from the number alone.

### 9. An anchor that resolves a bare filename, not a full path

**Anti-pattern**: a decompiled source tree had more than one file with the same name in different
packages (a common collision: a networking-library class and an app-specific class sharing a
generic name like `Connection` or `Requests`). An anchor citing only the filename lets a reader
open the wrong file with no warning — and separately, one such anchor cited a class name with a
small typo, nonexistent anywhere in the tree, unnoticed until a manual pass caught it.

**Fix**: every anchor citing a source file carries its full path from the decompile root, never
just the filename. Exit-gate check: a bare filename (no path separator) inside an anchor is a red
flag on its own.

### 10. A count that appears in prose is typed by hand, and hand-typed counts are wrong

**Anti-pattern**: a summary document stated three different counts from memory — a total of new
findings, a total findings count, and a count of mapped handlers — and all three were wrong (one
by double-counting two already-counted items, one off by one after a forgotten item was later
folded in, one because the real dispatch table had a fallback branch nobody added to the count).

**Fix**: any count that appears in prose inside a generated document (a dossier, a reference doc,
a run README) must be mechanically derivable from the underlying catalog at generation time —
never written from memory by whoever drafts the prose. If an agent generates the doc, it counts
before writing; if a human reviews it, re-deriving the count is the first thing to do before
approving.

## Destination-reality lessons — fidelity to the actual target codebase, not just to the pipeline's own artifacts

> The two lessons below come from a broader audit than the pipeline's own artifact set — they are
> about whether a migration claim is true of the **real destination codebase**, not just internally
> consistent between the pipeline's own documents.

### 11. "Not in the manifest" is not evidence that something doesn't exist in the codebase

**Incident**: a grep across every manifest file in a multi-package workspace, for a known set of
webview/realtime/networking dependency names, returned exactly one hit — commented out. The
natural reading was "greenfield, nothing here yet." The reality: a complete, in-production webview
bridge; a realtime SDK actively initializing — all pulled in **transitively** through a shared
dependency-aggregator package that wasn't checked out locally, so no manifest in the workspace
could show it. A smaller instance of the same failure, in the same audit: a spec read "zero usage
of a specific reactive primitive" as evidence that a whole capability was unimplemented, when what
was actually absent was one specific *pattern* — a working implementation of the same behavior
existed under a differently-named helper in the session-handling module.

**Discriminator**: does the project centralize dependencies through an aggregator package? If so,
a manifest has **zero** evidentiary value for absence. Verification against the real destination
is by **usage** — a symbol or import actually present in the source tree — never by manifest
inspection alone. The absence of a resolved lockfile/build-tool cache is itself the warning sign:
nothing has been resolved locally, so the manifest doesn't even describe the real dependency
graph.

**Fix (Spec-Refine phase)**: before marking any capability a "greenfield gap," grep for
**symbol/import usage in the source tree**, not only for a declared dependency in the manifest. If
the project uses a dependency-aggregator package, this step is mandatory, not optional —
mechanizable as an extractor that flags "manifest-silent but symbol-present."

### 12. Inspection scoped to one capability quietly travels as a claim about the whole program

**Incident**: a reference doc honestly recorded "destination-codebase state (inspected on
`<date>`)" — scoped, correctly, to one specific capability. No other capability had an equivalent
inspection recorded. A later sprint-level document then read a *different*, uninspected capability
(the single largest group of findings in the catalog) as "no visible candidate" — without anyone
having actually looked at the real destination code for that capability — when a real candidate
existed and was obvious once checked by usage (lesson 11's discriminator).

**Discriminator**: every "greenfield" or "no candidate" claim carries the scope of the inspection
that produced it. A greenfield claim with no declared inspection scope is an inference wearing the
clothes of a fact, not a fact.

**Fix (Brainstorming phase)**: every "greenfield" or "no candidate" statement that enters a
plan/sprint document carries, on the same line, exactly which capability was inspected and when —
never inherited by extension from a neighboring capability's inspection. If the capability in
question wasn't actually inspected, the correct label is "not inspected," never "greenfield."
