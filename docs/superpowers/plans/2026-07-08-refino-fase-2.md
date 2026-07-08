# Refino Fase 2 — Reestruturação em 4 plugins (D15) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extrair `plugins/council` e `plugins/team` do `core`, varrer o namespace `core:*` → `council:*`/`team:*`, fundir `advisor-check` no `grill-me`, adicionar a matriz de decisão ao `pipeline` e o aviso mecânico de dependência inter-plugin — com os 5 gates verdes em **cada commit**.

**Architecture:** 8 tasks sequenciais, commit por task **direto na `main`** (autorizado pelo operador em 2026-07-08; **push é ação do operador, nunca deste fluxo**). O move é um commit atômico (gates acoplam git mv + manifests + paths do GOVERNANCE/SKILL-CONTRACT + INVENTORY). A fusão roda ANTES do sweep (o pipeline referencia `core:advisor-check` legitimamente até a fusão existir). Fecha com review adversarial do range completo (histórico: 15 defeitos num move "mecânico" anterior).

**Tech Stack:** Claude Code plugin manifests (JSON), skills em Markdown, hooks em bash (+python3 stdlib inline), scripts python3 stdlib, evals tier-1 determinísticos (JSONL + bash).

**Fonte:** `docs/superpowers/specs/2026-07-07-refino-pos-auditoria-design.md` §3–§7 (Fase 2 = §5, D15 = §6). Rastro da Fase 1: `.superpowers/sdd/progress.md`.

## Global Constraints

- **Gate quíntuplo verde antes de cada commit** (rodar da raiz do repo):
  ```bash
  bash scripts/check-provenance.sh
  claude plugin validate .          # NÃO está no CI — só local; obrigatório em toda task
  ./evals/run-evals.sh
  python3 scripts/generate_inventory.py --check
  bash scripts/check-governance.sh
  ```
- **NO-PUSH**: nenhum `git push` neste fluxo. Commits na `main` autorizados por task.
- **Council intacto**: nos 11 artefatos do council (7 skills, 3 agents, POSITIONING.md), a ÚNICA mudança permitida é substituição mecânica de namespace/path (`core:X`→`council:X`, `/core:X`→`/council:X`, `plugins/core/`→`plugins/council/`). Nenhuma outra palavra muda — condição do censo (spec §3.3).
- **INVENTORY.md nunca à mão**: sempre `python3 scripts/generate_inventory.py` e commit do resultado no MESMO commit que mudou skills/agents/hooks/descriptions.
- **Não citar `D16`** em nenhum arquivo fora de `docs/superpowers/` — o check 2 do `check-governance.sh` deixa o gate vermelho para ID citado sem entrada no ledger (D16 é da Fase 3).
- **Todo grep de aceite** usa `--exclude-dir=superpowers --exclude-dir=.superpowers` — a spec e este plano contêm os padrões varridos, por citação legítima. NUNCA "corrigir" a spec ou este plano.
- **CHANGELOG histórico é imutável** — entradas antigas descrevem o estado da época (ex.: "em `plugins/core/skills/`"); não reescrever.
- Idioma (D14): corpo de skill pt-BR; código/comandos/paths em inglês. Exceção (decisão do dono 2026-07-08): o **grill-me fundido inteiro** (SKILL.md + REFERENCE.md) fica em inglês — aproveitamento verbatim do advisor-check, sem risco de tradução. `description` permanece pt-BR (cláusula própria do D14). A questão "kit inteiro em inglês?" fica registrada como decisão pendente pra Fase 3/censo (Task 8, Step 3).
- Scripts novos: linha 2 = `# desc: ...` (obrigatório — `generate_inventory.py` falha alto sem ela); commands em hooks.json seguem `"${CLAUDE_PLUGIN_ROOT}/..."`; shellcheck-clean (CI roda `find plugins scripts evals -name '*.sh'`).
- Mensagens de commit em inglês, terminadas com `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- Nunca escrever nomes reais de conta/empresa/cliente em arquivo do repo (denylist do `check-provenance.sh` casa por substring).

## Estrutura de arquivos (alvo)

```
plugins/
  core/     14 skills (pipeline, commit, pr, review-local, review-remote, tech-breakdown,
            spec-refine, archaeology, bug-report, learn, compound, methodology,
            using-agent-kit, grill-me[+modo escalação +REFERENCE.md]) · 1 agent
            (consumer-simulation) · hooks e scripts atuais — v0.3.0
  council/  7 skills (council[+POSITIONING.md], bohr, schrodinger, epicurus, sagan,
            council-log, council-recall) · 3 agents (maxwell, zeno, epistemic-council)
            · 1 hook (require-core) — v0.1.0
  team/     3 skills (refine-live, refine-async, chat-draft) · 1 hook (require-core) — v0.1.0
  mobile/   como está + 1 hook (require-core) — v0.2.0
```

Deletado: `plugins/core/skills/advisor-check/` (absorvido pelo grill-me — D10: substituído).

---

### Task 1: Hardening de gates (deferidos #5/#6 da Fase 1)

Protege os dois parsers que as tasks 2 e 7 exercitam (paths de provisórios e conformidade mudam no move). Verificado em 2026-07-08: zero mismatch name/dirname hoje (o assert entra verde); a divergência de fronteira `## `/`### ` entre bash e python é real.

**Files:**
- Modify: `scripts/generate_inventory.py` (função `collect_skills`, ~linha 189)
- Modify: `scripts/check-governance.sh` (check 5, linha 99)

**Interfaces:**
- Consumes: nada de tasks anteriores.
- Produces: `collect_skills` levanta `InventoryError` em mismatch frontmatter-name/dirname; check 5 do bash para a seção em QUALQUER heading `## `/`### ` (mesma semântica de `collect_provisional`).

- [ ] **Step 1: Assert name==dirname em `collect_skills`**

Em `scripts/generate_inventory.py`, logo após `fm = parse_frontmatter(skill_md)` e os dois checks de presença de `name`/`description`, adicionar:

```python
        if fm["name"] != name:
            raise InventoryError(
                f"{rel(skill_md)}: frontmatter name '{fm['name']}' difere do diretório '{name}'"
            )
```

(`name` é a variável do loop `for name in sorted(os.listdir(skills_dir))`.)

- [ ] **Step 2: Alinhar a fronteira de seção no check 5**

Em `scripts/check-governance.sh` linha 99, trocar:

```bash
section=$(sed -n '/^### Provisórios ativos/,/^## /p' "$LEDGER")
```

por:

```bash
section=$(sed -n '/^### Provisórios ativos/,/^##\{1,2\} /p' "$LEDGER")
```

