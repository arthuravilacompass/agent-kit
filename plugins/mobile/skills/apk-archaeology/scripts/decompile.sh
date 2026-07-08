#!/usr/bin/env bash
# desc: orquestra jadx + apktool sobre um APK (spec §5 [1])
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "uso: decompile.sh <caminho.apk> <dir_saida>" >&2
  exit 1
fi

APK="$1"
OUT="$2"

if ! command -v jadx >/dev/null 2>&1; then
  echo "ERRO: jadx não encontrado no PATH." >&2
  echo "Instale: brew install jadx" >&2
  echo "  ou baixe o release direto: https://github.com/skylot/jadx/releases/latest" >&2
  exit 1
fi

if ! command -v apktool >/dev/null 2>&1; then
  echo "ERRO: apktool não encontrado no PATH." >&2
  echo "Instale: brew install apktool" >&2
  exit 1
fi

if [[ ! -f "$APK" ]]; then
  echo "ERRO: APK não encontrado: $APK" >&2
  exit 1
fi

mkdir -p "$OUT"

echo "[1/2] jadx (source legível)..." >&2
# jadx retorna exit code != 0 quando alguma classe individual falha ao decompilar
# ("finished with errors, count: N") — isso é ESPERADO e normal em app real (obfuscação,
# classes sintéticas), não indica falha da decompilação como um todo. Com set -e/pipefail
# esse código abortaria o script inteiro antes de rodar o apktool — por isso o `|| true`
# aqui, e validamos sucesso pela EXISTÊNCIA de output, não pelo exit code do jadx.
jadx -d "$OUT/jadx" --no-res -j 4 "$APK" 2>&1 | tail -5 || true

if [[ ! -d "$OUT/jadx/sources" ]] || [[ -z "$(find "$OUT/jadx/sources" -name "*.java" -print -quit)" ]]; then
  echo "ERRO: jadx não produziu nenhuma classe decompilada em $OUT/jadx/sources" >&2
  exit 1
fi

echo "[2/2] apktool (manifest/resources)..." >&2
apktool d "$APK" -o "$OUT/apktool" -f >/dev/null 2>&1

CLASS_COUNT=$(find "$OUT/jadx/sources" -name "*.java" | wc -l | tr -d ' ')
echo "OK: $CLASS_COUNT classes em $OUT/jadx/sources; manifest em $OUT/apktool/AndroidManifest.xml" >&2
