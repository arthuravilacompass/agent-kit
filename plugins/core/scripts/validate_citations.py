#!/usr/bin/env python3
# desc: Valida citações de findings contra o read-ledger da sessão (Camada 1).
"""
validate_citations.py — Validador determinístico de citação (Camada 1).

Cruza os findings de um subagente (cada um com evidence.file:lineStart-lineEnd) contra o
read-ledger da sessão (o que foi REALMENTE lido via Read/Grep, gravado pelo hook
read-ledger.sh). Finding tool-output cujo range não sobrepõe nenhuma leitura → UNVERIFIED.
Mecanismo, não instrução: não se pode citar código que não se leu.

Veredictos:
  verified     — claim tool-output cujo range sobrepõe uma leitura no ledger.
  unverified   — claim tool-output sem evidence, ou cujo range não foi lido nesta sessão.
  passthrough  — epistemicSource inference/absence/external: não exige citação (anotado, não barrado).

Uso:
  # anotar (default, exit 0): findings via stdin ou --findings, ledger auto-descoberto
  python3 validate_citations.py --findings findings.json
  cat findings.json | python3 validate_citations.py --session <id> --json

  # hard gate (exit 2 se houver unverified) — pra finalização de bug-report
  python3 validate_citations.py --findings bug_report.json --gate

Entrada (stdin ou --findings): array JSON de findings, OU objeto {"findings": [...]}.
Cada finding: { "claim": "...", "epistemicSource": "tool-output",
                "evidence": {"file": "...", "lineStart": N, "lineEnd": M} }

Ledger: <state-dir>/read-ledger-<session>.jsonl (default: o mais recente).
Default de <state-dir>: $CLAUDE_PLUGIN_DATA/state se a env var estiver setada (mesma
convenção do hook read-ledger.sh); senão $TMPDIR/agent-kit-core/state. Sempre
sobreponível via --state-dir.
"""

import argparse
import glob
import json
import os
import sys

NO_CITATION_SOURCES = {"inference", "absence", "external"}


def default_state_dir():
    base = os.environ.get("CLAUDE_PLUGIN_DATA") or os.path.join(
        os.environ.get("TMPDIR", "/tmp"), "agent-kit-core"
    )
    return os.path.join(base, "state")


# ── Ledger ────────────────────────────────────────────────────────────────────
def discover_ledger(session, ledger_path, state_dir):
    if ledger_path:
        return ledger_path
    if session:
        return os.path.join(state_dir, f"read-ledger-{session}.jsonl")
    candidates = glob.glob(os.path.join(state_dir, "read-ledger-*.jsonl"))
    if not candidates:
        return None
    # Sessões concorrentes geram ledgers paralelos — auto-discovery pode pegar a errada.
    import time as _t
    recent = [c for c in candidates if _t.time() - os.path.getmtime(c) < 600]
    if len(recent) > 1:
        print(f"AVISO: {len(recent)} ledgers modificados <10min (sessões concorrentes?). "
              "Passe --session p/ precisão; usando o mais recente.", file=sys.stderr)
    return max(candidates, key=os.path.getmtime)


def load_ledger(path, project_dir):
    """Retorna (ranges_por_arquivo, arquivos_tocados). Ignora ranges 0-0 para overlap
    de linha (arquivo visto mas range desconhecido), mas registra o arquivo como tocado."""
    ranges = {}
    touched = set()
    if not path or not os.path.isfile(path):
        return ranges, touched
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except Exception:
                continue
            fp = normpath(e.get("file", ""), project_dir)
            if not fp:
                continue
            touched.add(fp)
            s, en = e.get("start"), e.get("end")
            if isinstance(s, int) and isinstance(en, int) and en > 0:
                lo, hi = (s, en) if s <= en else (en, s)
                ranges.setdefault(fp, []).append((lo, hi))
    return ranges, touched


def normpath(p, project_dir):
    if not p:
        return ""
    if not os.path.isabs(p):
        p = os.path.join(project_dir, p)
    return os.path.normpath(p)


