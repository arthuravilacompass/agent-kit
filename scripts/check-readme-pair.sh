#!/usr/bin/env bash
# Mechanical protection for the README pair (README.md source-of-truth,
# README.pt-BR.md the translation): before any restructuring touches the pair,
# this gate pins the invariants a restructure could silently break.
#
# Sub-checks:
#   1) Every fenced ```bash block in the PT-BR translation exists byte-identically
#      as a whole block somewhere in README.md or docs/INSTALL.md (directional
#      subset: the translation's commands must be verbatim copies of the English
#      source's; docs/INSTALL.md may not exist yet — treated as an empty haystack).
#      Fence extraction is indent- and backtick-count aware (CommonMark-style:
#      an opener of N backticks needs a closer of >= N; extra leading whitespace
#      and a trailing info string after `bash` don't hide a fence), tolerates
#      CRLF line endings, and hard-fails on an unterminated fence or on an
#      opener/extracted-block count mismatch (the extractor silently dropping a
#      fence would otherwise pass green).
#   2) Every SVG asset referenced by either README (via <picture>/<img>/markdown
#      image syntax pointing at assets/*.svg) exists, is resolved relative to the
#      referencing README's own directory (falling back to the repo root), and
#      is marked data-look="handDrawn".
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

# --- 1) Fenced bash blocks: PT-BR must be a byte-identical whole-block subset -----
# of EN+INSTALL --------------------------------------------------------------------

# Extract every ```bash ... ``` block from a file. Emits, on stdout:
#   ###BLOCK_START:<line>###\n<raw block bytes>\n###BLOCK_END###\n  (per block found)
#   ###UNTERMINATED:<line>###                                       (if EOF hit mid-block)
#   ###OPENER_COUNT:<n>###                                          (always, last line)
# Indent- and backtick-count aware: an opener of N backticks (N>=3), optionally
# indented and carrying a trailing info string, requires a closer of >= N
# backticks at the same-or-looser indent. CRLF is normalized away first.
extract_bash_blocks() {
  awk '
    {
      line = $0
      sub(/\r$/, "", line)
    }
    inblock {
      if (match(line, /^[ \t]*`+[ \t]*$/)) {
        s = line
        match(s, /^[ \t]*/)
        rest = substr(s, RLENGTH + 1)
        match(rest, /^`+/)
        close_ticks = RLENGTH
        if (close_ticks >= open_ticks) {
          inblock = 0
          printf "###BLOCK_START:%d###\n", startline
          printf "%s", buf
          printf "###BLOCK_END###\n"
          next
        }
      }
      buf = buf line "\n"
      next
    }
    {
      if (match(line, /^[ \t]*```+bash([ \t].*)?$/)) {
        s = line
        match(s, /^[ \t]*/)
        rest = substr(s, RLENGTH + 1)
        match(rest, /^`+/)
        open_ticks = RLENGTH
        inblock = 1
        startline = NR + 1
        buf = ""
        opener_count++
      }
    }
    END {
      if (inblock) {
        printf "###UNTERMINATED:%d###\n", startline
      }
      printf "###OPENER_COUNT:%d###\n", opener_count + 0
    }
  ' "$1"
}

