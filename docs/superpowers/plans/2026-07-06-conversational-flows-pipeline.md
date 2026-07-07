# core:pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar a skill condutora `core:pipeline` (camada de routing conversacional) + docs, sem tocar em nenhuma skill existente.

**Architecture:** 1 skill nova model-invocable que referencia as skills existentes como estágios; README/CHANGELOG atualizados; tabela de entrada no CLAUDE.md pessoal do usuário (fora do repo). Estado do pipeline mora nos artefatos já existentes.

**Tech Stack:** Claude Code plugin skills (SKILL.md + frontmatter), gate do repo (`check-provenance.sh` + `claude plugin validate` + `evals/run-evals.sh`).

## Global Constraints

- Spec: `docs/superpowers/specs/2026-07-06-conversational-flows-pipeline-design.md` (decisões §2 travadas).
- **Nenhuma skill/hook/script existente é modificado** (grill-me explicitamente intocado).
- SKILL.md alvo ≤120 linhas; model-invocable (SEM `disable-model-invocation` no frontmatter).
- Zero conteúdo de proveniência (sigla do cliente não aparece nem em docs novos).
- Gate completo antes de cada commit: `scripts/check-provenance.sh && claude plugin validate . && evals/run-evals.sh` (evals seguem 23/23 — sem casos novos, skill é prosa).
- Commits sem push até aprovação explícita do usuário.

---

### Task 1: Criar a skill `core:pipeline`

**Files:**
- Create: `plugins/core/skills/pipeline/SKILL.md`

**Interfaces:**
- Produces: skill `core:pipeline` listada pelo plugin core; nomes de estágio (Mapear, Diagnosticar, Clarificar, Especificar/refinar, Checkpoint, Quebrar, Implementar, Revisar, Entregar, Capturar) usados pelo README na Task 2.

- [ ] **Step 1: Escrever o arquivo (conteúdo integral)**

````markdown
---
name: pipeline
description: Invoque ao receber uma intenção crua de trabalho substancial (feature, bug, investigação, refactor, ticket/US) sem fluxo em andamento definido, ou quando o usuário pedir "por onde começo", "qual o fluxo pra isso", "me conduz nesse trabalho". Condutor de fluxo — detecta o estágio real da tarefa, classifica a intenção e roteia pelas skills do kit um estágio por vez; recomenda a próxima rota, nunca executa a cadeia inteira sozinho.
---

# Pipeline — condutor de fluxo

Camada de routing do kit: a mensagem do usuário carrega só a **intenção**; este condutor decide **onde ela entra** e **qual o próximo passo**; as skills de estágio executam. Não substitui nenhuma skill — referencia.

## 1. Detectar o estágio real (sempre primeiro)

Antes de classificar, olhe o que já existe:

- `docs/superpowers/{specs,plans,handoffs}` recentes — spec pronta = não reclarificar; plano pronto = ir pra implementação; handoff recente = retomar dali.
- `git log`/`git status` — código meio feito indica estágio implementar/revisar.

Se a tarefa já está em andamento: diga em que estágio ela está, com a evidência, e proponha a rota a partir dali. Nunca reexecute fase cumprida.

## 2. Classificar a intenção

| Classe | Rota |
|---|---|
| Feature nova | mapear? → clarificar → especificar → checkpoint → quebrar → implementar → revisar → entregar → capturar |
| Bug | mapear? → diagnosticar → implementar (fix) → revisar → entregar → capturar |
| Investigação | mapear → diagnosticar → relatório/handoff (termina aqui — não force implementação) |
| Spec-de-fora (ticket/US) | clarificar (consumer-simulation como apoio) → especificar/refinar → quebrar → segue como feature |
| Refactor | mapear → clarificar escopo → implementar → revisar → entregar → capturar |

`mapear?` = só se o codebase for desconhecido. **Rota mínima é legítima**: em tarefa pequena, proponha pular estágios explicitamente ("bug trivial: sugiro implementar→revisar→entregar") e deixe o usuário confirmar.

## 3. Estágios → skills

