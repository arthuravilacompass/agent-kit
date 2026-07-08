# Governança do kit

Doc canônico do ciclo de vida dos artefatos do agent-kit. Toda regra normativa de ciclo de vida vive aqui e só aqui; o formato de autoria de skills vive na §Contrato de SKILL.md deste doc (D14). `README.md`, `unwired/README.md` e `using-agent-kit` apontam pra cá. Histórico e datas vivem no `CHANGELOG.md`; medições vivem no gate (`scripts/check-governance.sh`).

## O modelo de 3 estados (D10)

Todo artefato que já existiu neste kit está num destes três estados, nunca em limbo:

- **wired** — vive em `plugins/<plugin>/` (hoje: `core`, `council`, `team`, `mobile`). Foi admitido porque tem uso real comprovado (não só "parecia bom"). Custa contexto toda sessão que carrega o plugin.
- **unwired** — vive em `unwired/`. Genericizável, scrub mecânico aplicado, mas sem prova de uso no novo projeto. Custo de contexto **zero** — só é lido se alguém abrir o arquivo.
- **deletado** — não existe no repo. Foi avaliado e descartado (vestigial, específico demais do projeto de origem pra genericizar, ou substituído por outra coisa melhor).

Nunca "testado mas não ligado" — essa terceira categoria fantasma é o que este modelo existe para eliminar.

## Regra de promoção

**Um item sobe de `unwired/` para `plugins/` (wired) quando tiver uso real comprovado no projeto novo — o mesmo critério de admissão que qualquer skill/agent/hook novo teria.** Não é "parece útil" nem "era usado no projeto de origem" — é: você invocou isso pelo menos uma vez no projeto novo, funcionou, e quer que sobreviva ao próximo `/clear`.

Ao promover:

1. **Reescreva a `description`** com o gatilho específico do novo contexto — a description arquivada carrega vocabulário/gatilho do projeto de origem (às vezes já genérico, às vezes não).
2. **Preencha os placeholders de proveniência** (`<TICKET>`, `<DesignTokens>`, `<BOARD_NAME>`, nomes de componente entre `<>`) com os nomes reais do projeto novo. O scrub que colocou o item em `unwired/` foi mecânico, não uma reescrita — o trabalho de reancorar no domínio novo é seu, não deste kit.
3. **Mova o arquivo** para `plugins/<plugin>/` na estrutura padrão (skills em `skills/<nome>/SKILL.md`, agents em `agents/<nome>.md`, etc.) e rode `claude plugin validate .`.
4. **Delete a cópia em `unwired/`** — um item promovido não fica duplicado nos dois estados.

### Exceção: promoção provisória por deadline de rotação

Quando a desalocação de um workspace de origem ameaça perder a janela de validação, um item PODE ser promovido sem uso real comprovado neste kit, desde que: (1) a exceção seja registrada no `CHANGELOG.md` com o motivo; (2) a promoção passe por review adversarial imediata do diff completo — a primeira leva promovida sob esta exceção teve 15 defeitos encontrados num move "puramente mecânico" (registro no `CHANGELOG.md`); (3) o item ganhe prazo de validação — sem uso real em 1 ciclo de projeto novo, volta a `unwired/`. Promoção provisória não codificada é violação da governança, não exceção dela.

### Provisórios ativos (lidos por máquina)

Itens atualmente wired sob a exceção acima. Formato de linha (contrato lido por `scripts/generate_inventory.py` e `scripts/check-governance.sh`): `` - `<path relativo do artefato>` — valida até AAAA-MM-DD ``. Skills são listadas pelo diretório da skill (`plugins/<p>/skills/<nome>`), agents pelo arquivo `.md` (`plugins/<p>/agents/<nome>.md`). Item validado por uso sai da lista (vira wired pleno); prazo vencido deixa o gate vermelho até a decisão — validar ou demover (D17).

- `plugins/core/skills/bug-report` — valida até 2026-08-06
- `plugins/team/skills/refine-live` — valida até 2026-08-06
- `plugins/team/skills/refine-async` — valida até 2026-08-06
- `plugins/mobile/skills/figma-to-component` — valida até 2026-08-06
- `plugins/council/skills/council` — valida até 2026-08-06
- `plugins/council/skills/bohr` — valida até 2026-08-06
- `plugins/council/skills/sagan` — valida até 2026-08-06
- `plugins/council/skills/council-log` — valida até 2026-08-06
- `plugins/council/skills/council-recall` — valida até 2026-08-06
- `plugins/council/agents/maxwell.md` — valida até 2026-08-06
- `plugins/council/agents/zeno.md` — valida até 2026-08-06
- `plugins/council/agents/epistemic-council.md` — valida até 2026-08-06

Nota: `schrodinger` e `epicurus` NÃO entram — foram wired na extração original com linhagem de uso, não sob a exceção (CHANGELOG, leva 2026-07-07 lista 8 arquivos).

