#!/usr/bin/env python3
# desc: Gera INVENTORY.md determinístico na raiz do repo a partir dos manifests dos plugins.
"""generate_inventory.py — gera INVENTORY.md na raiz do repo a partir de:
  - plugins/*/skills/*/SKILL.md   (frontmatter: name, description, disable-model-invocation)
  - plugins/*/agents/*.md         (frontmatter: name, description)
  - plugins/*/hooks/hooks.json    (evento, matcher, script) + a linha `# desc:` do script
  - plugins/*/scripts/*           (nome do arquivo) + a linha `# desc:` do script
  - plugins/mobile/.mcp.json      (nome do server + command)

Stdlib puro (sem PyYAML) — o parse de frontmatter é manual e restrito a linhas
`key: valor-em-uma-linha`; qualquer estrutura YAML inesperada (multiline, indentação,
chave duplicada) faz o script falhar alto (exit != 0), nunca silenciosamente.

Determinismo: toda enumeração de diretório usa sorted(); nenhum timestamp/data entra
no output; paths são repo-relativos; escrita sempre com '\n' e encoding utf-8. Isso
garante output byte-idêntico entre execuções para a mesma árvore de arquivos.

Uso:
  python3 scripts/generate_inventory.py            # escreve INVENTORY.md
  python3 scripts/generate_inventory.py --check    # compara com o disco; exit 0 se
                                                     # idêntico, exit 1 (com diff resumido)
                                                     # se divergente ou ausente.
"""

import difflib
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGINS = ["core", "mobile"]
INVENTORY_PATH = os.path.join(REPO_ROOT, "INVENTORY.md")

GENERATED_BANNER = (
    "<!-- GERADO por scripts/generate_inventory.py — não editar à mão. "
    "Regenerar: python3 scripts/generate_inventory.py -->"
)

FRONTMATTER_KEY_RE = re.compile(r"^([A-Za-z0-9_-]+):\s?(.*)$")
COMMAND_PATH_RE = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/(.+)$")
DESC_LINE_RE = re.compile(r"^#\s*desc:\s*(.+)$")

GOVERNANCE_PATH = os.path.join(REPO_ROOT, "docs", "GOVERNANCE.md")
PROVISIONAL_LINE_RE = re.compile(r"^- `([^`]+)` — valida até (\d{4}-\d{2}-\d{2})$")


