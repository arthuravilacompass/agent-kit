# archaeology — Reference

Supporting content extracted from `SKILL.md`. Consulted during step execution — not read before deciding whether to invoke the skill.

## §1 — Vocabulary presentation format (Step 1)

Present to the user before dispatching the agents:

```
Detected mode: <ticket | free domain | US text>
Domain: <Unified Search>

Primary terms: search, query, unified
Code terms: SearchController, SearchResultListController, SearchRepository
Candidate modules: home, catalog, filter, results

Grep patterns (used by the 4 agents):
- Entry:        SearchField|onSearchChanged|Route\..*search
- Controllers:  glob *search*_controller.*, *search*_store.*
- Repos:        SearchRepository|SearchDataSource, plus /api/.*search in the shared SDK/package
- Duplication:  RecentSearches|debounce.*search, shared pagination

Edit terms / modules / patterns? (enter = confirm)
```

Wait for confirmation before proceeding. Wrong terms contaminate all 4 agents.

## §2 — Detailed per-dimension instructions (Step 2)

Dispatch **4 Explore agents in parallel** (`subagent_type: "Explore"`), one per dimension. Pass the terms, modules, and patterns confirmed in step 1.

**Each agent delivers raw evidence + cites `file:line`.** It doesn't classify as "shared", "risk", or "opportunity" — that's the consolidator's job in step 3.

---

**Dimension A — Entry Points**

Where can the user trigger this functionality?

- Grep for the entry patterns confirmed in step 1
- For each entry point: module, widget/file:line, destination route, who instantiates it
- Classify only whether the entry leads to the `active` flow or the `legacy` flow (presence in `showcase/`, `old/`, `deprecated/`)
- **Do not** opine on "the US's new flow" — only current state

---

**Dimension B — Controllers and Stores**

What state manages this functionality?

- Grep for the confirmed controller/store globs
- For each one: name, module, repository/method called, active page that instantiates it (via DI or direct instance)
- Status: `active` (has a confirmed caller), `legacy` (no caller after grep), `duplicate` (same purpose as another — cite the duplicate)

---

**Dimension C — Repositories and Endpoints**

What API calls exist?

- Grep the modules directory and the shared SDK/package directory (config) for the confirmed terms
- For each repository: exposed method, inferred endpoint, response type, who consumes it
- Location: shared package or app-local
- **Cite file:line** for each method

---

**Dimension D — Duplication**

What's repeated?

- Grep for the confirmed duplication patterns (debounce, pagination, local cache, etc.)
- For each finding: files that duplicate it, description of the divergence (if any), `file:line` citation
- **Do not** opine on "removal candidate" — just list what's duplicated

---

## §3 — Consolidation template (Step 3)

With the 4 outputs in hand, synthesize the map **in this order and structure** (do not improvise sections):

```markdown
# Archaeological Map — <Domain> — <YYYY-MM-DD>

(If ticket mode: line **Ticket:** PROJ-XXX — <title>)
(If US text or ticket mode: line **Context:** <1 line summarizing the US>)

## TL;DR
<3-4 lines. What exists (how many controllers, how many modules), what's
duplicated (with 1 example), what's the most blocking strategic decision.
No tables. No lists. Punchline.>

## Decisions Needed for the Tech Breakdown
<Ranked by severity. Maximum 5 items. Each item: severity label,
1 sentence describing the decision, evidence citing file:line,
why it blocks the tech breakdown.>

1. **[High]** <decision>. Evidence: `file.ext:L23`. Blocks because: <1 line>.
2. **[High]** ...
3. **[Medium]** ...

(Other questions, even important ones, go into "Other Open Questions"
at the end — unranked.)

## Consolidated View by Module

| Module | Entry points | Active controllers | Endpoints | Status |
|---|---|---|---|---|
| catalog/new | SearchPage | SearchController, SearchResultListController | /api/search, /api/suggestions | active |
| catalog/legacy | LegacySearchPage | LegacySearchController | /api/legacy-search | legacy |
| ... | | | | |

Status: `active` / `legacy` / `partially migrated` / `delegates`.
Cross-referencing the 4 agents' A-D outputs.

## Evidence by Dimension

### Entry Points
<Agent A's table, unmodified. This section is the raw source — citations
here may repeat what appears in Opportunities.>

### Controllers and Stores
<Agent B's table, unmodified.>

### Repositories and Endpoints
<Agent C's table, unmodified.>

### Duplications
<Agent D's list, unmodified.>

## Improvement Opportunities

<Each item with severity anchored to the rubric below + evidence citing
file:line. Each file appears ONCE in this section (dedup rule).
The frame is "what could improve", not "what to remove".>

**Severity rubric:**
- **High**: blocks the tech breakdown, requires a strategic decision, or has
  a cross-module contract divergence
- **Medium**: affects scope but has a clear workaround
- **Low**: known debt / cleanup / dead code

| Opportunity | Severity | Evidence | Why it matters |
|---|---|---|---|
| Divergent endpoint between listing and search | High | `search_repository.ext:L82` + `catalog_repository.ext:L15` | filters and pagination may diverge |
| ... | | | |

**Optional subsections** (include only if applicable and if it avoids repeating the table above):

- **Reusable**: what's shared and can go into the new US/feature without change
- **Coupled to the module**: what would need a refactor to be reusable
- **Confirmed legacy**: no active caller after grep
- **Integrations to preserve**: analytics, tracking, instrumentation

(In US/ticket mode, "Removal by the US" is a valid label inside Opportunities
— the umbrella frame remains Opportunities, but items may be
marked `[removal by the US]`.)

## Other Open Questions

<List, unranked. Questions that do NOT block the tech breakdown but that
the PO/design needs to answer at some point.>
```