def overlaps(a_lo, a_hi, b_lo, b_hi):
    return a_lo <= b_hi and b_lo <= a_hi


# ── Validação ───────────────────────────────────────────────────────────────
def validate_finding(finding, ranges, touched, project_dir):
    src = (finding.get("epistemicSource") or "tool-output").lower()
    if src in NO_CITATION_SOURCES:
        return "passthrough", f"epistemicSource={src} — não exige citação"

    ev = finding.get("evidence") or {}
    file = ev.get("file", "")
    ls = ev.get("lineStart")
    le = ev.get("lineEnd", ls)
    if not file or not isinstance(ls, int):
        return "unverified", "claim tool-output sem evidence.file:lineStart"

    if not isinstance(le, int):
        le = ls
    lo, hi = (ls, le) if ls <= le else (le, ls)
    fp = normpath(file, project_dir)

    for (rlo, rhi) in ranges.get(fp, []):
        if overlaps(lo, hi, rlo, rhi):
            return "verified", f"range {lo}-{hi} sobrepõe leitura {rlo}-{rhi} no ledger"
    if fp in touched:
        return "unverified", f"arquivo lido, mas range {lo}-{hi} fora do que foi lido"
    return "unverified", "arquivo/range nunca lido nesta sessão (possível fabricação)"


def load_findings(path):
    raw = open(path, encoding="utf-8").read() if path else sys.stdin.read()
    data = json.loads(raw)
    if isinstance(data, dict) and "findings" in data:
        return data["findings"]
    if isinstance(data, list):
        return data
    raise ValueError("entrada deve ser array de findings ou {\"findings\": [...]}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Validador determinístico de citação (Camada 1).")
    ap.add_argument("--findings", help="arquivo JSON de findings (default: stdin)")
    ap.add_argument("--session", help="session id (deriva o caminho do ledger)")
    ap.add_argument("--ledger", help="caminho explícito do ledger .jsonl")
    ap.add_argument("--state-dir", default=default_state_dir(),
                    help="diretório onde read-ledger.sh grava os ledgers (default: "
                         "$CLAUDE_PLUGIN_DATA/state ou $TMPDIR/agent-kit-core/state)")
    ap.add_argument("--project-dir", default=os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()),
                    help="raiz do projeto p/ resolver paths relativos")
    ap.add_argument("--gate", action="store_true",
                    help="hard gate: exit 2 se houver finding unverified (p/ bug-report)")
    ap.add_argument("--json", action="store_true", help="emite findings anotados em JSON no stdout")
    args = ap.parse_args()

    project_dir = os.path.normpath(args.project_dir)
    ledger_path = discover_ledger(args.session, args.ledger, args.state_dir)
    ranges, touched = load_ledger(ledger_path, project_dir)

    try:
        findings = load_findings(args.findings)
    except Exception as e:
        print(f"erro ao ler findings: {e}", file=sys.stderr)
        sys.exit(1)

    annotated = []
    counts = {"verified": 0, "unverified": 0, "passthrough": 0}
    for fnd in findings:
        verdict, reason = validate_finding(fnd, ranges, touched, project_dir)
        counts[verdict] += 1
        annotated.append({**fnd, "_verdict": verdict, "_reason": reason})

    if args.json:
        print(json.dumps(annotated, ensure_ascii=False, indent=2))
    else:
        led = ledger_path or "(nenhum ledger encontrado)"
        print(f"ledger: {led}")
        print(f"findings: {len(findings)} · ✅ {counts['verified']} verified · "
              f"❌ {counts['unverified']} unverified · ⏭ {counts['passthrough']} passthrough\n")
        for a in annotated:
            mark = {"verified": "✅", "unverified": "❌", "passthrough": "⏭"}[a["_verdict"]]
            claim = (a.get("claim") or "")[:70]
            print(f"  {mark} {a['_verdict'].upper():11} {claim}\n     ↳ {a['_reason']}")

    if args.gate and counts["unverified"] > 0:
        print(f"\nGATE: {counts['unverified']} finding(s) UNVERIFIED — bloqueado.", file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