def collect_provisional():
    """path relativo -> deadline, da seção '### Provisórios ativos' de docs/GOVERNANCE.md."""
    if not os.path.isfile(GOVERNANCE_PATH):
        return {}
    result = {}
    in_section = False
    with open(GOVERNANCE_PATH, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if line.startswith("### Provisórios ativos"):
                in_section = True
                continue
            if in_section and (line.startswith("## ") or line.startswith("### ")):
                break
            if in_section:
                m = PROVISIONAL_LINE_RE.match(line)
                if m:
                    if m.group(1) in result:
                        raise InventoryError(
                            f"docs/GOVERNANCE.md: provisório duplicado '{m.group(1)}'"
                        )
                    result[m.group(1)] = m.group(2)
    return result


class InventoryError(Exception):
    """Raised on any structural problem in a source file — always fatal, never silent."""


def rel(path):
    return os.path.relpath(path, REPO_ROOT).replace(os.sep, "/")


def esc(cell):
    """Escape a markdown table cell: '|' -> '\\|', newline -> space."""
    if cell is None:
        cell = ""
    return cell.replace("\n", " ").replace("|", "\\|")


def parse_frontmatter(path):
    """Restricted manual parse of a `---`-delimited frontmatter block.

    Only accepts top-level, single-line `key: value` entries. Any indented line,
    any line that doesn't match `key: value`, or any duplicate key is treated as
    unexpected YAML structure and raises InventoryError.
    """
    with open(path, encoding="utf-8") as f:
        text = f.read()
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        raise InventoryError(f"{rel(path)}: frontmatter deve começar com '---' na primeira linha")
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        raise InventoryError(f"{rel(path)}: frontmatter sem '---' de fechamento")

    result = {}
    for lineno, raw in enumerate(lines[1:end], start=2):
        if not raw.strip():
            continue
        if raw[0] in (" ", "\t"):
            raise InventoryError(
                f"{rel(path)}:{lineno}: linha de frontmatter indentada — valor multiline ou "
                f"estrutura YAML inesperada não suportada pelo parse manual: {raw!r}"
            )
        m = FRONTMATTER_KEY_RE.match(raw)
        if not m:
            raise InventoryError(
                f"{rel(path)}:{lineno}: linha de frontmatter não é 'key: valor': {raw!r}"
            )
        key, val = m.group(1), m.group(2).strip()
        if key in result:
            raise InventoryError(f"{rel(path)}:{lineno}: chave de frontmatter duplicada '{key}'")
        result[key] = val
    return result


def get_desc_line(script_path):
    """Read the mandatory `# desc: ...` header, which must be line 2 of the file."""
    with open(script_path, encoding="utf-8") as f:
        lines = f.readlines()
    if len(lines) < 2:
        raise InventoryError(f"{rel(script_path)}: arquivo sem linha 2 (esperava '# desc: ...')")
    line2 = lines[1].rstrip("\n")
    m = DESC_LINE_RE.match(line2.strip())
    if not m:
        raise InventoryError(
            f"{rel(script_path)}: linha 2 não é '# desc: ...' — encontrado: {line2!r}"
        )
    return m.group(1).strip()


def collect_skills(plugin, provisional):
    skills_dir = os.path.join(REPO_ROOT, "plugins", plugin, "skills")
    result = []
    if not os.path.isdir(skills_dir):
        return result
    for name in sorted(os.listdir(skills_dir)):
        skill_md = os.path.join(skills_dir, name, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue
        fm = parse_frontmatter(skill_md)
        if "name" not in fm:
            raise InventoryError(f"{rel(skill_md)}: frontmatter sem 'name'")
        if "description" not in fm:
            raise InventoryError(f"{rel(skill_md)}: frontmatter sem 'description'")
        slash_only = fm.get("disable-model-invocation", "").strip().lower() == "true"
        key = f"plugins/{plugin}/skills/{name}"
        deadline = provisional.pop(key, None)
        result.append(
            {
                "name": fm["name"],
                "description": fm["description"],
                "slash_only": slash_only,
                "provisional_until": deadline,
            }
        )
    return result


def collect_agents(plugin, provisional):
    agents_dir = os.path.join(REPO_ROOT, "plugins", plugin, "agents")
    result = []
    if not os.path.isdir(agents_dir):
        return result
    for fname in sorted(os.listdir(agents_dir)):
        if not fname.endswith(".md"):
            continue
        agent_md = os.path.join(agents_dir, fname)
        fm = parse_frontmatter(agent_md)
        if "name" not in fm:
            raise InventoryError(f"{rel(agent_md)}: frontmatter sem 'name'")
        if "description" not in fm:
            raise InventoryError(f"{rel(agent_md)}: frontmatter sem 'description'")
        key = f"plugins/{plugin}/agents/{fname}"
        deadline = provisional.pop(key, None)
        result.append(
            {
                "name": fm["name"],
                "description": fm["description"],
                "provisional_until": deadline,
            }
        )
    return result


def resolve_hook_script_path(plugin, command):
    """Extract the on-disk script path referenced by a hooks.json command string."""
    stripped = command.strip()
    if stripped.startswith('"') and stripped.endswith('"'):
        stripped = stripped[1:-1]
    m = COMMAND_PATH_RE.search(stripped)
    if not m:
        raise InventoryError(
            f"plugins/{plugin}/hooks/hooks.json: command não segue o padrão "
            f'"${{CLAUDE_PLUGIN_ROOT}}/...": {command!r}'
        )
    return os.path.join(REPO_ROOT, "plugins", plugin, m.group(1))


def collect_hooks(plugin):
    hooks_json = os.path.join(REPO_ROOT, "plugins", plugin, "hooks", "hooks.json")
    result = []
    if not os.path.isfile(hooks_json):
        return result
    with open(hooks_json, encoding="utf-8") as f:
        data = json.load(f)
    for event, entries in data.get("hooks", {}).items():
        for entry in entries:
            matcher = entry.get("matcher", "")
            for hook in entry.get("hooks", []):
                command = hook.get("command", "")
                script_path = resolve_hook_script_path(plugin, command)
                if not os.path.isfile(script_path):
                    raise InventoryError(
                        f"plugins/{plugin}/hooks/hooks.json: script referenciado não existe: "
                        f"{rel(script_path)}"
                    )
                desc = get_desc_line(script_path)
                result.append(
                    {
                        "hook": os.path.basename(script_path),
                        "event": event,
                        "matcher": matcher,
                        "description": desc,
                    }
                )
    return result


def collect_scripts(plugin):
    scripts_dir = os.path.join(REPO_ROOT, "plugins", plugin, "scripts")
    result = []
    if not os.path.isdir(scripts_dir):
        return result
    for name in sorted(os.listdir(scripts_dir)):
        script_path = os.path.join(scripts_dir, name)
        if not os.path.isfile(script_path):
            continue
        desc = get_desc_line(script_path)
        result.append({"name": name, "description": desc})
    return result


def collect_mcp(plugin):
    mcp_path = os.path.join(REPO_ROOT, "plugins", plugin, ".mcp.json")
    result = []
    if not os.path.isfile(mcp_path):
        return result
    with open(mcp_path, encoding="utf-8") as f:
        data = json.load(f)
    servers = data.get("mcpServers", {})
    for name in sorted(servers.keys()):
        server = servers[name]
        result.append({"name": name, "command": server.get("command", "")})
    return result


def render_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(esc(c) for c in row) + " |")
    return lines


def render_plugin_section(plugin, provisional):
    lines = [f"## Plugin `{plugin}`", ""]

    skills = collect_skills(plugin, provisional)
    lines.append(f"### Skills ({len(skills)})")
    lines.append("")
    rows = []
    for s in skills:
        if s["slash_only"]:
            name_cell = f"`{s['name']}` (slash-only: `/{plugin}:{s['name']}`)"
        else:
            name_cell = f"`{s['name']}`"
        if s.get("provisional_until"):
            name_cell += f" ⏳ provisório até {s['provisional_until']}"
        rows.append([name_cell, s["description"]])
    lines.extend(render_table(["Skill", "Descrição"], rows))
    lines.append("")

    agents = collect_agents(plugin, provisional)
    lines.append(f"### Agents ({len(agents)})")
    lines.append("")
    rows = []
    for a in agents:
        name_cell = f"`{a['name']}`"
        if a.get("provisional_until"):
            name_cell += f" ⏳ provisório até {a['provisional_until']}"
        rows.append([name_cell, a["description"]])
    lines.extend(render_table(["Agent", "Descrição"], rows))
    lines.append("")

    hooks = collect_hooks(plugin)
    lines.append(f"### Hooks ({len(hooks)})")
    lines.append("")
    rows = [[f"`{h['hook']}`", h["event"], h["matcher"], h["description"]] for h in hooks]
    lines.extend(render_table(["Hook", "Evento", "Matcher", "Descrição"], rows))
    lines.append("")

    scripts = collect_scripts(plugin)
    lines.append(f"### Scripts ({len(scripts)})")
    lines.append("")
    rows = [[f"`{s['name']}`", s["description"]] for s in scripts]
    lines.extend(render_table(["Script", "Descrição"], rows))
    lines.append("")

    if plugin == "mobile":
        mcp = collect_mcp(plugin)
        lines.append(f"### MCP ({len(mcp)})")
        lines.append("")
        rows = [[f"`{m['name']}`", f"`{m['command']}`"] for m in mcp]
        lines.extend(render_table(["Server", "Command"], rows))
        lines.append("")

    return lines


def generate():
    lines = [
        GENERATED_BANNER,
        "# Inventário do agent-kit",
        "",
        "Gerado automaticamente a partir dos manifests dos plugins (`SKILL.md`, agents, "
        "`hooks.json`, scripts e `.mcp.json`) — não editar à mão; regenerar com "
        "`python3 scripts/generate_inventory.py`.",
        "",
        "Skills marcadas **slash-only** têm `disable-model-invocation: true` no frontmatter: "
        "rodam só via comando explícito (`/core:<nome>`, `/mobile:<nome>`), nunca por "
        "iniciativa do modelo.",
        "",
        "Itens com “provisório até <data>” estão wired sob a exceção de deadline "
        "(`docs/GOVERNANCE.md` §Provisórios ativos) — prazo vencido deixa o gate vermelho.",
        "",
        "---",
        "",
    ]
    provisional = collect_provisional()
    for i, plugin in enumerate(PLUGINS):
        lines.extend(render_plugin_section(plugin, provisional))
        if i < len(PLUGINS) - 1:
            lines.append("---")
            lines.append("")
    if provisional:
        raise InventoryError(
            "provisórios em docs/GOVERNANCE.md sem artefato correspondente: "
            + ", ".join(sorted(provisional))
        )
    # single trailing newline
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def main():
    check_mode = "--check" in sys.argv[1:]
    try:
        content = generate()
    except InventoryError as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 1

    if check_mode:
        if not os.path.isfile(INVENTORY_PATH):
            print("ERRO: INVENTORY.md não existe — rode sem --check para gerar.", file=sys.stderr)
            return 1
        with open(INVENTORY_PATH, encoding="utf-8") as f:
            disk_content = f.read()
        if disk_content == content:
            print("OK: INVENTORY.md está atualizado.")
            return 0
        diff = difflib.unified_diff(
            disk_content.splitlines(keepends=True),
            content.splitlines(keepends=True),
            fromfile="INVENTORY.md (disco)",
            tofile="INVENTORY.md (gerado)",
        )
        diff_text = "".join(diff)
        max_chars = 4000
        if len(diff_text) > max_chars:
            diff_text = diff_text[:max_chars] + "\n... (diff truncado)"
        print("FALHOU: INVENTORY.md está desatualizado.\n", file=sys.stderr)
        print(diff_text, file=sys.stderr)
        return 1

    with open(INVENTORY_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"OK: {rel(INVENTORY_PATH)} gerado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
