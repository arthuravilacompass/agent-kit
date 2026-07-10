#!/usr/bin/env bash
# desc: Governance gate — always-on tier byte ceiling + resolution of every D*/R* ID cited against docs/GOVERNANCE.md's ledger + SKILL.md contract (D14).
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

CEILING=16384
LEDGER="docs/GOVERNANCE.md"
fail=0

# 1) Always-on ceiling: session-start.sh's actual output (full JSON)
out=$(CLAUDE_PLUGIN_ROOT="plugins/core" bash plugins/core/hooks/session-start.sh 2>&1)
rc=$?
if [ "$rc" -ne 0 ]; then
  echo "ERROR: session-start.sh failed (rc=$rc) — ceiling not measured"
  echo "$out" | head -5
  fail=1
else
  bytes=$(printf '%s' "$out" | wc -c | tr -d ' ')
  if [ "$bytes" -gt "$CEILING" ]; then
    echo "ERROR: always-on tier measures ${bytes} bytes — over the ${CEILING}-byte ceiling (docs/GOVERNANCE.md §Always-on tier ceiling)"
    fail=1
  else
    echo "OK: always-on tier ${bytes} bytes <= ceiling ${CEILING}"
  fi
fi

# 2) Every D*/R* ID cited in the repo resolves in the ledger
# git grep -E doesn't support \b — use the system grep, same pattern as
# check-provenance.sh (no xargs: robust to filenames with spaces, checkable rc).
# superpowers/.superpowers is build residue, out of the census's scope.
# .worktrees is another branch's isolated workspace (gitignored), with its own ledger —
# its IDs don't resolve in the current branch's ledger and aren't a deliverable of it.
# 'R8' matches Android's R8/ProGuard shrinker (cited in apk-archaeology/references/method.md),
# not a governance ID — filter it out to avoid a false ledger miss. A principled census
# disambiguation (match IDs only in citation context) is deferred to the process audit;
# this narrow exclusion is the minimal source fix.
ids=$(grep -rhoE --include='*.md' --exclude-dir=superpowers --exclude-dir=.superpowers --exclude-dir=.worktrees \
  '\b[DR][0-9]+\b' . | sort -u | grep -vxF 'R8')
rc=$?
if [ "$rc" -ge 2 ]; then
  echo "ERROR: ID census failed (rc=$rc) — ledger resolution not verified"
  fail=1
elif [ -z "$ids" ]; then
  echo "OK: no D*/R* ID cited in the repo"
else
  missing=0
  for id in $ids; do
    if ! grep -qE "^- \*\*${id}\*\*" "$LEDGER"; then
      echo "ERROR: ID ${id} cited in the repo without an entry in the ledger (${LEDGER})"
      fail=1
      missing=1
    fi
  done
  if [ "$missing" -eq 0 ]; then
    echo "OK: every cited ID resolves in the ledger ($(echo "$ids" | tr '\n' ' '))"
  fi
fi

# 3) SKILL.md contract (D14, GOVERNANCE's §SKILL.md contract): every file
# in §Conformity exists and respects the line ceiling
CONTRACT="docs/GOVERNANCE.md"
MAX_LINES=120
if [ ! -f "$CONTRACT" ]; then
  echo "ERROR: ${CONTRACT} missing — D14 conformity not verified"
  fail=1
else
  # shellcheck disable=SC2016  # backtick and '$' are literal pattern chars for sed/grep, not expansion
  # Backtick UNESCAPED: in GNU grep -E, '\`' is a start-of-buffer anchor (GNU
  # extension) and the pattern never matches — that's what turned the gate red on CI (ubuntu)
  # while the local BSD grep treated '\`' as a literal backtick.
  paths=$(sed -n '/^### Conformity/,/^## /p' "$CONTRACT" | grep -oE '`plugins/[^`]+`' | tr -d '`')
  if [ -z "$paths" ]; then
    echo "ERROR: §Conformity empty or unreadable in ${CONTRACT} (D14)"
    fail=1
  else
    d14_ok=1
    while IFS= read -r p; do
      [ -z "$p" ] && continue
      if [ ! -f "$p" ]; then
        echo "ERROR: ${p} listed in §Conformity does not exist (D14)"
        fail=1; d14_ok=0
      else
        lines=$(wc -l < "$p" | tr -d ' ')
        if [ "$lines" -gt "$MAX_LINES" ]; then
          echo "ERROR: ${p} has ${lines} lines — over the ${MAX_LINES}-line ceiling (D14)"
          fail=1; d14_ok=0
        fi
      fi
    done <<< "$paths"
    if [ "$d14_ok" -eq 1 ]; then
      echo "OK: D14 conformity ($(echo "$paths" | wc -l | tr -d ' ') files <= ${MAX_LINES} lines)"
    fi
  fi
fi

