# archaeology — Reference

Conteúdo de apoio extraído do `SKILL.md` (D14, teto de 120 linhas). Consultado durante a execução dos steps — não é lido antes de decidir invocar a skill.

## §1 — Formato de apresentação do vocabulário (Step 1)

Apresente ao usuário antes de disparar os agentes:

```
Modo detectado: <ticket | domínio livre | US text>
Domínio: <Busca Unificada>

Termos primários: search, busca, query, unified
Termos de código: SearchController, SearchResultListController, SearchRepository
Módulos candidatos: home, catalog, filter, results

Grep patterns (4 agentes vão usar):
- Entry:        SearchField|onSearchChanged|Route\..*search
- Controllers:  glob *search*_controller.*, *search*_store.*
- Repos:        SearchRepository|SearchDataSource, plus /api/.*search no SDK/pacote compartilhado
- Duplicação:   RecentSearches|debounce.*search, paginação compartilhada

Editar termos / módulos / patterns? (enter = confirmar)
```

Aguarde confirmação antes de avançar. Termos errados contaminam todos os 4 agentes.

## §2 — Instruções detalhadas por dimensão (Step 2)

Dispare **4 agentes Explore em paralelo** (`subagent_type: "Explore"`), um por dimensão. Passe os termos, módulos e patterns confirmados no passo 1.

**Cada agente entrega evidência crua + cita `arquivo:linha`.** Não classifica como "shared", "risco" ou "oportunidade" — isso é trabalho do consolidador no passo 3.

---

**Dimensão A — Entry Points**

Onde o usuário pode acionar esta funcionalidade?

- Grep pelos patterns confirmados de entry no passo 1
- Para cada entry point: módulo, widget/arquivo:linha, rota destino, quem instancia
- Classifique apenas se o entry leva ao fluxo `ativo` ou ao fluxo `legado` (presença em `showcase/`, `old/`, `deprecated/`)
- **Não** opine sobre "fluxo novo da US" — só estado atual

---

**Dimensão B — Controllers e Stores**

Qual estado gerencia esta funcionalidade?

- Grep pelos globs confirmados de controllers/stores
- Para cada um: nome, módulo, repositório/método chamado, page ativa que o instancia (via DI ou instância direta)
- Status: `ativo` (tem caller confirmado), `legado` (sem caller após grep), `duplicado` (mesmo propósito de outro — citar o duplicado)

---

**Dimensão C — Repositórios e Endpoints**

Quais chamadas de API existem?

- Grep no diretório de módulos e no diretório de SDK/pacote compartilhado (config) pelos termos confirmados
- Para cada repositório: método exposto, endpoint inferido, tipo de resposta, quem consome
- Localização: pacote compartilhado ou app-local
- **Cite arquivo:linha** pra cada método

---

**Dimensão D — Duplicação**

O que está repetido?

- Grep pelos padrões de duplicação confirmados (debounce, paginação, cache local, etc.)
- Para cada achado: arquivos que duplicam, descrição da divergência (se houver), citação `arquivo:linha`
- **Não** opine sobre "candidato a remoção" — só liste o que está duplicado

---

## §3 — Template de consolidação (Step 3)

Com os 4 outputs em mãos, sintetize o mapa **nesta ordem e estrutura** (não improvise seções):

```markdown
# Mapa Arqueológico — <Domínio> — <YYYY-MM-DD>

(Se modo ticket: linha **Ticket:** PROJ-XXX — <título>)
(Se modo US text ou ticket: linha **Contexto:** <1 linha resumindo a US>)

## TL;DR
<3-4 linhas. O que existe (quantos controllers, quantos módulos), o que está
duplicado (com 1 exemplo), qual é a decisão estratégica mais bloqueante.
Sem tabelas. Sem listas. Punchline.>

## Decisões necessárias pro Tech Breakdown
<Ranked por severidade. Máximo 5 itens. Cada item: rótulo de severidade,
1 frase descrevendo a decisão, evidência citando arquivo:linha,
por quê bloqueia o tech breakdown.>

1. **[Alta]** <decisão>. Evidência: `arquivo.ext:L23`. Bloqueia porque: <1 linha>.
2. **[Alta]** ...
3. **[Média]** ...

(Demais perguntas, mesmo importantes, vão pra "Outras perguntas em aberto"
no fim — sem ranking.)

## Visão Consolidada por Módulo

| Módulo | Entry points | Controllers ativos | Endpoints | Status |
|---|---|---|---|---|
| catalog/new | SearchPage | SearchController, SearchResultListController | /api/search, /api/suggestions | ativo |
| catalog/legacy | LegacySearchPage | LegacySearchController | /api/legacy-search | legado |
| ... | | | | |

Status: `ativo` / `legado` / `parcialmente migrado` / `delega`.
Cruzamento dos 4 outputs dos agentes A-D.

## Evidência por Dimensão

### Entry Points
<Tabela do agente A, sem modificação. Esta seção é a fonte bruta — citações
aqui podem repetir o que aparece em Oportunidades.>

### Controllers e Stores
<Tabela do agente B, sem modificação.>

### Repositórios e Endpoints
<Tabela do agente C, sem modificação.>

### Duplicações
<Lista do agente D, sem modificação.>

## Oportunidades de Melhoria

<Cada item com severidade ancorada na rubrica abaixo + evidência citando
arquivo:linha. Cada arquivo aparece UMA VEZ nesta seção (regra de dedup).
O frame é "o que poderia melhorar", não "o que remover".>

**Rubrica de severidade:**
- **Alta**: bloqueia o tech breakdown, exige decisão estratégica, ou tem
  divergência de contrato cross-módulo
- **Média**: afeta escopo mas tem workaround claro
- **Baixa**: débito conhecido / limpeza / dead code

| Oportunidade | Severidade | Evidência | Por quê importa |
|---|---|---|---|
| Endpoint divergente entre listagem e busca | Alta | `search_repository.ext:L82` + `catalog_repository.ext:L15` | filtros e paginação podem divergir |
| ... | | | |

**Subseções opcionais** (incluir apenas se aplicável e se evita repetir tabela acima):

- **Reutilizável**: o que é shared e pode entrar na nova US/feature sem mudança
- **Acoplado ao módulo**: o que precisaria refactor pra ser reutilizado
- **Legado confirmado**: sem caller ativo após grep
- **Integrações a preservar**: analytics, tracking, instrumentação

(Em modo US/ticket, "Remoção pela US" é um label válido dentro de Oportunidades
— o frame guarda-chuva continua sendo Oportunidades, mas itens podem ser
marcados como `[remoção pela US]`.)

## Outras perguntas em aberto

<Lista, sem ranking. Perguntas que NÃO bloqueiam o tech breakdown mas que
o PO/design precisa responder em algum momento.>
```

