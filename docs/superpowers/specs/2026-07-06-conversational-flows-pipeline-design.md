# core:pipeline — camada de fluxos conversacionais

**Data:** 2026-07-06 · **Status:** design aprovado em sessão · **Origem:** dúvida do usuário sobre a própria forma de escrever prompts + conceito de Conversational Flows (separar intenção/routing/execução) + inspiração no ACT Lite (pipeline de fases com roteamento humano explícito).

---

## 1. Problema

Apps conversacionais degeneram num loop gigante que mistura lógica de negócio, routing e prompts. A interação com o Claude Code tem a mesma anatomia: a mensagem do usuário carrega intenção **e** routing **e** instruções de execução, misturados. O kit já separa a execução (skills), mas o **routing é 100% memória do usuário**: 9 das 16 skills do core são slash-only — o mesmo failure mode que matou as posturas no projeto de origem ("gatilhos ~0 conversão; depende de eu lembrar").

A dúvida do usuário — "minha forma de escrever prompts é boa?" — se responde por arquitetura, não por template: a mensagem dele deve carregar **só intenção** (curta e crua, como já escreve); a estrutura é responsabilidade do sistema.

## 2. Decisões travadas

| # | Decisão | Escolha |
|---|---|---|
| 1 | Forma | Pipeline **coerente com o que já existe** — skills atuais viram estágios referenciados, nenhuma é modificada (grill-me explicitamente intocado) |
| 2 | Roteamento de transição | **Centralizado no condutor** (`core:pipeline`), não distribuído em exit-routes dentro das skills |
| 3 | Invocação | **Model-invocable** (description com gatilhos) + `/core:pipeline` explícito |
| 4 | Estado entre sessões | Só pelos artefatos existentes (`docs/superpowers/{specs,plans,handoffs}` + `plan-autoload`) — sem marcador/arquivo novo |
| 5 | Entrada no meio | Condutor sempre detecta o estágio real (artefatos recentes + git log/status) antes de classificar — nunca repete fase |
| 6 | Superpowers | Estágios que o referenciam ganham **fallback nomeado** pra skill do próprio kit; resolve também o polimento pendente "core assume superpowers" |
| 7 | Ponta de entrada pessoal | Tabela intenção→fluxo + contrato de prompting no `~/.claude/CLAUDE.md` do usuário — fora do kit, fora do teto de 200 do always-on |
| 8 | Admissão | Wired por **função estrutural** (camada de routing), decisão do dono da governança; valor real medido na métrica de 2 semanas |

## 3. Arquitetura — três camadas

**Intenção** (usuário): mensagem curta e crua + resultado esperado. Nada de template.

**Routing** (sistema, 3 pontas):
- *Entrada:* descriptions das skills (já existe) + tabela pessoal no CLAUDE.md do usuário (sempre carregada).
- *Condução:* `core:pipeline` — classifica, conduz, roteia transições.
- *Transição:* ao fim de cada estágio o condutor recomenda as 2-3 próximas rotas. **Nunca auto-invoca** o estágio seguinte (regra ACT).

**Execução** (skills existentes): cada uma dona do seu "como", intocadas.

### 3.1 A skill `core:pipeline`

Frontmatter: `name: pipeline`, description com gatilhos ("tarefa nova substancial", "por onde começo", "me conduz nesse trabalho", "qual o fluxo pra isso"), model-invocable (sem `disable-model-invocation`).

Corpo, em 4 seções:

**(a) Detecção de estágio (sempre primeiro).** Antes de classificar: olhar `docs/superpowers/{specs,plans,handoffs}` recentes e `git log/status`. Se a tarefa já está em andamento, entrar no estágio real e dizer qual é — nunca reexecutar fase já cumprida.

**(b) Classes de tarefa e rotas.**

| Classe | Rota (estágios) |
|---|---|
| Feature nova | mapear? → clarificar → especificar → checkpoint → quebrar → implementar → revisar → entregar → capturar |
| Bug | mapear? → diagnosticar → implementar (fix) → revisar → entregar → capturar |
| Investigação | mapear → diagnosticar → relatório/handoff (para aqui; não força implementação) |
| Spec-de-fora (ticket/US) | clarificar (consumer-simulation como apoio) → refinar spec → quebrar → … como feature |
| Refactor | mapear → clarificar escopo → implementar → revisar (refactor-review no mobile) → entregar → capturar |

