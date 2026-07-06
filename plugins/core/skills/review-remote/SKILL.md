---
name: review-remote
description: Invoque para revisar código sem depender de plugins externos — pre-push do próprio trabalho (Flow A) ou review de PR alheio via `--branch` (Flow B), com comparação de escopo contra ticket via `--ticket`. Sequencial, plugin-free.
disable-model-invocation: true
---

# review-remote — Code Review (plugin-free, sequencial)

> **Qual usar**: este skill é plugin-free e sequencial. Com o plugin `pr-review-toolkit` ativo, prefira `core:review-local` (paralelo). **Divergência**: `core:review-local` BLOQUEIA em analyze-fail; este reporta como finding e segue.

Review de código para o time, sem dependência de plugins externos.

## Config do projeto

Este skill assume que o projeto consumidor define:
- **Branch base default** (fallback se `--base` não for passado; ex.: `main`).
- **Comando de lint** e **comando de testes** (Flow A, Step 2).
- **Checklist de Camada 1** — itens universais de review sempre aplicados (config: quantidade e conteúdo dependem do projeto; ex.: um arquivo `CHECKLIST.md` de uma skill de code-review própria).
- **Checklist de Camada 2** — gatilhos contextuais (UI, state management, listas, i18n, imagens, animações, navegação) e a skill que os aplica.
- **Regras de state-management/arquitetura específicas do stack** (Step 5), se o projeto usa um framework com padrões próprios (ex.: uma lib reativa com convenções de mutação).
- **Prefixos de comentário e destino do output** (Step 8 do Flow B) — ex.: `blocker:`/`non-blocker:` para Bitbucket, ou o formato de review nativo do GitHub.

Sem essas configs, o skill ainda roda a estrutura de Steps abaixo, só sem os checklists específicos do stack.

## Usage

```
review-remote                                           # Flow A: pre-push do próprio trabalho
review-remote --base <branch>                           # Flow A com base explícita
review-remote --branch feat/<algo>                       # Flow B: review de PR alheio
review-remote --branch feat/<algo> --base <base>          # Flow B com base diferente
review-remote --branch feat/<algo> --ticket <TICKET>       # Flow B + comparação de escopo com ticket
```

Parâmetros:
- `--branch` — branch remota do PR; sem este flag = Flow A (pre-push)
- `--base` — branch base do diff (default: config acima)
- `--ticket` — identificador de ticket para comparação de escopo (somente com `--branch`)

---

## Step 0 — Detectar modo

Parse `$ARGUMENTS`:
- `--branch` presente → **Flow B** (ir para seção Flow B abaixo)
- `--branch` ausente → **Flow A** (continuar abaixo)

---

## Flow A — Pre-push (sem `--branch`)

### Step 1 — Resolve scope

```bash
git diff origin/<base>...HEAD --stat
```

Se o output estiver vazio: parar. Reportar "Nenhuma alteração em relação a `origin/<base>`."

Exibir o `--stat` para que o autor confirme o escopo antes de prosseguir.

### Step 2 — Precondition

Executar em sequência o comando de lint e o comando de testes do projeto (config).

Reportar os resultados (erros, warnings, falhas de teste). **Não bloquear** — falhas viram findings do review, não impedem a continuação.

### Step 3 — Camada 1

Obter o diff completo: `git diff origin/<base>...HEAD`

Aplicar o checklist de Camada 1 do projeto (config) contra todos os arquivos alterados. Documentar cada violação encontrada com file path e número de linha.

### Step 4 — Camada 2

Verificar gatilhos contextuais presentes no diff (config — exemplos típicos): UI/componentes, reações de state management, listas/coleções, i18n/l10n (strings novas, formatação), imagens de rede, animações, navegação. Para cada gatilho verdadeiro, invocar a skill de code-review do projeto configurada para essa dimensão.

### Step 5 — Regras de stack (se aplicável)

Para cada arquivo de state/controller presente no diff, ler as regras de qualidade específicas do stack do projeto (config) — tanto os códigos sempre-aplicados quanto os aspiracionais.

### Step 6 — Aggregate

**Verification Discipline obrigatória:** antes de incluir qualquer finding no relatório, reler as linhas exatas do arquivo. Descartar findings de problemas já corrigidos.

Consolidar todos os findings em pt-BR, agrupados por severidade (config: nomes/prefixos de severidade do projeto — ex.: `blocker:` / `non-blocker:`).

Formato de cada finding: `<prefixo>: CODE — descrição (Arquivo.ext:linha)`

### Step 7 — Fechar

Apresentar relatório e perguntar: **"Como proceder?"**

O autor decide os próximos passos: corrigir antes do push, suprimir com justificativa, ou criar ticket de follow-up.

---

## Flow B — PR Remoto (com `--branch`)

### Step 1 — Resolve scope

Verificar se `origin/<branch>` já está disponível localmente:
```bash
git branch -r | grep "origin/<branch>"
```

Se não encontrar:
```bash
git fetch origin <branch>
```

Calcular e exibir o diff:
```bash
git diff origin/<base>...origin/<branch> --stat
```

Se vazio: parar. Reportar "Branch `<branch>` não tem alterações em relação a `<base>`."

### Step 2 — (sem precondition)

O reviewer não faz checkout. Lint e testes são responsabilidade do CI da branch.

### Step 3 — Camada 1

Obter diff: `git diff origin/<base>...origin/<branch>`

Aplicar o checklist de Camada 1 do projeto (config). Documentar violações com file path e linha.

### Step 4 — Camada 2

Mesmos gatilhos do Flow A. Invocar a skill de code-review do projeto para cada gatilho verdadeiro no diff.

### Step 5 — Regras de stack (se aplicável)

Para cada arquivo de state/controller no diff, ler as regras de qualidade específicas do stack do projeto (config).

### Step 6 — Ticket (se `--ticket` fornecido)

Comparar os critérios de aceitação do ticket vs escopo real do diff. Apontar divergências:
- Funcionalidades pedidas no ticket que não aparecem no diff
- Mudanças no diff que não foram pedidas no ticket

### Step 7 — Aggregate

**Verification Discipline obrigatória:** reler file:line de cada finding antes de incluir.

Excluir findings marcados como 🟣 pre-existing — não são responsabilidade deste PR.

### Step 8 — Output

Produzir bloco copiável no formato do destino configurado (config — ex.: Bitbucket, comentário de review do GitHub). **Não perguntar "como proceder"** — o reviewer não edita o código.

```
=== Comentários para o PR <branch> ===

blocker: CODE — descrição do problema (Arquivo.ext:linha)
blocker: CODE — descrição (Arquivo.ext:linha, :linha2)

non-blocker: CODE — sugestão (Arquivo.ext:linha)
```

Idioma do texto: pt-BR. Códigos de regra: no formato que o projeto já usa.
