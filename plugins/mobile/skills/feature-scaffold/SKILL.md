---
name: feature-scaffold
description: Invoke to scaffold a new Flutter feature — page, MobX store/controller, repository, entity — following the project's layered pattern (UI → State → Domain → Data). Triggers — "create a new feature", "scaffold <name>", "generate store+repository+page for this".
---

# Feature Scaffold — Scaffold Flutter Feature

Generates a complete Flutter feature following the layered pattern: page, MobX store/controller, repository, entity.

## Project Config

The templates assume `get_it`/`injectable` (DI), MobX (state), `dartz` `Either` (errors), and a `lib/src/modules/<module>/` folder. If your project uses a different state/DI/error stack, adapt the templates before use — the 4-file structure (entity/repository/controller/page) and the step order below still hold.

## Usage

Ask the user (if not provided in the message):
- **Feature name** (snake_case, e.g. `race_results`).
- **File subset** to generate: `entity`, `repository`, `controller`, `page` (default: all four). E.g. only `entity,repository` if the UI layer already exists; only `controller,page` if entity/repository already exist.

## Templates

Source of truth in `templates/`:

| Template | Generated Path | Role |
|---|---|---|
| `entity.dart.template` | `entities/{{feature_name}}_entity.dart` | Immutable domain entity. `extends Equatable`, `final` fields, `const` constructor, `fromDTO(...)` factory, `copyWith`, `props => [id]`. Identity by `id`. |
| `repository.dart.template` | `repository/{{feature_name}}_repository.dart` | Data layer. `@lazySingleton`, `final class`. `getAll()` stub throws `UnimplementedError` until the real endpoint is wired up. |
| `controller.dart.template` | `controller/{{feature_name}}_controller.dart` | State layer. `@injectable`, MobX `Store` mixin via `part '*.g.dart'`. `{{FeatureName}}State { initial, loading, success, error }` enum. Private observables (`_state`/`items`/`errorMessage`) with getters/computed; `@action load()` that wraps post-await mutations in `runInAction`. |
| `page.dart.template` | `pages/{{feature_name}}_page.dart` | UI layer. `StatefulWidget` resolving the controller in `initState()`. `Observer` switches on the `state` enum: loading → spinner, error → message, success → `ListView.builder`. |

Placeholders in every template:
- `{{FeatureName}}` — PascalCase (e.g. `RaceResults`).
- `{{feature_name}}` — snake_case (e.g. `race_results`).

Critical annotations preserved by the templates: `@lazySingleton`/`@injectable` (DI), `@observable`/`@computed`/`@action` (controller fields and methods), `part '*_controller.g.dart'`. Removing any of these silently breaks DI or codegen.

## Steps

1. **Feature name** — snake_case. If missing, ask.

2. **Parse the file subset** — validate against `{entity, repository, controller, page}`. Reject unknown entries. Default: all four.

3. **Confirm scope** — ask:
   - "Which module does this feature belong to?" (the name becomes the `<module>` path segment)
   - "Is it a screen-specific controller (`@injectable`) or a shared domain store (`@lazySingleton`/`@singleton`)?"
   - "What's the main data entity?"
   - "Does the API return a list, a single object, or perform a mutation (create/update/delete)?"

   Wait for the answers before generating.

4. **Design reference (if any)** — if the user has a visual reference (Figma or equivalent), ask whether to run your setup's design-to-code tool before filling in the UI. Without a reference: confirm "scaffold with no visual reference — placeholder layout" and proceed.

5. **Compute placeholders** — `{{feature_name}}` = the snake_case argument; `{{FeatureName}}` = PascalCase derivation (split on `_`, capitalize each segment).

6. **Generate files** — for each name in the resolved subset:
   1. Read `templates/{name}.dart.template`.
   2. Replace every occurrence of `{{FeatureName}}` and `{{feature_name}}`.
   3. Write to `lib/src/modules/<module>/{{feature_name}}/<layer>/{{feature_name}}_<name>.dart` (`<layer>` per the table above).
   4. Don't silently overwrite an existing file — if the target already exists, confirm with the user.

   Per-file notes:
   - **entity**: the corresponding DTO type needs to exist in the project's data SDK/package — check the real type and adjust the import/mapping.
   - **repository**: wire the real endpoint, replacing the `UnimplementedError` stub.
   - **controller**: swap `@injectable` for `@lazySingleton`/`@singleton` if the state needs to persist across screens. Store vs. Controller: singleton for shared domain state (cart, user); injectable for screen-specific state (filters, search, list pagination).
   - **page**: swap `CircularProgressIndicator()` for your design system's loading pattern (spinner vs. shimmer/skeleton — project convention).

7. **Register DI** — remind the user to run codegen:
   ```bash
   dart run build_runner build --delete-conflicting-outputs
   ```

8. **Register the route** — remind them to add the route entry in the project's router (`go_router` or equivalent).
   - go_router gotcha: in `redirect`, `return null` means "proceed to the requested location", not "cancel/stay put". If the location matches no route, it falls to `errorBuilder`. To *ignore* a path, return an explicit route — not `null`.

9. **Summary** — list only the files actually generated (respecting the subset) + follow-ups:
   - Wire the real DTO/endpoint.
   - Replace the placeholder UI with the project's design-system components + tokens.
   - Run `dart run build_runner build --delete-conflicting-outputs`.
   - Run `flutter analyze`.

## Important

- Never resolve a DI dependency inside `build()` — always in `initState()` or the constructor.
- Use a state enum + `runInAction()` after every `await` — never an ad-hoc observable future wrapper.
- Visual values (color, spacing, typography) come from the project's design system — never hardcoded.
- Entity fields are `final`, constructor `const` when possible.
- Don't generate tests — test coverage is handled separately, per the project's policy.
- If the feature needs a Coordinator (orchestrating multiple stores), design the architecture before scaffolding.
