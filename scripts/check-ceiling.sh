#!/usr/bin/env bash
# desc: Provenance-narration ban in plugins/ + personal MEMORY.md byte-ceiling sub-check.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

fail=0

# 1) Provenance-narration ban, scoped to plugins/: "Promoted from" (and variants —
# "Promotion from", lowercase, or with text in between, e.g. "Promoted 2026-07-26
# from") belongs in CHANGELOG.md, not in a shipped skill/agent body. Case-insensitive
# and tolerant of an inserted date/clause is deliberate: a literal-string match let
# "Promoted 2026-07-26 from ..." through once already (the two words split by a date).
# `[^.]{0,40}` bounds the gap to the same sentence, so it can't reach across a
# period into unrelated prose. Scoped (not repo-wide) so the CHANGELOG's own
# legitimate promotion narration never trips it. Validated against a manual review
# of every "promot*" hit in plugins/ (incl. case-insensitive) at the time this
# pattern was written: legitimate uses either don't pair "promot(ed|ion)" with
# "from" at all, or the two words aren't followed by "from" within the same clause
# (e.g. "promotion to BLOCKER", "promoted this gate", "not yet promoted to wired") —
# none of them false-positive against this pattern.
hits=$(grep -rEIni 'promot(ed|ion)[^.]{0,40}from' plugins/ 2>/dev/null)
if [ -n "$hits" ]; then
  echo "ERROR: provenance narration ('Promoted from' or a variant) found in plugins/:"
  echo "$hits"
  fail=1
else
  echo "OK: zero provenance narration ('Promoted from' or a variant) in plugins/"
fi

# 2) Personal memory index (MEMORY.md) byte ceiling. Soft check: the memory
# dir is per-machine/per-user (Claude Code project encoding), so a missing
# file (fresh clone, different user) SKIPs instead of failing the gate.
# Raised 8192 -> 12288 on 2026-08-03 (operator call): the index kept hitting the
# original ceiling on ordinary session-end writes, forcing a trim pass every time.
MEMORY_CEILING=12288
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
