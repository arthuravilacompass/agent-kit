# Contrato de SKILL.md (D14)

Formato de autoria de toda skill do kit. Complementa `docs/GOVERNANCE.md` — lá vive o ciclo de vida (o que entra, sobe e sai); aqui vive a forma do arquivo. Enforcement mecânico: `scripts/check-governance.sh` lê a §Conformidade deste doc.

**Escopo**: skill nova nasce conforme. Skill existente conforma quando for reformada — ao ser tocada, entra na §Conformidade. Sem big-bang no estoque.

## Os três esqueletos

Toda SKILL.md conforme é um destes três. O esqueleto de cada arquivo conformado está nomeado na §Conformidade.

### `postura` — lente epistêmica in-thread

Muda o raciocínio em curso; não produz artefato.

1. Frontmatter: `name` + `description` com o gatilho situacional citável.
2. Identidade (1–3 linhas): a pergunta que a postura força.
3. Ritual: Restate Gate → deliberação → dispositivo de oposição → cláusula de escalonamento.
4. Formato de saída: o callout do Conselho (`core:council`).

### `procedimento` — fluxo com efeitos

Passos que alteram estado (commit, PR, arquivos, board).

1. Frontmatter.
2. Propósito (1–2 linhas).
3. Config/pré-requisitos do projeto consumidor — o que o skill assume existir e o que fazer quando falta.
4. Steps numerados — cada um com ação e critério verificável; ponto de aprovação explícito antes de qualquer efeito difícil de reverter.
5. Regras invioláveis — seção final curta.

### `roteador` — índice que aponta

Mapeia quando ler o quê; não carrega o conteúdo.

1. Frontmatter.
2. O que este índice mapeia (1–2 linhas).
3. Rotas: tabela ou lista "leia X quando Y".
4. Regras de condução, se houver.

Conteúdo técnico inline num roteador é sinal de extração pendente para `REFERENCE.md`.

## Política de idioma

- Corpo em **pt-BR**. `name`, comandos, código, paths e termos técnicos em inglês.
- `description` em pt-BR, com gatilhos citáveis — frases que o usuário realmente diria.
- Exceção grandfathered: `plugins/core/skills/grill-me/SKILL.md` — corpo-prompt em inglês por decisão do dono (2026-07-07). Não reformar sem decisão nova.

## Teto de linhas

- `SKILL.md` ≤ **120 linhas** (`wc -l`), verificado pelo gate para os arquivos da §Conformidade.
- Excedente extrai para arquivos de apoio no mesmo diretório — `REFERENCE.md` (sinal completo, tabelas, exemplos longos), `PATTERNS.md`, `RECIPES.md`. O modelo é `plugins/mobile/skills/mobx/`.
- Critério do corte: no SKILL.md fica o que o modelo precisa para decidir **se** invoca e **como** começa; o resto é on-demand.
- Isento: `using-agent-kit` — tier sempre-ativo, governado pelo teto de bytes (`docs/GOVERNANCE.md` §Teto).

## Proibições (repo inteiro, não só conformados)

- **Narração de proveniência no corpo de skill** — "promovido de", "de onde veio", "diferente do setup original", datas de promoção. Proveniência mora no `CHANGELOG.md` e no ledger do GOVERNANCE. O marcador mecanizável (`Promovido de` em `plugins/`) é verificado pelo gate; o resto é critério de review.
- **História de correção como seção** — a formulação corrigida vive onde a regra vive; a história vive no git e no `CHANGELOG.md`.

## Conformidade

Lista lida pelo gate: cada arquivo abaixo existe e respeita o teto de linhas. Formato de entrada: `` - `<path>` — <esqueleto> ``.

- `plugins/core/skills/council/SKILL.md` — roteador
- `plugins/mobile/skills/mobx/SKILL.md` — roteador
- `plugins/core/skills/commit/SKILL.md` — procedimento
- `plugins/core/skills/archaeology/SKILL.md` — procedimento
