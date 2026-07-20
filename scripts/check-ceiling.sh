#!/usr/bin/env bash
# desc: Byte-ceiling gate — always-on tier's 16,384-byte ceiling + provenance-narration ban in plugins/.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

CEILING=16384
fail=0

# 1) Always-on ceiling: session-start.sh's actual output (full JSON)
# stdin explicitly /dev/null: session-start.sh now reads its own stdin (session-model
# persistence) — without this redirect, an interactive invocation (e.g. doctor.sh run
# from a terminal) would hang waiting for input instead of measuring the ceiling.
out=$(CLAUDE_PLUGIN_ROOT="plugins/core" bash plugins/core/hooks/session-start.sh </dev/null 2>&1)
rc=$?
if [ "$rc" -ne 0 ]; then
  echo "ERROR: session-start.sh failed (rc=$rc) — ceiling not measured"
  echo "$out" | head -5
  fail=1
else
  bytes=$(printf '%s' "$out" | wc -c | tr -d ' ')
  if [ "$bytes" -gt "$CEILING" ]; then
    echo "ERROR: always-on tier measures ${bytes} bytes — over the ${CEILING}-byte ceiling (docs/GOVERNANCE.md §Always-on tier ceiling)"
    fail=1
  else
    echo "OK: always-on tier ${bytes} bytes <= ceiling ${CEILING}"
  fi
fi

# 2) Provenance-narration ban, scoped to plugins/: "Promoted from" belongs in
# CHANGELOG.md, not in a shipped skill/agent body. Scoped (not repo-wide) so the
# CHANGELOG's own legitimate promotion narration never trips it.
hits=$(grep -rIn 'Promoted from' plugins/ 2>/dev/null)
if [ -n "$hits" ]; then
  echo "ERROR: provenance narration ('Promoted from') found in plugins/:"
  echo "$hits"
  fail=1
else
  echo "OK: zero provenance narration ('Promoted from') in plugins/"
fi

# 3) Personal memory index (MEMORY.md) byte ceiling. Soft check: the memory
# dir is per-machine/per-user (Claude Code project encoding), so a missing
# file (fresh clone, different user) SKIPs instead of failing the gate.
MEMORY_CEILING=8192
mem_file="$HOME/.claude/projects/$(pwd | sed 's,/,-,g')/memory/MEMORY.md"
if [ -f "$mem_file" ]; then
  mem_bytes=$(wc -c <"$mem_file" | tr -d ' ')
  if [ "$mem_bytes" -gt "$MEMORY_CEILING" ]; then
    echo "ERROR: MEMORY.md index measures ${mem_bytes} bytes — over the ${MEMORY_CEILING}-byte ceiling"
    fail=1
  else
    echo "OK: MEMORY.md index ${mem_bytes} bytes <= ceiling ${MEMORY_CEILING}"
  fi
else
  echo "SKIP: MEMORY.md not found at ${mem_file} (no personal memory dir on this machine)"
fi

exit $fail