BRE `^##\{1,2\} ` casa `## ` e `### ` (com espaço) — mesma condição de parada do python (`generate_inventory.py:61`). O sed range só testa o padrão de fim a partir da linha SEGUINTE ao início, então a própria linha `### Provisórios ativos` não encerra o range.

- [ ] **Step 3: Teste negativo do assert (temporário, fora do commit)**

```bash
mkdir -p plugins/core/skills/zz-eval-mismatch
printf -- '---\nname: outro-nome\ndescription: teste\n---\ncorpo\n' > plugins/core/skills/zz-eval-mismatch/SKILL.md
python3 scripts/generate_inventory.py --check; echo "exit=$?"
rm -rf plugins/core/skills/zz-eval-mismatch
```

Esperado: `ERRO: plugins/core/skills/zz-eval-mismatch/SKILL.md: frontmatter name 'outro-nome' difere do diretório 'zz-eval-mismatch'` e `exit=1`. Depois do `rm -rf`, rodar de novo e esperar `OK` e `exit=0`.

- [ ] **Step 4: Gate quíntuplo completo** — todos verdes; `check-governance.sh` deve seguir reportando `OK: provisórios dentro do prazo (12 itens, D17)`.

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_inventory.py scripts/check-governance.sh
git commit -m "harden(gates): assert skill name==dirname; align provisional section boundary with parser"
```

---

### Task 2: Move atômico — extrair `plugins/council` e `plugins/team` (D15)

Um commit só: os gates acoplam git mv + manifests + marketplace + paths no GOVERNANCE/SKILL-CONTRACT + `PLUGINS` do gerador + INVENTORY regen. A emenda D10 e a entrada D15 nascem AQUI (decisão nasce com entrada no ledger; GOVERNANCE já é editado nesta task). **Não** editar o conteúdo dos arquivos movidos (namespace é Task 4).

**Files:**
- Move (git mv): 7 dirs de skill + 3 agents → `plugins/council/`; 3 dirs de skill → `plugins/team/`
- Create: `plugins/council/.claude-plugin/plugin.json`, `plugins/team/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`, `plugins/core/.claude-plugin/plugin.json`, `scripts/generate_inventory.py`, `docs/GOVERNANCE.md`, `docs/SKILL-CONTRACT.md`
- Regen: `INVENTORY.md`

**Interfaces:**
- Consumes: parsers endurecidos da Task 1.
- Produces: 4 plugins validando; paths novos `plugins/council/skills/<nome>`, `plugins/council/agents/<nome>.md`, `plugins/team/skills/<nome>` — usados pelas Tasks 4, 6, 7; entrada `- **D15**` no ledger (qualquer texto posterior pode citar D15).

- [ ] **Step 1: git mv**

```bash
mkdir -p plugins/council/skills plugins/council/agents plugins/team/skills
for s in council bohr schrodinger epicurus sagan council-log council-recall; do
  git mv "plugins/core/skills/$s" "plugins/council/skills/$s"
done
for a in maxwell.md zeno.md epistemic-council.md; do
  git mv "plugins/core/agents/$a" "plugins/council/agents/$a"
done
for s in refine-live refine-async chat-draft; do
  git mv "plugins/core/skills/$s" "plugins/team/skills/$s"
done
```

(`POSITIONING.md` e os `.py` de council-log/recall viajam dentro dos dirs. `council-log/SKILL.md` e `council-recall/SKILL.md` usam `${CLAUDE_PLUGIN_ROOT}/skills/...` — estrutura relativa preservada, continuam corretos sem edição.)

- [ ] **Step 2: Manifests novos**

Create `plugins/council/.claude-plugin/plugin.json`:

```json
{
  "name": "council",
  "description": "Lentes epistêmicas para decisões de alto custo de reversão",
  "author": {
    "name": "Arthur Avila"
  },
  "version": "0.1.0"
}
```

Create `plugins/team/.claude-plugin/plugin.json`:

```json
{
  "name": "team",
  "description": "Copiloto de cerimônias ágeis — refinamento com PO, comunicação de squad",
  "author": {
    "name": "Arthur Avila"
  },
  "version": "0.1.0"
}
```

- [ ] **Step 3: marketplace.json** — inserir entre `core` e `mobile`, e atualizar a description raiz (cirúrgico; identidade completa é Fase 3):

```json
    {
      "name": "council",
      "source": "./plugins/council",
      "description": "Lentes epistêmicas para decisões de alto custo de reversão — instalar sempre junto do core",
      "category": "development"
    },
    {
      "name": "team",
      "source": "./plugins/team",
      "description": "Copiloto de cerimônias ágeis: refinamento com PO, triage pós-agenda, comunicação de squad",
      "category": "development"
    },
```

Description raiz do marketplace vira:

```
Metodologia pessoal de engenharia com agentes em 4 plugins: disciplina epistêmica e workflow (core), lentes de decisão (council), cerimônias ágeis (team) e toolkit Flutter/MobX (mobile). Extraído de uso real, genericizado, com governança de promoção por uso.
```

- [ ] **Step 4: Bump do core** — `plugins/core/.claude-plugin/plugin.json`: `"version": "0.2.1"` → `"0.3.0"` (breaking: 10 skills e 3 agents saem do namespace). Mobile NÃO muda nesta task (bump na Task 6, quando ganha hook).

- [ ] **Step 5: generate_inventory.py** — duas edições:

```python
PLUGINS = ["core", "council", "team", "mobile"]
```

e no banner de `generate()`, trocar:

```python
        "rodam só via comando explícito (`/core:<nome>`, `/mobile:<nome>`), nunca por "
```

por:

```python
        "rodam só via comando explícito (`/<plugin>:<nome>`), nunca por "
```

- [ ] **Step 6: docs/GOVERNANCE.md** — quatro edições:

(a) §Provisórios ativos — atualizar 10 paths (deadlines inalterados; `bug-report` e `figma-to-component` não mudam):

```
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
```

(b) Emenda D10 — no bullet `- **wired**` do §O modelo de 3 estados, trocar `vive em \`plugins/core/\` ou \`plugins/mobile/\`` por `vive em \`plugins/<plugin>/\` (hoje: \`core\`, \`council\`, \`team\`, \`mobile\`)`. Na §Regra de promoção, passo 3, trocar `plugins/<core|mobile|novo-plugin>/` por `plugins/<plugin>/`.

(c) Citação do D6 — trocar `plugins/core/skills/council-recall/SKILL.md` por `plugins/council/skills/council-recall/SKILL.md`.

(d) Entrada D15 no ledger (após a entrada D14, antes da D17; SEM citar o ID da governança de descriptions da Fase 3):