## Meta-princípios

- **Code com ID só nasce com validador.** Toda regra, hook ou skill identificada por um ID nasce junto com o mecanismo que verifica sua aplicação (gate, hook, script) — nunca como texto solto sem enforcement. Este doc aplica a regra a si mesmo: todo ID D*/R* citado no repo precisa resolver no ledger abaixo, verificado por `scripts/check-governance.sh` no gate.
- **Regra textual que falha repetido vira mecanismo.** Sob orçamento de atenção finito, instrução marginal é omitida (não desobedecida) — empilhar mais texto reduz o compliance agregado, não só deixa de melhorar. A regra de maior taxa de falha vira hook, schema de output obrigatório ou gate determinístico, não mais texto.
- **Advisory-nudge não entra em `plugins/` sem medição.** Mecanismo só-lembrete precisa provar conversão real antes de ser wired; caso concreto: `learning-pulse` (tabela por-item em `unwired/README.md`), que mediu ~0 conversão no projeto de origem e só volta com medição nova que sustente o custo.

## Teto do tier sempre-ativo

O tier sempre-ativo do `core` — o corpo de `using-agent-kit` injetado por sessão via `plugins/core/hooks/session-start.sh` — tem teto de **16.384 bytes**, medido sobre a saída real do hook (JSON completo; proxy conservador do payload injetado, envelope e escaping inclusos).

- **Enforcement**: `scripts/check-governance.sh` no gate — vermelho se a medição passar do teto.
- **Efeito pretendido**: pressão de seleção. Regra nova no sempre-ativo compete por espaço; quando o teto aperta, algo sai (vira skill on-demand, mecanismo, ou é deletado) — o teto não sobe por conveniência. Subir o teto é decisão de governança: exige entrada nova no ledger.

## Contrato de SKILL.md (D14)

Formato de autoria de toda skill do kit. Enforcement mecânico: `scripts/check-governance.sh` lê a §Conformidade abaixo.

**Escopo**: skill nova nasce conforme. Skill existente conforma quando for reformada — mudança de esqueleto, propósito ou estrutura; ao ser reformada, entra na §Conformidade. Correção cirúrgica (linhas pontuais que não mudam esqueleto, propósito nem estrutura) não constitui reforma e não obriga conformidade. Sem big-bang no estoque.

### Os três esqueletos

Toda SKILL.md conforme é um destes três. O esqueleto de cada arquivo conformado está nomeado na §Conformidade.

#### `postura` — lente epistêmica in-thread

Muda o raciocínio em curso; não produz artefato.

1. Frontmatter: `name` + `description` com o gatilho situacional citável.
2. Identidade (1–3 linhas): a pergunta que a postura força.
3. Ritual: Restate Gate → deliberação → dispositivo de oposição → cláusula de escalonamento.
4. Formato de saída: o callout do Conselho (`council:council`).

#### `procedimento` — fluxo com efeitos

Passos que alteram estado (commit, PR, arquivos, board).

1. Frontmatter.
2. Propósito (1–2 linhas).
3. Config/pré-requisitos do projeto consumidor — o que o skill assume existir e o que fazer quando falta.
4. Steps numerados — cada um com ação e critério verificável; ponto de aprovação explícito antes de qualquer efeito difícil de reverter.
5. Regras invioláveis — seção final curta.

#### `roteador` — índice que aponta

Mapeia quando ler o quê; não carrega o conteúdo.

1. Frontmatter.
2. O que este índice mapeia (1–2 linhas).
3. Rotas: tabela ou lista "leia X quando Y".
4. Regras de condução, se houver.

Conteúdo técnico inline num roteador é sinal de extração pendente para `REFERENCE.md`.

### Política de idioma

- Corpo em **pt-BR**. `name`, comandos, código, paths e termos técnicos em inglês.
- `description` em pt-BR, com gatilhos citáveis — frases que o usuário realmente diria.
- Exceção grandfathered: `plugins/core/skills/grill-me/SKILL.md` e o `REFERENCE.md` do mesmo diretório — corpo em inglês por decisão do dono (aproveitamento verbatim do advisor-check absorvido). A `description` e o output pro usuário seguem pt-BR; demais skills seguem o default.

### Teto de linhas

- `SKILL.md` ≤ **120 linhas** (`wc -l`), verificado pelo gate para os arquivos da §Conformidade.
- Excedente extrai para arquivos de apoio no mesmo diretório — `REFERENCE.md` (sinal completo, tabelas, exemplos longos), `PATTERNS.md`, `RECIPES.md`. O modelo é `plugins/mobile/skills/mobx/`.
- Critério do corte: no SKILL.md fica o que o modelo precisa para decidir **se** invoca e **como** começa; o resto é on-demand.
- Isento: `using-agent-kit` — tier sempre-ativo, governado pelo teto de bytes (`docs/GOVERNANCE.md` §Teto).

