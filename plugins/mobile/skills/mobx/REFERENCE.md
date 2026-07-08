# MobX & DI Quality — Reference

## Philosophy — Before Proposing Any State Change

**1. Does this state already exist in the store?** → observe it directly. Never create parallel imperative control (`GlobalKey`, callbacks, exposed `State`).

**2. Am I adding a boolean flag?** → almost always a signal for an enum or sealed class. `isLoading + isError` → `enum State { idle, loading, success, error }`.

**3. Am I using a counter to track something?** → anti-pattern. Use an observable list or derived state. `@computed int get count => items.length`.

**4. Could this `@observable` be a `@computed`?** → if it derives from other state, it's `@computed`. Redundant observables cause desync.

**5. Does the name reflect the domain, not the mechanism?** → `isEditingInput` → bad · `addressInputState` → good. Name = business concept.

---

## When to Apply

When generating, editing, or reviewing any `*_store.dart`, `*_controller.dart`, `*_page.dart`, `*_screen.dart`, or `*_widget.dart`. Covers smells the linter doesn't detect.

## Tiers — Enforcement Geography

| Tier | Where it lives | Behavior in review |
|---|---|---|
| 🔴 **BLOCKER (hook)** | This skill + `hooks/smell-checker.sh` (project config — see this plugin's hooks Task) | Blocks mechanically (exit 2) — DI001, ARCH001, LOG001 |
| 🔴 **BLOCKER (on-demand)** | This skill (REFERENCE.md) | `blocker:` — loaded by review agents and the advisor; no mechanical gate |
| 🟡 **STANDARD (on-demand)** | This skill + `mobile:code-review-mobile` STANDARDS.md | `blocker:` by default; an exception needs justification in the PR |
| 🔵 **ASPIRATIONAL** | `PATTERNS.md` (this skill) | `non-blocker:` — suggestion. Applies to new code; doesn't force a refactor |

> **Important:** ASPIRATIONAL ≠ "weak rule". It's a sophisticated pattern that deserves gradual enforcement. Blocking a small bugfix PR over an ASPIRATIONAL item is friction with no proportional benefit.

## Enforcement

Code with an ID is only born together with its machine-validator (hook, eval, or agent); with no validator, write prose with a strong title. IDs with a mechanical validator:

- **DI001, ARCH001, LOG001** — this plugin's `hooks/smell-checker.sh` (exit 2, add-only). The remaining BLOCKER items (MOBX001-005, "Store isn't created in build()") stay prose-only in this skill — there's no automatic gate for them.
- **FSM001 / SSOT001 / CMD001 / MOBX006** — `mobile:mobx-smell-hunter` agent.

---

## 🔴 BLOCKER

### MOBX001 — Parallel Boolean Flags in a Store

**You MUST NOT** create two or more mutually exclusive `@observable bool` in the same store.

**Why**: the real state is an enum/sealed class. Parallel boolean flags allow invalid combinations (`isLoading=true && isError=true`) and cause reactions on inconsistent intermediate states.

**Signal**: two+ `@observable bool` in the same store with no corresponding enum, with complementary names (`is*`, `has*`, `_pending*`, `_needs*`).

**Failure mode**: UI renders an impossible state (spinner + error simultaneously); Observer rebuilds on combinations that shouldn't exist; poor debugging.

---

### MOBX002 — `@computed` with a Side Effect

`@computed` is a pure function. No I/O, no async, no mutations, no calls that alter state.

**Signal**: a method call that mutates state, `await`, or `setState()` inside `@computed`.

**Failure mode**: `@computed` with a side effect can run at unexpected times (MobX tracks access, not explicit calls); I/O in a computed creates loops and non-deterministic behavior.

---

### MOBX003 — reaction/autorun/when Without Dispose

Every `ReactionDisposer` must be stored and called at teardown. In DI-managed classes, use your container's dispose hook (e.g. `injectable`'s `@disposeMethod`).

**Signal**: `reaction(`, `autorun(`, `when(` with no assignment to a `ReactionDisposer`; or a `ReactionDisposer` with no corresponding dispose.

**Failure mode**: memory leak — the reaction keeps running even after the object is "destroyed"; in widgets this causes `setState` after dispose.

---

### MOBX004 — Observable and Getter (Reconciled)

