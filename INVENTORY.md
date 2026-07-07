<!-- GERADO por scripts/generate_inventory.py — não editar à mão. Regenerar: python3 scripts/generate_inventory.py -->
# Inventário do agent-kit

Gerado automaticamente a partir dos manifests dos plugins (`SKILL.md`, agents, `hooks.json`, scripts e `.mcp.json`) — não editar à mão; regenerar com `python3 scripts/generate_inventory.py`.

Skills marcadas **slash-only** têm `disable-model-invocation: true` no frontmatter: rodam só via comando explícito (`/core:<nome>`, `/mobile:<nome>`), nunca por iniciativa do modelo (critério: `docs/SKILL-CONTRACT.md` §Critério slash-only).

Itens com “provisório até <data>” estão wired sob a exceção de deadline (`docs/GOVERNANCE.md` §Provisórios ativos) — prazo vencido deixa o gate vermelho.

---

## Plugin `core`

### Skills (25)

| Skill | Contrato (D14) | Descrição |
|---|---|---|
| `advisor-check` (slash-only: `/core:advisor-check`) | pendente | Invoque em 3 checkpoints deterministicos — pre-plan (antes de escolher abordagem), post-plan (plano aprovado, antes de codar), pre-done ("acho que terminei" / "tá pronto") — para escalar a um reviewer mais forte com contexto controlado ou cego, quebrando a bolha epistêmica da própria sessão. |
| `archaeology` (slash-only: `/core:archaeology`) | procedimento | Invoque para mapear o estado atual do código antes de qualquer planejamento técnico numa US, ticket ou domínio com histórico no app — dispatch de agentes de exploração em paralelo, mapa arqueológico consolidado com decisões ranqueadas por severidade. |
| `bohr` ⏳ provisório até 2026-08-06 | pendente | Invoque quando uma decisão desta conversa travar num "A ou B" ("refatorar ou entregar", "hook ou texto", "wired ou unwired"). Postura do Conselho (core:council) — recusa a falsa escolha e busca o eixo que dissolve o trade-off; lente in-thread sobre o raciocínio atual, não abre contexto novo. |
| `bug-report` (slash-only: `/core:bug-report`) ⏳ provisório até 2026-08-06 | pendente | Investiga um bug e produz relatório com citações verificadas — gate determinístico (validate_citations --gate) + verifier semântico em contexto fresco. Use ao investigar/reportar bug onde afirmar comportamento de código sem ler a fonte é o risco. |
| `chat-draft` | pendente | Invoque para redigir mensagens informais em pt-BR para Teams/Slack — recap de tech-sync, atualização de squad, ou qualquer pedido rotulado "mensagem para o time / chat / Teams / Slack". |
| `commit` (slash-only: `/core:commit`) | procedimento | Invoque para rodar validação pré-commit (lint + testes) e criar um commit convencional a partir do diff staged — nunca commita sem aprovação explícita do usuário. |
| `compound` (slash-only: `/core:compound`) | pendente | Write-back Estrutural de Fim de Track |
| `council` ⏳ provisório até 2026-08-06 | roteador | Invoque pra consultar o índice do Conselho de Posturas do kit — as 6 posturas wired (4 skills in-thread, 2 subagents isolados), o que cada uma interroga, quando vestir, o formato de saída (callout) e quando escalar pro modo cego (agent epistemic-council). O trabalho vive em cada postura; aqui é o mapa. |
| `council-log` ⏳ provisório até 2026-08-06 | pendente | Invoque após rodar uma postura do Conselho (core:schrodinger/bohr/epicurus/sagan ou agents maxwell/zeno) numa decisão de alto custo de reversão que vale lembrar — grava o brief no corpus episódico (~/.claude/epistemic/<postura>.jsonl, append-only). Advisory; nunca bloqueia. |
| `council-recall` ⏳ provisório até 2026-08-06 | pendente | Invoque antes de uma decisão de alto custo de reversão, junto com a postura do Conselho que vai vesti-la — consulta a memória episódica (~/.claude/epistemic/) e lista até 3 casos passados que rimam por FORMA (mesma postura + surface_class + overlap). Silencioso se nada rima. Advisory. |
| `epicurus` | pendente | Invoque antes de dar um design, escopo ou plano por pronto — classifica cada elemento como necessário, desejado-mas-dispensável ou vão, e corta os dois últimos. |
| `grill-me` | pendente | Invoque quando o usuário pedir para "me grillar" / "grill me", pressionar uma decisão de design, ou antes de dar um plano por pronto para execução — entrevista estruturada e implacável que resolve dependências entre decisões uma a uma. |
| `learn` | pendente | Invoque quando o usuário disser "salva isso", "captura esse aprendizado", "usa a skill learn", ou antes de um /clear ou compact quando a sessão acumulou correções e decisões não capturadas — escaneia a conversa e propõe entries de memória para aprovação. |
| `methodology` | pendente | Invoque quando o tier sempre-ativo (using-agent-kit) não bastar — metodologia de aplicação específica (verificação, evidência, escopo, investigação, exploração, tooling compartilhado) e referência técnica portável de Claude Code (hooks, advisor), git (rerere, revert parcial) e Flutter/Dart (build_runner). Gatilhos: "esse gate pode dar falso-negativo", "esse critério é proxy do objetivo real?", "hook não disparou", "revert parcial pós-release", "vou dar por pronto/executar — verifiquei o artefato final?". |
| `pipeline` | pendente | Invoque ao receber uma intenção crua de trabalho substancial (feature, bug, investigação, refactor, ticket/US) sem fluxo em andamento definido, ou quando o usuário pedir "por onde começo", "qual o fluxo pra isso", "me conduz nesse trabalho". NÃO invoque para pergunta conceitual ou lookup pontual ("como funciona X?"), nem quando já há um fluxo em andamento (brainstorming, plano em execução, review). Condutor de fluxo — detecta o estágio real da tarefa, classifica a intenção e roteia pelas skills do kit um estágio por vez; recomenda a próxima rota, nunca executa a cadeia inteira sozinho. |
| `pr` (slash-only: `/core:pr`) | pendente | Invoque para analisar todos os commits da branch, rodar verificação e montar a descrição de um Pull Request pronta para revisão — nunca faz push ou cria o PR sem aprovação explícita. |
| `refine-async` (slash-only: `/core:refine-async`) ⏳ provisório até 2026-08-06 | pendente | Triage pós-refinamento — consolida o contexto salvo pelo /core:refine-live, roda exploração leve do codebase (grep orçado, sem arquitetura profunda) e gera subtarefas [INTERIM] para aprovação e criação no board. Use logo após a agenda de refinamento, antes do pipeline técnico (archaeology → tech-breakdown). |
| `refine-live` (slash-only: `/core:refine-live`) ⏳ provisório até 2026-08-06 | pendente | Copiloto ao vivo para a agenda de refinamento com o PO — recebe o card do board + bullets do PO em tempo real e gera perguntas de esclarecimento por prioridade (escopo, critérios implícitos, dependências). Use durante a call de refinamento; consolida estado pro /core:refine-async na sequência. |
| `review-local` (slash-only: `/core:review-local`) | pendente | Invoque para disparar reviewers especializados em paralelo contra o diff da branch atual — última linha de defesa antes de `core:pr`. Requer o plugin `pr-review-toolkit`; sem ele, use `core:review-remote` (sequencial). |
| `review-remote` (slash-only: `/core:review-remote`) | pendente | Invoque para revisar código sem depender de plugins externos — pre-push do próprio trabalho (Flow A) ou review de PR alheio via `--branch` (Flow B), com comparação de escopo contra ticket via `--ticket`. Sequencial, plugin-free. |
| `sagan` ⏳ provisório até 2026-08-06 | pendente | Invoque antes de investir esforço numa decisão ou tarefa desta conversa — calibra se importa, em que escala, e se sobrevive ao tempo. Postura do Conselho (core:council). Distinta de core:epicurus, que corta elementos de um design já julgado digno; Sagan calibra a altitude da decisão inteira. |
| `schrodinger` | pendente | Invoque quando um diagnóstico tiver mais de uma explicação plausível e a tentação for fechar em uma sem a observação que a discrimine — mantém as hipóteses vivas até existir essa observação. |
| `spec-refine` (slash-only: `/core:spec-refine`) | pendente | Invoque para estress-testar uma spec ou design doc antes de virar plano de implementação — expõe gaps, estados ambíguos, error paths ausentes e invariantes não escritos, uma pergunta focada por vez. Rode depois de `core:tech-breakdown` (se disponível) e antes de `superpowers:writing-plans`. |
| `tech-breakdown` (slash-only: `/core:tech-breakdown`) | pendente | Invoque para transformar um ticket em plano de implementação pronto para desenvolvedor — busca o ticket, roda brainstorming + refinamento adversarial + writing-plans, e faz o critic-phase grillar o plano contra o codebase real. Uso típico do Tech Lead. |
| `using-agent-kit` | pendente | Sempre carregado via SessionStart — regras epistêmicas e de disciplina do agent-kit |

