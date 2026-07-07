# Design — Onda de refino pós-auditoria

**Data**: 2026-07-07 · **Status**: aprovado em brainstorm, aguardando review do spec
**Insumos**: 2 auditorias externas (GitHub, sem acesso a fonte de hooks), 1 crítica de overengineering, 2 planos de estrutura/identidade, verificação local dos claims (esta sessão), 6 decisões do operador via AskUserQuestion.

## 1. Contexto e objetivo

O kit acabou de ser extraído do workspace de origem (Marcos 1–3 concluídos em 2026-07-07). A D13 define o critério de sucesso — primeiro uso real em projeto fora do de origem em 2 semanas — e o relógio corre. Esta onda consolida o que as cinco camadas de crítica convergiram, filtrado por verificação local, em: (a) quick-wins mecânicos confirmados, (b) reestruturação de identidade em 4 plugins, (c) higiene de superfície pública. Dogfood é o item 1 e nada compete com ele.

## 2. Fatos verificados que fundamentam o design

Verificação feita em 2026-07-07, nesta sessão, contra o fonte local e runtime:

| Claim das críticas | Veredito | Evidência |
|---|---|---|
| Sem CI | **Confirmado** | `.github/workflows` não existe; gates rodam manualmente (`docs/OPERATIONS.md:64-75`) |
| INVENTORY não marca wired-provisório | **Confirmado** | Nenhum marcador em `INVENTORY.md`; exceção só em prosa no `CHANGELOG.md` |
| Critério slash-only não escrito | **Confirmado** | `INVENTORY.md` explica a mecânica, nenhum doc declara a regra |
| Contrato cobre 4/35 skills, dívida invisível | **Confirmado** | `docs/SKILL-CONTRACT.md` §Conformidade |
| `bash-autoapprove` é regex ingênuo contornável | **Refutado** | Parser fail-closed compound-aware (`plugins/core/hooks/bash-autoapprove-readonly.sh:5-19`); hook mais coberto da suíte (14/42 casos em `evals/cases/hook-cases.jsonl`) |
| Estado de hooks fora de plugin-data | **Refutado** | `read-ledger.sh:27-28` e `context-monitor.sh:40-43` usam `${CLAUDE_PLUGIN_DATA}`; corpus epistêmico em `~/.claude/epistemic/` é deliberado (cross-projeto) |
| Reads de subagent não entram no ledger (C3) | **Refutado em runtime** | Teste 2026-07-07: reads via tool Read de subagent aparecem no ledger da sessão-mãe — confirma `review-local/SKILL.md:77` |
| — | **Furo novo achado** | Leitura via **Bash** (`cat`/`grep`/`sed`) contorna o read-ledger (hook cobre só Read\|Grep) — vetor de falso-vermelho no gate de citação do `review-local` |
| Descriptions "rivalizam com o sempre-ativo" | **Parcial** | 10.281 bytes agregados em 35 skills (teto do sempre-ativo: 16.384) — real, não-governado, magnitude menor que a alegada |
| `claude-dir-guard` cobre menos do que promete | **Parcial** | Cobre só `rm` literal (`claude-dir-guard.sh:26`), mas a descrição no inventário é honesta |

Calibração extraída: claims de **ausência** das auditorias acertaram 4/4; claims de **comportamento de código** erraram 3/3. Crítica futura de fonte externa sem acesso ao fonte: pesar por essa régua.

## 3. Decisões desta onda

1. **Escopo**: onda completa — mecânico + conceitual + identidade (rejeitadas: moratória total, quick-wins-only).
2. **D15 — identidade**: extrair plugin `team` **e** redeclarar o README (especificidade como posicionamento).
3. **Conselho**: extração como plugin `council/` intacto no PR da Fase 2 — **emenda** a decisão do mesmo dia de "não tocar até o censo". Condições que preservam o censo: zero reforma interna, 11 artefatos intactos, descriptions idênticas, `council` instalado em todo lugar onde `core` estiver (senão a medição de conversão confunde com disponibilidade). A consolidação interna (posturas → lentes) e o destino de `council-log`/`recall` continuam decisões do censo.
4. **Fusão `advisor-check` → `grill-me`**: uma skill com dois modos — entrevista (pressiona o operador) e escalação (revisor mais forte nos 3 checkpoints). `advisor-check` é deletado após absorção (D10: substituído).
5. **Matriz de decisão** da superfície "desafie meu plano" no corpo do `core:pipeline` (fonte única de roteamento): quando `grill-me` (cada modo), `spec-refine`, Conselho — estágio, insumo, o que cada um cobre que os outros não.
6. **Docs 4→2** na Fase 3, com ressalva registrada (ver §7).

## 4. Estrutura alvo

```
plugins/
  core/     pipeline, commit, pr, review-local, review-remote, tech-breakdown,
            spec-refine, archaeology, bug-report, learn, compound, methodology,
            using-agent-kit, grill-me (com modo escalação) + hooks e scripts atuais
  council/  council, bohr, schrodinger, epicurus, sagan, council-log, council-recall
            + agents maxwell, zeno, epistemic-council + POSITIONING.md
  team/     refine-live, refine-async, chat-draft
  mobile/   como está
```

