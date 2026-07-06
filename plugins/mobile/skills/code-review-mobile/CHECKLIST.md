# Flutter Code Review Checklist

Checklist universal de code review para Flutter/Dart (stack MobX + get_it/injectable + go_router + dartz). Sempre carregado em PR review.

## Verification Discipline (mandatory)

Antes de listar qualquer finding em report de review, releia as linhas exatas que vai marcar e cite-as. Se o problema já está corrigido no estado atual do arquivo, descarte o finding. Reviews perdem credibilidade quando listam issues já resolvidos.

Aplica-se a:
- Reviews de PRs remotos (o arquivo na branch remota pode diferir do snapshot inicial do diff)
- Reviews depois que o autor pushou novos commits no meio do review
- Qualquer finding produzido por subagent que não leu o arquivo diretamente

**Regra**: todo finding no report final precisa ter file path + line number, e você deve ter acabado de ler aquelas linhas.

## Workflow

1. `git diff <base>...HEAD` (config: branch base do projeto) para ver todos os commits do PR
2. Aplicar **Camada 1** abaixo — todo PR, sem exceção (17 itens)
3. Aplicar **Camada 2** (este skill) — apenas quando o gatilho for verdadeiro
4. Se for refactor: `mobile:refactor-review` (protocolo de 2 fases)
5. Antes de commit/PR: rode o fluxo de commit/PR do seu setup (ex.: `core:commit`, `core:pr`)

## Camada 1 — Sempre Revisar

| # | Item | Regra |
|---|---|---|
| 1 | Lógica de negócio correta | — |
| 2 | State shape: sem boolean flags paralelos | MOBX001 |
| 3 | `runInAction()` após await com múltiplas mutações | MOBX005 |
| 4 | Error handling: `Either` no repo, `fold` no controller (ou o padrão de erro do seu projeto) | architecture |
| 5 | Fix na camada certa (não compensar producer no consumer) | bugfix principles (config do projeto) |
| 6 | Null safety: sem `!` excessivo, sem `dynamic` implícito | Dart |
| 7 | `catch (e)` genérico sem `on` → especificar tipo da exceção | Dart |
| 8 | Nunca capturar `Error` (indica bug, não deve ser tratado) | Dart |
| 9 | Sem `print()` em produção → usar `dart:developer log()` | LOG001 |
| 10 | Sem dados sensíveis em logs (tokens, PII) | Security |
| 11 | Testes adicionados/atualizados para código novo | Testing |
| 12 | Controllers não lançam exceções → mutam estado ou retornam sealed result | CTRL001 |
| 13 | Chamada direta ao container de DI nunca dentro de Store/Controller | DI001/DI004 |
| 14 | Tipo de retorno explícito em `@action` e métodos públicos | DART001 |
| 15 | Estado de erro carrega informação para exibição (não só flag) | state shape |
| 16 | Estado de loading não retém dados de fetch anterior | state shape |
| 17 | Sem comentários explicando qual regra foi aplicada (`// MOBX004`, `// item 6`) em código produtivo — comentário descreve o *porquê*, não a regra | code hygiene |

## Prefixos de Comentário

Convenção comum de PR review (adapte à ferramenta do seu projeto — GitHub, Bitbucket, etc.):

| Tier da regra | Regras | Prefixo |
|---|---|---|
| 🔴 BLOCKER | MOBX001-005, ARCH001, DI001-002, LOG001 | `blocker:` |
| 🟡 STANDARD | codes em `STANDARDS.md` (on-demand) | `blocker:` |
| 🔵 ASPIRATIONAL | FSM001, ARCH002-003, CMD001, SSOT001, MOBX006 | `non-blocker:` |
| Preferência pessoal | estilo, nomes, decomposição | `non-blocker:` |

`blocker:` = obrigatório corrigir antes do merge. `non-blocker:` = avaliar e responder — pode discordar com justificativa.

Formato: `blocker: MOBX001 — _isLoading e _hasError são flags paralelos, deveriam ser um enum (BasketStore.dart:42)`

## Atalhos

- Este skill — Camada 2 (gatilhos contextuais) + reference (component structure, naming, imports, formatting)
- `mobile:refactor-review` — protocolo de 2 fases para refactor
- `mobile:mobx` `RECIPES.md` — receitas de fix por código de smell
- Entry points de review do seu setup (config): review completo pré-PR, review pre-push, review de PR remoto

## Fontes Canônicas

- `mobile:mobx` `REFERENCE.md` — regras codificadas (MOBX*, DI*, ARCH*, LOG001) BLOCKER tier
- `STANDARDS.md` (esta skill) — STANDARD codes on-demand
- `SKILL.md` (esta skill) — Camada 2 contextual + component structure reference
- `COOKBOOK.md` — exemplos DI, navegação, Either pattern, Security checklist, Testing

## Camada 2 — Quando Aplicável

