#!/usr/bin/env bash
# desc: SessionStart — avisa se core@agent-kit não consta como instalado no registro de plugins (checa instalação, não enablement por sessão; fail-open em qualquer anomalia).
set -uo pipefail
command -v python3 >/dev/null 2>&1 || exit 0
REG="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/plugins/installed_plugins.json"
[ -f "$REG" ] || exit 0
python3 - "$REG" "${CLAUDE_PLUGIN_ROOT:-}" <<'PY'
import json, sys

# Limitação documentada: o registro diz o que está INSTALADO (qualquer escopo),
# não o que está habilitado nesta sessão. Entry project-scoped de outro projeto
# conta como presente (falso-silêncio aceito; falso-aviso é pior — meta-princípio
# advisory-nudge em docs/GOVERNANCE.md). Formato do registro é contrato interno
# do Claude Code ("version": 2 hoje) — qualquer forma inesperada = silêncio.
try:
    with open(sys.argv[1], encoding="utf-8") as f:
        entries = json.load(f).get("plugins", {}).get("core@agent-kit") or []
except Exception:
    sys.exit(0)
if entries:
    sys.exit(0)

plugin = "este plugin"
try:
    with open(sys.argv[2] + "/.claude-plugin/plugin.json", encoding="utf-8") as f:
        plugin = json.load(f).get("name", plugin)
except Exception:
    pass

print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
    "additionalContext": (
        f"[require-core] O plugin '{plugin}' assume as regras sempre-ativas e o "
        "pipeline do core@agent-kit, que não consta como instalado. Instale com: "
        "claude plugin install core@agent-kit"
    )}}))
PY
