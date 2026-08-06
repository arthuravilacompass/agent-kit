---
name: methodology
description: A corpus to read, not a conductor — it holds rules to consult and never structures, sequences, or drives a session; conduction lives in CE (`/ce-*`) and discovery in superpowers. Invoke when the always-on tier (using-agent-kit) isn't enough — completes two of its rules with rationale/exception, plus a verification-gate note and a pointer to portable technical reference for Claude Code (hooks, advisor), git (rerere, partial revert), and Flutter/Dart (build_runner) in references/technical-reference.md. Triggers: "could this gate false-negative?", "hook didn't fire", "post-release partial revert".
---

# Methodology — tier 2 (on-demand)

Extension of `using-agent-kit`: that tier holds the highest-recurrence principles (always-on) with their rule and Signal; this file holds the rationale/exception for two of them, plus a verification-gate note and a pointer to portable technical reference (`references/technical-reference.md`).

**2026-08-06**: this file used to also carry 16 additional methodology sections (broad-goal-as-proxy, pre-existing-issue-as-follow-up, self-created-artifact-not-evidence, evidence-re-read-current-state, grep-before-answering, evidence-before-claim, measure-before-building, shared-tooling-layers, two-read-paths, exploration-opportunity-frame, analysis-is-a-means, consolidation-checkpoint, confirm-the-route, worker-output-contract, and others). None had an inbound reference from anywhere else in the kit, and the skill was invoked 2 times across 1,680 transcripts in the 30 days before this cut. Moved to `~/.claude/backups/simplify-2026-08-06/methodology.SKILL.md.pre-cut-2026-08-06` rather than lost — restore individually, with the concrete gap that motivated it, if one is missed.

## Methodology

### A verification gate must not derive from the artifact under test itself

A gate that proves "X is clean/correct" can't compute the truth from X itself when X had its history or provenance rewritten/reconstructed — the test loses its reference point and becomes a silent false negative, which is worse than no gate at all (it gives false confidence).

**Signal**: the gate derives the "clean" criterion by inspecting the reconstructed artifact, not a reference that retains the original history.

**Failure mode**: the gate reports green with the problem still present; it only surfaces later, in production or a manual audit.

**How to apply**: compute the criterion from a ref that retains the relevant history (an old branch, a diff of a slice with history); generate the violation list programmatically instead of by hand; the gate only checks presence/absence in the final artifact. Add an inverse gate when applicable (what shouldn't have changed, didn't) — proving cleanliness requires proving both sides.

---

### No silent removal of annotations/imports — detail

Descended from the always-on tier (`using-agent-kit`) — the rule and its **Signal** stay there; this holds the exception.

**Exception**: an import genuinely unused, flagged by the linter.

---

### Fix at the source, never at the consequence — detail

Descended from the always-on tier (`using-agent-kit`) — the rule and its **Signal** stay there; this holds the rationale.

**Why**: masking the bug downstream guarantees it resurfaces when the context changes.

**Failure mode**: the bug reappears in another caller; the root cause remains in the codebase.

## Technical Reference

Portable reference for Claude Code (hooks, advisor), git (rerere, partial revert), and Flutter/Dart (`build_runner`) — moved out to `references/technical-reference.md` to keep this tier's body to epistemic discipline only.
