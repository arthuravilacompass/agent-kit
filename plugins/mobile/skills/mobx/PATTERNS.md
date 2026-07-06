# MobX Aspirational Patterns — Reference

> Padrões sofisticados que valem **como norte**, não como gate. Aplique em código novo onde fizer sentido. **Não obrigam refactor de código existente.** Em PRs de bugfix, são `non-blocker`.

Companion to `REFERENCE.md` (BLOCKER + STANDARD tiers). Use `RECIPES.md` para receitas de migração quando um smell já foi detectado.

## Quando aplicar

- Stores ou controllers novos tocando flow state, async results, ou multi-observable composition.
- PRs introduzindo novos `@observable` fields ou `@action` methods com async.
- Code review flagging estes codes: FSM001, SSOT001, CMD001, MOBX006.
- Nunca bloqueia PRs de bugfix — são `non-blocker`.

---

### FSM001 — Estado de fluxo como sealed class — sem flags compostos

> enforced-by: agente `mobile:mobx-smell-hunter`

**Sinal**: 3+ `@observable` fields como `*State`, `*Mode`, `is*`, `has*`, `_pending*` que se influenciam mutuamente.

```dart
// ERRADO — 4 fields compondo um único conceito de fluxo
@observable FlowMode _mode = FlowMode.list;
@observable SubState _subState = SubState.initial;
@observable bool _isEditingInput = false;
@observable bool _needsCompletion = false;

// CERTO — sealed class expressando estados mutuamente exclusivos
@observable FlowState _flowState = const FlowIdle();
FlowState get flowState => _flowState;

sealed class FlowState { const FlowState(); }
final class FlowIdle extends FlowState { const FlowIdle(); }
// FlowBrowsing, FlowEditing, FlowPendingCompletion seguem mesmo padrão
```

**Quando NÃO se aplica**: Observables que são dados independentes (lista, entidade, mensagem de erro).

---

### Ação falível retorna sealed result, não bool/void

**Sinal**: `@action` que retorna `Future<bool>` ou `Future<void>` para operações que podem falhar.

```dart
// ERRADO — bool como sinal de sucesso/falha
@action
Future<bool> submit() async {
  try { await _repository.save(_draft); return true; }
  catch (_) { return false; }
}

// CERTO — resultado tipado com sealed class
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

**Quando NÃO se aplica**: Fire-and-forget genuíno (analytics, logging).

---

### Store gerenciada por Coordinator é pura — I/O no Coordinator

**Sinal**: Store injetada por Coordinator que ainda tem `_repository` próprio.

```dart
// ERRADO — Store com _repository próprio enquanto gerenciada por Coordinator
abstract class _ItemStoreBase with Store {
  _ItemStoreBase(this._repository);
  final ItemRepository _repository;
  @action Future<void> loadItem(String id) async { /* I/O na store */ }
}

// CERTO — Store pura (estado + computed), I/O no Coordinator
abstract class _ItemStoreBase with Store {
  @observable ItemState _state = const ItemIdle();
  ItemState get state => _state;
  @action void applyItem(ItemEntity item) => _state = ItemLoaded(item);
  @action void applyLoading() => _state = const ItemLoading();
  @action void applyError(String msg) => _state = ItemError(msg);
}
// Coordinator chama _itemStore.applyLoading(), faz I/O, depois applyItem/applyError
```

**Quando NÃO se aplica**: Stores que operam de forma independente (sem Coordinator gerenciando seu ciclo de vida).

---

### CMD001 — Discriminador primitivo vira sealed Command

> enforced-by: agente `mobile:mobx-smell-hunter`

**Sinal**: `bool` ou `String` passado como parâmetro seleciona QUAL comportamento executar.

```dart
// ERRADO — discriminadores primitivos
Future<void> processFlow(String id, bool isNew, String mode) async {
  if (isNew) { await _create(id); }
  else if (mode == 'quick') { await _quickUpdate(id); }
  else { await _fullUpdate(id); }
}

// CERTO — intenção tipada, switch exhaustivo
Future<FlowResult> processFlow(FlowCommand command) async {
  return switch (command) {
    CreateItem(:final draft) => _create(draft),
    QuickUpdateItem(:final id) => _quickUpdate(id),
  };
}
sealed class FlowCommand { const FlowCommand(); }
final class CreateItem extends FlowCommand { final ItemDraft draft; const CreateItem(this.draft); }
```

**Quando NÃO se aplica**: Parâmetros que são dados de uma única operação (`loadItems(String query, int page)`).

---

### SSOT001 — Estado tipado escrito por um único writer privado

> enforced-by: agente `mobile:mobx-smell-hunter`

`sealed class` state atom exposed as `@readonly` MUST be written through a single private `_set*` action.

```dart
// ERRADO — múltiplos write sites diretos
@observable ShippingSelection _selection = _emptySelection;
_selection = _emptySelection;          // em resetOnExit
_selection = _selection.copyWith(...); // em _reconcileSelections
_selection = next;                     // em _applySelection

// CERTO — sealed class + @readonly + single writer
@readonly
DeliverySelection _delivery = const DeliveryNotSelected();

@action
void _setDelivery(DeliverySelection next) => _delivery = next;
// Todo write no arquivo passa por _setDelivery — auditável via grep.
```

---

### MOBX006 — Estado sintético de concorrência — absorva no enum ou use Future?

> enforced-by: agente `mobile:mobx-smell-hunter`

**Sinal**: enum `{ idle, inFlight }` cujo único propósito é impedir re-entrada, coexistindo com guards de staleness no mesmo arquivo.

```dart
// ERRADO — lock como @observable cria segunda fonte para isLoading
@observable _OpLock _lock = _OpLock.idle;
@computed bool get isLoading =>
    _state == DomainState.loading || _lock == _OpLock.inFlight;

// CERTO — absorver no enum de domínio
enum DomainState { idle, loading, operating, success, error }
@computed bool get isLoading =>
    _state == DomainState.loading || _state == DomainState.operating;

// CERTO — lock puramente mecânico como Future? não-observável
Future<Result>? _pending;
Future<Result> _operate() async {
  if (_pending != null) return _pending!;
  _pending = _doOperate();
  try { return await _pending!; } finally { _pending = null; }
}
```

**Quando NÃO se aplica**: Dois estados de loading genuinamente independentes que o usuário precisa distinguir na UI.
