---
name: marionette
description: Invoke to visually validate Flutter UI changes in the app running in the simulator — launch the app in debug for agent-driven checks, take screenshots, tap/scroll/drive screens, hot-reload after edits. Triggers — "confirm this screen in the simulator", "validate this change visually", "screenshot of the running app".
---

# Marionette — Agent-Driven Visual Validation

## Project Config

Flavors, env files, and the convention for which backend each one points to are specific to each app — fill in the table in `references/SETUP.md` §Environments & flavors with your project's real config before using this skill in production. The driving mechanism (connect, list elements, tap, screenshot, hot-reload) is generic and doesn't change between projects.

## Overview

Connects the session to the Flutter app running in debug in the simulator via marionette MCP (LeanCode): `take_screenshots`, `tap`, `scroll_to`, `enter_text`, `get_logs`, `hot_reload`. Execution is **inline in the main session** — the edit → hot_reload → re-screenshot loop depends on the conversation context (don't delegate to a subagent: subagent screenshots are invisible to the user).

## Step 0 — Preflight

Are the `marionette__*` tools available in this session?

- **No**, and the user wants agent-driven validation → read [references/SETUP.md](references/SETUP.md), pass the setup commands to the user, and **STOP** (MCP registration requires a session restart).
- **No**, and it's a quick check → fallback: ask the user for a manual screenshot.
- **Yes** → proceed.

## Prerequisites — explicit, never a silent default

| Input | How to resolve it |
|---|---|
| Simulator device id | `xcrun simctl list devices booted` — empty? ask or boot one |
| Target backend | Project config: which variable/env file decides the backend (usually not `--flavor` alone). Check the backend the launch script prints on every run. |
| Logged-in state | Authenticated flows (onboarding, checkout, profile) require a logged-in user in the app |
| Feature flag/onboarding visibility | Project config: if the app uses remote config to control onboarding/feature visibility, check the relevant flag before assuming the screen will appear |

## Workflow

1. **Launch**: `bash scripts/run.sh -d <device-id> [-f <flavor>] [-t 600]` (from this skill) — kills duplicate runs, brings up the app in the background, prints the `ws://` connect URI. Flavor and env file: project convention (see `references/SETUP.md`), override with `-e`.
2. **Connect**: `marionette__connect` with the printed URI — **as the very next action, with no work in between**: an idle VM service detaches.
3. **Drive**: `get_interactive_elements` → `tap` / `enter_text` / `scroll_to`. Match by `ValueKey` > text (widget with no key? see Gotchas).
4. **Validate**: `take_screenshots` (renders as an image for the agent) → compare against the expected (reference design / spec / user screenshot).
5. **Iterate**: edit the code → `marionette__hot_reload` → re-screenshot. `get_logs` for analytics events.

## Gotchas

| Symptom | Cause / Fix |
|---|---|
| `marionette__*` tools don't show up | MCP server only loads at session boot — restart; still missing? registration may have been done outside the project/workspace root (see `references/SETUP.md`) |
| VM service won't attach / "OS terminated debug connection for being inactive" | Simulator with accumulated state — reboot **without erasing**: `xcrun simctl shutdown <id> && xcrun simctl bootstatus <id> -b` (erase wipes Keychain/login), then **re-run run.sh** |
| URI file empty after timeout | Check `/tmp/marionette_run.log`; confirm there are no duplicate runs: `pgrep -f main_marionette` |
| Widget not found by the tools | Add `ValueKey('...')` to the target widget and `hot_reload` |
| App landed on the wrong backend | The environment variable that decides the backend (project config) ≠ expected — change the env file or the value, not `--flavor` |

## When NOT to Use

- Static code × reference-design comparison without needing the app running → use your setup's comparison tool, if any.
- Code review → review skills (`mobile:code-review-mobile`).
