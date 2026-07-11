#!/usr/bin/env bash
# Hygiene gate: no content from the origin domain/company in the kit (including unwired/).
# Scans ONLY git-tracked files — gitignored and untracked paths (e.g. .claude/settings.local.json,
# docs/superpowers/, .worktrees/) never reach a commit, so flagging them is a false positive.
# Exit: 0 = clean · 1 = provenance content found · >=2 = grep aborted (indeterminate).
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
DENY='TF-[0-9]{3,}|TF-\\d|BM-[0-9]+|ID-[0-9]{6}|tfsports|tf\.com\.br|[Bb]usinessmap|TFTokens|TFC Market|TF Mall|squad-produtos|[Bb]itrise|release_26|snapshot/26|tf-[a-z]+-mobile|tf-mobile-workspace|arthuravila'

# Fail CLOSED if git can't enumerate the tree: a broken/absent git must be indeterminate,
# never reported clean — the original grep-based gate kept that contract (">=2 = indeterminate").
# The guard is a separate preflight (not the exit code of a NUL-producing command substitution,
# which bash mangles): $(git ls-files -z) strips NUL bytes and is unreliable on bash 3.2.
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: not a git work tree (git absent/broken) — indeterminate, do NOT treat as clean" >&2
  exit 2
fi

# Enumerate tracked files, NUL-safe, excluding this gate itself (it holds the DENY patterns).
# Process substitution (not $()) so NUL delimiters survive; read -d '' loop for bash 3.2.
files=()
while IFS= read -r -d '' f; do files+=("$f"); done \
  < <(git ls-files -z ':!:scripts/check-provenance.sh')

if [ "${#files[@]}" -eq 0 ]; then
  # An empty tracked-file set in this repo is itself suspect (broken checkout) — not clean.
  echo "ERROR: no tracked files found — indeterminate, do NOT treat as clean" >&2
  exit 2
fi

grep -InE "$DENY" "${files[@]}"
rc=$?
if [ "$rc" -eq 0 ]; then
  echo "FAILED: provenance content found (above)"
  exit 1
elif [ "$rc" -ge 2 ]; then
  echo "ERROR: grep aborted (exit $rc) — indeterminate result, do NOT treat as clean"
  exit "$rc"
fi
echo "OK: zero provenance content"
