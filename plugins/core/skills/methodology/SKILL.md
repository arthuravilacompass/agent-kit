---
name: methodology
description: A corpus to read, not a conductor — it holds rules to consult and never structures, sequences, or drives a session; conduction lives in CE (`/ce-*`) and discovery in superpowers. Invoke when the always-on tier (using-agent-kit) isn't enough — methodology for more specific application (verification, evidence, scope, investigation, exploration, shared tooling) and a pointer to portable technical reference for Claude Code (hooks, advisor), git (rerere, partial revert), and Flutter/Dart (build_runner) in references/technical-reference.md. Triggers: "could this gate false-negative?", "is this criterion a proxy for the real goal?", "hook didn't fire", "post-release partial revert", "about to call it done/execute — did I verify the final artifact?", "Mermaid hand-drawn look not rendering", "workflow diagram reads as generated/generic", "the map/investigation just closed — build now, or another pass first?"
---

# Methodology — tier 2 (on-demand)

Extension of `using-agent-kit`: that tier holds the highest-recurrence principles (always-on); this one holds methodology that's equally valid but more specific in application, plus a pointer to a portable technical reference (`references/technical-reference.md`).

## Methodology

### A verification gate must not derive from the artifact under test itself

A gate that proves "X is clean/correct" can't compute the truth from X itself when X had its history or provenance rewritten/reconstructed — the test loses its reference point and becomes a silent false negative, which is worse than no gate at all (it gives false confidence).

**Signal**: the gate derives the "clean" criterion by inspecting the reconstructed artifact, not a reference that retains the original history.

**Failure mode**: the gate reports green with the problem still present; it only surfaces later, in production or a manual audit.

**How to apply**: compute the criterion from a ref that retains the relevant history (an old branch, a diff of a slice with history); generate the violation list programmatically instead of by hand; the gate only checks presence/absence in the final artifact. Add an inverse gate when applicable (what shouldn't have changed, didn't) — proving cleanliness requires proving both sides.

---

### A broad goal doesn't collapse into a proxy

When the request is broad or qualitative and lacks an explicit acceptance criterion, design the success criterion so it FAILS if the real goal wasn't met — not a proxy satisfied by content that already existed. When simplifying, separate incidental complexity (tooling, build steps — cut freely) from essential value (new content/views — preserve).

**Signal**: the success criterion passes even though nothing of the stated goal changed; or a simplification pass removes new content along with incidental machinery.

**Failure mode**: the deliverable passes the criterion but doesn't solve what was asked; rework follows once someone notices the gap.

---

### A pre-existing issue becomes a follow-up, not a fix in the same PR

Don't fix, in the current PR, problems the change didn't introduce — functional, cosmetic, or common tech debt become a separate ticket. Exception: security (data/credential leak) is treated as an incident, not a deferrable follow-up.

**Signal**: the diff includes a fix for something that was already broken before the change, unrelated to the PR's goal.

**Failure mode**: PR scope inflates, review gets harder, regression risk in an unrelated area.

---

### Edit only in scope — detail

Descended from the always-on tier (`using-agent-kit`) — the **Signal** stays there, and the rule statement is question 1 of that tier's `3 Questions Before Editing`; this holds the rationale.

**Why**: editing "while I'm in here" hijacks the PR and makes review impossible.

**Failure mode**: review becomes impossible; rollback requires manual cherry-pick.

---

### No silent removal of annotations/imports — detail

Descended from the always-on tier (`using-agent-kit`) — the rule and its **Signal** stay there; this holds the exception.

**Exception**: an import genuinely unused, flagged by the linter.

---

### A self-created artifact is not independent evidence

A card/doc/draft you created yourself (or created on request) doesn't count as independent evidence for a conclusion — it only echoes the framing you already had. Before citing an artifact as evidence, check its provenance: if it came from you/your session, exclude it from the scale and rebuild the argument using only independent sources (the original spec, code, commits, third-party decisions).

**Signal**: a conclusion cites, as corroboration, an artifact produced by the session itself or at its request.

**Failure mode**: circular judgment; inflated confidence in a fragile conclusion that doesn't survive an independent source.

