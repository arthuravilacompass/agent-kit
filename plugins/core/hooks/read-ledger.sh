#!/usr/bin/env bash
# read-ledger.sh — PostToolUse Read|Grep hook (Camada 1 / verificação por citação)
#
# Registra, por sessão, os ranges file:line que o agente REALMENTE leu. O validador
# determinístico de citação (scripts/validate_citations.py) cruza depois: finding cuja
# evidence.file:lines não sobrepõe nada no ledger → UNVERIFIED. Apenas OBSERVA; nunca
# bloqueia (PostToolUse, sempre exit 0).
#
# Ledger: ${CLAUDE_PLUGIN_DATA}/state/read-ledger-<session_id>.jsonl (1 linha JSON/leitura)
# Campos: {"file","start","end","tool","ts"}  · range 0-0 = arquivo tocado, linhas desconhecidas.
#
# DESIGN NB: a forma exata de `tool_response` para Read/Grep não é documentada — o hook
# PREFERE parsear o range realmente retornado (cat -n); se não conseguir, cai para
# tool_input (offset/limit, ou arquivo inteiro).

set -uo pipefail

if ! command -v python3 &>/dev/null; then
    echo '{}'
    exit 0
fi

INPUT_JSON=$(cat)
export INPUT_JSON

# Estado persistente do hook — nunca workspace path, nunca ${HOME}/.claude direto.
STATE_DIR="${CLAUDE_PLUGIN_DATA:-${TMPDIR:-/tmp}/agent-kit-core}/state"
export STATE_DIR

python3 << 'PYEOF'
import json, os, re, sys, time

try:
    data = json.loads(os.environ.get("INPUT_JSON", "{}"))
except Exception:
    print("{}"); sys.exit(0)

tool_name = data.get("tool_name", "")
if tool_name not in ("Read", "Grep"):
    print("{}"); sys.exit(0)

tool_input = data.get("tool_input", {}) or {}
tool_response = data.get("tool_response", {})        # campo correto (não tool_output)
session_id = data.get("session_id", "unknown")

state_dir = os.environ.get("STATE_DIR", "")
try:
    os.makedirs(state_dir, exist_ok=True)
except Exception:
    print("{}"); sys.exit(0)
ledger = os.path.join(state_dir, f"read-ledger-{session_id}.jsonl")


def resp_text(r):
    """Coage tool_response (shape variável) numa string escaneável."""
    if isinstance(r, str):
        return r
    if isinstance(r, dict):
        for k in ("content", "output", "text", "result", "stdout"):
            v = r.get(k)
            if isinstance(v, str):
                return v
            if isinstance(v, list):
                parts = []
                for b in v:
                    if isinstance(b, dict) and isinstance(b.get("text"), str):
                        parts.append(b["text"])
                    elif isinstance(b, str):
                        parts.append(b)
                if parts:
                    return "\n".join(parts)
    return ""


entries = []  # (file, start, end)

if tool_name == "Read":
    fp = tool_input.get("file_path", "")
    if fp:
        # 1) preferir o range REALMENTE retornado (linhas "   123\t..." do cat -n)
        nums = [int(m) for m in re.findall(r"(?m)^\s*(\d+)\t", resp_text(tool_response))]
        if nums:
            start, end = min(nums), max(nums)
        else:
            # 2) fallback: tool_input offset/limit, senão arquivo inteiro
            off, lim = tool_input.get("offset"), tool_input.get("limit")
            if isinstance(off, int):
                start = off
                end = off + lim - 1 if isinstance(lim, int) else off + 1999
            else:
                start = 1
                try:
                    with open(fp, encoding="utf-8", errors="replace") as f:
                        end = sum(1 for _ in f)
                except Exception:
                    end = start
        entries.append((fp, start, end))

elif tool_name == "Grep":
    txt = resp_text(tool_response)
    # content mode (com -n): "path:line:conteúdo"
    for m in re.finditer(r"(?m)^(.+?):(\d+):", txt):
        entries.append((m.group(1), int(m.group(2)), int(m.group(2))))
    # files_with_matches: só paths → arquivo tocado, range desconhecido (0-0)
    if not entries:
        for m in re.finditer(r"(?m)^(/.+?)\s*$", txt):
            entries.append((m.group(1).strip(), 0, 0))

if not entries:
    print("{}"); sys.exit(0)

ts = int(time.time())
try:
    with open(ledger, "a") as f:
        for fp, s, e in entries:
            f.write(json.dumps({"file": fp, "start": s, "end": e, "tool": tool_name, "ts": ts}) + "\n")
except Exception:
    pass  # ledger nunca bloqueia nem falha o hook

print("{}")
sys.exit(0)
PYEOF

exit 0