| Estágio | Skill | Fallback sem superpowers | Saída |
|---|---|---|---|
| Mapear | `core:archaeology` | — | mapa com citações |
| Diagnosticar | `superpowers:systematic-debugging` (+ `core:schrodinger` se >1 hipótese viva) | `core:schrodinger` + protocolo de debugging do always-on | causa raiz com evidência |
| Clarificar | `superpowers:brainstorming` ou `core:grill-me` | `core:grill-me` | decisões acordadas |
| Especificar/refinar | brainstorming (spec) ou `core:spec-refine` | `core:spec-refine` | spec em `docs/superpowers/specs/` |
| Checkpoint | `core:advisor-check` post-plan | — | veredito |
| Quebrar | `superpowers:writing-plans` ou `core:tech-breakdown` | `core:tech-breakdown` | plano em `docs/superpowers/plans/` |
| Implementar | `superpowers:executing-plans` ou subagent-driven | execução direta com o gate do projeto | código + commits |
| Revisar | `core:review-local` + `core:advisor-check` pre-done | — | findings resolvidos |
| Entregar | `core:commit` → `core:pr` | — | commit/PR |
| Capturar | `core:learn` + `core:compound` | — | memória + handoff |

Skills marcadas `core:*` slash-only (`archaeology`, `spec-refine`, `advisor-check`, `tech-breakdown`, `review-local`, `commit`, `pr`, `compound`): recomende o comando exato (`/core:<nome>`) pro usuário disparar — a tool Skill não as invoca.

## 4. Regras de condução

- **Um estágio por vez.** Ao fechar um estágio, recomende as 2-3 próximas rotas com 1 linha de porquê — e PARE. Nunca invoque o próximo estágio sem confirmação do usuário.
- **Estado = artefatos.** O progresso mora nos artefatos (specs/plans/handoffs) — não crie marcador ou arquivo de estado próprio.
- **Disciplina de sessão.** Uma fase pesada por sessão: *clarificar/especificar* · *implementar* · *revisar/entregar* · *fechar*. Ao cruzar de fase pesada, recomende sessão nova com handoff; o `plan-autoload` reabre o contexto.
- **Fechar sempre captura.** Fim de trabalho relevante → `core:learn` (se houve correções/decisões) + handoff proporcional ao trabalho da sessão.
````

- [ ] **Step 2: Validar estrutura**

Run: `cd "$HOME/dev/agent-kit" && claude plugin validate . && wc -l plugins/core/skills/pipeline/SKILL.md`
Expected: validation passa (mesmos 3 warnings pré-existentes); ≤120 linhas.

- [ ] **Step 3: Smoke de disparo (aceite §5.2 da spec, aproximado)**

Run: `claude --plugin-dir "$HOME/dev/agent-kit/plugins/core" -p "tenho uma feature nova pra começar nesse app e não sei por onde começar"`
Expected: resposta menciona condução por estágios/classes (evidência de que a description roteou) — ou invoca a skill pipeline explicitamente.

- [ ] **Step 4: Smoke de meia-entrada (aceite §5.3 da spec)**

```bash
FIX="${TMPDIR:-/tmp}/pipeline-midentry" && rm -rf "$FIX" && mkdir -p "$FIX/docs/superpowers/specs" && cd "$FIX" && git init -q
cat > docs/superpowers/specs/2026-07-06-favoritos-design.md << 'EOF'
# Feature Favoritos — Design
**Status:** aprovado. Requisitos: usuário marca/desmarca item como favorito; lista persiste localmente; badge com contagem no header.
EOF
claude --plugin-dir "$HOME/dev/agent-kit/plugins/core" -p "quero continuar o trabalho da feature de favoritos"
```
Expected: resposta reconhece a spec existente e propõe o estágio seguinte (checkpoint/quebrar/implementar) — NÃO propõe reclarificar/re-especificar do zero.

- [ ] **Step 5: Gate + commit**

```bash
cd "$HOME/dev/agent-kit"
scripts/check-provenance.sh && claude plugin validate . && evals/run-evals.sh
git add plugins/core/skills/pipeline/SKILL.md
git commit -m "feat(core): pipeline skill — conversational-flows conductor over existing skills"
```
Expected: gate 3× verde (evals 23/23); commit criado.

### Task 2: README + CHANGELOG

**Files:**
- Modify: `README.md` (3 edits: contagem/lista de invocáveis; linha na tabela; nota superpowers)
- Modify: `CHANGELOG.md` (1 bullet)

**Interfaces:**
- Consumes: nome `pipeline` e vocabulário de estágios da Task 1.

- [ ] **Step 1: README — contagem e lista de invocáveis**

