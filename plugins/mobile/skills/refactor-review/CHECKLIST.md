# Refactor Review — Checklist

## Phase 1 — Regression Analysis

For each dimension, analyze `git diff --cached` (or `git diff`). State "No issues found" explicitly if clean — do not skip.

### 1.1 Behavioral Regressions

- Removed/renamed functions: grep all call sites — are any broken?
- Signature changes (params added/removed/reordered/type-changed): do all callers still pass compatible args?
- Return type/shape changes: do all consumers handle the new return?
- Same inputs → same observable output?

### 1.2 Silently Altered Business Rules

- Rewritten conditionals/loops/validators: same cases covered before vs after?
- "Simplified" conditions that now match different inputs (`> 0` → `!= null`, `isEmpty` → `== null`)?
- Guards removed as "dead code" that were actually protecting a business rule?
- Changed default values/fallbacks — do they alter behavior for existing data?

### 1.3 Hidden Side-Effects

- Removed/moved code: did it trigger analytics events, RUM calls (the project's tool), cache invalidation, state updates, notification dispatches?
- Was it inside `try/catch/finally` where `finally` had cleanup logic?
- Was it setting a flag downstream code depends on (`_isLoaded = true`, `_hasBeenValidated = true`)?
- Was it part of an optimistic update rollback path?

### 1.4 Broken Contracts

- Repository interface signature change? Grep all implementations and callers.
- Entity `fromDTO()`, `copyWith()`, or `props` change? Check all construction sites and equality comparisons.
- Store public getter or `@computed` type/semantics change? Check all `Observer` widgets depending on it.
- Route parameter change? Check all `context.push()`/`context.go()` call sites.
- **Sealed class wildcard audit:** For every `_ =>` wildcard in switch statements — enumerate variants that fall into it. Is "do nothing" the *correct, intentional* behavior for each? Prefer exhaustive switches; if a no-op is intentional, name it explicitly (`SomeTransientState() => _state, // no-op: transient state`).

### 1.5 Uncovered Edge Cases

- Removed defensive code: null checks, empty list guards, zero-value handling, default branches?
- Simplified timeout or retry logic?
- Error state handling (loading/error/empty) — does refactored code still handle all three?
- Boundary conditions: first item, last item, single item, max pagination, empty search results.

### 1.6 Invisible Coupling

- Moved/extracted code: does it still have access to the same scope (DI, context, lifecycle)?
- Execution order still holds? Check code depending on `initState`, specific `@action`, or `runInAction()` block.
- `@lazySingleton` vs `@injectable` vs `@singleton` — did a lifetime scope change? (A `@lazySingleton` becoming `@injectable` creates new instances where there should be one.)
- MobX reactions and `autorun` — any dependency chain broken by an observable moved or renamed?

### 1.7 Unmapped Scenarios

- Input/state combinations not handled: concurrent async calls, partial failures, cancellation mid-flow.
- Assumptions may not hold: specific user roles, legacy data formats, empty collections, guest vs logged-in.
- Race conditions: fire-and-forget, multiple rapid taps, navigation during loading.
- External dependency failures: API timeout, null response body, malformed JSON, network offline.
- **Cross-store seam audit:** For every store that calls a method on another store, enumerate every state the called store can be in at call time — across ALL entry points, not just the happy path. Verify the method produces the correct side-effect for each entry state.

These are not necessarily regressions — flag as pre-existing risks exposed by the refactor.

---

## Phase 2 — Code Quality

Run each in order. Reference Phase 1 findings where relevant.

### 2.1 Bloat and Dead Code

- `/simplify` — changed code for reuse, dead code, efficiency.
- Unused imports, unreferenced private fields, `@computed` properties nothing observes, commented-out code, TODO without tickets.

### 2.2 Over-Engineering

- Abstractions serving only one concrete implementation?
- Generic type params always used with the same concrete type?
- Design patterns (Strategy, Factory, Decorator) where a simple function would suffice?
- New layers or indirections that don't carry their weight?

### 2.3 Redundancy and Duplication

- Functions doing similar things with different names.
- Parallel data structures representing the same domain concept.
- Copy-pasted logic that should be extracted to a shared module.

### 2.4 Accidental Complexity

- Deeply nested conditionals → flatten with early returns.
- Functions >40 lines doing multiple things.
- Boolean parameters that control branching → separate functions.
- Complex expressions → extract to named variable or `@computed`.

### 2.5 Cohesion and Responsibility

- `mobile:code-review-mobile` (`STRUCTURE.md`) — module structure, layer boundaries, import direction.
- Store contains repository logic? Widget contains business logic in `build()`?
- Entity imports from UI layer? Repository imports from store?

### 2.6 Consistency and Patterns

- `mobile:code-review-mobile` — full Flutter/Dart checklist.
- Compare with nearest sibling module — naming, structure, style match?
- Private observables with public getters, `runInAction()` after await, `const` constructors, `required` params, project line-length convention.

### 2.7 Silent Fragility

- Trace every user-facing touchpoint through its full state change sequence.
- Implicit ordering dependencies, temporal coupling, state "just happens" to be initialized before use.

### 2.8 Readability and Expressiveness

- Code communicates intent? New team member understands without context?
- Names descriptive, matching domain language?
- Logic rewritable to be more self-documenting?

---

## Output Format

```markdown
# Refactor Review — [scope description]

## Phase 1: Regression Analysis

### Behavioral Regressions
[findings or "No issues found"]

### Silently Altered Business Rules
[findings or "No issues found"]

### Hidden Side-Effects
[findings or "No issues found"]

### Broken Contracts
[findings or "No issues found"]

### Uncovered Edge Cases
[findings or "No issues found"]

### Invisible Coupling
[findings or "No issues found"]

### Unmapped Scenarios (pre-existing risks)
[findings or "None identified"]

## Phase 2: Code Quality

### Bloat / Over-Engineering / Redundancy
[findings]

### Complexity / Cohesion / Consistency
[findings]

### Fragility / Readability
[findings]

## Summary

| Category | Issues | Severity |
|---|---|---|
| ... | ... | Bug / Structure / Pattern / Quality / Info |

### Blocks merge
[list or "None"]

### Should fix in this PR
[list or "None"]

### Can be follow-up
[list or "None"]
```
