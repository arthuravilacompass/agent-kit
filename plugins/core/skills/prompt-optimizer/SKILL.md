---
name: prompt-optimizer
description: Invoke when the user asks to optimize, improve, or rewrite a draft prompt before running it, or asks how best to phrase a request for this kit ("optimize this prompt", "help me prompt for X", "how should I ask for this", "rewrite this prompt"). Analyzes intent, project context, and scope gaps, matches this kit's real skills/agents/postures, and outputs a ready-to-paste optimized prompt (full + quick) plus rationale. Advisory only — never executes the task itself. Do NOT invoke when the user wants the task run directly ("just do it", "só faz"), or for code/performance optimization requests ("otimizar código", "optimize this code", "optimize performance") — those are refactor/perf tasks, not prompt optimization.
---

# prompt-optimizer — draft-prompt analysis and rewrite

> Adapted from `LittleBearBond/everything-claude-code@e0ddb33` (`skills/prompt-optimizer/SKILL.md`), MIT License, Copyright (c) 2026 Affaan Mustafa. Logic and 6-phase pipeline kept faithful to the source; component catalog, model recommendation, and lifecycle routing re-pointed to this kit's real inventory — no references to the source ecosystem remain.

Analyze a draft prompt, critique it, match it to this kit's real skills/agents/postures, and output a complete optimized prompt the user can paste and run.

## When to Use

- User says "optimize this prompt", "improve my prompt", "rewrite this prompt"
- User says "help me write a better prompt for..."
- User says "what's the best way to ask Claude Code to..."
- User says "otimiza esse prompt", "melhora esse prompt", "como eu peço isso direito"
- User pastes a draft prompt and asks for feedback or enhancement
- User says "I don't know how to prompt for this" / "não sei como pedir isso"

### Do Not Use When

- User wants the task done directly (just execute it) — "just do it", "só faz", "direto"
- User says "otimizar código", "otimizar performance", "optimize this code", "optimize performance" — these are refactoring/perf tasks, not prompt optimization
- User wants help installing/configuring the kit itself — that's the README + `scripts/install.sh`, not this skill
- User wants a component inventory — point to `INVENTORY.md` at the repo root (generated, verified in the gate) instead of hand-listing skills here

## How It Works

**Advisory only — do not execute the user's task.**

Do NOT write code, create files, run commands, or take any implementation
action. Your ONLY output is an analysis plus an optimized prompt.

If the user says "just do it", "só faz", or "don't optimize, just execute",
do not switch into implementation mode inside this skill. Tell the user this
skill only produces optimized prompts, and instruct them to make a normal
task request if they want execution instead.

Run this 6-phase pipeline sequentially. Present results using the Output Format below.

### Analysis Pipeline

### Phase 0: Project Detection

Before analyzing the prompt, detect the current project context:

1. Check if a `CLAUDE.md` exists in the working directory — read it for project conventions (this is also where a test policy, if any, lives — see Phase 4)
2. Detect tech stack from project files:
   - `package.json` → Node.js / TypeScript / React / Next.js
   - `go.mod` → Go
   - `pyproject.toml` / `requirements.txt` → Python
   - `Cargo.toml` → Rust
   - `build.gradle` / `pom.xml` → Java / Kotlin / Spring Boot
   - `pubspec.yaml` → Flutter/Dart — if the `mobile` plugin is installed in this session, this activates the kit's flagship stack-specific toolkit (see Phase 3, By Tech Stack)
   - `Package.swift` → Swift
   - `Gemfile` → Ruby
   - `composer.json` → PHP
   - `*.csproj` / `*.sln` → .NET
   - `Makefile` / `CMakeLists.txt` → C / C++
3. Note detected tech stack for use in Phase 3 and Phase 4

If no project files are found (e.g., the prompt is abstract or for a new project),
skip detection and flag "tech stack unknown" in Phase 4.

Whether this task is already mid-flow (an existing spec/plan/handoff in
`docs/superpowers/`) is `core:pipeline`'s job (its stage-detection step), not
this phase's — don't re-check it here; if `core:pipeline` is already active
for this task, defer to it instead of re-running this phase.

### Phase 1: Intent Detection

Classify the user's task into one or more categories:

| Category | Signal Words (EN / pt-BR) | `core:pipeline` class |
|----------|-------------|---------|
| New Feature | build, create, add, implement / construir, criar, adicionar, implementar | New feature |
| Bug Fix | fix, broken, not working, error / corrigir, quebrado, não funciona, erro | Bug |
| Refactor | refactor, clean up, restructure / refatorar, limpar, reestruturar | Refactor |
| Investigation | how to, what is, explore, investigate / como, o que é, explorar, investigar | Investigation |
| External spec (ticket/US) | ticket, US, story, acceptance criteria / ticket, US, história, critério de aceite | External spec |
| Testing | test, coverage, verify / testar, cobertura, verificar | cross-cutting — see Phase 4's test-policy check |
| Review | review, audit, check / revisar, auditar, checar | maps directly to `core:review-local`/`core:review-remote`, not a pipeline stage class |
| Documentation | document, update docs / documentar, atualizar docs | no dedicated pipeline stage |
| Infrastructure | deploy, CI, docker, database / deploy, CI, docker, banco de dados | folds into New feature or Refactor depending on scope |
| Design | design, architecture, plan / desenhar, arquitetura, planejar | folds into New feature's clarify/specify stages; triggers `council:council` at HIGH+ scope |

### Phase 2: Scope Assessment

If Phase 0 detected a project, use codebase size as a signal. Otherwise, estimate
from the prompt description alone and mark the estimate as uncertain.

