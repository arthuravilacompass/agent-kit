---
name: refine-live
description: Copiloto ao vivo para a agenda de refinamento com o PO — recebe o card do board + bullets do PO em tempo real e gera perguntas de esclarecimento por prioridade (escopo, critérios implícitos, dependências). Use durante a call de refinamento; consolida estado pro /core:refine-async na sequência.
disable-model-invocation: true
---

# /refine-live -- Assistente de Refinamento ao Vivo

Copiloto para uso durante a agenda semanal de refinamento com o PO. Recebe o card do board + contexto verbal do PO em bullets, e gera perguntas de esclarecimento em tempo real para maximizar o entendimento da US.

**Posição no workflow:**
```
/refine-live <card-id>                     ← você está aqui (durante a agenda)
        ↓
/refine-async <card-id>                    ← pós-agenda (triage + subtarefas)
        ↓
archaeology → tech-breakdown → spec-refine → plano
```

(`archaeology`, `tech-breakdown`, `spec-refine` são skills do plugin `core` deste kit — ver `plugins/core/skills/`.)

## Quando Usar

Execute **durante a agenda de refinamento** quando o PO apresentar uma US. Use em paralelo com o PO falando — você digita bullets do que ele diz e a IA gera perguntas pra fazer na hora.

Não usar para: exploração técnica profunda (use `archaeology`), stress-test de spec (use `spec-refine`), decomposição em subtarefas (use `/refine-async`).

## Input

```
/refine-live <TICKET>
/refine-live <card-id-numérico>
```

Aceita:
- **Custom ID** (formato ticket do board, ex. `<TICKET>`): resolve via `search_cards(custom_id: "<TICKET>")`
- **Card ID numérico**: valida via `search_cards` no board ou tool equivalente de detalhe

## Steps

### 1. Fetch card do board

Busque o card via API do sistema de board/kanban do projeto:
- Se formato de ticket: use a busca com `custom_id` para obter o `card_id` numérico
- Se numérico: valide existência no board

Recupere: título e descrição (via tool de detalhe se disponível; se tool disabled, use apenas o resultado da busca + título).

Se card não encontrado: informe o usuário e peça pra confirmar o ID.

Apresente um resumo breve:
```
📋 Card: <TICKET> — "<título do card>"
Descrição: [primeiras 3 linhas ou "sem descrição"]

Pronto. Cole bullets do PO ou pergunte algo.
```

### 2. Bloco inicial de perguntas

Com base no título + descrição do card, gere **3-5 perguntas** organizadas por prioridade:

| Prioridade | Categoria | Exemplos |
|---|---|---|
| 1 | **Escopo/Contexto** | "Isso é extensão de feature existente ou nova?", "Afeta apenas uma plataforma?", "Qual(is) segmento(s)/marca(s)?" |
| 2 | **Critérios implícitos** | "Tem estado vazio/loading definido?", "O que acontece em erro?", "Funciona offline?" |
| 3 | **Dependências/Bloqueios** | "Precisa de endpoint novo do backend?", "Depende de outra US?", "Tem design/Figma pronto?" |

Formato de cada pergunta:
```
[Escopo] — <pergunta curta e direta>
```

Não exceda 5 perguntas neste bloco. O objetivo é ser rápido e digerível durante a call.

### 3. Modo incremental (loop principal)

O usuário cola bullets do que o PO está falando. Para cada input:

1. **Leia o bullet** — entenda o contexto adicionado
2. **Grep oportunístico** (opcional): se o bullet menciona módulo/tela/feature que pode existir no código, faça 1 grep rápido (<2s). Se confirmar existência, use na pergunta ("PO, isso é extensão do `<FeatureX>Store` que já temos, ou é fluxo novo?")
3. **Gere 1-2 perguntas adicionais** relevantes ao bullet — mantenha as 3 categorias prioritárias

Se o bullet é puramente informativo e não levanta dúvida, responda brevemente: "✓ Entendido. Próximo bullet ou pergunta?"

**Não faça no modo incremental:**
- Exploração pesada de código (>2s)
- Perguntas de edge case técnico (error paths, race conditions)
- Sugestão de implementação ou arquitetura
- Geração de subtarefas

### 4. "fecha" — Consolidação

Quando o usuário digita **"fecha"**, consolide o estado da sessão:

1. Gere o resumo estruturado abaixo
2. Salve em `docs/refine/refine-<card-id>.md` (garanta que o diretório existe: `mkdir -p docs/refine`; use o external_id se disponível, ex: `refine-<TICKET>.md`)
3. Confirme ao usuário: "Estado salvo. Pode rodar `/refine-async <TICKET>` quando quiser."

**Schema do estado:**

```markdown
# Refine: <external_id>

## Card
- title: <título do card>
- card_id: <numérico>
- external_id: <TICKET>
- board: <BOARD_NAME>

## Contexto do PO
- <bullet 1>
- <bullet 2>
- ...

## Perguntas Feitas
- Q: <pergunta> → A: <resposta do PO | "sem resposta">
- ...

## Gaps Pendentes
- <perguntas não respondidas ou temas que ficaram em aberto>

## Status
- fase: live_closed
- pronto_para_pipeline: <sim | não (motivo)>
- data: <YYYY-MM-DD>
```

A sessão continua ativa após "fecha" — o usuário pode rodar outro `/refine-live` com outro card ID.

## Important

- **Velocidade > completude**: perguntas curtas, diretas, 1 linha. O PO está falando — você não pode gerar parágrafos.
- **Sem jargão técnico nas perguntas**: o PO é de negócio. Pergunte sobre comportamento esperado, não sobre stores/repositories.
- **Sem codebase exploration pesada**: grep oportunístico ok (<2s). Qualquer coisa além disso, deixe pro async.
- **Sem subtarefas**: geração de subtarefas é responsabilidade do `/refine-async`.
- **Sem spec-level questions**: error paths, race conditions, state transitions complexas → `spec-refine` faz isso melhor com contexto completo.
- **Uma US por invocação**: não misture contexto de cards diferentes na mesma chamada.
