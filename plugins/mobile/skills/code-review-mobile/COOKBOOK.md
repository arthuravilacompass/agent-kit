# Flutter Cookbook — Patterns and Examples

> **Reference, not enforcement.** These patterns are good-practice examples — not rules with review weight. For rules with weight (BLOCKER/STANDARD/ASPIRATIONAL), see `mobile:mobx` `REFERENCE.md` (on-demand BLOCKER + tier policy) and `STANDARDS.md` (this skill).

## Project Config

The examples assume `get_it` + `injectable` (DI), `go_router` (navigation), `mockito` (mocks), `dartz` `Either` (errors). If your project uses a different stack, adapt the example — the structure (where the decision is made, what's tested) is what's worth porting. Design system component names (`AppHeader`, `AppCta` below) are placeholders — swap in your project's.

## Index

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
- [Layering check (arch_violations)](#layering-check-arch_violations)

---

## Dependency Injection

Stack: `get_it` + `injectable` (with codegen). Central registration in the project's DI module (e.g., `lib/core/di/service_locator.dart`).

### When to Use Each Annotation

| Annotation | Behavior | Use for |
|---|---|---|
| `@injectable` | New instance on every `get<T>()` | Stateless use cases, factories |
| `@singleton` | One instance created at app startup | Services that need to be ready immediately (logger, analytics) |
| `@lazySingleton` | One instance created on first call | **Preferred default** — Stores, Coordinators, Repositories |
| `@Injectable(as: IInterface)` | Registers the implementation under the interface type | Repositories with an abstract interface |

### Example — Repository With Interface

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

### After Changing Annotations

```bash
dart run build_runner build --delete-conflicting-outputs
```

> **Related rules:** `mobile:mobx` DI001 (no `GetIt.I` in a store), "Store isn't created in build()".

---

## Navigation

Stack: `go_router`. Routes defined in a central router file (project config). Path constants in a routes file (project config).

### Route Definition

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

### Navigation

```dart
// PUSH onto the stack — user can go back
context.push(AppRoutes.checkoutDelivery);

// REPLACE current — no back button
context.go(AppRoutes.home);

// With a path parameter
context.push('${AppRoutes.productDetailsBase}/$productId');
```

**Don't use:**
- Direct `Navigator.push` (loses auth/analytics middleware, if any)
- `Navigator.of(context).pushReplacement` (use `context.go`)

> **Related rule:** `mobile:mobx` ARCH001 — navigation NEVER inside a Store. Use `@observable pendingNavigation` + `reaction` on the Page.

---

## Testing — Mocks

Stack: `mockito` + `@GenerateMocks` annotation + codegen.

### Generating Mocks

```dart
// test file — declare mocks at the top
import 'package:mockito/annotations.dart';
import 'basket_store_test.mocks.dart'; // generated

@GenerateMocks([BasketRepository, CatalogStore])
void main() {
  // ...
}
```

After adding/changing:
```bash
dart run build_runner build --delete-conflicting-outputs
```

Mocks live in a `<test_name>.mocks.dart` file next to the test.

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

**Notes:**
- `Right(value)` = success, `Left(failure)` = error (dartz `Either`)
- Reset state in `setUp()` — never share between tests
- Assertions check the **final observable state** (not exceptions)

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

**Notes:**
- Pages should accept an optional store via constructor (`BasketPage.withStore(...)`) to ease test injection
- In production code, resolve the dependency in the default constructor (not in `build()` — breaks DI001/equivalent)
- Prefer shimmer/skeleton over a spinner where your team's convention says so (project config)

---

## Testing — Naming & Coverage

### Naming Convention

BDD-style structure with 3 levels:

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
# Run with coverage
flutter test --coverage

# Generate HTML report
genhtml coverage/lcov.info -o coverage/html && open coverage/html/index.html
```

### Common Pitfalls

- ❌ **Don't test private methods** — test through the public interface
- ❌ **Don't use `sleep()`** — use `tester.pumpAndSettle()` (animations) or `tester.pump(Duration(...))` (timers)
- ❌ **Don't share state between tests** — reset in `setUp()`
- ❌ **Don't forget to regenerate mocks** after changing `@GenerateMocks` — `dart run build_runner build`
- ❌ **Don't forget `tester.pump()`** after triggering a state change in a widget test
- ✅ For tests involving a `Future`, use `await tester.pump()` or `await tester.pumpAndSettle()`
- ✅ To test reactions/observers, trigger the change via the store and check the updated subtree

---

## Layering check (arch_violations)

Report-only — never fails a build. `arch_violations.py` reads a Lakos import graph (`.dot`) and reports layering-direction violations against a config **your project supplies**; it has no folder structure of its own baked in, so every consuming project defines its own layers.

### 1. Generate the import graph

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/arch_graph.sh" [project-root]
```

This runs `dart run lakos -m lib`, writes `build/arch.dot`, and (if `ARCHITECTURE.md` already has an `<!-- arch-graph:start -->…<!-- arch-graph:end -->` block) regenerates that data block in place — it never touches the surrounding prose. If your project doesn't have that doc yet, run `dart run lakos -m lib > build/arch.dot` directly and skip the doc part.

### 2. Write `arch-graph.config.json` (project root)

No rule is hardcoded — copy this 4-rule example from the script's own module docstring and adapt the `match`/`module_pattern` values to your project's real folder names:

```json
{
  "layers": [
    {"name": "core",   "match": "/lib/core/"},
    {"name": "shared", "match": "/lib/shared/"},
    {"name": "l10n",   "match": "/lib/l10n/", "exclude": true}
  ],
  "module_pattern": "/lib/modules/([^/]+)/",
  "module_exceptions": ["<module name exempt from the module-to-module rule>"],
  "composition_root_patterns": ["di_module", "app_router"],
  "direction_rules": [
    {"label": "core -> shared",   "from": "core",   "to": "shared"},
    {"label": "core -> modules",  "from": "core",   "to": "module:*"},
    {"label": "shared -> modules","from": "shared", "to": "module:*"},
    {"label": "module -> module", "from": "module:*", "to": "module:*", "cross_only": true}
  ]
}
```

### 3. Run the check

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/arch_violations.py" build/arch.dot --config arch-graph.config.json
```

Prints violation counts (and whether the import graph is acyclic) to stdout for a human/reviewer to act on — it does not fail the build. Without `--config` it looks for `arch-graph.config.json` next to `build/`'s parent (project root) and, if missing, prints setup instructions to stderr and exits 1 — that's a setup gap, not a graph problem.

---

## Either Pattern

Repositories return `Either<Failure, T>` (dartz). The caller uses `fold` to explicitly handle success vs. failure.

### Repository

```dart
Future<Either<Failure, List<OrderEntity>>> getOrders() async {
  try {
    final result = await _sdk.getOrders();
    return Right(result.map((e) => OrderEntity.fromDTO(e)).toList());
  } catch (error, stack) {
    log('Error fetching orders: $error', name: 'OrderRepository', error: error, stackTrace: stack);
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

**Notes:**
- `try/catch` ALWAYS in the repository — the controller only does `fold`
- Raw exceptions are mapped to `Failure` before reaching the UI
- A pagination error doesn't destroy the loaded list — differentiate an initial error from a next-page error

> **Related rules:** ARCH001 (no navigation in the store), "action mutates error state" (`mobile:code-review-mobile` STANDARDS.md), MOBX005 (runInAction after await).

---

## Security Checklist

### Storage

- [ ] Sensitive data (tokens, credentials) in secure/encrypted storage — never unencrypted preferences
- [ ] No secrets in source code or hardcoded

### API Keys

- [ ] API keys via `--dart-define-from-file` (or equivalent) — never hardcoded in Dart
- [ ] Env file in `.gitignore`
- [ ] Backend proxy for truly secret keys

### Input

- [ ] User input validated before sending to the API
- [ ] Deep link URLs validated and sanitized before navigation
- [ ] No direct interpolation of user input into queries

### Network

- [ ] HTTPS mandatory for every API call
- [ ] Auth tokens with proper refresh and expiration
- [ ] No sensitive data in logs (`log()` must not print tokens, passwords, PII)

---

## Page Template

Pages use `StatefulWidget` when they need a lifecycle (text controllers, scroll controllers, focus nodes), or `StatelessWidget` for simple read-only screens.

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
      appBar: AppHeader(title: 'Page Title'),  // placeholder — your design system's component
      body: SingleChildScrollView(
        controller: _scrollController,
        child: Column(
          children: [
            _buildSection1(context),
            _buildSection2(context),
          ],
        ),
      ),
      bottomNavigationBar: AppCta.onlyButton(   // placeholder — your design system's component
        buttonLabel: 'Continue',
        onPressed: () {},
      ),
    );
  }

  Widget _buildSection1(BuildContext context) => /* ... */;
  Widget _buildSection2(BuildContext context) => /* ... */;
}
```

**Widget extraction rules:**
- 15-50 line subtree, used once → private method `_buildSectionX`
- 50+ line subtree or needs its own state → private widget class
- Reused across pages in the module → public widget in `widgets/`
- Reused across modules → move to the shared design-system package (project config)

---

## Widget Patterns

### Required vs Optional Props

```dart
class MyWidget extends StatelessWidget {
  // Required — always needed for the widget to work
  final String title;
  final VoidCallback onPressed;

  // Optional — has a sensible default or can be absent
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

- `VoidCallback` — callback with no argument
- `ValueChanged<T>` — callback with 1 argument
- Custom `typedef` — complex signatures
- Naming: `on` prefix (`onPressed`, `onItemSelected`, `onDismissed`)

## See Also

- `mobile:mobx` `REFERENCE.md` — enforced MobX and DI rules
- `mobile:code-review-mobile` `STANDARDS.md` — on-demand STANDARD codes
- `mobile:refactor-review` — 2-phase refactor protocol
