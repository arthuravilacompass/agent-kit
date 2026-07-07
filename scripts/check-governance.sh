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

# 3) Contrato de SKILL.md (D14): todo arquivo na §Conformidade existe e respeita o teto de linhas
CONTRACT="docs/SKILL-CONTRACT.md"
MAX_LINES=120
if [ ! -f "$CONTRACT" ]; then
  echo "ERRO: ${CONTRACT} ausente — conformidade D14 não verificada"
  fail=1
else
  # shellcheck disable=SC2016  # crase e '$' são literais do padrão sed/grep, não expansão
  paths=$(sed -n '/^## Conformidade/,$p' "$CONTRACT" | grep -oE '\`plugins/[^\`]+\`' | tr -d '\`')
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

# 5) Provisórios (D17): prazo vencido = gate vermelho até validar ou demover
# shellcheck disable=SC2016  # '$' é a ancora de fim-de-linha do regex, não expansão
prov=$(sed -n '/^### Provisórios ativos/,/^## /p' "$LEDGER" \
  | grep -E '^- `[^`]+` — valida até [0-9]{4}-[0-9]{2}-[0-9]{2}$' || true)
if [ -z "$prov" ]; then
  echo "OK: nenhum item provisório ativo"
else
  today=$(date +%F)
  expired=0
  while IFS= read -r line; do
    # shellcheck disable=SC2016  # crase é literal do padrão grep, não expansão
    path=$(echo "$line" | grep -oE '`[^`]+`' | tr -d '`')
    deadline=$(echo "$line" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}')
    if [ ! -e "$path" ]; then
      echo "ERRO: provisório ${path} listado em ${LEDGER} não existe no disco (D17)"
      fail=1
    fi
    if [[ "$today" > "$deadline" ]]; then
      echo "ERRO: provisório ${path} venceu em ${deadline} — validar por uso ou demover (D17)"
      fail=1; expired=1
    fi
  done <<< "$prov"
  if [ "$expired" -eq 0 ]; then
    echo "OK: provisórios dentro do prazo ($(echo "$prov" | wc -l | tr -d ' ') itens, D17)"
  fi
fi

exit $fail
