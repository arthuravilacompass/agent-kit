---
name: council-recall
description: Invoke before a high-cost-to-reverse decision, together with the Council posture that will wear it — queries episodic memory (~/.claude/epistemic/) and lists up to 3 past cases that rhyme by FORM (same posture + surface_class + overlap). Silent if nothing rhymes. Advisory.
---

# /council:council-recall — retrieve analogues

Lists up to 3 cases that rhyme by decision-shape. Hard filter = posture; strong signal = `surface_class`; medium = keywords/topic overlap; recency only breaks ties. **Silence** if nothing clears the threshold (doesn't invent a case).

```bash
command -v python3 >/dev/null 2>&1 || exit 0   # advisory guard: no python3 → silence, exit 0
python3 "${CLAUDE_PLUGIN_ROOT}/skills/council-recall/recall.py" \
  --posture <bohr|schrodinger|epicurus|sagan|maxwell|zeno> \
  --surface <repository|datasource|dto|mapper|coordinator|router|entity|state|store|controller|other> \
  --keywords "kw1,kw2" --topic "1 line for the current decision"
```

- Adjustable threshold: `COUNCIL_RECALL_MIN` (default 3 = a single `surface_class` match already clears it).
- `outcome` is **displayed** when a brief with `outcome_of` points at the case, but **doesn't enter the score** (D6: store+display, never rank — the corpus stays "cases that happened"; the interpretation is yours).
- There's no automatic "light vs. escalate" judgment — you decide.
