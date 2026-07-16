---
name: pipeline
description: Invoke when receiving a raw intent for substantial work (feature, bug, investigation, refactor, ticket/US) with no flow already underway, or when the user asks "where do I start", "what's the flow for this", "guide me through this work". Do NOT invoke for a conceptual question or a point lookup ("how does X work?"), nor when a flow is already underway (brainstorming, plan in execution, review). Flow conductor — detects the task's real stage, classifies the intent, and routes through the kit's skills one stage at a time; recommends the next route — and proposes running core:orchestrate when the work is fan-out-shaped — never executes the whole chain by itself.
---

# Pipeline — flow conductor

Kit routing layer: the user's message carries only the **intent**; this conductor decides **where it enters** and **what the next step is**; the stage skills execute. Doesn't replace any skill — it references them.

## 1. Detect the real stage (always first)

Before classifying, look at what already exists:

- Recent `docs/superpowers/{specs,plans,handoffs}` — a ready spec means don't reclarify; a ready plan means go to implementation; a recent handoff means resume from there.
- `git log`/`git status` — half-done code indicates implement/review stage.
- A loop manifest (`docs/superpowers/loops/<slug>.md`) if one exists — it supplies active roles / delegated / pending / mode. **Live detection above is authoritative for the stage**; the manifest only supplements. (Convention: `references/loop-manifest.md`.)

If the task is already underway: state what stage it's at, with evidence, and propose the route from there. Never re-run a stage already completed.

## 2. Classify the intent

