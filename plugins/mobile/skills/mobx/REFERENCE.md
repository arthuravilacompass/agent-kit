# MobX & DI Quality — Reference

## Filosofia — Antes de Propor Qualquer Mudança de Estado

**1. Esse estado já existe no store?** → observe diretamente. Nunca crie controle imperativo paralelo (`GlobalKey`, callbacks, `State` exposto).

**2. Vou adicionar um boolean flag?** → quase sempre sinal de enum ou sealed class. `isLoading + isError` → `enum State { idle, loading, success, error }`.

**3. Estou usando contador para rastrear algo?** → anti-pattern. Use lista observável ou estado derivado. `@computed int get count => items.length`.

**4. Esse `@observable` poderia ser `@computed`?** → se deriva de outro estado, é `@computed`. Observáveis redundantes causam dessync.

**5. O nome reflete o domínio, não o mecanismo?** → `isEditingInput` → ruim · `addressInputState` → certo. Nome = conceito de negócio.

---

## Quando aplicar

Ao gerar, editar ou revisar qualquer `*_store.dart`, `*_controller.dart`, `*_page.dart`, `*_screen.dart`, ou `*_widget.dart`. Cobre smells que linter não detecta.

## Tiers — geografia de enforcement

| Tier | Onde vive | Comportamento em review |
|---|---|---|
| 🔴 **BLOCKER (hook)** | Esta skill + `hooks/smell-checker.sh` (config do projeto — ver Task de hooks deste plugin) | Bloqueia mecanicamente (exit 2) — DI001, ARCH001, LOG001 |
| 🔴 **BLOCKER (on-demand)** | Esta skill (REFERENCE.md) | `blocker:` — carregado por review agents e advisor; sem gate mecânico |
| 🟡 **STANDARD (on-demand)** | Esta skill + `mobile:code-review-mobile` STANDARDS.md | `blocker:` por padrão; exceção precisa de justificativa no PR |
| 🔵 **ASPIRATIONAL** | `PATTERNS.md` (esta skill) | `non-blocker:` — sugestão. Aplica em código novo; não obriga refactor |

> **Importante:** ASPIRATIONAL ≠ "regra ruim". É padrão sofisticado que vale enforcement gradual. Bloquear PR de bugfix pequeno por ASPIRATIONAL é fricção sem benefício proporcional.

## Enforcement

Code com ID só nasce junto com seu validador-máquina (hook, eval ou agent); sem validador, escreva prosa com título forte. IDs com validador mecânico:

- **DI001, ARCH001, LOG001** — `hooks/smell-checker.sh` deste plugin (exit 2, add-only). Os demais BLOCKER (MOBX001-005, "Store não nasce em build()") ficam só em prosa nesta skill — não há gate automático para eles.
- **FSM001 / SSOT001 / CMD001 / MOBX006** — agente `mobile:mobx-smell-hunter`.

---

## 🔴 BLOCKER

### MOBX001 — Boolean flags paralelos em Store

**You MUST NOT** criar dois ou mais `@observable bool` mutuamente exclusivos no mesmo store.

**Why**: o estado real é um enum/sealed class. Boolean flags paralelos permitem combinações inválidas (`isLoading=true && isError=true`) e causam reactions em estados intermediários inconsistentes.

**Sinal**: dois+ `@observable bool` no mesmo store sem enum correspondente, com nomes complementares (`is*`, `has*`, `_pending*`, `_needs*`).

**Failure mode**: UI renderiza estado impossível (spinner + erro simultâneos); Observer rebuilds em combinações que não deveriam existir; debug ruim.

---

### MOBX002 — `@computed` com side effect

`@computed` é função pura. Sem I/O, sem async, sem mutações, sem chamadas que alteram estado.

**Sinal**: chamada de método que muta estado, `await`, ou `setState()` dentro de `@computed`.

**Failure mode**: `@computed` com side effect pode executar em momentos inesperados (MobX rastreia acesso, não chamada explícita); I/O em computed cria loops e comportamento não-determinístico.

---

### MOBX003 — reaction/autorun/when sem dispose

Todo `ReactionDisposer` deve ser armazenado e chamado no teardown. Em classes gerenciadas por DI, use o hook de dispose do seu container (ex.: `@disposeMethod` do `injectable`).

**Sinal**: `reaction(`, `autorun(`, `when(` sem atribuição a `ReactionDisposer`; ou `ReactionDisposer` sem dispose correspondente.

**Failure mode**: memory leak — reaction continua rodando mesmo depois que o objeto é "destruído"; em widgets isso causa `setState` após dispose.

---

### MOBX004 — Observable e getter (reconciliado)

**Formulação original** (não reflete a prática — ver correção abaixo): "`@observable` deve ser campo privado (`_field`) com getter público."

**Correção registrada**: medido em um projeto real (2026), **61% dos `@observable` em stores reais eram públicos** (sem underscore) e reativamente corretos — o padrão dominante era `class X = _XBase with _$X;` + campo público `@observable` na classe base abstrata, com `mobx_codegen` gerando o accessor trackado via mixin. Campo público **não** quebra reatividade quando o mixin gerado é quem expõe o accessor. Um review que tratou `@observable` público como violação clara errou — a prática real estava do lado do código, não da regra.

**You MUST NOT** declarar um getter manual que bypassa o mixin gerado.

**Sinal real**: getter escrito à mão (`Type get x => _x;`) sobre um campo que deveria ser exposto só pela classe gerada (`_$Store`). Isso sim quebra o tracking — o MobX não sabe que `x` depende de `_x` fora do mecanismo do codegen.

