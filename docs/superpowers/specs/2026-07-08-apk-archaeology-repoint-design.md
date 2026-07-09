# Re-apontamento apk-archaeology v0 — design doc

> Doc de design para uma **sessão de execução PÓS-migração-inglês**. Origem: review
> cega do Fable (2026-07-08) sobre o v0 já mesclado, convergente com evidência de campo
> de um Tech Lead. Fixa problema, objetivo, os 3 moves, a decisão de design aberta e as
> constraints. A execução roda `specify (este doc) → plan → implement` **depois** que a
> migração do kit pro inglês aterrissar. **NÃO commitado; NÃO executar antes da migração**
> (colisão de working tree e de conteúdo — ver §7).

## 1. Problema — a deriva, medida por review cega

Uma review cega do Fable (mandato de altitude, não de código; narrativa da sessão retida
de propósito) julgou o v0 — spec `2026-07-08-apk-archaeology-design.md`, plano
`2026-07-08-apk-archaeology-plan.md`, `SKILL.md`, demo `newpipe-demo.md` — contra o
objetivo de negócio declarado em §1/§11/§13 (acelerar o ciclo de migração nativo→Flutter
+ servir de case medível).

**Veredito:** o v0 virou primariamente **"provar que a extração é segura/correta"** — uma
máquina de confiança de alta qualidade com a tese de aceleração anexada como prosa. Das 5
etapas de §11:

| Etapa (§11) | Ganho prometido | Estado real no v0 |
|---|---|---|
| Spec | spec candidata com evidência citável | matéria-prima calibrada (43 claims em 2 partições **escolhidas à mão**); artefato de handoff **não produzido** |
| Plano | C → sequenciamento de épico | **quebrado** — grafo degenerado, sem join node→arquivo |
| Implementação | B → esqueleto repository/DTO | **ausente** — 125 URLs extraídas, nenhum esqueleto |
| Testes | A → cenário BDD (`legacy-observed`) | **ausente** |
| Validação | diferida pro v2 | diferimento legítimo |

Tudo que recebeu código + teste + número medido é do polo confiança/segurança. Todo
elemento de aceleração está **quebrado**, **ausente** ou **diferido**.

**Achado de origem (verificado contra o texto do spec):** a deriva está gravada no próprio
**critério de aceite da §9**. As 4 linhas do AC são todas de confiança (roda fim-a-fim,
mapa tiered, scorecard, redação dispara). **Nenhuma exige que qualquer linha de §11
funcione.** O v0 podia passar em todos os gates com a tese de aceleração inteira em prosa —
e passou. Corrigir a consequência (produzir o artefato faltante) sem corrigir a origem (o
`define-done`) garante que toda rodada futura derive de novo. Por isso o move #3 existe.

## 2. Validação de campo (por que isto importa agora)

Testemunho informal de um Tech Lead (chat), num engajamento de migração nativo→Flutter:

- **Fato (o que ele disse):** sem acesso aos repositórios antigos → **tiveram que
  descompilar** (feito antes de ele chegar); histórias vêm vagas, pendência pra todo lado,
  **mock pra todo lado**, **os QAs não sabem o que testar**, ambiente caótico, time bom.
- **Inferência (leitura):** o gargalo que ele nomeia é **entender o que o app faz pra saber
  o que construir e testar** — comprehension / spec / oráculo de teste. É o lado
  **aceleração** da tese, não o lado segurança/corretude.

Convergência com o Fable, de fontes independentes: o Fable (cego) diz "construíram a metade
de confiança, deixaram a de aceleração quebrada"; o campo diz "a dor que importa é a de
aceleração". As 3 dores do TL mapeiam direto no artefato de handoff (§4, move #2):

| Dor do TL | Sub-artefato do handoff |
|---|---|
| histórias vagas / "entender o q fazer" | User Story candidata (Dimensão A) → *o que construir* |
| mock pra todo lado | esqueleto DTO da Dimensão B → *contrato real no lugar do mock* |
| QAs não sabem o que testar | Critério de Aceite como Cenário Gherkin → *o que testar* |

**Caveats honestos:** é **n=1 anedótico**, não baseline medido — sustenta *direção*, não ROI.
Pergunta aberta a resolver antes de tratar como validação direta: o engajamento do TL **é o
cliente-alvo** do apk-archaeology ou é adjacente? (Ver `project_kit_thesis_and_roadmap` /
memória.)

## 3. Objetivo do re-apontamento

Trazer o centro de gravidade de volta pra **aceleração** com a **mudança mínima**, operando
sobre o run do NewPipe **que já está em disco** (`~/dev/apk-archaeology-lab/demo-run/newpipe/`
— confirmado presente: `graph.json`, `endpoints.json`, árvore jadx, `newpipe-source` gabarito).
**Sem refazer o v0, sem novo APK, sem nova medição de fidelidade.** A máquina de confiança
construída é o alicerce, não desperdício — não se toca nela pra tirar valor, se completa o
último passo que faltou.