```
- **D15** — Identidade e estrutura em 4 plugins: `core` (metodologia de entrega com enforcement determinístico, do ticket ao PR, qualquer stack), `council` (lentes epistêmicas para decisões de alto custo de reversão), `team` (copiloto de cerimônias ágeis — refinamento com PO, comunicação de squad), `mobile` (toolkit Flutter/Dart). Teste de coerência para skill nova: não cabe em nenhuma frase de identidade ⇒ não entra em nenhum plugin. Inclui a emenda ao texto de D10 (wired vive em `plugins/<plugin>/`). Condição do censo preservada na extração do council: zero reforma interna, descriptions idênticas módulo namespace, `council` instalado onde `core` estiver (`docs/OPERATIONS.md` §1). Validadores: `claude plugin validate .` (manual, fora do CI) + `python3 scripts/generate_inventory.py --check` (CI).
```

- [ ] **Step 7: docs/SKILL-CONTRACT.md §Conformidade** — trocar `plugins/core/skills/council/SKILL.md` por `plugins/council/skills/council/SKILL.md`.

- [ ] **Step 8: Regen + gates**

```bash
python3 scripts/generate_inventory.py
```

Esperado: `OK: INVENTORY.md gerado.` com 4 seções de plugin (core 15 skills/1 agent neste ponto — advisor-check ainda existe; council 7/3; team 3/0; mobile 10/1). Gate quíntuplo completo — `check-governance.sh` deve reportar `OK: provisórios dentro do prazo (12 itens, D17)` e o census de IDs deve listar D15.

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "feat(structure): extract council and team plugins (D15) — mechanical move, no internal reform"
```

---

### Task 3: Fusão `advisor-check` → `grill-me` (dois modos)

ANTES do sweep: o pipeline referencia `core:advisor-check` legitimamente até aqui. Fusão = reforma (SKILL-CONTRACT §Escopo) ⇒ o grill-me entra na §Conformidade como `procedimento` e respeita ≤120 linhas, com a mecânica longa extraída para `REFERENCE.md`. Idioma (decisão do dono 2026-07-08): skill fundida inteira em inglês (corpo + REFERENCE.md) — conteúdo do advisor-check aproveitado verbatim, sem tradução; `description` fica pt-BR (cláusula de description do D14); exceção do contrato alargada pra skill fundida.

**Files:**
- Rewrite: `plugins/core/skills/grill-me/SKILL.md`
- Create: `plugins/core/skills/grill-me/REFERENCE.md`
- Delete: `git rm -r plugins/core/skills/advisor-check`
- Modify: `docs/SKILL-CONTRACT.md` (§Política de idioma + §Conformidade), `plugins/core/skills/pipeline/SKILL.md` (linhas 39, 42, 46), `unwired/WORKFLOW.md` (entradas advisor-check/grill-me)
- Regen: `INVENTORY.md`

**Interfaces:**
- Consumes: nada da Task 2 (fusão é core-interna).
- Produces: skill única `core:grill-me` com modos `entrevista` (default) e `escalação` (`pre-plan|post-plan|pre-done`); rota de pipeline `core:grill-me` nos estágios Checkpoint e Revisar — o sweep (Task 4) e a matriz (Task 5) dependem desses nomes.

- [ ] **Step 1: Rewrite `plugins/core/skills/grill-me/SKILL.md`** (conteúdo integral):

```markdown
---
name: grill-me
description: Invoque quando o usuário pedir para "me grillar" / "grill me", pressionar uma decisão de design, ou antes de dar um plano por pronto (modo entrevista); ou nos checkpoints determinísticos pre-plan / post-plan / pre-done para escalar a um reviewer mais forte com contexto controlado ou cego (modo escalação, ex.: `/core:grill-me pre-done`).
---

# grill-me — relentless interview + checkpoint escalation

One skill, two modes. Mode selection happens in the first lines of the request:

- **No argument** (or a "grill me" / challenge-my-decision request) → **interview mode**.
- **Argument `pre-plan <TICKET> [--greenfield]` | `post-plan` | `pre-done`** → **escalation mode** (absorbs the former escalation-checkpoint skill; same checkpoint semantics).
- Invalid argument → show the usage above and stop.

## Interview mode

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time.

If a question can be answered by exploring the codebase, explore the codebase instead.

For structured interrogation with a formal artifact (Gap Summary) in the tech-breakdown pipeline, see `core:spec-refine` (if available in this kit) instead of this mode.

## Escalation mode

Deterministic escalation to a stronger reviewer at a checkpoint YOU pick — breaks the session's epistemic bubble. Complements Claude Code's native advisor (`/advisor`); does not replace it.

Consumer-project config and prerequisites (advisor model, architecture doc, rule files, ticket source): `REFERENCE.md` in this directory — the skill still runs without them, with less specialized context.

| Mode | Mechanism | When |
|---|---|---|
| `pre-plan <TICKET>` | native advisor (full context) | before choosing an approach; `--greenfield` firewalls the project's rules |
| `post-plan` | native advisor (full context) | plan approved, before coding |
| `pre-done` | blind adversarial subagent (diff + ACs only) | "I think I'm done", before final review |

Inviolable rules of escalation mode:

1. **Propose and stop.** Findings are signal, not decision — present them and ask how to proceed (`address-all` / `address-selected <n,m,...>` / `note-as-followup` / `ignore`). Never apply fixes automatically; never modify code inside this skill.
2. **Confirm before dispatch.** `pre-done` dispatches a subagent — confirm with the user before dispatching whenever the invocation did not come from their explicit command.
3. **The checkpoint is never skipped.** With no advisor configured, fall back to an equivalent subagent (full context for `pre-plan`/`post-plan`) and disclose the substitution.
4. **Narrative withheld in `pre-done`.** The blind subagent gets only diff + ACs + rule-file paths — never the plan, the commits, or the session's rationale.

