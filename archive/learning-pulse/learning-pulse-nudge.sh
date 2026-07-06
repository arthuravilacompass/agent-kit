#!/usr/bin/env bash
# learning-pulse-nudge.sh — UserPromptSubmit hook (ARQUIVADO, não wired)
#
# Extraído de um hook de dois propósitos num projeto de origem. O outro propósito
# (reset de debounce de um hook de scope-injection) foi resolvido de outra forma no
# `plugins/core` deste kit (ver hooks/scope-inject.sh) — não sobrevive aqui porque
# depende de um mecanismo antigo que já foi redesenhado.
#
# Este arquivo preserva SÓ o nudge: a cada N mensagens do usuário na sessão, injeta
# um lembrete pra considerar capturar correções/preferências em memória (skill
# `learn` ou memory write inline).
#
# STATUS: advisory nudge, mediu ~0 conversão em uso real (o hook original foi
# removido do projeto de origem por essa razão) — só volta a ser wired com medição
# nova que sustente o custo de contexto do lembrete. Fica em archive como material
# de referência, não como recomendação de reativar sem dado.
#
# Outputs JSON com additionalContext opcional, no formato entendido pelo Claude Code.

set -euo pipefail

NUDGE_EVERY="${LEARNING_PULSE_EVERY:-15}"   # a cada N mensagens

if ! command -v python3 &>/dev/null; then
    echo '{}'
    exit 0
fi

INPUT_JSON=$(cat)

SESSION_ID=$(python3 -c "
import json, sys
try:
    data = json.loads(sys.stdin.read())
    print(data.get('session_id', 'unknown'))
except Exception:
    print('unknown')
" <<< "$INPUT_JSON" 2>/dev/null || echo "unknown")

STATE_DIR="${CLAUDE_PLUGIN_DATA:-${TMPDIR:-/tmp}/agent-kit-archive}/state"
mkdir -p "$STATE_DIR"

COUNTER_FILE="${STATE_DIR}/msg-count-${SESSION_ID}"
COUNT=0
if [ -f "$COUNTER_FILE" ]; then
    COUNT=$(cat "$COUNTER_FILE" 2>/dev/null || echo 0)
fi
COUNT=$((COUNT + 1))
echo "$COUNT" > "$COUNTER_FILE"

# Lazy cleanup: once per session, purge state files older than 7 days
CLEANUP_MARKER="${STATE_DIR}/.cleanup-${SESSION_ID}"
if [ ! -f "$CLEANUP_MARKER" ]; then
    find "$STATE_DIR" -name "msg-count-*" -mtime +7 -delete 2>/dev/null || true
    find "$STATE_DIR" -name ".cleanup-*" -mtime +7 -delete 2>/dev/null || true
    touch "$CLEANUP_MARKER"
fi

if [ $((COUNT % NUDGE_EVERY)) -eq 0 ]; then
    python3 -c "
import json
ctx = '[learning-reminder] Esta sessão tem ${COUNT} mensagens. Se o usuário fez correções ou estabeleceu preferências, considere capturar em memory tipada (inline ou via skill learn).'
print(json.dumps({'hookSpecificOutput': {'hookEventName': 'UserPromptSubmit', 'additionalContext': ctx}}))
"
else
    echo '{}'
fi

exit 0
