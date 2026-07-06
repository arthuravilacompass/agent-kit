---
name: tech-breakdown
description: Invoque para transformar um ticket em plano de implementação pronto para desenvolvedor — busca o ticket, roda brainstorming + refinamento adversarial + writing-plans, e faz o critic-phase grillar o plano contra o codebase real. Uso típico do Tech Lead.
disable-model-invocation: true
---

# tech-breakdown — Technical Breakdown for TL

Fetch a ticket, perform technical analysis, and produce a ready-to-develop implementation plan using superpowers brainstorming + writing-plans pipeline.

**Intended user:** Tech Lead (TL)

## Config do projeto

Este skill assume que o projeto consumidor define:
- **Tracker de ticket** — de onde vem o texto do ticket (Jira, Linear, um board Kanban interno, ou texto colado manualmente). O mecanismo abaixo usa Jira como exemplo concreto, mas depende só do **conteúdo do ticket**, nunca de uma integração específica.
- **Padrão/prefixo de ticket ID** — usado só para nomear o arquivo do plano salvo (ex.: `PROJ-123`, `ACME-456`). Sem essa config, use o ID tal como o usuário forneceu.
- **Convenção de stack usada no critic phase** — nomes de lib de logging, padrão de erro, serialização etc. que o critic deve validar contra o codebase real (ver Step 7).

## Prerequisites

- Um tool de tracker de ticket configurado na sessão (ex.: MCP Atlassian) — ou o usuário cola o texto do ticket diretamente.
- superpowers marketplace skills must be installed

## Steps

1. **Receive ticket ID**

   The user provides the ticket ID as an argument: `tech-breakdown <TICKET>`

   If no argument is provided, ask: "Which ticket would you like to break down?"

2. **Fetch ticket from the tracker**

   Do not hardcode an MCP tool name. Resolve the *get-issue* tool available in the session at runtime (e.g. via tool search) and fetch the ticket by issue key — MCP server aliases change over time and a hardcoded name silently breaks the fetch. If no tracker tool is available, ask the user to paste the ticket text.

   Extract:
   - Summary (ticket title)
   - Description (requirements, acceptance criteria)
   - Issue type (Story, Bug, Task, Sub-task)
   - Priority
   - Labels and components
   - Linked issues (if any)
   - Comments that clarify requirements (if any)

3. **Summarize ticket context**

   Present to the user a structured summary:

   ```
   Ticket: <TICKET> — [Summary]
   Type: [Story/Bug/Task]
   Priority: [High/Medium/Low]

   Requirements:
   [Key requirements extracted from description]

   Acceptance Criteria:
   [List of ACs if present]

   Dependencies:
   [Linked tickets or systems]
   ```

   Ask: "Does this summary capture everything relevant? Any additional context I should know before the technical analysis?"

   Wait for confirmation or additions.

4. **Run superpowers brainstorming**

   Invoke the superpowers:brainstorming skill with the ticket context as input.

   The brainstorming session will:
   - Explore the codebase relevant to the ticket
   - Propose 2-3 implementation approaches with trade-offs
   - Get the TL's approval on the chosen approach
   - Produce a validated design/spec

5. **Adversarial spec refinement**

   Before writing the plan, run `core:spec-refine` (se disponível neste kit) against the spec produced in step 4.

   This stress-tests the spec for missing error paths, ambiguous states, and unwritten invariants. The session produces a Gap Summary that is incorporated into the spec before planning begins.

   Skip only if the TL explicitly says "skip refinement" or the ticket is a trivial 1-file change.

6. **Generate implementation plan**

   After brainstorming produces the spec (and refinement closes the gaps), invoke the superpowers:writing-plans skill.

   The plan will be saved to:
   ```
   docs/superpowers/plans/YYYY-MM-DD-<ticket-id>-<short-title>.md
   ```

