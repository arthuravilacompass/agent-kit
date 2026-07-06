#!/usr/bin/env python3
"""
Claude Code Token Usage Analyzer
Identifies per-turn and on-demand token cost for each component in your setup.

Usage:
    python3 scripts/analyze_tokens.py [workspace_path] [--verbose]

    --verbose   Also show disabled plugins (greyed out) and their would-be cost

Optional dependency (more accurate counts):
    pip install tiktoken
"""

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# ── Token counter ────────────────────────────────────────────────────────────
try:
    import tiktoken

    _enc = tiktoken.get_encoding("cl100k_base")

    def count_tokens(text: str) -> int:
        return len(_enc.encode(text))

    TOKEN_COUNTER = "tiktoken/cl100k_base (≈Claude)"
except ImportError:
    def count_tokens(text: str) -> int:
        return max(1, len(text) // 4)

    TOKEN_COUNTER = "chars÷4 approximation  (pip install tiktoken for accuracy)"


# ── Data model ───────────────────────────────────────────────────────────────
LOAD_ALWAYS = "always"
LOAD_SESSION = "session-start"
LOAD_ON_DEMAND = "on-demand"
LOAD_DISABLED = "disabled"


@dataclass
class Component:
    name: str
    category: str
    load_when: str   # LOAD_* constant
    tokens: int
    files: int = 1
    path: str = ""
    note: str = ""


# ── Helpers ──────────────────────────────────────────────────────────────────
def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def parse_frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    result = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            result[k.strip()] = v.strip()
    return result


def skill_listing_tokens(skill_dir: Path) -> int:
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.exists():
        return 0
    fm = parse_frontmatter(read(skill_file))
    name = fm.get("name", skill_dir.name)
    description = fm.get("description", "")
    listing_line = f"- {name}: {description[:120]}"
    return count_tokens(listing_line)


def _get_enabled_plugins(workspace: Path) -> set[str]:
    project_settings = workspace / ".claude" / "settings.json"
    try:
        ps = json.loads(project_settings.read_text())
        return {k for k, v in ps.get("enabledPlugins", {}).items() if v}
    except Exception:
        return set()


def _load_plugin_data() -> dict:
    plugins_file = Path.home() / ".claude" / "plugins" / "installed_plugins.json"
    try:
        return json.loads(plugins_file.read_text()).get("plugins", {})
    except Exception:
        return {}


# ── Analyzers ────────────────────────────────────────────────────────────────
def analyze_claude_md(workspace: Path) -> list[Component]:
    out = []
    for label, path in [
        ("CLAUDE.md (project)", workspace / "CLAUDE.md"),
        ("CLAUDE.md (user)", Path.home() / ".claude" / "CLAUDE.md"),
    ]:
        if path.exists():
            out.append(Component(
                name=label, category="Config",
                load_when=LOAD_ALWAYS, tokens=count_tokens(read(path)),
                path=str(path),
            ))
    return out


def analyze_rules(workspace: Path) -> list[Component]:
    out = []
    for rules_dir, label_prefix in [
        (workspace / ".claude" / "rules", "project"),
        (Path.home() / ".claude" / "rules", "user"),
    ]:
        if not rules_dir.exists():
            continue
        for f in sorted(rules_dir.glob("*.md")):
            out.append(Component(
                name=f"rule:{f.stem} ({label_prefix})",
                category="Rules",
                load_when=LOAD_ALWAYS,
                tokens=count_tokens(read(f)),
                path=str(f.relative_to(workspace) if f.is_relative_to(workspace) else f),
            ))
    return out


def analyze_local_skills(workspace: Path) -> list[Component]:
    out = []
    skills_root = workspace / ".claude" / "skills"
    if not skills_root.exists():
        return out
    for skill_dir in sorted(skills_root.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue
        listing = skill_listing_tokens(skill_dir)
        full = count_tokens(read(skill_file))
        out.append(Component(
            name=f"skill:{skill_dir.name} [listing]",
            category="Skills/local",
            load_when=LOAD_ALWAYS,
            tokens=listing,
            path=str(skill_file.relative_to(workspace)),
        ))
        out.append(Component(
            name=f"skill:{skill_dir.name} [full]",
            category="Skills/local",
            load_when=LOAD_ON_DEMAND,
            tokens=full,
            path=str(skill_file.relative_to(workspace)),
        ))
    return out


def analyze_plugin_skills(workspace: Path, verbose: bool = False) -> list[Component]:
    out = []
    enabled = _get_enabled_plugins(workspace)

    for plugin_key, installs in _load_plugin_data().items():
        if not installs:
            continue
        install = installs[0]
        install_path = Path(install.get("installPath", ""))
        scope = install.get("scope", "?")
        is_enabled = plugin_key in enabled

        if not is_enabled and not verbose:
            continue

        load_skills = LOAD_ALWAYS if is_enabled else LOAD_DISABLED
        load_full = LOAD_ON_DEMAND if is_enabled else LOAD_DISABLED
        status = "enabled" if is_enabled else "disabled"

        for skills_subpath in [
            install_path / ".claude" / "skills",
            install_path / "skills",
        ]:
            if not skills_subpath.exists():
                continue

            listing_total, full_total, skill_count = 0, 0, 0
            for skill_dir in skills_subpath.iterdir():
                if not skill_dir.is_dir():
                    continue
                skill_file = skill_dir / "SKILL.md"
                if not skill_file.exists():
                    continue
                listing_total += skill_listing_tokens(skill_dir)
                full_total += count_tokens(read(skill_file))
                skill_count += 1

            if skill_count == 0:
                continue

            plugin_short = plugin_key.split("@")[0]
            out.append(Component(
                name=f"plugin:{plugin_short} [{skill_count} skills, listing]",
                category="Skills/plugins",
                load_when=load_skills,
                tokens=listing_total,
                files=skill_count,
                path=str(install_path),
                note=f"{status}, scope={scope}",
            ))
            out.append(Component(
                name=f"plugin:{plugin_short} [{skill_count} skills, full]",
                category="Skills/plugins",
                load_when=load_full,
                tokens=full_total,
                files=skill_count,
                path=str(install_path),
                note=f"{status}, scope={scope}",
            ))
    return out


def analyze_plugin_agents(workspace: Path, verbose: bool = False) -> list[Component]:
    """Measure agent definitions from plugin cache — these load into Agent tool description per turn."""
    out = []
    enabled = _get_enabled_plugins(workspace)

    for plugin_key, installs in _load_plugin_data().items():
        if not installs:
            continue
        install_path = Path(installs[0].get("installPath", ""))
        scope = installs[0].get("scope", "?")
        is_enabled = plugin_key in enabled

        if not is_enabled and not verbose:
            continue

        load_when = LOAD_ALWAYS if is_enabled else LOAD_DISABLED
        status = "enabled" if is_enabled else "disabled"
        plugin_short = plugin_key.split("@")[0]

        for agents_subpath in [
            install_path / ".claude" / "agents",
            install_path / "agents",
        ]:
            if not agents_subpath.exists():
                continue

            total, count = 0, 0
            for f in agents_subpath.glob("*.md"):
                content = read(f)
                if content:
                    total += count_tokens(content)
                    count += 1

            if count == 0:
                continue

            out.append(Component(
                name=f"plugin:{plugin_short} [{count} agents, defs]",
                category="Agents/plugins",
                load_when=load_when,
                tokens=total,
                files=count,
                path=str(agents_subpath),
                note=f"{status}, scope={scope} — injected into Agent tool description",
            ))
    return out


def analyze_memory(workspace: Path) -> list[Component]:
    out = []
    proj_key = str(workspace).replace("/", "-")
    for memory_dir, label in [
        (Path.home() / ".claude" / "projects" / proj_key / "memory", "project"),
        (Path.home() / ".claude" / "memory", "user"),
    ]:
        if not memory_dir.exists():
            continue
        index = memory_dir / "MEMORY.md"
        if index.exists():
            out.append(Component(
                name=f"MEMORY.md index ({label})",
                category="Memory",
                load_when=LOAD_ALWAYS,
                tokens=count_tokens(read(index)),
                path=str(index),
            ))
        total, count = 0, 0
        for f in memory_dir.glob("*.md"):
            if f.name == "MEMORY.md":
                continue
            total += count_tokens(read(f))
            count += 1
        if count:
            out.append(Component(
                name=f"memory files ({label})",
                category="Memory",
                load_when=LOAD_ON_DEMAND,
                tokens=total,
                files=count,
                path=str(memory_dir),
                note=f"{count} files",
            ))
    return out


def analyze_agents(workspace: Path) -> list[Component]:
    out = []
    for agents_dir, label in [
        (workspace / ".claude" / "agents", "project"),
        (Path.home() / ".claude" / "agents", "user"),
    ]:
        if not agents_dir.exists():
            continue
        for f in sorted(agents_dir.glob("*.md")):
            out.append(Component(
                name=f"agent:{f.stem} ({label})",
                category="Agents",
                load_when=LOAD_ALWAYS,
                tokens=count_tokens(read(f)),
                path=str(f.relative_to(workspace) if f.is_relative_to(workspace) else f),
            ))
    return out


def analyze_commands(workspace: Path) -> list[Component]:
    out = []
    for commands_dir, label in [
        (workspace / ".claude" / "commands", "project"),
        (Path.home() / ".claude" / "commands", "user"),
    ]:
        if not commands_dir.exists():
            continue
        for f in sorted(commands_dir.glob("*.md")):
            out.append(Component(
                name=f"command:{f.stem} ({label})",
                category="Commands",
                load_when=LOAD_ON_DEMAND,
                tokens=count_tokens(read(f)),
                path=str(f.relative_to(workspace) if f.is_relative_to(workspace) else f),
            ))
    return out


def analyze_session_hooks(workspace: Path) -> list[Component]:
    out = []
    enabled = _get_enabled_plugins(workspace)

    for plugin_key, installs in _load_plugin_data().items():
        if plugin_key not in enabled or not installs:
            continue
        install_path = Path(installs[0].get("installPath", ""))
        plugin_short = plugin_key.split("@")[0]

        for hook_path in [
            install_path / "hooks" / "session-start.md",
            install_path / ".claude" / "hooks" / "session-start.md",
            install_path / "STARTUP.md",
            install_path / ".claude" / "STARTUP.md",
        ]:
            if hook_path.exists():
                out.append(Component(
                    name=f"hook:{plugin_short} session-start",
                    category="Hooks",
                    load_when=LOAD_SESSION,
                    tokens=count_tokens(read(hook_path)),
                    path=str(hook_path),
                ))
    return out


def estimate_mcp_hidden_costs(workspace: Path) -> dict:
    """Count MCP servers from settings to estimate hidden tool definition costs."""
    mcp_servers: list[str] = []

    for settings_path in [
        workspace / ".claude" / "settings.json",
        workspace / ".claude" / "settings.local.json",
        Path.home() / ".claude" / "settings.json",
    ]:
        if not settings_path.exists():
            continue
        try:
            s = json.loads(settings_path.read_text())
            mcp_servers.extend(s.get("mcpServers", {}).keys())
            if s.get("enableAllProjectMcpServers"):
                mcp_servers.append("(all project MCP servers enabled)")
            mcp_servers.extend(s.get("enabledMcpjsonServers", []))
        except Exception:
            pass

    return {
        "mcp_servers": list(dict.fromkeys(mcp_servers)),  # dedupe, preserve order
    }


# ── Rendering ─────────────────────────────────────────────────────────────────
COLORS = {
    LOAD_ALWAYS:    "\033[91m",   # red
    LOAD_SESSION:   "\033[93m",   # yellow
    LOAD_ON_DEMAND: "\033[92m",   # green
    LOAD_DISABLED:  "\033[90m",   # grey
    "reset": "\033[0m",
    "bold":  "\033[1m",
    "dim":   "\033[2m",
}

LOAD_BADGE = {
    LOAD_ALWAYS:    "● always   ",
    LOAD_SESSION:   "◑ session  ",
    LOAD_ON_DEMAND: "○ on-demand",
    LOAD_DISABLED:  "✕ disabled ",
}


def fmt_tokens(n: int) -> str:
    return f"{n:>8,}"


def render(components: list[Component], workspace: Path, verbose: bool):
    always    = [c for c in components if c.load_when == LOAD_ALWAYS]
    session   = [c for c in components if c.load_when == LOAD_SESSION]
    on_demand = [c for c in components if c.load_when == LOAD_ON_DEMAND]
    disabled  = [c for c in components if c.load_when == LOAD_DISABLED]

    total_always    = sum(c.tokens for c in always)
    total_session   = sum(c.tokens for c in session)
    total_on_demand = sum(c.tokens for c in on_demand)
    total_disabled  = sum(c.tokens for c in disabled)

    name_w = max((len(c.name) for c in components), default=40) + 2
    name_w = max(name_w, 45)

    SEP = "─" * (name_w + 55)
    B = COLORS["bold"]
    R = COLORS["reset"]
    D = COLORS["dim"]

    def section(title: str, items: list[Component], color: str, total: int):
        badge = LOAD_BADGE.get(items[0].load_when if items else LOAD_ALWAYS, "")
        print(f"\n{B}{color}{badge}  {title}{R}")
        print(SEP)
        for c in sorted(items, key=lambda c: c.tokens, reverse=True):
            pct = f"{c.tokens / total * 100:.1f}%" if total else "  0.0%"
            note = f"  {D}({c.note}){R}" if c.note else ""
            cat = f"{D}[{c.category}]{R}"
            print(f"  {c.name:<{name_w}} {fmt_tokens(c.tokens)}  {pct:>6}  {cat}{note}")
        print(f"  {'SUBTOTAL':<{name_w}} {fmt_tokens(total)}")

    print(f"\n{B}{'─'*20} Claude Code Token Usage Analyzer {'─'*20}{R}")
    print(f"  Workspace : {workspace}")
    print(f"  Counter   : {TOKEN_COUNTER}")
    if verbose:
        print(f"  Mode      : verbose (showing disabled plugins)")

    if always:
        section("PER-TURN COST (injected every message)", always, COLORS[LOAD_ALWAYS], total_always)
    if session:
        section("PER-SESSION COST (injected on session start)", session, COLORS[LOAD_SESSION], total_session)
    if on_demand:
        section("ON-DEMAND COST (loaded when skill/command invoked)", on_demand, COLORS[LOAD_ON_DEMAND], total_on_demand)
    if disabled and verbose:
        section("DISABLED (would cost if re-enabled)", disabled, COLORS[LOAD_DISABLED], total_disabled)

    # ── Hidden cost estimates ─────────────────────────────────────────────────
    mcp = estimate_mcp_hidden_costs(workspace)
    n_mcp = len([s for s in mcp["mcp_servers"] if not s.startswith("(")])
    # Claude Code built-in system prompt: ~8-10K
    hidden_system = 9_000
    # Per MCP server: ~300 tokens for tool names + 1000 avg for instructions
    hidden_mcp_tools = n_mcp * 200    # deferred tool name listing (~15 tokens × N tools per server)
    hidden_mcp_instr = n_mcp * 800    # instruction text injected per server
    # Deferred tool list (just names): each MCP tool is ~15 tokens, assume ~10 tools/server
    hidden_deferred = n_mcp * 10 * 15
    # Enabled plugin agents listed in Agent tool description: already measured above
    hidden_total_est = hidden_system + hidden_mcp_tools + hidden_mcp_instr + hidden_deferred

    print(f"\n{B}── Estimated Hidden Costs (not measurable from files) ──{R}")
    print(f"  Claude Code system prompt        ~{hidden_system:,} tokens  (built-in, fixed)")
    if n_mcp > 0:
        print(f"  MCP servers active               {n_mcp} server(s): {', '.join(s for s in mcp['mcp_servers'] if not s.startswith('('))}")
        print(f"  MCP instruction text             ~{hidden_mcp_instr:,} tokens  (~800/server avg; Figma alone ~2-3K)")
        print(f"  MCP deferred tool names          ~{hidden_deferred:,} tokens  (~15 tokens × ~10 tools/server)")
    else:
        print(f"  No MCP servers detected in settings")
    print(f"  {D}Note: re-enabled plugin agents (pr-review-toolkit etc.) also inject into Agent tool desc{R}")

    print(f"\n{B}── Estimated Real Per-Turn Total ──{R}")
    print(f"  {COLORS[LOAD_ALWAYS]}● Measured (files)  {R}: {fmt_tokens(total_always)} tokens")
    print(f"  {COLORS['dim']}  Hidden estimate    {R}: ~{hidden_total_est:,} tokens")
    print(f"  {B}  TOTAL estimate     : ~{total_always + hidden_total_est:,} tokens/turn{R}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{B}{'─'*20} Summary {'─'*20}{R}")
    print(f"  {COLORS[LOAD_ALWAYS]}● Per-turn   {R}: {fmt_tokens(total_always)} tokens measured  ← recurring cost")
    print(f"  {COLORS[LOAD_SESSION]}◑ Per-session{R}: {fmt_tokens(total_session)} tokens")
    print(f"  {COLORS[LOAD_ON_DEMAND]}○ On-demand  {R}: {fmt_tokens(total_on_demand)} tokens  ← only when skills/commands run")
    if verbose and total_disabled:
        print(f"  {COLORS[LOAD_DISABLED]}✕ Disabled   {R}: {fmt_tokens(total_disabled)} tokens  ← would cost if re-enabled")

    print(f"\n{B}Top 5 per-turn culprits:{R}")
    for i, c in enumerate(sorted(always, key=lambda x: x.tokens, reverse=True)[:5], 1):
        pct = f"{c.tokens / total_always * 100:.1f}%" if total_always else "0%"
        print(f"  {i}. {c.name:<{name_w - 3}} {fmt_tokens(c.tokens)}  ({pct})")
        if c.path:
            print(f"     {D}→ {c.path}{R}")

    print(f"\n{B}Per-turn cost by category:{R}")
    cat_totals: dict[str, int] = {}
    for c in always:
        cat_totals[c.category] = cat_totals.get(c.category, 0) + c.tokens
    for cat, total in sorted(cat_totals.items(), key=lambda x: x[1], reverse=True):
        pct = f"{total / total_always * 100:.1f}%" if total_always else "0%"
        bar_len = int(total / total_always * 40) if total_always else 0
        bar = "█" * bar_len
        print(f"  {cat:<20} {fmt_tokens(total)}  ({pct:>6})  {COLORS[LOAD_ALWAYS]}{bar}{R}")
    print()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    args = sys.argv[1:]
    verbose = "--verbose" in args
    positional = [a for a in args if not a.startswith("--")]

    workspace = Path(positional[0]).resolve() if positional else Path.cwd().resolve()

    components: list[Component] = []
    components += analyze_claude_md(workspace)
    components += analyze_rules(workspace)
    components += analyze_local_skills(workspace)
    components += analyze_plugin_skills(workspace, verbose=verbose)
    components += analyze_plugin_agents(workspace, verbose=verbose)
    components += analyze_memory(workspace)
    components += analyze_agents(workspace)
    components += analyze_commands(workspace)
    components += analyze_session_hooks(workspace)

    if not components:
        print("No Claude Code components found in", workspace)
        sys.exit(1)

    render(components, workspace, verbose=verbose)
