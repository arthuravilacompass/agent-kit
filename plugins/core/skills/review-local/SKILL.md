---
name: review-local
description: Invoke to dispatch specialized reviewers in parallel against the current branch's diff — last line of defense before pushing / opening the PR. Requires the `pr-review-toolkit` plugin; without it, use `core:review-remote` (sequential).
disable-model-invocation: true
---

# review-local — Local PR Review Chain Before Push

> **Which to use**: this skill requires the `pr-review-toolkit` plugin (parallel dispatch). Without the plugin, use `core:review-remote` (sequential, no parallelism). **Divergence**: `review-local` BLOCKS on lint/analyze failure; `review-remote` reports the failure as a finding and continues.

Dispatch specialized reviewers in parallel against the current branch diff. Last line of defense before pushing / opening the PR. Output is presented in conversation only — never auto-posted.

## Project config

This skill assumes the consumer project defines:
- **Base branch** (suggested default: `main`).
- **Lint command** and **test command** used in the precondition (Step 2).
- **The project's own rule codes** that the `code`/`type` agents should treat as 🔴 Important (see `agents.md` — the agent table is the configuration point).
- **Package directories**, if the repo is a monorepo with multiple projects using different lint/test commands.

## Usage

```
review-local
review-local --ticket <TICKET>
review-local --base <branch>
review-local --agents code,silent
review-local --ticket <TICKET> --base <branch> --agents code,consumer
```

Default base: config above (fallback: `main`). When `--ticket` is provided, the `consumer` agent is auto-included unless filtered out by `--agents`.

## Steps

1. **Resolve diff scope**

   - Parse `--base <branch>` if provided, else the project's default base branch (config; fallback `main`).
   - `git diff <base>...HEAD --stat` to summarize scope.
   - If empty: stop and report "No changes relative to `<base>`. Nothing to review."
   - Echo scope (base, total files, exclusions) and wait 5 seconds for user abort.

2. **Precondition — base verification (automatic)**

   Detect the project/package from the diff path (config — e.g. multiple packages in a monorepo) and run:

   - the project's lint/static-analysis command (config)
   - the project's test command (config, without coverage, for speed)

   If either fails, abort with:

   > "Base verification failed. Fix it before spending tokens on review."

   Attach the last lines of the error. Do not proceed.

3. **Dispatch agents in parallel**

   Read `agents.md` for the agent table (ID, `subagent_type`, framing, preconditions).

   **Resolve dispatch list:**

   - Parse `--agents <id1,id2,...>` (comma-separated).
   - **Without `--agents`:** dispatch every agent whose precondition is met (4 normally; 5 if `--ticket` is present — `consumer` is gated on `--ticket`).
   - **With `--agents`:**
     - Validate each ID against the config table. Unknown ID → abort: "Unknown agent: `<id>`. Valid IDs: `<list>`."
     - Filter the dispatch to the requested IDs.
     - If `consumer` was requested without `--ticket` → abort: "Agent `consumer` requires `--ticket <TICKET>`."

   **Dispatch:** all `Agent` calls in **a single message** (parallel). Each agent receives the diff (`git diff <base>...HEAD`) + the framing string from config. `consumer` receives ONLY the ticket text (resolved at runtime from the tracker tool available in the session — do not hardcode an MCP tool name) — never the diff. Every agent prompt MUST require: use the **Read/Grep** tool (never `cat`/`sed`/`grep` via Bash) for any file that will be cited as evidence — reading via Bash doesn't enter the read-ledger and breaks the citation at the gate.

4. **Wait for all agents to return.** Do not summarize partially.

5. **Aggregate findings**

   Before aggregating, **citation verification (a mechanism, not just manual re-reading — re-reading alone doesn't catch fabrication)**:

   - Assemble the findings as JSON `[{ "claim": "...", "evidence": { "file": "...", "lineStart": N, "lineEnd": M } }]` (the file:line each agent cited; single point → `lineStart`=`lineEnd`).
   - If the grill-me-internal citation validator is available (the same mechanism `core:grill-me` runs at `pre-done` — this skill reuses it, doesn't own it; a script that checks findings against the session's read-ledger), run it with an explicit `--session <current-session-id>`. The read-ledger logs reads via the Read/Grep tool from ALL subagents under the parent session_id (verified at runtime, 2026-07-07); reads via Bash do NOT enter it — hence the Dispatch mandate. **Pass `--session` explicitly** — do NOT rely on auto-discovery (there may be concurrent sessions).
   - `unverified` finding (file:line overlaps nothing read this session) = likely fabrication → "⚠️ Unverified" section, **not** presented as a confirmed finding. `verified`/`passthrough` proceed normally.
   - Complementary (doesn't replace the mechanism): re-read the lines and drop findings already fixed.

   Group by severity. If `consumer` was dispatched, add a "Ticket vs Implementation" section.

   ```
   ## Local Review — <N> findings

   ### 🔴 Important (<count>)
   - **[<agent-id>]** <finding> — <file>:<line> — rule <CODE>

   ### 🟡 Nit (<count>)
   - **[<agent-id>]** <finding> — <file>:<line>

   ### 🟣 Pre-existing (<count>)
   - **[<agent-id>]** <finding> — <file>:<line> (not touched in this diff)

   ### ⚠️ Unverified (<count>)
   - **[<agent-id>]** <finding> — <file>:<line> (citation doesn't overlap a ledger read — possible fabrication)

   ### Ticket vs Implementation (if consumer dispatched)
   - ✓ <behavior> (implemented)
   - ✗ <behavior> (not visible in the diff — gap?)
   ```

6. **Ask how to proceed**

   > "How should I proceed? Reply: fix-all / fix <severity> / fix <numbers> / ignore-preexisting / done"

## Important

- **Never post findings to any PR or external system.**
- **Output mirrors the user's language, default English. Rule codes stay in English.**
- **Do not fix 🟣 pre-existing in this PR.** Those are follow-ups.
- **Dispatch is parallel** (one message). Sequential doubles the runtime with no benefit.
- **The roster lives in `agents.md`** — edit there to add/remove/retune agents.
- **Agent that fails or times out:** present the ones that succeeded, note which failed. Don't retry without being asked.
