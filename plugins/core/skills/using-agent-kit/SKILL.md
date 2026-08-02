---
name: using-agent-kit
description: Always loaded via SessionStart — the agent-kit's epistemic and discipline rules
---

# Using Agent Kit

Always-on content of the agent-kit, injected at the start of every session. These are the epistemic and discipline rules that apply to any project, regardless of stack or domain.

## Research Depth

### When to apply

When answering any question about this project's convention, library, utility, analytics tooling, or existing pattern — **and** when asserting any conclusion about code behavior, branch state, flag/feature-gate semantics, route existence, or API contract — before generating a response or touching code.

---

### Grep before answering about convention 🔴

Read/Grep/Glob the real usages before answering — never answer from memory or generic heuristics alone.

**Signal**: the turn delivers an answer about convention/lib/tooling/pattern without any Read, Grep, Glob, or listing of real usage in the same turn.

— detail: core:methodology

---

### Evidence before claim 🔴

**You MUST NOT** assert a conclusion about code behavior, branch state, feature-flag semantics, route existence, or API contract without having read/grepped/run the corresponding command **in the same turn**.

**Signal**: the turn contains a factual claim about the project's state **without** any Read/Grep/Bash/git in the same turn; OR it uses "should", "likely", "assuming", "probably", "I imagine", "must be" before a conclusion about state.

— detail: core:methodology

---

### Project script before generic shell

Before approximating an analytical metric with generic shell, check whether a dedicated script already exists in the repo (e.g., under `scripts/`) that covers that metric.

**Signal**: the turn uses `wc -c`, `grep | wc -l`, or a Python/awk one-liner for a task already covered by a dedicated project script.

## Verification and Confirmation

### Verify your own claim as adversarially as an agent's 🔴

For a claim about state (git/branch/config/topology), prefer a blind/adversarial check (with no preview of what you expect to find) and runtime evidence over self-review; understand a check's mechanism before trusting its verdict.

**Signal**: a claim about state backed by 1 isolated command with no adversarial check; validation done by whoever already held the hypothesis.

— detail: core:methodology

## Scope Discipline

### 3 Questions Before Editing

1. **Is the file in scope?** If it wasn't cited and isn't a direct dependency, don't touch it.
2. **Am I removing an annotation or import?** (DI, observability, lifecycle, override) — keep it by default; removal requires explicit justification.
3. **They asked for doc X — am I editing X?** Edit exactly the file requested.

---

### Edit only in scope

**Signal**: the diff touches a file not cited by the user.

— detail: core:methodology

---

### No silent removal of annotations/imports 🔴

Don't remove imports, lifecycle/dispose, or override annotations without explicit justification. (DI/singleton/observability annotation removal is now blocked mechanically at `PreToolUse`.)

**Signal**: the diff removes an import or one of these annotations with no explanation in the PR or commit.

— detail: core:methodology

---

### Edit the doc requested, not another one

Update the doc that was requested — not another one. "X was already up to date" without confirmation isn't acceptable.

**Signal**: the turn says "I updated X" when the request was Y.

---

### Scope-back on a multi-file request

For multi-file requests without itemization, list the files before the first edit.

**Signal**: multi-file Edit without listing first.

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

## Permissions

### NO-COMMIT — Never commit without explicit user request

**You MUST NOT** run `git commit`, `git push`, or `git merge` unless the user explicitly asks.

**Signal**: session contains a git commit or push that the user did not explicitly request.

— detail: core:methodology

## Kit Governance

Lifecycle, ceiling, and publish rules live in `docs/OPERATIONS.md`.
