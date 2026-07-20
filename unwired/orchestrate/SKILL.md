---
name: orchestrate
description: Invoke when a task is too large for one pass or needs parallel work across many independent subtasks — "fan this out", "too big for one model", "orchestrate across a team", parallel research/generation over N items, a multi-leg audit. Runs the full plan→delegate→verify→synthesize loop with cheap parallel workers and a stronger advisor consulted at the commitment boundaries. NOT for single-file edits or anything one pass handles; NOT a replacement for core:pipeline's stage routing (the pipeline proposes THIS when it detects fan-out-shaped work).
metadata: {author: "Shubham Saboo", source: "https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/agent_skills/advisor-orchestrator-worker", license: "Apache-2.0"}
---

# orchestrate — plan→delegate→verify→synthesize loop

> Adapted from [advisor-orchestrator-worker](https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/agent_skills/advisor-orchestrator-worker) (Shubham Saboo, awesome-llm-apps) — Apache-2.0.
>
> **Archived 2026-07-20 (core 0.16.0). Unwired — nothing loads this.** Its `core:methodology §Dispatch/§Topology/§Choosing the executor/§Fan-in/§Tool scoping/§Model routing` cross-references predate the trio collapse: the dispatch doctrine and worker output contract now live in `core:pipeline §6`, and fan-out mechanics defer to `superpowers:dispatching-parallel-agents` / native parallel subagents. Resurrecting this loop requires re-pointing those references first.

This skill sequences the kit's existing dispatch doctrine (`core:methodology` §Dispatch) into a runnable loop. It adds only what that doctrine doesn't already cover: a spend budget, a degraded mode, a status board, and a worker-brief template. It does not restate Topology, the Dispatch contract, the Fan-in contract, Tool scoping, or Model routing — those live in `methodology` and are referenced by name below.

Two departures from the reference this is adapted from, both deliberate:

- **Advisor gates are propose-and-confirm, never auto-fire.** The reference's advisor consults are mandatory and unconditional; this kit's are structural (the timing and the routing are fixed) but the firing is the operator's confirmation, same as any other `grill-me` checkpoint (`core:pipeline` §4).
- **Workers are the Agent tool, Worker tier — never a CLI or bash process.** Default `model: sonnet` per the current personal binding, overridable (concrete model is never baked here — `methodology` §Topology). There is no `agy`/API-key fallback path here; a "worker with no path" in this kit means Degraded mode (below), not a shell fallback.

## The loop

1. **Frame.** State the deliverable and 3–5 checkable success criteria. If the task is too vague for that, ask one question and stop. State the **budget** (below) alongside the criteria — sized to the plan, not an afterthought.

2. **Plan.** Decompose into self-contained subtasks, each typed **LABOR** (`methodology` §Choosing the executor, "Type the work first") — inline inputs, acceptance criteria, and wave assignments that maximize parallelism. Only 3+ independent LABOR legs justify a fan-out (the same threshold `using-agent-kit` §Dispatch names — "Fan-out: 3+ independent tasks"); with fewer, say so and drop to a direct pass instead of running this loop's machinery on work that doesn't need it — the same "don't delegate on a trivial task" judgment `using-agent-kit` §Dispatch already applies to any dispatch decision. Before proposing the plan-review consult (step 3), write the plan to a file — e.g. `docs/superpowers/plans/<date>-<slug>-loop.md`, or the plan path already in use for this work — never left in-context only.

3. **Plan review — advisor consult (propose-and-confirm).** Propose the plan-review checkpoint — `post-plan` once a plan exists to hand over, `pre-plan` if the approach itself is still open (`core:grill-me` REFERENCE.md, "Two mechanisms, by design" + mode table). Wait for the operator's confirmation before it fires. On confirm, point the advisor at the plan file written in step 2 rather than re-pasting it — same discipline `post-plan`'s own context-loading step already follows: it resolves the most recent `docs/superpowers/plans/*.md` on disk, so this loop's plan must already be there or the consult targets an unrelated, older plan. State what changed and what you rejected.

4. **Delegate.** Dispatch each wave via the **Agent tool** — `subagent_type: general-purpose` (or a fitting custom agent), Worker tier (default `model: sonnet` per the current personal binding, overridable — see `methodology` §Topology) — one self-sufficient brief per worker (`references/worker-brief.md`), per `methodology` §Dispatch contract. Parallel within a wave, then collect before verifying.
   - **Read-only by default.** A subtask typed LABOR produces a *finding*, not an edit — scope tools to `Read`/`Grep`/`Glob` unless the subtask genuinely needs to write (`methodology` §Tool scoping).
   - **Write-capable fan-out is explicit opt-in, guarded.** Several write-capable workers in the background hit the exact failure mode `methodology` §Tool scoping already names for a single background edit — so when a wave needs writes, run it in the foreground or worktree-isolate each worker on disjoint files (`superpowers:using-git-worktrees`); never fire-and-forget a background writer. State in the wave's dispatch which mode (foreground / worktree-isolated) it uses.
   - **Context-isolation caveat.** A kit Agent-tool worker already starts with everything `methodology` §Dispatch contract lists — including the CLAUDE.md/memory hierarchy — unlike the reference's stateless CLI workers; it is not a blank slate. Write the brief as if it were anyway (self-sufficient, no unstated context); at Synthesize, flag any result that looks primed by inherited context rather than by the brief's own inputs.

