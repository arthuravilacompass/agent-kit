#!/usr/bin/env bash
# desc: PreToolUse(Edit|Write|MultiEdit) — injects a scope pointer when the edited file matches a project knowledge map.
# scope-inject.sh — PreToolUse Edit|Write|MultiEdit hook
# Responsibility:
#   Knowledge map: when touching a mapped area (path → decision pointer), injects the
#   pointer once per session per area (C3 — decision consumer).
#
# Generic by design — zero hardcoded area. Reads the mappings from a config file of
# the project ITSELF: ${CLAUDE_PROJECT_DIR}/.claude/knowledge-map.tsv, one mapping per
# line, format `substring<TAB>pointer message`. `substring` matches case-insensitive
# against tool_input.file_path. Absence of the file (or of CLAUDE_PROJECT_DIR) → clean
# no-op. Any project that wants this behavior creates its own knowledge-map.tsv; the
# kit assumes no domain.
#
# File format (blank lines and lines starting with `#` are ignored):
#   pubspec.yaml<TAB>[knowledge-map] Change to pubspec.yaml: read docs/pubspec.md
#   deeplink<TAB>[knowledge-map] Deeplink area: decisions in docs/deeplink.md

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

# Hook's persistent state — never a workspace path, never ${HOME}/.claude directly.
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

# ── Loads mappings from the project's config: `substring<TAB>message` per line ──
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

# One area per edit is enough: first match (file order) wins, even if it was already
# injected earlier this session (in that case it stays silent, it doesn't fall through
# to the next candidate).
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
