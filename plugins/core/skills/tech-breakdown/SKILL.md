---
name: tech-breakdown
description: Invoke to turn a ticket into a developer-ready implementation plan — fetches the ticket, runs brainstorming + adversarial refinement + writing-plans, and has the critic phase grill the plan against the real codebase. Typical Tech Lead use.
disable-model-invocation: true
---

# tech-breakdown — Technical Breakdown for TL

Fetch a ticket, perform technical analysis, and produce a ready-to-develop implementation plan using superpowers brainstorming + writing-plans pipeline.

**Intended user:** Tech Lead (TL)

## Project config

This skill assumes the consumer project defines:
- **Ticket tracker** — where the ticket text comes from (Jira, Linear, an internal Kanban board, or text pasted manually). The mechanism below uses Jira as a concrete example, but depends only on the **ticket's content**, never on a specific integration.
- **Ticket ID pattern/prefix** — used only to name the saved plan file (e.g., `PROJ-123`, `ACME-456`). Without this config, use the ID as the user provided it.
- **Stack convention used in the critic phase** — logging library names, error pattern, serialization, etc. that the critic should validate against the real codebase (see Step 7).

## Prerequisites

- A ticket-tracker tool configured in the session (e.g., MCP Atlassian) — or the user pastes the ticket text directly.
- superpowers marketplace skills must be installed

## Steps

1. **Receive ticket ID**

   The user provides the ticket ID as an argument: `tech-breakdown <TICKET>`

   If no argument is provided, ask: "Which ticket would you like to break down?"

2. **Fetch ticket from the tracker**

   Do not hardcode an MCP tool name. Resolve the *get-issue* tool available in the session at runtime (e.g. via tool search) and fetch the ticket by issue key — MCP server aliases change over time and a hardcoded name silently breaks the fetch. If no tracker tool is available, ask the user to paste the ticket text.

   Extract:
   - Summary (ticket title)
   - Description (requirements, acceptance criteria)
   - Issue type (Story, Bug, Task, Sub-task)
   - Priority
   - Labels and components
   - Linked issues (if any)
   - Comments that clarify requirements (if any)

3. **Summarize ticket context**

   Present to the user a structured summary:

   ```
   Ticket: <TICKET> — [Summary]
   Type: [Story/Bug/Task]
   Priority: [High/Medium/Low]

   Requirements:
   [Key requirements extracted from description]

   Acceptance Criteria:
   [List of ACs if present]

   Dependencies:
   [Linked tickets or systems]
   ```

   Ask: "Does this summary capture everything relevant? Any additional context I should know before the technical analysis?"

   Wait for confirmation or additions.

4. **Run superpowers brainstorming**

   Invoke the superpowers:brainstorming skill with the ticket context as input.

   The brainstorming session will:
   - Explore the codebase relevant to the ticket
   - Propose 2-3 implementation approaches with trade-offs
   - Get the TL's approval on the chosen approach
   - Produce a validated design/spec

5. **Adversarial spec refinement**

   Before writing the plan, run `core:spec-refine` (if available in this kit) against the spec produced in step 4.

   This stress-tests the spec for missing error paths, ambiguous states, and unwritten invariants. The session produces a Gap Summary that is incorporated into the spec before planning begins.

   Skip only if the TL explicitly says "skip refinement" or the ticket is a trivial 1-file change.

6. **Generate implementation plan**

   After brainstorming produces the spec (and refinement closes the gaps), invoke the superpowers:writing-plans skill.

   The plan will be saved to:
   ```
   docs/superpowers/plans/YYYY-MM-DD-<ticket-id>-<short-title>.md
   ```

7. **Critic phase — grill the plan against the actual codebase**

   Before declaring the plan ready, dispatch a critic subagent (Explore-style) with the produced plan and the ticket context. The critic answers concretely:

   - For each lib/utility named in the plan, does it already exist in the codebase? Grep and cite the file.
   - For each new file/class/store proposed, is there a close analogue already (avoid parallel implementations)?
   - For each "we'll use library X" assumption, does the project actually use X? (Confirm the project's real convention for logging, error handling, serialization, etc. — see **Project config** — instead of assuming a default.)
   - For each analytical claim (file count, token count, lines of code), was a real measurement tool used, or only shell approximation?

   The critic returns PASS (proceed) or FAIL (concrete gaps → loop back to step 4 brainstorming with gaps as input; cap at 2 critic rounds; if still failing, escalate to the TL).

8. **Link plan back to the tracker**

   After saving the plan, resolve the *add-comment* tool available in the session at runtime (do not hardcode an MCP tool name — see Step 2) and add a comment to the ticket with the plan path: `"Implementation plan created: docs/superpowers/plans/YYYY-MM-DD-<ticket-id>-<title>.md"`.

9. **Hand off to the developer with a verifier**

   Present to the TL:
   - Path to the saved plan
   - Summary of the chosen approach
   - Suggested sub-tasks (if the scope warrants a split)
   - **Verifier** (signals below) — embed in each phase's "done" criteria

   Plan ready for the developer to execute via `superpowers:executing-plans`.

   **Verifier — signals before declaring a phase complete** (heuristic, not a rigid checklist):

   Before any "F1 / F2 / Phase N complete" claim, confirm whatever makes sense for the phase:
   - Expected files actually touched (`git status` / `git diff --stat`).
   - Acceptance criteria observably met (not inferred from "the code compiled").
   - Tests / analyzer ran with captured output.
   - Prior phases actually finished before moving on.

   If any signal fails, the phase stays `in_progress`. Do not report "phase complete" upstream without going back and closing the gap.

   Why it exists: past sessions have claimed a phase complete when brainstorming/writing-plans/critic hadn't actually run — the verifier exists so the gap between "I thought I was done" and "I was actually done" doesn't repeat.

## When the ticket is incomplete

Before generating the tech breakdown, validate that the ticket has:

- **Acceptance Criteria** (observable behavior that validates done)
- **Suggested entrypoints** (files/modules expected to be touched)
- **Test Plan** (list of tests to implement — unit/widget/integration)

If 1+ is missing, **ask the user 3 short questions** before generating the breakdown:

1. "Which files do we expect to touch?"
2. "What behavior validates that it's done?"
3. "Any project-specific constraint (see Project config / design system / state-management tier, etc.)?"

Use the answers to fill in the tech breakdown. If the ticket already has these sections, treat them as a contract and use them directly.

Do NOT create a required template. This is a heuristic — the user can say "skip, let's go with what we have".

## Fat signals to cut

Before finalizing the artifact, re-read it looking for:

- **Background duplicating the ticket** — if it's on the card, no need to repeat it here.
- **"Alternatives Considered" with no decision** — if you didn't choose, don't encode it.
- **Code examples that will be in the diff** — reference the diff, don't duplicate it.
- **File lists with no "why"** — an entrypoint with no reason to touch it is noise.
- **Redundant "Background" + "Motivation" + "Context" sections** — pick one.

If 2+ signals appear, there's probably ~30% cuttable fat. Whether to cut or justify keeping it is your call.

## Important

- The TL drives the brainstorming session. Claude supports, proposes, and documents.
- Never skip the ticket fetch step — the plan must trace back to real requirements.
- If the ticket lacks sufficient detail (no acceptance criteria, vague description), flag this to the TL before starting technical analysis.