> **Atualização de execução (2026-07-08 — decisão do operador).** No kickoff ficou claro que o
> NewPipe é proxy público **pobre** pro alvo real (Telecorp): **sem WebView** e raso em
> regra de negócio (o §10 do spec original já admitia o 2º eixo). A **frente F1** (re-run em APK
> nova, §6) foi **dobrada neste re-apontamento**: escolhida a **WordPress-Android** (pública, GPLv2,
> híbrida WebView, self-service de compra de domínio) como fixture de aceleração — run em
> `~/dev/apk-archaeology-lab/demo-run/wordpress/`. O run do NewPipe segue como **demo de fidelidade**
> (único gradável); o handoff (`examples/wordpress-handoff.md`) roda sobre o WordPress. Move #1a e #3
> seguem idênticos; **move #1b ganhou um refino verificado no dry-run**: a chave top-level do
> `classify` degenera num blob (`org/wordpress` = 9596 classes), a regra real é prefixo de pacote
> **em profundidade** (raiz + ~3 segmentos). O run WordPress também revelou o **limite WebView** (a
> lógica de compra roda dentro do WebView, invisível à análise estática) — incorporado ao §10.

## 4. Abordagem — os 3 moves (do re-apontamento mínimo do Fable)

### Move #1 — tornar o passo 5 executável

- **1a — `node → arquivo` em `extract_graph.py`.** Hoje `graph.json` guarda só nome simples
  de classe; não dá pra juntar mecanicamente um node ao arquivo/endpoint. Fix: schema
  **aditivo** (recomendado, back-compat) — adicionar `node_files: {classe: [arquivo, ...]}`
  ao output, preservando `nodes` como lista de nomes. (Alternativa mais limpa e disruptiva:
  `nodes` vira lista de objetos `{name, file}` — quebra selftest e consumidores; **não
  escolhida**, YAGNI.) Nome simples colide entre pacotes → o valor é **lista** de arquivos.
- **1b — particionamento por prefixo de pacote** (§5[5] do spec original já lista essa
  alternativa). Trocar "componente conexo" (degenerou em 1 blob de 678 nodes) e "cluster
  escolhido à mão" pela regra mecânica: agrupar `business-candidate` pela chave de pacote de
  `classify.json`; cada grupo é uma unidade de trabalho; os arquivos de cada partição vêm de
  `node_files` (move #1a). É edição do passo 5 do `SKILL.md` — **sem novo script** (um
  `partition_work.py` dedicado fica deferido, §6).

### Move #2 — atravessar o último passo UMA vez

Produzir **um** artefato de handoff de jusante a partir dos dados **já produzidos** (os 43
claims da demo + `endpoints.json`), na **língua do time** (decidido 2026-07-08), consumível
por `tech-breakdown`/`spec-refine`:

- **User Stories candidatas** (Dimensão A) de ≥1 partição (preferir a mecânica do move #1b;
  fallback: partição "Streaming Services" da demo). Em cada US, só a **capability** é ancorada
  (regra + `arquivo:linha` + tier); **papel e benefício são inferência flagada** — não estão
  no bytecode (§11.1, fato ≠ intenção).
- **Critério de Aceite = Cenário Gherkin** por US (`@legacy-observed @tier-<t>`,
  `Given/When/Then`, `arquivo:linha`) — a linha Testes de §11 e a dor #1 do TL ("QAs não
  sabem o que testar"). CA e Cenário são a mesma coisa: o CA é o cenário testável da US.
- **Esqueleto DTO** (Flutter/Dart) de 3-5 endpoints da Dimensão B, padrão DTO+Entity+mapper
  (§11 Implementação).

Tudo sob banner `legacy-observed ≠ target-approved`, ratificação do PO obrigatória. Converte
as etapas Spec, meia Implementação **e Testes** de **gesticuladas** pra **demonstradas** (3
das 5 linhas de §11), sem medição nova. Não é TDD — é execução + curadoria.

### Move #3 — emendar o AC da §9 (fix na origem)

Adicionar ao critério de aceite da demo (§9 do spec original) uma linha que **exige** o
artefato de handoff:

> *Produz ao menos um artefato de jusante no formato de handoff — ≥1 User Story candidata
> (Dimensão A) com Critério de Aceite como Cenário Gherkin (`legacy-observed`) + esqueleto
> DTO de ≥3 endpoints da Dimensão B, consumível por `tech-breakdown`/`spec-refine`,
> demonstrando as etapas Spec/Implementação/Testes de §11. Sem esta linha o define-done
> aponta só pra confiança.*

O spec original fica pt-BR (fora do escopo da migração, §2 dela) — a linha nova entra em
pt-BR, coerente com o doc.

## 5. Decisão de design ABERTA — formato/contrato do artefato de handoff

A §3 do spec original marcou o "template de consolidação e contrato de handoff pra
`tech-breakdown`/`spec-refine`" como **provisional, fixado no primeiro uso real**. Portanto
**não sobre-projetar agora** (Epicurus). Proposta **default** (a confirmar no kickoff da
execução):