# 4) D14 prohibition: provenance narration in plugins/ (mechanizable marker)
hits=$(grep -rIn 'Promoted from' plugins/ 2>/dev/null)
if [ -n "$hits" ]; then
  echo "ERROR: provenance narration in plugins/ (D14 §Prohibitions):"
  echo "$hits"
  fail=1
else
  echo "OK: zero provenance narration ('Promoted from') in plugins/"
fi

# 5) Provisionals (D17): missed deadline, malformed entry, or invalid date =
# red gate — fail-loud, never silently ignored.
# shellcheck disable=SC2016  # '$' is the regex end-of-line anchor, not expansion
section=$(sed -n '/^### Active provisionals/,/^##\{1,2\} /p' "$LEDGER")
# shellcheck disable=SC2016  # backtick is a literal grep pattern char, not expansion
entries=$(printf '%s\n' "$section" | grep -E '^- `' || true)
# shellcheck disable=SC2016  # backtick and '$' are literal grep pattern chars, not expansion
prov=$(printf '%s\n' "$section" | grep -E '^- `[^`]+` — valid until [0-9]{4}-[0-9]{2}-[0-9]{2}$' || true)
problem=0
if [ -n "$entries" ]; then
  # shellcheck disable=SC2016  # backtick and '$' are literal grep pattern chars, not expansion
  malformed=$(printf '%s\n' "$entries" | grep -vE '^- `[^`]+` — valid until [0-9]{4}-[0-9]{2}-[0-9]{2}$' || true)
  if [ -n "$malformed" ]; then
    while IFS= read -r line; do
      [ -z "$line" ] && continue
      echo "ERROR: malformed provisional line in docs/GOVERNANCE.md: ${line}"
      fail=1; problem=1
    done <<< "$malformed"
  fi
fi
if [ -z "$entries" ]; then
  echo "OK: no active provisional item"
elif [ -n "$prov" ]; then
  today=$(date +%F)
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    # shellcheck disable=SC2016  # backtick is a literal grep pattern char, not expansion
    path=$(echo "$line" | grep -oE '`[^`]+`' | tr -d '`')
    deadline=$(echo "$line" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}')
    if ! python3 -c 'import datetime,sys; datetime.date.fromisoformat(sys.argv[1])' "$deadline" 2>/dev/null; then
      echo "ERROR: invalid provisional date: $deadline (docs/GOVERNANCE.md, D17)"
      fail=1; problem=1
      continue
    fi
    if [ ! -e "$path" ]; then
      echo "ERROR: provisional ${path} listed in ${LEDGER} does not exist on disk (D17)"
      fail=1; problem=1
    fi
    if [[ "$today" > "$deadline" ]]; then
      echo "ERROR: provisional ${path} expired on ${deadline} — validate by use or demote (D17)"
      fail=1; problem=1
    fi
  done <<< "$prov"
  if [ "$problem" -eq 0 ]; then
    echo "OK: provisionals within deadline ($(echo "$prov" | wc -l | tr -d ' ') items, D17)"
  fi
fi

# 6) Descriptions (D16): per-skill ceiling (350; router 700) + per-plugin aggregate.
# council exempt until the census (docs/GOVERNANCE.md §Descriptions). Ceilings hardcoded
# here, doc as source — same pattern as the always-on tier's CEILING.
if python3 - <<'PYEOF'
import os, re, sys

CEIL_DEFAULT, CEIL_ROUTER = 350, 700
ROUTERS = {"pipeline", "methodology", "mobx"}
AGG = {"core": 4096, "team": 1024, "mobile": 3584}
fail = 0
for plugin, agg_ceil in AGG.items():
    base = os.path.join("plugins", plugin, "skills")
    if not os.path.isdir(base):
        print(f"ERROR: {base} does not exist — D16 not measured")
        fail = 1
        continue
    total = 0
    for name in sorted(os.listdir(base)):
        p = os.path.join(base, name, "SKILL.md")
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8") as f:
            text = f.read()
        # description lives in the frontmatter (delimited by the first two '---');
        # restricting the search avoids matching 'description:' in a skill's body.
        parts = text.split("\n---", 2)
        fm = parts[0] + ("\n---" if len(parts) > 1 else "")
        m = re.search(r"^description: (.*)$", fm, re.M)
        if not m:
            print(f"ERROR: {p} has no 'description:' in the frontmatter (D16)")
            fail = 1
            continue
        n = len(m.group(1).encode("utf-8"))
        total += n
        ceil = CEIL_ROUTER if name in ROUTERS else CEIL_DEFAULT
        if n > ceil:
            print(f"ERROR: {plugin}:{name}'s description measures {n} bytes — ceiling {ceil} (D16)")
            fail = 1
    if total > agg_ceil:
        print(f"ERROR: {plugin}'s description aggregate measures {total} bytes — ceiling {agg_ceil} (D16)")
        fail = 1
    else:
        print(f"OK: {plugin} descriptions — aggregate {total} <= {agg_ceil} bytes (D16)")
sys.exit(fail)
PYEOF
then :; else fail=1; fi

exit $fail
