---
name: using-agent-kit
description: Always loaded via SessionStart — the agent-kit's epistemic and discipline rules
---

# Using Agent Kit

Always-on content of the agent-kit, injected at the start of every session. Domain-specific opinion the model doesn't have by default — not a restatement of harness-level scope/verification/commit behavior, which the model already does well without prompting.

## Bugfix Principles

### 4 Questions Before Any Fix

1. **Where was the contract violated? Is the fix in the same layer?**
2. **Does the fix use `isEmpty`/`null` to infer what the operation returned?** — if so, it's a data-model problem, not a flow problem.
3. **Does the fix preserve state across operations? Name it: origin, home, discard.**
4. **Does the safety argument depend on an unwritten invariant?** If it contains "always", "never", "at this point" — encode it in the type.

---

### Fix at the source, never at the consequence 🔴

**You MUST NOT** fix the consumer to compensate for what the producer should have done.

**Signal**: the fix adds a conditional in S to compensate for what R should have done.

— detail: core:methodology

---

### Absent ≠ empty

`isEmpty`/`== null`/`?? fallback` don't distinguish "came back empty" from "wasn't returned". The fix belongs in the data model.

**Signal**: the fix uses `isEmpty`/`null` to decide whether to preserve previous state.

---

### State that survives has a named lifecycle

State that survives multiple operations needs an explicit origin, a named home, an explicit discard point.

**Signal**: the fix can't name the origin, home, and discard point of the state it preserves.

---

### Implicit invariant becomes a type

"Safe because X always happens before Y" = an unwritten invariant. Encode it in the type or structure.

**Signal**: the argument contains "always", "never", "at this point", "before this".

---

### Fix scope = reported-bug scope

When the reported bug is "action X does nothing", the fix needs to make X work — decorating the broken state with an error message, a warning, or a UX change instead of that is not a fix for the reported bug.

**Signal**: the fix responds to "X doesn't work" with new messaging/UX instead of making X execute/record.

## Code Change Discipline

### No silent removal of annotations/imports 🔴

Don't remove imports, lifecycle/dispose, or override annotations without explicit justification — DI, observability, and lifecycle wiring look dead from a local diff but aren't.

**Signal**: the diff removes an import or one of these annotations with no explanation in the PR or commit.

**Exception**: an import genuinely unused, flagged by the linter.

— detail: core:methodology

## Kit Governance

Lifecycle, ceiling, and publish rules live in `docs/OPERATIONS.md`.