Full mechanics (per-mode context loading, framings, findings schema, citation verification, presentation format): `REFERENCE.md` in this directory.
```

Contar linhas: `wc -l plugins/core/skills/grill-me/SKILL.md` ≤ 120.

- [ ] **Step 2: Create `plugins/core/skills/grill-me/REFERENCE.md`** — aproveitamento **verbatim em inglês** do conteúdo do `plugins/core/skills/advisor-check/SKILL.md` atual (ler o arquivo ANTES do `git rm`; sem tradução — decisão do dono 2026-07-08), reorganizado nesta ordem de seções:

1. `# grill-me escalation mode — reference` (título novo; parágrafo de abertura + §"Two mechanisms, by design" verbatim, incluindo a tabela).
2. `## Consumer-project config` — a lista de 6 itens verbatim (§"Config do projeto" do original) + a frase "sem essas configs, roda com menos contexto".
3. `## Advisor prerequisite` — verbatim: `/advisor <model>` ou `"advisorModel"` em settings (Claude Code ≥ v2.1.98, API Anthropic); sem advisor → fallback subagent contexto-cheio, checkpoint nunca pulado.
4. `## Ticket source` — verbatim: nunca hardcodar nome de tool MCP; resolver a tool get-issue em runtime; sem tracker → pedir o texto colado.
5. `## Steps per mode` — steps 2–4 do original verbatim (carga de contexto por modo, incluindo a regra `--greenfield` de NÃO carregar rules/skills/estrutura; os três framings; verificação de citações no `pre-done` com session id explícito e bucket "⚠️ Não-verificadas" = hipótese, nunca finding confirmado).
6. Schema de findings (bloco JSON verbatim):

```json
[{ "claim": "...", "epistemicSource": "tool-output",
   "evidence": {"file": "...", "lineStart": 1, "lineEnd": 2},
   "severity": "critico|atencao|consideracao", "rule": "CODE|null" }]
```

7. `## Presentation format` — o bloco de formato do original verbatim, INCLUSIVE a instrução "Present findings to the user in pt-BR" e o template pt-BR (Críticos 🔴 / Atenção 🟡 / Considerações 🟣 / ⚠️ Não-verificadas): o corpo da skill é EN, mas o output pro usuário permanece pt-BR.
8. `## Important` — os bullets finais do original verbatim (sinal-não-decisão; independência estrutural do pre-done; sem captura de memória dentro da skill — apontar `core:learn`; ordem típica: pre-plan → antes de writing-plans, post-plan → após aprovação, pre-done → antes de `core:review-local`; quando usar o advisor nativo vs esta skill).

Invariantes do aproveitamento (o reviewer da task confere): nenhum passo/seção omitido do original; schema e comandos intactos; toda string de invocação do antigo comando atualizada para `/core:grill-me <modo>`; **o token literal do nome da skill antiga NÃO aparece em nenhum arquivo produzido** (SKILL.md, REFERENCE.md — o grep de aceite das Tasks 3/8 exige zero hits em `plugins/`; referências à origem reformuladas como "the former escalation-checkpoint skill"); zero narração de proveniência ("promovido de" etc.).

- [ ] **Step 3: Delete**

```bash
git rm -r plugins/core/skills/advisor-check
```

- [ ] **Step 4: docs/SKILL-CONTRACT.md** — duas edições:

(a) §Política de idioma, substituir a linha da exceção por:

```
- Exceção grandfathered (alargada na fusão de 2026-07-08): `plugins/core/skills/grill-me/SKILL.md` e o `REFERENCE.md` do mesmo diretório — corpo em inglês por decisão do dono (aproveitamento verbatim do advisor-check absorvido). A `description` e o output pro usuário seguem pt-BR; demais skills seguem o default.
```

(b) §Conformidade, adicionar:

```
- `plugins/core/skills/grill-me/SKILL.md` — procedimento
```

- [ ] **Step 5: pipeline/SKILL.md** — três linhas:

- Linha 39: `| Checkpoint | \`core:advisor-check\` post-plan | — | veredito |` → `| Checkpoint | \`core:grill-me\` modo escalação \`post-plan\` | — | veredito |`
- Linha 42: `| Revisar | \`core:review-local\` + \`core:advisor-check\` pre-done | — | findings resolvidos |` → `| Revisar | \`core:review-local\` + \`core:grill-me\` modo escalação \`pre-done\` | — | findings resolvidos |`
- Linha 46: remover `advisor-check` da lista slash-only: `(\`archaeology\`, \`spec-refine\`, \`tech-breakdown\`, \`review-local\`, \`commit\`, \`pr\`, \`compound\`)`.

- [ ] **Step 6: unwired/WORKFLOW.md** — quatro pontos (grep `advisor-check` no arquivo para não perder nenhum):

- Linha ~23 (fluxo Feature): `advisor-check pre-plan <TICKET>` → `grill-me pre-plan <TICKET>`; `advisor-check post-plan` → `grill-me post-plan`; `advisor-check pre-done` → `grill-me pre-done`.
- Linha ~25 (fluxo Refactor): `advisor-check pre-plan` → `grill-me pre-plan`.
- Linha ~38 (entrada `grill-me` na lista de skills): reescrever para citar os dois modos (entrevista default; escalação `pre-plan`/`post-plan`/`pre-done` absorvida do antigo checkpoint de escalação — NÃO escrever o token literal do nome da skill antiga: o grep de aceite da Task 8 exige zero hits em `unwired/`).
- Linhas ~78–82 (bloco `advisor-check <modo>`): remover o bloco; o conteúdo já está resumido na entrada do grill-me.

- [ ] **Step 7: Regen + gates** — `python3 scripts/generate_inventory.py` (linha advisor-check some; description do grill-me muda; core: 14 skills). Gate quíntuplo. Conferir: `grep -rn "advisor-check" plugins/ INVENTORY.md` → zero hits.

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "feat(core): merge advisor-check into grill-me as escalation mode (D10: superseded)"
```

---

### Task 4: Sweep de namespace `core:*` → `council:*` / `team:*`

Substituição mecânica. Nos artefatos do council: SÓ namespace/path, nenhuma outra palavra (condição do censo). Grep-driven: os pontos listados abaixo são os conhecidos; o subagente re-grepa antes de fechar.

**Files:**
- Modify: `plugins/council/skills/{council,bohr,sagan,council-log,council-recall}/SKILL.md`, `plugins/council/agents/{maxwell,zeno,epistemic-council}.md` (e `schrodinger`/`epicurus` SE o grep achar — hoje não têm refs)
- Modify: `plugins/team/skills/{refine-live,refine-async}/SKILL.md`
- Modify: `plugins/core/skills/using-agent-kit/SKILL.md`, `plugins/core/skills/pipeline/SKILL.md`
- Modify: `docs/SKILL-CONTRACT.md`, `README.md`, `unwired/WORKFLOW.md`, `unwired/README.md`
- Regen: `INVENTORY.md`

**Interfaces:**
- Consumes: paths novos da Task 2; rotas de pipeline pós-fusão da Task 3.
- Produces: namespace limpo — critério de aceite do grep abaixo; README com contagens/instalação corretas que a Task 7 NÃO retoca.

- [ ] **Step 1: Substituições no council** (mecânicas; conferir cada arquivo com grep antes/depois):

- `council/SKILL.md`: `/core:bohr` `/core:sagan` `/core:epicurus` `/core:schrodinger` → `/council:...` (2 ocorrências de cada, linhas 35 e 39); `/core:council-log`, `/core:council-recall` → `/council:...` (linha 39); `plugins/core/agents/zeno.md` → `plugins/council/agents/zeno.md` (linha 35).
- `bohr/SKILL.md`: description `(core:council)` → `(council:council)`; linha 15 `a skill \`core:council\`` → `\`council:council\``.
- `sagan/SKILL.md`: description `(core:council)` → `(council:council)` e `core:epicurus` → `council:epicurus`; linha 15 idem bohr.
- `council-log/SKILL.md`: description `(core:schrodinger/bohr/epicurus/sagan ...)` → `(council:schrodinger/bohr/epicurus/sagan ...)`; header `# /core:council-log` → `# /council:council-log`.
- `council-recall/SKILL.md`: header `# /core:council-recall` → `# /council:council-recall`.
- `agents/maxwell.md` e `agents/zeno.md`: description `(skill core:council)` → `(skill council:council)`; linha 16 `ver a skill \`core:council\`` → `\`council:council\``.
- `agents/epistemic-council.md`: description `(skill core:council)` → `(skill council:council)`; `/core:council-recall` → `/council:council-recall` (linha 43); `/core:council-log` → `/council:council-log` (linha 47).

