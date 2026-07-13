#!/usr/bin/env bash
# desc: PostToolUse(Read|Grep) — records the range read into the session ledger (basis of the citation mechanism). Internal infrastructure of core:grill-me pre-done (operator decision 2026-07-12) — not a standalone gate.
# read-ledger.sh — PostToolUse Read|Grep hook (Layer 1 / citation verification)
#
# Records, per session, the file:line ranges the agent ACTUALLY read. The deterministic
# citation validator (scripts/validate_citations.py) cross-checks later: a finding whose
# evidence.file:lines doesn't overlap anything in the ledger → UNVERIFIED. Purely OBSERVES;
# never blocks (PostToolUse, always exit 0).
#
# Ledger: ${CLAUDE_PLUGIN_DATA}/state/read-ledger-<session_id>.jsonl (1 JSON line per read)
# Fields: {"file","start","end","tool","ts"}  · range 0-0 = file touched, lines unknown.
#
# DESIGN NB: the exact shape of `tool_response` for Read/Grep isn't documented — the hook
# PREFERS parsing the range actually returned (cat -n); if it can't, it falls back to
# tool_input (offset/limit, or the whole file).

set -uo pipefail

if ! command -v python3 &>/dev/null; then
    echo '{}'
    exit 0
fi

INPUT_JSON=$(cat)
export INPUT_JSON

# Hook's persistent state — never a workspace path, never ${HOME}/.claude directly.
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
tool_response = data.get("tool_response", {})        # correct field (not tool_output)
session_id = data.get("session_id", "unknown")

state_dir = os.environ.get("STATE_DIR", "")
try:
    os.makedirs(state_dir, exist_ok=True)
except Exception:
    print("{}"); sys.exit(0)
ledger = os.path.join(state_dir, f"read-ledger-{session_id}.jsonl")


def resp_text(r):
    """Coerces tool_response (variable shape) into a scannable string."""
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
        # 1) prefer the range ACTUALLY returned (lines "   123\t..." from cat -n)
        nums = [int(m) for m in re.findall(r"(?m)^\s*(\d+)\t", resp_text(tool_response))]
        if nums:
            start, end = min(nums), max(nums)
        else:
            # 2) fallback: tool_input offset/limit, else the whole file
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
    # content mode (with -n): "path:line:content"
    for m in re.finditer(r"(?m)^(.+?):(\d+):", txt):
        entries.append((m.group(1), int(m.group(2)), int(m.group(2))))
    # files_with_matches: paths only → file touched, range unknown (0-0)
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
    pass  # the ledger never blocks or fails the hook

print("{}")
sys.exit(0)
PYEOF

exit 0
