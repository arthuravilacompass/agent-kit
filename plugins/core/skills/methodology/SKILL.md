---
name: methodology
description: Invoke when the always-on tier (using-agent-kit) isn't enough — methodology for more specific application (verification, evidence, scope, investigation, exploration, dispatch/orchestration, shared tooling) and portable technical reference for Claude Code (hooks, advisor), git (rerere, partial revert), and Flutter/Dart (build_runner). Triggers: "could this gate false-negative?", "is this criterion a proxy for the real goal?", "hook didn't fire", "post-release partial revert", "about to call it done/execute — did I verify the final artifact?", "should this fan out / dispatch a subagent / open a background session?".
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

### Edit only in scope — detail

Descended from the always-on tier (`using-agent-kit`) — the rule and its **Signal** stay there; this holds the rationale.

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

### Fix scope = reported-bug scope — detail

Descended from the always-on tier (`using-agent-kit`) — the rule and its **Signal** stay there; this holds the failure mode.

**Failure mode**: the action stays broken; the delivery looks like progress but the reported bug remains open.

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

---

### Confirm understanding before producing — detail

Descended from the always-on tier (`using-agent-kit`) — the rule and its **Signal** stay there; this holds the rationale.

**Why**: going straight to output buries silent choices that only surface after the work is done.

**Failure mode**: wasted effort when the understanding was wrong; eroded trust.

---

### NO-COMMIT — detail

Descended from the always-on tier (`using-agent-kit`, §Permissions) — the rule and its **Signal** stay there; this holds the rationale.

**Why**: committing or pushing on the user's behalf bypasses their review of what goes on the branch and in history.

**Failure mode**: unwanted commits on the wrong branch; history rewrite required.

## Dispatch — who executes

Who runs a piece of work — the main thread, a subagent, or an external session — is a decision, not a default. `using-agent-kit` carries the signal (when to consider dispatch); this section carries the doctrine (how to do it safely). The fan-out/pipeline mechanics themselves live in superpowers — this is the decision layer, not a duplicate of them.

### Choosing the executor

The discriminating question is the lifecycle contract, not the task's size: **can this need an operator decision mid-flight?**

- **May fork into a decision** → external session (`claude --bg` / Agent View). Only the operator opens sessions; you suggest, you don't open. A diagnosis with a branching root cause ("Path A vs Path B") belongs here — the fork is exactly where a subagent, which has no channel back to the operator, would strand the decision.
- **Read-heavy, no mid-flight decision** → subagent. Pure research/exploration; the operator doesn't need to steer.
- **Synthesis that consumes other results** → the main thread. It already holds the returned summaries; reconciling them is its job, not a delegate's.

Worked shape: a diagnosis-that-forks = session; the research it depends on = subagent (dispatched in parallel); the consolidation of both = main thread. Tasks that *look* equally parallelizable separate by which one carries a dependency and which one can fork — not by how many agents you could open.

### Dispatch contract

A subagent starts near-zero: it gets its system prompt, environment, the CLAUDE.md/memory hierarchy, a git snapshot, named skills — and nothing else. Any path, error message, branch name, or decision already made in the conversation must be written into the dispatch. "Fix the button" produces wrong work.

Output contract, required at the end of every dispatch:

- Verdict + evidence + `file:line` refs, max 10 bullets, no raw logs or transcript.
- **STOP on a pending decision**: if anything depends on the operator, return only a numbered `PENDING DECISIONS` block (question + options) — do not finalize or decide alone. (Label in English here; a real dispatch mirrors the operator's language, per kit convention.)
- On a code change: run build/tests and report the result.

Long outputs go to a file — the chat gets the path plus a 3-line summary. This applies to the **main thread too**, not only subagents: any long deliverable (doc, analysis, plan) is written to a file, never streamed into the chat, so a turn can't be lost to an output-length error.

### Fan-in contract

The synthesis after a fan-out accounts for **every dispatched front**. A front that couldn't be resolved is flagged explicitly — never silently dropped. When several fronts run in parallel, the reconciliation names each one and its status before summarizing.

### Tool scoping

Research/audit agents are read-only (`Read`, `Grep`, `Glob`). **Omitting the `tools` field grants everything, including MCP** — scope deliberately. An edit that would need approval stays in the main thread or runs in the foreground: a background agent auto-denies the approval prompt and fails silently while reporting success.

### Model routing

Execution dispatch goes to the cheaper model — per-agent (`model` field) or globally (`CLAUDE_CODE_SUBAGENT_MODEL`); keep the main thread on the stronger model for reconciliation. The model-vs-effort trade-off that decides *which* tier fits a given leg lives in the Technical Reference below (§Claude Code, "Model vs. effort") — this subsection is only its application to dispatch, not a restatement.

### Extra-session cheat sheet

Commands verified against CLI 2.1.207 (2026-07-11); items marked `[nota]` are not reconfirmed against this CLI version.

- `claude agents` — open the background-session dashboard. `[verificado]`
- `claude --bg "<task>"` — dispatch a background session from the shell. `[verificado]`
- `claude --bg --model sonnet --effort high "<task>"` — background session with explicit model/effort. `[verificado]`
- `claude --tools "Read,Grep,Glob" "<task>"` — force read-only for a whole session. `[verificado]`
- `claude agents --json [--all]` — list sessions, scriptable. `[verificado]`
- `claude -r` — picker to resume a session by id. `[verificado]`
- In-session: `/agents` (running + library), `/tasks` (background in this session), `Ctrl+B` (send a running subagent to background). `[nota]`

A background session is **local**: it dies with the process or if the machine sleeps. `[nota]` Before deleting a session that edited files, merge/push its worktree (`.claude/worktrees/`) — it is removed with the session. `[nota]` Subagents do not open subagents; orchestration always lives in the main thread. `[nota]`

### Routing to superpowers

This section decides *who executes*; the mechanics of each pattern live in superpowers — don't duplicate them:

- Parallel fan-out over independent tasks → `superpowers:dispatching-parallel-agents`.
- Executing a written plan task-by-task → `superpowers:subagent-driven-development`.
- Reviewing a diff/PR with a reviewer panel → the kit's review skills (`core:review-local`).

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