Edit (old→new), preservando o restante da linha:
- `**Skills (16)** — \`plugins/core/skills/<nome>/SKILL.md\`. 7 são invocáveis pelo modelo via tool Skill (\`chat-draft\`, \`epicurus\`, \`grill-me\`, \`learn\`, \`methodology\`, \`schrodinger\`, \`using-agent-kit\`)` → `**Skills (17)** — \`plugins/core/skills/<nome>/SKILL.md\`. 8 são invocáveis pelo modelo via tool Skill (\`chat-draft\`, \`epicurus\`, \`grill-me\`, \`learn\`, \`methodology\`, \`pipeline\`, \`schrodinger\`, \`using-agent-kit\`)`

- [ ] **Step 2: README — linha na tabela de skills**

Inserir após a linha da `methodology`:
`| \`pipeline\` | condutor de fluxo: detecta o estágio real, classifica a intenção (feature/bug/investigação/spec-de-fora/refactor) e roteia pelas skills um estágio por vez — camada de routing do kit |`

- [ ] **Step 3: README — nota superpowers (fecha o polimento (b) pendente)**

Inserir parágrafo após "`core` não depende de `mobile` e serve qualquer stack. `mobile` pressupõe `core` instalado (usa as mesmas convenções de skill/hook) e só é útil em projetos Flutter/Dart.":
`Alguns fluxos do \`core\` referenciam skills do marketplace \`superpowers\` (brainstorming, writing-plans, systematic-debugging, executing-plans). Sem ele instalado nada quebra: \`core:pipeline\` indica o fallback interno equivalente de cada estágio (grill-me, tech-breakdown, schrodinger, execução direta com gate).`

- [ ] **Step 4: CHANGELOG — bullet em ### Adicionado**

Inserir após o bullet `- README.md completo (...)`:
`- \`core:pipeline\` — condutor de fluxo (camada de routing conversacional): detecção de estágio, 5 classes de tarefa com rotas, tabela estágio→skill com fallbacks sem superpowers, disciplina de sessão. Spec: \`docs/superpowers/specs/2026-07-06-conversational-flows-pipeline-design.md\``

- [ ] **Step 5: Gate + commit**

```bash
cd "$HOME/dev/agent-kit"
scripts/check-provenance.sh && claude plugin validate . && evals/run-evals.sh
git add README.md CHANGELOG.md
git commit -m "docs: README/CHANGELOG for core:pipeline (17 skills, superpowers fallback note)"
```
Expected: gate verde; commit criado.

### Task 3: Ponta pessoal — `~/.claude/CLAUDE.md` (fora do repo, sem commit)

**Files:**
- Modify: `~/.claude/CLAUDE.md` (append de seção)

- [ ] **Step 1: Append da seção (conteúdo integral)**

```markdown

## Fluxos (entrada rápida)

Trabalho novo substancial → `core:pipeline` conduz (detecta estágio, classifica, roteia). Telegrama das rotas:

| Intenção | Rota |
|---|---|
| Feature nova | clarificar → especificar → quebrar → implementar → revisar → entregar |
| Bug | diagnosticar → fix → revisar → entregar |
| Investigação | mapear → diagnosticar → handoff (para aqui) |
| Ticket/US de fora | clarificar → refinar → quebrar → segue como feature |
| Fim de sessão relevante | `core:learn` + handoff |

**Meu contrato de prompting**: abro com intenção crua + resultado esperado; classe se eu souber; não estruturo — o pipeline extrai o resto; decisões via AskUserQuestion.
```

- [ ] **Step 2: Verificar**

Run: `tail -20 ~/.claude/CLAUDE.md`
Expected: seção presente, tabela íntegra.

### Task 4: Push + propagação + registro

- [ ] **Step 1: Push (com aprovação explícita do usuário)**

Run: `git push`
Expected: main atualizada no remote.

- [ ] **Step 2: Propagar pro cache**

Run: `claude plugin update core@agent-kit`
Expected: cache atualizado pro novo HEAD; lembrar: reinício de sessão aplica.

- [ ] **Step 3: Atualizar memória**

Na memória de projeto da extração do kit (store do workspace de origem, fora deste repo), atualizar a linha de estado wired do core: 16→17 skills (inclui `pipeline`, condutor de fluxo, model-invocable), HEAD novo, e nota de que o polimento (b) (nota superpowers no README) foi fechado — restando só o (a) (`description` no marketplace.json).
