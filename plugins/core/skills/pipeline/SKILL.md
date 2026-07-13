---
name: pipeline
description: Invoke when receiving a raw intent for substantial work (feature, bug, investigation, refactor, ticket/US) with no flow already underway, or when the user asks "where do I start", "what's the flow for this", "guide me through this work". Do NOT invoke for a conceptual question or a point lookup ("how does X work?"), nor when a flow is already underway (brainstorming, plan in execution, review). Flow conductor — detects the task's real stage, classifies the intent, and routes through the kit's skills one stage at a time; recommends the next route, never executes the whole chain by itself.
---

# Pipeline — flow conductor

Kit routing layer: the user's message carries only the **intent**; this conductor decides **where it enters** and **what the next step is**; the stage skills execute. Doesn't replace any skill — it references them.

## 1. Detect the real stage (always first)

Before classifying, look at what already exists:

- Recent `docs/superpowers/{specs,plans,handoffs}` — a ready spec means don't reclarify; a ready plan means go to implementation; a recent handoff means resume from there.
- `git log`/`git status` — half-done code indicates implement/review stage.

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
| Deliver | `core:commit` → `core:pr` | — | commit/PR |
| Capture | Ship & remember → core:learn (memory capture); session handoff is manual since compound's demotion (2026-07-12) | — | memory + handoff |

Skills marked `core:*` slash-only (`archaeology`, `spec-refine`, `tech-breakdown`, `review-local`, `commit`, `pr`): recommend the exact command (`/core:<name>`) for the user to trigger — the Skill tool doesn't invoke them.

Stage notes:
- Investigation's terminal ("report/handoff"): a manual handoff proportional to the work — there's no dedicated skill.
- `consumer-simulation` is an AGENT, not a skill: dispatch it as a subagent (Agent tool), passing ONLY the ticket text + acceptance criteria, never the implementation.
- **Audience of each deliverable (Specify/Break down).** Work that produces a deliverable names, in the spec/plan, *who receives each artifact and what they must do with it* — one line per artifact. That line is the input the `cold-reader` pass consumes at define-done; missing at planning time, the audience gap is surfacing early instead of in the recipient's hands.
- **`cold-reader` at define-done (Review).** When a deliverable's audience didn't live the session (client, PO/QA, handoff colleague), dispatch the `cold-reader` AGENT (Agent tool) before marking it done — passing ONLY the rendered artifact + the audience role, never the plan/diff/rationale. It reports whether the recipient can use it and flags content aimed at another reader. **Blinding is the caller's job — `tools: Read` can't enforce it:** dispatch in a worktree off HEAD, which hides only *uncommitted* material, so if a prior critique of this artifact is already committed, isolate another way (a checkout without it, or hand the agent only the artifact's text). Verify the isolation each dispatch; it is not automatic. Complements `pre-done` (diff vs ACs); this checks the artifact vs its recipient.
- Reviewing in a project with the mobile plugin installed: add `mobile:refactor-review` when the change is a refactor.

## 4. "Challenge my plan" — which mechanism

| Mechanism | Stage | Input | Covers what the others don't |
|---|---|---|---|
| `core:grill-me` (interview) | clarify; before calling a plan done | open decisions in the thread | extracts what only the operator knows; resolves decisions one dependency at a time |
| `core:grill-me` (escalation `pre-plan`/`post-plan`/`pre-done`) | the track's deterministic checkpoints | conversation (advisor) or diff+ACs (blind subagent) | second opinion from a stronger reviewer; breaks the epistemic bubble; doesn't decide for the operator |
| `/core:spec-refine` | specify | written spec/ticket | stress-tests the artifact with a formal Gap Summary |
| Council (`council:council`) | high reversal-cost decision, at any stage | the decision + the conversation's lean | a reasoning mode (reframe, limits, propagation) — not an artifact review |

Apparent overlap resolves by object: the interview interrogates **the operator**; escalation interrogates **the work** with another reviewer; spec-refine interrogates **the document**; the Council interrogates **the reasoning**.

## 5. Conduction rules

- **One stage at a time.** When closing a stage, recommend the next 2-3 routes with a 1-line reason — and STOP. Never invoke the next stage without user confirmation.
- **Coordination with superpowers.** If a superpowers flow is already active (brainstorming in progress, plan in execution), do NOT take over conduction: only do stage detection if useful, and defer to the active stage skill.
- **State = artifacts.** Progress lives in artifacts (specs/plans/handoffs) — don't create your own state marker or file.
- **Session discipline.** One heavy phase per session: *clarify/specify* · *implement* · *review/deliver* · *close*. When crossing a heavy-phase boundary, recommend a new session with a handoff; `plan-autoload` reopens plans/handoffs — specs are detected by this skill's section 1.
- **Closing always captures.** End of relevant work → `core:learn` (if corrections/decisions occurred) + a handoff proportional to the session's work.
