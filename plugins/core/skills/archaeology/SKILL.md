---
name: archaeology
description: Invoque para mapear o estado atual do código antes de qualquer planejamento técnico numa US, ticket ou domínio com histórico no app — dispatch de agentes de exploração em paralelo, mapa arqueológico consolidado com decisões ranqueadas por severidade.
disable-model-invocation: true
---

# archaeology — Pre-US Codebase Map

Mapa arqueológico do estado atual do app para uma US ou domínio — antes de qualquer planejamento técnico. Entrega: TL;DR, decisões necessárias ranked, tabela cross-dimensão por módulo, evidência por dimensão e oportunidades de melhoria.

## Config do projeto

Este skill assume que o projeto consumidor define:
- **Padrão de ticket ID** — regex usado na regra de detecção (ex.: `^ACME-\d+$`, `^PROJ-\d+$`). Sem essa config, trate qualquer token que pareça um identificador de ticket do tracker do projeto como modo **ticket**.
- **Diretório de módulos** — onde vivem as features (ex.: `src/modules/`, `src/features/`). Usado no passo 1 para listar módulos candidatos.
- **Diretório(s) de SDK/pacote compartilhado** — se o projeto separa chamadas de API em um pacote próprio (ex.: um SDK de repositórios), informe o caminho para a Dimensão C.

**Posição no workflow:**
```
archaeology <US | ticket | domínio>   ← você está aqui
        ↓
core:tech-breakdown                    ← recebe o mapa como contexto (modo US/ticket)
        ↓
core:spec-refine
```

## Quando Usar

Execute **antes** de `core:tech-breakdown` (se disponível neste kit) sempre que a US tocar funcionalidade que:
- Tem histórico no app (não é feature totalmente nova)
- Cruza múltiplos módulos
- Tem suspeita de legado, duplicação ou N implementações paralelas

Também execute **sem US** para mapear um domínio inteiro como referência arquitetural (`archaeology busca`, `archaeology checkout`). Nesse modo o output não vira tech breakdown — é referência pra decisões futuras e abertura de tickets de débito.

Exemplos típicos: busca, filtros, checkout, perfil, autenticação.

Não usar em features 100% novas sem código existente relacionado.

## Input

O usuário fornece uma das opções:

- **Texto da US**: cola a descrição completa no chat
- **Ticket ID**: `archaeology PROJ-608692` — busca via MCP/tracker do projeto
- **Domínio livre**: `archaeology busca` — exploração arquitetural sem US

### Regra de detecção (determinística)

| Input recebido | Modo |
|---|---|
| Match no padrão de ticket ID do projeto (config acima) | **ticket** — fetch via tool de tracker disponível na sessão |
| Token único, sem whitespace/newline (`busca`, `checkout`, `perfil`) | **domínio livre** |
| Multi-linha OU contém marcadores de US (`Como `, `Critérios de aceite`, `Dado que`, `História do usuário`) | **US text** |
| Ambíguo (ex: frase curta tipo "fluxo de busca") | **perguntar** ao usuário qual modo |

Se nenhum input for fornecido: perguntar "Qual US, ticket ou domínio deseja mapear?"

## Steps

### 1. Extrair vocabulário + grep patterns

A partir do input, extraia:
- **Termos primários**: nomes de features, fluxos, entidades
- **Termos de código**: controllers, stores, repos que provavelmente existem
- **Módulos candidatos**: quais módulos no diretório de módulos do projeto (config) provavelmente têm código relacionado
- **Grep patterns**: regex/glob concretos que cada agente vai usar

Apresente ao usuário antes de disparar os agentes — formato completo: `REFERENCE.md` §1.

Aguarde confirmação antes de avançar. Termos errados contaminam todos os 4 agentes.

### 2. Dispatch 4 agentes Explore em paralelo

Dispare **4 agentes Explore em paralelo** (`subagent_type: "Explore"`), um por dimensão — A: Entry Points, B: Controllers e Stores, C: Repositórios e Endpoints, D: Duplicação. Passe os termos, módulos e patterns confirmados no passo 1.

Cada agente entrega **evidência crua + cita `arquivo:linha`**, sem classificar como "shared", "risco" ou "oportunidade" — isso é trabalho do consolidador no passo 3. Instruções detalhadas de cada dimensão: `REFERENCE.md` §2.

### 3. Consolidação — estrutura prescritiva

Com os 4 outputs em mãos, sintetize o mapa nesta ordem fixa (não improvise seções): **TL;DR → Decisões necessárias → Visão Consolidada por Módulo → Evidência por Dimensão → Oportunidades de Melhoria → Outras perguntas em aberto**.

Template completo da estrutura + regras obrigatórias do consolidador (ordem fixa, TL;DR escrito por último, dedup em Oportunidades, citação `arquivo:linha` obrigatória, ranking limitado a 5 itens): `REFERENCE.md` §3.

### 4. Salvar o mapa

Salve em `docs/superpowers/archaeology/`:

- Modo ticket / US text: `YYYY-MM-DD-<dominio>.md` (ex: `2026-05-26-busca-unificada.md`)
- Modo domínio livre: `YYYY-MM-DD-dominio-<dominio>.md` (ex: `2026-05-26-dominio-checkout.md`)

O prefixo `dominio-` deixa explícito que é exploração arquitetural, não pré-US.

### 5. Handoff condicional

Modo ticket/US text: recomende `core:tech-breakdown <ticket>` (se disponível) e pergunte se inicia agora ou se o usuário prefere revisar o mapa antes. Modo domínio livre: não há tech breakdown sem US — sugira usar como referência e abrir tickets de follow-up pras Oportunidades de severidade Alta. Mensagens completas: `REFERENCE.md` §5.

## Regras invioláveis

- Nunca classifique código como legado sem verificar caller ativo (grep por instanciação via DI ou instância direta na page).
- Achados sem evidência — cada item em Oportunidades cita `arquivo:linha`. Sem citação, é inferência — corte.
- Seções improvisadas — se você está prestes a criar uma seção que não está no template (`Features a Remover`, `Analytics Atual`, etc.), pare e enfie o conteúdo em **Oportunidades** com label apropriado.
- Modo **domínio livre** não dispara handoff pra `core:tech-breakdown` — é referência arquitetural, não pré-US.
- Se o domínio cruzar mais de 6 módulos, pergunte ao usuário se quer escopo reduzido antes do dispatch.

Lista completa de sinais de gordura a cortar e notas adicionais: `REFERENCE.md` §6 e §7.
