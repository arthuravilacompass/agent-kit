---
name: refine-live
description: Live copilot for the refinement session with the PO — takes the board card + PO's real-time bullets and generates clarifying questions by priority (scope, implicit criteria, dependencies). Use during the refinement call; consolidates state for the follow-up /team:refine-async.
disable-model-invocation: true
---

# /refine-live -- Live Refinement Assistant

Copilot for use during the weekly refinement session with the PO. Takes the board card + the PO's verbal context in bullets, and generates clarifying questions in real time to maximize understanding of the US.

**Position in the workflow:**
```
/team:refine-live <card-id>                ← you are here (during the session)
        ↓
/team:refine-async <card-id>               ← post-session (triage + subtasks)
        ↓
archaeology → tech-breakdown → spec-refine → plan
```

(`archaeology`, `tech-breakdown`, `spec-refine` are skills from this kit's `core` plugin — invoke as `/core:archaeology`, `/core:tech-breakdown`, `/core:spec-refine`.)

## When to Use

Run **during the refinement session** when the PO presents a US. Use in parallel with the PO talking — you type bullets of what they say and the AI generates questions to ask on the spot.

Not for: deep technical exploration (use `/core:archaeology`), spec stress-testing (use `/core:spec-refine`), decomposition into subtasks (use `/team:refine-async`).

## Input

```
/team:refine-live <TICKET>
/team:refine-live <numeric-card-id>
```

Accepts:
- **Custom ID** (board ticket format, e.g. `<TICKET>`): resolved via the consumer project's board MCP search tool (e.g., `search_cards(custom_id: "<TICKET>")` — illustrative syntax; adapt to the real board MCP available in the session, this kit doesn't bundle one)
- **Numeric card ID**: validated via the same tool, or an equivalent detail tool

## Steps

### 1. Fetch card from the board

**Depends on a board/kanban MCP specific to the consumer project — this kit doesn't include one.** Fetch the card via that MCP's tool (e.g., `search_cards`/card detail — adapt to the real server connected in the session):
- If ticket format: use the search with `custom_id` to obtain the numeric `card_id`
- If numeric: validate existence on the board

Retrieve: title and description (via the detail tool if available; if the tool is disabled, use only the search result + title).

If card not found: inform the user and ask them to confirm the ID.

Present a brief summary:
```
📋 Card: <TICKET> — "<card title>"
Description: [first 3 lines or "no description"]

Ready. Paste PO bullets or ask something.
```

### 2. Initial question block

Based on the card's title + description, generate **3-5 questions** organized by priority:

| Priority | Category | Examples |
|---|---|---|
| 1 | **Scope/Context** | "Is this an extension of an existing feature or new?", "Does it affect only one platform?", "Which segment(s)/brand(s)?" |
| 2 | **Implicit criteria** | "Is there a defined empty/loading state?", "What happens on error?", "Does it work offline?" |
| 3 | **Dependencies/Blockers** | "Does it need a new backend endpoint?", "Does it depend on another US?", "Is there design/Figma ready?" |

Format for each question:
```
[Scope] — <short, direct question>
```

Don't exceed 5 questions in this block. The goal is to be fast and digestible during the call.

### 3. Incremental mode (main loop)

The user pastes bullets of what the PO is saying. For each input:

1. **Read the bullet** — understand the added context
2. **Opportunistic grep** (optional): if the bullet mentions a module/screen/feature that might exist in the code, do 1 quick grep (<2s). If it confirms existence, use it in the question ("PO, is this an extension of the `<FeatureX>Store` we already have, or is it a new flow?")
3. **Generate 1-2 additional questions** relevant to the bullet — keep the 3 priority categories

If the bullet is purely informative and raises no question, reply briefly: "✓ Got it. Next bullet or question?"

**Don't do in incremental mode:**
- Heavy code exploration (>2s)
- Technical edge-case questions (error paths, race conditions)
- Implementation or architecture suggestions
- Subtask generation

### 4. "close" — Consolidation

When the user types **"close"**, consolidate the session state:

1. Generate the structured summary below
2. Save to `docs/refine/refine-<card-id>.md` (make sure the directory exists: `mkdir -p docs/refine`; use the external_id if available, e.g.: `refine-<TICKET>.md`)
3. Confirm to the user: "State saved. You can run `/team:refine-async <TICKET>` whenever you want."

**State schema:**

```markdown
# Refine: <external_id>

## Card
- title: <card title>
- card_id: <numeric>
- external_id: <TICKET>
- board: <BOARD_NAME>

## PO Context
- <bullet 1>
- <bullet 2>
- ...

## Questions Asked
- Q: <question> → A: <PO's answer | "no answer">
- ...

## Open Gaps
- <unanswered questions or topics left open>

## Status
- phase: live_closed
- ready_for_pipeline: <yes | no (reason)>
- date: <YYYY-MM-DD>
```

The session stays active after "close" — the user can run another `/team:refine-live` with a different card ID.

## Important

- **Speed > completeness**: short, direct, 1-line questions. The PO is talking — you can't generate paragraphs.
- **No technical jargon in the questions**: the PO is business-side. Ask about expected behavior, not about stores/repositories.
- **No heavy codebase exploration**: opportunistic grep is ok (<2s). Anything beyond that, leave for the async step.
- **No subtasks**: subtask generation is `/team:refine-async`'s responsibility.
- **No spec-level questions**: error paths, race conditions, complex state transitions → `/core:spec-refine` does this better with full context.
- **One US per invocation**: don't mix context from different cards in the same call.
- **`<BOARD_NAME>`, `<TICKET>`, and module/store names in this file are placeholders** — adapt them to the real board and consumer project names when using this skill; this kit has no board of its own to fill these in with.
