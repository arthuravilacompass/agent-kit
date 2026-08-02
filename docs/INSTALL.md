# Install reference

Detail behind the README's one-line happy path: native `claude plugin` commands (what `scripts/install.sh` wraps), emitting the epistemic tier as `AGENTS.md` for non-Claude-Code tools, uninstall, and the repo's own governance/structure tables. Nothing here is required reading to get started — [README.md](../README.md#installation) covers that in three steps.

## Native install commands

Prefer the native commands over `scripts/install.sh`? This is exactly what the script wraps. Run any of it **from inside the project where the kit should be active** — `claude plugin install`/`update` default to user scope (every project on this machine); pass `--scope project` to confine an install (and its later `update`) to this one.

### Kit plugins

```bash
claude plugin marketplace add "$HOME/dev/agent-kit"
claude plugin install core@agent-kit
claude plugin install council@agent-kit  # recommended with core
claude plugin install team@agent-kit     # optional: agile ceremonies with PO/squad
claude plugin install mobile@agent-kit   # only in a Flutter/Dart project
```

### External plugins

**Three external plugins, none of them installed by any profile.** The kit's gates and hooks work with nothing else installed — skip this if that's all you want. But the routing map in [README.md](../README.md#which-tool-when) assumes CE and `superpowers`; without them `/ce-plan`, `/ce-work`, and `superpowers:brainstorming` don't exist yet. The third, `pr-review-toolkit`, gates `/core:review-local` — this repo pins no source for it (it's a generic marketplace plugin), so install it from wherever you get it; see the [Requirements](../README.md#requirements) table for what you lose without it, and the detail below for the full cost.

```bash
claude plugin marketplace add https://github.com/obra/superpowers
claude plugin install superpowers@superpowers-dev

claude plugin marketplace add https://github.com/EveryInc/compound-engineering-plugin
claude plugin install compound-engineering@compound-engineering-plugin
```

### Requirements — detail

The README's Requirements table is deliberately compact. The full detail behind each row:

- [Claude Code](https://claude.com/claude-code) with plugin support
- [superpowers](https://github.com/obra/superpowers) — owns discovery (brainstorming, systematic debugging, parallel dispatch)
- [compound-engineering](https://github.com/EveryInc/compound-engineering-plugin) ("CE", MIT, tested against 3.20.0) — owns stage conduction; at user scope it conducts in every project on this machine
- **`core:review-local` requires the `pr-review-toolkit` plugin** (parallel reviewer dispatch). Without it the fallback is `/core:review-remote` — not an equivalent. The real cost isn't lost parallelism: it's losing the citation check, the kit's most distinctive idea, which `review-remote` substitutes with hand re-reading it does not itself call equivalent. Lost alongside: parallel dispatch, and lint/test behavior that differs by mode (pre-push reports a failure as a finding and continues; remote-PR mode skips lint/tests entirely, leaving that to CI)
- For `mobile`: a Flutter/Dart project
- The kit ships no MCP servers of its own. The one place it expects one you supply is `team`'s two refine commands — a board/kanban MCP; nothing else in the kit assumes any

## Use the epistemic tier on another AI tool

The plugins are Claude Code-native, but the always-on epistemic tier is tool-agnostic. Emit it as an `AGENTS.md`, read by GitHub Copilot, Cursor, and other AGENTS.md-honoring tools:

```bash
~/dev/agent-kit/scripts/install.sh --tool copilot --out .   # writes ./AGENTS.md
# --dry-run to preview · --force to overwrite an existing AGENTS.md
```

Enforcement doesn't travel — hooks and subagent skills run only under Claude Code, so there the rules are **advisory**, and the emitted header says so. Source of truth stays the `using-agent-kit` skill shipped in `core`; re-run to refresh, never hand-edit the output.

## Uninstall

```bash
claude plugin uninstall mobile@agent-kit   # if installed
claude plugin uninstall team@agent-kit
claude plugin uninstall council@agent-kit
claude plugin uninstall core@agent-kit
claude plugin marketplace remove agent-kit
```

## Advanced

**Governance & operations.** This kit governs itself with the same rigor it enforces. See **[docs/OPERATIONS.md](OPERATIONS.md)**: architecture, the artifact lifecycle, the promotion rule, publishing, and the quality gate.

**Repository structure.**

| Directory | What it is |
|---|---|
| `plugins/` | The four installable plugins (`core`, `council`, `team`, `mobile`) |
| `assets/` | Manual copy-paste templates: status line, `CLAUDE.md` skeleton, `settings.json` snippets |
| `docs/` | [OPERATIONS.md](OPERATIONS.md) |
| `scripts/` | Provenance gate, inventory generator, and maintenance tooling |
