---
name: refine-async
description: Triage pós-refinamento — consolida o contexto salvo pelo /core:refine-live, roda exploração leve do codebase (grep orçado, sem arquitetura profunda) e gera subtarefas [INTERIM] para aprovação e criação no board. Use logo após a agenda de refinamento, antes do pipeline técnico (archaeology → tech-breakdown).
disable-model-invocation: true
---

# /refine-async -- Triage Pós-Refinamento

Processamento assíncrono após a agenda de refinamento. Consolida o contexto capturado no `/core:refine-live`, executa exploração leve do codebase, gera subtarefas para aprovação e cria no board.

**Posição no workflow:**
```
/core:refine-live <card-id>                ← durante a agenda
        ↓
/core:refine-async <card-id>               ← você está aqui (pós-agenda)
        ↓
archaeology → tech-breakdown → spec-refine → plano
```

## Quando Usar

Execute **após a agenda de refinamento**, quando o `/core:refine-live` já consolidou o contexto da US. Pode ser imediatamente depois (mesma sessão) ou em outro momento (lê do state file).

Não usar para: exploração arquitetural profunda (use `/core:archaeology`), decomposição técnica detalhada (use `/core:tech-breakdown`), stress-test de spec (use `/core:spec-refine`).

## Input

```
/core:refine-async <TICKET>
/core:refine-async <card-id-numérico>
```

Aceita os mesmos formatos de card ID do `/core:refine-live`.

## Steps

### 1. Carregar estado do live

Busque o state file em `docs/refine/refine-<card-id>.md`:
- Tente primeiro com external_id: `refine-<TICKET>.md`
- Se não encontrado, tente com numérico: `refine-<card-id-numérico>.md`
- Se encontrado: carregue e apresente resumo ("Encontrei o contexto do live: [título], [N bullets], [N gaps pendentes]")
- Se **não encontrado em nenhum formato**: pergunte ao usuário se deseja:
  - (a) Fornecer o contexto manualmente (colar resumo)
  - (b) Rodar sem contexto prévio (apenas card do board)

Se opção (b): busque card via a tool do MCP de board do projeto consumidor (este kit não embute nenhum — adapte ao servidor real conectado na sessão) e use apenas título + descrição como base.

### 2. Light grep — exploração leve do codebase

Com base nos termos do card (título, contexto do PO, módulos mencionados), execute exploração leve:

**Budget:**
- Máximo **10 grep queries**
- Tempo total < **30 segundos**
- Foco em **confirmar existência** (não mapear arquitetura)
- Se atingir budget antes de completar: pare e reporte o que encontrou até então

**O que buscar** (tools do Claude Code — `Glob`/`Grep`, não as APIs de IDE do projeto de origem):
| Alvo | Exemplo |
|---|---|
| Módulo/feature existe? | `Glob("**/*<feature>*")` |
| Store/Controller existe? | `Grep("<Feature>Store\|<Feature>Controller")` |
| Endpoint/Repository existe? | `Grep("<feature>Repository\|<feature>DataSource")` |
| Rota existe? | `Grep("<RoutesTable>.*<feature>")` |

**Output do grep** — resumo conciso:
```
🔍 Exploração leve:
- ✅ Módulo `<feature_module>` existe em lib/src/modules/<feature_module>/
- ✅ <FeatureX>Store encontrado (<feature>_store.dart)
- ❌ Endpoint de recomendação NÃO encontrado no repositório de dados
- ⚠️ Rota existente: <RoutesTable>.<feature> (escopo restrito)
```

### 3. Gerar subtarefas [INTERIM]

Com base no contexto consolidado (live + grep), gere subtarefas para a US:

**Regras de geração:**
- Cada subtarefa é uma unidade de trabalho independente ou sequencial
- Título: verbo no imperativo + escopo claro (ex: "Criar endpoint X no backend")
- Descrição: 2-3 linhas com o que precisa ser feito
- Tag: `[INTERIM]` — subtarefas são ponto de partida, não verdade final
- Sem acceptance criteria detalhado (isso é pra `/core:tech-breakdown`)
- Sem estimativa de tempo

