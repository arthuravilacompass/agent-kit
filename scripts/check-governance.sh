#!/usr/bin/env bash
# desc: Gate de governança — teto de bytes do tier sempre-ativo + resolução de todo ID D*/R* citado no ledger de docs/GOVERNANCE.md + contrato de SKILL.md (D14).
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

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

# 3) Contrato de SKILL.md (D14, §Contrato de SKILL.md do GOVERNANCE): todo arquivo
# na §Conformidade existe e respeita o teto de linhas
CONTRACT="docs/GOVERNANCE.md"
MAX_LINES=120
if [ ! -f "$CONTRACT" ]; then
  echo "ERRO: ${CONTRACT} ausente — conformidade D14 não verificada"
  fail=1
else
  # shellcheck disable=SC2016  # crase e '$' são literais do padrão sed/grep, não expansão
  # Crase SEM escape: em GNU grep -E, '\`' é âncora de início de buffer (extensão
  # GNU) e o padrão nunca casa — foi o que deixou o gate vermelho no CI (ubuntu)
  # enquanto o BSD grep local tratava '\`' como crase literal.
  paths=$(sed -n '/^### Conformidade/,/^## /p' "$CONTRACT" | grep -oE '`plugins/[^`]+`' | tr -d '`')
  if [ -z "$paths" ]; then
    echo "ERRO: §Conformidade vazia ou ilegível em ${CONTRACT} (D14)"
    fail=1
  else
    d14_ok=1
    while IFS= read -r p; do
      [ -z "$p" ] && continue
      if [ ! -f "$p" ]; then
        echo "ERRO: ${p} listado na §Conformidade não existe (D14)"
        fail=1; d14_ok=0
      else
        lines=$(wc -l < "$p" | tr -d ' ')
        if [ "$lines" -gt "$MAX_LINES" ]; then
          echo "ERRO: ${p} tem ${lines} linhas — acima do teto de ${MAX_LINES} (D14)"
          fail=1; d14_ok=0
        fi
      fi
    done <<< "$paths"
    if [ "$d14_ok" -eq 1 ]; then
      echo "OK: conformidade D14 ($(echo "$paths" | wc -l | tr -d ' ') arquivos <= ${MAX_LINES} linhas)"
    fi
  fi
fi

# 4) Proibição D14: narração de proveniência em plugins/ (marcador mecanizável)
hits=$(grep -rIn 'Promovido de' plugins/ 2>/dev/null)
if [ -n "$hits" ]; then
  echo "ERRO: narração de proveniência em plugins/ (D14 §Proibições):"
  echo "$hits"
  fail=1
else
  echo "OK: zero narração de proveniência ('Promovido de') em plugins/"
fi

# 5) Provisórios (D17): prazo vencido, entrada malformada ou data inválida =
# gate vermelho — fail-loud, nunca silenciosamente ignorado.
# shellcheck disable=SC2016  # '$' é a ancora de fim-de-linha do regex, não expansão
section=$(sed -n '/^### Provisórios ativos/,/^##\{1,2\} /p' "$LEDGER")
# shellcheck disable=SC2016  # crase é literal do padrão grep, não expansão
entries=$(printf '%s\n' "$section" | grep -E '^- `' || true)
# shellcheck disable=SC2016  # crase e '$' são literais do padrão grep, não expansão
prov=$(printf '%s\n' "$section" | grep -E '^- `[^`]+` — valida até [0-9]{4}-[0-9]{2}-[0-9]{2}$' || true)
problem=0
if [ -n "$entries" ]; then
  # shellcheck disable=SC2016  # crase e '$' são literais do padrão grep, não expansão
  malformed=$(printf '%s\n' "$entries" | grep -vE '^- `[^`]+` — valida até [0-9]{4}-[0-9]{2}-[0-9]{2}$' || true)
  if [ -n "$malformed" ]; then
    while IFS= read -r line; do
      [ -z "$line" ] && continue
      echo "ERRO: linha de provisório malformada em docs/GOVERNANCE.md: ${line}"
      fail=1; problem=1
    done <<< "$malformed"
  fi
fi
if [ -z "$entries" ]; then
  echo "OK: nenhum item provisório ativo"
elif [ -n "$prov" ]; then
  today=$(date +%F)
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    # shellcheck disable=SC2016  # crase é literal do padrão grep, não expansão
    path=$(echo "$line" | grep -oE '`[^`]+`' | tr -d '`')
    deadline=$(echo "$line" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}')
    if ! python3 -c 'import datetime,sys; datetime.date.fromisoformat(sys.argv[1])' "$deadline" 2>/dev/null; then
      echo "ERRO: data de provisório inválida: $deadline (docs/GOVERNANCE.md, D17)"
      fail=1; problem=1
      continue
    fi
    if [ ! -e "$path" ]; then
      echo "ERRO: provisório ${path} listado em ${LEDGER} não existe no disco (D17)"
      fail=1; problem=1
    fi
    if [[ "$today" > "$deadline" ]]; then
      echo "ERRO: provisório ${path} venceu em ${deadline} — validar por uso ou demover (D17)"
      fail=1; problem=1
    fi
  done <<< "$prov"
  if [ "$problem" -eq 0 ]; then
    echo "OK: provisórios dentro do prazo ($(echo "$prov" | wc -l | tr -d ' ') itens, D17)"
  fi
fi

# 6) Descriptions (D16): teto por skill (350; roteador 700) + agregado por plugin.
# council isento até o censo (docs/GOVERNANCE.md §Descriptions). Tetos hardcoded
# aqui, doc como fonte — mesmo padrão do CEILING do sempre-ativo.
if python3 - <<'PYEOF'
import os, re, sys

CEIL_DEFAULT, CEIL_ROUTER = 350, 700
ROUTERS = {"pipeline", "methodology", "mobx"}
AGG = {"core": 4096, "team": 1024, "mobile": 3584}
fail = 0
for plugin, agg_ceil in AGG.items():
    base = os.path.join("plugins", plugin, "skills")
    if not os.path.isdir(base):
        print(f"ERRO: {base} inexistente — D16 não medido")
        fail = 1
        continue
    total = 0
    for name in sorted(os.listdir(base)):
        p = os.path.join(base, name, "SKILL.md")
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8") as f:
            text = f.read()
        # description vive no frontmatter (delimitado pelos dois primeiros '---');
        # restringir a busca evita casar 'description:' em corpo de skill.
        parts = text.split("\n---", 2)
        fm = parts[0] + ("\n---" if len(parts) > 1 else "")
        m = re.search(r"^description: (.*)$", fm, re.M)
        if not m:
            print(f"ERRO: {p} sem 'description:' no frontmatter (D16)")
            fail = 1
            continue
        n = len(m.group(1).encode("utf-8"))
        total += n
        ceil = CEIL_ROUTER if name in ROUTERS else CEIL_DEFAULT
        if n > ceil:
            print(f"ERRO: description de {plugin}:{name} mede {n} bytes — teto {ceil} (D16)")
            fail = 1
    if total > agg_ceil:
        print(f"ERRO: agregado de descriptions de {plugin} mede {total} bytes — teto {agg_ceil} (D16)")
        fail = 1
    else:
        print(f"OK: descriptions de {plugin} — agregado {total} <= {agg_ceil} bytes (D16)")
sys.exit(fail)
PYEOF
then :; else fail=1; fi

exit $fail
