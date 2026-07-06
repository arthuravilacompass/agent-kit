# MobX Smell Fix — Receitas Canônicas

Companion to the `mobile:mobx-smell-hunter` agent. The hunter *finds* smells; this file *fixes* them with the canonical pattern. Each entry below is a fix recipe — read `REFERENCE.md` for the exhaustive signal/why/failure-mode, and use these steps to drive the migration in the right order.

## When to use

- A reviewer or `mobile:mobx-smell-hunter` cited a specific code (e.g., "MOBX001 in CartStore").
- You're refactoring a store and want to confirm the canonical shape before mutating.
- You introduced new state and want to validate it against the BLOCKER rules before opening a PR.

## How to use

1. **Identify the smell code.** If you don't have one, run the `mobile:mobx-smell-hunter` agent first.
2. **Read the canonical signal** in `REFERENCE.md` (BLOCKER tier — DI001/ARCH001/LOG001 are hook-enforced, the rest are on-demand); STANDARD guidance lives in `mobile:code-review-mobile` STANDARDS.md; ASPIRATIONAL in `PATTERNS.md`. This file summarizes the migration steps.
3. **Apply the fix in the order below.** Order matters when multiple smells overlap (e.g., MOBX001 + SSOT001 in the same store — fix MOBX001 first to introduce the typed atom, then SSOT001 to gate writes).
4. **Re-run the hunter** to confirm the smell is gone.

## Canonical fix patterns

### BLOCKER smells

| Smell | Signal | Canonical fix |
|---|---|---|
| **MOBX001 — Sem boolean flags paralelos** | 2+ mutually exclusive `@observable bool` | Replace with `enum` or `sealed class`. Use sealed class when each state carries different data. |
| **MOBX002 — `@computed` é puro** | `@computed` calls async / mutates state | Move side effect into `@action`. `@computed` must be a pure projection. |
| **MOBX003 — Toda reaction tem dispose** | `reaction/autorun/when` without disposer stored | Store the `ReactionDisposer` in a `late final` field; call it from your DI container's dispose hook or widget `dispose()`. |
| **MOBX004 — Observable e getter (reconciliado)** | Manual getter (`Type get x => _x;`) bypassing the codegen mixin | Remove the manual getter — let the generated `_$Store` mixin expose the accessor. Do NOT rename a public `@observable` to private just because it lacks an underscore; check the project's dominant convention first. |
| **MOBX005 — Mutação pós-await dentro de runInAction** | Multiple post-`await` mutations without `runInAction` | Wrap *all* post-await observable assignments in a single `runInAction(() { ... })`. |
| **ARCH001 — BuildContext/GoRouter fora do store** | `BuildContext` / `GoRouter` / `Navigator` / `showDialog` inside store | Expose state (`@observable CheckoutStep? _pendingStep`) and let the Page/Coordinator observe via `reaction` and navigate. |
| **DI001 — Container de DI não entra no store** | `GetIt.I<T>()` or the project's DI-resolver wrapper inside store/controller | Move resolution to constructor: `MyStore(this._repo)` with the appropriate DI annotation (`@lazySingleton`/equivalent). |
| **"Store não nasce em build()"** | Store created in `build()` | Resolve once in the page constructor or `initState()`: `MyPage() : _store = resolve<MyStore>();` |
| **SSOT001** | `@readonly` (or sealed class observable) written in 2+ sites | Introduce a single `_setX(next)` `@action`. Make every assignment go through it. The `@readonly` annotation makes external writes a compile error. |
| **CMD001** | `bool`/`String` parameter selects *which behavior* the method runs | Replace with sealed `Command` class + exhaustive `switch`. |
| **Action muta estado de erro — não lança exceção** | `throw` inside `@action` | Mutate `_errorMessage` and `_state` instead. Caller observes; doesn't catch. |
| **LOG001** | `print()` / `debugPrint()` in production code | Replace with `dart:developer log()` with `name`, `error`, `stackTrace`. |

### WARNING / STANDARD smells

