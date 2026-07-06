#!/usr/bin/env bash
# prune_branches.sh — lista branches remotos candidatos a deleção. NUNCA deleta — gera
# um arquivo de comandos para revisão manual antes de qualquer `git push --delete`.
# Branches "stale-unmerged" têm commits únicos: exigem inspeção individual
# (git log <base-branch>..<branch>) antes de deletar.
#
# Uso: ./prune_branches.sh <base-branch> [dias_stale] [protected-regex]
#   base-branch      ref usada para checar merge (ex.: origin/main)
#   dias_stale       default 90
#   protected-regex  extended regex de prefixos nunca sugeridos p/ delete
#                     (default: protege a própria base + main/HEAD)
set -euo pipefail
BASE_BRANCH="${1:?uso: prune_branches.sh <base-branch> [dias_stale] [protected-regex]}"
STALE_DAYS="${2:-90}"
BASE_SHORT="${BASE_BRANCH#origin/}"
PROTECTED="${3:-^[[:space:]]*(origin/)?(${BASE_SHORT}|main|HEAD)}"
NOW=$(date +%s)
OUT="${TMPDIR:-/tmp}/prune_branches_$(date +%y%m%d).sh"
echo "#!/usr/bin/env bash" > "$OUT"
git fetch --prune origin
MERGED=$(git branch -r --merged "$BASE_BRANCH" | grep -vE "$PROTECTED" || true)
for b in $MERGED; do echo "git push origin --delete ${b#origin/}  # merged (seguro)" >> "$OUT"; done
echo "# --- STALE-UNMERGED: commits únicos possíveis — INSPECIONE antes ---" >> "$OUT"
for b in $(git branch -r | grep -vE "$PROTECTED" | grep -vF "$MERGED" || true); do
  LAST=$(git log -1 --format=%ct "$b" 2>/dev/null || echo "$NOW")
  AGE=$(( (NOW - LAST) / 86400 ))
  if (( AGE > STALE_DAYS )); then echo "git push origin --delete ${b#origin/}  # stale ${AGE}d UNMERGED" >> "$OUT"; fi
done
chmod +x "$OUT"
echo "Candidatos em $OUT — REVISE antes de executar (total: $(grep -c 'git push' "$OUT" || echo 0))"
