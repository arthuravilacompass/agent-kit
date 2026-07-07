---
name: methodology
description: Invoque quando o tier sempre-ativo (using-agent-kit) não bastar — metodologia de aplicação específica (verificação, evidência, escopo, investigação, exploração, tooling compartilhado) e referência técnica portável de Claude Code (hooks, advisor), git (rerere, revert parcial) e Flutter/Dart (build_runner). Gatilhos: "esse gate pode dar falso-negativo", "esse critério é proxy do objetivo real?", "hook não disparou", "revert parcial pós-release", "vou dar por pronto/executar — verifiquei o artefato final?".
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

---

### Evidência é relida no estado atual e gerada, não transcrita

Antes de listar um achado (review, auditoria, enumeração), releia a evidência no estado atual — arquivo atual, cwd confirmado, comando sem truncamento (`head`/`tail` mascara contagem/topologia) — nunca a partir de snapshot antigo. E quando o entregável é uma lista humana derivada de fonte estruturada, gere-a por script sobre a fonte, mesmo com N pequeno (mesmo mandamento do §Gate de verificação, "Como aplicar").

**Sinal**: achado citado sem reler no mesmo turno; claim negativa ("X não existe") de busca com cwd não confirmado; lista final sem comando/script que a gerou.

**Failure mode**: lista cita item já corrigido ou perde item real — um único erro detectado destrói a credibilidade de toda a entrega.

---

### Medir antes de construir tem precondição — não é lei universal

Quando a existência/taxa-base de um alvo é desconhecida (alvo raro, erro silencioso, hipótese não testada), meça antes de construir a solução. Mas só enquanto a precondição se mantém: se a direção já foi decidida explicitamente, reintroduzir o gate de medição — mesmo reformulado — não é rigor, é resistência à decisão.

**Sinal**: medição pós-build encolhe o alvo a cada rodada (solução construída sobre presunção); ou o gate reaparece reformulado após decisão explícita já tomada.

**Failure mode**: anedota isolada vira subsistema antes de confirmar tamanho real; ou, no sentido inverso, medição repetida vira adiamento que nunca converge em entrega.

---

### Tooling compartilhado separa infraestrutura, padrão de time e preferência pessoal

Ao distribuir configuração que outros vão herdar, separe três camadas: infraestrutura universal (nível compartilhado), padrão de time (convenção acordada, com enforcement explícito) e preferência pessoal (estilo individual — nível de usuário/local, nunca no compartilhado).

**Sinal**: config compartilhada carrega preferência de um indivíduo que o time nunca acordou como padrão.

**Failure mode**: onboarding gera fricção; config apodrece rápido porque preferência pessoal muda mais que padrão de time.

**Como aplicar**: antes de commitar um item de config compartilhada, pergunte "um colega competente discordaria disso com razão válida?" — se sim, é camada pessoal.

---

### Dois caminhos de leitura independentes exigem instrumentar os dois

Quando um valor tem duas rotas de leitura pro mesmo dado lógico (uma camada renderiza de uma fonte, uma validação lê de outra), não trate uma como prova de que a outra tem o mesmo valor — mapeie e instrumente as duas nos boundaries de camada antes de formar hipótese.

**Sinal**: hipótese assume que "a camada A mostra X" implica que a camada B também tem X, sem checar B direto.

**Failure mode**: hipótese aplicada antes da cadeia completa mapeada não corrige nada; o ciclo de investigação é refeito do zero.

**NÃO se aplica quando**: o bug já tem causa localizada numa única camada.

---

### Output de exploração usa frame de oportunidade, com severidade ancorada

Em output de mapeamento/exploração destinado a decisão (não review pontual), prefira "Oportunidades de melhoria" a "Riscos"/"Remoções". Ancore severidade em rubrica explícita (bloqueia decisão vs. tem workaround vs. débito conhecido), não em vibe. Abra com TL;DR curto, rankeie no máximo ~5 itens-chave, cite arquivo:linha por item — sem citação é inferência, corte.

**Sinal**: severidade sem rubrica; sem TL;DR; mais de ~5 itens todos "prioritários".

**Failure mode**: leitor recebe wall of data e refaz a priorização que o relatório deveria ter feito.

---

### Checkpoint de consolidação e gate de advisor nas transições que comprometem

Em investigação longa, não empilhe hipóteses paralelas sem fechar cada uma — periodicamente (e sempre que a direção for desafiada) produza um quadro único: provado com evidência vs. aberto, e UM próximo passo. Pra tema crítico, investigação linear sozinha não basta: faça fan-out por dimensão e verifique cada achado contra a fonte primária antes de sintetizar. Nas transições que comprometem, verifique o artefato FINAL (não só a abordagem): saindo de planejamento, advisor; declarando concluído, prefira subagent cego adversarial — o advisor vê a conversa inteira e herda o ponto cego do "tá pronto" (ver §Advisor nativo abaixo).

**Sinal**: 3+ hipóteses paralelas nunca fechadas; transição plano→execução ou "pronto" sem verificação independente do artefato final.

**Failure mode**: ruído consome a sessão sem fio condutor; buraco que um revisor fresco pegaria só aparece horas dentro da execução.

**Como aplicar**: plano trivial (typo, rename único) pula o gate; ≥3 itens ou ≥1 fase de código passa por ele.

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
