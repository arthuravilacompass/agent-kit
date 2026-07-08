# Flutter Component / Module Structure

Reference for naming conventions, folder structure, barrel files, widget composition rules, and import organization in a modular Flutter app.

## Project Config

The folder table and the "modal bottom sheets vs. routes" list below are common conventions — swap in your project's real module/screen names. What doesn't change between projects: barrel files, widget extraction rules, import order.

## Feature Module Folder Structure

```
lib/src/modules/{module_name}/
├── controller/          # Screen-specific MobX controllers
│   ├── {module}_controller.dart
│   └── index.dart
├── entities/            # Domain models (immutable, plain Dart)
├── models/              # Data/serialization models (DTOs)
├── pages/               # UI pages (full screens)
├── repositories/        # Data access (API calls, local storage)
├── routes/              # GoRouter route definitions
│   ├── {module}_routes.dart      # Path constants
│   └── {module}_route.dart       # Route configuration
├── stores/              # Shared MobX observable state
├── widgets/             # Module-specific UI components
└── index.dart           # Module barrel file
```

Not every module needs every folder. Include only what's used. Prefer a **flat** module structure — entities, stores, and pages directly under the module (no DDD nesting) — unless the codebase already uses a DDD-influenced layout (`infra/`, `domain/`, `presenter/`); follow the existing pattern in the module you're editing rather than mixing conventions inside one module.

## Naming Conventions

| Element | Convention | Pattern | Example |
|---|---|---|---|
| Files | `snake_case` | `{name}_{type}.dart` | `basket_store.dart` |
| Classes | `PascalCase` | `{Name}{Type}` | `BasketStore` |
| Stores | `*Store` | `{Domain}Store` | `BasketStore`, `CatalogStore` |
| Controllers | `*Controller` | `{Screen}Controller` | `ProductListController` |
| Entities | `*Entity` | `{Name}Entity` | `ProductEntity`, `BasketItemEntity` |
| Models/DTOs | `*Model` or `*DTO` | `{Name}Model` | `ProductModel` |
| Enums | `PascalCase` | `{Name}Status`/`{Name}Type` | `BasketStatus`, `PaymentType` |
| Extensions | `*Ext` | `{Type}Ext` | `DoubleExt`, `StringExt` |
| Helpers | `*Helper` | `{Domain}Helper` | `ShippingHelper` |
| Mappers | `*Mapper` | `{Domain}Mapper` | `SummaryMapper` |
| Repositories | `*Repository` | `{Module}Repository` | `ProductRepository` |
| Pages | `*Page` | `{Screen}Page` | `OrderConfirmationPage` |
| Widgets | `*Widget` or descriptive | `{Name}Widget` | `ProductCardWidget` |
| Routes file | `*_routes.dart` | `{module}_routes.dart` | `sales_routes.dart` |
| Route config | `*_route.dart` | `{module}_route.dart` | `sales_route.dart` |

### Conversion Pattern (DTO ↔ Entity)

- DTO → Entity: `Entity.fromMap(dto)`, `Entity.fromDTO(dto)`, or `Entity.fromSDK(dto)`
- Entity → DTO: `.toDTO` getter or `.toMap()` method

## Barrel Files

Every folder with public Dart files **must** have an `index.dart` barrel file.

```dart
// stores/index.dart
export 'basket_store.dart';
export 'catalog_store.dart';
```

Rules:
- Export only public API files
- Do NOT export `.g.dart` or `.freezed.dart` files
- Do NOT export private/internal files
- Keep alphabetically sorted
- Module root `index.dart` exports sub-folder barrels

## Widget Composition Rules

### Widget Extraction Rules

- Extract to a **private method** (`_buildSectionX`) if the subtree is 15–50 lines and used once
- Extract to a **private widget class** if the subtree is 50+ lines or needs its own state/Observer
- Extract to a **public widget** (in `widgets/`) if reused across pages in the module
- Extract to a **shared component package** (config: your project's shared/design-system package, if any) if reused across modules

### Modal Bottom Sheets (Imperative)

Some screens are modal bottom sheets — **not** router destinations (config: which screens in your project use this pattern, e.g. product detail, cart, filters):

```dart
void _showDetail(BuildContext context, ProductEntity product) {
  showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    builder: (_) => MyModalWrapper(
      child: ProductDetailContent(product: product),
    ),
  );
}
```

### Observer Pattern (MobX)

Observer granularity and rebuild patterns: see `mobile:mobx` `REFERENCE.md` §MOBX001-006 + `mobile:performance-patterns`.

## Prop Patterns

Conventions for `required` vs default, `VoidCallback` vs `ValueChanged`, naming `on*`: see `COOKBOOK.md` §Widget Patterns.

## Import Organization

```dart
// 1. Dart SDK
import 'dart:async';

// 2. Flutter framework
import 'package:flutter/material.dart';

// 3. Third-party packages (alphabetical)
import 'package:flutter_mobx/flutter_mobx.dart';
import 'package:go_router/go_router.dart';

// 4. Project shared/SDK packages (config: your project's internal package names)
import 'package:my_design_system/my_design_system.dart';
import 'package:my_repositories/core/di/service_locator.dart';

// 5. App package imports (prefer relative for same module)
import 'package:my_app/src/core/router/app_routes.dart';

// 6. Relative imports (same module)
import '../stores/basket_store.dart';
import '../widgets/widgets.dart';
```

## Formatting

- **Line length**: config (common default: 120 characters — `dart format --line-length 120`)
- **Trailing commas**: Always on the last argument of multi-line function calls/constructors
- **Const**: Use `const` constructors and `const` literals wherever possible