- [ ] **Step 2: Substituições no team**: em `refine-live/SKILL.md` e `refine-async/SKILL.md`, TODAS as ocorrências de `/core:refine-live` → `/team:refine-live` e `/core:refine-async` → `/team:refine-async` (≈16 ocorrências somadas — o grep de aceite é a fonte de verdade, não esta contagem). NÃO tocar `/core:archaeology`, `/core:spec-refine`, `archaeology → tech-breakdown` (ficam no core). `chat-draft/SKILL.md`: contém `core:commit`/`core:pr` (linha ~39) — apontam para skills que PERMANECEM no core; **NÃO converter** (o padrão de aceite não cobre `commit`/`pr`, então uma conversão indevida passaria pelos gates até a Task 8).

- [ ] **Step 3: Consumidores no core**: `using-agent-kit/SKILL.md` linha 183 `em \`core:council\`` → `em \`council:council\``; `pipeline/SKILL.md` linha 36: `core:schrodinger` → `council:schrodinger` (2×).

- [ ] **Step 4: docs/SKILL-CONTRACT.md** linha 18 (esqueleto postura): `o callout do Conselho (\`core:council\`)` → `(\`council:council\`)`.

- [ ] **Step 5: README.md cirúrgico** (a reescrita de identidade é Fase 3 — aqui só correção factual):

- Linha 3: `distribuídos como dois plugins instaláveis via marketplace local: **\`core\`** (qualquer stack) e **\`mobile\`** (Flutter/Dart)` → `distribuídos como quatro plugins instaláveis via marketplace local: **\`core\`** (metodologia, qualquer stack), **\`council\`** (lentes de decisão), **\`team\`** (cerimônias ágeis) e **\`mobile\`** (Flutter/Dart)`.
- Linha 18: `25 skills, 4 agents, 7 hooks e 5 scripts` → `14 skills, 1 agent, 7 hooks e 5 scripts`.
- Remover o bullet do `core:council` (linha 23) da seção do core e inserir após a seção do core:

```markdown
### `council` — lentes epistêmicas (instalar junto do `core`)

7 skills, 3 agents, 1 hook. Conselho de Posturas: 6 lentes (Schrödinger, Bohr, Epicurus, Sagan, Maxwell, Zeno) para decisões de alto custo de reversão — índice em `council:council`.

### `team` — cerimônias ágeis

3 skills, 1 hook. `/team:refine-live` (copiloto da agenda de refinamento com o PO), `/team:refine-async` (triage pós-agenda) e `team:chat-draft` (mensagens de squad).
```

- Linha 24: `core:learn + /core:compound` fica (core).
- Seção Instalação, passo 2: adicionar após a linha do core: `claude plugin install council@agent-kit  # acompanha o core — condição do censo de validação das posturas` e `claude plugin install team@agent-kit     # opcional: cerimônias ágeis com PO/squad`.
- Passo 3 (`claude plugin list`): citar os quatro.
- Seção Desinstalar: adicionar `claude plugin uninstall team@agent-kit` e `claude plugin uninstall council@agent-kit` antes do core.
- §Estrutura do repositório, linha da tabela `plugins/`: `Os dois plugins instaláveis (\`core\`, \`mobile\`)` → `Os quatro plugins instaláveis (\`core\`, \`council\`, \`team\`, \`mobile\`)`.

- [ ] **Step 6: unwired/**: `WORKFLOW.md` linha ~84: `/core:refine-live` / `/core:refine-async` → `/team:...` e `(plugins/core/skills/)` → `(plugins/team/skills/)`; grep `plugins/core` no arquivo e corrigir refs stale a artefatos movidos (ex.: linha ~72). `unwired/README.md` linha ~21: `plugins/core/skills/` → `plugins/council/skills/` (frase sobre Schrödinger/Epicurus).

- [ ] **Step 7: Regen + aceite**

```bash
python3 scripts/generate_inventory.py
grep -rEn "core:(council|bohr|schrodinger|epicurus|sagan|refine-|chat-draft|advisor-check)" \
  plugins/ docs/ README.md INVENTORY.md unwired/ --exclude-dir=superpowers --exclude-dir=.superpowers
echo "exit=$?"
```

Esperado: nenhuma linha, `exit=1`. (CHANGELOG fica fora de propósito — histórico imutável.) Gate quíntuplo completo.

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "refactor(namespace): sweep core:* -> council:*/team:* across plugins and docs"
```

---

### Task 5: Matriz de decisão no `pipeline`

Superfície "desafie meu plano": quando usar cada mecanismo. Critério de aceite da spec: matriz presente E descriptions dos mecanismos INALTERADAS (`git diff` só toca pipeline/SKILL.md).

**Files:**
- Modify: `plugins/core/skills/pipeline/SKILL.md`

**Interfaces:**
- Consumes: nomes pós-fusão (`core:grill-me` modos) da Task 3; namespace `council:*` da Task 4.
- Produces: seção `## 4.` nova; seção "Regras de condução" renumerada para `## 5.`.

- [ ] **Step 1: Inserir a seção** entre `## 3. Estágios → skills` e a atual `## 4. Regras de condução` (que vira `## 5.`):

