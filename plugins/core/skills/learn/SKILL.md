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
- **Index:** `MEMORY.md` (always loaded; 200-line limit)
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

Default scope: entire conversation up to the most recent `/clear`. If the user asked for "last N messages", limit to that.

If no signal is found: report *"No learning detected this session."* and stop.

### 2. Categorize each finding

| Finding | Memory type |
|---|---|
| Behavior correction, style/workflow preference | `feedback` |
| API facts, architectural patterns, business rules, conventions | `reference` |
| Sprint status, ticket scope, project decisions, deadlines | `project` |
| Personal tool preferences, settings | `user` |

### 3. Check duplicates

Read `MEMORY.md`. For each proposal:
- Compare semantically against existing names/descriptions.
- Identical concept → skip (mark as duplicate).
- New version adds useful detail → propose an **update** to the existing file (show the diff).

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
- Find the section matching the type: `## Feedback`, `## Reference`, `## Project`, `## User`.
- Add a bullet: `- [Name](filename.md) — Description` (<150 chars).
- Verify total <200 lines; warn if >185 and suggest consolidation.

### 6. Report summary

```
Saved N learning(s), skipped M.
MEMORY.md: X/200 lines used.
Files created: feedback_name.md, reference_name.md, ...
```