# Runs extract_bash_blocks on $1, writes each extracted block's raw bytes to its
# own file under WORKDIR (named with $2 as a per-call tag), and leaves the
# results in the globals PARSED_FILES, PARSED_LINES, PARSED_COUNT,
# PARSED_OPENER_COUNT, PARSED_UNTERMINATED for the caller to consume immediately.
parse_blocks() {
  local src="$1" tag="$2"
  PARSED_FILES=()
  PARSED_LINES=()
  PARSED_UNTERMINATED=""
  PARSED_OPENER_COUNT=0
  PARSED_COUNT=0
  local line block_start="" content="" in_block=0 outfile
  while IFS= read -r line; do
    if [[ "$line" =~ ^###BLOCK_START:([0-9]+)###$ ]]; then
      block_start="${BASH_REMATCH[1]}"
      content=""
      in_block=1
      continue
    fi
    if [ "$line" = "###BLOCK_END###" ]; then
      PARSED_COUNT=$((PARSED_COUNT + 1))
      outfile="$WORKDIR/block_${tag}_${PARSED_COUNT}"
      printf '%s' "$content" >"$outfile"
      PARSED_FILES+=("$outfile")
      PARSED_LINES+=("$block_start")
      in_block=0
      continue
    fi
    if [[ "$line" =~ ^###UNTERMINATED:([0-9]+)###$ ]]; then
      PARSED_UNTERMINATED="${BASH_REMATCH[1]}"
      continue
    fi
    if [[ "$line" =~ ^###OPENER_COUNT:([0-9]+)###$ ]]; then
      PARSED_OPENER_COUNT="${BASH_REMATCH[1]}"
      continue
    fi
    if [ "$in_block" -eq 1 ]; then
      content="${content}${line}"$'\n'
    fi
  done < <(extract_bash_blocks "$src")
}

# Runs parse_blocks for $1 and turns its PARSED_* globals into ERROR lines
# (unterminated fence / opener-vs-extracted-block mismatch). Sets `fail=1` on
# either. Leaves PARSED_* populated for the caller.
check_extraction_integrity() {
  local src="$1" tag="$2"
  parse_blocks "$src" "$tag"
  if [ -n "$PARSED_UNTERMINATED" ]; then
    echo "ERROR: $src:$PARSED_UNTERMINATED — \`\`\`bash fence opened but never closed (unterminated at EOF)"
    fail=1
  fi
  if [ "$PARSED_OPENER_COUNT" -ne "$PARSED_COUNT" ]; then
    echo "ERROR: $src — bash-fence opener/extracted-block count mismatch (openers=$PARSED_OPENER_COUNT extracted=$PARSED_COUNT); the extractor may be silently dropping a fence"
    fail=1
  fi
}

HAYSTACK_FILES=()

check_extraction_integrity "$README_EN" "en"
if [ "${#PARSED_FILES[@]}" -gt 0 ]; then
  HAYSTACK_FILES+=("${PARSED_FILES[@]}")
fi

if [ -f "$README_INSTALL" ]; then
  check_extraction_integrity "$README_INSTALL" "install"
  if [ "${#PARSED_FILES[@]}" -gt 0 ]; then
    HAYSTACK_FILES+=("${PARSED_FILES[@]}")
  fi
fi

check_extraction_integrity "$README_PT" "pt"
PT_FILES=()
PT_LINES=()
if [ "${#PARSED_FILES[@]}" -gt 0 ]; then
  PT_FILES=("${PARSED_FILES[@]}")
  PT_LINES=("${PARSED_LINES[@]}")
fi
pt_block_count="$PARSED_COUNT"

fence_fail=0
idx=0
while [ "$idx" -lt "$pt_block_count" ]; do
  needle_file="${PT_FILES[$idx]}"
  needle_line="${PT_LINES[$idx]}"
  matched=0
  if [ "${#HAYSTACK_FILES[@]}" -gt 0 ]; then
    for hay_file in "${HAYSTACK_FILES[@]}"; do
      if cmp -s "$needle_file" "$hay_file"; then
        matched=1
        break
      fi
    done
  fi
  if [ "$matched" -ne 1 ]; then
    echo "ERROR: $README_PT:$needle_line — bash fence not found byte-identically as a whole block in $README_EN or $README_INSTALL"
    fence_fail=1
  fi
  idx=$((idx + 1))
done

if [ "$fence_fail" -eq 1 ]; then
  fail=1
else
  echo "OK: all $pt_block_count $README_PT bash fence(s) matched byte-identically as whole blocks in $README_EN/$README_INSTALL"
fi

# --- 2) Referenced SVG assets exist and carry data-look="handDrawn" ----------------
SVG_ANY_REF=0
SVG_FAIL=0

check_svg_refs_in() {
  local src="$1" srcdir refs ref resolved
  srcdir="$(dirname "$src")"
  refs=$(grep -ohE 'assets/[A-Za-z0-9_./-]*\.svg' "$src" 2>/dev/null | sort -u)
  [ -z "$refs" ] && return 0
  while IFS= read -r ref; do
    [ -z "$ref" ] && continue
    SVG_ANY_REF=1
    resolved="$srcdir/$ref"
    if [ ! -f "$resolved" ]; then
      resolved="$ref"
    fi
    if [ ! -f "$resolved" ]; then
      echo "ERROR: referenced SVG asset '$ref' (from $src) does not exist"
      SVG_FAIL=1
      continue
    fi
    if ! grep -q 'data-look="handDrawn"' "$resolved"; then
      echo "ERROR: referenced SVG asset '$resolved' (from $src) exists but lacks data-look=\"handDrawn\""
      SVG_FAIL=1
    fi
  done <<<"$refs"
}

check_svg_refs_in "$README_EN"
check_svg_refs_in "$README_PT"

if [ "$SVG_ANY_REF" -eq 0 ]; then
  echo "OK: no SVG assets referenced by the README pair (vacuously green)"
elif [ "$SVG_FAIL" -eq 1 ]; then
  fail=1
else
  echo "OK: every referenced SVG asset exists and carries data-look=\"handDrawn\""
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
