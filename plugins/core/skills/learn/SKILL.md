---
name: learn
description: Invoque quando o usuário disser "salva isso", "captura esse aprendizado", "usa a skill learn", ou antes de um /clear ou compact quando a sessão acumulou correções e decisões não capturadas — escaneia a conversa e propõe entries de memória para aprovação.
---

Escaneie a conversa atual (ou as últimas N mensagens se especificado) por correções, preferências estabelecidas, fatos de domínio e decisões. Proponha entries estruturados pra memory tipada com aprovação inline. Grave apenas o aprovado.

## Quando usar

- Usuário pede explicitamente: "use skill learn", "salva esse aprendizado", "captura isso".
- Sessão longa onde correções acumularam sem captura inline.
- Antes de `/clear` ou compact se mudanças não-triviais foram discutidas.

## Caminhos do sistema de memory

- **Memory dir:** o diretório de memória do projeto atual (informado no system prompt da sessão).
- **Index:** `MEMORY.md` (always loaded; 200-line limit)
- **Nome do arquivo:** `{type}_{snake_case_name}.md`
- **Types:** `feedback` | `reference` | `project` | `user`

## Steps

### 1. Escanear conversa por sinais (pt-BR + EN)

| Sinal | Exemplos pt-BR | Exemplos EN |
|---|---|---|
| **Correções explícitas** | não, não é assim, errado, na verdade, aliás, pivota, corrige, revisita, na realidade | no, don't do that, actually, instead, wrong, not like that |
| **Preferências** | sempre use X, nunca faça Y, daqui pra frente, prefiro, lembra de | always use X, never do Y, from now on, I prefer, remember to |
| **Domain knowledge** | fatos técnicos sobre APIs, arquitetura, regras de negócio explicados durante a conversa | (same — technical content is usually language-mixed) |
| **Decisões** | escolhas de arquitetura, decisões de processo, abordagens confirmadas | architecture choices, process decisions, confirmed approaches |
| **Comportamentos confirmados** | isso, perfeito, continua assim, exato — após approach não-óbvia | yes exactly, perfect, keep doing that |

Default scope: conversa inteira até `/clear` mais recente. Se usuário pediu "últimas N mensagens", limitar.

Se nenhum sinal: reportar *"Nenhum aprendizado detectado nesta sessão."* e parar.

### 2. Categorizar cada finding

| Finding | Memory type |
|---|---|
| Correção de comportamento, preferência de estilo/workflow | `feedback` |
| Fatos de API, padrões arquiteturais, regras de negócio, convenções | `reference` |
| Status de sprint, escopo de ticket, decisões de projeto, prazos | `project` |
| Preferências de ferramenta pessoal, settings | `user` |

### 3. Checar duplicatas

Ler `MEMORY.md`. Para cada proposta:
- Comparar semanticamente vs nomes/descrições existentes.
- Conceito idêntico → skip (marcar como duplicate).
- Versão nova adiciona detalhe útil → propor **atualização** do arquivo existente (mostrar diff).

### 4. Apresentar pra aprovação

Lista numerada: título, type, descrição de 1 linha. Aguardar aprovação. Por item:
- `approve` / `aprova` → escreve
- `edit [o que mudar]` → ajusta
- `skip` / `pula` → ignora

Não escrever sem aprovação.

### 5. Gravar entries aprovados

Para cada aprovado, em sequência:

**a. Criar/atualizar arquivo:**
No diretório de memória do projeto atual (informado no system prompt da sessão):
```
{memory_dir}/{type}_{snake_case_name}.md
```

Frontmatter exato (sem campos extras):
```markdown
---
name: Título humano
description: Sumário 1-linha pro MEMORY.md index
type: feedback
---

[Parágrafo diretivo]

**Why:** [Explicação]

**How to apply:** [Guidance concreto]
```

**b. Atualizar `MEMORY.md` index:**
- Achar seção que casa o type: `## Feedback`, `## Reference`, `## Project`, `## User`.
- Adicionar bullet: `- [Nome](filename.md) — Descrição`
- Verificar total <200 linhas; avisar se >185.

### 6. Reportar resumo

```
Saved N learning(s), skipped M.
MEMORY.md: X/200 lines used.
Files created: feedback_name.md, reference_name.md, ...
```

## Important

- **Aprovação obrigatória** antes de cada write. Não fabricar conteúdo — só capturar o que foi dito.
- **Sem duplicatas.** Checar MEMORY.md antes.
- Frontmatter: apenas `name`, `description`, `type`. Body: parágrafo diretivo + `**Why:**` + `**How to apply:**`.
- Filenames: `{type}_{snake_case}.md`. Entries no index <150 chars.
- Avisar se MEMORY.md >185 linhas; sugerir consolidação.
- **pt-BR é o idioma primário do workflow.** Detecção precisa pegar correções em pt-BR (não pode ser EN-only).
