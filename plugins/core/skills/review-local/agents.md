# review-local Agent Configuration

Source of truth for agents dispatched by the `review-local` skill. The skill reads this file at step 3 to build the parallel dispatch payload. Add, remove, or retune agents here — never inline in the skill body.

## Project config

The rows below use `pr-review-toolkit` (a generic marketplace plugin) as the default roster. The **framing strings** cite rule codes in brackets — replace them with the project's real codes (e.g., the state-management/architecture blockers defined in your stack's rules). Without this config, the agent still runs, just without a specific list of codes to prioritize.

## Agents

| ID | Subagent type | Focus | Framing |
|---|---|---|---|
| `code` | `pr-review-toolkit:code-reviewer` | State-management, DI, Architecture smells (config: project's rule codes) | "[Project's blocker rule codes] violations must be flagged as 🔴 Important (not 🟡 Nit). Reference the rule code." |
| `silent` | `pr-review-toolkit:silent-failure-hunter` | Result-type misuse, purposeless try/catch, swallowed errors | "Focus on: swallowed error branches in the project's error-handling type, try/catch without re-raise or state update, synchronous reset methods wrapped in try/catch." |
| `type` | `pr-review-toolkit:type-design-analyzer` | Hardcoded design-system values, boolean flags, raw discriminators (config: project's rule codes) | "Flag hardcoded visual values (colors, spacing, radius) that bypass the project's design-token system. Flag 3+ mutually-exclusive bool state fields as an implicit-FSM smell. Flag raw bool/String discriminators where a sealed/enum type would do." |
| `test` | `pr-review-toolkit:pr-test-analyzer` | Coverage on critical layers (config: % target), screen/component tests for modified screens | "This project requires ≥[X]% coverage on [config: stores/repositories or equivalent]. Flag missing tests when a screen/component is modified." |
| `consumer` | `core:consumer-simulation` | Implementation vs ticket coverage gap analysis | "Only include if `--ticket` was provided. Pass ONLY the ticket text — never the diff." |

## Dispatch Rules

- **Default**: dispatch all agents whose preconditions are met.
- **`consumer`** is gated on `--ticket`. If `--ticket` is absent, omit `consumer` from the dispatch.
- **`--agents` flag** (see skill): selects a subset by ID. Each ID must match an entry in this table. Unknown IDs abort with an error before dispatch.
- All agents receive the diff scope (`git diff <base>...HEAD`) except `consumer`, which receives ONLY the ticket text.

## Adding a new agent

1. Add a row to the table above with a unique short ID, the `subagent_type`, the focus area, and the framing string (guidance text mirrors the user's language, default English; rule codes stay in whatever casing the project uses).
2. If the agent has a precondition (like `consumer` requires `--ticket`), document it in **Dispatch Rules**.
3. The skill picks up the change automatically — no edit to `SKILL.md` needed unless the precondition logic changes.

**Worked example — stack-specific smell hunter:** a project on a framework with its own state-management footguns (e.g. a reactive-state library with smells a generic reviewer won't catch) can add a narrow subagent for that domain — its own agent definition file with a fixed prompt, dispatched here with `Framing: "Pass the diff. Agent has its own narrow prompt from its definition file."` and no precondition beyond "state files changed in the diff." This project does not ship such an agent by default (core stays stack-agnostic); add one per-stack if your codebase warrants it.
