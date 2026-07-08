---
name: refine-async
description: Post-refinement triage — consolidates the context saved by /team:refine-live, runs light codebase exploration (budgeted grep, no deep architecture) and generates [INTERIM] subtasks for approval and creation on the board. Use right after the refinement session, before the technical pipeline (archaeology → tech-breakdown).
disable-model-invocation: true
---

# /refine-async -- Post-Refinement Triage

Asynchronous processing after the refinement session. Consolidates the context captured in `/team:refine-live`, runs light codebase exploration, generates subtasks for approval, and creates them on the board.

**Position in the workflow:**
```
/team:refine-live <card-id>                ← during the session
        ↓
/team:refine-async <card-id>               ← you are here (post-session)
        ↓
archaeology → tech-breakdown → spec-refine → plan
```

## When to Use

Run **after the refinement session**, once `/team:refine-live` has already consolidated the US's context. Can be immediately after (same session) or at another time (reads from the state file).

Not for: deep architectural exploration (use `/core:archaeology`), detailed technical decomposition (use `/core:tech-breakdown`), spec stress-testing (use `/core:spec-refine`).

## Input

```
/team:refine-async <TICKET>
/team:refine-async <numeric-card-id>
```

Accepts the same card ID formats as `/team:refine-live`.

## Steps

### 1. Load state from the live session

Look for the state file at `docs/refine/refine-<card-id>.md`:
- Try first with the external_id: `refine-<TICKET>.md`
- If not found, try with the numeric one: `refine-<numeric-card-id>.md`
- If found: load it and present a summary ("Found the live session's context: [title], [N bullets], [N open gaps]")
- If **not found in either format**: ask the user whether they want to:
  - (a) Provide the context manually (paste a summary)
  - (b) Run without prior context (board card only)

If option (b): fetch the card via the consumer project's board MCP tool (this kit doesn't bundle one — adapt to the real server connected in the session) and use only the title + description as the basis.

### 2. Light grep — light codebase exploration

Based on the card's terms (title, PO context, modules mentioned), run a light exploration:

**Budget:**
- Maximum **10 grep queries**
- Total time < **30 seconds**
- Focus on **confirming existence** (not mapping architecture)
- If the budget is hit before completing: stop and report what was found so far

**What to search for** (Claude Code tools — `Glob`/`Grep`):
| Target | Example |
|---|---|
| Does the module/feature exist? | `Glob("**/*<feature>*")` |
| Does the Store/Controller exist? | `Grep("<Feature>Store\|<Feature>Controller")` |
| Does the Endpoint/Repository exist? | `Grep("<feature>Repository\|<feature>DataSource")` |
| Does the route exist? | `Grep("<RoutesTable>.*<feature>")` |

**Grep output** — concise summary:
```
🔍 Light exploration:
- ✅ Module `<feature_module>` exists at lib/src/modules/<feature_module>/
- ✅ <FeatureX>Store found (<feature>_store.dart)
- ❌ Recommendation endpoint NOT found in the data repository
- ⚠️ Existing route: <RoutesTable>.<feature> (restricted scope)
```

### 3. Generate [INTERIM] subtasks

Based on the consolidated context (live + grep), generate subtasks for the US:

**Generation rules:**
- Each subtask is an independent or sequential unit of work
- Title: imperative verb + clear scope (e.g.: "Create endpoint X on the backend")
- Description: 2-3 lines on what needs to be done
- Tag: `[INTERIM]` — subtasks are a starting point, not final truth
- No detailed acceptance criteria (that's for `/core:tech-breakdown`)
- No time estimate

**Presentation format:**

```
## Proposed subtasks — <TICKET> [INTERIM]

1. **Create recommendation endpoint on the backend**
   Endpoint that returns items related to the current context.
   Dependency: eligibility rule definition with the PO.

2. **Implement <Feature>Repository + DataSource**
   Integration with the new endpoint. Use the project's error pattern (e.g., Either<Failure, T>).

3. **Create the feature's UI on the target screen**
   Design system component with a list/section of recommended items.
   Ref: existing `<feature_module>` module (if any) can be reused.

4. **[QA] Feature integration tests**
   Validate the full end-to-end flow.

---
Approve? Options:
- `approve all` — I create all of them on the board
- `approve N` — select which ones (e.g.: "approve 1,2,3")
- `edit N` — request a change to a specific subtask
- `redo` — regenerate with new instructions
```

### 4. Approval + Creation on the board

**Depends on a board/kanban MCP specific to the consumer project — this kit doesn't include one.** After the user's approval:

1. **Try to create via the board MCP's tool**: subtask batch creation with the approved subtasks, adapted to the real server connected in the session
2. **If no board MCP is connected, or the call fails** (unavailable, error, permission): export as formatted text:

```
⚠️ Board API unavailable. Subtasks ready for manual creation:

□ Create recommendation endpoint on the backend
□ Implement <Feature>Repository + DataSource
□ Create the feature's UI on the target screen
□ [QA] Feature integration tests
```

3. **No retry**: report the failure, no automatic retry.

### 5. Pipeline signal

After subtasks are created (or exported), ask:

```
## Next step

Is this US ready to enter the technical pipeline?

- `ready` — can run `/core:archaeology` → `/core:tech-breakdown` once a dev picks it up
- `blocked` — still has gaps that need the PO (list which)
- `partial` — part is ready, part needs clarification

What's the status?
```

Record the answer in the state file.

### 6. Update state

Update the state file at `docs/refine/refine-<card-id>.md` (make sure the directory exists: `mkdir -p docs/refine`):

```markdown
## Async (added)
- async_date: <YYYY-MM-DD>
- grep_findings: [1-line summary per finding]
- subtasks_created: [list of titles]
- subtasks_rejected: [list, if any]
- pipeline_status: ready | blocked (reason) | partial (reason)

## Status
- phase: async_done
- ready_for_pipeline: <updated>
```

## Important

- **Triage, not architecture**: the goal is to organize the US into workable pieces, not to design the solution. That's `/core:tech-breakdown`'s job.
- **Subtasks are [INTERIM]**: they'll be refined when the dev runs the full pipeline. Don't treat them as final truth.
- **Approval gate is mandatory**: NEVER create subtasks on the board without the user's explicit approval.
- **Light grep, not archaeology**: max 10 queries, max 30s. If more is needed, flag it: "I recommend running `/core:archaeology` for full mapping."
- **Graceful fallback**: without a board MCP, or if the call fails, export text. Don't block the workflow.
- **No detailed spec**: don't generate acceptance criteria, test plans, or design docs. Those are outputs of `/core:tech-breakdown` + `/core:spec-refine`.
- **Idempotency**: if run twice on the same card, detect existing subtasks and ask: "Subtasks already exist on the card. Add new ones or replace?"
- **`<TICKET>`, module/store/repository names, and the board in this file are placeholders** — adapt them to the consumer project's real names when using this skill; this kit has no stack of its own to fill these in with.
