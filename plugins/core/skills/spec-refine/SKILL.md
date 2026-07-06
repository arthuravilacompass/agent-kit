---
name: spec-refine
description: Invoque para estress-testar uma spec ou design doc antes de virar plano de implementação — expõe gaps, estados ambíguos, error paths ausentes e invariantes não escritos, uma pergunta focada por vez. Rode depois de `core:tech-breakdown` (se disponível) e antes de `superpowers:writing-plans`.
disable-model-invocation: true
---

# spec-refine — Adversarial Spec Refinement

## Config do projeto

Este skill assume que o projeto consumidor pode definir, opcionalmente:
- **Verificações de domínio adicionais** para a Step 2 — ex.: cobertura de i18n/l10n em strings novas, padrões de concorrência assíncrona específicos do stack (mutações fora de uma seção atômica após um `await`), campos de contrato externo (API/BFF) guardados contra null/ausente. Se o projeto não definir nada, a Step 2 roda só com as 7 categorias genéricas da tabela abaixo.

Stress-test a feature spec before it enters planning. Acts as a skeptical senior engineer who exposes gaps, ambiguous states, missing error paths, and unwritten invariants — one focused question at a time.

## When to Use

Run **after** `core:tech-breakdown` (se disponível neste kit) produces a spec and **before** `superpowers:writing-plans` turns it into an implementation plan. This is the adversarial second pass that catches what the first pass misses.

Also usable standalone: paste any spec or design doc and run this skill.

## Steps

1. **Receive the spec**

   The user either:
   - Runs this right after `core:tech-breakdown` — in which case the spec is already in context
   - Pastes a spec directly into the chat

   If neither, ask: "Please paste the spec or design you'd like stress-tested."

2. **Analyze silently first**

   Before asking any questions, read the spec and identify candidates for each of these gap categories:

   | Category | What to look for |
   |---|---|
   | **Error paths** | Actions that can fail but have no stated failure handling |
   | **Empty/null states** | Data that could be absent, empty list, or null with no defined behavior |
   | **Concurrent operations** | Multiple actions that could race (double-tap, fast navigation, background refresh) |
   | **State transitions** | Implicit transitions — what triggers X to become Y? Is it reversible? |
   | **Scope boundaries** | "This screen" without defining what happens when user navigates away mid-flow |
   | **External dependencies** | Fields assumed present in an external contract but not guaranteed by it |
   | **Invariants** | Assumptions stated as "always" or "never" without enforcement mechanism |

   If the project defined domain-specific checks (see **Config do projeto**), treat each as an additional category.

   Prioritize: ask about gaps where an unstated assumption would cause a real user-facing bug first.

3. **Ask questions one at a time**

   Ask the highest-priority question first. Wait for the answer before asking the next.

   For each question:
   - State the gap category briefly: `[Error path]`, `[Empty state]`, `[Concurrent ops]`, etc.
   - Name the specific section or component the gap is in
   - Ask a single, focused question
   - Provide your recommended answer (what you'd do if you had to implement this today)

   Example format:
   ```
   [Error path] Repository layer — `loadAddresses()`

   If the backend returns a 503 during checkout, the spec doesn't define whether the user
   sees an error state, a retry button, or falls back to manual input.

   Recommended: show an inline error with a retry CTA; do not clear any previously loaded
   data. What's the intended behavior?
   ```

4. **Continue until no more gaps**

   Ask 5–8 questions covering different categories. Avoid asking about the same category twice unless a previous answer introduced a new gap.

   If the user says "enough" or "done" or "looks good", stop questioning and move to step 5.

5. **Produce gap summary**

   After all questions are answered, output a **Gap Summary**:

   ```
   ## Spec Gaps Resolved — <Feature Name>

   ### Decisions Made
   | Gap | Decision |
   |---|---|
   | [Error path] loadAddresses failure | Show inline error + retry; retain existing addresses |
   | [Empty state] cart items on first load | Show empty-state illustration, not error |
   | ... | ... |

   ### Assumptions Still in Spec (Accepted Risk)
   - <assumption> — user accepted, no change to spec
   - ...

   ### Spec Sections to Update Before Planning
   - Section X: add failure handling for [scenario]
   - Section Y: define empty-state behavior
   ```

6. **Ask how to proceed**

   > "Gap summary is ready. Options:
   > - `update spec` — I'll incorporate the decisions into the spec document now
   > - `proceed to plan` — move directly to `superpowers:writing-plans` with these decisions as addenda
   > - `done` — keep the gap summary in context only"

## Sinais de gordura a cortar

Antes de finalizar o artefato, releia procurando por:

- **Background duplicando o card/ticket** — se está no card, não precisa repetir aqui.
- **"Alternatives Considered" sem decisão** — se você não escolheu, não codifica.
- **Exemplos de código que vão estar no diff** — refira o diff, não duplique.
- **Listas de arquivos sem o "porquê"** — entrypoint sem motivo de tocar é ruído.
- **Seções "Background" + "Motivation" + "Context"** redundantes — escolha uma.

Se 2+ sinais aparecem, provavelmente há ~30% de gordura cortável. Decisão de cortar ou justificar mantendo é sua.

## Important

- Ask questions that expose **user-visible bugs**, not style preferences.
- Every question must include a recommended answer — the goal is to close the gap, not just surface it.
- Do not ask more than 8 questions unless the spec is unusually large (>500 lines). Depth beats breadth.
- Do not ask about implementation choices already resolved in the spec — only gaps.
- Domain-specific checks defined in **Config do projeto** count as first-class gap categories, not an afterthought.
