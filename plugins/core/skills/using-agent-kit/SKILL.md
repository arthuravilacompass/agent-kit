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

Read/Grep/Glob the real usages before answering. An answer based only on memory or generic heuristics fails when the project already uses a specific lib (e.g.: the project's logging lib, the chosen observability tool, the adopted serialization lib, etc.).

**Signal**: the turn delivers an answer about convention/lib/tooling/pattern without any Read, Grep, Glob, or listing of real usage in the same turn.

**When it does NOT apply**: purely conceptual questions ("what is X?"), not about how the *project* does it.

---

### Evidence before claim 🔴

**You MUST NOT** assert a conclusion about code behavior, branch state, feature-flag semantics, route existence, or API contract without having read/grepped/run the corresponding command **in the same turn**.

**Why**: premature assumption is the most common cause of rework in review — the model generates plausible-but-wrong text when it lacks evidence, and the reviewer spends an extra turn refuting it with real data. Examples: assuming a remote-config flag's behavior without reading the config, inferring an environment is "beta" without checking, inventing a route/endpoint that doesn't exist, proposing `-m 1` on a commit that isn't a merge.

**Signal**: the turn contains a factual claim about the project's state **without** any Read/Grep/Bash/git in the same turn; OR it uses "should", "likely", "assuming", "probably", "I imagine", "must be" before a conclusion about state.

**How to apply**: before asserting X about code, list the file(s)/command(s) you need to inspect. Don't conclude until you've read them. If tempted to use "should/likely/assuming/probably", stop and `grep` instead.

**Failure mode**: the reviewer refutes it with evidence (log, code); wasted turn; eroded trust; in repeated cases, the user stops trusting future claims.

---

### Project script before generic shell

Before approximating an analytical metric with generic shell, check whether a dedicated script already exists in the repo (e.g., under `scripts/`) that covers that metric.

**Signal**: the turn uses `wc -c`, `grep | wc -l`, or a Python/awk one-liner for a task already covered by a dedicated project script.

## Verification and Confirmation

### Verify your own claim as adversarially as an agent's 🔴

A review that inherits the framing of whoever produced the work — including yourself — carries the same blind spot. For a claim about state (git/branch/config/topology), prefer a blind/adversarial check (with no preview of what you expect to find) and runtime evidence over self-review; understand a check's mechanism before trusting its verdict.

**Signal**: a claim about state backed by 1 isolated command with no adversarial check; validation done by whoever already held the hypothesis.

**Failure mode**: a wrong claim escalates into the narrative; a framed review lets through what a blind check would catch.

---

### Confirm understanding before producing

On a multi-part request (or a "grill me"-style interview), reflect your understanding back — the parts + the interpretive choices you're making — and confirm with the user BEFORE producing the artifact. Going straight to output buries silent choices that only surface after the work is done.

**Signal**: a request with multiple fronts or ambiguity gets a direct artifact, with no prior reflection + confirmation.

**Failure mode**: wasted effort when the understanding was wrong; eroded trust.

## Scope Discipline

### 3 Questions Before Editing

1. **Is the file in scope?** If it wasn't cited and isn't a direct dependency, don't touch it.
2. **Am I removing an annotation or import?** (DI, observability, lifecycle, override) — keep it by default; removal requires explicit justification.
3. **They asked for doc X — am I editing X?** Edit exactly the file requested.

---

### Edit only in scope

**You MUST NOT** edit files not cited by the user that aren't a direct dependency of the requested change.

**Why**: editing "while I'm in here" hijacks the PR and makes review impossible.

**Signal**: the diff touches a file not cited by the user.

**Failure mode**: review becomes impossible; rollback requires manual cherry-pick.

---

### No silent removal of annotations/imports 🔴

Don't remove dependency-injection, singleton, observability, lifecycle/dispose, or override annotations, or imports, without explicit justification.

**Signal**: the diff removes any of these annotations with no explanation in the PR or commit.

**Exception**: an import genuinely unused, flagged by the linter.

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

**Why**: masking the bug downstream guarantees it resurfaces when the context changes.

**Signal**: the fix adds a conditional in S to compensate for what R should have done.

**Failure mode**: the bug reappears in another caller; the root cause remains in the codebase.

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

**Failure mode**: the action stays broken; the delivery looks like progress but the reported bug remains open.

## Permissions

### NO-COMMIT — Never commit without explicit user request

**You MUST NOT** run `git commit`, `git push`, or `git merge` unless the user explicitly asks.

**Why**: committing or pushing on the user's behalf bypasses their review of what goes on the branch and in history.

**Sinal**: session contains a git commit or push that the user did not explicitly request.

**Failure mode**: unwanted commits on the wrong branch; history rewrite required.

## Posture Vocabulary

Six reasoning modes to deliberately wear when facing a decision — four as in-thread skills, two as isolated subagents; index and output format in `council:council`:

- **Schrödinger** — ambiguous diagnosis: keeps hypotheses alive until an observation exists that discriminates between them.
- **Bohr** — false dichotomy ("A or B"): looks for the axis that dissolves the trade-off.
- **Epicurus** — before calling a design/scope done: separates necessary from wanted-but-dispensable from vain.
- **Sagan** — before investing effort: calibrates whether it matters, at what scale, whether it survives time.
- **Maxwell** — before touching something coupled: maps how the change propagates and which invariants travel.
- **Zeno** — validating a proposed solution: pushes invariants to the limit (zero, one, infinity, concurrent, fail-midway) until it finds where it breaks.

## Kit Governance

The kit's lifecycle rules — state model, unwired → wired promotion, the meta-principle, always-on ceiling, and the "Decisions worth remembering" note — live in `docs/GOVERNANCE.md` **in the agent-kit repo**, not in this injected context. When editing the kit itself (promoting, demoting, turning a repeatedly-failing rule into a mechanism), consult that doc first.