Estágios com `?` são condicionais (codebase desconhecido). Rota mínima é legítima: bug pequeno pode ir direto a fix→revisar→entregar — o condutor propõe pular, o usuário confirma.

**(c) Tabela de estágios → skill.**

| Estágio | Skill | Fallback sem superpowers | Saída |
|---|---|---|---|
| Mapear | `core:archaeology` | — | mapa com citações |
| Diagnosticar | `superpowers:systematic-debugging`, com `core:schrodinger` se houver >1 hipótese viva | `core:schrodinger` + protocolo de debugging do always-on | causa raiz com evidência |
| Clarificar | `superpowers:brainstorming` ou `core:grill-me` | `core:grill-me` | decisões acordadas |
| Especificar/refinar | brainstorming (spec) ou `core:spec-refine` | `core:spec-refine` | spec em `docs/superpowers/specs/` |
| Checkpoint | `core:advisor-check` post-plan | — | veredito |
| Quebrar | `superpowers:writing-plans` ou `core:tech-breakdown` | `core:tech-breakdown` | plano em `docs/superpowers/plans/` |
| Implementar | `superpowers:executing-plans`/subagent-driven | execução direta com gate do projeto | código+commits |
| Revisar | `core:review-local` + `core:advisor-check` pre-done | — | findings resolvidos |
| Entregar | `core:commit` → `core:pr` | — | commit/PR |
| Capturar | `core:learn` + `core:compound` | — | memória + handoff |

**(d) Disciplina de sessão.** Tipos nomeados: *clarificar/especificar* · *implementar* · *revisar/entregar* · *fechar*. Regra: uma fase pesada por sessão; fechar sempre com handoff (e `learn` se houve correções); a próxima sessão reabre via `plan-autoload`. É a resposta ao "giant loop": concerns separados por sessão, não empilhados.

### 3.2 Ponta pessoal (fora do kit)

Seção no `~/.claude/CLAUDE.md` do usuário:
- Tabela intenção→fluxo (~6 linhas espelhando 3.1b, versão telegráfica).
- Contrato de prompting (3 linhas): *abro com intenção crua + resultado esperado; classe se eu souber; não estruturo — o pipeline extrai o resto; decisões via AskUserQuestion.*

Não é artefato do repo; é passo de adoção pessoal documentado nesta spec.

## 4. Inventário de mudança

1. **Novo:** `plugins/core/skills/pipeline/SKILL.md` (única peça nova; alvo ≤120 linhas).
2. **README:** mapa do core passa a 17 skills / 8 model-invocable; linha na tabela de skills; nota "core assume superpowers, com fallbacks nomeados no pipeline" (fecha o polimento (b) pendente).
3. **CHANGELOG:** entrada.
4. **Pessoal (fora do repo):** seção no `~/.claude/CLAUDE.md`.

Zero mudança em skills/hooks/scripts existentes. Zero always-on novo no kit.

## 5. Aceite

1. `claude plugin validate .` + `check-provenance.sh` + evals verdes (23/23 — sem casos novos; skill é prosa).
2. Teste de disparo: sessão nova com intenção crua de tarefa substancial → pipeline entra (ou é sugerido) sem o usuário digitar `/core:pipeline`.
3. Teste de meia-entrada: sessão sobre tarefa com spec já existente → condutor detecta e propõe o estágio seguinte, não reclarifica.
4. README/CHANGELOG consistentes com o disco.
5. **Valor real:** usado de ponta a ponta na primeira tarefa do primeiro projeto novo (mesma métrica de 2 semanas do kit — se o pipeline não for usado lá, é candidato a unwired, pelas próprias regras).

## 6. Riscos

| Risco | Mitigação |
|---|---|
| Condutor vira burocracia em tarefa pequena | Rota mínima explícita por classe; condutor propõe pular estágios; usuário sempre confirma |
| Mais uma skill que "depende de lembrar" | Model-invocable com gatilhos de intenção + tabela no CLAUDE.md pessoal (sempre carregada) |
| Sobreposição com superpowers (brainstorming já roteia) | Pipeline referencia superpowers como estágio, não compete; fallbacks pro kit standalone |
| Auto-invocação em cascata (condutor dispara tudo sozinho) | Regra ACT explícita no corpo: recomendar, nunca invocar o próximo estágio sem confirmação |