| Smell | Signal | Canonical fix |
|---|---|---|
| **FSM001** | 3+ observables jointly representing one flow concept | Single `sealed class` state atom; each variant carries its own data. |
| **Ação falível retorna sealed result, não bool/void** | `@action Future<bool>` or `Future<void>` for fallible op | Return a sealed `XResult` class: `XSuccess`, `XValidationError`, `XError`. |
| **Store gerenciada por Coordinator é pura — I/O no Coordinator** | Coordinator-managed store with its own `_repository` | Remove repo from store; store becomes pure state + `apply*` actions. Coordinator orchestrates I/O. |
| **UI não importa SDK nem tipos DTO diretamente** | UI imports from the project's SDK/repository package or types `*DTO` parameters | Replace DTO types with domain entities. Add a `fromDTO` mapper if missing. |
| **MOBX006** | Synthetic concurrency `enum { idle, inFlight }` as `@observable` | Either fold "in-flight" into the domain enum, or replace with non-observable `Future<T>? _pending`. Pick based on whether the user needs to *see* the in-flight state. ASPIRATIONAL — see `PATTERNS.md`. |
| **ObservableList/Map/Set é privado com getter** | Public `ObservableList`/`Map`/`Set` (no underscore) | Privatize + getter. All mutations go through `@action setX(list)`. |
| **@observable bool isolado absorvido no enum de fluxo** | Isolated `@observable bool` that's part of a flow | Fold into the existing flow enum, or convert to `@computed` if derivable. |
| **Resolução de dependência fora do build()** | DI resolver call inside `build()` | Move to constructor (`StatelessWidget`) or `initState()` (`StatefulWidget`). |
| **FocusNode listener não chama setState — lógica vai pro store** | `FocusNode.addListener` calling `setState()` | Move validation into store; widget uses `Observer` to react. |
| **const constructor não resolve dependência em build()** | `const` constructor + DI resolver call in `build()` | Drop `const`; resolve in constructor. |
| **reaction() não chama setState — use Observer granular** | `reaction()` calling `setState()` | Replace with granular `Observer` widget. Use `reaction` only for genuine side effects (navigation, scroll, analytics). |
| **l10n pertence à camada de UI — store recebe string pronta** | l10n resolved inside store / static field | Move to Page; pass localized strings as parameters when the store needs them (rare). |
| **Todo método público tem tipo de retorno explícito** | Public method without explicit return type | Add `void` / `Future<void>` / concrete type. |

## Migration recipes for the hardest cases

### MOBX001 — Sem boolean flags paralelos — use enum/sealed

```
1. Identify the booleans that are mutually exclusive (read together, never simultaneously true).
2. Define the enum / sealed class outside the store class.
3. Replace the bools with one `@observable` field of the new type.
4. Update every write site to assign the new type.
5. Update every read site:
   - `if (isLoading)` → `if (state == X.loading)`
   - Dispatch in UI via `switch` (sealed class) for exhaustiveness.
6. Delete the old `@computed` derivations that combined the bools.
```

### FSM001 → sealed-class flow state

```
1. List every observable that describes "where in the flow we are" (mode, substate, isEditing*, _pending*, _needs*).
2. Enumerate the *valid combinations* the UI actually renders. These are your sealed-class variants.
3. For each variant, list the data the UI needs (selected item ID, draft, error message). Embed it in the variant.
4. Replace the N observables with one `@observable FlowState _flowState`.
5. Migrate writes through `_setFlowState(NewVariant(...))`.
6. UI becomes `switch (store.flowState) { case Editing(:final id) => ...; }`.
```

### SSOT001 → single-writer pattern

```
1. Mark the field with `@readonly` (mobx_codegen) — this makes external writes a compile error.
2. Add `@action void _setX(X next) => _x = next;` as the *only* writer.
3. grep the file for every `_x = ` assignment; replace each with `_setX(...)`.
4. Run codegen and confirm the build passes — any missed write becomes a compile error by construction.
```

### CMD001 → sealed Command

```
1. Identify the boolean/string discriminator parameter (signals: `isNew`, `mode`, `type`, `action`).
2. List the distinct branches inside the method body. Each branch is a Command variant.
3. Define `sealed class XCommand` with one final subclass per branch. Carry only the data each branch needs.
4. Method signature becomes `Future<XResult> run(XCommand cmd)` with `switch (cmd) { ... }`.
5. Update all callers to construct the right Command variant.
```

### Ação falível retorna sealed result, não bool/void

```
1. Enumerate the failure modes the caller cares about (validation? network? domain rule?).
2. Define `sealed class XResult` with `XSuccess(entity)`, `XValidationError(fields)`, `XError(message)`.
3. Replace `try/catch` returning `bool` with a `try/catch` that maps each exception type to a Result variant.
4. Update callers: `switch (await store.submit())` instead of `if (!await store.submit())`.
```

## Cross-references

- **`REFERENCE.md`** (this skill) — full BLOCKER catalogue (hook-enforced: DI001/ARCH001/LOG001; on-demand: MOBX001-005, "Store não nasce em build()") + tier policy.
- **`PATTERNS.md`** (this skill) — ASPIRATIONAL codes with full examples (FSM001, SSOT001, CMD001, MOBX006).
- **`mobile:code-review-mobile`** STANDARDS.md — canonical signals for STANDARD-tier guidance (on-demand).
- **`mobile:mobx-smell-hunter`** — the agent that detects FSM001, SSOT001, CMD001, MOBX006.
- **`mobile:refactor-review`** — run after applying multiple fixes to catch regressions.

## Output expectations

When applying a fix, your report should:
1. **State the smell** being fixed (use title from the table above; include code if it's a code with a validator).
2. **Show the diff** for one representative file.
3. **List remaining work** if multiple files share the same smell.
4. **Flag any unsafe migrations** — e.g., changing a public API of a store invalidates every caller; surface them, don't silently update them.
