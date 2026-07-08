# marionette MCP Setup — once per machine (opt-in)

1. **Install the server**:
   ```bash
   dart pub global activate marionette_mcp
   ```
   Binary at `~/.pub-cache/bin/marionette_mcp` — needs to be on `PATH`.

2. **Register the MCP** — ⚠️ run this from the root of the **workspace/project you open in Claude Code**, not from a subfolder:
   ```bash
   claude mcp add --scope local --transport stdio marionette -- marionette_mcp
   ```
   Registration is written to `~/.claude.json` under the **cwd's project key**. Registered in the wrong subfolder, the server shows up in `claude mcp list` but the tools **never load** in a session opened from the root.

3. **Restart** the Claude Code session — a new MCP server only loads at session boot.

4. **Verify**: the `marionette__*` tools appear in the new session's toolset.

## App Side (one-time setup in the repo)

- `marionette_flutter` dep in `pubspec.yaml` (pure-Dart, no native plugin).
- A dedicated entrypoint (e.g., `lib/main_marionette.dart`): `MarionetteBinding.ensureInitialized()` + `bootstrap(...)`. The normal bootstrap must not reference marionette, so release builds tree-shake the test binding.

## Project Config — Environments & Flavors

Fill in this table with your app's real flavors before using this skill in production. Example shape (generic, don't copy the values):

| Flavor | Env file | Application ID suffix | Notes |
|---|---|---|---|
| `dev` | `env.json` | `.dev` | Local development |
| `hml` | `env_hml.json` | `.hml` | Staging / QA |
| `preprod` | `env_preprod.json` | `.preprod` | Pre-production |
| `prod` | `env_prod.json` | *(none)* | Production |

Run commands (adapt the flavor/env names to your project):
```bash
flutter run --flavor dev --dart-define-from-file=env.json
flutter run --flavor hml --dart-define-from-file=env_hml.json
```

Android flavors: `android/app/build.gradle` (`productFlavors` block).
iOS schemes: `ios/Runner.xcodeproj/xcshareddata/xcschemes/`.

If the app depends on local/monorepo packages (SDK, design system) via `path:`/git ref, document your dev branch/version convention here — the launch script only handles the app; package dependencies are your pubspec workflow's responsibility.
