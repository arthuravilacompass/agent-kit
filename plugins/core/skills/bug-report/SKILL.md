---
name: bug-report
description: Investiga um bug e produz relatório com citações verificadas — gate determinístico (validate_citations --gate) + verifier semântico em contexto fresco. Use ao investigar/reportar bug onde afirmar comportamento de código sem ler a fonte é o risco.
disable-model-invocation: true
---

# /bug-report -- Relatório de bug com citação verificada

Investiga um bug e **só finaliza** o relatório com findings cuja citação `file:line` (1) sobrepõe código realmente lido nesta sessão **e** (2) é semanticamente sustentada pelo código. É o caminho com **gate duro** — porque um bug-report com citação fabricada (ex.: uma rota que não existe no código, inventada pelo modelo) é um failure conhecido em relatórios gerados por LLM sem esse gate.

**Dependência:** este skill assume a existência do mecanismo de citação verificada — um read-ledger que registra cada `Read`/`Grep` da sessão + um script `validate_citations.py --gate` que recusa finding `tool-output` citando código não lido. Se o projeto consumidor já tem esse mecanismo (ex.: portado via `plugins/core`), aponte os comandos abaixo para ele; caso contrário, este skill precisa do mecanismo antes de funcionar.

## Usage

```
/bug-report <descrição do bug / ticket>
```

## Steps

1. **Escopo** — sintoma, passos de repro, área suspeita. Aplique as perguntas de bugfix-principles do projeto (contrato violado? ausente≠vazio? ciclo de vida do estado? invariante implícito?), se o projeto tiver essa rule.

2. **Investigar** — Read/Grep o código relevante. **Cada Read popula o read-ledger da sessão**. Não conclua sobre comportamento sem ler a fonte.

3. **Findings estruturados** — montar JSON:
   ```json
   [{ "claim": "...", "epistemicSource": "tool-output",
      "evidence": { "file": "...", "lineStart": N, "lineEnd": M, "quote": "..." } }]
   ```
   `epistemicSource`: `tool-output` (afirmação sobre código lido) · `inference` · `absence` · `external`. Só `tool-output` é gateado.

4. **Gate determinístico (duro)** —
   ```
   python3 <path-do-mecanismo>/validate_citations.py --session <session-id-atual> --gate --findings <arquivo>
   ```
   Passe `--session` explícito (sessões concorrentes). **Exit 2** = há finding `tool-output` citando código não-lido (fabricação de localização) → **NÃO finalizar**; voltar ao passo 2, ler de fato ou corrigir o finding. Só prossiga com exit 0.

5. **Verifier semântico (contexto fresco)** — pega o que o gate determinístico não pega: claim que cita código **real** mas o **interpreta errado**. Dispatch um subagente em contexto limpo, com este prompt, passando os findings que sobreviveram ao passo 4:

   > Você é um verificador cético de citações. Para CADA claim abaixo, em contexto fresco: (1) Read o range EXATO `file:lineStart-lineEnd`; leia algumas linhas ao redor se precisar. (2) Julgue se o código realmente lido **sustenta** o claim — `supported=true` só se o código implica o que o claim afirma; `false` se contradiz, não menciona, sustenta só parcialmente (overreach), ou o range está vazio. (3) Default cético: na dúvida, `false`. NÃO confie no `quote` fornecido — re-leia o arquivo. Escopo: só veredito de sustentação; não revise estilo nem sugira fix. Saída por claim: `{ "claim", "file", "supported": bool, "confidence": "high|medium|low", "reason": "<citando o que o código realmente faz>" }`.

   Findings com `supported=false` → seção "⚠️ Citação não sustenta o claim", **não** afirmar como causa-raiz.

6. **Relatório** — só findings `verified` (passo 4) **e** `supported` (passo 5):
   ```
   ## Bug: <título>
   **Sintoma**: <...>  ·  **Repro**: <...>
   **Causa-raiz**: <claim> — `<file>:<lineStart>-<lineEnd>`
   **Evidência**: <quote do código real>
   **Fix proposto**: <na origem, não na consequência>
   ### ⚠️ Citação não sustenta (<count>)   — findings refutados por um dos gates
   ```

## Important

- **Gate duro aqui** (≠ um review menos estrito que só anota) — o custo de um bug-report falso justifica bloquear.
- **Fix na origem, nunca na consequência**; estado que sobrevive tem ciclo de vida nomeado.
- Não postar em sistema externo (tracker/board) sem pedido explícito.
