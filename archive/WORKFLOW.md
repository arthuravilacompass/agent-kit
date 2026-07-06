# WORKFLOW — uso diário com Claude Code

Guia operacional do dia-a-dia: **quando** você pega cada ferramenta e **como** dirige. É o manual do operador.

> Genericizado a partir do manual de um projeto de origem — os nomes de skill/comando abaixo já refletem o vocabulário deste kit (`core` + `mobile`), não o original. Onde o original tinha algo que não foi portado (dashboard de release, design-tokens do design system específico), a lacuna fica marcada, não inventada.

---

## 0. O fluxo

Tarefa não-trivial roda em quatro tempos: **planejar → executar → revisar → entregar**.

```
planejar (modelo forte)  →  /clear  →  executar (modelo de execução)  →  revisar  →  commit/PR
```

- **Plano-orientado.** Abra qualquer coisa não-trivial com brainstorm/planejamento, salve o plano ou handoff em `docs/` (`plans/` para planos, `specs/` para specs, `handoffs/` para handoffs), e só então execute.
- **Modelo forte planeja, modelo de execução executa.** Reserve o modelo mais caro/lento para planning e síntese; o modelo de execução para código, fixes, reviews e investigação. Documente a divisão real do seu setup em vez de herdar nomes de modelo de outro projeto.
- **`/clear` entre tarefas independentes.** Contexto sujo de uma tarefa contamina a próxima. Quando o contexto encher no meio de uma, salve um handoff e retome a partir dele.

Os três tipos de trabalho seguem o mesmo esqueleto, com paradas diferentes:

- **Feature.** `advisor-check pre-plan <TICKET>` → `superpowers:brainstorming` → `superpowers:writing-plans` → `advisor-check post-plan` → execução → `advisor-check pre-done` → `review-local` (ou `review-remote` sem o plugin de review) → `commit`/`pr`. (O post-plan é obrigatório antes de executar — ver §2.)
- **Bugfix.** Mapeie a cadeia completa (UI → validação → estado → origem) antes do fix; siga as 4 perguntas de bugfix-principles do projeto (contrato violado? ausente≠vazio? ciclo de vida do estado? invariante implícito?). Ao fechar, se o bug passou pelo harness, adicione o caso em `docs/evals/` (tier 1 se mecanizável, tier 2 se julgamento).
- **Refactor.** Ancore o smell antes de brainstormar; rode `advisor-check pre-plan` quando há alternativas reais; feche com a skill `refactor-review` em todos os callers afetados antes do commit.

---

## 1. Skills

Invocação: `/<nome>` (humano) ou descoberta pelo modelo, conforme o frontmatter.

### Planejamento
- **`superpowers:brainstorming`** — antes de qualquer trabalho criativo (feature, componente, mudança de comportamento). Fecha objetivo/escopo/critérios antes de uma linha de código. Termina num spec aprovado.
- **`superpowers:writing-plans`** — transforma o spec num plano de implementação passo a passo. Salva em `docs/plans/`.
- **`tech-breakdown <TICKET>`** — para TL: busca o ticket, roda brainstorming + refinamento adversarial + writing-plans, e devolve um plano pronto pra dev.
- **`spec-refine`** — refinamento adversarial de um spec: caça error paths faltando, estados ambíguos, invariantes não-escritos.
- **`grill-me`** — entrevista relentless pra stress-test de um plano ou decisão de design antes de construir.

### Execução
- **`feature-scaffold`** — scaffold de módulo Flutter completo (entity, repository, controller, page) seguindo a estrutura em camadas do projeto.
- **`superpowers:executing-plans`** — executa um plano escrito com checkpoints de review (sessão separada).
- **`superpowers:subagent-driven-development`** — executa tarefas independentes de um plano na sessão atual, via subagents.

### Review (antes do PR)
- **`review-local`** — review vs branch base antes do PR: precondition (analyze/test) + agentes paralelos + verificação por citação. Requer o plugin `pr-review-toolkit`.
- **`review-remote`** — mesma proposta, sequencial e plugin-free (sem `pr-review-toolkit`).
- **`code-review-mobile`** — checklist universal (sempre) + camada contextual (UI, Observer, listas, l10n, navegação, testes) + referência de estrutura de módulo/componente.
- **`refactor-review`** — protocolo pós-refactor (regressão + qualidade) antes de commitar código compartilhado (stores, repos, coordinators, nav, checkout).
- **`/code-review`** e **`/simplify`** (built-in do Claude Code) — revisam o diff atual: o primeiro caça bugs de correção; o segundo, redundância/clareza.

### Domínio (consulta sob demanda)
- **`mobx`** — casa única do conhecimento MobX: tier policy, codes, receitas de fix, patterns aspiracionais.
- **`<design-tokens>`** — placeholder: referência do design system do projeto, se existir (todo valor visual via token, nunca hardcode cor/spacing/raio). Não portado neste kit — o original era proprietário demais pra genericizar (ver `archive/figma-to-component/` e `archive/ui-comparison/` pela mesma razão).
- **`performance-patterns`** — Observer rebuilds, chamadas de rede, imagens, memória, RUM.
- **`marionette`** — validação visual agent-driven no simulador (ver §4).

### Debug
- **`superpowers:systematic-debugging`** — protocolo estruturado: mapeia UI + validação antes do fix, cadeia completa, sem pivô de hipótese no meio.
- **`export-logs`** — exporta logs de rede do Flutter por intervalo de tempo via Dart VM Service.

### Captura / aprendizado
- **`learn`** — escaneia a sessão por correções/preferências/decisões e propõe entradas de memória (com aprovação).
- **`compound`** — gate de fim de track: `learn` + handoff condicional + candidato a graduação.

