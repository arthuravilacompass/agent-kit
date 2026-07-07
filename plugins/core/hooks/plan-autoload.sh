#!/usr/bin/env bash
# desc: SessionStart — injeta ponteiro de retomada quando existe plano recente (<72h).
# plan-autoload.sh — SessionStart hook
# Detects the most recently modified plan file across the canonical doc locations.
# Notifies user via stderr (visible in terminal before session starts).
# Injects only the relative path into additionalContext so Claude can act on "continue plan".
# User still decides: say "continue plan" to resume, or ignore to start fresh.
#
# Search locations (in priority order):
#   - docs/superpowers/plans/        (canonical plan location)
#   - docs/superpowers/handoffs/     (handoff documents — also resumable)
#   - docs/                          (runbooks, ad-hoc YYYY-MM-DD-*.md files)
#
# Time window: 72h (covers multi-day plans; 24h was too narrow for real workflow).

set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
DOCS_DIR="${PROJECT_DIR}/docs"

if [ ! -d "$DOCS_DIR" ]; then
    echo '{}'
    exit 0
fi

if ! command -v python3 &>/dev/null; then
    echo '{}'
    exit 0
fi

DOCS_DIR="$DOCS_DIR" PROJECT_DIR="$PROJECT_DIR" python3 << 'PYEOF'
import json, os, time, glob, sys

docs_dir = os.environ.get("DOCS_DIR", "")
project_dir = os.environ.get("PROJECT_DIR", "")
if not docs_dir:
    print('{}')
    sys.exit(0)

contexts = []

# ── Curadoria de memória: alerta acoplado a limiar ──
# MEMORY.md é always-on; acima de ~5k tokens (≈20k chars) vira o maior custo próprio.
# Localização segue a mesma convenção de sanitização do Claude Code para o diretório
# de projeto (~/.claude/projects/<path-com-/-trocado-por-->/memory/MEMORY.md) —
# nenhum path de workspace fica hardcoded aqui, é derivado de CLAUDE_PROJECT_DIR.
if project_dir:
    proj_key = os.path.normpath(os.path.abspath(project_dir)).replace(os.sep, "-")
    memory_index = os.path.expanduser(f"~/.claude/projects/{proj_key}/memory/MEMORY.md")
    try:
        idx_size = os.path.getsize(memory_index)
        if idx_size > 20_000:
            contexts.append(
                f"[memory-budget] MEMORY.md está em ~{idx_size // 4} tokens always-on (>5k). "
                "Quando houver folga na sessão, rode curadoria: mesclar duplicatas, arquivar entradas "
                "stale em memory/archive/, encurtar hooks verbosos do índice."
            )
    except OSError:
        pass

# Canonical locations for resumable docs (plans + handoffs at the top — root last)
search_dirs = [
    os.path.join(docs_dir, "superpowers", "plans"),
    os.path.join(docs_dir, "superpowers", "handoffs"),
    docs_dir,
]

pattern = "[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-*.md"
plan_files = []
for d in search_dirs:
    if os.path.isdir(d):
        plan_files.extend(glob.glob(os.path.join(d, pattern)))

def emit_and_exit():
    if contexts:
        print(json.dumps({"additionalContext": "\n\n".join(contexts)}))
    else:
        print('{}')
    sys.exit(0)

if not plan_files:
    emit_and_exit()

# Sort by modification time, most recent first
plan_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
latest = plan_files[0]
mtime = os.path.getmtime(latest)
age_hours = (time.time() - mtime) / 3600

# Window: 72h. Multi-day plans (typical for iterative work) survive past 24h.
if age_hours > 72:
    emit_and_exit()

rel_path = os.path.relpath(latest, docs_dir)
age_str = f"{int(age_hours)}h ago" if age_hours >= 1 else f"{int(age_hours * 60)}m ago"

# Notify user via stderr — they see this and decide
print(f"\n[plan-autoload] Plan encontrado / found: docs/{rel_path} ({age_str})\n  → Diga \"continuar plano\" ou \"continue plan\" para retomar, ou ignore para começar do zero.\n", file=sys.stderr)

# Inject relative path into Claude's context so it can act if user says "continue plan" / "continuar plano"
contexts.append(f'[plan-autoload] If the user says "continue plan" or "continuar plano", read `docs/{rel_path}` and resume from the last incomplete step.')
emit_and_exit()
PYEOF

exit 0
