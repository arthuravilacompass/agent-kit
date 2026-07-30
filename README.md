# agent-kit

*English · [Português](README.pt-BR.md) — this file is the source of truth.*

> **agent-kit is an epistemic-discipline kit for Flutter/Dart work with Claude Code — deterministic verifiers for what the harness doesn't check, plus the reasoning postures to use them well.**

**How to read the map below.** The top band is entry — three ways in: a loose phrase, a `/ce-*` command, or always-on (no invocation needed). The rail underneath is conduction: `superpowers` owns Discover, [compound-engineering](https://github.com/EveryInc/compound-engineering-plugin) ("CE" from here on) owns Plan through Ship — both external plugins you install separately. This repo (`/core:*`, `/team:*`) is the always-on floor under either conductor.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/routing-diagram-dark.svg">
  <img alt="agent-kit routing map: how you enter (loose phrase, /ce-*, always-on) and who conducts each stage" src="assets/routing-diagram-light.svg">
</picture>

*The gate behind Ship is `/core:review-local` (lint · tests · citation validation); capture after Ship is `/ce-compound` and `core:learn`. `/core:tech-breakdown` (dead end, dotted) never enters CE automatically — its output is copy-pasted into `/ce-plan`.*

Conduction and discovery aren't the kit's job — CE and `superpowers` own those, or your own process. Of everything the kit ships, **only the hooks are a guarantee**: they fire on their own, and every skill, gate, and posture runs because you invoked it. Architecture (3 layers) and posture: **[docs/GOVERNANCE.md](docs/GOVERNANCE.md)**.

## What's included

Four plugins installable via a local marketplace. `mobile` is the flagship vertical; `core` and `council` are the stack-agnostic foundation under it.

| Plugin | What it is | Install when |
|---|---|---|
| `mobile` — **flagship** | Flutter/Dart toolkit: review rules, scaffolding, four deterministic verifiers (one blocking smell-checker + three advisory hooks) | Flutter/Dart project on (or near) the assumed stack — note below |
| `core` | Deterministic mechanism: read-ledger and citation gate, the always-on discipline rules, `core:grill-me`'s checkpoints (`pre-plan`/`post-plan`/`pre-done`), the repo gates | Always — the foundation for the rest |
| `council` | Epistemic lenses (reasoning postures) for high-cost-to-reverse decisions | Recommended with `core` |
| `team` | Copilot for agile ceremonies — refinement with the PO, squad communication | You run refinement or write to a squad |

**The `mobile` stack assumption.** Verifiers are calibrated to MobX + `get_it`/`injectable` (scaffolding also assumes `dartz`). On Bloc/Riverpod the DI and lifecycle checks simply don't fire — they look for `get_it` calls inside `_store.dart`/`_controller.dart`. No false positives, but no coverage either, until you edit the hook regexes yourself.

Full generated catalog of every skill, agent, hook, and script: **[INVENTORY.md](INVENTORY.md)**.

## Installation

### 1. Clone (once)

Already have a clone, at any path, from any source? Skip to step 2 — every command below uses `~/dev/agent-kit` as a placeholder; substitute your actual path.

```bash
git clone <this-repo-url> ~/dev/agent-kit
```

### 2. Install — one line, by profile

Run it **from inside the project where the kit should be active**. `claude plugin install` installs at user scope by default — every project on this machine; pass `--scope project` to confine it to this one.

```bash
~/dev/agent-kit/scripts/install.sh minimal   # or: mobile · team · full
```

| Profile | Plugins | Pick it when |
|---|---|---|
| `minimal` | core + council | any project — the foundation |
| `mobile` | minimal + mobile | Flutter/Dart project on the assumed stack |
| `team` | minimal + team | you run refinement / talk to a squad — needs a board MCP you supply |
| `full` | all four | everything above applies |

Prefer the native commands? They're exactly what the script wraps:

```bash
claude plugin marketplace add "$HOME/dev/agent-kit"
claude plugin install core@agent-kit
claude plugin install council@agent-kit  # recommended with core
claude plugin install team@agent-kit     # optional: agile ceremonies with PO/squad
claude plugin install mobile@agent-kit   # only in a Flutter/Dart project
```

**Three external plugins, none of them installed by any profile.** The kit's gates and hooks work with nothing else installed — skip this if that's all you want. But the routing below assumes CE and `superpowers`; without them `/ce-plan`, `/ce-work`, and `superpowers:brainstorming` don't exist yet. The third, `pr-review-toolkit`, gates `/core:review-local` — this repo pins no source for it (it's a generic marketplace plugin), so install it from wherever you get it; see [Requirements](#requirements) for exactly what you lose without it.

```bash
claude plugin marketplace add https://github.com/obra/superpowers
claude plugin install superpowers@superpowers-dev

claude plugin marketplace add https://github.com/EveryInc/compound-engineering-plugin
claude plugin install compound-engineering@compound-engineering-plugin
```

### 3. Verify, and update later

```bash
~/dev/agent-kit/scripts/doctor.sh   # checks CLI, marketplace, plugins, and the kit's own gates
claude plugin list                  # or manually: should list what you installed

# after a new commit to the kit — session restart required
claude plugin update core@agent-kit council@agent-kit team@agent-kit mobile@agent-kit
```

In a new session, `core`'s rules already come in via SessionStart — nothing to type. A plugin installed at project scope needs `--scope project` on update too.

### Use the epistemic tier on another AI tool

The plugins are Claude Code-native, but the always-on epistemic tier is tool-agnostic. Emit it as an `AGENTS.md`, read by GitHub Copilot, Cursor, and other AGENTS.md-honoring tools:

```bash
~/dev/agent-kit/scripts/install.sh --tool copilot --out .   # writes ./AGENTS.md
# --dry-run to preview · --force to overwrite an existing AGENTS.md
```

Enforcement doesn't travel — hooks and subagent skills run only under Claude Code, so there the rules are **advisory**, and the emitted header says so. Source of truth stays the `using-agent-kit` skill shipped in `core`; re-run to refresh, never hand-edit the output.

### Uninstall

```bash
claude plugin uninstall mobile@agent-kit   # if installed
claude plugin uninstall team@agent-kit
claude plugin uninstall council@agent-kit
claude plugin uninstall core@agent-kit
claude plugin marketplace remove agent-kit
```

## Which tool, when

Indexed by the situation you're in, not by plugin.

**The boundary convention.** Loose phrase → `superpowers`; slash command → CE. Both implement most of the same loop, so nothing mechanically stops a loose phrase from landing on either side's model-invocable skill — the convention moves the election from pattern-matching (indeterminate) to syntax (not).

**Ground rules for the chain in the diagram:**

- **Explicit path, always.** CE's planner auto-discovers only its own artifacts (plus legacy `docs/brainstorms/*-requirements.md`); a superpowers spec at `docs/superpowers/specs/...` matches neither, so a bare `/ce-plan` plans from the wrong input.
- **One executor, chosen once.** `/ce-work` and superpowers' execution flow can both implement a plan; giving it to both leaves neither accountable for "done."
- **The two reviews compose.** `/ce-code-review` is the judgment pass. `/core:review-local` is the gate: blocks before spending a review token if lint or tests fail (CE's review has no such gate), then validates every citation against the read-ledger.
- **Cite only what you read via `Read`/`Grep`.** The ledger is event-driven off those two tools; reads via `Bash` (`cat`, `sed`, shell `grep`) never enter it, so a reviewer that reads that way breaks its own citations at the gate.
- **Unverified ≠ fabricated.** A citation overlapping nothing read lands in its own "Unverified" section as a hypothesis. A missing or session-mismatched ledger reports "nothing to verify against" — never proof of fabrication.
- **Capture runs twice, on purpose.** `/ce-compound` writes the repo-local learning doc (committed, shared); `core:learn` writes personal cross-session memory. `ce-compound`'s scan folds in auto-memory as lower-priority context — run `core:learn` first if you want that.
- **The kit no longer conducts flow.** No kit skill routes you stage to stage. Why: `CHANGELOG.md`'s "CE adopted as flow conductor" decision record.

### "I have a vague feature idea"

Say it loose — "let's think about X" — and `superpowers:brainstorming` fires: interrogation one question at a time, 2–3 candidate approaches, and a committed spec at `docs/superpowers/specs/<date>-<topic>-design.md`. From there, `/ce-plan <that spec path>` and onward.

### "I have a ticket"

For a ticket asking for new or changed behavior — a ticket *reporting a bug* goes to the next section instead, whatever tracker it lives in. The discriminator is what the ticket asks for, not its source format.

Type `/core:tech-breakdown <TICKET>`. CE's planner builds from plans and briefs, never from a ticket, so this skill owns the ticket→plan seam: fetches the ticket, runs discovery, generates the plan, runs a critic phase against the real codebase, and writes the plan path back as a comment.

The seam is narrower than "the kit reads trackers and CE doesn't" — CE does read them, just not to start a plan from one (`ce-debug` fetches a referenced GitHub/Linear/Jira issue; `ce-sweep` reads issues through `gh`). No total is claimed about either provider: two third-party plugins on their own release schedules would make one stale fast. And note the asymmetry — this is the one path that does **not** route through CE. Whether it should hand the enriched ticket to `/ce-plan` instead is an open question, not a settled design.

At review time, pass `--ticket <TICKET>` to `/core:review-local` so the `consumer-simulation` agent joins the panel — it gets only the ticket text and acceptance criteria, never the diff, so it can notice what the implementation quietly dropped. `/core:review-remote` also accepts `--ticket`, but only compares inline, with no agent.

### "Something is broken"

Existing behavior misbehaving. Say it loose — "this test started failing" — and `superpowers:systematic-debugging` fires; type `/ce-debug` for CE's diagnosis loop instead. `ce-debug` is model-invocable and claims the same utterances, so only the loose/slash split decides.

### "I'm touching Flutter code"

Nothing to type — this is the vertical, and it fires regardless of who's conducting. The smell-checker **blocks** an edit that adds a Dart correctness smell (DI resolved inside a store/controller, BuildContext/navigation in a store, `print()`/`debugPrint()` in production code) — add-only, so legacy files stay editable. Three advisory hooks warn without blocking: codegen staleness, DI mismatch (an `@injectable` class missing from the generated config), and lifecycle (a disposable resource with no `dispose()`). On demand: `mobile:code-review-mobile`, `mobile:mobx`, `mobile:performance-patterns`, `mobile:feature-scaffold`, `mobile:marionette`, and the rest. CE has zero Flutter coverage — the vertical is entirely the kit's.

### "I'm about to make a decision that's expensive to undo"

Wear a `council` posture. Postures are a reasoning layer, not a flow layer — they compose with any conductor.

| Posture | Question it forces | Wear it when |
|---|---|---|
| `council:schrodinger` | which explanations still coexist? | a diagnosis is ambiguous and you're tempted to settle |
| `council:bohr` | is the dichotomy false? | a decision is stuck on "A or B" |
| `council:epicurus` | what here is excess? | before calling a design or scope done |
| `council:sagan` | does this matter, at what scale? | before investing real effort |
| `maxwell` (agent — dispatch via the Agent tool) | how does this propagate? | before touching something coupled |
| `zeno` (agent — dispatch via the Agent tool) | where does this break? | validating a proposed solution |

One posture per decision is the default; escalation to blind mode (`epistemic-council`, an isolated subagent that never sees the thread's lean) has its own criteria — the map is `council:council`. CE's `ce-pov` overlaps only Sagan and Maxwell, partially; the other four have no counterpart.

### "I'm about to say it's done"

`/core:grill-me pre-done`. A blind reviewer gets the diff, the acceptance criteria, the rule-file paths, and the plan's `session-settled:` decision entries if it carries any — never the session's narrative — and its findings go through the citation gate before you see them. If what needs pressing is a *decision you own* rather than an artifact, bare `core:grill-me` is the interview mode.

### "The work just split into independent legs"

Three or more legs with no shared state — parallel research, generation, audit — go to `superpowers:dispatching-parallel-agents` (or native parallel subagents) instead of one long sequential pass.

### "I'm running refinement or writing to the squad"

`/team:refine-live` (PO in the room), `/team:refine-async` (from the board), `team:chat-draft` (pt-BR message for Teams/Slack). Both refines expect a board/kanban MCP this kit does not ship, and fail differently without one: `refine-async` degrades gracefully on both ends (works from a pasted context summary if `refine-live`'s state file is missing, exports subtasks as text if the board call fails); `refine-live` has no fallback — it cannot get past fetching the card.

## Requirements

- [Claude Code](https://claude.com/claude-code) with plugin support
- [superpowers](https://github.com/obra/superpowers) — owns discovery (brainstorming, systematic debugging, parallel dispatch)
- [compound-engineering](https://github.com/EveryInc/compound-engineering-plugin) ("CE", MIT, tested against 3.20.0) — owns stage conduction; at user scope it conducts in every project on this machine
- **`core:review-local` requires the `pr-review-toolkit` plugin** (parallel reviewer dispatch). Without it the fallback is `/core:review-remote` — not an equivalent. The real cost isn't lost parallelism: it's losing the citation check, the kit's most distinctive idea, which `review-remote` substitutes with hand re-reading it does not itself call equivalent. Lost alongside: parallel dispatch, and lint/test behavior that differs by mode (pre-push reports a failure as a finding and continues; remote-PR mode skips lint/tests entirely, leaving that to CI)
- For `mobile`: a Flutter/Dart project
- The kit ships no MCP servers of its own. The one place it expects one you supply is `team`'s two refine commands — a board/kanban MCP; nothing else in the kit assumes any

## Advanced

**Governance.** This kit governs itself with the same rigor it enforces. See **[docs/GOVERNANCE.md](docs/GOVERNANCE.md)**: the architecture, the posture on what's proven vs. untested, the artifact lifecycle (wired/unwired/deleted), the promotion rule, and conventions. Owner operations — publishing, the five-part quality gate, `unwired/` triage: **[docs/OPERATIONS.md](docs/OPERATIONS.md)**.

**Repository structure.**

| Directory | What it is |
|---|---|
| `plugins/` | The four installable plugins (`core`, `council`, `team`, `mobile`) |
| `unwired/` | Genericized raw material awaiting proof of use — nothing is loaded, zero context cost ([details](docs/OPERATIONS.md)) |
| `assets/` | Manual copy-paste templates: status line, `CLAUDE.md` skeleton, `settings.json` snippets |
| `docs/` | [GOVERNANCE.md](docs/GOVERNANCE.md) and [OPERATIONS.md](docs/OPERATIONS.md) |
| `scripts/` | Provenance gate, inventory generator, and maintenance tooling |

---

[INVENTORY.md](INVENTORY.md) · [docs/GOVERNANCE.md](docs/GOVERNANCE.md) · [docs/OPERATIONS.md](docs/OPERATIONS.md) · [CHANGELOG.md](CHANGELOG.md)
