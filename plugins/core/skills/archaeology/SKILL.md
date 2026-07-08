---
name: archaeology
description: Invoke to map the current state of the code before any technical planning on a US, ticket, or domain with history in the app — dispatches exploration agents in parallel, consolidated archaeological map with decisions ranked by severity.
disable-model-invocation: true
---

# archaeology — Pre-US Codebase Map

Archaeological map of the app's current state for a US or domain — before any technical planning. Delivers: TL;DR, ranked decisions needed, cross-dimension table by module, evidence per dimension, and improvement opportunities.

## Project config

This skill assumes the consumer project defines:
- **Ticket ID pattern** — regex used by the detection rule (e.g., `^ACME-\d+$`, `^PROJ-\d+$`). Without this config, treat any token that looks like an identifier from the project's tracker as **ticket** mode.
- **Modules directory** — where features live (e.g., `src/modules/`, `src/features/`). Used in step 1 to list candidate modules.
- **Shared SDK/package directory(ies)** — if the project separates API calls into its own package (e.g., a repositories SDK), provide the path for Dimension C.

**Position in the workflow:**
```
archaeology <US | ticket | domain>   ← you are here
        ↓
core:tech-breakdown                    ← receives the map as context (US/ticket mode)
        ↓
core:spec-refine
```

## When to Use

Run **before** `core:tech-breakdown` (if available in this kit) whenever the US touches functionality that:
- Has history in the app (not a fully new feature)
- Crosses multiple modules
- Is suspected of legacy code, duplication, or N parallel implementations

Also run **without a US** to map an entire domain as architectural reference (`archaeology search`, `archaeology checkout`). In this mode the output does not become a tech breakdown — it's reference for future decisions and opening debt tickets.

Typical examples: search, filters, checkout, profile, authentication.

Do not use on 100% new features with no related existing code.

## Input

The user provides one of:

- **US text**: paste the full description into the chat
- **Ticket ID**: `archaeology PROJ-608692` — fetched via the project's MCP/tracker
- **Free domain**: `archaeology search` — architectural exploration without a US

### Detection rule (deterministic)

| Input received | Mode |
|---|---|
| Matches the project's ticket ID pattern (config above) | **ticket** — fetch via the tracker tool available in the session |
| Single token, no whitespace/newline (`search`, `checkout`, `profile`) | **free domain** |
| Multi-line OR contains US markers (`As a `, `Acceptance criteria`, `Given that`, `User story`) | **US text** |
| Ambiguous (e.g., a short phrase like "search flow") | **ask** the user which mode |

If no input is provided: ask "Which US, ticket, or domain would you like to map?"

## Steps

### 1. Extract vocabulary + grep patterns

From the input, extract:
- **Primary terms**: feature names, flows, entities
- **Code terms**: controllers, stores, repos that likely exist
- **Candidate modules**: which modules in the project's modules directory (config) likely have related code
- **Grep patterns**: concrete regex/glob each agent will use

Present to the user before dispatching the agents — full format: `REFERENCE.md` §1.

Wait for confirmation before proceeding. Wrong terms contaminate all 4 agents.

### 2. Dispatch 4 Explore agents in parallel

Dispatch **4 Explore agents in parallel** (`subagent_type: "Explore"`), one per dimension — A: Entry Points, B: Controllers and Stores, C: Repositories and Endpoints, D: Duplication. Pass the terms, modules, and patterns confirmed in step 1.

Each agent delivers **raw evidence + cites `file:line`**, without classifying as "shared", "risk", or "opportunity" — that's the consolidator's job in step 3. Detailed instructions per dimension: `REFERENCE.md` §2.

### 3. Consolidation — prescriptive structure

With the 4 outputs in hand, synthesize the map in this fixed order (do not improvise sections): **TL;DR → Decisions Needed → Consolidated View by Module → Evidence by Dimension → Improvement Opportunities → Other Open Questions**.

Full structure template + consolidator's mandatory rules (fixed order, TL;DR written last, dedup in Opportunities, mandatory `file:line` citation, ranking capped at 5 items): `REFERENCE.md` §3.

### 4. Save the map

Save to `docs/superpowers/archaeology/`:

- Ticket / US text mode: `YYYY-MM-DD-<domain>.md` (e.g., `2026-05-26-unified-search.md`)
- Free domain mode: `YYYY-MM-DD-domain-<domain>.md` (e.g., `2026-05-26-domain-checkout.md`)

The `domain-` prefix makes explicit that this is architectural exploration, not pre-US.

### 5. Conditional handoff

Ticket/US text mode: recommend `core:tech-breakdown <ticket>` (if available) and ask whether to start now or the user prefers to review the map first. Free domain mode: there's no tech breakdown without a US — suggest using it as reference and opening follow-up tickets for High-severity Opportunities. Full messages: `REFERENCE.md` §5.

## Inviolable rules

- Never classify code as legacy without verifying an active caller (grep for instantiation via DI or direct instance in the page).
- Findings without evidence — every item in Opportunities cites `file:line`. Without a citation, it's inference — cut it.
- Improvised sections — if you're about to create a section not in the template (`Features to Remove`, `Current Analytics`, etc.), stop and fold the content into **Opportunities** with an appropriate label.
- **Free domain** mode does not trigger handoff to `core:tech-breakdown` — it's architectural reference, not pre-US.
- If the domain crosses more than 6 modules, ask the user whether they want reduced scope before dispatch.

Full list of fat signals to cut and additional notes: `REFERENCE.md` §6 and §7.
