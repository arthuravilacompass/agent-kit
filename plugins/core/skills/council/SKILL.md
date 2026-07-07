---
name: council
description: Invoque pra consultar o índice do Conselho de Posturas do kit — as 6 posturas wired (4 skills in-thread, 2 subagents isolados), o que cada uma interroga, quando vestir, o formato de saída (callout) e quando escalar pro modo cego (agent epistemic-council). O trabalho vive em cada postura; aqui é o mapa.
---

# Conselho de Posturas Epistêmicas

Modos de raciocínio que você veste de propósito — não tarefas. A saída de cada um é um movimento sobre o raciocínio, não um artefato, no **callout do Conselho** (ver §Formato de saída abaixo).

## Formato de saída — o callout do Conselho

Toda intervenção do Conselho — sugestão proativa ("o council interfere") OU output de uma postura vestida — sai num **callout**: header em negrito + um **code-fence**. O code-fence é a única primitiva markdown que vira caixa com borda no terminal/UI; molduras estilo `★ Insight` (ASCII `─`) renderizam ragged e estão **aposentadas** aqui.

**O council interfere:**
```
∴ <Postura> percebe: <observação em uma linha>.

  <evidência/contexto específico — indentado, linhas curtas>

  <label>: <a pergunta que a postura força>
```

- Prefixo `∴` + nome da postura por extenso (sem emoji dentro da fence — emoji fica no texto ao redor, se quiser).
- Postura com Restate Gate (Bohr/Schrödinger/Epicurus/Sagan): o Restate Gate abre a fence (`Original:` / `Reformulação:` / `Divergência:`); o mapa/lista da deliberação segue **fora** da fence (senão vira parede monoespaçada).

| Postura | Pergunta | Quando vestir | Vaso |
|---|---|---|---|
| 🐱 Schrödinger | Quais explicações ainda coexistem? | diagnóstico ambíguo | skill |
| ⚛️ Bohr | A dicotomia é falsa? | decisão travada em "A ou B" | skill |
| 🌿 Epicurus | O que aqui é excesso? | antes de dar por pronto (corta elementos) | skill |
| 🔭 Sagan | Isso importa? Em que escala? | antes de investir esforço (altitude) | skill |
| 🧲 Maxwell | Como isso propaga? | antes de mexer em algo acoplado | subagent |
| 🐢 Zeno | Onde isso quebra? | validando uma solução | subagent |

Invocação: as 4 skills se vestem por nome no thread (`/core:bohr`, `/core:sagan`, `/core:epicurus`, `/core:schrodinger`); Maxwell e Zeno são despachados isolados (agents `maxwell` e `zeno` deste plugin). **Zeno precisa das premissas vivas coladas no dispatch** (ver `plugins/core/agents/zeno.md`). O nome é identidade; o gatilho situacional vive na `description` de cada arquivo.

**Camada automática (opcional, arquitetura de referência — não incluída neste kit):** um porteiro `type:"agent"` no Stop (registrável em settings do projeto) pode interceptar conclusões consequentes DO ASSISTENTE (claim de estado, diagnóstico, "pronto/validado", número-que-vira-premissa) e bloquear o encerramento até o claim ser verificado pelo `epistemic-council` (modo cego, mandato executável) e a resposta revisada — marcador `∴ council-verified`. Nessa arquitetura o usuário nunca vê nudge; vê resposta já verificada. Hooks de sugestão proativa só entram com medição de conversão que sustente o custo — ver meta-princípio advisory-nudge em `docs/GOVERNANCE.md`.

**Dispositivos inline (overlays in-thread):** as 4 skills inline (`/core:bohr` `/core:schrodinger` `/core:epicurus` `/core:sagan`) abrem com um **Restate Gate** (passo 0, output estruturado) e fecham com um **dispositivo de oposição** no callout + uma **cláusula de escalonamento** para o subagent isolado `epistemic-council` (modo cego). Os dispositivos elevam o custo de performar concordância, mas rodam no mesmo thread — a separação real só existe no escalonamento. Memória/recall: `/core:council-log`, `/core:council-recall`.

**Anti-contaminação de output (ritual):** antes de entregar artefato *context-seeding* (handoff / spec / "prompt da próxima sessão" / descrição de PR), passá-lo por **review cego** (subagent isolado, sem o thread) + checklist mecânico (sem valores-esperados pré-escritos; framing neutro; aponta-pra-fonte). Não mecanizado — ver `POSITIONING.md`.

Posicionamento (o porquê — o que o Conselho é, o que NÃO promete, e onde ainda não provou que funciona): `POSITIONING.md`.
