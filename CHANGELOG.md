# CHANGELOG

## [Unreleased]

### Adicionado

- **Conselho de Posturas completo promovido a wired (2026-07-07)** — `bohr`, `sagan`, `council` (índice + formato de saída), `council-log`, `council-recall` em `plugins/core/skills/`; `maxwell`, `zeno`, `epistemic-council` em `plugins/core/agents/`. Promoção provisória sob a exceção de deadline de rotação (codificada em `unwired/README.md` nesta mesma mudança), decidida explicitamente pelo dono após a auditoria de harness de 2026-07-07; linhagem de uso: corpus episódico pré-existente das 6 posturas em `~/.claude/epistemic/` (jun–jul 2026). Prazo de validação: sem uso real em 1 ciclo de projeto novo, volta a `unwired/`. Adaptações na promoção: descriptions dos 8 arquivos reescritas com o gatilho do contexto do kit (passo 1 da regra — cobrado pela review adversarial), convenção `/core:` aplicada nos corpos, `<path-do-skill>` → `${CLAUDE_PLUGIN_ROOT}`, refs cruzadas `council/SKILL.md` → skill `core:council`, nota de proveniência refeita. Review adversarial pós-promoção rodada na mesma sessão (regra de memória do dono).
- **Exceção de promoção por deadline de rotação codificada em `unwired/README.md`** (regra completa lá; `using-agent-kit` §Governança ganhou o ponteiro).
- **Hardening do `bash-autoapprove-readonly.sh`** (finding da auditoria 2026-07-07): `git fetch` (rede), criação de branch/tag, `pub get` (muta lockfile) e `flutter/dart test` (executa código do repo) saem da classificação read-only e passam a deferir. +7 eval cases cobrindo os novos guards (30 no total). README ganhou parágrafo de composição das duas camadas de permissão (modo do harness × hook).
- Versões nos manifests (`core` 0.2.0, `mobile` 0.1.0) e descrição na marketplace.

### Alterado

- `using-agent-kit` §Vocabulário de Posturas: as 6 posturas agora são todas wired (4 skills in-thread + 2 subagents) com ponteiro pro índice `core:council`.
- README: contagens atualizadas (core: 25 skills, 4 agents), tabela de agents, seção unwired, descrição do autoapprove.
- Auditoria de harness & identidade (2026-07-07, workflow de 15 agentes): relatório completo fora do repo (contém contexto do projeto de origem — o gate de proveniência recusa, corretamente) em `~/.claude/audits/2026-07-07-harness-identity-audit.md`.

- Skeleton inicial do repo com plugins core e mobile
- README.md completo (instalação, mapa wired dos 2 plugins, unwired/promoção (à época archive/), assets manuais, princípios, nota de double-loading)
- `core:pipeline` — condutor de fluxo (camada de routing conversacional): detecção de estágio, 5 classes de tarefa com rotas, tabela estágio→skill com fallbacks sem superpowers, disciplina de sessão. Spec: `docs/superpowers/specs/2026-07-06-conversational-flows-pipeline-design.md`
- Promovidos de `unwired/` para wired: `bug-report`, `refine-live`, `refine-async` (`plugins/core/skills/`) e `figma-to-component` (`plugins/mobile/skills/` — Flutter-only, não cabia em `core`). `bug-report` já era skill-folder válida (só mover + remover nota de proveniência); `figma-to-component` teve a `description` reescrita e ganhou `disable-model-invocation: true`; `refine-live`/`refine-async` converteram de comando flat pra skill-folder com frontmatter (mesmo padrão usado em `tech-breakdown`/`archaeology`/`advisor-check` na extração original). Decisão de promoção — exceção deliberada à regra padrão de "uso real comprovado", motivada pelo prazo de desalocação do workspace de origem — documentada num plano de sessão externo a este repo (não versionado aqui). Revisão pós-promoção (xhigh, workflow de code-review) encontrou 15 defeitos de conteúdo introduzidos pela promoção mecânica — referências cruzadas mortas, placeholders não preenchidos, nomes de tool inexistentes no Claude Code, convenção `/core:`/`/mobile:` não aplicada no corpo das skills — todos corrigidos na mesma sessão.

### Aceite final (spec §7) — via marketplace local

Rodado em dois projetos virgens sob `$TMPDIR` (`git init` + `claude plugin marketplace add "$HOME/dev/agent-kit"`), sem depender de GitHub.

