---
name: feature-scaffold
description: Invoque para gerar o scaffold de uma feature Flutter nova — page, MobX store/controller, repository, entity — seguindo o padrão em camadas (UI → State → Domain → Data) do projeto. Gatilhos em pt-BR — "cria uma feature nova", "faz o scaffold de <nome>", "gera store+repository+page pra isso".
---

# Feature Scaffold — Scaffold Flutter Feature

Gera uma feature Flutter completa seguindo o padrão em camadas: page, MobX store/controller, repository, entity.

## Config do projeto

Os templates assumem `get_it`/`injectable` (DI), MobX (state), `dartz` `Either` (erros), e uma pasta `lib/src/modules/<module>/`. Se seu projeto usa outro stack de estado/DI/erro, adapte os templates antes de usar — a estrutura de 4 arquivos (entity/repository/controller/page) e a ordem dos steps abaixo continuam valendo.

## Uso

Peça ao usuário (se não vier na mensagem):
- **Nome da feature** (snake_case, ex.: `race_results`).
- **Subconjunto de arquivos** a gerar: `entity`, `repository`, `controller`, `page` (default: todos os quatro). Ex.: só `entity,repository` se a camada de UI já existe; só `controller,page` se entity/repository já existem.

## Templates

Fonte de verdade em `templates/`:

| Template | Path gerado | Papel |
|---|---|---|
| `entity.dart.template` | `entities/{{feature_name}}_entity.dart` | Entidade de domínio imutável. `extends Equatable`, campos `final`, construtor `const`, factory `fromDTO(...)`, `copyWith`, `props => [id]`. Identidade por `id`. |
| `repository.dart.template` | `repository/{{feature_name}}_repository.dart` | Camada de dados. `@lazySingleton`, `final class`. Stub `getAll()` lança `UnimplementedError` até o endpoint real ser plugado. |
| `controller.dart.template` | `controller/{{feature_name}}_controller.dart` | Camada de estado. `@injectable`, mixin MobX `Store` via `part '*.g.dart'`. Enum `{{FeatureName}}State { initial, loading, success, error }`. Observables privados (`_state`/`items`/`errorMessage`) com getters/computed; `@action load()` que envolve mutações pós-await em `runInAction`. |
| `page.dart.template` | `pages/{{feature_name}}_page.dart` | Camada de UI. `StatefulWidget` resolvendo o controller em `initState()`. `Observer` faz switch no enum `state`: loading → spinner, error → mensagem, success → `ListView.builder`. |

Placeholders em todo template:
- `{{FeatureName}}` — PascalCase (ex.: `RaceResults`).
- `{{feature_name}}` — snake_case (ex.: `race_results`).

Anotações críticas preservadas pelos templates: `@lazySingleton`/`@injectable` (DI), `@observable`/`@computed`/`@action` (campos e métodos do controller), `part '*_controller.g.dart'`. Remover qualquer uma quebra DI ou codegen silenciosamente.

## Steps

1. **Nome da feature** — snake_case. Se ausente, pergunte.

2. **Parse do subconjunto de arquivos** — valide contra `{entity, repository, controller, page}`. Rejeite entradas desconhecidas. Default: todos os quatro.

3. **Confirmar escopo** — pergunte:
   - "Em qual módulo essa feature entra?" (o nome vira o segmento `<module>` no path de destino)
   - "É um controller específico de tela (`@injectable`) ou store de domínio compartilhado (`@lazySingleton`/`@singleton`)?"
   - "Qual é a entidade principal de dado?"
   - "A API retorna uma lista, um objeto único, ou faz uma mutação (create/update/delete)?"

   Espere as respostas antes de gerar.

4. **Referência de design (se houver)** — se o usuário tiver uma referência visual (Figma ou equivalente), pergunte se quer rodar a ferramenta de design-to-code do seu setup antes de preencher a UI. Sem referência: confirme "scaffold sem referência visual — layout placeholder" e prossiga.

5. **Computar placeholders** — `{{feature_name}}` = argumento snake_case; `{{FeatureName}}` = derivação PascalCase (split em `_`, capitaliza cada segmento).

6. **Gerar arquivos** — para cada nome no subconjunto resolvido:
   1. Leia `templates/{name}.dart.template`.
   2. Substitua toda ocorrência de `{{FeatureName}}` e `{{feature_name}}`.
   3. Escreva em `lib/src/modules/<module>/{{feature_name}}/<layer>/{{feature_name}}_<name>.dart` (`<layer>` conforme a tabela acima).
   4. Não sobrescreva um arquivo existente silenciosamente — se o alvo já existe, confirme com o usuário.

   Notas por arquivo:
   - **entity**: o tipo DTO correspondente precisa existir no SDK/pacote de dados do projeto — confira o tipo real e ajuste o import/mapeamento.
   - **repository**: plugue o endpoint real substituindo o stub `UnimplementedError`.
   - **controller**: troque `@injectable` por `@lazySingleton`/`@singleton` se o estado precisa persistir entre telas. Store vs Controller: singleton para estado de domínio compartilhado (carrinho, usuário); injectable para estado específico de tela (filtros, busca, paginação de lista).
   - **page**: troque o `CircularProgressIndicator()` pelo padrão de loading do seu design system (spinner vs. shimmer/skeleton — convenção do projeto).

7. **Registrar DI** — lembre o usuário de rodar o codegen:
   ```bash
   dart run build_runner build --delete-conflicting-outputs
   ```

8. **Registrar rota** — lembre de adicionar a entrada de rota no router do projeto (`go_router` ou equivalente).

9. **Resumo** — liste só os arquivos de fato gerados (respeitando o subconjunto) + follow-ups:
   - Plugar DTO/endpoint real.
   - Substituir UI placeholder pelos componentes + tokens do design system do projeto.
   - Rodar `dart run build_runner build --delete-conflicting-outputs`.
   - Rodar `flutter analyze`.

## Important

- Nunca resolva a dependência de DI dentro de `build()` — sempre em `initState()` ou no construtor.
- Use enum de estado + `runInAction()` após todo `await` — nunca wrapper de future observável ad-hoc.
- Valores visuais (cor, espaçamento, tipografia) vêm do design system do projeto — nunca hardcoded.
- Campos de entity são `final`, construtor `const` quando possível.
- Não gere testes — cobertura de teste é tratada separadamente, conforme a política do projeto.
- Se a feature precisa de um Coordinator (orquestrando múltiplas stores), desenhe a arquitetura antes de fazer o scaffold.
