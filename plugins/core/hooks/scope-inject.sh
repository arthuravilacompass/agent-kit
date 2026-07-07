#!/usr/bin/env bash
# desc: PreToolUse(Edit|Write|MultiEdit) — injeta ponteiro de escopo quando o arquivo editado casa um mapa de conhecimento do projeto.
# scope-inject.sh — PreToolUse Edit|Write|MultiEdit hook
# Responsabilidade:
#   Knowledge map: ao tocar uma área mapeada (path → ponteiro de decisão), injeta o
#   ponteiro uma vez por sessão por área (C3 — consumidor de decisões).
#
# Genérico por design — zero área hardcoded. Lê os mapeamentos de um arquivo de
# config do PRÓPRIO projeto: ${CLAUDE_PROJECT_DIR}/.claude/knowledge-map.tsv, uma
# mapping por linha, formato `substring<TAB>mensagem do ponteiro`. `substring` casa
# case-insensitive contra tool_input.file_path. Ausência do arquivo (ou de
# CLAUDE_PROJECT_DIR) → no-op limpo. Cada projeto que quiser este comportamento cria
# o próprio knowledge-map.tsv; o kit não assume nenhum domínio.
#
# Formato do arquivo (linhas em branco e iniciadas por `#` são ignoradas):
#   pubspec.yaml<TAB>[knowledge-map] Mudança em pubspec.yaml: leia docs/pubspec.md
#   deeplink<TAB>[knowledge-map] Área de deeplink: decisões em docs/deeplink.md

set -euo pipefail

if ! command -v python3 &>/dev/null; then
    echo '{}'
    exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-}"
MAP_FILE="${PROJECT_DIR}/.claude/knowledge-map.tsv"

if [ -z "$PROJECT_DIR" ] || [ ! -f "$MAP_FILE" ]; then
    echo '{}'
    exit 0
fi

INPUT_JSON=$(cat)

# Estado persistente do hook — nunca workspace path, nunca ${HOME}/.claude direto.
STATE_DIR="${CLAUDE_PLUGIN_DATA:-${TMPDIR:-/tmp}/agent-kit-core}/state"
mkdir -p "$STATE_DIR"

export INPUT_JSON MAP_FILE STATE_DIR
python3 << 'PYEOF'
import hashlib
import json
import os
import sys

map_file = os.environ.get("MAP_FILE", "")
state_dir = os.environ.get("STATE_DIR", "")

try:
    data = json.loads(os.environ.get("INPUT_JSON", "{}"))
except Exception:
    print("{}"); sys.exit(0)

session_id = data.get("session_id", "unknown")
tool_input = data.get("tool_input", {}) or {}
file_path = tool_input.get("file_path", "") if isinstance(tool_input, dict) else ""
fp_lower = file_path.lower()

if not fp_lower:
    print("{}"); sys.exit(0)

# ── Carrega mapeamentos do config do projeto: `substring<TAB>mensagem` por linha ──
mappings = []  # (key, pattern, message)
try:
    with open(map_file, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = line.split("\t", 1)
            if len(parts) != 2:
                continue
            pattern, message = parts[0].strip(), parts[1].strip()
            if not pattern or not message:
                continue
            key = hashlib.sha1(pattern.encode("utf-8")).hexdigest()[:8]
            mappings.append((key, pattern.lower(), message))
except Exception:
    print("{}"); sys.exit(0)

# Uma área por edit é suficiente: primeiro match (ordem do arquivo) vence, mesmo que
# já tenha sido injetado antes nesta sessão (nesse caso fica em silêncio, não cai
# para o próximo candidato).
matched = None
for key, pattern, message in mappings:
    if pattern in fp_lower:
        matched = (key, message)
        break

if matched is None:
    print("{}"); sys.exit(0)

key, message = matched
marker = os.path.join(state_dir, f"area-{key}-{session_id}")
if os.path.exists(marker):
    print("{}"); sys.exit(0)

try:
    open(marker, "w").close()
except Exception:
    pass

print(json.dumps({"additionalContext": message}, ensure_ascii=False))
PYEOF

exit 0
