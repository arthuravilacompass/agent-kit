#!/usr/bin/env bash
# Mechanical protection for the README pair (README.md source-of-truth,
# README.pt-BR.md the translation): before any restructuring touches the pair,
# this gate pins the invariants a restructure could silently break.
#
# Sub-checks:
#   1) Every fenced ```bash block in the PT-BR translation exists byte-identically
#      somewhere in README.md or docs/INSTALL.md (directional subset: the
#      translation's commands must be verbatim copies of the English source's;
#      docs/INSTALL.md may not exist yet — treated as an empty haystack).
#   2) Every SVG asset referenced by either README (via <picture>/<img>/markdown
#      image syntax pointing at assets/*.svg) exists and is marked
#      data-look="handDrawn". Vacuously green when no SVG is referenced (true
#      today — the repo has no such reference yet).
#   3) Both files carry their source-of-truth header substance: README.md's
#      header declares itself the source; README.pt-BR.md's declares English
#      as the source it follows.
#
# Env overrides (scratch-copy testing, mirrors check-ceiling.sh's CEILING_OVERRIDE
# style): README_EN, README_PT default to the repo's real pair; README_INSTALL
# defaults to docs/INSTALL.md.
#
# Exit: 0 = clean · 1 = drift/violation found · 2 = indeterminate (files missing).
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

README_EN="${README_EN:-README.md}"
README_PT="${README_PT:-README.pt-BR.md}"
README_INSTALL="${README_INSTALL:-docs/INSTALL.md}"
fail=0

if [ ! -f "$README_EN" ]; then
  echo "ERROR: $README_EN not found — indeterminate, cannot check the pair" >&2
  exit 2
fi
if [ ! -f "$README_PT" ]; then
  echo "ERROR: $README_PT not found — indeterminate, cannot check the pair" >&2
  exit 2
fi

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

# --- 1) Fenced bash blocks: PT-BR must be a byte-identical subset of EN+INSTALL ----
# Build the haystack: README.md, plus docs/INSTALL.md if it exists (missing = empty set).
haystack_file="$WORKDIR/haystack"
cat "$README_EN" >"$haystack_file"
if [ -f "$README_INSTALL" ]; then
  cat "$README_INSTALL" >>"$haystack_file"
fi

# Extract every ```bash ... ``` block from a file as records, each prefixed with
# the 1-based line number of its first content line (for error reporting).
extract_bash_blocks() {
  awk '
    /^```bash[ \t]*$/ { if (!inblock) { inblock=1; startline=NR+1; buf=""; next } }
    inblock && /^```[ \t]*$/ { inblock=0; printf "###BLOCK_START:%d###\n", startline; printf "%s", buf; printf "###BLOCK_END###\n"; next }
    inblock { buf = buf $0 "\n" }
  ' "$1"
}

fence_fail=0
block_start=""
content=""
while IFS= read -r line; do
  if [[ "$line" =~ ^###BLOCK_START:([0-9]+)###$ ]]; then
    block_start="${BASH_REMATCH[1]}"
    content=""
    continue
  fi
  if [ "$line" = "###BLOCK_END###" ]; then
    needle_file="$WORKDIR/needle"
    printf '%s' "$content" >"$needle_file"
    if ! python3 -c '
import sys
needle = open(sys.argv[1], "rb").read()
hay = open(sys.argv[2], "rb").read()
sys.exit(0 if needle in hay else 1)
' "$needle_file" "$haystack_file"; then
      echo "ERROR: $README_PT:$block_start — bash fence not found byte-identically in $README_EN or $README_INSTALL"
      fence_fail=1
    fi
    continue
  fi
  content="${content}${line}"$'\n'
done < <(extract_bash_blocks "$README_PT")

if [ "$fence_fail" -eq 1 ]; then
  fail=1
else
  echo "OK: every $README_PT bash fence matches byte-identically in $README_EN/$README_INSTALL"
fi

# --- 2) Referenced SVG assets exist and carry data-look="handDrawn" ----------------
svg_refs=$(grep -ohE 'assets/[A-Za-z0-9_./-]*\.svg' "$README_EN" "$README_PT" 2>/dev/null | sort -u)
if [ -z "$svg_refs" ]; then
  echo "OK: no SVG assets referenced by the README pair (vacuously green)"
else
  svg_fail=0
  while IFS= read -r svg; do
    [ -z "$svg" ] && continue
    if [ ! -f "$svg" ]; then
      echo "ERROR: referenced SVG asset '$svg' does not exist"
      svg_fail=1
      continue
    fi
    if ! grep -q 'data-look="handDrawn"' "$svg"; then
      echo "ERROR: referenced SVG asset '$svg' exists but lacks data-look=\"handDrawn\""
      svg_fail=1
    fi
  done <<<"$svg_refs"
  if [ "$svg_fail" -eq 1 ]; then
    fail=1
  else
    echo "OK: every referenced SVG asset exists and carries data-look=\"handDrawn\""
  fi
fi

# --- 3) Source-of-truth cross-link headers, substance not exact prose -------------
en_line3=$(sed -n '3p' "$README_EN")
pt_line3=$(sed -n '3p' "$README_PT")

if ! grep -qi 'source of truth' <<<"$en_line3"; then
  echo "ERROR: $README_EN:3 does not declare itself the source of truth: $en_line3"
  fail=1
else
  echo "OK: $README_EN:3 declares itself the source of truth"
fi

if ! grep -qi 'fonte de verdade' <<<"$pt_line3" || ! grep -q "$(basename "$README_EN")" <<<"$pt_line3"; then
  echo "ERROR: $README_PT:3 does not declare $README_EN as the source of truth: $pt_line3"
  fail=1
else
  echo "OK: $README_PT:3 declares $README_EN as the source of truth"
fi

exit $fail