| Plugin | Identidade em uma frase |
|---|---|
| `core` | Metodologia de entrega com enforcement determinístico — do ticket ao PR, qualquer stack |
| `council` | Lentes epistêmicas para decisões de alto custo de reversão |
| `team` | Copiloto de cerimônias ágeis — refinamento com PO, comunicação de squad |
| `mobile` | Toolkit Flutter/Dart — review, tracking, simulador |

Teste de coerência mecânico: skill nova que não cabe em nenhuma frase não entra em nenhum plugin.

## 5. Plano por fase

Fases expressam **dependência de ordem, não calendário**: CI (1.2) antes da Fase 2 — o PR de reestruturação é o que mais precisa dos gates automáticos; Fase 2 antes da Fase 3 — README e docs descrevem a estrutura final. Dogfood (1.1) roda em paralelo desde o dia 1 e nada compete com ele. Âncoras de calendário são só duas: D13 (janela de 2 semanas) e o censo (~30 dias). O ritmo é ditado pela capacidade de review do operador; gargalo esperado: item 2.6.

### Fase 1 — uso + mecânico

| # | Item | Critério de aceite |
|---|---|---|
| 1.1 | **Dogfood**: kit instalado e trabalhando em projeto externo real (alvo definido pelo operador) | Primeiro uso real registrado dentro da janela D13 |
| 1.2 | **CI** `.github/workflows/ci.yml`: `check-provenance.sh`, `check-governance.sh`, `generate_inventory.py --check`, `run-evals.sh`, shellcheck (via `find`, não glob) | Workflow verde em push na `main` |
| 1.3 | **Fix furo Bash-read**: mandato "tool Read para qualquer arquivo que vá ser citado como evidência" no dispatch do `review-local`; nota na linha 77 com a evidência do teste de 2026-07-07 (reads de subagent via Read entram no ledger-mãe; via Bash não) | Texto no SKILL.md; limitação documentada |
| 1.4 | **Marcador wired-provisório**: tabela machine-readable no GOVERNANCE (item, data de promoção, prazo de validação; formato de linha parseável, análogo ao contrato do ledger que o gate já lê), lida por `generate_inventory.py` (`⏳ provisório — valida até <data>` no INVENTORY) e por `check-governance.sh` (gate **vermelho** com prazo vencido — força o censo) | INVENTORY marca todos os provisórios; gate acusa vencidos |
| 1.5 | **Critério slash-only escrito** (emenda ao contrato de skills, sem ID novo): efeito difícil de reverter, custo alto de execução (dispatch em massa, rede), ou cerimônia longa ⇒ `disable-model-invocation: true`; lente/postura/referência barata ⇒ invocável pelo modelo | Parágrafo normativo no contrato; legenda do INVENTORY aponta pra ele |
| 1.6 | **Coluna de conformidade** no INVENTORY (conforme/pendente ao contrato) | Dívida das 31 skills visível e contável |

### Fase 2 — reestruturação (1 PR, review adversarial obrigatório)

| # | Item | Critério de aceite |
|---|---|---|
| 2.1 | Extrair `plugins/team` e `plugins/council` (git mv + manifests + `marketplace.json`) | `claude plugin validate` verde nos 4 plugins |
| 2.2 | Sweep de referências: `core:bohr`→`council:bohr` etc. em using-agent-kit, pipeline, council/SKILL.md, agents, docs, memória de projeto | `grep -r "core:(council\|bohr\|schrodinger\|epicurus\|sagan\|refine-\|chat-draft\|advisor-check)"` zero em `plugins/` e `docs/` |
| 2.3 | Fusão `advisor-check` → `grill-me` (dois modos) | Skill única; INVENTORY regen; rota atualizada no pipeline |
| 2.4 | Matriz de decisão no corpo do `pipeline` | Tabela presente; descriptions dos mecanismos inalteradas |
| 2.5 | Dependência inter-plugin vira aviso mecânico: SessionStart de `team`/`mobile`/`council` avisa se `core` ausente | Hook pequeno + caso de eval correspondente |
| 2.6 | Review do PR com `/core:review-remote` (o último move mecânico teve 15 defeitos) | Review rodado; findings tratados antes de merge |
| 2.7 | Emendas de texto: D10 ("wired vive em `plugins/<plugin>/`"), instrução de instalação no OPERATIONS ("council acompanha core" — condição do censo) | Textos atualizados |

### Fase 3 — identidade pública + docs

