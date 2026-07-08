# Flutter/Dart/Architecture — STANDARD Codes

Common team agreements in Flutter/MobX projects — `blocker:` by default in review, an exception needs justification in the PR. These codes are a starting point; adapt/rename them to your team's real conventions.

> **UI codes** (V1/V2 component versioning, raw visual values, Material widget) depend on your project's design system — if it versions components or centralizes visual tokens, adapt these codes to your config.

---

## Configurable Business Value Isn't Hardcoded on the Client

Values that vary by brand, locale, market, or release cadence belong in the backend/CMS — not on the client. Hardcoding it speeds things up today and creates a release bottleneck tomorrow (any change becomes an app deploy + store review).

Domain examples: filter date presets, sort options, promotional banners, currency/tax/shipping rules, per-market feature toggles, brand-specific labels.

**Signal**: an array/map of constants in a widget or store representing filter options, sort, presets, or brand labels; or a `const` list that could change without a release.

**When it does NOT apply** (legitimate client defaults):
- Animation timing, pagination page-size, debounce
- Locale-derived format strings (currency formatter, date formatter)
- Purely internal UI state (snap points, breakpoints)

---

## UI Doesn't Import the SDK or DTO Types Directly

UI files (`*_widget.dart`, `*_page.dart`, `*_screen.dart`) must not import from the project's SDK/repository package nor declare parameters or fields with `*DTO` types. When this happens, the external model leaks into the presentation layer, coupling the UI to the API contract.

**Signal**: an import from the SDK/repository package (config: your project's package name) or a `*DTO` type in `*_widget.dart`, `*_page.dart`, `*_screen.dart`.

**When it does NOT apply**: files inside the SDK package itself — there, the external vocabulary is expected by design.

---

## ObservableList/Map/Set Is Private With a Getter

`ObservableList`, `ObservableMap`, and `ObservableSet` must be private fields with a public getter. Direct exposure allows external mutation with no `@action`, breaking traceability.

**Signal**: `@observable ObservableList` (or Map/Set) with no underscore in the name.

---

## An Isolated @observable bool Absorbed Into the Flow Enum

A single `@observable bool` that represents a flow state (not an independent UI flag) must be absorbed into the existing state enum. Isolated booleans create implicit compound states.

**When it does NOT apply**: UI booleans genuinely independent of domain state (e.g. `_isBottomSheetOpen` for local visual control).

**Signal**: `@observable bool` that coexists with a flow-state enum in the same store.

---

## Dependency Resolution Outside build()

Resolving a dependency from the DI container inside `build()` resolves it on every rebuild — creates unnecessary instances and prevents `const` propagation. Resolve in the constructor, `initState()`, or a final field.

**Signal**: a DI-resolution call (`GetIt.I`, or your project's wrapper) inside a `build()` or `_build*()` method.

---

## A DI-Resolution Call Doesn't Enter the Store

Stores receive dependencies via the constructor (injectable or equivalent). Calling the DI container's resolver inside the Store breaks inversion of control and hinders testing.

**Signal**: `GetIt.I`, `GetIt.instance`, or the project's DI wrapper inside `*_store.dart` or `*_controller.dart`.

Differs from DI001: DI001 covers the direct container call (`GetIt.I<T>()`); this code covers any equivalent wrapper the project has built on top of it.

---

## Action Mutates Error State — Doesn't Throw an Exception

`@action` methods that `throw` force the caller to use `try/catch`. The correct contract is to mutate the observable state to an error, or return a sealed result — the caller observes, it doesn't catch.

**Signal**: `throw` inside an `@action` method in a store or controller.

---

## Every Public Method Has an Explicit Return Type

Every public and `@action` method must have an explicit return type. Inference like `dynamic` causes silent errors and hinders review.

**Signal**: a method with no return type before the name (`clearData()` instead of `void clearData()`).

---

## FocusNode Listener Doesn't Call setState — Logic Goes in the Store

Focus logic (validation, field state) belongs in the store/controller. `FocusNode.addListener` that calls `setState()` mixes UI logic with form state.

**Signal**: `addListener` + `setState` in the same block.

---

## const Constructor Doesn't Resolve a Dependency in build()

A widget with a `const` constructor that resolves a DI dependency in `build()` is a contradiction: `const` implies the widget is immutable and reusable, but resolving in build runs on every rebuild. Remove `const` or move the resolution outside build.

**Signal**: `const` constructor + DI resolution inside `build()`.

---

## reaction() Doesn't Call setState — Use a Granular Observer

`reaction()` that calls `setState()` defeats MobX's tracking — it forces a rebuild of the entire widget instead of letting `Observer` granularly rebuild the affected subtree.

**When it does NOT apply**: genuine side effects (navigation, scroll, analytics) that aren't UI rebuilds.

**Signal**: `reaction(` with a callback that calls `setState(`.

---

## l10n Belongs to the UI Layer — the Store Receives a Ready-Made String

Stores are the domain/application layer — they don't know about locale. l10n resolution belongs to the UI layer (Page). If the store needs localized strings, it receives them via a parameter.

**Signal**: l10n resolution (e.g. `AppLocalizations.of(context)` or equivalent) inside `*_store.dart` or `*_controller.dart`.

---

## Adding New Codes

See the policy in `mobile:mobx` `REFERENCE.md` §Adding New Codes.