### Comunicação / entrega
- **`pr`** — criação de PR padronizada com template e validações.
- **`commit`** — commit padronizado com validações de formato e scope.
- **`chat-draft`** — draft de mensagens informais pt-BR pra Teams/Slack (squad update, recap de tech-sync).

### Conselho de Posturas (arquivado, não wired neste kit)
Seis modos de raciocínio que você veste de propósito — *como* interrogar um problema, não *o quê*. Silêncio é a feature no trabalho rotineiro. Material completo em `archive/council/` + `archive/posturas/` + `archive/agents/` — sobe a `plugins/` só com uso real comprovado (ver `archive/README.md`).

---

## 2. Commands / checkpoints

- **`advisor-check <modo>`** — escalada controlada em checkpoints de decisão. Três modos:
  - `pre-plan <TICKET> [--greenfield]` — advisor nativo (contexto cheio) antes de escolher a abordagem. `--greenfield` firewalla as rules pra não re-ancorar um conceito novo no que já existe.
  - `post-plan` — advisor nativo, plano aprovado e antes de codar. **Obrigatório no track de feature** antes de qualquer skill de execução (pula-lo deixa bugs landarem horas adentro).
  - `pre-done` — subagent **cego** adversarial (só diff + ACs, sem sua narrativa); findings verificados por `validate_citations.py`. Roda no "acho que terminei", antes do review.
  - Complementa o advisor nativo, não substitui: o nativo vê tudo (ideal pra planning); o `pre-done` esconde a narrativa de propósito, pra quebrar a bolha epistêmica.
- **`archaeology`** — mapa do codebase pré-US: o terreno antes de começar.
- **`refine-live` / `refine-async`** — assistente de refinamento ao vivo + triage pós-refinamento. Arquivados (`archive/refine/`) por não terem uso comprovado neste kit — placeholders de ticket/board no lugar dos nomes reais do projeto de origem.
- **Dashboard de prontidão de release** — o projeto de origem tinha uma skill de operação bem específica (git delta + QA + board + pubspec) que não generalizou o bastante pra portar; se o novo projeto precisar de algo assim, escreva a própria a partir do zero em vez de herdar esta.

---

## 3. Hooks

Validação mecânica que o harness roda sozinho em eventos do Claude Code. Você não invoca — precisa entender o que aparece.

**Plugin `core`:**
- **`session-start.sh`** (SessionStart) — injeta o corpo da skill `using-agent-kit` como contexto sempre-ligado.
- **`plan-autoload.sh`** (SessionStart) — detecta o plano/handoff mais recente nos locais canônicos de doc e injeta o path pra retomar.
- **`bash-autoapprove-readonly.sh`** (PreToolUse Bash) — auto-aprova comando Bash só se TODO segmento (incl. dentro de `$()`/crase) for read-only; ambiguidade nunca aprova.
- **`claude-dir-guard.sh`** (PreToolUse Bash) — bloqueia `rm` que também toque um path `.claude/` (projeto ou usuário).
- **`scope-inject.sh`** (PreToolUse Edit/Write/MultiEdit) — knowledge map genérico: lê `.claude/knowledge-map.tsv` do projeto consumidor e injeta o ponteiro de decisão 1×/sessão por área tocada. Sem arquivo de mapa → no-op.
- **`context-monitor.sh`** (PostToolUse Bash) — monitora tamanho do transcript como proxy de uso de context window; avisa 1× por threshold.
- **`read-ledger.sh`** (PostToolUse Read/Grep) — registra file:line realmente lido na sessão; alimenta o gate de citação (`validate_citations.py`).

**Plugin `mobile`:**
- **`smell-checker.sh`** (PreToolUse Edit/Write/MultiEdit) — **bloqueia** (exit 2) um conjunto pequeno de smells MobX/DI estaticamente detectáveis. Add-only: não cobra código pré-existente.
- **`dart-auto-format.sh`** (PostToolUse Edit/Write/MultiEdit) — formata `.dart` editado com `dart format --line-length 120`. Pula gerados (`.g.dart`/`.freezed.dart`/`.config.dart`).
- **`dart-analyze-file.sh`** (PostToolUse Edit/Write/MultiEdit) — `dart analyze` escopado ao arquivo editado, feedback advisory (nunca bloqueia).
- **`package-feedback.sh`** (PostToolUse Edit/Write) — reage a edits em `pubspec.yaml` num workspace multi-pacote (ex.: dispara `flutter pub get` em background).

---

## 4. MCPs

Servidores externos conectados à sessão. Prefira a tool do MCP a aproximar com shell.

- **marionette** — dirige o app Flutter em debug no simulador: screenshots, tap, scroll, enter text, hot reload.
- **dart** — toolchain Dart/Flutter: analyze, format, run tests, hot reload, runtime errors, widget tree.
- **context7** — docs de bibliotecas ao vivo, sob demanda. Use antes de afirmar API de lib.
- **Kanban/board do projeto** — lê/escreve cards e docs de gestão de trabalho (nome do servidor MCP depende do board real do projeto consumidor).
- **Figma** — lê designs do Figma (`get_design_context`, `get_screenshot`) → mapeie pra widgets do design system real do projeto.

---

## 5. Ponteiros

- **Inventário deste kit:** `.claude-plugin/marketplace.json` + READMEs de `plugins/core/` e `plugins/mobile/`.
- **Regra de promoção de `archive/` → `plugins/`:** `archive/README.md`.
- **Convenções, arquitetura, padrões-chave do projeto consumidor:** o `CLAUDE.md` do projeto — ver `assets/claude-md-starter.md` pra um esqueleto de partida.