| Scope | Heuristic | Orchestration |
|-------|-----------|---------------|
| TRIVIAL | Single file, < 50 lines | Direct execution |
| LOW | Single component or module | Single skill, or direct execution — a minimal route is legitimate (`core:pipeline`'s own rule: propose skipping stages and let the user confirm) |
| MEDIUM | Multiple components, same domain | `core:pipeline`'s stage chain + `core:review-local`/`core:review-remote` + `core:commit` |
| HIGH | Cross-domain, 5+ files | `core:archaeology` (map) first, then `core:pipeline`'s phased stages; `council:council` for any high-reversal-cost call inside it |
| EPIC | Multi-session, multi-PR, architectural shift | `core:pipeline`'s session-discipline rule (one heavy phase per session + handoff at each boundary) + `core:learn` at each close; `council:sagan` to calibrate whether the effort altitude is actually warranted |

### Phase 3: Kit Component Matching

Map intent + scope + tech stack (from Phase 0) to specific kit components. This
kit is a methodology/conduction layer, not a per-stack pattern-skill catalog —
the only stack-opinionated vertical it ships is `mobile` (Flutter/Dart).

#### By Intent Type

| Intent | Skills | Agents / Council postures |
|--------|--------|--------|
| New Feature | `core:pipeline` (feature route) → `superpowers:brainstorming` or `core:grill-me` (clarify) → `core:spec-refine` (specify) → `superpowers:writing-plans` or `core:tech-breakdown` (break down) → `superpowers:executing-plans` (implement) → `core:review-local`/`core:review-remote` (review) → `core:commit` → `core:pr` (deliver) → `core:learn` (capture) | `core:cold-reader` (deliverable for a cold audience), `council:epicurus` (cut scope before done) |
| Bug Fix | `core:pipeline` (bug route): `superpowers:systematic-debugging` (diagnose) → implement fix → `core:review-local`/`core:review-remote` → `core:commit` | `council:schrodinger` (if more than one live hypothesis for the cause) |
| Refactor | `core:pipeline` (refactor route): `core:archaeology` (map) → clarify scope → implement → `core:review-local`/`core:review-remote` (+ `mobile:refactor-review` if the `mobile` plugin is active) → `core:commit` | `council:maxwell` (coupling map before touching), `council:epicurus` |
| Investigation | `core:pipeline` (investigation route): `core:archaeology` (map) → `superpowers:systematic-debugging` (diagnose) → report/handoff (terminal — don't force implementation) | `council:schrodinger` |
| External spec (ticket/US) | `core:archaeology` → `core:tech-breakdown` or `superpowers:brainstorming` → continues as New Feature | `core:consumer-simulation` (ticket-vs-implementation gap check) |
| Testing | No dedicated skill — check `core:methodology` if a verification-gate question is involved; if a TDD flow is already in use, `superpowers:test-driven-development` | — |
| Review | `core:review-local` (needs the `pr-review-toolkit` plugin) or `core:review-remote` (plugin-free) + `core:grill-me` escalation mode `pre-done` | `core:cold-reader`, `core:consumer-simulation` |
| Documentation | No dedicated skill in this kit | — |
| Infrastructure | No dedicated skill — treat as New Feature or Refactor by scope; `core:methodology` has portable git/hook reference | `council:maxwell` if coupling is the concern |
| Design (HIGH) | `superpowers:brainstorming`, `council:council` (entry point for a high-reversal-cost decision, any stage) | `council:maxwell`, `council:sagan` |
| Design (EPIC) | No blueprint-equivalent skill — `core:pipeline`'s session-discipline rule (one heavy phase/session, handoff between phases) | `council:sagan` (calibrate altitude before committing effort) |

#### By Tech Stack

| Tech Stack | Kit Component |
|------------|--------------|
| Flutter/Dart, on the `mobile` plugin's assumed stack (MobX + `get_it`/`injectable`) | `mobile` plugin: `code-review-mobile`, `refactor-review`, `feature-scaffold`, `deeplink-debug`, `export-logs`, `ga4-validate`, `marionette`, `mobx`, `performance-patterns`, `apk-archaeology`, `figma-to-component` + `mobx-smell-hunter` agent |
| Any other stack | No stack-specific skill catalog ships in this kit — `core:methodology`'s portable technical reference (hooks, advisor, git rerere/partial-revert) applies regardless of stack |

If the tech stack table above returns nothing project-specific, say so plainly
in the output rather than improvising a catalog that doesn't exist.

### Phase 4: Missing Context Detection

Scan the prompt for missing critical information. Check each item and mark
whether Phase 0 auto-detected it or the user must supply it:

- [ ] **Tech stack** — Detected in Phase 0, or must user specify?
- [ ] **Target scope** — Files, directories, or modules mentioned?
- [ ] **Acceptance criteria** — How to know the task is done?
- [ ] **Error handling** — Edge cases and failure modes addressed?
- [ ] **Security requirements** — Auth, input validation, secrets?
- [ ] **Testing expectations** — Unit, integration, E2E? Check `CLAUDE.md`/project conventions for test policy — this skill doesn't hardcode a TDD-by-default assumption; defer to whatever the project states, or ask.
- [ ] **Performance constraints** — Load, latency, resource limits?
- [ ] **UI/UX requirements** — Design specs, responsive, a11y? (if frontend)
- [ ] **Database changes** — Schema, migrations, indexes? (if data layer)
- [ ] **Existing patterns** — Reference files or conventions to follow?
- [ ] **Scope boundaries** — What NOT to do?

**If 3+ critical items are missing**, ask the user up to 3 clarification
questions before generating the optimized prompt. Then incorporate the
answers into the optimized prompt.

### Phase 5: Workflow & Model Recommendation

**Lifecycle routing.** Don't re-derive a stage sequence here — that's
`core:pipeline`'s job (its §3 "Stages → skills" table is the single source).
This phase's only job is to state where in that flow the prompt currently
sits (e.g. "this is a Clarify-stage prompt, next stop `core:spec-refine`")
and let `core:pipeline` (or the user) drive stage-to-stage from there.
Recommending the full chain here would duplicate pipeline's job — don't.

**Model recommendation.** This kit's model strategy runs on two independent
axes (`core:methodology`, §Model vs. effort is the source of truth — don't
invent a parallel policy here):

- **Model** = what it knows. Roles, not versions: **Fable** is the session
  default for synthesis/decisions/brainstorming/architecture; **Sonnet**
  executes via subagents (code, fixes, reviews, investigation); **Opus** is
  the fallback and long-horizon-planning option at lower cost than Fable.
  The `model-routing` hook enforces the boundary: a Fable-tier session model
  editing a code/hook/eval artifact directly gets an advisory nudge to
  delegate to a Sonnet subagent instead.
- **Effort** = how hard it tries (how much it reads/verifies before calling
  it done). It's a per-domain preference, not a per-task dial — don't
  re-tune it per prompt here.
- **Difficulty sensitivity** (prose, not a scope→version grid): harder or
  more architectural reasoning leans toward Fable or Opus for the synthesis
  step; execution is always a Sonnet subagent regardless of scope. A wrong
  result gets the input fixed first (prompt/tools/context) — model or effort
  changes are the last resort, not the first.

**Multi-session splitting** (for HIGH/EPIC scope): this kit has no
`save-session`/`resume-session` command pair — apply `core:pipeline`'s
session-discipline rule instead (one heavy phase per session: *clarify/specify*
· *implement* · *review/deliver* · *close*), with a handoff at each boundary
and `core:learn` capturing decisions/corrections at each close.

---

## Output Format

Present your analysis in this exact structure. Respond in the same language
as the user's input.

### Section 1: Prompt Diagnosis

**Strengths:** List what the original prompt does well.

**Issues:**

| Issue | Impact | Suggested Fix |
|-------|--------|---------------|
| (problem) | (consequence) | (how to fix) |

**Needs Clarification:** Numbered list of questions the user should answer.
If Phase 0 auto-detected the answer, state it instead of asking.

### Section 2: Recommended Kit Components

| Type | Component | Purpose |
|------|-----------|---------|
| Skill | `core:spec-refine` | Stress-test the spec before planning |
| Skill | `superpowers:writing-plans` | Turn the refined spec into a plan |
| Agent/Posture | `council:maxwell` | Map coupling before touching a shared module |
| Model | Sonnet subagent (+ Fable in-session for judgment calls) | Recommended role split for this scope |

### Section 3: Optimized Prompt — Full Version

Present the complete optimized prompt inside a single fenced code block.
The prompt must be self-contained and ready to copy-paste. Include:
- Clear task description with context
- Tech stack (detected or specified)
- Skill/agent invocations at the right workflow stages (reference `core:pipeline` for the stage sequence rather than re-listing every stage)
- Acceptance criteria
- Verification steps
- Scope boundaries (what NOT to do)

For EPIC-scope prompts, write "apply `core:pipeline`'s session-discipline rule
(one heavy phase per session + handoff)" — this kit has no blueprint-equivalent
skill to invoke instead.

### Section 4: Optimized Prompt — Quick Version

A compact version for experienced kit users. Vary by intent type:

| Intent | Quick Pattern |
|--------|--------------|
| New Feature | `core:spec-refine` the ask. `superpowers:writing-plans`. Implement. `core:review-local`/`core:review-remote`. `core:commit`.` |
| Bug Fix | `superpowers:systematic-debugging` for [bug] (`council:schrodinger` if >1 hypothesis). Fix. `core:review-local`/`core:review-remote`. `core:commit`.` |
| Refactor | `core:archaeology` [scope]. Implement. `core:review-local`/`core:review-remote` (+ `mobile:refactor-review` if mobile). `core:commit`.` |
| Investigation | `core:archaeology` for [topic]. Diagnose. Report/handoff — no forced implementation.` |
| Testing | Check `CLAUDE.md` test policy first. `superpowers:test-driven-development` if that flow applies.` |
| Review | `core:review-local` (or `core:review-remote` without the toolkit plugin). `core:grill-me pre-done`.` |
| Docs | Direct edit. `core:commit`.` |
| EPIC | `council:sagan` to calibrate. Phase via `core:pipeline`'s session discipline, handoff between phases, `core:learn` to capture.` |

### Section 5: Enhancement Rationale

| Enhancement | Reason |
|-------------|--------|
| (what was added) | (why it matters) |

### Footer

> Not what you need? Tell me what to adjust, or make a normal task request
> if you want execution instead of prompt optimization.

---

## Examples

### Trigger Examples

- "Optimize this prompt for this kit"
- "Rewrite this prompt so Claude Code uses the right skills"
- "Otimiza esse prompt pra mim"
- "Como eu devo pedir isso pro Claude Code fazer certo?"

### Example 1: pt-BR Prompt, Flutter Project Detected

**User input:**
```
faz uma tela de login
```

**Phase 0 detects:** `pubspec.yaml` with Flutter, MobX + `get_it`/`injectable` — the `mobile` plugin is installed (flagship stack)

**Optimized Prompt (Full):**
```
Implemente uma tela de login usando o stack já existente no projeto
(Flutter + MobX + get_it/injectable).

Requisitos técnicos:
- Seguir a estrutura de módulos e o padrão de state management (MobX) já
  usados no projeto
- Autenticação: reaproveitar o esquema já existente (verificar o
  repositório/service atual antes de criar um novo)
- Incluir: formulário de e-mail/senha, validação, mensagens de erro,
  estado de carregamento, layout responsivo

Fluxo:
1. core:archaeology no módulo de auth, se ainda não mapeado
2. Implementar seguindo os padrões existentes (mobile:feature-scaffold
   como base de scaffold, se aplicável)
3. mobile:code-review-mobile / core:review-local para revisão
4. core:commit ao final, com aprovação explícita

Critério de aceite:
- Login bem-sucedido navega para a tela principal; falha mostra erro
- Tela renderiza corretamente em telas pequenas e grandes
- Nenhuma credencial ou token aparece em log ou código-fonte

Não fazer:
- Não implementar tela de cadastro
- Não implementar "esqueci minha senha"
- Não alterar a estrutura de rotas existente
```

### Example 2: English Prompt, No Mobile Plugin

**User input:**
```
Fix the auth flow, it's broken after the last refresh-token change
```

**Phase 0 detects:** `package.json`, TypeScript — no `CLAUDE.md` test policy stated

**Optimized Prompt (Full):**
```
Fix the auth flow regression introduced by the last refresh-token change.

Tech stack: Node.js / TypeScript (detected from package.json)

Requirements:
- Use superpowers:systematic-debugging to isolate the root cause before
  proposing a fix — if more than one plausible cause survives initial
  investigation, wear council:schrodinger instead of picking one to move fast
- Fix must not regress the refresh-token flow that was just changed
- State the test policy this project follows (none found in CLAUDE.md) —
  ask before assuming TDD or writing tests as part of this fix

Workflow:
1. Reproduce the break, then superpowers:systematic-debugging to find the
   root cause with evidence
2. Implement the fix
3. core:review-remote (no pr-review-toolkit plugin detected — use
   core:review-local instead if it gets installed)
4. core:commit after explicit approval

Do not:
- Touch unrelated parts of the auth module
- Introduce a new token-storage mechanism to "fix" this
```

### Example 3: EPIC-Scope Prompt

**User input:**
```
Migrate our monolith service to an event-driven architecture
```

**Optimized Prompt (Full):**
```
Before any implementation, wear council:sagan to calibrate whether this
migration is worth the effort at this scale, and council:council as the
entry point for the high-reversal-cost architectural calls inside it.

Scope: EPIC — multi-session, architectural shift.

Session discipline (core:pipeline): one heavy phase per session —
clarify/specify · implement · review/deliver · close — with a handoff
at each boundary and core:learn capturing decisions between sessions.

Suggested phases:
1. core:archaeology per current domain/module to map real coupling
   (council:maxwell if coupling is the open question)
2. Clarify service boundaries and messaging pattern (superpowers:brainstorming
   or core:grill-me) → core:spec-refine
3. superpowers:writing-plans or core:tech-breakdown for the phased plan
4. Execute one service extraction per session, core:review-local/
   core:review-remote + core:commit at the end of each
5. core:pr once a phase is independently shippable

Model: Fable or Opus for the cross-session architectural plan (synthesis),
Sonnet subagent for each phase's implementation — see core:methodology
§Model vs. effort; this isn't a fixed scope→model table, adjust by the
actual difficulty of each phase.

Do not:
- Attempt the full migration in one session
- Skip the review/commit gate between phases to "save time"
```

---

## Related Components

| Component | When to Reference |
|-----------|------------------|
| `core:pipeline` | Full lifecycle routing — this skill defers to it, never re-derives the stage sequence |
| `core:grill-me` | Interview mode for operator-owned decisions; escalation mode at `pre-plan`/`post-plan`/`pre-done` |
| `council:council` | Entry point for a high-reversal-cost decision, at any stage |
| `core:methodology` | §Model vs. effort (source of truth for model recommendation), portable technical reference (hooks, advisor, git, Flutter/Dart `build_runner`) |
| `mobile:*` | Flutter/Dart stack-specific component catalog, only when that plugin is installed |
| `core:learn` | Capture stage — persist corrections/decisions worth remembering |
| `INVENTORY.md` (repo root) | Generated, gate-verified inventory of every skill/agent/hook — use instead of trusting a hardcoded catalog when auditing what's actually installed |