### Agents (4)

| Agent | Descrição |
|---|---|
| `consumer-simulation` | Context-restricted subagent that receives ONLY a ticket text + acceptance criteria (never the implementation) and produces a list of expected behaviors. Use to detect gaps between what a ticket asked for and what was implemented. Output is in Portuguese (pt-BR). |
| `epistemic-council` ⏳ provisório até 2026-08-06 | Modo cego do Conselho (skill core:council) — invoque no escalonamento das posturas (decisão pré-commit de alto custo de reversão) ou como verificador de conclusão. Recebe SÓ o problema reformulado + posições SEM autoria, nunca a prosa do thread nem o lean; roda UMA postura (bohr\|schrodinger\|epicurus\|sagan\|maxwell\|zeno) e verifica executando. Único ponto de separação estrutural real do Conselho. Output em pt-BR. Advisory. |
| `maxwell` ⏳ provisório até 2026-08-06 | Postura do Conselho (skill core:council) em subagent isolado — invoque antes de mexer em algo acoplado ou numa mudança não-trivial deste repo. Mapeia como a mudança propaga (dependências, efeitos, acoplamento) e que invariantes viajam; reporta touchpoints reais com file:linha. Output em pt-BR. |
| `zeno` ⏳ provisório até 2026-08-06 | Postura do Conselho (skill core:council) em subagent isolado — invoque ao validar uma solução já proposta, colando no dispatch as premissas vivas da conversa. Empurra os invariantes ao limite (zero, um, infinito, null, vazio, concorrente, falho-no-meio) até achar a borda concreta onde quebra. Output em pt-BR. |