| # | Item | Critério de aceite |
|---|---|---|
| 3.1 | **README nova hierarquia**: frase de identidade → ledger de citação como bandeira → pipeline de entrega → tabela dos 4 plugins → Conselho/governança como seções avançadas. Glossário de 5 termos (wired, unwired, grillado, gate, censo). Sai a voz de dotfile | README reordenado; zero termo interno sem glossário |
| 3.2 | **Docs 4→2**: GOVERNANCE absorve SKILL-CONTRACT (§Contrato); OPERATIONS absorve unwired/README (tabela de itens fica); `check-governance.sh` atualizado pra ler a seção no novo local; nota de numeração externa dos IDs migra pro CHANGELOG | Gates verdes pós-merge; ponteiros atualizados |
| 3.3 | **D16 — descriptions**: regra de forma no contrato (description responde só "quando invocar"); teto por classe de esqueleto — procedimento/postura ≤ 350 bytes, roteador ≤ 700 (cortar gatilhos de `pipeline`/`methodology` degradaria a conversão que o censo mede); teto agregado por plugin medido no gate; passe find-and-cut em todas as skills **exceto `council/`** (descriptions congeladas até o censo — condição da decisão 3 do §3; o teto passa a valer pro council só depois) | Check novo no `check-governance.sh` verde; agregado publicado no INVENTORY; `git diff` de `plugins/council/` vazio neste item |
| 3.4 | **Higiene pública**: description + topics no GitHub (`claude-code`, `claude-plugins`, `flutter`, `agentic-coding`); tag semver coerente com versões atuais dos plugins (core 0.2.x — não `v0.1.0`); asciinema/GIF 30s do pipeline no README (gravação manual do operador) | About preenchido; tag publicada; mídia no README |

**Não fazer nesta onda** (consenso das cinco camadas + decisões): reescrever skills por dentro, reformar o Conselho internamente, criar regra de governança além das listadas, mexer nos hooks de enforcement (`bash-autoapprove`, `read-ledger`, `claude-dir-guard` — verificados sólidos ou honestos), `set -euo pipefail` cego (fail-open do `claude-dir-guard` é deliberado; shellcheck no CI cobre a higiene).

## 6. Entradas novas no ledger (mínimo necessário, cada uma com validador)

- **D15** — Identidade e estrutura em 4 plugins (core/council/team/mobile), cada um com frase de identidade; teste de coerência pra skill nova; README assume especificidade. Validador: `claude plugin validate` + `generate_inventory.py --check` no CI. Inclui a emenda ao texto de D10.
- **D16** — Governança de descriptions: regra de forma + tetos por esqueleto + teto agregado por plugin. Validador: check novo em `check-governance.sh`.
- **D17** — Marcador wired-provisório machine-readable com prazo; gate vermelho em prazo vencido. Validador: `generate_inventory.py` + `check-governance.sh`.

Após esta onda, ledger **congela**: decisão nova só entra se mudar comportamento de gate (proposta das críticas, adotada).

## 7. Riscos e trade-offs declarados

- **Docs 4→2 é a segunda reescrita estrutural de docs no mesmo ciclo** (GOVERNANCE virou canônico hoje, Marco 2). Aceito pelo operador com a ressalva registrada: se apertar o cronograma, é o primeiro item a cair pro censo.
- **Namespace do Conselho muda no meio da janela de validação** (`core:*` → `council:*`). Mitigação: descriptions idênticas, instalação acoplada ao core, review adversarial do PR. O censo mede conversão por postura na embalagem nova — anotar a mudança de condição no registro do censo.
- **Move mecânico tem histórico de 15 defeitos** — por isso 2.6 é obrigatório, não opcional.
- **Teto de descriptions pode subestimar roteadores** — mitigado pelo teto diferenciado por esqueleto; se o censo mostrar queda de conversão do pipeline, o teto de roteador é revisto por entrada de ledger.
- **Furo Bash-read tem fix textual, não mecânico** (mandato no prompt do dispatch). Se falhar repetido em uso, vira mecanismo (meta-princípio) — candidato: PostToolUse(Bash) parseando `cat`/`sed -n` de paths, custo a avaliar no censo.

## 8. Fora de escopo — pré-agendado pro censo (fim do ciclo, ~30 dias)

1. Consolidação interna do Conselho (posturas → lentes) e destino de `council-log`/`council-recall` — com dado de conversão por postura.
2. Colocação de evals junto aos artefatos + gate eval↔artefato (o failure mode do `handoff-gate` vira regra mecânica).
3. D10 aplicado à própria governança: regra de processo não exercitada no período vira "governança adormecida" ou colapsa em uma linha.
4. Ampliação do `claude-dir-guard` (mv, `find -delete`, `git clean`) — ou permanece documentado como está.
5. Mecanização do fix Bash-read, se o textual falhar em uso.

## 9. Critérios de aceite da onda

- D13 satisfeita: primeiro uso real em projeto externo dentro da janela.
- CI verde na `main` com os 5 checks.
- 4 plugins validando; INVENTORY regenerado com marcadores provisórios e coluna de conformidade.
- Zero referência stale de namespace (grep 2.2 limpo).
- Ledger com D15–D17 resolvendo no gate; nenhum ID citado sem entrada.
- README na hierarquia nova com glossário; About do GitHub preenchido; tag publicada.