```markdown
## 4. "Desafie meu plano" — qual mecanismo

| Mecanismo | Estágio | Insumo | Cobre o que os outros não |
|---|---|---|---|
| `core:grill-me` (entrevista) | clarificar; antes de dar plano por pronto | decisões em aberto no thread | extrai o que só o operador sabe; resolve dependências decisão-a-decisão |
| `core:grill-me` (escalação `pre-plan`/`post-plan`/`pre-done`) | checkpoints determinísticos do track | conversa (advisor) ou diff+ACs (subagent cego) | segunda opinião de reviewer mais forte; quebra a bolha epistêmica; não decide pelo operador |
| `/core:spec-refine` | especificar | spec/ticket escrito | stress-test do artefato com Gap Summary formal |
| Conselho (`council:council`) | decisão de alto custo de reversão, em qualquer estágio | a decisão + o lean da conversa | modo de raciocínio (reframe, limites, propagação) — não é review de artefato |

Sobreposição aparente se resolve pelo objeto: entrevista interroga **o operador**; escalação interroga **o trabalho** com outro reviewer; spec-refine interroga **o documento**; o Conselho interroga **o raciocínio**.
```

- [ ] **Step 2: Verificar** — `wc -l plugins/core/skills/pipeline/SKILL.md` ≤ 120; `git diff --stat` toca só esse arquivo; descriptions de grill-me/spec-refine/council intactas (`git diff plugins/core/skills/grill-me plugins/core/skills/spec-refine plugins/council/` vazio). Gate quíntuplo (INVENTORY não muda — corpo não é description; `--check` segue verde sem regen).

- [ ] **Step 3: Commit**

```bash
git add plugins/core/skills/pipeline/SKILL.md
git commit -m "docs(pipeline): add decision matrix for the plan-challenge surface"
```

---

### Task 6: Hook `require-core` em team/council/mobile + evals

Aviso mecânico de dependência inter-plugin (spec 2.5). Checa **instalação** (registro `installed_plugins.json`), não enablement por sessão — limitação documentada honestamente no próprio script. Fail-open: qualquer anomalia (arquivo ausente, JSON ilegível, formato desconhecido, sem python3) = silêncio, exit 0 — falso-aviso é pior que falso-silêncio (meta-princípio advisory-nudge, `docs/GOVERNANCE.md`). Chave presente com array vazio conta como ausente.

**Files:**
- Create: `plugins/team/hooks/require-core.sh`, `plugins/council/hooks/require-core.sh`, `plugins/mobile/hooks/require-core.sh` (byte-idênticos)
- Create: `plugins/team/hooks/hooks.json`, `plugins/council/hooks/hooks.json`
- Modify: `plugins/mobile/hooks/hooks.json`, `plugins/mobile/.claude-plugin/plugin.json` (0.1.1 → 0.2.0)
- Modify: `evals/run-evals.sh` (fixtures + cmp anti-drift), `evals/cases/hook-cases.jsonl` (+5 casos), `README.md` (linha do mobile: contagem de hooks)
- Regen: `INVENTORY.md`

**Interfaces:**
- Consumes: dirs `plugins/team/`, `plugins/council/` da Task 2.
- Produces: hook SessionStart nos 3 plugins; marcador de output `[require-core]` (usado nos casos de eval e no smoke do operador).

- [ ] **Step 1: Escrever os casos de eval PRIMEIRO** (TDD — vão falhar até o hook existir). Adicionar ao fim de `evals/cases/hook-cases.jsonl`:

```jsonl
{"desc": "require-core (team): core ausente do registro dispara aviso", "hook": "plugins/team/hooks/require-core.sh", "env": {"CLAUDE_CONFIG_DIR": "{{TMPDIR}}/agent-kit-evals/require-core-absent", "CLAUDE_PLUGIN_ROOT": "{{REPO_ROOT}}/plugins/team"}, "input": {"hook_event_name": "SessionStart", "session_id": "eval-rc-team"}, "expect_exit": 0, "expect_contains": "[require-core]"}
{"desc": "require-core (council): core ausente do registro dispara aviso", "hook": "plugins/council/hooks/require-core.sh", "env": {"CLAUDE_CONFIG_DIR": "{{TMPDIR}}/agent-kit-evals/require-core-absent", "CLAUDE_PLUGIN_ROOT": "{{REPO_ROOT}}/plugins/council"}, "input": {"hook_event_name": "SessionStart", "session_id": "eval-rc-council"}, "expect_exit": 0, "expect_contains": "[require-core]"}
{"desc": "require-core (mobile): core ausente do registro dispara aviso", "hook": "plugins/mobile/hooks/require-core.sh", "env": {"CLAUDE_CONFIG_DIR": "{{TMPDIR}}/agent-kit-evals/require-core-absent", "CLAUDE_PLUGIN_ROOT": "{{REPO_ROOT}}/plugins/mobile"}, "input": {"hook_event_name": "SessionStart", "session_id": "eval-rc-mobile"}, "expect_exit": 0, "expect_contains": "[require-core]"}
{"desc": "require-core: core presente no registro = silêncio", "hook": "plugins/team/hooks/require-core.sh", "env": {"CLAUDE_CONFIG_DIR": "{{TMPDIR}}/agent-kit-evals/require-core-present", "CLAUDE_PLUGIN_ROOT": "{{REPO_ROOT}}/plugins/team"}, "input": {"hook_event_name": "SessionStart", "session_id": "eval-rc-silent"}, "expect_exit": 0, "expect_not_contains": "require-core"}
{"desc": "require-core: registro inexistente = fail-open silencioso", "hook": "plugins/team/hooks/require-core.sh", "env": {"CLAUDE_CONFIG_DIR": "{{TMPDIR}}/agent-kit-evals/require-core-nowhere", "CLAUDE_PLUGIN_ROOT": "{{REPO_ROOT}}/plugins/team"}, "input": {"hook_event_name": "SessionStart", "session_id": "eval-rc-noreg"}, "expect_exit": 0, "expect_not_contains": "require-core"}
```

- [ ] **Step 2: Fixtures + guard anti-drift em `evals/run-evals.sh`** — adicionar ao bloco de fixtures (após o bloco do context-monitor). Fixtures SINTÉTICAS obrigatórias: **nunca** copiar o `installed_plugins.json` real da máquina (contém paths que a denylist de proveniência casa).

