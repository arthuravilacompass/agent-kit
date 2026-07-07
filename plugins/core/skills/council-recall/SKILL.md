---
name: council-recall
description: Invoque antes de uma decisão de alto custo de reversão, junto com a postura do Conselho que vai vesti-la — consulta a memória episódica (~/.claude/epistemic/) e lista até 3 casos passados que rimam por FORMA (mesma postura + surface_class + overlap). Silencioso se nada rima. Advisory.
---

# /core:council-recall — recuperar análogos

Lista até 3 casos que rimam por forma-de-decisão. Filtro duro = postura; sinal forte = `surface_class`; médio = overlap de keywords/topic; recência só desempata. **Silêncio** se nada passa o limiar (não inventa caso).

```bash
command -v python3 >/dev/null 2>&1 || exit 0   # guard advisory: sem python3 → silêncio exit 0
python3 "${CLAUDE_PLUGIN_ROOT}/skills/council-recall/recall.py" \
  --posture <bohr|schrodinger|epicurus|sagan|maxwell|zeno> \
  --surface <repository|datasource|dto|mapper|coordinator|router|entity|state|store|controller|other> \
  --keywords "kw1,kw2" --topic "1 linha da decisão atual"
```

- Limiar ajustável: `COUNCIL_RECALL_MIN` (default 3 = um match de `surface_class` já passa).
- `outcome` é **exibido** quando há um brief `outcome_of` apontando pro caso, mas **não entra no score** (D6: armazenar+exibir, nunca ranquear — corpus segue "casos que aconteceram"; a interpretação é sua).
- Não há julgamento automático de "leve vs escalar" — você decide.
