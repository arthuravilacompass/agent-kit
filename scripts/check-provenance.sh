#!/usr/bin/env bash
# Gate de higiene: nada de conteúdo do domínio/empresa de origem no kit (inclusive unwired/).
# Exit: 0 = limpo · 1 = conteúdo de proveniência encontrado · >=2 = grep abortou (indeterminado).
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
DENY='TF-[0-9]{3,}|TF-\\d|BM-[0-9]+|ID-[0-9]{6}|tfsports|tf\.com\.br|[Bb]usinessmap|TFTokens|TFC Market|TF Mall|squad-produtos|[Bb]itrise|release_26|snapshot/26|tf-[a-z]+-mobile|tf-mobile-workspace|arthuravila'
grep -rInE "$DENY" --exclude-dir=.git --exclude-dir=.superpowers --exclude=check-provenance.sh .
rc=$?
if [ "$rc" -eq 0 ]; then
  echo "FALHOU: conteúdo de proveniência encontrado (acima)"
  exit 1
elif [ "$rc" -ge 2 ]; then
  echo "ERRO: grep abortou (exit $rc) — resultado indeterminado, NÃO tratar como limpo"
  exit "$rc"
fi
echo "OK: zero conteúdo de proveniência"