```bash
# require-core: registro sintético com core presente (silêncio) e ausente/array
# vazio (aviso). NUNCA copiar o installed_plugins.json real (proveniência).
mkdir -p "$EVAL_ROOT/require-core-present/plugins" "$EVAL_ROOT/require-core-absent/plugins"
printf '{"version":2,"plugins":{"core@agent-kit":[{"scope":"user","installPath":"/dev/null"}]}}\n' \
  > "$EVAL_ROOT/require-core-present/plugins/installed_plugins.json"
printf '{"version":2,"plugins":{"team@agent-kit":[{"scope":"user","installPath":"/dev/null"}],"core@agent-kit":[]}}\n' \
  > "$EVAL_ROOT/require-core-absent/plugins/installed_plugins.json"

# require-core existe em 3 plugins por cópia byte-idêntica — drift entre as
# cópias falha a suíte antes de qualquer caso rodar. Tolerante a arquivo
# ausente (cópia faltando é pega pelos próprios casos de eval, "hook não
# encontrado" — o cmp valida só o drift entre cópias existentes).
for rc_copy in plugins/team/hooks/require-core.sh plugins/council/hooks/require-core.sh; do
  if [ -f "$REPO_ROOT/$rc_copy" ] && [ -f "$REPO_ROOT/plugins/mobile/hooks/require-core.sh" ] \
     && ! cmp -s "$REPO_ROOT/$rc_copy" "$REPO_ROOT/plugins/mobile/hooks/require-core.sh"; then
    echo "ERRO: $rc_copy diverge de plugins/mobile/hooks/require-core.sh (cópias devem ser byte-idênticas)" >&2
    exit 1
  fi
done
```

- [ ] **Step 3: Rodar evals e ver os 5 casos novos FALHAREM** (`./evals/run-evals.sh` → "✗ require-core ..." ×5, hook não encontrado).

- [ ] **Step 4: Criar o hook** — conteúdo integral, idêntico nos 3 paths (`plugins/{team,council,mobile}/hooks/require-core.sh`):

```bash
#!/usr/bin/env bash
# desc: SessionStart — avisa se core@agent-kit não consta como instalado no registro de plugins (checa instalação, não enablement por sessão; fail-open em qualquer anomalia).
set -uo pipefail
command -v python3 >/dev/null 2>&1 || exit 0
REG="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/plugins/installed_plugins.json"
[ -f "$REG" ] || exit 0
python3 - "$REG" "${CLAUDE_PLUGIN_ROOT:-}" <<'PY'
import json, sys

# Limitação documentada: o registro diz o que está INSTALADO (qualquer escopo),
# não o que está habilitado nesta sessão. Entry project-scoped de outro projeto
# conta como presente (falso-silêncio aceito; falso-aviso é pior — meta-princípio
# advisory-nudge em docs/GOVERNANCE.md). Formato do registro é contrato interno
# do Claude Code ("version": 2 hoje) — qualquer forma inesperada = silêncio.
try:
    with open(sys.argv[1], encoding="utf-8") as f:
        entries = json.load(f).get("plugins", {}).get("core@agent-kit") or []
except Exception:
    sys.exit(0)
if entries:
    sys.exit(0)

plugin = "este plugin"
try:
    with open(sys.argv[2] + "/.claude-plugin/plugin.json", encoding="utf-8") as f:
        plugin = json.load(f).get("name", plugin)
except Exception:
    pass

print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
    "additionalContext": (
        f"[require-core] O plugin '{plugin}' assume as regras sempre-ativas e o "
        "pipeline do core@agent-kit, que não consta como instalado. Instale com: "
        "claude plugin install core@agent-kit"
    )}}))
PY
```

- [ ] **Step 5: hooks.json** — criar `plugins/team/hooks/hooks.json` e `plugins/council/hooks/hooks.json` (idênticos):

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|clear|compact",
        "hooks": [ { "type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/require-core.sh\"" } ]
      }
    ]
  }
}
```

Em `plugins/mobile/hooks/hooks.json`, adicionar a chave `SessionStart` com o mesmo bloco, antes de `PreToolUse`.

- [ ] **Step 6: Bump mobile + contagem no README** — `plugins/mobile/.claude-plugin/plugin.json`: `"0.1.1"` → `"0.2.0"`. No `README.md`, linha do mobile (`10 skills, 1 agent, 4 hooks, 5 scripts e 2 MCP servers`): `4 hooks` → `5 hooks` (o mobile ganha o require-core nesta task; a Task 4 editou o README antes do hook existir).

- [ ] **Step 7: Verificar** — `./evals/run-evals.sh` → 5 casos novos PASSAM (esperado: `Evals tier-1: 40 passou, 0 falhou.` — baseline atual é 35, não 42; 42 é contagem de linhas do arquivo, não de casos); `shellcheck plugins/team/hooks/require-core.sh plugins/council/hooks/require-core.sh plugins/mobile/hooks/require-core.sh` limpo; `python3 scripts/generate_inventory.py` (3 hooks novos entram); gate quíntuplo completo.

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "feat(hooks): require-core SessionStart warning in team/council/mobile + tier-1 evals"
```

---

### Task 7: Emendas de texto — OPERATIONS + CHANGELOG

**Files:**
- Modify: `docs/OPERATIONS.md` (§1 e §3), `CHANGELOG.md` ([Unreleased])

**Interfaces:**
- Consumes: tudo das Tasks 2–6 (a entrada do CHANGELOG descreve o resultado).
- Produces: instrução de instalação acoplada (condição do censo, citada pela entrada D15); registro público da mudança de condição do censo.

- [ ] **Step 1: docs/OPERATIONS.md §1** — no bloco de install do consumidor, trocar as duas linhas de `claude plugin install` por:

```bash
claude plugin install core@agent-kit
claude plugin install council@agent-kit   # acompanha o core SEMPRE — condição do censo de validação das posturas
claude plugin install team@agent-kit      # opcional: cerimônias de refinamento/squad
claude plugin install mobile@agent-kit    # só em projeto Flutter/Dart
```

E adicionar após o bloco:

```markdown
A dependência inter-plugin tem aviso mecânico numa direção só: `team`/`council`/`mobile` avisam no SessionStart se o `core` não consta como instalado (hook `require-core.sh`). A direção reversa (`core` referenciando o Conselho) é coberta por esta instrução de instalação acoplada, não por hook — o `core` funciona sem o `council`, mas o censo de conversão das posturas exige os dois instalados juntos para não confundir conversão com disponibilidade.
```

Atualizar também a linha de update: `claude plugin update core@agent-kit` (e/ou `council@agent-kit`, `team@agent-kit`, `mobile@agent-kit`).

- [ ] **Step 2: docs/OPERATIONS.md §3** — trocar `o plugin usa namespace (\`core:\`/\`mobile:\`)` por `o plugin usa namespace (\`core:\`/\`council:\`/\`team:\`/\`mobile:\`)`.

- [ ] **Step 3: CHANGELOG.md** — adicionar no topo de `### Adicionado` de `[Unreleased]`:

