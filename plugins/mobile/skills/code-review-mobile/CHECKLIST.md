# Flutter Code Review Checklist

Universal code review checklist for Flutter/Dart (stack: MobX + get_it/injectable + go_router + dartz). Always loaded during PR review.

## Verification Discipline (mandatory)

Before listing any finding in a review report, re-read the exact lines you're about to flag and cite them. If the issue is already fixed in the file's current state, drop the finding. Reviews lose credibility when they list issues that are already resolved.

Applies to:
- Reviews of remote PRs (the file on the remote branch may differ from the diff's initial snapshot)
- Reviews after the author pushed new commits mid-review
- Any finding produced by a subagent that didn't read the file directly

**Rule**: every finding in the final report needs a file path + line number, and you must have just read those lines.

## Workflow

1. `git diff <base>...HEAD` (config: the project's base branch) to see all commits in the PR
2. Apply **Layer 1** below — every PR, no exception (17 items)
3. Apply **Layer 2** (this skill) — only when the trigger is true
4. If it's a refactor: `mobile:refactor-review` (2-phase protocol)
5. Before commit/PR: run your setup's commit/PR flow (e.g. `core:commit`, `core:pr`)

## Layer 1 — Always Review

| # | Item | Rule |
|---|---|---|
| 1 | Correct business logic | — |
| 2 | State shape: no parallel boolean flags | MOBX001 |
| 3 | `runInAction()` after await with multiple mutations | MOBX005 |
| 4 | Error handling: `Either` in the repo, `fold` in the controller (or your project's error pattern) | architecture |
| 5 | Fix at the right layer (don't compensate for the producer in the consumer) | bugfix principles (project config) |
| 6 | Null safety: no excessive `!`, no implicit `dynamic` | Dart |
| 7 | Generic `catch (e)` with no `on` → specify the exception type | Dart |
| 8 | Never catch `Error` (indicates a bug, shouldn't be handled) | Dart |
| 9 | No `print()` in production → use `dart:developer log()` | LOG001 |
| 10 | No sensitive data in logs (tokens, PII) | Security |
| 11 | Tests added/updated for new code | Testing |
| 12 | Controllers don't throw exceptions → mutate state or return a sealed result | CTRL001 |
| 13 | Direct call to the DI container never inside a Store/Controller | DI001/DI004 |
| 14 | Explicit return type on `@action` and public methods | DART001 |
| 15 | Error state carries information for display (not just a flag) | state shape |
| 16 | Loading state doesn't retain data from a previous fetch | state shape |
| 17 | No comments explaining which rule was applied (`// MOBX004`, `// item 6`) in production code — a comment describes the *why*, not the rule | code hygiene |

## Comment Prefixes

Common PR review convention (adapt to your project's tool — GitHub, Bitbucket, etc.):

| Rule tier | Rules | Prefix |
|---|---|---|
| 🔴 BLOCKER | MOBX001-005, ARCH001, DI001-002, LOG001 | `blocker:` |
| 🟡 STANDARD | codes in `STANDARDS.md` (on-demand) | `blocker:` |
| 🔵 ASPIRATIONAL | FSM001, ARCH002-003, CMD001, SSOT001, MOBX006 | `non-blocker:` |
| Personal preference | style, names, decomposition | `non-blocker:` |

`blocker:` = must fix before merge. `non-blocker:` = evaluate and respond — may disagree with justification.

Format: `blocker: MOBX001 — _isLoading and _hasError are parallel flags, should be an enum (BasketStore.dart:42)`

## Shortcuts

- This skill — Layer 2 (contextual triggers) + reference (component structure, naming, imports, formatting)
- `mobile:refactor-review` — 2-phase refactor protocol
- `mobile:mobx` `RECIPES.md` — fix recipes by smell code
- Your setup's review entry points (config): full pre-PR review, pre-push review, remote PR review

## Canonical Sources

- `mobile:mobx` `REFERENCE.md` — codified rules (MOBX*, DI*, ARCH*, LOG001) BLOCKER tier
- `STANDARDS.md` (this skill) — on-demand STANDARD codes
- `SKILL.md` (this skill) — contextual Layer 2 + component structure reference
- `COOKBOOK.md` — DI, navigation, Either pattern, Security checklist, Testing examples

## Layer 2 — When Applicable

| # | When | Item | Rule |
|---|---|---|---|
| 18 | There are reactions | Reactions disposed in `dispose()` | MOBX003 |
| 19 | There is UI | No SDK/DTO import in the UI layer | ACL001 |
| 20 | There is UI | Design system components + visual tokens (config: your project's token system) | UI001/UI002 |
| 21 | There is UI | `build()` < ~100 lines, decompose into widgets | Widget |
| 22 | There is UI | Subwidgets in their own classes (element reuse + const propagation) | Widget |
| 23 | There is UI | `const` constructors on widgets whose fields are `final` | Widget |
| 24 | There is an Observer | Granular Observer (smallest possible scope, not the whole screen) | Performance |
| 25 | There is an Observer | Static subtrees inside Observer marked `const` | Performance |
| 26 | There are lists | `ListView.builder` / `GridView.builder` for large lists | Performance |
| 27 | There is complex rebuild | `RepaintBoundary` on subtrees that repaint independently | Performance |
| 28 | There are network images | Caching, appropriate resolution, `cacheWidth`/`cacheHeight`, placeholder/error | Performance |
| 29 | There is opacity animation | `AnimatedOpacity`/`FadeTransition` instead of direct `Opacity` | Performance |
| 30 | There is layout | `IntrinsicHeight`/`IntrinsicWidth` used sparingly (extra layout pass) | Performance |
| 31 | There is MediaQuery | `MediaQuery.sizeOf(context)` instead of `MediaQuery.of(context).size` | Performance |
| 32 | There is fire-and-forget async | Race conditions: version token or cancellation | MobX |
| 33 | There are collections in the UI | Sorting/filtering outside `build()` → `@computed` | Performance |
| 34 | There are new strings | l10n present in every supported locale (config: project's list) | L10n |
| 35 | There are localized strings | No concatenation — use placeholders in the key | L10n |
| 36 | There is date/currency/number | Locale-aware formatting (don't hardcode the locale) | L10n |
| 37 | There is l10n in store/controller | l10n resolved in the Page, injected via parameter | L10N001 |
| 38 | There is DI resolution in a widget | Never in `build()`, only in `initState()` or a final field | DI003 |
| 39 | There is `ObservableList/Map/Set` | Must be private (`_`) with a public getter | MOBX007 |
| 40 | There is a `const` widget | `const` constructor + DI resolution in build = error | WIDGET003 |
| 41 | There is a FocusNode | Listeners never call `setState()` → logic goes in the store | WIDGET002 |
| 42 | There is `reaction()` in a widget | Never calls `setState()` → use Observer instead | PERF001 |
| 43 | There is pagination | An error on the next page doesn't destroy the already-loaded list | Errors |
| 44 | There are transient errors | Retry available to the user | Errors |
| 45 | There is navigation | Typed arguments via `extra` — no `Map<String, dynamic>` or `Object?` cast | Navigation |
| 46 | There is a new DI class | No circular dependencies in the graph | DI |
| 47 | There are tests | Edge cases: empty, error, loading, pagination, filter | Testing |
| 48 | There are tests | Each test file covers a single class | Testing |
| 49 | There are widget tests | `pumpWidget` + `pump`/`pumpAndSettle` used correctly (no `sleep`) | Testing |
| 50 | There are critical visual components | Golden tests covering states | Testing |

## Standards — Supporting Content

### Dart Language

- **`late`** — use only when necessary; prefer nullable or constructor initialization
- **`final`/`const`** — `final` for local variables, `const` for compile-time constants
- **Switch expressions** — prefer over `if/else is` cascades for pattern matching (Dart 3+)
- **Records** — `(String, int)` for simple multi-value returns instead of throwaway classes
- **Sealed class** — model states with mutually exclusive variants
- **`unawaited()`** — a `Future` returned without `await` must be marked with `unawaited()` to signal intent
- **`StringBuffer`** — use in loops; no string concatenation (`+=`) in loops

### Widget Keys

- **`ValueKey`** — use in lists/grids to preserve state across reorders
- **`GlobalKey`** — use sparingly; never for state sharing between widgets
- **`UniqueKey`** — never in `build()` (forces a rebuild every frame)

### Race Conditions

```dart
// BAD — race condition if updateFilter is called twice quickly
@action
void updateFilter(FilterEntity newFilter) {
  _resetFilter();
  fetchFilteredProducts();  // fire-and-forget, no protection
}

// GOOD — version token discards stale responses
int _filterVersion = 0;

@action
Future<void> fetchFilteredProducts() async {
  final version = ++_filterVersion;
  final result = await _repository.getProducts(filter);
  if (version != _filterVersion) return;  // stale, discard
  runInAction(() {
    result.fold(
      (failure) => _state = ProductListState.error,
      (items) {
        _items
          ..clear()
          ..addAll(items);
        _state = ProductListState.success;
      },
    );
  });
}
```

### Navigation Guards

- Auth guards centralized in a route middleware — don't replicate auth logic in every route
- Deep links configured on both platforms (Android intent-filter + iOS Universal Links) — see `mobile:deeplink-debug`
- Consistent `context.pop()` — don't mix `Navigator.of(context).pop()` and `context.pop()` in the same flow
- Typed arguments via `extra` — never `Map<String, dynamic>` or an `Object?` cast

### Coverage

Common target: 80% on stores/repos (config: your project's goal). `setUp()` patterns and state-transition coverage: see `COOKBOOK.md` §Testing.