**Sinal que NÃO deve ser tratado como violação por si só**: `@observable` sem underscore no nome do campo. Verifique a convenção do projeto antes de sinalizar — pode ser o padrão dominante e reativamente são.

**Failure mode (do smell real)**: getter manual não é rastreado como dependência pelo MobX; `Observer` que lê o getter não rebuilda quando `_x` muda.

**Como aplicar**: se o projeto usa o padrão privado+getter, mantenha consistência com o restante do arquivo. Se o projeto usa campo público direto (classe base abstrata com mixin), não force a migração — sinalize apenas o getter manual.

---

### MOBX005 — Múltiplas mutações pós-await sem `runInAction()`

**You MUST NOT** atribuir a `@observable` após `await` fora de `runInAction()`.

**Why**: sem `runInAction()`, cada atribuição dispara uma reaction separada. Observers veem estados intermediários inválidos (e.g., `data` populado mas `isLoading` ainda true).

**Sinal**: atribuição a `@observable` (ou chamada a setter de observable) após `await` sem envelopar em `runInAction(() { ... })`.

**Failure mode**: UI pisca / renderiza estado inconsistente; reactions disparam em momentos errados; race conditions difíceis de reproduzir.

---

### ARCH001 — `BuildContext` / `GoRouter` / `Navigator` dentro de Store

> enforced-by: `hooks/smell-checker.sh` (exit 2)

**You MUST NOT** referenciar `BuildContext`, `Navigator`, `GoRouter`, `ScaffoldMessenger`, `showDialog` dentro de `*_store.dart` ou `*_controller.dart`.

**Why**: stores são camada de domínio/aplicação. Não conhecem UI. Acoplar a `BuildContext` impede teste sem widget tree e quebra a separação de camadas.

**Sinal**: `context.push`, `context.pop`, `Navigator.of`, `GoRouter.of`, `showDialog`, `ScaffoldMessenger.of` dentro de arquivo de store/controller.

**Failure mode**: store impossível de testar sem widget; refactor de navegação cascateia em N stores; coordenação fica espalhada.

**Como aplicar**: store expõe `@observable State` → Page observa via `Observer` e chama `context.push` / `Navigator.pop` no callback do widget.

---

### DI001 — `GetIt.I<T>()` dentro de Store ou Controller

> enforced-by: `hooks/smell-checker.sh` (exit 2)

**You MUST NOT** chamar `GetIt.I<>`, `GetIt.instance.get`, ou wrappers equivalentes dentro de `*_store.dart` ou `*_controller.dart`.

**Why**: dependências chegam via construtor (`injectable` + `@injectable`/`@lazySingleton`, ou o equivalente do seu container de DI). O container de DI é responsabilidade do módulo de registro, não do consumer.

**Sinal**: `GetIt.I<`, `GetIt.instance`, `GetIt.I.get`, ou o wrapper de resolução de DI do projeto (config) dentro de store/controller.

**Failure mode**: dependências invisíveis quebram teste (precisa stub do container global); ciclo de vida não controlado; refactor de DI fica perigoso.

**Como aplicar**: store recebe dependências via constructor (`MyStore(this._repo, this._coordinator)`); registro fica no módulo de DI do projeto com a anotação apropriada.

---

### "Store não nasce em build()"

Store criada em `build()` é destruída e recriada a cada rebuild — perde todo o estado.

**Sinal**: `StoreClass()` ou `ControllerClass()` instanciado dentro de método `build()`.

**Failure mode**: estado perdido a cada rebuild; o container de DI não gerencia ciclo de vida; possível vazamento se o store não for disposto.

---

### LOG001 — `print()`/`debugPrint()` trocado por `dart:developer log()`

> enforced-by: `hooks/smell-checker.sh` (exit 2)

`print()` e `debugPrint()` em código de produção (`lib/src/` ou equivalente — config do projeto) devem ser substituídos por `dart:developer log()`.
`print()` não é filtrado por nível, não carrega stackTrace, e polui o console em produção.

**Sinal**: `print(` ou `debugPrint(` em arquivos de produção.
**Exceção**: arquivos de teste podem usar `print()`.

---

## 🟡 STANDARD on-demand

Ver `mobile:code-review-mobile` STANDARDS.md: valor de negócio configurável não fica hardcoded no cliente, UI não importa tipos de SDK/DTO diretamente, `ObservableList`/`Map`/`Set` privado com getter, `@observable bool` isolado absorvido no enum de fluxo, resolução de dependência fora do `build()`, chamada de resolução de DI não entra no store, action muta estado de erro em vez de lançar exceção, todo método público tem tipo de retorno explícito, `FocusNode` listener não chama `setState` (lógica vai pro store), `const` constructor não resolve dependência em `build()`, `reaction()` não chama `setState` (use `Observer` granular), l10n pertence à camada de UI (store recebe string pronta).

## 🔵 ASPIRATIONAL — PATTERNS.md (on-demand)

FSM001, CMD001, SSOT001, MOBX006 (com IDs — validados pelo agente `mobile:mobx-smell-hunter`). Formas narrativas: ação falível retorna sealed result, store gerenciada por Coordinator é pura. `non-blocker:` em review.

---

## Política de codes

Code com ID só nasce junto com seu validador-máquina (hook, eval ou agent); sem validador, escreva prosa com título forte nesta seção.

## Adicionar novos codes

Default: nova orientação STANDARD nasce em `mobile:code-review-mobile` STANDARDS.md. Promoção para BLOCKER com gate mecânico (hook) requer decisão explícita — apenas quando o code captura bug, leak, correctness ou segurança.
