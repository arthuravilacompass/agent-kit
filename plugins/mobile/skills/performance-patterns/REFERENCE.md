# Performance Patterns — Reference

> Regras de MobX (rebuild em `Observer` inteiro, `@computed` puro, disposers de reaction) estão em `mobile:mobx` `REFERENCE.md`.

## MobX Rebuild Optimization

### Granular Observers

Quebrar `Observer` grandes em vários menores, cada um observando só o que precisa.

```dart
// BAD — tela inteira rebuilda quando qualquer observable muda
Observer(
  builder: (_) => Column(
    children: [
      HeaderSection(title: store.title),
      ItemList(items: store.items),
      SummarySection(total: store.totalPrice),
    ],
  ),
)

// GOOD — cada seção rebuilda independente
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
      const SectionTitle(text: 'Cart'),  // const — não recriado
      Text(store.itemCount.toString()),
      const Divider(),
    ],
  ),
)
```

### Use @computed for Derived Values

```dart
// BAD — recalculado a cada build
Observer(builder: (_) => Text(store.items.where((i) => i.isAvailable).length.toString()))

// GOOD — cached, recalcula só quando items muda
@computed
int get availableCount => _items.where((i) => i.isAvailable).length;

Observer(builder: (_) => Text(store.availableCount.toString()))
```

### Batch Observable Updates

```dart
// BAD — dispara 3 rebuilds separados
_state = MyState.success;
_data = result;
_errorMessage = null;

// GOOD — dispara 1 rebuild
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
// BAD — constrói todos os children imediatamente
ListView(children: items.map((item) => ProductCard(item: item)).toList())

// GOOD — constrói só os children visíveis
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

`Opacity` força saveLayer a cada frame mesmo estático.

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

Forçam um layout pass extra. Use apenas quando não houver alternativa via `Expanded`/`Flexible`/aspect ratio.

### MediaQuery.sizeOf over MediaQuery.of(context).size

```dart
// BAD — rebuild quando teclado abre/fecha
final size = MediaQuery.of(context).size;

// GOOD — rebuild apenas quando size muda
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
// BAD — sequencial, total time = t1 + t2
final products = await _repository.fetchProducts();
final categories = await _repository.fetchCategories();

// GOOD — paralelo, total time = max(t1, t2)
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

`NetworkImageWidget` é um placeholder — troque pelo widget de imagem do seu projeto (com suporte a dimensões explícitas).

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

Default no iOS e Android. Jank de compilação de shader eliminado. Nenhuma ação necessária — considere só durante profiling.

---

## RUM (ferramenta de Real User Monitoring do projeto)

Setup vive na camada de observabilidade do app (config do projeto). Um observer de navegação (config do projeto: nome real, ex. um `NavigatorObserver` custom) costuma reportar mudanças de rota automaticamente pra ferramenta de RUM escolhida (Datadog, Firebase Performance, Sentry, etc.).

---

## Performance Checklist

- [ ] Cada seção reativa tem seu próprio `Observer` (não envolvendo a tela inteira)
- [ ] Filhos estáticos dentro de `Observer` são `const`
- [ ] Valores derivados usam `@computed`, não computação inline em `build()`
- [ ] Múltiplos updates de observable após `await` usam `runInAction()`
- [ ] Todas as reactions MobX têm disposer correspondente
- [ ] Listas longas usam `ListView.builder`
- [ ] Widget de imagem tem width/height explícitos
- [ ] Chamadas de API independentes usam `Future.wait()`
- [ ] `CancelToken` usado em requests Dio dentro de controllers descartáveis
- [ ] `TextEditingController`/`ScrollController` descartados em `State.dispose()`
- [ ] Sem computação pesada em `build()`
- [ ] Widgets usam construtores `const` onde possível
- [ ] `RepaintBoundary` em subtrees caras que repintam independentemente