### Hooks (7)

| Hook | Evento | Matcher | Descrição |
|---|---|---|---|
| `session-start.sh` | SessionStart | startup\|clear\|compact | SessionStart — injeta o corpo de using-agent-kit como contexto sempre-ativo. |
| `plan-autoload.sh` | SessionStart |  | SessionStart — injeta ponteiro de retomada quando existe plano recente (<72h). |
| `bash-autoapprove-readonly.sh` | PreToolUse | Bash | PreToolUse(Bash) — auto-aprova comandos de leitura reconhecidos como seguros; escrita, rede e mutação de deps deferem. |
| `claude-dir-guard.sh` | PreToolUse | Bash | PreToolUse(Bash) — bloqueia comandos rm que atingem .claude/. |
| `scope-inject.sh` | PreToolUse | Edit\|Write\|MultiEdit | PreToolUse(Edit\|Write\|MultiEdit) — injeta ponteiro de escopo quando o arquivo editado casa um mapa de conhecimento do projeto. |
| `context-monitor.sh` | PostToolUse | Bash | PostToolUse(Bash) — avisa quando o transcript da sessão cresce além de um limiar. |
| `read-ledger.sh` | PostToolUse | Read\|Grep | PostToolUse(Read\|Grep) — registra o range lido no ledger da sessão (base do mecanismo de citação). |

### Scripts (5)

| Script | Descrição |
|---|---|
| `analyze_tokens.py` | Analisa custo de contexto (tokens) por componente do setup Claude Code. |
| `census_usage.py` | Censo de uso dos artefatos invocáveis (commands/skills) por janela de tempo. |
| `conflict_triage.py` | Faz triage de conflitos de merge entre uma branch base e branches feature/team. |
| `prune_branches.sh` | Lista branches remotos candidatos a deleção; nunca deleta, gera arquivo para revisão manual. |
| `validate_citations.py` | Valida citações de findings contra o read-ledger da sessão (Camada 1). |

---

## Plugin `mobile`

### Skills (10)