```markdown
- **Fase 2 da onda de refino — reestruturação em 4 plugins (2026-07-08, D15, spec em `docs/superpowers/specs/2026-07-07-refino-pos-auditoria-design.md` §5)** — `plugins/council/` (7 skills, 3 agents do Conselho — move mecânico, zero reforma interna, descriptions idênticas módulo namespace; condição do censo preservada e instalação acoplada ao core em `docs/OPERATIONS.md` §1) e `plugins/team/` (`refine-live`, `refine-async`, `chat-draft`) extraídos do `core`; sweep de namespace `core:*` → `council:*`/`team:*` em plugins, docs, README e unwired; **nota pro censo**: o namespace das posturas mudou no meio da janela de validação (prazo 2026-08-06) — medir conversão por postura na embalagem nova. Fusão `advisor-check` → `grill-me` (modo entrevista + modo escalação `pre-plan`/`post-plan`/`pre-done`; `advisor-check` deletado — D10: substituído; mecânica em `grill-me/REFERENCE.md`, contrato D14: procedimento, exceção de idioma alargada à skill fundida — corpo EN, description e output pt-BR). Matriz de decisão da superfície "desafie meu plano" no corpo do `pipeline`. Hook `require-core.sh` (SessionStart de `team`/`council`/`mobile`): aviso de dependência quando `core@agent-kit` não consta instalado — aviso de instalação quebrada com eval determinística (5 casos tier-1), não nudge comportamental de conversão (meta-princípio advisory-nudge não se aplica). Emenda D10: wired vive em `plugins/<plugin>/`. Versões: core 0.3.0, council 0.1.0, team 0.1.0, mobile 0.2.0. Hardening de gates deferido da Fase 1: assert name==dirname no inventário; fronteira de seção alinhada entre check 5 e parser python.
```

- [ ] **Step 4: Gate quíntuplo** (OPERATIONS/GOVERNANCE sem data nova — a entrada de CHANGELOG carrega as datas; census de IDs: D15/D10/D14/D17 todos resolvem).

- [ ] **Step 5: Commit**

```bash
git add docs/OPERATIONS.md CHANGELOG.md
git commit -m "docs: Fase 2 amendments — coupled install instruction, changelog entry with census note"
```

---

### Task 8: Fechamento — review adversarial do range + registro do censo + handoff

O move mecânico anterior teve 15 defeitos. Este fechamento é obrigatório (spec 2.6) e roda LOCAL (commits diretos na main, sem PR — decisão do operador 2026-07-08; `/core:review-remote` fica disponível pós-push como segunda camada, a critério do operador).

**Interfaces:**
- Consumes: range completo `ab93046..HEAD`.
- Produces: findings tratados; memória de projeto atualizada; handoff com ações do operador.

- [ ] **Step 1: Bateria mecânica completa**

```bash
bash scripts/check-provenance.sh && claude plugin validate . && ./evals/run-evals.sh \
  && python3 scripts/generate_inventory.py --check && bash scripts/check-governance.sh
grep -rEn "core:(council|bohr|schrodinger|epicurus|sagan|refine-|chat-draft|advisor-check)" \
  plugins/ docs/ README.md INVENTORY.md unwired/ --exclude-dir=superpowers --exclude-dir=.superpowers
grep -rn "advisor-check" plugins/ README.md INVENTORY.md unwired/
find plugins scripts evals -name '*.sh' -print0 | xargs -0 shellcheck
```

Esperado: gates verdes; os dois greps sem output (CHANGELOG e docs/superpowers fora — histórico e citação legítima); shellcheck limpo.

- [ ] **Step 2: Review adversarial do range** — despachar reviewer(s) adversarial(is) sobre `git diff ab93046..HEAD` com mandato explícito calibrado no histórico de 15 defeitos: referências cruzadas mortas, placeholders não preenchidos, convenção `/plugin:` não aplicada, contagens erradas (README/INVENTORY), paths stale, tool names inexistentes, aproveitamento do REFERENCE.md que perdeu passo/schema do advisor-check original (diff contra `git show ab93046:plugins/core/skills/advisor-check/SKILL.md`), description do council alterada além do namespace (diff palavra-a-palavra das 11 descriptions vs `git show ab93046:...`). Findings Critical/Important corrigidos e re-verificados antes de fechar; commit de fixes se houver: `fix(review): address adversarial review findings on Fase 2 range`.

- [ ] **Step 3: Registro do censo na memória de projeto (ação do orquestrador, fora do repo)** — no diretório de memória auto-carregada deste projeto (`~/.claude/projects/<slug-deste-repo>/memory/` — o orquestrador conhece o path da própria sessão; NÃO escrever o path literal em arquivo do repo, a denylist de proveniência casa o nome da conta), atualizar `project_council_posturas_pendente.md`: posturas agora em `plugins/council/` sob namespace `council:*` (mudança de condição no meio da janela — anotar que o censo mede conversão na embalagem nova; install acoplado ao core; prazo 2026-08-06 inalterado). Re-grep desse diretório por namespace morto com o mesmo padrão do aceite da Task 4 → corrigir hits se houver (hoje: zero). Registrar também a decisão pendente do dono (2026-07-08): **"kit inteiro em inglês?"** — avaliar na Fase 3/censo junto com identidade pública; decidido que NÃO entra na Fase 2 (mudaria política D14 e condição do censo no meio da janela).

- [ ] **Step 4: Handoff pro operador** — relatório final com: (a) range de commits e estado dos gates; (b) ações do operador: `git push` (dispara o CI), smoke manual num projeto virgem (marketplace local → install dos 4 → sessão nova: injeção do core presente, `/council:bohr` responde, `require-core` silencioso; depois desinstalar o core e ver o aviso), opcional `/core:review-remote` pós-push; (c) findings Minor deferidos, se houver.

---

## Self-review (feito na escrita do plano)

- **Cobertura da spec §5 Fase 2**: 2.1 → Task 2 · 2.2 → Task 4 (+memória na Task 8) · 2.3 → Task 3 · 2.4 → Task 5 · 2.5 → Task 6 · 2.6 → Task 8 · 2.7 → Tasks 2 (D10+D15) e 7 (OPERATIONS). §7 "anotar mudança de condição no censo" → Tasks 7 (CHANGELOG) e 8 (memória). Deferidos Fase 1 #5/#6 → Task 1 (por decisão desta sessão; #8 e TRIVIAL ficam pro censo).
- **Fora de escopo (spec §5 "não fazer")**: nenhuma task reescreve skill por dentro além do grill-me (fusão mandatada), nenhuma reforma no Conselho, nenhum hook de enforcement tocado.
- **Consistência de nomes**: `require-core.sh` / marcador `[require-core]` / `council:council` / `core:grill-me` modos `pre-plan|post-plan|pre-done` — únicos e coerentes entre as tasks.
