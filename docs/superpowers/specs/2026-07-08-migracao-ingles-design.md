# Migração do kit para inglês — design doc

> Doc de design para uma **sessão nova**. Decisão do dono (2026-07-08): todo o conteúdo autorado do kit passa a inglês por padrão; o híbrido pt-BR/EN atual sai. Este doc fixa escopo, decisões e abordagem; a sessão de execução roda `core:pipeline` → refino/plano → subagent-driven a partir daqui.

## 1. Decisão e contexto

Arthur decidiu migrar **todo o conteúdo autorado do kit para inglês, por padrão**. Motivação: compartilhabilidade (GitHub público, audiência não-lusófona) e o incômodo concreto com o híbrido pt-BR-corpo / EN-identificadores dentro do mesmo arquivo.

Esta decisão **encerra a pendência** registrada em `project_pending_decision_kit_language.md` (levantada na Fase 2, adiada pra cá). A política vigente era D14: corpo pt-BR, exceção grandfathered do `grill-me` (EN). A migração **inverte o default** para EN e torna a exceção do grill-me a regra geral.

### Censo — condição waived

O congelamento das descriptions do `council` até 2026-08-06 (condição do censo de conversão das posturas, spec §3.3) é **explicitamente dispensado pelo dono**: "esse censo não me preocupa muito, pois ainda estamos construindo o kit". Consequência registrada: a métrica de **conversão-por-postura** do censo fica inconclusiva (janela mal começou — council/team só instalados 2026-07-08 — e já contaminada pela troca de namespace). O resto do censo (demote de wired sem uso real) continua válido. A migração toca as descriptions do council junto com o resto.

## 2. Escopo

### Entra (→ EN)

- **Corpos de skill**: todos os `SKILL.md` (core 14 · council 7 · team 3 · mobile 10 = 34) + arquivos de apoio (`REFERENCE.md`, `PATTERNS.md`, `RECIPES.md`, `POSITIONING.md`, `PLAYBOOK.md`).
- **Descriptions** (frontmatter): os gatilhos passam a EN. Nota funcional: o match de skill é semântico — description EN ainda casa prompt pt-BR do Arthur; é mudança real mas de baixo risco. Sujeito aos tetos D16 (bytes) — re-medir, EN costuma ser mais compacto.
- **Agents**: todos os `.md` em `plugins/*/agents/`.
- **Tier sempre-ativo**: `using-agent-kit` (corpo injetado por sessão) → EN. Re-medir contra o teto de 16.384 bytes (EN provavelmente enxuga).
- **Docs de superfície**: `README.md`, `docs/GOVERNANCE.md`, `docs/OPERATIONS.md`, `unwired/README.md`, `assets/` (templates de cópia: `CLAUDE.md` skeleton, snippets).
- **Metadados que aparecem no INVENTORY**: linhas `# desc:` de hooks/scripts (`plugins/*/hooks`, `plugins/*/scripts`) → EN; INVENTORY regenerado.
- **Manifests**: campo `description` de `.claude-plugin/plugin.json` e `marketplace.json`.
- **Política D14**: texto da §Política de idioma (hoje em `docs/GOVERNANCE.md` §Contrato) invertido — EN é o default; a exceção grandfathered do grill-me é absorvida na regra geral.

### Fica (pt-BR, fora do escopo)

- **CHANGELOG histórico**: entradas antigas registram o estado da época — regra "histórico imutável". Entradas **novas** (a partir da migração) em EN.
- **Memória do projeto** (`~/.claude/projects/.../memory/`): notas privadas do Arthur + working memory, fora do repo, não é conteúdo shippado do kit.
- **Este design doc e os specs/plans anteriores** em `docs/superpowers/`: são deliverables de construção; ficam como estão (pt-BR). Novos artefatos de fluxo podem nascer em EN a critério da sessão.
- **Mensagens de commit**: já são EN (convenção vigente).

## 3. Decisão aberta (resolver no kickoff da sessão de execução)

**Idioma do OUTPUT em runtime vs. idioma do conteúdo autorado.** Várias skills/agents hardcodam `Output em pt-BR` / `Output em pt-BR (pt-BR)` (ex.: `council:*`, `consumer-simulation`, `team:chat-draft` produz pt-BR por natureza). Isso é eixo distinto de "conteúdo autorado EN". Três leituras:

