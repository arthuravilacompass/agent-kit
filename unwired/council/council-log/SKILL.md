---
name: council-log
description: Grava um brief de deliberação do Conselho no corpus episódico (~/.claude/epistemic/<postura>.jsonl, append-only). Use após rodar uma postura numa decisão de alto custo de reversão que vale lembrar. Advisory; nunca bloqueia.
---

# /council-log — registrar deliberação

Persiste UM brief (append-only, sob flock). Não decide nada; é infra de recall.

Monte o objeto JSON do brief e appenda:
```bash
echo '{"posture":"<roster-6>","topic":"<1 linha>","move":"<output verbatim da postura>","claim_status":"APOSTA|FATO","mode":"light|escalated","surface_class":"<repository|...|other>","keywords":["..."],"evidence":["file:linha"]}' \
  | python3 <path-do-skill>/council-log/log.py
```

Regras:
- `claim_status=FATO` **exige** `evidence` (≥1 `file:linha`/`doc:seção`) — senão o script recusa (assimetria deliberada: um FATO errado no recall é mais danoso que um APOSTA errado).
- `move` > 800 chars vai pra `blobs/<id>.txt`; o JSONL guarda o truncado + `move_blob`.
- Correção = NOVO brief com `supersedes:"<id-antigo>"` (UM nível; nunca edite/apague linha).
- **Outcome (desfecho):** para registrar como um caso terminou, logue um NOVO brief com `outcome:"<o que aconteceu>"` + `outcome_of:"<id-do-brief-original>"` (append-only; nunca edita a linha original). `recall` exibe o outcome no caso original mas **não ranqueia por ele** (corpus segue "casos que aconteceram"; você julga).
