# Flutter/Dart/Architecture — STANDARD Codes

Acordos de time comuns em projetos Flutter/MobX — `blocker:` por padrão em review, exceção precisa de justificativa no PR. Estes codes são um ponto de partida; adapte/renomeie para as convenções reais do seu time.

> **UI codes** (V1/V2 component versioning, raw visual values, Material widget) dependem do design system do seu projeto — se ele versiona componentes ou centraliza tokens visuais, adapte esses codes à sua config.

---

## Valor de negócio configurável não fica hardcoded no cliente

Valores que variam por marca, locale, mercado ou cadência de release pertencem ao backend/CMS — não ao cliente. Hardcoded acelera hoje e cria gargalo de release amanhã (qualquer mudança vira app deploy + review na loja).

Exemplos de domínio: filter date presets, sort options, promotional banners, currency/tax/shipping rules, per-market feature toggles, labels específicas de marca.

**Sinal**: array/map de constantes em widget ou store representando opções de filtro, sort, presets, ou rótulos de marca; ou `const` list que poderia mudar sem release.

**Quando NÃO se aplica** (defaults legítimos do cliente):
- Timing de animação, page-size de paginação, debounce
- Format strings derivadas de locale (currency formatter, date formatter)
- Estado puramente interno de UI (snap points, breakpoints)

---

## UI não importa SDK nem tipos DTO diretamente

Arquivos de UI (`*_widget.dart`, `*_page.dart`, `*_screen.dart`) não devem importar do pacote de SDK/repositórios do projeto nem declarar parâmetros ou campos com tipos `*DTO`. Quando isso acontece, o modelo externo vaza para a camada de apresentação, acoplando UI ao contrato da API.

**Sinal**: import do pacote de SDK/repositórios (config: nome do pacote no seu projeto) ou tipo `*DTO` em `*_widget.dart`, `*_page.dart`, `*_screen.dart`.

**Quando NÃO se aplica**: arquivos dentro do próprio pacote de SDK — lá o vocabulário externo é esperado por design.

---

## ObservableList/Map/Set é privado com getter

`ObservableList`, `ObservableMap` e `ObservableSet` devem ser campos privados com getter público. Exposição direta permite mutação externa sem `@action`, quebrando rastreabilidade.

**Sinal**: `@observable ObservableList` (ou Map/Set) sem underscore no nome.

---

## @observable bool isolado absorvido no enum de fluxo

Um único `@observable bool` que representa um estado de fluxo (não um flag de UI independente) deve ser absorvido no enum de estado existente. Booleans isolados criam estados compostos implícitos.

**Quando NÃO se aplica**: booleans de UI genuinamente independentes do estado de domínio (ex: `_isBottomSheetOpen` para controle visual local).

**Sinal**: `@observable bool` que coexiste com um enum de estado de fluxo no mesmo store.

---

## Resolução de dependência fora do build()

Resolver uma dependência do container de DI dentro de `build()` resolve a cada rebuild — cria instâncias desnecessárias e impede `const` propagation. Resolver no construtor, `initState()`, ou campo final.

**Sinal**: chamada de resolução de DI (`GetIt.I`, ou o wrapper do seu projeto) dentro de método `build()` ou `_build*()`.

---

## Chamada de resolução de DI não entra no store

Stores recebem dependências via construtor (injectable ou equivalente). Chamar o resolver do container de DI dentro do Store quebra inversão de controle e dificulta testes.

**Sinal**: `GetIt.I`, `GetIt.instance`, ou o wrapper de DI do projeto dentro de `*_store.dart` ou `*_controller.dart`.

Difere de DI001: DI001 cobre a chamada direta ao container (`GetIt.I<T>()`); este code cobre qualquer wrapper equivalente que o projeto tenha por cima dele.

---

## Action muta estado de erro — não lança exceção

Métodos `@action` que fazem `throw` forçam o caller a usar `try/catch`. O contrato correto é mutar o estado observável para erro ou retornar sealed result — o caller observa, não captura.

**Sinal**: `throw` dentro de método `@action` em store ou controller.

---

## Todo método público tem tipo de retorno explícito

Todo método público e `@action` deve ter tipo de retorno explícito. Inferência como `dynamic` causa erros silenciosos e dificulta review.

**Sinal**: método sem tipo de retorno antes do nome (`clearData()` em vez de `void clearData()`).

---

## FocusNode listener não chama setState — lógica vai pro store

Lógica de foco (validação, estado de campo) pertence ao store/controller. `FocusNode.addListener` que chama `setState()` mistura lógica de UI com estado de formulário.

**Sinal**: `addListener` + `setState` no mesmo bloco.

---

## const constructor não resolve dependência em build()

Widget com `const` constructor que resolve uma dependência de DI em `build()` é uma contradição: `const` implica que o widget é imutável e pode ser reutilizado, mas a resolução em build executa a cada rebuild. Remover `const` ou mover a resolução para fora do build.

**Sinal**: `const` constructor + resolução de DI dentro de `build()`.

---

## reaction() não chama setState — use Observer granular

`reaction()` que chama `setState()` derrota o tracking do MobX — força rebuild do widget inteiro em vez de permitir que `Observer` faça rebuild granular do subtree afetado.

**Quando NÃO se aplica**: side-effects genuínos (navegação, scroll, analytics) que não são rebuild de UI.

**Sinal**: `reaction(` com callback que chama `setState(`.

---

## l10n pertence à camada de UI — store recebe string pronta

Stores são camada de domínio/aplicação — não conhecem locale. Resolução de l10n pertence à camada de UI (Page). Se o store precisa de strings localizadas, recebe via parâmetro.

**Sinal**: resolução de l10n (ex.: `AppLocalizations.of(context)` ou equivalente) dentro de `*_store.dart` ou `*_controller.dart`.

---

## Adicionar novos codes

Ver política em `mobile:mobx` `REFERENCE.md` § Adicionar novos codes.