5. **Verify.** Check each result against its own acceptance criteria, exercising the real deliverable — never a proxy (`methodology` §"A verification gate must not derive from the artifact under test itself" + §"Evidence is re-read in its current state and generated, not transcribed"). Verdict per result: **PASS** / **FIX** (redispatch, naming the specific failure) / **ESCALATE**. Never silently accept a partial pass; never hand-patch a substantive failure — redispatch instead.

6. **Synthesize.** When all subtasks pass, assemble the deliverable. Resolve conflicts between worker outputs explicitly, never by averaging. Account for every dispatched front, including any flagged by step 4's context-isolation caveat (`methodology` §Fan-in contract).

7. **Taste pass — advisor consult (propose-and-confirm).** Propose the `pre-done` checkpoint — `grill-me`'s blind-adversarial form (`core:grill-me` REFERENCE.md, same mode table). On the operator's confirmation, send the draft; the blind form withholds your narrative by design, so hand over only the deliverable and its acceptance criteria, nothing more. Apply or explicitly rebut each note — never drop one silently.

## Commitment boundaries — mid-loop advisor escalation

Escalate to the advisor mid-loop — same propose-and-confirm gate as steps 3 and 7 — when:

- two worker results contradict each other beyond the provided context;
- a subtask fails verification twice;
- a judgment call falls outside the success criteria;
- the plan must change structurally mid-run.

This is the `escalate` edge (`methodology` §Topology) firing inside the loop rather than only at its two scheduled checkpoints — the trigger is a mid-run event, not a stage transition, but firing is still the operator's call, never automatic.

## Budget

Set at Frame, sized to the plan: a reasonable shape is **2 × subtask count** worker dispatches (retries and redispatches count) plus **up to 5 advisor consults** — 2 scheduled (proposed at steps 3 and 7: the plan-review and the taste pass — proposed, not auto-fired; the operator still confirms each before it runs), the rest covering commitment-boundary escalations. The cap is not the point: **spending past it is never silent** — on exhaustion, stop and report, or tell the operator what more would cost and let them decide. This is the escalate edge, applied to spend.

## Degraded mode

If a role has no working path, fall back in order — an independent dispatch path first, self-play only as the last resort:

1. **Independent path first.** An unavailable Advisor falls back to a full-context subagent dispatch for `pre-plan`/`post-plan` (`grill-me` REFERENCE.md's own fallback already covers this — the advisor prerequisite section). An unavailable Worker falls back to an equivalent dispatch via a different route (another subagent type, a different tool scoping). Use the fallback; it still keeps the role off the orchestrator.
2. **Self-play — last resort, labeled.** Only when no dispatch path exists at all does the orchestrator temporarily play that role itself, under the same propose-and-confirm discipline as any other checkpoint: same budgets, every affected section and the final result labeled `[DEGRADED: <role>]`. Note the context-isolation caveat (step 4) wherever it applies inside a degraded section. This is the one exception to "the orchestrator does no labor" (`methodology` §Topology).

Never skip the checkpoint — degrade it, labeled.

## Status board

After each loop step, print a one-line-per-subtask board: state (PENDING / DISPATCHED / PASS / FIX / ESCALATED), dispatch path, retries.

Example: `W2: FIX → PASS | sonnet | 1 retry`

**Persist at stage-close, schema-only.** The board above stays in-chat — it is not part of the manifest. At each stage-close (`pipeline`'s `references/loop-manifest.md` convention), write only that convention's fixed 5 fields to `docs/superpowers/loops/<slug>.md`: `stage` (echo), `roles` (active this loop — e.g. orchestrator, worker×N), `delegated` (what's out to a worker, or —), `pending` (what blocks advancing, or —), `mode` (route class). Do not add a board field or a ledger field — the schema is fixed by convention, not extended per-skill. Consequence, stated plainly: a mid-run compaction, `/clear`, or interruption recovers the coarse manifest state — which stage, which roles, what's pending — enough to reconstruct where the loop was; it does **not** recover the fine-grained per-subtask board or the verification ledger, which live only in-chat and are lost with the context. This state is subordinate to `pipeline` §1 live detection, exactly like any other loop manifest — it echoes progress, it never becomes the authority on stage.

## Finish

Stop at a verified deliverable, an exhausted budget, or a blocker that needs the operator. Return:

- the deliverable;
- the plan;
- a per-subtask verification ledger;
- advisor notes applied and rejected;
- remaining risks.

A long deliverable goes to a file, with a 3-line summary in the chat (`methodology` §Dispatch contract) — the rule that governs subagent output applies to the orchestrator's own just as much.