| # | Quando | Item | Regra |
|---|---|---|---|
| 18 | Há reactions | Reactions com dispose em `dispose()` | MOBX003 |
| 19 | Há UI | Sem import de SDK/DTO na camada de UI | ACL001 |
| 20 | Há UI | Componentes do design system + tokens visuais (config: sistema de tokens do projeto) | UI001/UI002 |
| 21 | Há UI | `build()` < ~100 linhas, decompor em widgets | Widget |
| 22 | Há UI | Subwidgets em classes próprias (element reuse + const propagation) | Widget |
| 23 | Há UI | `const` constructors em widgets cujos campos são `final` | Widget |
| 24 | Há Observer | Observer granular (menor escopo possível, não tela inteira) | Performance |
| 25 | Há Observer | Subtrees estáticos dentro de Observer marcados como `const` | Performance |
| 26 | Há listas | `ListView.builder` / `GridView.builder` para listas grandes | Performance |
| 27 | Há rebuild complexo | `RepaintBoundary` em subtrees que repintam independentemente | Performance |
| 28 | Há imagens de rede | Cache, resolução apropriada, `cacheWidth`/`cacheHeight`, placeholder/error | Performance |
| 29 | Há animação de opacidade | `AnimatedOpacity`/`FadeTransition` em vez de `Opacity` direto | Performance |
| 30 | Há layout | `IntrinsicHeight`/`IntrinsicWidth` com parcimônia (extra layout pass) | Performance |
| 31 | Há MediaQuery | `MediaQuery.sizeOf(context)` em vez de `MediaQuery.of(context).size` | Performance |
| 32 | Há async fire-and-forget | Race conditions: token de versão ou cancelamento | MobX |
| 33 | Há coleções na UI | Sorting/filtering fora do `build()` → `@computed` | Performance |
| 34 | Há strings novas | l10n presente em todas as locales suportadas (config: lista do projeto) | L10n |
| 35 | Há strings localizadas | Sem concatenação — usar placeholders na chave | L10n |
| 36 | Há data/moeda/número | Formatação locale-aware (não hardcodar o locale) | L10n |
| 37 | Há l10n em store/controller | l10n resolvido na Page, injetado via parâmetro | L10N001 |
| 38 | Há resolução de DI em widget | Nunca em `build()`, só em `initState()` ou campo final | DI003 |
| 39 | Há `ObservableList/Map/Set` | Devem ser privados (`_`) com getter público | MOBX007 |
| 40 | Há widget `const` | `const` constructor + resolução de DI em build = erro | WIDGET003 |
| 41 | Há FocusNode | Listeners nunca chamam `setState()` → lógica no store | WIDGET002 |
| 42 | Há `reaction()` em widget | Nunca chama `setState()` → usar Observer em vez disso | PERF001 |
| 43 | Há paginação | Erro de página seguinte não destrói lista já carregada | Errors |
| 44 | Há erros transientes | Retry disponível para o usuário | Errors |
| 45 | Há navegação | Argumentos tipados via `extra` — sem `Map<String, dynamic>` ou cast de `Object?` | Navigation |
| 46 | Há nova classe DI | Sem dependências circulares no grafo | DI |
| 47 | Há testes | Edge cases: vazio, erro, loading, paginação, filtro | Testing |
| 48 | Há testes | Cada arquivo de teste cobre uma única classe | Testing |
| 49 | Há widget tests | `pumpWidget` + `pump`/`pumpAndSettle` corretamente (sem `sleep`) | Testing |
| 50 | Há componentes visuais críticos | Golden tests cobrindo estados | Testing |

## Standards — Conteúdo de Apoio

### Dart Language

- **`late`** — usar somente quando necessário; preferir nullable ou inicialização no construtor
- **`final`/`const`** — `final` para variáveis locais, `const` para constantes de compilação
- **Switch expressions** — preferir a cascatas de `if/else is` para pattern matching (Dart 3+)
- **Records** — `(String, int)` para retornos múltiplos simples em vez de classes descartáveis
- **Sealed class** — modelar estados com variantes mutuamente exclusivas
- **`unawaited()`** — `Future` retornado sem `await` deve ser marcado com `unawaited()` para indicar intenção
- **`StringBuffer`** — usar em loops; sem concatenação de string (`+=`) em loops

### Widget Keys

- **`ValueKey`** — usar em listas/grids para preservar estado entre reorders
- **`GlobalKey`** — usar com parcimônia; nunca para state sharing entre widgets
- **`UniqueKey`** — nunca em `build()` (força rebuild a cada frame)

### Race Conditions

```dart
// BAD — race condition se updateFilter for chamado duas vezes rápido
@action
void updateFilter(FilterEntity newFilter) {
  _resetFilter();
  fetchFilteredProducts();  // fire-and-forget, sem proteção
}

// GOOD — token de versão descarta responses obsoletas
int _filterVersion = 0;

@action
Future<void> fetchFilteredProducts() async {
  final version = ++_filterVersion;
  final result = await _repository.getProducts(filter);
  if (version != _filterVersion) return;  // stale, descarta
  runInAction(() {
    result.fold(
      (failure) => _state = ProductListState.error,
      (items) {
        _items
          ..clear()
          ..addAll(items);
        _state = ProductListState.success;
      },
    );
  });
}
```

### Navigation Guards

- Auth guards centralizados em um middleware de rota — não replicar lógica de auth em cada rota
- Deep links configurados em ambas plataformas (Android intent-filter + iOS Universal Links) — ver `mobile:deeplink-debug`
- `context.pop()` consistente — não misturar `Navigator.of(context).pop()` e `context.pop()` no mesmo fluxo
- Argumentos via `extra` tipado — nunca `Map<String, dynamic>` ou cast de `Object?`

### Coverage

Target comum: 80% em stores/repos (config: meta do seu projeto). Padrões de `setUp()` e cobertura de transições de estado: ver `COOKBOOK.md` §Testing.