7. **Critic phase — grill the plan against the actual codebase**

   Before declaring the plan ready, dispatch a critic subagent (Explore-style) with the produced plan and the ticket context. The critic answers concretely:

   - For each lib/utility named in the plan, does it already exist in the codebase? Grep and cite the file.
   - For each new file/class/store proposed, is there a close analogue already (avoid parallel implementations)?
   - For each "we'll use library X" assumption, does the project actually use X? (Confirm the project's real convention for logging, error handling, serialization, etc. — see **Config do projeto** — instead of assuming a default.)
   - For each analytical claim (file count, token count, lines of code), was a project script used (config: e.g. `scripts/analyze_tokens.py`) or only shell approximation?

   The critic returns PASS (proceed) or FAIL (concrete gaps → loop back to step 4 brainstorming with gaps as input; cap at 2 critic rounds; if still failing, escalate to the TL).

8. **Link plan back to the tracker**

   After saving the plan, resolve the *add-comment* tool available in the session at runtime (do not hardcode an MCP tool name — see Step 2) and add a comment to the ticket with the plan path: `"Implementation plan created: docs/superpowers/plans/YYYY-MM-DD-<ticket-id>-<title>.md"`.

9. **Hand off ao desenvolvedor com verifier**

   Apresente ao TL:
   - Caminho do plano salvo
   - Resumo da abordagem escolhida
   - Sub-tasks sugeridas (se o escopo merecer split)
   - **Verifier** (sinais abaixo) — embed nos critérios de "done" de cada phase

   Plano pronto para developer executar via `superpowers:executing-plans`.

   **Verifier — sinais antes de declarar phase completa** (heurística, não checklist rígido):

   Antes de qualquer claim "F1 / F2 / Phase N completa", confirme o que fizer sentido pra phase:
   - Arquivos esperados realmente tocados (`git status` / `git diff --stat`).
   - Acceptance criteria observavelmente cumpridos (não inferidos de "código compilou").
   - Testes / analyzer rodaram com output capturado.
   - Phases anteriores realmente terminaram antes de avançar.

   Se algum sinal falha, phase fica `in_progress`. Não reporte "phase completa" upstream sem voltar e fechar a lacuna.

   Por que existe: sessões anteriores já claimaram phase completa quando brainstorming/writing-plans/critic não tinham de fato rodado — o verifier existe para não repetir esse gap entre "achei que terminei" e "terminei de verdade".

## Quando o ticket está incompleto

Antes de gerar o tech breakdown, valide que o ticket tem:

- **Acceptance Criteria** (comportamento observável que valida pronto)
- **Entrypoints sugeridos** (arquivos/módulos que devem ser tocados)
- **Test Plan** (lista de testes a implementar — unidade/widget/integração)

Se 1+ está ausente, **pergunte ao usuário 3 perguntas curtas** antes de gerar o breakdown:

1. "Quais arquivos esperamos tocar?"
2. "Que comportamento valida que está pronto?"
3. "Alguma constraint específica do projeto (ver Config do projeto / design system / tier de state management, etc.)?"

Use as respostas para preencher o tech breakdown. Se o ticket já tem essas seções, trate como contrato e use diretamente.

NÃO crie um template required. Esta é uma heurística — o usuário pode dizer "skip, vamos com o que tem".

## Sinais de gordura a cortar

Antes de finalizar o artefato, releia procurando por:

- **Background duplicando o ticket** — se está no card, não precisa repetir aqui.
- **"Alternatives Considered" sem decisão** — se você não escolheu, não codifica.
- **Exemplos de código que vão estar no diff** — refira o diff, não duplique.
- **Listas de arquivos sem o "porquê"** — entrypoint sem motivo de tocar é ruído.
- **Seções "Background" + "Motivation" + "Context"** redundantes — escolha uma.

Se 2+ sinais aparecem, provavelmente há ~30% de gordura cortável. Decisão de cortar ou justificar mantendo é sua.

## Important

- The TL drives the brainstorming session. Claude supports, proposes, and documents.
- Never skip the ticket fetch step — the plan must trace back to real requirements.
- If the ticket lacks sufficient detail (no acceptance criteria, vague description), flag this to the TL before starting technical analysis.