**Formato de apresentação:**

```
## Subtarefas propostas — <TICKET> [INTERIM]

1. **Criar endpoint de recomendação no backend**
   Endpoint que retorna itens relacionados ao contexto atual.
   Dependência: definição de regra de elegibilidade com PO.

2. **Implementar <Feature>Repository + DataSource**
   Integração com o novo endpoint. Usar padrão de erro do projeto (ex.: Either<Failure, T>).

3. **Criar UI da feature na tela alvo**
   Componente do design system com lista/seção de itens recomendados.
   Ref: módulo `<feature_module>` existente (se houver) pode ser reutilizado.

4. **[QA] Testes de integração da feature**
   Validar fluxo completo ponta a ponta.

---
Aprovar? Opções:
- `aprovar tudo` — crio todas no board
- `aprovar N` — selecione quais (ex: "aprovar 1,2,3")
- `editar N` — peça alteração em subtarefa específica
- `refazer` — regenero com novas instruções
```

### 4. Aprovação + Criação no board

**Depende de um MCP de board/kanban específico do projeto consumidor — este kit não inclui nenhum.** Após aprovação do usuário:

1. **Tente criar via a tool do MCP de board**: batch de criação de subtarefa com as subtarefas aprovadas, adaptado ao servidor real conectado na sessão
2. **Se não houver MCP de board conectado, ou a chamada falhar** (indisponível, erro, permissão): exporte como texto formatado:

```
⚠️ API do board indisponível. Subtarefas prontas para criação manual:

□ Criar endpoint de recomendação no backend
□ Implementar <Feature>Repository + DataSource
□ Criar UI da feature na tela alvo
□ [QA] Testes de integração da feature
```

3. **Não retry**: reportar falha, sem retry automático.

### 5. Sinal de pipeline

Após subtarefas criadas (ou exportadas), pergunte:

```
## Próximo passo

Esta US está pronta para entrar no pipeline técnico?

- `pronta` — pode rodar `/core:archaeology` → `/core:tech-breakdown` quando um dev pegar
- `bloqueada` — ainda tem gaps que precisam do PO (liste quais)
- `parcial` — parte está pronta, parte precisa de esclarecimento

Qual o status?
```

Registre a resposta no state file.

### 6. Atualizar estado

Atualize o state file em `docs/refine/refine-<card-id>.md` (garanta que o diretório existe: `mkdir -p docs/refine`):

```markdown
## Async (adicionado)
- data_async: <YYYY-MM-DD>
- grep_findings: [resumo 1 linha por achado]
- subtarefas_criadas: [lista de títulos]
- subtarefas_rejeitadas: [lista, se houver]
- pipeline_status: pronta | bloqueada (motivo) | parcial (motivo)

## Status
- fase: async_done
- pronto_para_pipeline: <atualizado>
```

## Important

- **Triage, não arquitetura**: o objetivo é organizar a US em pedaços trabalháveis, não fazer design de solução. Isso é do `/core:tech-breakdown`.
- **Subtarefas são [INTERIM]**: vão ser refinadas quando o dev rodar o pipeline completo. Não trate como verdade final.
- **Approval gate obrigatório**: NUNCA crie subtarefas no board sem aprovação explícita do usuário.
- **Grep leve, não archaeology**: max 10 queries, max 30s. Se precisar de mais, sinalize: "Recomendo rodar `/core:archaeology` pra mapeamento completo."
- **Fallback gracioso**: sem MCP de board ou se a chamada falhar, exporte texto. Não bloqueie o workflow.
- **Sem spec detalhado**: não gere acceptance criteria, test plans, ou design docs. Esses são outputs de `/core:tech-breakdown` + `/core:spec-refine`.
- **Idempotência**: se rodar duas vezes no mesmo card, detecte subtarefas existentes e pergunte: "Subtarefas já existem no card. Adicionar novas ou substituir?"
- **`<TICKET>`, nomes de módulo/store/repositório e o board neste arquivo são placeholders** — adapte aos nomes reais do projeto consumidor ao usar esta skill; este kit não tem uma stack própria pra preencher aqui.
