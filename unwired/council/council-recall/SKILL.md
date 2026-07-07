---
name: council-recall
description: Consulta a memória episódica do Conselho e lista casos passados que rimam por FORMA com a decisão atual (mesma postura + surface_class + overlap). Use antes de uma decisão de alto custo p/ trazer análogos. Silencioso se nada rima. Advisory.
---

# /council-recall — recuperar análogos

Lista até 3 casos que rimam por forma-de-decisão. Filtro duro = postura; sinal forte = `surface_class`; médio = overlap de keywords/topic; recência só desempata. **Silêncio** se nada passa o limiar (não inventa caso).

```bash
command -v python3 >/dev/null 2>&1 || exit 0   # guard advisory: sem python3 → silêncio exit 0
python3 <path-do-skill>/council-recall/recall.py \
  --posture <bohr|schrodinger|epicurus|sagan|maxwell|zeno> \
  --surface <repository|datasource|dto|mapper|coordinator|router|entity|state|store|controller|other> \
  --keywords "kw1,kw2" --topic "1 linha da decisão atual"
```

- Limiar ajustável: `COUNCIL_RECALL_MIN` (default 3 = um match de `surface_class` já passa).
- `outcome` é **exibido** quando há um brief `outcome_of` apontando pro caso, mas **não entra no score** (D6: armazenar+exibir, nunca ranquear — corpus segue "casos que aconteceram"; a interpretação é sua).
- Não há julgamento automático de "leve vs escalar" — você decide.
