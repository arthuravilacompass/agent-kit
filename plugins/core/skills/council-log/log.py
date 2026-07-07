#!/usr/bin/env python3
"""council-log — valida e appenda UM brief ao corpus episódico (append-only, flock).
Lê um objeto JSON (o brief) no stdin. Recusa (exit!=0, corpus inalterado) brief
inválido. Advisory: nunca toca código nem bloqueia commit."""
import json, os, sys, time, fcntl, re

ROSTER = {"bohr", "schrodinger", "epicurus", "sagan", "maxwell", "zeno"}
SURFACE = {"repository","datasource","dto","mapper","coordinator","router",
           "entity","state","store","controller","other"}
CLAIM = {"APOSTA", "FATO"}
MODE = {"light", "escalated"}
MOVE_MAX = 800

def fail(msg):
    sys.stderr.write(f"council-log: REJEITADO — {msg}\n")
    sys.exit(1)

def main():
    raw = sys.stdin.read()
    try:
        b = json.loads(raw)
    except Exception as e:
        fail(f"JSON inválido: {e}")
    if not isinstance(b, dict):
        fail("brief não é objeto JSON")
    posture = b.get("posture")
    if posture not in ROSTER:
        fail(f"posture ausente/ inválida (roster-6): {posture!r}")
    if b.get("claim_status") not in CLAIM:
        fail("claim_status obrigatório ∈ {APOSTA, FATO}")
    if b.get("mode") not in MODE:
        fail("mode obrigatório ∈ {light, escalated}")
    if b.get("surface_class") not in SURFACE:
        fail(f"surface_class obrigatório ∈ {sorted(SURFACE)}")
    for f in ("topic", "move"):
        if not isinstance(b.get(f), str) or not b[f].strip():
            fail(f"campo obrigatório ausente/vazio: {f}")
    if b["claim_status"] == "FATO":
        ev = b.get("evidence")
        if not isinstance(ev, list) or len(ev) < 1:
            fail("claim_status=FATO exige >=1 entrada em evidence")
    for opt in ("outcome", "outcome_of"):                 # D6: desfecho opcional (armazena, não ranqueia)
        if opt in b and (not isinstance(b[opt], str) or not b[opt].strip()):
            fail(f"campo opcional inválido (precisa str não-vazia): {opt}")

    ts = int(b.get("ts") or time.time())
    b["ts"] = ts
    slug = re.sub(r"[^a-z0-9]+", "-", b["topic"].lower()).strip("-")[:40] or "x"
    b["id"] = b.get("id") or f"{posture}-{slug}-{ts}"

    base = os.path.join(os.path.expanduser("~"), ".claude", "epistemic")
    blobs = os.path.join(base, "blobs")
    try:
        os.makedirs(blobs, exist_ok=True)
    except Exception as e:
        fail(f"não criou diretório do corpus: {e}")

    # overflow: move verbatim > MOVE_MAX vai pro blob (escrito SOB o MESMO flock
    # da linha — fix advisor: blob fora do lock pode ser sobrescrito por id colidente)
    overflow = len(b["move"]) > MOVE_MAX
    full_move = b["move"]
    if overflow:
        b["move_blob"] = f"blobs/{b['id']}.txt"
        b["move"] = b["move"][:MOVE_MAX]

    target = os.path.join(base, f"{posture}.jsonl")
    line = json.dumps(b, ensure_ascii=False) + "\n"
    try:
        with open(target, "a", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)   # serializa appends E blob concorrentes
            try:
                if overflow:                          # blob sob o mesmo lock que a linha
                    with open(os.path.join(blobs, f"{b['id']}.txt"), "w", encoding="utf-8") as bf:
                        bf.write(full_move)
                f.write(line)
                f.flush()
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except Exception as e:
        fail(f"append falhou: {e}")
    print(b["id"])
    sys.exit(0)

if __name__ == "__main__":
    main()
