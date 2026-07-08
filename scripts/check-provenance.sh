#!/usr/bin/env bash
# Hygiene gate: no content from the origin domain/company in the kit (including unwired/).
# Exit: 0 = clean · 1 = provenance content found · >=2 = grep aborted (indeterminate).
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
DENY='TF-[0-9]{3,}|TF-\\d|BM-[0-9]+|ID-[0-9]{6}|tfsports|tf\.com\.br|[Bb]usinessmap|TFTokens|TFC Market|TF Mall|squad-produtos|[Bb]itrise|release_26|snapshot/26|tf-[a-z]+-mobile|tf-mobile-workspace|arthuravila'
grep -rInE "$DENY" --exclude-dir=.git --exclude-dir=.superpowers --exclude-dir=.worktrees --exclude=check-provenance.sh .
rc=$?
if [ "$rc" -eq 0 ]; then
  echo "FAILED: provenance content found (above)"
  exit 1
elif [ "$rc" -ge 2 ]; then
  echo "ERROR: grep aborted (exit $rc) — indeterminate result, do NOT treat as clean"
  exit "$rc"
fi
echo "OK: zero provenance content"
