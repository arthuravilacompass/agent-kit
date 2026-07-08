---
name: compound
description: Invoque no fim de um track de trabalho relevante — gera o handoff estruturado da sessão (estado, decisões, próximos passos) que sobrevive ao /clear e alimenta a retomada via plan-autoload.
disable-model-invocation: true
---

# compound — Write-back Estrutural de Fim de Track

Gate final de qualquer track não-trivial. Garante que o que a sessão aprendeu não evapora: memória tipada, handoff se necessário, e candidatura a graduação. Não cria store paralelo — grava nos mecanismos que já existem (memória tipada + `docs/superpowers/handoffs/` + `docs/graduation-log.md`).

## Usage

```
compound            # varredura completa
compound --quick    # sessão curta: só a pergunta 1, sem varredura
```

## Steps

1. **Captura de aprendizado** — invoque a skill `core:learn` (varredura da conversa por correções, preferências, decisões; aprovação inline antes de gravar). Se nada for encontrado, declare explicitamente: *"Nada a capturar nesta sessão"* — a declaração é o modo rápido, sem cerimônia.

2. **Handoff (condicional)** — se a sessão está pesada (aviso do context-monitor ≥800KB) OU o trabalho continua em outra sessão: escreva `docs/superpowers/handoffs/<AAAA-MM-DD>-<tarefa>.md` com: tarefa, decisões tomadas, próximos passos, arquivos tocados. O `plan-autoload` resurfaça na próxima sessão. Se a track terminou de verdade (PR criada), pule.

3. **Candidato a graduação (condicional)** — se a sessão refinou uma rule/skill/hook do toolkit: cheque os 3 critérios do `docs/graduation-log.md` (recorre ≥2× · estabilizou em uso real · não é específico de um projeto só). Se os 3 valem, **proponha** a linha para a tabela append-only — o dono do toolkit decide; nunca adicione sem aprovação.

4. **Smell-log (informativo)** — se `docs/engineering/smell-log.txt` ganhou entradas nesta sessão, mencione no resumo: código(s) que dispararam e onde. Recorrência de um code é sinal para refinar a rule correspondente.

5. **Resumo de 4 linhas** — memórias gravadas/skipped · handoff escrito (ou n/a) · graduação proposta (ou n/a) · smells bloqueados (ou n/a).

## Important

- **Modo `--quick`**: apenas step 1, e a skill `core:learn` limitada às últimas ~20 mensagens.
- **Aprovação obrigatória** para qualquer write de memória (herda da skill `core:learn`) e para linha no graduation-log.
- Bugfix que o harness deixou passar: além da memória, adicione um caso em `docs/evals/` (ver README de lá) — bugs fechados são evals nascendo.
- Não duplique: se o aprendizado já está em memória/rule, atualize em vez de criar.
