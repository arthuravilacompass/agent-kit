---
name: review-local
description: Invoque para disparar reviewers especializados em paralelo contra o diff da branch atual — última linha de defesa antes de `core:pr`. Requer o plugin `pr-review-toolkit`; sem ele, use `core:review-remote` (sequencial).
disable-model-invocation: true
---

# review-local — Local PR Review Chain Before Push

> **Qual usar**: este skill exige o plugin `pr-review-toolkit` (dispatch paralelo). Sem o plugin, use `core:review-remote` (sequencial, sem paralelismo). **Divergência**: `review-local` BLOQUEIA em falha de lint/analyze; `review-remote` reporta a falha como finding e segue.

Dispatch specialized reviewers in parallel against the current branch diff. Last line of defense before `core:pr`. Output is presented in conversation only — never auto-posted.

## Config do projeto

Este skill assume que o projeto consumidor define:
- **Branch base** (default sugerido: `main`).
- **Comando de lint** e **comando de testes** usados na precondition (Step 2).
- **Códigos de regra do próprio projeto** que os agentes `code`/`type` devem tratar como 🔴 Important (ver `agents.md` — a tabela de agentes é o ponto de configuração).
- **Diretórios de pacotes**, se o repo for um monorepo com múltiplos projetos que usam comandos de lint/teste diferentes.

## Usage

```
review-local
review-local --ticket <TICKET>
review-local --base <branch>
review-local --agents code,silent
review-local --ticket <TICKET> --base <branch> --agents code,consumer
```

Default base: config acima (fallback: `main`). When `--ticket` is provided, the `consumer` agent is auto-included unless filtered out by `--agents`.

## Steps

1. **Resolve diff scope**

   - Parse `--base <branch>` if provided, else the project's default base branch (config; fallback `main`).
   - `git diff <base>...HEAD --stat` to summarize scope.
   - If empty: stop and report "Nenhuma mudança em relação a `<base>`. Nada para revisar."
   - Echo scope (base, total files, exclusões) and wait 5 seconds for user abort.

2. **Precondition — base verification (automático)**

   Detect the project/package from the diff path (config — e.g. multiple packages in a monorepo) and run:

   - the project's lint/static-analysis command (config)
   - the project's test command (config, sem coverage, para velocidade)

   Se qualquer um falhar, abortar com:

   > "Verificação base falhou. Corrija antes de gastar tokens em review."

   Anexar últimas linhas do erro. Não prosseguir.

3. **Dispatch agents in parallel**

   Read `agents.md` for the agent table (ID, `subagent_type`, framing, preconditions).

   **Resolve dispatch list:**

   - Parse `--agents <id1,id2,...>` (comma-separated).
   - **Sem `--agents`:** dispatch every agent whose precondition is met (4 normalmente; 5 se `--ticket` presente — `consumer` é gated em `--ticket`).
   - **Com `--agents`:**
     - Validar cada ID contra a tabela do config. ID desconhecido → abortar: "Agente desconhecido: `<id>`. IDs válidos: `<list>`."
     - Filtrar dispatch para os IDs pedidos.
     - Se `consumer` foi pedido sem `--ticket` → abortar: "Agente `consumer` requer `--ticket <TICKET>`."

   **Dispatch:** todos os `Agent` calls em **uma única mensagem** (paralelo). Cada agente recebe o diff (`git diff <base>...HEAD`) + framing string do config. `consumer` recebe APENAS o texto do ticket (resolvido em runtime a partir do tool de tracker disponível na sessão — não hardcode nome de tool MCP) — nunca o diff. Cada prompt de agente DEVE mandar: use o tool **Read/Grep** (nunca `cat`/`sed`/`grep` via Bash) para qualquer arquivo que vá ser citado como evidência — leitura via Bash não entra no read-ledger e derruba a citação no gate.

4. **Wait for all agents to return.** Não summarize parcial.

5. **Aggregate findings (pt-BR)**

   Antes de agregar, **verificação por citação (mecanismo, não só releitura manual — releitura sozinha não pega fabricação)**:

   - Montar as findings como JSON `[{ "claim": "...", "evidence": { "file": "...", "lineStart": N, "lineEnd": M } }]` (o file:line que cada agente citou; ponto único → `lineStart`=`lineEnd`).
   - Se o projeto tiver um validador de citações (script que checa findings contra o read-ledger da sessão), rode-o com `--session <session-id-atual>` explícito. O read-ledger registra os reads via tool Read/Grep de TODOS os subagentes sob a session_id-pai (verificado em runtime, 2026-07-07); leitura via Bash NÃO entra — daí o mandato do Dispatch. **Passe `--session` explícito** — NÃO confie em auto-discovery (pode haver sessões concorrentes).
   - Finding `unverified` (file:line não sobrepõe nada lido nesta sessão) = provável fabricação → seção "⚠️ Não-verificadas", **não** apresentar como achado confirmado. `verified`/`passthrough` seguem.
   - Complementar (não substitui o mecanismo): re-ler as linhas e dropar findings já corrigidos.

   Group by severity. Se `consumer` foi dispatched, adicionar seção "Ticket vs Implementação".

   ```
   ## Review Local — <N> achados

   ### 🔴 Important (<count>)
   - **[<agent-id>]** <finding> — <file>:<line> — regra <CODE>

   ### 🟡 Nit (<count>)
   - **[<agent-id>]** <finding> — <file>:<line>

   ### 🟣 Pre-existing (<count>)
   - **[<agent-id>]** <finding> — <file>:<line> (não mexido neste diff)

   ### ⚠️ Não-verificadas (<count>)
   - **[<agent-id>]** <finding> — <file>:<line> (citação não sobrepõe leitura no ledger — possível fabricação)

   ### Ticket vs Implementação (se consumer dispatched)
   - ✓ <behavior> (implementado)
   - ✗ <behavior> (não visível no diff — gap?)
   ```

6. **Ask how to proceed**

   > "Como proceder? Reply: fix-all / fix <severity> / fix <numbers> / ignore-preexisting / done"

## Important

- **Never post findings to any PR or external system.**
- **Output em pt-BR.** Rule codes em English.
- **Não corrigir 🟣 pre-existing neste PR.** São follow-up.
- **Dispatch é paralelo** (uma mensagem). Sequencial dobra o runtime sem benefício.
- **Roster vive em `agents.md`** — edite lá para adicionar/remover/retunar agentes.
- **Agente que falha ou time-out:** apresentar os que sucederam, notar quais falharam. Não retry sem pedido.
