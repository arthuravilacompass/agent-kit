# Governança do kit

Doc canônico do ciclo de vida dos artefatos do agent-kit. Toda regra normativa de governança vive aqui e só aqui — `README.md`, `unwired/README.md` e `using-agent-kit` apontam pra cá. Histórico e datas vivem no `CHANGELOG.md`; medições vivem no gate (`scripts/check-governance.sh`).

## O modelo de 3 estados (D10)

Todo artefato que já existiu neste kit está num destes três estados, nunca em limbo:

- **wired** — vive em `plugins/core/` ou `plugins/mobile/`. Foi admitido porque tem uso real comprovado (não só "parecia bom"). Custa contexto toda sessão que carrega o plugin.
- **unwired** — vive em `unwired/`. Genericizável, scrub mecânico aplicado, mas sem prova de uso no novo projeto. Custo de contexto **zero** — só é lido se alguém abrir o arquivo.
- **deletado** — não existe no repo. Foi avaliado e descartado (vestigial, específico demais do projeto de origem pra genericizar, ou substituído por outra coisa melhor).

Nunca "testado mas não ligado" — essa terceira categoria fantasma é o que este modelo existe para eliminar.

## Regra de promoção

**Um item sobe de `unwired/` para `plugins/` (wired) quando tiver uso real comprovado no projeto novo — o mesmo critério de admissão que qualquer skill/agent/hook novo teria.** Não é "parece útil" nem "era usado no projeto de origem" — é: você invocou isso pelo menos uma vez no projeto novo, funcionou, e quer que sobreviva ao próximo `/clear`.

Ao promover:

1. **Reescreva a `description`** com o gatilho específico do novo contexto — a description arquivada carrega vocabulário/gatilho do projeto de origem (às vezes já genérico, às vezes não).
2. **Preencha os placeholders de proveniência** (`<TICKET>`, `<DesignTokens>`, `<BOARD_NAME>`, nomes de componente entre `<>`) com os nomes reais do projeto novo. O scrub que colocou o item em `unwired/` foi mecânico, não uma reescrita — o trabalho de reancorar no domínio novo é seu, não deste kit.
3. **Mova o arquivo** para `plugins/<core|mobile|novo-plugin>/` na estrutura padrão (skills em `skills/<nome>/SKILL.md`, agents em `agents/<nome>.md`, etc.) e rode `claude plugin validate .`.
4. **Delete a cópia em `unwired/`** — um item promovido não fica duplicado nos dois estados.

### Exceção: promoção provisória por deadline de rotação

Quando a desalocação de um workspace de origem ameaça perder a janela de validação, um item PODE ser promovido sem uso real comprovado neste kit, desde que: (1) a exceção seja registrada no `CHANGELOG.md` com o motivo; (2) a promoção passe por review adversarial imediata do diff completo — a primeira leva promovida sob esta exceção teve 15 defeitos encontrados num move "puramente mecânico" (registro no `CHANGELOG.md`); (3) o item ganhe prazo de validação — sem uso real em 1 ciclo de projeto novo, volta a `unwired/`. Promoção provisória não codificada é violação da governança, não exceção dela.

## Meta-princípios

- **Code com ID só nasce com validador.** Toda regra, hook ou skill identificada por um ID nasce junto com o mecanismo que verifica sua aplicação (gate, hook, script) — nunca como texto solto sem enforcement. Este doc aplica a regra a si mesmo: todo ID D*/R* citado no repo precisa resolver no ledger abaixo, verificado por `scripts/check-governance.sh` no gate.
- **Regra textual que falha repetido vira mecanismo.** Sob orçamento de atenção finito, instrução marginal é omitida (não desobedecida) — empilhar mais texto reduz o compliance agregado, não só deixa de melhorar. A regra de maior taxa de falha vira hook, schema de output obrigatório ou gate determinístico, não mais texto.
- **Advisory-nudge não entra em `plugins/` sem medição.** Mecanismo só-lembrete precisa provar conversão real antes de ser wired; caso concreto: `learning-pulse` (tabela por-item em `unwired/README.md`), que mediu ~0 conversão no projeto de origem e só volta com medição nova que sustente o custo.

## Teto do tier sempre-ativo

O tier sempre-ativo do `core` — o corpo de `using-agent-kit` injetado por sessão via `plugins/core/hooks/session-start.sh` — tem teto de **16.384 bytes**, medido sobre a saída real do hook (JSON completo; proxy conservador do payload injetado, envelope e escaping inclusos).

- **Enforcement**: `scripts/check-governance.sh` no gate — vermelho se a medição passar do teto.
- **Efeito pretendido**: pressão de seleção. Regra nova no sempre-ativo compete por espaço; quando o teto aperta, algo sai (vira skill on-demand, mecanismo, ou é deletado) — o teto não sobe por conveniência. Subir o teto é decisão de governança: exige entrada nova no ledger.

## Ledger de decisões

Registro das decisões identificadas por ID (série `D*` = decisão de design, `R*` = requisito de aceite) citadas neste repo. A numeração é esparsa por origem: os IDs nasceram na numeração contínua do material de auditoria/spec do projeto de origem (fora deste repo — o gate de proveniência recusa importá-lo); este ledger cobre os IDs citados aqui, reconstituídos de evidência in-repo. **Decisão nova pega o próximo ID livre da série `D` e nasce com entrada neste ledger** — citar ID sem entrada aqui deixa o gate vermelho. Formato de entrada (contrato lido pelo gate): item de lista iniciando com `- **<ID>** — <decisão>`.

- **D6** — Corpus episódico do Conselho: `outcome` é armazenado e exibido, nunca entra no score/ranqueamento — o corpus registra "casos que aconteceram"; a interpretação é do leitor. Citado em `plugins/core/skills/council-recall/SKILL.md`.
- **D10** — Modelo de 3 estados (wired/unwired/deletado) para todo artefato do kit; elimina a categoria fantasma "testado mas não ligado". Texto normativo: seção "O modelo de 3 estados" deste doc.
- **D13** — Métricas de aceite da extração do kit: tag `gate-day3-pass` e métrica-2-semanas (primeiro uso real em projeto fora do projeto de origem dentro do prazo, senão o resultado foi "inventário com README"). Registro e datas: `CHANGELOG.md` §Métricas D13.
- **R2** — Requisito de aceite da extração: medir o custo real de payload do kit (tokens/turno + injeção de sessão) e rodar A/B comportamental com e sem o kit. Resultados e lacunas conhecidas da medição: `CHANGELOG.md` §Aceite final (c).