### Consolidator's mandatory rules

1. **Fixed order.** TL;DR → Decisions → Cross-dim → Evidence → Opportunities → Other questions. Don't improvise sections (`Features to Remove`, `Current Analytics`, etc.). If a finding doesn't fit the prescribed sections, it goes into **Opportunities** with an appropriate label.
2. **TL;DR is written last.** Only after having the other 5 sections in hand.
3. **Dedup**: each `file.ext` or symbol appears **once** in Opportunities. Evidence-by-Dimension tables are the exception (raw source, repetition expected).
4. **Mandatory citation in Opportunities**: every item requires a `file:line` that came from one of the 4 agents. Without a citation, the item doesn't go in. If the consolidator can't cite it, the finding is inference — cut it.
5. **Limited ranking**: "Decisions Needed" has at most 5 items. Everything else goes into "Other Open Questions" unranked.

## §5 — Handoff messages (Step 5)

**Ticket / US text mode:**

> "Map saved to `docs/superpowers/archaeology/...`
>
> Recommended next step: `core:tech-breakdown <ticket>` (if available) — the map serves as additional context.
>
> Should I start now, or would you rather review the map first?"

**Free domain mode:**

> "Map saved to `docs/superpowers/archaeology/...`
>
> There's no tech breakdown without a US. Use this as architectural reference. Consider opening follow-up tickets for the High-severity Opportunities — they represent strategic decisions that haven't been made yet."

## §6 — Fat signals to cut

Before presenting the map, sweep for these signals:

- **Findings without evidence** — every item in Opportunities cites `file:line`. Without a citation, it's inference — cut it.
- **"Maybe legacy" status** — classify as active or legacy; ambiguity is noise.
- **Invented endpoints** — if the grep in the shared SDK/package didn't confirm it, mark it "to confirm".
- **Modules listed with no finding** — omit modules where the grep found nothing relevant to the cross-dim table.
- **Generic risk** — "may have breaking changes" without pointing at what specifically doesn't help; cut it.
- **Risk without grep** — Opportunities inferred from the US text without confirming in the codebase is exactly the problem that motivated the prescriptive structure. Every Opportunity requires a real `file:line`.
- **Improvised sections** — if you're about to create a section not in the template (`Features to Remove`, `Current Analytics`, etc.), stop and fold the content into **Opportunities** with an appropriate label.
- **Cross-section duplication** — the same finding in Opportunities + Cross-dim + Other Questions is overlap. Keep it in Opportunities; omit it from the others.

## §7 — Important

- Never classify code as legacy without verifying an active caller (grep for instantiation via DI or direct instance in the page).
- The cross-dim table by module is the most critical artifact after the TL;DR — prioritize completeness there.
- The map **is not a technical plan** — it describes current state and raises decisions, it doesn't propose solutions.
- If the domain crosses more than 6 modules, ask the user whether they want reduced scope before dispatch.
- Always confirm the extracted vocabulary and grep patterns (step 1) before executing.
- **Free domain** mode does not trigger handoff to `core:tech-breakdown` — it's architectural reference, not pre-US.
- The 4 agents deliver raw evidence. **Opportunities is 100% consolidator synthesis** — which is why the mandatory-citation rule is what separates honest synthesis from inference without grep.
