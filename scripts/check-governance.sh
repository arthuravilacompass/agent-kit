#!/usr/bin/env bash
# desc: Gate de governança — teto de bytes do tier sempre-ativo + resolução de todo ID D*/R* citado no ledger de docs/GOVERNANCE.md.
set -uo pipefail
cd "$(dirname "$0")/.."

CEILING=16384
LEDGER="docs/GOVERNANCE.md"
fail=0

# 1) Teto do sempre-ativo: saída real do session-start.sh (JSON completo)
out=$(CLAUDE_PLUGIN_ROOT="plugins/core" bash plugins/core/hooks/session-start.sh 2>&1)
rc=$?
if [ "$rc" -ne 0 ]; then
  echo "ERRO: session-start.sh falhou (rc=$rc) — teto não medido"
  echo "$out" | head -5
  fail=1
else
  bytes=$(printf '%s' "$out" | wc -c | tr -d ' ')
  if [ "$bytes" -gt "$CEILING" ]; then
    echo "ERRO: sempre-ativo mede ${bytes} bytes — acima do teto de ${CEILING} (docs/GOVERNANCE.md §Teto)"
    fail=1
  else
    echo "OK: sempre-ativo ${bytes} bytes <= teto ${CEILING}"
  fi
fi

# 2) Todo ID D*/R* citado no repo resolve no ledger
# git grep -E não suporta \b — usar grep do sistema, no mesmo padrão do
# check-provenance.sh (sem xargs: robusto a filename com espaço, rc verificável).
# superpowers/.superpowers é resíduo de construção, fora do escopo do censo.
ids=$(grep -rhoE --include='*.md' --exclude-dir=superpowers --exclude-dir=.superpowers \
  '\b[DR][0-9]+\b' . | sort -u)
rc=$?
if [ "$rc" -ge 2 ]; then
  echo "ERRO: census de IDs falhou (rc=$rc) — resolução no ledger não verificada"
  fail=1
elif [ -z "$ids" ]; then
  echo "OK: nenhum ID D*/R* citado no repo"
else
  missing=0
  for id in $ids; do
    if ! grep -qE "^- \*\*${id}\*\*" "$LEDGER"; then
      echo "ERRO: ID ${id} citado no repo sem entrada no ledger (${LEDGER})"
      fail=1
      missing=1
    fi
  done
  if [ "$missing" -eq 0 ]; then
    echo "OK: todo ID citado resolve no ledger ($(echo "$ids" | tr '\n' ' '))"
  fi
fi

exit $fail