### Regras obrigatórias do consolidador

1. **Ordem fixa.** TL;DR → Decisões → Cross-dim → Evidência → Oportunidades → Outras perguntas. Não improvise seções (`Features a Remover`, `Analytics Atual` etc.). Se um achado não cabe nas seções prescritas, ele entra em **Oportunidades** com label apropriado.
2. **TL;DR é escrito por último.** Só depois de ter as outras 5 seções na mão.
3. **Dedup**: cada `arquivo.ext` ou símbolo aparece **uma vez** em Oportunidades. Tabelas de Evidência por Dimensão são exceção (fonte bruta, repetição esperada).
4. **Citação obrigatória em Oportunidades**: cada item exige `arquivo:linha` que veio de algum dos 4 agentes. Sem citação, o item não entra. Se o consolidador não consegue citar, o achado é inferência — corte.
5. **Ranking limitado**: "Decisões necessárias" tem no máximo 5 itens. Tudo o que sobrar vai pra "Outras perguntas em aberto" sem ranking.

## §5 — Mensagens de handoff (Step 5)

**Modo ticket / US text:**

> "Mapa salvo em `docs/superpowers/archaeology/...`
>
> Próximo passo recomendado: `core:tech-breakdown <ticket>` (se disponível) — o mapa serve como contexto adicional.
>
> Posso iniciar agora, ou você prefere revisar o mapa antes?"

**Modo domínio livre:**

> "Mapa salvo em `docs/superpowers/archaeology/...`
>
> Não há tech breakdown sem US. Use como referência arquitetural. Considere abrir tickets de follow-up pras Oportunidades de severidade Alta — elas representam decisões estratégicas que ainda não foram tomadas."

## §6 — Sinais de gordura a cortar

Antes de apresentar o mapa, varra estes sinais:

- **Achados sem evidência** — cada item em Oportunidades cita `arquivo:linha`. Sem citação, é inferência — corte.
- **Status "talvez legado"** — classifique como ativo ou legado; ambiguidade é ruído.
- **Endpoints inventados** — se o grep no SDK/pacote compartilhado não confirmou, marque como "a confirmar".
- **Módulos listados sem achado** — omita módulos onde o grep não encontrou nada relevante na tabela cross-dim.
- **Risco genérico** — "pode ter breaking changes" sem apontar o que específico não ajuda; corte.
- **Risco sem grep** — Oportunidades inferidas do texto da US sem confirmar no codebase é exatamente o problema que motivou a estrutura prescritiva. Toda Oportunidade exige `arquivo:linha` real.
- **Seções improvisadas** — se você está prestes a criar uma seção que não está no template (`Features a Remover`, `Analytics Atual`, etc.), pare e enfie o conteúdo em **Oportunidades** com label apropriado.
- **Duplicação cross-seção** — um mesmo achado em Oportunidades + Cross-dim + Outras perguntas é overlap. Mantenha em Oportunidades; nas outras seções, omita.

## §7 — Important

- Nunca classifique código como legado sem verificar caller ativo (grep por instanciação via DI ou instância direta na page).
- A tabela cross-dim por módulo é o artefato mais crítico depois do TL;DR — priorize completude nela.
- O mapa **não é um plano técnico** — descreve estado atual e levanta decisões, não propõe soluções.
- Se o domínio cruzar mais de 6 módulos, pergunte ao usuário se quer escopo reduzido antes do dispatch.
- Sempre confirme o vocabulário e os grep patterns extraídos (passo 1) antes de executar.
- Modo **domínio livre** não dispara handoff pra `core:tech-breakdown` — é referência arquitetural, não pré-US.
- Os 4 agentes entregam evidência crua. **Oportunidades é 100% síntese pelo consolidador** — por isso a regra de citação obrigatória é o que separa síntese honesta de inferência sem grep.
