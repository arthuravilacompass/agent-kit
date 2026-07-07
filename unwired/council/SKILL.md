---
name: council
description: Invoque para ver o Conselho de Posturas — os 6 modos de raciocínio (Schrödinger, Bohr, Epicurus, Sagan, Maxwell, Zeno), o que cada um interroga, e quando vesti-lo. É o índice/presença; o trabalho vive em cada postura.
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

Invocação: as 4 skills se vestem por nome no thread (`/bohr`, `/sagan`, `/epicurus`, `/schrodinger`); Maxwell e Zeno são despachados isolados. **Zeno precisa das premissas vivas coladas no dispatch** (ver `agents/zeno.md`). O nome é identidade; o gatilho situacional vive na `description` de cada arquivo.

**Camada automática (opcional, arquitetura de referência — não incluída neste kit):** um porteiro `type:"agent"` no Stop (registrável em settings do projeto) pode interceptar conclusões consequentes DO ASSISTENTE (claim de estado, diagnóstico, "pronto/validado", número-que-vira-premissa) e bloquear o encerramento até o claim ser verificado pelo `epistemic-council` (modo cego, mandato executável) e a resposta revisada — marcador `∴ council-verified`. Nessa arquitetura o usuário nunca vê nudge; vê resposta já verificada. Hooks de sugestão proativa foram testados e removidos num projeto de origem (mediram ~0 conversão em campo) — sinal para não reintroduzir sem medição.

**Dispositivos V1 (overlays in-thread):** as 4 skills inline (`/bohr` `/schrodinger` `/epicurus` `/sagan`) abrem com um **Restate Gate** (passo 0, output estruturado) e fecham com um **dispositivo de oposição** no callout + uma **cláusula de escalonamento** para o subagent isolado `epistemic-council` (modo cego). Os dispositivos elevam o custo de performar concordância, mas rodam no mesmo thread — a separação real só existe no escalonamento. Memória/recall: `/council-log`, `/council-recall`.

**Anti-contaminação de output (ritual):** antes de entregar artefato *context-seeding* (handoff / spec / "prompt da próxima sessão" / descrição de PR), passá-lo por **review cego** (subagent isolado, sem o thread) + checklist mecânico (sem valores-esperados pré-escritos; framing neutro; aponta-pra-fonte). Não mecanizado — ver `POSITIONING.md`.

Posicionamento (o porquê — o que o Conselho é, o que NÃO promete, e onde ainda não provou que funciona): `POSITIONING.md`.

**Nota de proveniência (arquivo neste kit):** as referências originais a specs/planos datados de um projeto de origem (validação faseada, auditoria do mecanismo, plano de execução V2) foram removidas por não serem portáveis — o raciocínio e a arquitetura acima ficam de pé sem elas; se for promover este material a `plugins/`, refaça esses registros no novo projeto.