| Class | Route |
|---|---|
| New feature | map? → clarify → specify → checkpoint → break down → implement → review → deliver → capture |
| Bug | map? → diagnose → implement (fix) → review → deliver → capture |
| Investigation | map → diagnose → report/handoff (ends here — don't force implementation) |
| External spec (ticket/US) | clarify (consumer-simulation as support) → specify/refine → break down → continues as feature |
| Refactor | map → clarify scope → implement → review → deliver → capture |

`map?` = only if the codebase is unfamiliar. **A minimal route is legitimate**: on a small task, explicitly propose skipping stages ("trivial bug: I suggest implement→review→deliver") and let the user confirm.

## 3. Stages → skills

| Stage | Skill | Fallback without superpowers | Output |
|---|---|---|---|
| Map | `core:archaeology` | — | map with citations |
| Diagnose | `superpowers:systematic-debugging` (+ `council:schrodinger` if >1 live hypothesis) | `council:schrodinger` + the always-on debugging protocol | root cause with evidence |
| Clarify | `superpowers:brainstorming` or `core:grill-me` | `core:grill-me` | agreed decisions |
| Specify/refine | brainstorming (spec) or `core:spec-refine` | `core:spec-refine` | spec in `docs/superpowers/specs/` |
| Checkpoint | `core:grill-me` escalation mode `post-plan` | — | verdict |
| Break down | `superpowers:writing-plans` or `core:tech-breakdown` | `core:tech-breakdown` | plan in `docs/superpowers/plans/` |
| Implement | `superpowers:executing-plans` or subagent-driven | direct execution with the project's gate | code + commits |
| Review | `core:review-local` + `core:grill-me` escalation mode `pre-done` + `cold-reader` agent (deliverables for a cold audience) | — | resolved findings |
| Deliver | `core:commit` → open the PR (native/`gh` flow) | — | commit/PR |
| Capture | `core:learn` (memory) + manual handoff (compound demoted, later deleted) | — | memory + handoff |

Skills marked `core:*` slash-only (`archaeology`, `spec-refine`, `tech-breakdown`, `review-local`, `commit`): recommend the exact command (`/core:<name>`) for the user to trigger — the Skill tool doesn't invoke them.

Stage notes:
- Investigation's terminal ("report/handoff"): a manual handoff proportional to the work — there's no dedicated skill.
- `consumer-simulation` is an AGENT, not a skill: dispatch it as a subagent (Agent tool), passing ONLY the ticket text + acceptance criteria, never the implementation.
- **Audience of each deliverable (Specify/Break down).** Work that produces a deliverable names, in the spec/plan, *who receives each artifact and what they must do with it* — one line per artifact. That line is the input the `cold-reader` pass consumes at define-done; missing at planning time, the audience gap is surfacing early instead of in the recipient's hands.
- **Decision ledger append (any stage).** A materially resolved decision at any stage (a brainstorming approach choice, an `AskUserQuestion` answer, a `grill-me` interview outcome) appends an `L#` record when a ledger exists for the work — the ledger is emitted by `core:spec-refine` (format: its `references/ledger-format.md`).
- Review stage: deliverables whose audience didn't live the session get a blind cold-reader pass.
- Reviewing in a project with the mobile plugin installed: add `mobile:refactor-review` when the change is a refactor.
- **Type each stage's work.** Map/archaeology and read-heavy research legs are **LABOR** → propose a read-only Worker (the `using-agent-kit` dispatch signal; doctrine in `core:methodology` §Topology / §Choosing the executor). Planning, verifying, synthesizing, and deciding stay **ORCHESTRATION** on the main thread. The work-type, not the stage's name, decides the executor.
- **Propose the loop when the route fans out.** When classification (§2) yields a route with **3+ independent LABOR legs** (the same fan-out threshold `using-agent-kit` §Dispatch names — "Fan-out: 3+ independent tasks"), the conductor **proposes** invoking `core:orchestrate` for that segment — piggybacking on the route confirmation §2 already does, no separate ceremony. A minimal route (§2) with fewer than 3 independent LABOR legs proposes no loop.

## 4. "Challenge my plan" / high-stakes decisions — where to look

- Council (`council:council`) — entry point for a high reversal-cost decision, at ANY stage (stage-independent, so it's not a row in the per-stage table above).
- `core:grill-me` escalation has three checkpoints — `pre-plan`, `post-plan`, `pre-done`. At each transition a route actually includes, the pipeline **proposes** the consult (a minimal route that skips a transition proposes nothing); the operator confirms before it fires. Routing to the **Advisor tier** (personal binding) is structural and independent of the main model.
- Which of the four to reach for, by object: interview interrogates the operator, escalation checks the work, `core:spec-refine` the document, Council the reasoning.

Reviewer-escalation mechanics (which mode, which mechanism, when): see grill-me's REFERENCE.md — single source.

## 5. Conduction rules

- **One stage at a time.** When closing a stage, recommend the next 2-3 routes with a 1-line reason — and STOP. Never invoke the next stage without user confirmation.
- **Stage-order pull-gate (artifact transitions only).** Where a stage's predecessor produces a durable artifact — Specify (spec) before Break down, Break down (plan) before Implement — that artifact must exist to enter the next stage. Skipping such a transition is not silent drift: the Orchestrator **pauses and escalates the skip** ("I'm about to go to Plan with no spec — confirm?"). Stages whose output is not a disk artifact (clarify → decisions, diagnose → root cause) do **not** gate — no ceremony on routine routes. A minimal route stays legitimate (§2): skipping is fine *if the operator confirms*.
- **Analysis is a means, not a deliverable.** When an analysis/map/investigation stage closes (outside the Investigation class, whose terminal IS the report), the default recommended route is the concrete construction it enables — never another round of analysis. Recommending more analysis requires naming the decision it unblocks.
- **Coordination with superpowers.** If a superpowers flow is already active (brainstorming in progress, plan in execution), do NOT take over conduction: only do stage detection if useful, and defer to the active stage skill.
- **State = artifacts.** Progress lives in artifacts (specs/plans/handoffs) — don't create your own *ad-hoc* state marker. The one sanctioned exception is the per-work-unit **loop manifest** (`docs/superpowers/loops/`, convention `references/loop-manifest.md`), which is subordinate to the artifact/git detection in §1, not a competing source of truth.
- **Session discipline.** One heavy phase per session: *clarify/specify* · *implement* · *review/deliver* · *close*. When crossing a heavy-phase boundary, recommend a new session with a handoff; check `docs/superpowers/` artifacts manually at session start — specs/plans/handoffs are detected by this skill's section 1, not auto-reopened.
- **Closing always captures.** End of relevant work → `core:learn` (if corrections/decisions occurred) + a handoff proportional to the session's work.
