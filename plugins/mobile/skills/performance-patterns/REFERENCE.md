# Performance Patterns — Reference

> MobX rules (rebuilding the whole `Observer`, pure `@computed`, reaction disposers) are in `mobile:mobx` `REFERENCE.md`.

## MobX Rebuild Optimization

### Granular Observers

Break large `Observer`s into several smaller ones, each observing only what it needs.

```dart
// BAD — the whole screen rebuilds when any observable changes
Observer(
  builder: (_) => Column(
    children: [
      HeaderSection(title: store.title),
      ItemList(items: store.items),
      SummarySection(total: store.totalPrice),
    ],
  ),
)

// GOOD — each section rebuilds independently
Column(
  children: [
    Observer(builder: (_) => HeaderSection(title: store.title)),
    Observer(builder: (_) => ItemList(items: store.items)),
    Observer(builder: (_) => SummarySection(total: store.totalPrice)),
  ],
)
```

### Const Children Inside Observer

```dart
Observer(
  builder: (_) => Column(
    children: [
      const SectionTitle(text: 'Cart'),  // const — not recreated
      Text(store.itemCount.toString()),
      const Divider(),
    ],
  ),
)
```

### Use @computed for Derived Values

```dart
// BAD — recalculated on every build
Observer(builder: (_) => Text(store.items.where((i) => i.isAvailable).length.toString()))

// GOOD — cached, only recalculates when items changes
@computed
int get availableCount => _items.where((i) => i.isAvailable).length;

Observer(builder: (_) => Text(store.availableCount.toString()))
```

### Batch Observable Updates

```dart
// BAD — fires 3 separate rebuilds
_state = MyState.success;
_data = result;
_errorMessage = null;

// GOOD — fires 1 rebuild
runInAction(() {
  _state = MyState.success;
  _data = result;
  _errorMessage = null;
});
```

---

## Widget Tree Optimization

### Const Constructors

```dart
class ProductBadge extends StatelessWidget {
  const ProductBadge({super.key, required this.label});
  final String label;
  @override
  Widget build(BuildContext context) => /* ... */;
}
```

### ListView.builder for Long Lists

```dart
// BAD — builds all children immediately
ListView(children: items.map((item) => ProductCard(item: item)).toList())

// GOOD — builds only the visible children
ListView.builder(
  itemCount: items.length,
  itemBuilder: (context, index) => ProductCard(item: items[index]),
)
```

### RepaintBoundary for Expensive Subtrees

```dart
RepaintBoundary(child: NetworkImageWidget(url: product.imageUrl, width: 200, height: 200))
```

### AnimatedOpacity over Opacity

`Opacity` forces a saveLayer every frame even when static.

```dart
// BAD
Opacity(opacity: _isVisible ? 1.0 : 0.0, child: heavySubtree)

// GOOD
AnimatedOpacity(
  opacity: _isVisible ? 1.0 : 0.0,
  duration: const Duration(milliseconds: 200),
  child: heavySubtree,
)
```

### IntrinsicHeight / IntrinsicWidth

Force an extra layout pass. Use only when there's no alternative via `Expanded`/`Flexible`/aspect ratio.

### MediaQuery.sizeOf over MediaQuery.of(context).size

```dart
// BAD — rebuilds when the keyboard opens/closes
final size = MediaQuery.of(context).size;

// GOOD — rebuilds only when size changes
final size = MediaQuery.sizeOf(context);
```

---

## Network Performance (Dio)

### Cancel Requests on Disposal

```dart
final CancelToken _cancelToken = CancelToken();

@action
Future<void> load() async {
  try {
    _data = await _repository.fetchData(cancelToken: _cancelToken);
  } on DioException catch (e) {
    if (e.type == DioExceptionType.cancel) return;
  }
}

@disposeMethod
void dispose() => _cancelToken.cancel('Controller disposed');
```

### Parallel API Calls

```dart
// BAD — sequential, total time = t1 + t2
final products = await _repository.fetchProducts();
final categories = await _repository.fetchCategories();

// GOOD — parallel, total time = max(t1, t2)
final results = await Future.wait([
  _repository.fetchProducts(),
  _repository.fetchCategories(),
]);
```

### Cache Store Results

```dart
@action
Future<void> load({bool forceRefresh = false}) async {
  if (_data != null && !forceRefresh) return;
  _state = MyState.loading;
  // ... fetch
}
```

---

## Image Performance

Always provide dimensions — enables CDN resize and prevents extra layout pass.

```dart
NetworkImageWidget(url: product.imageUrl, width: 120, height: 120, fit: BoxFit.cover)
```

`NetworkImageWidget` is a placeholder — swap in your project's image widget (with support for explicit dimensions).

---

## Memory Management

### Dispose MobX Reactions

```dart
late final ReactionDisposer _syncDisposer;
_syncDisposer = reaction((_) => _storeA.data, (_) => _sync());

@disposeMethod
void dispose() => _syncDisposer();
```

### Dispose Flutter Controllers

```dart
@override
void initState() {
  super.initState();
  _textController = TextEditingController();
  _scrollController = ScrollController();
}

@override
void dispose() {
  _textController.dispose();
  _scrollController.dispose();
  super.dispose();
}
```

---

## Impeller (Flutter ≥ 3.38)

Default on iOS and Android. Shader-compilation jank eliminated. No action needed — consider it only during profiling.

---

## RUM (Real User Monitoring Tool)

Setup lives in the app's observability layer (project config). A navigation observer (project config: real name, e.g. a custom `NavigatorObserver`) usually reports route changes automatically to whichever RUM tool is chosen (Datadog, Firebase Performance, Sentry, etc.).

---

## Performance Checklist

- [ ] Each reactive section has its own `Observer` (not wrapping the whole screen)
- [ ] Static children inside `Observer` are `const`
- [ ] Derived values use `@computed`, not inline computation in `build()`
- [ ] Multiple observable updates after `await` use `runInAction()`
- [ ] Every MobX reaction has a matching disposer
- [ ] Long lists use `ListView.builder`
- [ ] Image widgets have explicit width/height
- [ ] Independent API calls use `Future.wait()`
- [ ] `CancelToken` used on Dio requests inside disposable controllers
- [ ] `TextEditingController`/`ScrollController` disposed in `State.dispose()`
- [ ] No heavy computation in `build()`
- [ ] Widgets use `const` constructors where possible
- [ ] `RepaintBoundary` on expensive subtrees that repaint independently
