#!/usr/bin/env bash
# desc: Lists remote branches that are deletion candidates; never deletes, generates a file for manual review.
# prune_branches.sh — lists remote branches that are deletion candidates. NEVER deletes —
# generates a file of commands for manual review before any `git push --delete`.
# "Stale-unmerged" branches have unique commits: they require individual inspection
# (git log <base-branch>..<branch>) before deleting.
#
# Usage: ./prune_branches.sh <base-branch> [stale_days] [protected-regex]
#   base-branch      ref used to check merge status (e.g. origin/main)
#   stale_days       default 90
#   protected-regex  extended regex of prefixes never suggested for deletion
#                     (default: protects the base itself + main/HEAD)
set -euo pipefail
BASE_BRANCH="${1:?usage: prune_branches.sh <base-branch> [stale_days] [protected-regex]}"
STALE_DAYS="${2:-90}"
BASE_SHORT="${BASE_BRANCH#origin/}"
PROTECTED="${3:-^[[:space:]]*(origin/)?(${BASE_SHORT}|main|HEAD)}"
NOW=$(date +%s)
OUT="${TMPDIR:-/tmp}/prune_branches_$(date +%y%m%d).sh"
echo "#!/usr/bin/env bash" > "$OUT"
git fetch --prune origin
MERGED=$(git branch -r --merged "$BASE_BRANCH" | grep -vE "$PROTECTED" || true)
for b in $MERGED; do echo "git push origin --delete ${b#origin/}  # merged (safe)" >> "$OUT"; done
echo "# --- STALE-UNMERGED: possible unique commits — INSPECT before deleting ---" >> "$OUT"
for b in $(git branch -r | grep -vE "$PROTECTED" | grep -vF "$MERGED" || true); do
  LAST=$(git log -1 --format=%ct "$b" 2>/dev/null || echo "$NOW")
  AGE=$(( (NOW - LAST) / 86400 ))
  if (( AGE > STALE_DAYS )); then echo "git push origin --delete ${b#origin/}  # stale ${AGE}d UNMERGED" >> "$OUT"; fi
done
chmod +x "$OUT"
echo "Candidates in $OUT — REVIEW before running (total: $(grep -c 'git push' "$OUT" || echo 0))"
