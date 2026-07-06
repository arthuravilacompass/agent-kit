# Flutter Cookbook — Padrões e Exemplos

> **Reference, not enforcement.** Esses padrões são exemplos de boas práticas — não regras com peso de review. Para regras com peso (BLOCKER/STANDARD/ASPIRATIONAL), consulte `mobile:mobx` `REFERENCE.md` (BLOCKER on-demand + tier policy) e `STANDARDS.md` (esta skill).

## Config do projeto

Os exemplos assumem `get_it` + `injectable` (DI), `go_router` (navegação), `mockito` (mocks), `dartz` `Either` (erros). Se seu projeto usa outro stack, adapte o exemplo — a estrutura (onde a decisão é tomada, o que é testado) é o que vale a pena portar. Nomes de componentes de design system (`AppHeader`, `AppCta` abaixo) são placeholders — troque pelos do seu projeto.

## Índice

- [Dependency Injection](#dependency-injection)
- [Navigation](#navigation)
- [Testing — Mocks](#testing--mocks)
- [Testing — Store Pattern](#testing--store-pattern)
- [Testing — Widget Pattern](#testing--widget-pattern)
- [Testing — Naming & Coverage](#testing--naming--coverage)
- [Either Pattern](#either-pattern)
- [Security Checklist](#security-checklist)
- [Page Template](#page-template)
- [Widget Patterns](#widget-patterns)

---

## Dependency Injection

Stack: `get_it` + `injectable` (com codegen). Registro central no módulo de DI do projeto (ex.: `lib/core/di/service_locator.dart`).

### Quando usar cada anotação

| Anotação | Comportamento | Use para |
|---|---|---|
| `@injectable` | Nova instância a cada `get<T>()` | Use cases stateless, factories |
| `@singleton` | Uma instância criada no startup do app | Services que precisam estar prontos imediatamente (logger, analytics) |
| `@lazySingleton` | Uma instância criada na primeira chamada | **Default preferido** — Stores, Coordinators, Repositories |
| `@Injectable(as: IInterface)` | Registra implementação sob tipo da interface | Repositories com interface abstrata |

### Exemplo — Repository com interface

```dart
// abstract interface
abstract class BasketRepository {
  Future<Either<Failure, BasketEntity>> getBasket();
}

// implementation registered as the interface type
@LazySingleton(as: BasketRepository)
class BasketRepositoryImpl implements BasketRepository {
  BasketRepositoryImpl(this._sdk);
  final AppApi _sdk;

  @override
  Future<Either<Failure, BasketEntity>> getBasket() async {
    // ...
  }
}
```

### Após mudar anotações

```bash
dart run build_runner build --delete-conflicting-outputs
```

> **Regras relacionadas:** `mobile:mobx` DI001 (no `GetIt.I` em store), "Store não nasce em build()".

---

## Navigation

Stack: `go_router`. Rotas definidas em um arquivo central de router (config do projeto). Constantes de path em um arquivo de rotas (config do projeto).

### Definição de rota

```dart
final appRouter = GoRouter(
  initialLocation: AppRoutes.home,
  routes: [
    GoRoute(
      path: AppRoutes.productDetails,  // '/product/:productId'
      builder: (context, state) {
        final productId = state.pathParameters['productId']!;
        return ProductDetailsPage(productId: productId);
      },
    ),
  ],
);
```

### Navegação

```dart
// PUSH na stack — usuário pode voltar
context.push(AppRoutes.checkoutDelivery);

// REPLACE current — sem botão voltar
context.go(AppRoutes.home);

// Com path parameter
context.push('${AppRoutes.productDetailsBase}/$productId');
```

**Não usar:**
- `Navigator.push` direto (perde middleware de auth/analytics, se houver)
- `Navigator.of(context).pushReplacement` (use `context.go`)

> **Regra relacionada:** `mobile:mobx` ARCH001 — navegação NUNCA dentro de Store. Use `@observable pendingNavigation` + `reaction` na Page.

---

## Testing — Mocks

Stack: `mockito` + `@GenerateMocks` annotation + codegen.

### Geração de mocks

```dart
// arquivo de teste — declarar mocks no topo
import 'package:mockito/annotations.dart';
import 'basket_store_test.mocks.dart'; // gerado

@GenerateMocks([BasketRepository, CatalogStore])
void main() {
  // ...
}
```

Após adicionar/mudar:
```bash
dart run build_runner build --delete-conflicting-outputs
```

Mocks ficam em arquivo `<nome_test>.mocks.dart` ao lado do teste.

---

## Testing — Store Pattern

```dart
import 'package:dartz/dartz.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';

import 'basket_store_test.mocks.dart';

@GenerateMocks([BasketRepository])
void main() {
  late BasketStore store;
  late MockBasketRepository mockRepository;

  setUp(() {
    mockRepository = MockBasketRepository();
    store = BasketStore(mockRepository);
  });

  group('BasketStore', () {
    group('loadBasket', () {
      test('should populate items when repository succeeds', () async {
        // Arrange
        final mockBasket = BasketEntity(items: const [], total: 0);
        when(mockRepository.getBasket())
            .thenAnswer((_) async => Right(mockBasket));

        // Act
        await store.loadBasket();

        // Assert
        expect(store.basket, equals(mockBasket));
        expect(store.state, equals(BasketState.success));
        expect(store.errorMessage, isNull);
      });

      test('should set error state when repository fails', () async {
        // Arrange
        when(mockRepository.getBasket())
            .thenAnswer((_) async => const Left(NetworkFailure('timeout')));

        // Act
        await store.loadBasket();

        // Assert
        expect(store.state, equals(BasketState.error));
        expect(store.errorMessage, equals('timeout'));
      });
    });
  });
}
```

**Notas:**
- `Right(value)` = sucesso, `Left(failure)` = erro (dartz `Either`)
- Reset state em `setUp()` — nunca compartilhar entre testes
- Asserções verificam o **estado observável final** (não exceções)

---

## Testing — Widget Pattern

```dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:flutter_mobx/flutter_mobx.dart';

void main() {
  late MockBasketStore mockStore;

  setUp(() {
    mockStore = MockBasketStore();
  });

  testWidgets('shows items when basket has data', (tester) async {
    // Arrange
    when(mockStore.state).thenReturn(BasketState.success);
    when(mockStore.items).thenReturn([
      BasketItemEntity(id: '1', name: 'Running Shoe', price: 299),
    ]);

    // Act
    await tester.pumpWidget(
      MaterialApp(
        home: BasketPage.withStore(store: mockStore),
      ),
    );

    // Assert
    expect(find.text('Running Shoe'), findsOneWidget);
  });

  testWidgets('shows skeleton when state is loading', (tester) async {
    when(mockStore.state).thenReturn(BasketState.loading);

    await tester.pumpWidget(
      MaterialApp(home: BasketPage.withStore(store: mockStore)),
    );

    expect(find.byType(BasketSkeleton), findsOneWidget);
  });
}
```

**Notas:**
- Pages devem aceitar store opcional via construtor (`BasketPage.withStore(...)`) para facilitar test injection
- Em código de produção, resolva a dependência no construtor padrão (não em `build()` — quebra DI001/equivalente)
- Prefira shimmer/skeleton a spinner onde a convenção do time definir isso (config do projeto)

---

## Testing — Naming & Coverage

### Naming convention

Estrutura BDD-style com 3 níveis:

```dart
group('ClassName', () {
  group('methodName', () {
    test('should [expected behavior] when [condition]', () {
      // Arrange
      // Act
      // Assert
    });
  });
});
```

### Coverage

```bash
# Rodar com coverage
flutter test --coverage

# Gerar HTML report
genhtml coverage/lcov.info -o coverage/html && open coverage/html/index.html
```

### Common Pitfalls

- ❌ **Não testar métodos privados** — teste através da interface pública
- ❌ **Não usar `sleep()`** — use `tester.pumpAndSettle()` (animações) ou `tester.pump(Duration(...))` (timers)
- ❌ **Não compartilhar estado entre testes** — reset em `setUp()`
- ❌ **Não esquecer de regenerar mocks** após mudar `@GenerateMocks` — `dart run build_runner build`
- ❌ **Não esquecer `tester.pump()`** após trigger de state change em widget test
- ✅ Para testes que envolvem `Future`, use `await tester.pump()` ou `await tester.pumpAndSettle()`
- ✅ Para testar reactions/observers, dispare a mudança via store e verifique o subtree atualizado

---

## Either Pattern

Repositories retornam `Either<Failure, T>` (dartz). Caller usa `fold` para tratar success vs failure explicitamente.

### Repository

```dart
Future<Either<Failure, List<OrderEntity>>> getOrders() async {
  try {
    final result = await _sdk.getOrders();
    return Right(result.map((e) => OrderEntity.fromDTO(e)).toList());
  } catch (error, stack) {
    log('Erro ao buscar orders: $error', name: 'OrderRepository', error: error, stackTrace: stack);
    return Left(Failure(error.toString()));
  }
}
```

### Controller / Store

```dart
@action
Future<void> loadOrders() async {
  _state = OrderState.loading;
  final result = await _repository.getOrders();
  runInAction(() {
    result.fold(
      (failure) {
        _errorMessage = failure.message;
        _state = OrderState.error;
      },
      (orders) {
        _orders = ObservableList.of(orders);
        _state = OrderState.success;
      },
    );
  });
}
```

**Notas:**
- `try/catch` SEMPRE no repository — controller só faz `fold`
- Exceções cruas mapeadas para `Failure` antes de chegar na UI
- Erro de paginação não destrói lista carregada — diferenciar erro inicial vs erro de próxima página

> **Regras relacionadas:** ARCH001 (sem navegação no store), "action muta estado de erro" (`mobile:code-review-mobile` STANDARDS.md), MOBX005 (runInAction após await).

---

## Security Checklist

### Storage

- [ ] Dados sensíveis (tokens, credenciais) em storage seguro/encriptado — nunca preferências não-encriptadas
- [ ] Sem secrets em código fonte ou hardcoded

### API Keys

- [ ] API keys via `--dart-define-from-file` (ou equivalente) — nunca hardcoded em Dart
- [ ] Arquivo de env no `.gitignore`
- [ ] Backend proxy para chaves verdadeiramente secretas

### Input

- [ ] Input do usuário validado antes de enviar para API
- [ ] Deep link URLs validadas e sanitizadas antes de navegação
- [ ] Sem interpolação direta de input do usuário em queries

### Network

- [ ] HTTPS obrigatório para todas as chamadas API
- [ ] Tokens de autenticação com refresh e expiração adequados
- [ ] Sem dados sensíveis em logs (`log()` não deve imprimir tokens, senhas, PII)

---

## Page Template

Pages usam `StatefulWidget` quando precisam de lifecycle (text controllers, scroll controllers, focus nodes), ou `StatelessWidget` para telas read-only simples.

```dart
class MyFeaturePage extends StatefulWidget {
  const MyFeaturePage({super.key});

  @override
  State<MyFeaturePage> createState() => _MyFeaturePageState();
}

class _MyFeaturePageState extends State<MyFeaturePage> {
  final _scrollController = ScrollController();
  late final MyController _controller;

  @override
  void initState() {
    super.initState();
    _controller = dependencies.get<MyController>();
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppHeader(title: 'Page Title'),  // placeholder — componente do seu design system
      body: SingleChildScrollView(
        controller: _scrollController,
        child: Column(
          children: [
            _buildSection1(context),
            _buildSection2(context),
          ],
        ),
      ),
      bottomNavigationBar: AppCta.onlyButton(   // placeholder — componente do seu design system
        buttonLabel: 'Continue',
        onPressed: () {},
      ),
    );
  }

  Widget _buildSection1(BuildContext context) => /* ... */;
  Widget _buildSection2(BuildContext context) => /* ... */;
}
```

**Regras de extração de widget:**
- Subtree 15-50 linhas, usado uma vez → método privado `_buildSectionX`
- Subtree 50+ linhas ou precisa estado próprio → classe widget privada
- Reutilizado em pages do módulo → widget público em `widgets/`
- Reutilizado entre módulos → mover para o pacote de design system compartilhado (config do projeto)

---

## Widget Patterns

### Required vs Optional Props

```dart
class MyWidget extends StatelessWidget {
  // Required — sempre necessário para o widget funcionar
  final String title;
  final VoidCallback onPressed;

  // Optional — tem default sensato ou pode estar ausente
  final String? subtitle;
  final bool isEnabled;

  const MyWidget({
    required this.title,
    required this.onPressed,
    this.subtitle,
    this.isEnabled = true,
    super.key,
  });
}
```

### Callbacks

- `VoidCallback` — callback sem argumento
- `ValueChanged<T>` — callback com 1 argumento
- `typedef` próprio — assinaturas complexas
- Naming: prefixo `on` (`onPressed`, `onItemSelected`, `onDismissed`)

## Ver também

- `mobile:mobx` `REFERENCE.md` — regras enforce de MobX e DI
- `mobile:code-review-mobile` `STANDARDS.md` — STANDARD codes on-demand
- `mobile:refactor-review` — protocolo de 2 fases para refactor
