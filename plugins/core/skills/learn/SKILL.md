---
name: learn
description: Invoke when the user says "save this", "capture this learning", "use skill learn", or before a /clear or compact when the session has accumulated uncaptured corrections and decisions — scans the conversation and proposes memory entries for approval.
---

Scan the current conversation (or the last N messages if specified) for corrections, established preferences, domain facts, and decisions. Propose structured entries for typed memory with inline approval. Write only what's approved.

## When to use

- User explicitly asks: "use skill learn", "save this learning", "capture this".
- Long session where corrections accumulated without inline capture.
- Before `/clear` or compact if non-trivial changes were discussed.

## Memory system paths

- **Memory dir:** the current project's memory directory (given in the session's system prompt).
- **Index:** `MEMORY.md` (always loaded; ~8192-byte ceiling — matches `scripts/check-ceiling.sh`, not a line count)
- **File name:** `{type}_{snake_case_name}.md`
- **Types:** `feedback` | `reference` | `project` | `user`

## Steps

### 1. Scan conversation for signals (pt-BR + EN)

pt-BR is the primary language of the workflows this skill runs in, so detection must catch corrections in either language — the two literal-phrase rows below keep the pt-BR examples verbatim (pattern-matching targets, not prose to translate).

| Signal | pt-BR example | EN example |
|---|---|---|
| **Explicit corrections** | não, na verdade, corrige | no, actually, wrong |
| **Preferences** | sempre use X, prefiro | always use X, I prefer |
| **Domain knowledge / decisions** | architecture choices, business rules, process decisions explained during the conversation | (same — language-mixed content) |
| **Confirmed behaviors** | isso, perfeito, exato — after a non-obvious approach | yes exactly, perfect |

**Materiality bar:** a signal only becomes a proposal if it would still be true and still change behavior in a month. Most "isso, perfeito" is plain agreement, not a lesson — the qualifier ("after a non-obvious approach") is the filter; apply it strictly. When in doubt, skip.

Default scope: entire conversation up to the most recent `/clear`. If the user asked for "last N messages", limit to that.

If no signal is found: report *"No learning detected this session."* and stop.

### 2. Categorize each finding

| Finding | Memory type |
|---|---|
| Behavior correction, style/workflow preference | `feedback` |
| API facts, architectural patterns, business rules, conventions | `reference` |
| Sprint status, ticket scope, project decisions, deadlines | `project` |
| Personal tool preferences, settings | `user` |

### 3. Check duplicates and overlap

Read `MEMORY.md`, then **read the full body of any topically-close existing file** — overlap hides behind unrelated-sounding titles (index-line comparison alone missed three separate files independently capturing "a review I commission inherits my framing" because none of their titles or descriptions matched textually).

For each proposal:
- Identical concept → skip (mark as duplicate).
- New detail on an existing principle → propose an **update** to that file (show the diff).
- Overlaps substantially with one or more existing entries without being identical → propose a **merge**: one file capturing the shared principle, replacing the existing member(s) (moved to `_archive/` if this memory dir has one). Do not create a new standalone file when a merge is the better fit.

### 4. Present for approval

Numbered list: title, type, 1-line description. Wait for approval. Per item:
- `approve` → write it
- `edit [what to change]` → adjust
- `skip` → ignore

Do not write without approval. Do not fabricate content — only capture what was actually said.

### 5. Write approved entries

For each approved entry, in sequence:

**a. Create/update file:**
In the current project's memory directory (given in the session's system prompt):
```
{memory_dir}/{type}_{snake_case_name}.md
```

Exact frontmatter (no extra fields):
```markdown
---
name: Human title
description: 1-line summary for the MEMORY.md index
type: feedback
---

[Directive paragraph]

**Why:** [Explanation]

**How to apply:** [Concrete guidance]
```

**b. Update the `MEMORY.md` index:**
- The index is a flat list (no `## Feedback`/`## Reference` section headers) — add a bullet: `- [Name](filename.md) — Description` (<150 chars).
- Verify total index size <8192 bytes (`wc -c MEMORY.md`, matches `scripts/check-ceiling.sh`); warn if >7000 and propose merging into an existing entry instead of appending.

### 6. Report summary

```
Saved N learning(s), skipped M, merged K into existing entries.
MEMORY.md: X/8192 bytes used.
Files created/updated: feedback_name.md, reference_name.md, ...
```
