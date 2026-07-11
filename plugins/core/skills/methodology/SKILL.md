---
name: methodology
description: Invoke when the always-on tier (using-agent-kit) isn't enough — methodology for more specific application (verification, evidence, scope, investigation, exploration, shared tooling) and portable technical reference for Claude Code (hooks, advisor), git (rerere, partial revert), and Flutter/Dart (build_runner). Triggers: "could this gate false-negative?", "is this criterion a proxy for the real goal?", "hook didn't fire", "post-release partial revert", "about to call it done/execute — did I verify the final artifact?".
---

# Methodology — tier 2 (on-demand)

Extension of `using-agent-kit`: that tier holds the highest-recurrence principles (always-on); this one holds methodology that's equally valid but more specific in application, plus technical reference portable across projects.

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

### A self-created artifact is not independent evidence

A card/doc/draft you created yourself (or created on request) doesn't count as independent evidence for a conclusion — it only echoes the framing you already had. Before citing an artifact as evidence, check its provenance: if it came from you/your session, exclude it from the scale and rebuild the argument using only independent sources (the original spec, code, commits, third-party decisions).

**Signal**: a conclusion cites, as corroboration, an artifact produced by the session itself or at its request.

**Failure mode**: circular judgment; inflated confidence in a fragile conclusion that doesn't survive an independent source.

---

### Evidence is re-read in its current state and generated, not transcribed

Before listing a finding (review, audit, enumeration), re-read the evidence in its current state — current file, confirmed cwd, an untruncated command (`head`/`tail` masks count/topology) — never from an old snapshot. And when the deliverable is a human-readable list derived from a structured source, generate it via script over the source, even with small N (same commandment as §Verification gate, "How to apply").

**Signal**: a finding cited without re-reading in the same turn; a negative claim ("X doesn't exist") from a search with unconfirmed cwd; a final list with no command/script that generated it.

**Failure mode**: the list cites an already-fixed item or misses a real one — a single detected error destroys the credibility of the entire deliverable.

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

### Exploration output uses an opportunity frame, with anchored severity

In mapping/exploration output meant for a decision (not a point-in-time review), prefer "Improvement opportunities" over "Risks"/"Removals". Anchor severity to an explicit rubric (blocks the decision vs. has a workaround vs. known debt), not vibe. Open with a short TL;DR, rank at most ~5 key items, cite file:line per item — no citation is inference, cut it.

**Signal**: severity with no rubric; no TL;DR; more than ~5 items all "priority".

**Failure mode**: the reader gets a wall of data and has to redo the prioritization the report should have done.

---

### Consolidation checkpoint and advisor gate at the transitions that commit

In a long investigation, don't stack parallel hypotheses without closing each one — periodically (and whenever the direction is challenged) produce a single frame: proven-with-evidence vs. open, and ONE next step. For a critical topic, linear investigation alone isn't enough: fan out by dimension and verify each finding against the primary source before synthesizing. At the transitions that commit, verify the FINAL artifact (not just the approach): leaving planning, use the advisor; declaring done, prefer a blind adversarial subagent — the advisor sees the whole conversation and inherits the "looks done" blind spot (see §Native advisor below).

**Signal**: 3+ parallel hypotheses never closed; a plan→execution transition or a "done" claim with no independent verification of the final artifact.

**Failure mode**: noise consumes the session with no throughline; a gap a fresh reviewer would catch only surfaces hours into execution.

**How to apply**: a trivial plan (typo, single rename) skips the gate; ≥3 items or ≥1 code phase goes through it.

## Technical Reference

### Claude Code

- **Hook payload**: `PostToolUse` receives `tool_response` (an object with the result), not `tool_output`; `UserPromptSubmit` delivers `prompt` (raw text). The format varies by hook event — check the official schema (`docs/en/hooks`) before assuming a field.
- **`UserPromptSubmit` JSON output**: to inject context, `additionalContext` must be nested under `hookSpecificOutput` (`{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "..."}}`). At the root level it's valid JSON but **silently discarded** (exit 0, no error) — the smoke test has to check the effect, not just the exit code.
- **Checking whether a hook is registered**: check BOTH sources — user settings (`~/.claude/settings.json`) AND project settings (`.claude/settings.json` + `.claude/settings.local.json`) — before concluding "not registered". Checking only one source has already produced a wrong claim, including from a blind adversarial reviewer who checked the wrong source.
- **`.claude/rules/` vs. `.claude/docs/` vs. `.claude/skills/`**: `rules/*.md` is auto-loaded (the only mechanism that fires at generation time); `docs/*.md` is inert — it only loads if some wired consumer references it explicitly (review-time); `skills/` (SKILL.md) is on-demand but auto-discovered via the description. A rule that needs to shape code at generation time goes in `rules/`, not `docs/`.
- **Native advisor** (`/advisor <model>`): a server-side tool that consults a stronger model at decision points; Claude itself decides when to call it (model-driven, not a rule). It ALWAYS receives the whole conversation — there is no blind mode. Good for planning (context helps); bad for breaking a self-assessment blind spot ("looks done") — prefer a blind adversarial subagent there (minimal input, mandate to refute).
- **Model vs. effort**: two axes, not one. Switching models swaps the weights — what Claude *knows*; effort regulates how much work it does before calling it done — how many files it reads, how much it verifies, how far it goes on a multi-step task without checking with you. Wrong result: fix the input first (prompt, tools, skills, context — the most common cause of error is not a setting); if it skipped a file/test/verification, raise effort ("didn't try hard enough"); if it read everything, clearly tried, and confidently kept being wrong, raise model ("didn't know enough"). Effort is a general per-domain preference, not a per-task tweak. Mental model: Fable is the specialist for problems almost no one else can crack, Opus the expert, Sonnet a strong generalist — effort is how much time any of them spends. The cost/quality trade-off flips with difficulty: on routine work a bigger model just adds verification tokens at a higher per-token price for the same result (drop it — cuts cost and latency, no meaningful quality loss); on hard multi-step work the smaller model burns iterations grinding toward its ceiling, so the bigger model can cost *less* per task — and can finish tasks the smaller one can't reach at any effort. Effort shapes token consumption but doesn't cap it — the only hard cap is `max_tokens` (truncates mid-stream; mostly an API concern); guide with soft budgets or "keep it brief", which the model is trained to wind down toward as it nears the limit.

### Git

- **`rerere` can silently reapply a wrong resolution**: with `rerere.enabled=true`, redoing a cherry-pick/merge whose earlier attempt resolved a conflict WRONG makes git reapply the recorded resolution (`using previous resolution`) — no conflict markers, no visual warning. When retrying after a buggy resolution, purge that day's entries in `.git/rr-cache` (or run with `-c rerere.enabled=false`) before continuing.
- **Recovering a feature from a partial revert**: when a revert kept the infra and reverted only the UI, reapplying the original feature via cherry-pick generates "already applied" conflicts (the infra is already there). The surgical path is `git revert -m 1 <revert-commit>` — reverts the revert, bringing back exactly what was removed, nothing more. Signal to use this path: the revert's diffstat is much smaller than the original feature's (partial revert); if it's symmetric, it's a full revert and a direct cherry-pick is safe.

### Flutter / Dart

- **`build_runner` regenerates files outside the change's scope**: running `build_runner build` for a targeted DI change can regenerate dozens of unrelated modules' `.g.dart` files from purely cosmetic churn (formatting drift between toolchain versions). After running it, restrict the commit to the files actually relevant: list the touched `.g.dart` files, revert the out-of-scope ones, keep only what the change actually asked for. Don't accept "it's pre-existing" from a subagent without checking yourself with `git diff`.