**(a) Projeto Flutter virgem, core+mobile instalados (`-s project`):**
- `using-agent-kit` presente: hook `session-start.sh` injeta o corpo da skill (confirmado via `claude -p`, sessão relata regras "Grep antes de responder convenção" e "Evidência antes de claim").
- `core:*` e `mobile:*` invocáveis: 9/9 skills mobile listadas e coerentes com o disco; 7/16 skills core aparecem na auto-enumeração do modelo — as 9 restantes (`advisor-check`, `archaeology`, `commit`, `compound`, `pr`, `review-local`, `review-remote`, `spec-refine`, `tech-breakdown`) têm `disable-model-invocation: true` no frontmatter (funcionam só via `/core:<nome>` explícito, não pela tool Skill) — confirmado invocando `/core:archaeology` diretamente, respondeu corretamente.
- `learn` gravando: verificado à parte, num terceiro projeto virgem (`$TMPDIR/learn-check`, `git init` + mesmo marketplace local), via `claude -p "Usando a skill core:learn: eu prefiro sempre usar tabs em vez de espaços. Capture essa preferência como uma proposta de memória — mostre o arquivo de memória que você proporia (frontmatter + corpo)."`. Resultado observado: a skill carregou, procurou `MEMORY.md` (ausente, sem duplicata), e devolveu uma proposta estruturada — frontmatter `name`/`description`/`type: feedback` + corpo com `Why`/`How to apply` + entrada correspondente pro índice `MEMORY.md` — parando explicitamente para aprovação (`approve`/`edit ...`/`skip`) sem gravar nada em disco (confirmado: diretório do projeto ficou só com `README.md` do `git init`, nenhum `.md` novo). Isso é o comportamento correto do fluxo propose-then-approve da skill, não uma falha. **PASS.**
- Hook dispara: `session-start.sh` (core) e `smell-checker.sh` (mobile, bloqueou DI001 com exit 2) rodados direto no cache instalado (`~/.claude/plugins/cache/agent-kit/{core,mobile}/66a0edfe53fe`) — ambos confirmados fora do harness de eval.
- `.mcp.json` registrado: `claude mcp list` mostra `plugin:mobile:dart` e `plugin:mobile:marionette`, ambos ✔ Connected (binários presentes no PATH da máquina de teste).
- Zero ref de proveniência quebrada: denylist de `check-provenance.sh` (à época `check-no-tf.sh`) rodada contra o cache instalado (`plugins/cache/agent-kit/{core,mobile}/66a0edfe53fe`) — limpo.

**(b) Projeto não-mobile virgem, só core instalado:** confirmado por `claude -p` que não há nenhuma skill `mobile:*` disponível e nenhum MCP `dart`/`marionette` — e que o contexto `using-agent-kit` injeta normalmente (mesma citação de regra 🔴 que em (a)).

**(c) R2 — custo de payload + A/B comportamental:**
- `analyze_tokens.py`: achado colateral — o script resolve plugin instalado em múltiplos scopes pegando `installs[0]` de `installed_plugins.json`, não necessariamente o scope efetivo da sessão; nesta máquina havia um `core@agent-kit` (scope user) preso num commit anterior ao gate-dia-3 (`4aabfbc`, o commit imediatamente anterior ao commit tageado `gate-day3-pass` = `1674a57`), medindo 15 skills em vez de 16 — corrigido com `claude plugin update core@agent-kit` antes de medir (ação fora do repo, disclosed aqui).
  - Core+mobile juntos (projeto a): **2.321 tokens/turno** medidos (chars÷4, sem tiktoken instalado) — agent defs (mobile 990 + core 526) + skill listings (core 499 + mobile 306). On-demand (custo só quando skill roda): 31.856 tokens.
  - Só core (projeto b): **1.025 tokens/turno**. On-demand: 22.703 tokens.
  - Lacuna do script: `analyze_session_hooks()` só detecta arquivo estático `session-start.md`/`STARTUP.md`; não mede a saída dinâmica de `hooks/session-start.sh`, que injeta o corpo inteiro de `using-agent-kit` uma vez por sessão. Medido à parte via `wc -c` na saída real do hook: **11.737 chars ≈ 2.934 tokens** (mesma aproximação chars÷4) — custo de sessão, não por turno, ausente do relatório do script pra esse padrão de hook.
  - **Total realista da 1ª mensagem de uma sessão**: ~5.255 tokens (core+mobile) ou ~3.959 tokens (só core), além do baseline fixo do Claude Code (~9k, não relacionado ao kit).
- A/B comportamental: tarefa idêntica ("qual biblioteca de logging esse projeto usa?" contra um arquivo com `structlog`) rodada com e sem `core@agent-kit` habilitado no mesmo projeto (b). **Sem diferença observável** — as duas rodadas leram o arquivo antes de responder e acertaram (`num_turns=5` em ambas). Hipótese mais provável: o ambiente de teste já tinha `superpowers` instalado (outro plugin com disciplina epistêmica sobreposta) e/ou o modelo (Sonnet 5) já exibe esse comportamento de baseline sem o rule textual explícito — o teste não discrimina nesse cenário específico. Procedimento documentado para o dono rodar uma bateria maior (2-3 tarefas, projeto realmente limpo sem `superpowers`) se quiser sinal mais forte; só 1 rodada A/B foi executada de fato aqui (não só documentada) por orçamento de tempo/custo da sessão.

### Métricas D13

- gate-day3: 2026-07-06 14:12:26 -0300 (commit `1674a57`, tag `gate-day3-pass`)
- métrica-2-semanas: primeiro uso real em projeto fora do projeto de origem até 2026-07-20 — senão foi "inventário com README"
