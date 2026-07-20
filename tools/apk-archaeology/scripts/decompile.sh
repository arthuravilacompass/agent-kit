#!/usr/bin/env bash
# desc: orchestrates jadx + apktool over an APK (spec §5 [1])
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: decompile.sh <apk-path> <output-dir>" >&2
  exit 1
fi

APK="$1"
OUT="$2"

if ! command -v jadx >/dev/null 2>&1; then
  echo "ERROR: jadx not found on PATH." >&2
  echo "Install: brew install jadx" >&2
  echo "  or download the release directly: https://github.com/skylot/jadx/releases/latest" >&2
  exit 1
fi

if ! command -v apktool >/dev/null 2>&1; then
  echo "ERROR: apktool not found on PATH." >&2
  echo "Install: brew install apktool" >&2
  exit 1
fi

if [[ ! -f "$APK" ]]; then
  echo "ERROR: APK not found: $APK" >&2
  exit 1
fi

mkdir -p "$OUT"

# Run contract (skill topology, SKILL.md "Run layout"): decompile output lives
# under <work_dir>/decompile/ — a gitignored, regenerable cache — while steps
# 2-4's JSON artifacts live under <work_dir>/data/. This is always step 1 of
# the pipeline, so both are created here.
mkdir -p "$OUT/decompile" "$OUT/data"
echo '*' > "$OUT/decompile/.gitignore"

echo "[1/2] jadx (readable source)..." >&2
# jadx returns a non-zero exit code when some individual class fails to decompile
# ("finished with errors, count: N") — this is EXPECTED and normal on a real app
# (obfuscation, synthetic classes), not a sign the decompilation failed as a whole.
# With set -e/pipefail that code would abort the whole script before apktool runs —
# hence the `|| true` here, and we validate success by output EXISTENCE, not jadx's
# exit code.
jadx -d "$OUT/decompile/jadx" --no-res -j 4 "$APK" 2>&1 | tail -5 || true

if [[ ! -d "$OUT/decompile/jadx/sources" ]] || [[ -z "$(find "$OUT/decompile/jadx/sources" -name "*.java" -print -quit)" ]]; then
  echo "ERROR: jadx produced no decompiled classes in $OUT/decompile/jadx/sources" >&2
  exit 1
fi

echo "[2/2] apktool (manifest/resources)..." >&2
if ! apktool d "$APK" -o "$OUT/decompile/apktool" -f 2>&1 | tail -5; then
  echo "ERROR: apktool failed — see output above" >&2
  exit 1
fi

CLASS_COUNT=$(find "$OUT/decompile/jadx/sources" -name "*.java" | wc -l | tr -d ' ')
echo "OK: $CLASS_COUNT classes in $OUT/decompile/jadx/sources; manifest at $OUT/decompile/apktool/AndroidManifest.xml" >&2
