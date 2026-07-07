#!/usr/bin/env python3
"""council-recall — recupera casos que RIMAM por FORMA-DE-DECISÃO.
Filtro duro = postura. Sinal forte = surface_class igual. Médio = overlap
keywords/topic. Recência só desempata. top-3 acima do limiar; silêncio se nada
passa. python3-guard idiom padrão de scripts advisory. SEMPRE exit 0 (advisory)."""
import json, os, sys, argparse, re

SURFACE_STRONG = 3      # surface_class igual
KW_EACH = 1             # cada keyword/token de topic em overlap
KW_CAP = 3              # teto do sinal médio

def tokens(s):
    # \w é unicode-aware no py3 → preserva acento pt-BR (alteração, serviço, inscrição)
    return set(t for t in re.split(r"[^\w]+", (s or "").lower()) if len(t) > 2)

def load(posture, base):
    path = os.path.join(base, f"{posture}.jsonl")
    rows = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue   # JSON malformado: ignora, nunca quebra
    except FileNotFoundError:
        return []
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--posture", required=True)
    ap.add_argument("--surface", default="other")
    ap.add_argument("--keywords", default="")
    ap.add_argument("--topic", default="")
    args = ap.parse_args()

    # NB: o guard de "sem python3" é BASH, no SKILL.md ANTES de invocar este script.
    # Aqui dentro já estamos em python3 — guard interno seria dead code.
    base = os.path.join(os.path.expanduser("~"), ".claude", "epistemic")
    rows = load(args.posture, base)
    if not rows:
        sys.exit(0)   # silêncio: corpus vazio

    superseded = {r.get("supersedes") for r in rows if r.get("supersedes")}
    rows = [r for r in rows if r.get("id") not in superseded]   # dedup 1 nível
    outcomes = {r["outcome_of"]: r.get("outcome", "") for r in rows if r.get("outcome_of")}  # D6
    rows = [r for r in rows if not r.get("outcome_of")]   # briefs de outcome = anotação, não caso (D6)

    q_surface = args.surface
    q_tokens = set(k.strip().lower() for k in args.keywords.split(",") if k.strip()) | tokens(args.topic)

    try:                                  # advisory: env var inválida não pode crashar (B10)
        threshold = int(os.environ.get("COUNCIL_RECALL_MIN", "3"))
    except (ValueError, TypeError):
        threshold = 3
    scored = []
    for r in rows:
        score = 0
        if r.get("surface_class") == q_surface:
            score += SURFACE_STRONG
        r_tokens = set(t.lower() for t in (r.get("keywords") or [])) | tokens(r.get("topic"))
        overlap = len(q_tokens & r_tokens)
        score += min(overlap * KW_EACH, KW_CAP)
        if score >= threshold:
            scored.append((score, int(r.get("ts") or 0), r))   # `or 0`: ts=null não crasha (B10)

    if not scored:
        sys.exit(0)   # silêncio: nada rima acima do limiar (não inventa caso)

    # relevância domina; recência (ts) só desempata
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    for score, ts, r in scored[:3]:
        ev = ";".join(r.get("evidence") or []) or "—"
        print(f"[{r.get('id')}] score={score} surface={r.get('surface_class')} "
              f"claim={r.get('claim_status')} mode={r.get('mode')}")
        print(f"    topic: {r.get('topic')}")
        print(f"    move:  {r.get('move')}")
        print(f"    evidence: {ev}")
        if r.get("id") in outcomes and outcomes[r["id"]]:   # D6: exibe desfecho, sem ranquear
            print(f"    outcome: {outcomes[r['id']]}")
    sys.exit(0)

if __name__ == "__main__":
    main()
