#!/usr/bin/env bash
# Gate de higiene: nada de conteúdo do domínio/empresa no kit (inclusive archive/).
set -euo pipefail
cd "$(dirname "$0")/.."
DENY='TF-[0-9]{3,}|TF-\\d|BM-[0-9]+|ID-[0-9]{6}|tfsports|tf\.com\.br|[Bb]usinessmap|TFTokens|TFC Market|TF Mall|squad-produtos|[Bb]itrise|release_26|snapshot/26|tf-[a-z]+-mobile|tf-mobile-workspace|arthuravila'
if grep -rInE "$DENY" --exclude-dir=.git --exclude-dir=.superpowers --exclude=check-no-tf.sh . ; then
  echo "FALHOU: conteúdo TF encontrado (acima)"; exit 1
fi
echo "OK: zero conteúdo TF"