### Critério slash-only

`disable-model-invocation: true` quando a skill: (a) dispara efeito difícil de reverter (commit, PR, escrita externa consumida por terceiros, board), (b) tem custo alto de execução por orquestração (dispatch de múltiplos agents/subagentes), ou (c) conduz cerimônia longa que não deve começar por iniciativa do modelo. Lente, postura, índice ou referência barata em contexto fica invocável pelo modelo — assim como ferramenta de propósito único disparada por intenção explícita do usuário (ex.: dirigir o app no simulador), mesmo que rode um build. Caso de borda decide pelo custo do disparo errado: skill que só propõe e para (`learn`) pode ser invocável; skill que executa cadeia inteira (`bug-report`) é slash-only.

### Proibições (repo inteiro, não só conformados)

- **Narração de proveniência no corpo de skill** — "promovido de", "de onde veio", "diferente do setup original", datas de promoção. Proveniência mora no `CHANGELOG.md` e no ledger do GOVERNANCE. O marcador mecanizável (`Promovido de` em `plugins/`) é verificado pelo gate; o resto é critério de review.
- **História de correção como seção** — a formulação corrigida vive onde a regra vive; a história vive no git e no `CHANGELOG.md`.

### Conformidade

Lista lida pelo gate: cada arquivo abaixo existe e respeita o teto de linhas. Formato de entrada: `` - `<path>` — <esqueleto> ``.

- `plugins/council/skills/council/SKILL.md` — roteador
- `plugins/mobile/skills/mobx/SKILL.md` — roteador
- `plugins/core/skills/commit/SKILL.md` — procedimento
- `plugins/core/skills/archaeology/SKILL.md` — procedimento
- `plugins/core/skills/grill-me/SKILL.md` — procedimento

## Ledger de decisões

Registro das decisões identificadas por ID (série `D*` = decisão de design, `R*` = requisito de aceite) citadas neste repo. **Decisão nova pega o próximo ID livre da série `D` e nasce com entrada neste ledger** — citar ID sem entrada aqui deixa o gate vermelho. Formato de entrada (contrato lido pelo gate): item de lista iniciando com `- **<ID>** — <decisão>`.

- **D6** — Corpus episódico do Conselho: `outcome` é armazenado e exibido, nunca entra no score/ranqueamento — o corpus registra "casos que aconteceram"; a interpretação é do leitor. Citado em `plugins/council/skills/council-recall/SKILL.md`.
- **D10** — Modelo de 3 estados (wired/unwired/deletado) para todo artefato do kit; elimina a categoria fantasma "testado mas não ligado". Texto normativo: seção "O modelo de 3 estados" deste doc.
- **D13** — Métricas de aceite da extração do kit: tag `gate-day3-pass` e métrica-2-semanas (primeiro uso real em projeto fora do projeto de origem dentro do prazo, senão o resultado foi "inventário com README"). Registro e datas: `CHANGELOG.md` §Métricas D13.
- **R2** — Requisito de aceite da extração: medir o custo real de payload do kit (tokens/turno + injeção de sessão) e rodar A/B comportamental com e sem o kit. Resultados e lacunas conhecidas da medição: `CHANGELOG.md` §Aceite final (c).
- **D14** — Contrato de SKILL.md: três esqueletos nomeados (postura / procedimento / roteador), política de idioma (corpo pt-BR; exceção grandfathered: grill-me) e teto de 120 linhas com extração para arquivos de apoio. Texto normativo e lista de conformidade: §Contrato de SKILL.md deste doc; enforcement: `scripts/check-governance.sh` (conformidade + proibição de narração de proveniência em `plugins/`).
- **D15** — Identidade e estrutura em 4 plugins: `core` (metodologia de entrega com enforcement determinístico, do ticket ao PR, qualquer stack), `council` (lentes epistêmicas para decisões de alto custo de reversão), `team` (copiloto de cerimônias ágeis — refinamento com PO, comunicação de squad), `mobile` (toolkit Flutter/Dart). Teste de coerência para skill nova: não cabe em nenhuma frase de identidade ⇒ não entra em nenhum plugin. Inclui a emenda ao texto de D10 (wired vive em `plugins/<plugin>/`). Condição do censo preservada na extração do council: zero reforma interna, descriptions idênticas módulo namespace, `council` instalado onde `core` estiver (`docs/OPERATIONS.md` §1). Validadores: `claude plugin validate .` (manual, fora do CI) + `python3 scripts/generate_inventory.py --check` (CI).
- **D17** — Marcador wired-provisório machine-readable com prazo (§Provisórios ativos deste doc): INVENTORY marca o item, prazo vencido deixa o gate vermelho até validar ou demover. Enforcement: `scripts/check-governance.sh` (check 5) + `scripts/generate_inventory.py` (marcador ⏳).
