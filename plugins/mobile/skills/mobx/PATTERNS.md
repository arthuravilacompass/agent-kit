# MobX Aspirational Patterns — Reference

> Sophisticated patterns that are worth **as a direction**, not as a gate. Apply in new code where it makes sense. **Do not force a refactor of existing code.** In bugfix PRs, they are `non-blocker`.

Companion to `REFERENCE.md` (BLOCKER + STANDARD tiers). Use `RECIPES.md` for migration recipes once a smell has already been detected.

## When to Apply

- New stores or controllers touching flow state, async results, or multi-observable composition.
- PRs introducing new `@observable` fields or async `@action` methods.
- Code review flagging these codes: FSM001, SSOT001, CMD001, MOBX006.
- Never blocks bugfix PRs — they are `non-blocker`.

---

### FSM001 — Flow State as a Sealed Class — No Compound Flags

> enforced-by: `mobile:mobx-smell-hunter` agent

**Signal**: 3+ `@observable` fields like `*State`, `*Mode`, `is*`, `has*`, `_pending*` that mutually influence each other.

```dart
// BAD — 4 fields composing a single flow concept
@observable FlowMode _mode = FlowMode.list;
@observable SubState _subState = SubState.initial;
@observable bool _isEditingInput = false;
@observable bool _needsCompletion = false;

// GOOD — sealed class expressing mutually exclusive states
@observable FlowState _flowState = const FlowIdle();
FlowState get flowState => _flowState;

sealed class FlowState { const FlowState(); }
final class FlowIdle extends FlowState { const FlowIdle(); }
// FlowBrowsing, FlowEditing, FlowPendingCompletion follow the same pattern
```

**When it does NOT apply**: Observables that are independent data (a list, an entity, an error message).

---

### A Fallible Action Returns a Sealed Result, Not bool/void

**Signal**: an `@action` that returns `Future<bool>` or `Future<void>` for operations that can fail.

```dart
// BAD — bool as a success/failure signal
@action
Future<bool> submit() async {
  try { await _repository.save(_draft); return true; }
  catch (_) { return false; }
}

// GOOD — typed result with a sealed class
@action
Future<SubmitResult> submit() async {
  try {
    final saved = await _repository.save(_draft);
    runInAction(() => _state = FlowState.success);
    return SubmitResult.success(saved);
  } catch (e) {
    runInAction(() => _state = FlowState.error);
    return SubmitResult.error(e.toString());
  }
}
sealed class SubmitResult { const SubmitResult(); }
final class SubmitSuccess extends SubmitResult { final SavedEntity entity; const SubmitSuccess(this.entity); }
```

**When it does NOT apply**: genuine fire-and-forget (analytics, logging).

---

### A Coordinator-Managed Store Is Pure — I/O Lives in the Coordinator

**Signal**: a store injected by a Coordinator that still has its own `_repository`.

```dart
// BAD — Store with its own _repository while managed by a Coordinator
abstract class _ItemStoreBase with Store {
  _ItemStoreBase(this._repository);
  final ItemRepository _repository;
  @action Future<void> loadItem(String id) async { /* I/O in the store */ }
}

// GOOD — Pure store (state + computed), I/O in the Coordinator
abstract class _ItemStoreBase with Store {
  @observable ItemState _state = const ItemIdle();
  ItemState get state => _state;
  @action void applyItem(ItemEntity item) => _state = ItemLoaded(item);
  @action void applyLoading() => _state = const ItemLoading();
  @action void applyError(String msg) => _state = ItemError(msg);
}
// Coordinator calls _itemStore.applyLoading(), does I/O, then applyItem/applyError
```

**When it does NOT apply**: Stores that operate independently (with no Coordinator managing their lifecycle).

---

### CMD001 — Primitive Discriminator Becomes a Sealed Command

> enforced-by: `mobile:mobx-smell-hunter` agent

**Signal**: a `bool` or `String` passed as a parameter selects WHICH behavior to run.

```dart
// BAD — primitive discriminators
Future<void> processFlow(String id, bool isNew, String mode) async {
  if (isNew) { await _create(id); }
  else if (mode == 'quick') { await _quickUpdate(id); }
  else { await _fullUpdate(id); }
}

// GOOD — typed intent, exhaustive switch
Future<FlowResult> processFlow(FlowCommand command) async {
  return switch (command) {
    CreateItem(:final draft) => _create(draft),
    QuickUpdateItem(:final id) => _quickUpdate(id),
  };
}
sealed class FlowCommand { const FlowCommand(); }
final class CreateItem extends FlowCommand { final ItemDraft draft; const CreateItem(this.draft); }
```

**When it does NOT apply**: Parameters that are data for a single operation (`loadItems(String query, int page)`).

---

### SSOT001 — Typed State Written by a Single Private Writer

> enforced-by: `mobile:mobx-smell-hunter` agent

A `sealed class` state atom exposed as `@readonly` MUST be written through a single private `_set*` action.

```dart
// BAD — multiple direct write sites
@observable VariantSelection _selection = _emptySelection;
_selection = _emptySelection;          // in resetOnExit
_selection = _selection.copyWith(...); // in _reconcileVariants
_selection = next;                     // in _applySelection

// GOOD — sealed class + @readonly + single writer
@readonly
SizeSelection _size = const SizeNotSelected();

@action
void _setSize(SizeSelection next) => _size = next;
// Every write in the file goes through _setSize — auditable via grep.
```

---

### MOBX006 — Synthetic Concurrency State — Absorb into the Enum or Use Future?

> enforced-by: `mobile:mobx-smell-hunter` agent

**Signal**: an `{ idle, inFlight }` enum whose sole purpose is preventing re-entry, coexisting with staleness guards in the same file.

```dart
// BAD — lock as @observable creates a second source of truth for isLoading
@observable _OpLock _lock = _OpLock.idle;
@computed bool get isLoading =>
    _state == DomainState.loading || _lock == _OpLock.inFlight;

// GOOD — absorb into the domain enum
enum DomainState { idle, loading, operating, success, error }
@computed bool get isLoading =>
    _state == DomainState.loading || _state == DomainState.operating;

// GOOD — purely mechanical lock as a non-observable Future?
Future<Result>? _pending;
Future<Result> _operate() async {
  if (_pending != null) return _pending!;
  _pending = _doOperate();
  try { return await _pending!; } finally { _pending = null; }
}
```

**When it does NOT apply**: Two genuinely independent loading states that the user needs to distinguish in the UI.