| Skill | Contrato (D14) | Descrição |
|---|---|---|
| `code-review-mobile` | pendente | Invoque para revisar um PR/diff Flutter — checklist universal Camada 1 (17 itens, sempre) + Camada 2 contextual (UI, Observer, listas, l10n, navegação, testes) + referência de estrutura de módulo/componente. Gatilhos em pt-BR — "revisa esse PR Flutter", "checklist de review mobile", "onde devia ficar esse widget/store". |
| `deeplink-debug` | pendente | Invoque quando um deeplink/App Link abre no navegador em vez do app, falha ao rotear, abre a tela errada, ou você precisa validar comportamento de deeplink num device. Sintomas — "abre no navegador", "não abre o app", link está verified mas ainda abre no navegador, quebrou depois de reativar, funciona numa versão de Android/iOS mas não em outra. |
| `export-logs` | pendente | Invoque para exportar logs de rede HTTP de uma sessão Flutter debug rodando, filtrados por intervalo de tempo, como JSON estruturado. Gatilhos em pt-BR — "exporta os logs de rede desse intervalo", "pega as requisições HTTP entre HH:MM:SS e HH:MM:SS", "captura o tráfego de rede desse teste". |
| `feature-scaffold` | pendente | Invoque para gerar o scaffold de uma feature Flutter nova — page, MobX store/controller, repository, entity — seguindo o padrão em camadas (UI → State → Domain → Data) do projeto. Gatilhos em pt-BR — "cria uma feature nova", "faz o scaffold de <nome>", "gera store+repository+page pra isso". |
| `figma-to-component` (slash-only: `/mobile:figma-to-component`) ⏳ provisório até 2026-08-06 | pendente | Extrai um design do Figma via MCP (get_design_context/get_screenshot) e produz uma especificação de widget tree mapeada aos componentes do design system do projeto consumidor — tabela de mapeamento, tokens e lista de gaps sem equivalente. Use com /mobile:figma-to-component ao converter uma tela/componente do Figma pra Flutter. |
| `ga4-validate` | pendente | Invoque para validar tracking GA4 (tela × evento, antes × depois de uma mudança) num app Flutter rodando no simulador/emulador — dirige o app, captura o evento real com params, screenshota, casa tela × evento, monta a tabela de CTs e o report visual. Gatilhos em pt-BR — "valida os eventos GA4 dessa tela", "confirma o tracking antes e depois dessa mudança", "captura o evento real desse componente". |
| `marionette` | pendente | Invoque para validar visualmente mudanças de UI Flutter no app rodando no simulador — lançar o app em debug pra checks dirigidos por agente, tirar screenshots, tocar/rolar/dirigir telas, hot-reload após edits. Gatilhos em pt-BR — "confirma essa tela no simulador", "valida essa mudança visualmente", "screenshot do app rodando". |
| `mobx` | roteador | Invoque para revisar ou escrever qualquer store/controller MobX (Flutter) — smells que o linter não pega, do correctness blocker à direção arquitetural aspiracional. Gatilhos em pt-BR — "esse observable está certo?", "esse estado deveria ser enum?", "por que esse getter não atualiza a UI?", "revisão de MobX/DI". |
| `performance-patterns` | pendente | Invoque para revisar ou aplicar padrões de performance num app Flutter/MobX — rebuilds de Observer, chamadas de rede (Dio), imagens, memória. Gatilhos em pt-BR — "esse Observer está rebuildando demais", "essa lista tá lenta", "revisão de performance dessa tela". |
| `refactor-review` | pendente | Invoque antes de commitar um refactor que toca stores/repositories/coordinators compartilhados ou navegação — protocolo de 2 fases (regressão + qualidade). Gatilhos em pt-BR — "revisa esse refactor antes de eu commitar", "confirma que esse refactor não quebrou nada", "checklist pós-refactor". |

### Agents (1)

| Agent | Descrição |
|---|---|
| `mobx-smell-hunter` | Specialist subagent that hunts four specific MobX smells not caught by a linter — FSM001 (multi-flag flow composition), SSOT001 (multi-writer typed state), CMD001 (primitive discriminator), MOBX006 (synthetic concurrency state). Use when a store or controller has been modified in the current diff. Output is in Portuguese (pt-BR). |

### Hooks (4)

| Hook | Evento | Matcher | Descrição |
|---|---|---|---|
| `smell-checker.sh` | PreToolUse | Edit\|Write\|MultiEdit | PreToolUse(Edit\|Write\|MultiEdit) — bloqueia (exit 2, add-only) smells de correctness em Dart: DI direto, BuildContext vazando, print em produção. |
| `dart-auto-format.sh` | PostToolUse | Edit\|Write\|MultiEdit | PostToolUse(Edit\|Write\|MultiEdit) — roda dart format no arquivo editado. |
| `dart-analyze-file.sh` | PostToolUse | Edit\|Write\|MultiEdit | PostToolUse(Edit\|Write\|MultiEdit) — roda dart analyze escopado ao arquivo, feedback sempre advisory. |
| `package-feedback.sh` | PostToolUse | Edit\|Write | PostToolUse(Edit\|Write) — pub get em background pra pubspec.yaml editado; lembrete de teste pra _test.dart editado, uma vez por sessão. |

### Scripts (5)

| Script | Descrição |
|---|---|
| `arch_graph.sh` | Mede o grafo de imports (lakos) e regenera o bloco de dados do ARCHITECTURE.md. |
| `arch_violations.py` | Lê um grafo de imports (dot) e reporta violações de layering contra config do projeto. |
| `check_merged_imports.py` | Verifica resolução de imports Dart internos numa árvore git mergeada (sem checkout). |
| `export_network_logs.py` | Exporta logs de rede HTTP do Dart VM Service para JSON. |
| `swap_pubspec.py` | Troca dependências git-ref do pubspec.yaml por dependências de path local, e volta. |

### MCP (2)

| Server | Command |
|---|---|
| `dart` | `dart` |
| `marionette` | `marionette_mcp` |