**Original formulation** (doesn't reflect practice — see the correction below): "`@observable` must be a private field (`_field`) with a public getter."

**Recorded correction**: measured in a real project (2026), **61% of `@observable`s in real stores were public** (no underscore) and reactively correct — the dominant pattern was `class X = _XBase with _$X;` + a public `@observable` field on the abstract base class, with `mobx_codegen` generating the tracked accessor via the mixin. A public field does **not** break reactivity when the generated mixin is what exposes the accessor. A review that treated a public `@observable` as a clear violation was wrong — the real practice was on the code's side, not the rule's.

**You MUST NOT** declare a manual getter that bypasses the generated mixin.

**Real signal**: a hand-written getter (`Type get x => _x;`) over a field that should only be exposed by the generated class (`_$Store`). This IS what breaks tracking — MobX doesn't know that `x` depends on `_x` outside the codegen mechanism.

**Signal that should NOT be treated as a violation by itself**: `@observable` with no underscore in the field name. Check the project's convention before flagging it — it may be the dominant pattern and reactively sound.

**Failure mode (of the real smell)**: a manual getter isn't tracked as a dependency by MobX; an `Observer` reading the getter doesn't rebuild when `_x` changes.

**How to apply**: if the project uses the private+getter pattern, keep it consistent with the rest of the file. If the project uses a direct public field (abstract base class with mixin), don't force the migration — only flag the manual getter.

---

### MOBX005 — Multiple Post-await Mutations Without `runInAction()`

**You MUST NOT** assign to an `@observable` after `await` outside of `runInAction()`.

**Why**: without `runInAction()`, each assignment fires a separate reaction. Observers see invalid intermediate states (e.g., `data` populated but `isLoading` still true).

**Signal**: assignment to an `@observable` (or a call to an observable setter) after `await` with no wrapping `runInAction(() { ... })`.

**Failure mode**: UI flickers / renders an inconsistent state; reactions fire at the wrong times; hard-to-reproduce race conditions.

---

### ARCH001 — `BuildContext` / `GoRouter` / `Navigator` Inside a Store

> enforced-by: `hooks/smell-checker.sh` (exit 2)

**You MUST NOT** reference `BuildContext`, `Navigator`, `GoRouter`, `ScaffoldMessenger`, `showDialog` inside `*_store.dart` or `*_controller.dart`.

**Why**: stores are the domain/application layer. They don't know about UI. Coupling to `BuildContext` prevents testing without a widget tree and breaks the layer separation.

**Signal**: `context.push`, `context.pop`, `Navigator.of`, `GoRouter.of`, `showDialog`, `ScaffoldMessenger.of` inside a store/controller file.

**Failure mode**: the store becomes impossible to test without a widget; a navigation refactor cascades across N stores; coordination ends up scattered.

**How to apply**: the store exposes `@observable State` → the Page observes via `Observer` and calls `context.push` / `Navigator.pop` in the widget callback.

---

### DI001 — `GetIt.I<T>()` Inside a Store or Controller

> enforced-by: `hooks/smell-checker.sh` (exit 2)

**You MUST NOT** call `GetIt.I<>`, `GetIt.instance.get`, or equivalent wrappers inside `*_store.dart` or `*_controller.dart`.

**Why**: dependencies arrive via the constructor (`injectable` + `@injectable`/`@lazySingleton`, or your DI container's equivalent). The DI container is the registration module's responsibility, not the consumer's.

**Signal**: `GetIt.I<`, `GetIt.instance`, `GetIt.I.get`, or the project's DI-resolution wrapper (config) inside a store/controller.

**Failure mode**: invisible dependencies break tests (need a stub for the global container); uncontrolled lifecycle; a DI refactor becomes risky.

**How to apply**: the store receives dependencies via the constructor (`MyStore(this._repo, this._coordinator)`); registration lives in the project's DI module with the appropriate annotation.

---

### "Store Isn't Created in build()"

A store created in `build()` is destroyed and recreated on every rebuild — it loses all its state.

**Signal**: `StoreClass()` or `ControllerClass()` instantiated inside a `build()` method.

**Failure mode**: state lost on every rebuild; the DI container doesn't manage the lifecycle; possible leak if the store is never disposed.

---

### LOG001 — `print()`/`debugPrint()` Replaced With `dart:developer log()`

> enforced-by: `hooks/smell-checker.sh` (exit 2)

`print()` and `debugPrint()` in production code (`lib/src/` or equivalent — project config) must be replaced with `dart:developer log()`.
`print()` isn't filtered by level, doesn't carry a stackTrace, and pollutes the console in production.

**Signal**: `print(` or `debugPrint(` in production files.
**Exception**: test files may use `print()`.

---

## 🟡 STANDARD on-demand

See `mobile:code-review-mobile` STANDARDS.md: configurable business value isn't hardcoded on the client, UI doesn't import SDK/DTO types directly, `ObservableList`/`Map`/`Set` is private with a getter, an isolated `@observable bool` is absorbed into the flow enum, dependency resolution outside `build()`, a DI-resolution call doesn't enter the store, an action mutates error state instead of throwing an exception, every public method has an explicit return type, a `FocusNode` listener doesn't call `setState` (logic goes in the store), a `const` constructor doesn't resolve a dependency in `build()`, `reaction()` doesn't call `setState` (use a granular `Observer`), l10n belongs to the UI layer (the store receives a ready-made string).

## 🔵 ASPIRATIONAL — PATTERNS.md (on-demand)

FSM001, CMD001, SSOT001, MOBX006 (with IDs — validated by the `mobile:mobx-smell-hunter` agent). Narrative forms: a fallible action returns a sealed result; a Coordinator-managed store is pure. `non-blocker:` in review.

---

## Code Policy

Code with an ID is only born together with its machine-validator (hook, eval, or agent); with no validator, write prose with a strong title in this section.

## Adding New Codes

Default: new STANDARD guidance is born in `mobile:code-review-mobile` STANDARDS.md. Promotion to BLOCKER with a mechanical gate (hook) requires an explicit decision — only when the code captures a bug, leak, correctness, or security issue.

---

## Observer and Deferred Builders

`Observer` (flutter_mobx) only tracks observables read **synchronously inside its own `builder`**. Reads inside a nested deferred builder — `ListenableBuilder`, `Builder`, `LayoutBuilder`, `AnimatedBuilder`, `FutureBuilder`, `ValueListenableBuilder`, `StreamBuilder` — are not tracked: that closure runs outside the Observer's `reaction.track()`.

**Symptom**: the widget only reacts to what's read directly in the Observer's builder; state that changes later (e.g., asynchronously) doesn't trigger a rebuild.

**Fix**: invert the nesting — the deferred builder on the outside, the `Observer` on the inside wrapping the subtree. This is more robust than hoisting each read manually into the Observer's builder, because it doesn't depend on remembering to do so for every new read introduced later.
