#!/usr/bin/env bash
# handoff-gate.sh — Stop hook (UNWIRED — presente no repo, não carregado)
#
# Fecha o loop alerta→ação do context-monitor: se a sessão cruzou 800KB de
# transcript e NENHUM handoff foi escrito/atualizado em docs/superpowers/handoffs/
# nas últimas 12h, bloqueia o stop UMA vez por sessão pedindo o handoff. O
# plan-autoload resurfaça o handoff na próxima sessão.
#
# Por que está em unwired/ e não em plugins/: no projeto de origem este hook nunca
# foi registrado em settings algum — existia (com evals passando) sem nunca ter
# disparado, e foi descartado na extração como "peso morto com aparência de vivo".
# A rodada de revisão pós-construção (censo cego, 2026-07-06) avaliou o mérito do
# mecanismo de forma independente (nota 4/5) e o artefato foi resgatado pra cá:
# preserva a opção sem custo de contexto. Promoção a wired segue a regra do
# docs/GOVERNANCE.md — exige uso real, não mérito percebido.
#
# Notas pra promoção (se um dia subir pra plugins/core):
#   1. Registrar em hooks/hooks.json no evento Stop.
#   2. Migrar o state dir de ~/.claude/hooks/state para ${CLAUDE_PLUGIN_DATA}.
#   3. Recriar casos de eval tier-1 (threshold, debounce por sessão,
#      stop_hook_active, handoff recente suprime o bloqueio).
#
# Salvaguardas contra loop: respeita stop_hook_active e marker por sessão.

set -uo pipefail

if ! command -v python3 &>/dev/null; then
    echo '{}'
    exit 0
fi

INPUT_JSON=$(cat)
export INPUT_JSON
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export PROJECT_DIR

python3 << 'PYEOF'
import json, os, sys, time

try:
    data = json.loads(os.environ.get("INPUT_JSON", "{}"))
except Exception:
    print("{}"); sys.exit(0)

# Nunca bloquear duas vezes na mesma cadeia de stop
if data.get("stop_hook_active"):
    print("{}"); sys.exit(0)

transcript = data.get("transcript_path", "")
session_id = data.get("session_id", "unknown")

THRESHOLD = 800_000  # mesmo limiar "alert" do context-monitor.sh
if not transcript or not os.path.isfile(transcript) or os.path.getsize(transcript) < THRESHOLD:
    print("{}"); sys.exit(0)

# Handoff recente (12h) já existe? — então o trabalho está persistido
handoffs_dir = os.path.join(os.environ.get("PROJECT_DIR", ""), "docs", "superpowers", "handoffs")
now = time.time()
if os.path.isdir(handoffs_dir):
    for f in os.listdir(handoffs_dir):
        if f.endswith(".md"):
            try:
                if now - os.path.getmtime(os.path.join(handoffs_dir, f)) < 12 * 3600:
                    print("{}"); sys.exit(0)
            except OSError:
                continue

# Debounce: bloqueia no máximo 1 vez por sessão
state_dir = os.path.join(os.path.expanduser("~"), ".claude", "hooks", "state")
os.makedirs(state_dir, exist_ok=True)
marker = os.path.join(state_dir, f"handoff-gated-{session_id}")
if os.path.exists(marker):
    print("{}"); sys.exit(0)
try:
    open(marker, "w").close()
except Exception:
    pass

print(json.dumps({
    "decision": "block",
    "reason": (
        "[handoff-gate] Sessão >800KB sem handoff recente. Antes de encerrar, escreva "
        "docs/superpowers/handoffs/<AAAA-MM-DD>-<tarefa>.md com: tarefa atual, decisões tomadas, "
        "próximos passos, arquivos tocados. O plan-autoload resurfaça na próxima sessão. "
        "Se a sessão genuinamente não tem trabalho a persistir, diga isso ao usuário e encerre."
    ),
}))
PYEOF

exit 0
