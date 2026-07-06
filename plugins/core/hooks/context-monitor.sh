#!/usr/bin/env bash
# context-monitor.sh — PostToolUse hook
# Monitors transcript size as proxy for context window usage.
# Warns once per threshold level per session (debounced via state file).
# No native API for context % exists — transcript file size is the best proxy.

set -euo pipefail

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

TRANSCRIPT_PATH=$(python3 -c "
import json, sys
try:
    data = json.loads(sys.stdin.read())
    print(data.get('transcript_path', ''))
except Exception:
    print('')
" <<< "$INPUT_JSON" 2>/dev/null || echo "")

if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
    echo '{}'
    exit 0
fi

# Estado persistente do hook — nunca workspace path, nunca ${HOME}/.claude direto.
# CLAUDE_PLUGIN_DATA sobrevive a updates do plugin; fallback só para invocação standalone
# (fora do processo de hook do Claude Code, ex.: smoke test manual).
STATE_DIR="${CLAUDE_PLUGIN_DATA:-${TMPDIR:-/tmp}/agent-kit-core}/state"
mkdir -p "$STATE_DIR"

export TRANSCRIPT_PATH
export SESSION_ID
export STATE_DIR

python3 << 'PYEOF'
import json, os, sys

transcript = os.environ.get("TRANSCRIPT_PATH", "")
session_id = os.environ.get("SESSION_ID", "unknown")
state_dir  = os.environ.get("STATE_DIR", "")

if not transcript or not os.path.isfile(transcript):
    print("{}")
    sys.exit(0)

size_bytes = os.path.getsize(transcript)

# Thresholds — calibrate based on observed session sizes
LEVELS = [
    (1_200_000, "critical", "[context-monitor] CRÍTICO / CRITICAL: transcript em {kb}KB. ESCREVA um handoff AGORA em docs/superpowers/handoffs/<AAAA-MM-DD>-<tarefa>.md (tarefa atual, decisões tomadas, próximos passos, arquivos tocados) e então rode /compact — plan-autoload surfaça esse handoff na próxima sessão. / Write a handoff to docs/superpowers/handoffs/ NOW, then /compact; plan-autoload resurfaces it next session."),
    (  800_000, "alert",    "[context-monitor] AVISO / WARNING: transcript em {kb}KB. Antes de /compact, escreva um handoff em docs/superpowers/handoffs/<AAAA-MM-DD>-<tarefa>.md (estado atual + próximos passos + arquivos tocados) — plan-autoload lê de lá na próxima sessão. / Before /compact, write a handoff to docs/superpowers/handoffs/ — plan-autoload reads it next session."),
    (  500_000, "warn",     "[context-monitor] Contexto crescendo ({kb}KB). Planeje um /compact em breve. / Context growing. Plan a /compact soon."),
]

matched_level = None
matched_msg   = None

for threshold, level, template in LEVELS:
    if size_bytes >= threshold:
        matched_level = level
        matched_msg   = template.format(kb=size_bytes // 1000)
        break

if not matched_level:
    print("{}")
    sys.exit(0)

# Debounce: only warn once per level per session
marker = os.path.join(state_dir, f"ctx-warned-{session_id}-{matched_level}")
if os.path.exists(marker):
    print("{}")
    sys.exit(0)

# Write marker so this level won't fire again this session
try:
    with open(marker, "w") as f:
        f.write(matched_level)
except Exception:
    pass  # Never block on state write failure

print(json.dumps({"additionalContext": matched_msg}))
PYEOF

exit 0