- Arquivo novo `examples/newpipe-handoff.md` (separado da demo: demo = prova de viabilidade;
  handoff = prova de aceleração). EN (plugin `mobile` já migrado na execução).
- Banner `legacy-observed ≠ target-approved` no topo + nota de que **papel e benefício de US
  são inferência**, não código.
- **User Story candidata** por regra de negócio da partição: "As a `<role — inferred>`, I
  want `<capability — anchored>`, so that `<benefit — inferred>`", com `[tier]` + evidência
  `arquivo:linha` na capability; papel/benefício marcados como inferência.
- **Critério de Aceite = cenário Gherkin** por US: `@legacy-observed @tier-<t>`,
  `Given/When/Then`, `arquivo:linha`, `# PO must ratify`.
- **Esqueleto DTO**: por endpoint, stub Dart `Dto`/`Entity`/`mapper` anotado com endpoint de
  origem + `arquivo:linha` + tier + o mesmo banner.

**Decidido (2026-07-08):** o handoff sai na **língua do time — US + CA/Cenário + DTO** (era a
dor #1 do TL; responde a frente F2). **Aberto pra confirmar no kickoff da execução:** conjunto
exato de campos e arquivo próprio vs. seção na demo.

## 6. Escopo

**Entra:** os 3 moves acima (`extract_graph.py` + selftest; passo 5 do `SKILL.md`;
`examples/newpipe-handoff.md`; emenda §9 do spec original).

**Fica de fora / deferido (Epicurus):**
- Script de partição dedicado (`partition_work.py`) — o passo 5 mecânico via `node_files` +
  `classify.json` basta pro v0.x.
- Formato de handoff "perfeito" — provisional até o primeiro uso real (§5).
- Re-run em APK novo / app rico em regra de negócio (**frente F1**): **dobrado nesta rodada**
  (decisão do operador, ver §3) — WordPress-Android virou o fixture de aceleração/handoff. Fica
  deferido o restante de F1: re-run no APK do **cliente real** e medição de fidelidade em APK novo.
- Redesign amplo do formato de saída (**frente F2**) — informado por §5, mas não é este doc.
- Análise dinâmica, benchmark com `mapping.txt` — v2 (§12 do spec original).

## 7. Constraints de execução (pós-migração) — LER ANTES DE EXECUTAR

- **Só executar após a migração pro inglês estar mesclada na `main`.** Motivo: `SKILL.md` e a
  demo estão **no escopo da migração** (plugin `mobile`) — editá-los antes garante retrabalho
  ou conflito de merge.
- **Não executar enquanto a sessão de migração estiver ativa no mesmo working tree** (risco
  de commit varrer trabalho não-commitado alheio; risco de checkout race). Rodar em
  branch/worktree limpa a partir da `main` já migrada.
- **Idioma por arquivo** (a migração inverte o default pra EN):
  - `SKILL.md`, `examples/*.md` (plugin migrado) → **EN**.
  - Corpo de script (`extract_graph.py` docstrings/comentários) → **pt-BR** (a migração só
    toca a linha `# desc:`); casar o idioma prevalente do arquivo no momento.
  - `docs/superpowers/specs` e `plans` (este doc, o plano, o spec original) → **pt-BR**
    (fora do escopo da migração).
- **Zero número novo de ROI/produtividade/tempo-economizado** — segue §10/§13 do spec original.

## 8. Aceite do re-apontamento

- `extract_graph.py` emite `node_files` (join node→arquivo); os 4 selftests existentes
  continuam verdes (extends/implements, unclassifiable excluído, sintética filtrada) + nova
  asserção de `node_files`.
- ≥1 partição derivada **mecanicamente** por prefixo de pacote (não escolhida à mão).
- `examples/newpipe-handoff.md` existe, é consumível por `tech-breakdown`/`spec-refine`, com
  ≥1 US candidata (capability ancorada em `arquivo:linha`, papel/benefício flagados) + CA como
  cenário Gherkin (`legacy-observed`) + esqueleto DTO de ≥3 endpoints.
- §9 do spec original emendada com a linha de handoff (fix na origem).
- Nenhum segredo/endpoint literal da Telecorp em lugar nenhum (§8 do spec original, inalterado).

## 9. Riscos

- **Colisão com a migração** se executado cedo — mitigado por §7.
- **Formato de handoff muda no primeiro uso real** — aceito; §5 é provisional por design.
- **`legacy-observed ≠ target-approved` amplificado** — no caos que o TL descreve (mock e
  história vaga), o legado é justo o que se abandona e pode carregar o bug. O guardrail de
  §11.1 do spec original fica **mais** crítico, não menos: o handoff é oráculo de partida pra
  reagir + ratificação do PO, nunca critério de aceite direto.
- **Run em disco pode ter sido limpo** — regenerável a partir dos comandos documentados
  (spec original §15 + plano Task 7); custo baixo.
