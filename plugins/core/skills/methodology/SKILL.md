---
name: methodology
description: Invoque quando o tier sempre-ativo (using-agent-kit) não bastar — pra consultar metodologia de aplicação mais específica (gate de verificação, objetivo vs proxy, escopo de fix, evidência circular) ou referência técnica portável de Claude Code (hooks, advisor), git (rerere, revert parcial) e Flutter/Dart (build_runner). Gatilhos: "esse gate pode dar falso-negativo", "esse critério é proxy do objetivo real?", "hook não disparou/não chegou no modelo", "revert parcial pós-release", "build_runner mudou arquivo fora de escopo".
---

# Methodology — tier 2 (on-demand)

Extensão do `using-agent-kit`: lá ficam os princípios de maior recorrência (sempre-ativos); aqui fica metodologia igualmente válida mas de aplicação mais específica, e referência técnica portável entre projetos.

## Metodologia

### Gate de verificação não deriva do próprio artefato sob teste

Um gate que prova "X está limpo/correto" não pode calcular a verdade a partir do próprio X quando X teve a história ou proveniência reescrita/reconstruída — o teste perde o referencial e vira falso-negativo silencioso, o que é pior que não ter gate (dá confiança falsa).

**Sinal**: o gate deriva o critério de "limpo" inspecionando o artefato reconstruído, não uma referência que retém a história original.

**Failure mode**: gate reporta verde com o problema ainda presente; só aparece depois, em produção ou auditoria manual.

**Como aplicar**: compute o critério a partir de uma ref que retém a história relevante (branch antiga, diff de uma fatia com histórico); gere a lista de violações programaticamente em vez de à mão; o gate só checa presença/ausência no artefato final. Some um gate inverso quando aplicável (o que não devia mudar, não mudou) — provar limpeza exige provar os dois lados.

---

### Objetivo amplo não colapsa num proxy

Quando o pedido é amplo ou qualitativo e falta critério de aceite explícito, desenhe o critério de sucesso de forma que ele FALHE se o objetivo real não foi atingido — não um proxy satisfeito pelo conteúdo que já existia. Ao simplificar, separe complexidade incidental (tooling, passos de build — corte à vontade) de valor essencial (conteúdo/vistas novas — preserve).

**Sinal**: o critério de sucesso passa mesmo quando nada do objetivo declarado mudou; ou uma rodada de simplificação remove conteúdo novo junto com máquina incidental.

**Failure mode**: entrega passa no critério mas não resolve o que foi pedido; retrabalho quando alguém nota a lacuna.

---

### Issue pré-existente vira follow-up, não fix no mesmo PR

Não corrija, no PR atual, problemas que a mudança não introduziu — funcional, estético ou dívida técnica comum viram ticket separado. Exceção: segurança (vazamento de dado/credencial) é tratada como incidente, não follow-up adiável.

**Sinal**: diff inclui fix de algo que já estava quebrado antes da mudança, sem relação com o objetivo do PR.

**Failure mode**: PR infla escopo, review fica mais difícil, risco de regressão em área não relacionada.

---

### Artefato auto-criado não é evidência independente

Um card/doc/draft que você mesmo criou (ou criou a pedido) não conta como evidência independente pra uma conclusão — ele só ecoa o enquadramento que você já tinha. Antes de citar um artefato como evidência, confira a proveniência: se saiu de você/da sua sessão, exclua-o da balança e reconstrua o argumento só com fontes independentes (spec original, código, commits, decisões de terceiros).

**Sinal**: conclusão cita como corroboração um artefato produzido pela própria sessão ou a pedido dela.

**Failure mode**: julgamento circular; confiança inflada numa conclusão frágil que não resiste a uma fonte independente.

## Referência Técnica

### Claude Code

- **Payload de hook**: `PostToolUse` recebe `tool_response` (objeto com o resultado), não `tool_output`; `UserPromptSubmit` entrega `prompt` (texto cru). O formato varia por hook event — confira o schema oficial (`docs/en/hooks`) antes de assumir um campo.
- **Output JSON de `UserPromptSubmit`**: pra injetar contexto, `additionalContext` precisa estar aninhado sob `hookSpecificOutput` (`{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "..."}}`). No nível raiz é JSON válido mas **descartado silenciosamente** (exit 0, sem erro) — o smoke-test tem que checar o efeito, não só o exit code.
- **Verificar se um hook está registrado**: cheque as DUAS fontes — settings do usuário (`~/.claude/settings.json`) E do projeto (`.claude/settings.json` + `.claude/settings.local.json`) — antes de concluir "não registrado". Checar só uma fonte já produziu claim errado, inclusive por um revisor cego adversarial que checou a fonte errada.
- **`.claude/rules/` vs `.claude/docs/` vs `.claude/skills/`**: `rules/*.md` é auto-loaded (único mecanismo que dispara em generation-time); `docs/*.md` é inerte — só carrega se algum consumidor cabeado o referenciar explicitamente (review-time); `skills/` (SKILL.md) é on-demand mas auto-descoberto pela description. Regra que precisa moldar código em generation-time vai em `rules/`, não em `docs/`.
- **Advisor nativo** (`/advisor <model>`): tool server-side que consulta um modelo mais forte em decision points; o próprio Claude decide quando chamar (model-driven, não regra). Recebe SEMPRE a conversa inteira — não existe modo cego. Bom pra planejamento (contexto ajuda); ruim pra quebrar ponto cego de auto-avaliação ("tá pronto") — aí prefira um subagent cego adversarial (input mínimo, mandato de refutar).

### Git

- **`rerere` pode reaplicar resolução errada silenciosamente**: com `rerere.enabled=true`, refazer um cherry-pick/merge cuja tentativa anterior resolveu um conflito ERRADO faz o git reaplicar a resolução gravada (`using previous resolution`) — sem markers de conflito, sem aviso visual. Ao re-tentar depois de uma resolução buggy, purgue as entradas do dia em `.git/rr-cache` (ou rode com `-c rerere.enabled=false`) antes de continuar.
- **Recuperar feature de um revert parcial**: quando um revert manteve a infra e reverteu só a UI, reaplicar a feature original via cherry-pick gera conflitos de "já aplicado" (a infra já está lá). O caminho cirúrgico é `git revert -m 1 <revert-commit>` — reverte o revert, trazendo de volta exatamente o que foi removido, nada mais. Sinal pra usar essa via: o diffstat do revert é bem menor que o da feature original (revert parcial); se for simétrico, é revert total e cherry-pick direto é seguro.

### Flutter / Dart

- **`build_runner` regenera arquivos fora do escopo da mudança**: rodar `build_runner build` pra uma mudança pontual de DI pode regenerar dezenas de `.g.dart` de módulos não relacionados por churn puramente cosmético (drift de formatação entre versões do toolchain). Depois de rodar, restrinja o commit aos arquivos de fato relevantes: liste os `.g.dart` tocados, reverta os fora de escopo, mantenha só o que a mudança pediu de fato. Não aceite "é pré-existente" de um subagent sem checar você mesmo com `git diff`.