---

### Verify your own claim as adversarially as an agent's — detail

Descended from the always-on tier (`using-agent-kit`) — the rule and its **Signal** stay there; this holds the rationale.

**Why**: a review that inherits the framing of whoever produced the work — including yourself — carries the same blind spot.

**Failure mode**: a wrong claim escalates into the narrative; a framed review lets through what a blind check would catch.

---

### Evidence is re-read in its current state and generated, not transcribed

Before listing a finding (review, audit, enumeration), re-read the evidence in its current state — current file, confirmed cwd, an untruncated command (`head`/`tail` masks count/topology) — never from an old snapshot. And when the deliverable is a human-readable list derived from a structured source, generate it via script over the source, even with small N (same commandment as §Verification gate, "How to apply").

**Signal**: a finding cited without re-reading in the same turn; a negative claim ("X doesn't exist") from a search with unconfirmed cwd; a final list with no command/script that generated it.

**Failure mode**: the list cites an already-fixed item or misses a real one — a single detected error destroys the credibility of the entire deliverable.

---

### Grep before answering about convention — detail

Descended from the always-on tier (`using-agent-kit`) — the rule and its **Signal** stay there; this holds the rationale and the exception.

**Why**: an answer based only on memory or generic heuristics fails when the project already uses a specific lib (e.g.: the project's logging lib, the chosen observability tool, the adopted serialization lib, etc.) — the generic answer is plausible but wrong for this codebase.

**Does NOT apply when**: purely conceptual questions ("what is X?"), not about how the *project* does it.

---

### Evidence before claim — detail

Descended from the always-on tier (`using-agent-kit`) — the rule and its **Signal** stay there; this holds the rationale and the application steps.

**Why**: premature assumption is the most common cause of rework in review — the model generates plausible-but-wrong text when it lacks evidence, and the reviewer spends an extra turn refuting it with real data. Examples: assuming a remote-config flag's behavior without reading the config, inferring an environment is "beta" without checking, inventing a route/endpoint that doesn't exist, proposing `-m 1` on a commit that isn't a merge.

**How to apply**: before asserting X about code, list the file(s)/command(s) you need to inspect. Don't conclude until you've read them. If tempted to use "should/likely/assuming/probably", stop and `grep` instead.

**Failure mode**: the reviewer refutes it with evidence (log, code); wasted turn; eroded trust; in repeated cases, the user stops trusting future claims.

---

### Measure before building has a precondition — it isn't a universal law

When a target's existence/base rate is unknown (rare target, silent failure, untested hypothesis), measure before building the solution. But only while the precondition holds: if the direction has already been explicitly decided, reintroducing the measurement gate — even reframed — isn't rigor, it's resistance to the decision.

**Signal**: post-build measurement shrinks the target every round (a solution built on presumption); or the gate reappears reframed after an explicit decision was already made.

**Failure mode**: an isolated anecdote becomes a subsystem before confirming its real size; or, conversely, repeated measurement becomes a delay that never converges into delivery.

---

### Shared tooling separates infrastructure, team standard, and personal preference

When distributing configuration others will inherit, separate three layers: universal infrastructure (shared level), team standard (agreed convention, with explicit enforcement), and personal preference (individual style — user/local level, never in the shared layer).

**Signal**: shared config carries one individual's preference that the team never agreed on as a standard.

**Failure mode**: onboarding friction; config rots fast because personal preference changes more often than team standard.

**How to apply**: before committing a shared-config item, ask "would a competent colleague reasonably disagree with this?" — if yes, it's a personal-layer concern.

---

### Two independent read paths require instrumenting both

When a value has two read paths to the same logical data (one layer renders from one source, a validation reads from another), don't treat one as proof that the other has the same value — map and instrument both at the layer boundaries before forming a hypothesis.

**Signal**: the hypothesis assumes "layer A shows X" implies layer B also has X, without checking B directly.

**Failure mode**: the hypothesis applied before the full chain is mapped fixes nothing; the investigation cycle gets redone from scratch.

**Does NOT apply when**: the bug already has a root cause localized to a single layer.

---

### Fix at the source, never at the consequence — detail

Descended from the always-on tier (`using-agent-kit`) — the rule and its **Signal** stay there; this holds the rationale.

**Why**: masking the bug downstream guarantees it resurfaces when the context changes.

**Failure mode**: the bug reappears in another caller; the root cause remains in the codebase.

---

### Exploration output uses an opportunity frame, with anchored severity

In mapping/exploration output meant for a decision (not a point-in-time review), prefer "Improvement opportunities" over "Risks"/"Removals". Anchor severity to an explicit rubric (blocks the decision vs. has a workaround vs. known debt), not vibe. Open with a short TL;DR, rank at most ~5 key items, cite file:line per item — no citation is inference, cut it.

**Signal**: severity with no rubric; no TL;DR; more than ~5 items all "priority".

**Failure mode**: the reader gets a wall of data and has to redo the prioritization the report should have done.

---

### Analysis is a means, not a deliverable

When an analysis, map, or investigation closes, the default next move is the concrete construction it enables — not another round of analysis. Recommending more analysis requires naming the decision it unblocks. The exception is work whose deliverable *is* the report: there, the report is the construction.

**Signal**: an analysis closes and the recommended next step is more analysis, with no named decision waiting on it.

**Failure mode**: the session cycles through investigation after investigation, producing more maps and no delivered change; effort accumulates with nothing built on top of it.

---

### Consolidation checkpoint and advisor gate at the transitions that commit

In a long investigation, don't stack parallel hypotheses without closing each one — periodically (and whenever the direction is challenged) produce a single frame: proven-with-evidence vs. open, and ONE next step. For a critical topic, linear investigation alone isn't enough: fan out by dimension and verify each finding against the primary source before synthesizing. At the transitions that commit, verify the FINAL artifact (not just the approach): leaving planning, use the advisor; declaring done, prefer a blind adversarial subagent — the advisor sees the whole conversation and inherits the "looks done" blind spot (see §Native advisor below).

**Signal**: 3+ parallel hypotheses never closed; a plan→execution transition or a "done" claim with no independent verification of the final artifact.

**Failure mode**: noise consumes the session with no throughline; a gap a fresh reviewer would catch only surfaces hours into execution.

**How to apply**: a trivial plan (typo, single rename) skips the gate; ≥3 items or ≥1 code phase goes through it.

---

### Confirm the route before crossing plan → execution — detail

Descended from the always-on tier (`using-agent-kit`) — the rule and its **Signal** stay there; this holds the rationale.

**Why**: going straight to output buries silent choices that only surface after the work is done. The plan → execution boundary is where the omission costs most, because everything downstream inherits the unconfirmed reading.

**Failure mode**: wasted effort when the understanding was wrong; eroded trust. A broad licence read as a waiver of the checkpoint is the specific way this fails.

**How to apply**: at the opening of each heavy phase, list the route and the stages you intend to skip, and confirm. The harness default already covers checking in when competing readings would change the work materially; this rule is the narrower, stronger case — the stage boundary itself.

---

### NO-COMMIT — detail

Descended from the always-on tier (`using-agent-kit`, §Permissions) — the rule and its **Signal** stay there; this holds the rationale.

**Why**: committing or pushing on the user's behalf bypasses their review of what goes on the branch and in history.

**Failure mode**: unwanted commits on the wrong branch; history rewrite required.

---

### Worker output contract

Descended from the always-on tier (`using-agent-kit`, §Dispatch) — the trigger ("required at the end of every dispatch") stays there as a one-line pointer; this holds the full contract.

- Verdict + evidence + `file:line` refs, max 10 bullets, no raw logs or transcript.
- **STOP on a pending decision**: if anything depends on the operator, return only a numbered `PENDING DECISIONS` block — do not decide alone.
- On a code change: run build/tests and report the result.
- Long outputs go to a file; the chat gets the path plus a 3-line summary. This applies to the main thread too.

## Technical Reference

Portable reference for Claude Code (hooks, advisor), git (rerere, partial revert), and Flutter/Dart (`build_runner`) — moved out to `references/technical-reference.md` to keep this tier's body to epistemic discipline only.