- **(a) Recomendada — output segue o idioma do usuário, default EN.** Trocar `Output em pt-BR` por `Output in the user's language (default English)`. Arthur continua recebendo pt-BR (Claude espelha o idioma do prompt / o CLAUDE.md dele pede pt-BR); um consumidor não-lusófono recebe EN. Kit verdadeiramente compartilhável.
- **(b) Output sempre EN, hard.** Mais simples, mas Arthur passa a receber output EN das posturas mesmo prompando em pt-BR — atrita com o CLAUDE.md pessoal dele.
- **(c) Exceção declarada**: conteúdo EN, mas output pro usuário permanece pt-BR onde já é. Recria o híbrido que a decisão quer matar.

`team:chat-draft` é caso à parte: ele **gera mensagens pt-BR pro time do Arthur** — o output pt-BR ali é o produto, não híbrido acidental. Provável exceção legítima mesmo em (a)/(b): a skill fica EN no corpo, mas seu output-alvo continua pt-BR por design (o time é lusófono). Confirmar.

## 4. Abordagem sugerida (para a sessão de execução)

- **Não é tradução mecânica.** Cada regra carrega `Sinal`/`Failure mode`, voz de laudo, termos técnicos precisos — tradução exige julgamento. Risco central: **drift semântico** (a regra perder força ou mudar de sentido na tradução). Review adversarial é obrigatório, não opcional.
- **Subagent-driven, um plugin por batch** (ou por skill nos casos densos: `mobx`, `grill-me` já-EN, `pipeline`, `methodology`). Implementador traduz; reviewer confere fidelidade **contra o original pt-BR** (o diff mostra os dois lados), não só fluência do EN.
- **grill-me já está em EN** — serve de referência de voz/registro pro resto; provavelmente intocado (confirmar que o corpo não tem resíduo pt-BR).
- **Gates verdes por batch**: `generate_inventory.py` regen (descriptions mudam), `check-governance.sh` (tetos D16 re-medidos em bytes EN; teto do sempre-ativo re-medido), `check-provenance.sh` (inalterado), `claude plugin validate`, evals. INVENTORY commitado junto.
- **D14**: a inversão da política é **emenda ao texto de D14** (não novo ID) — o ledger congelou pós-Fase-3 e "decisão nova só entra se mudar comportamento de gate"; idioma não é gate-enforced (é critério de review), então amenda-se D14 e registra-se no CHANGELOG. Confirmar essa leitura no kickoff.
- **Ordem**: docs de política (D14 + GOVERNANCE §Contrato) primeiro — fixa a regra nova; depois skills/agents por plugin; README/OPERATIONS por último (descrevem o resultado); using-agent-kit junto ou por último (re-medir teto). Fecha com review adversarial whole-branch (histórico: move grande junta defeitos).

## 5. Riscos declarados

- **Drift semântico na tradução** — mitigar com review que compara contra o original pt-BR, não avalia só o EN isolado.
- **Tetos D16 em bytes**: uma description que passa em pt-BR pode estourar/afundar em EN — re-medir todas; ajustar teto por entrada de ledger só se necessário (não cortar gatilho por caber).
- **Teto do sempre-ativo**: `using-agent-kit` EN precisa ficar ≤16.384 bytes (provável folga; confirmar).
- **Gatilho de invocação**: descriptions EN podem mudar levemente a taxa de auto-descoberta de skill quando o Arthur promptar em pt-BR — aceitável (match semântico), monitorar.
- **Escala**: ~34 SKILL.md + apoio + agents + docs num único move — é a maior reescrita do kit até hoje. Não fazer big-bang num commit; batches revisáveis.
- **Perda da voz**: o pt-BR "direto e sem cerimônia" do Arthur tem um registro; o EN deve manter concisão de laudo, não virar prosa corporativa.

## 6. Aceite

- Zero corpo de skill/agent/doc-de-superfície em pt-BR (grep por marcadores pt-BR comuns — acentuação, "quando", "não", conectivos — como heurística, não prova; review humano fecha).
- D14 §Política de idioma reescrita: EN default; sem exceção grandfathered pendente.
- Todos os 5 gates verdes; INVENTORY regenerado; tetos D16 e do sempre-ativo re-medidos e dentro do limite.
- Decisão de output-language (§3) resolvida e aplicada consistentemente.
- CHANGELOG: entrada nova (em EN) registrando a migração e a emenda de D14; entradas históricas intactas.
- Review adversarial whole-branch rodado; findings de drift tratados antes do merge.
