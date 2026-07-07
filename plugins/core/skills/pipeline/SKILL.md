---
name: pipeline
description: Invoque ao receber uma intenção crua de trabalho substancial (feature, bug, investigação, refactor, ticket/US) sem fluxo em andamento definido, ou quando o usuário pedir "por onde começo", "qual o fluxo pra isso", "me conduz nesse trabalho". NÃO invoque para pergunta conceitual ou lookup pontual ("como funciona X?"), nem quando já há um fluxo em andamento (brainstorming, plano em execução, review). Condutor de fluxo — detecta o estágio real da tarefa, classifica a intenção e roteia pelas skills do kit um estágio por vez; recomenda a próxima rota, nunca executa a cadeia inteira sozinho.
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

Notas de estágio:
- Terminal de Investigação ("relatório/handoff"): produzido via `core:compound` (handoff) ou handoff manual proporcional — não há skill própria.
- `consumer-simulation` é um AGENT, não skill: dispatch como subagente (tool Agent), passando SÓ o texto do ticket + critérios de aceite, nunca a implementação.
- Revisar num projeto com o plugin mobile instalado: some `mobile:refactor-review` quando a mudança for refactor.

## 4. Regras de condução

- **Um estágio por vez.** Ao fechar um estágio, recomende as 2-3 próximas rotas com 1 linha de porquê — e PARE. Nunca invoque o próximo estágio sem confirmação do usuário.
- **Coordenação com superpowers.** Se um fluxo superpowers já está ativo (brainstorming em curso, plano em execução), NÃO assuma a condução: faça só a detecção de estágio, se útil, e defira à skill de estágio ativa.
- **Estado = artefatos.** O progresso mora nos artefatos (specs/plans/handoffs) — não crie marcador ou arquivo de estado próprio.
- **Disciplina de sessão.** Uma fase pesada por sessão: *clarificar/especificar* · *implementar* · *revisar/entregar* · *fechar*. Ao cruzar de fase pesada, recomende sessão nova com handoff; o `plan-autoload` reabre planos/handoffs — specs são detectadas pela seção 1 desta skill.
- **Fechar sempre captura.** Fim de trabalho relevante → `core:learn` (se houve correções/decisões) + handoff proporcional ao trabalho da sessão.
