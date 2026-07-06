# Setup marionette MCP — uma vez por máquina (opt-in)

1. **Instalar o server**:
   ```bash
   dart pub global activate marionette_mcp
   ```
   Binário em `~/.pub-cache/bin/marionette_mcp` — precisa estar no `PATH`.

2. **Registrar o MCP** — ⚠️ rode da raiz do **workspace/projeto que você abre no Claude Code**, não de uma subpasta:
   ```bash
   claude mcp add --scope local --transport stdio marionette -- marionette_mcp
   ```
   O registro grava em `~/.claude.json` sob o **project key do cwd**. Registrado na subpasta errada, o server aparece em `claude mcp list` mas as tools **nunca carregam** na sessão aberta da raiz.

3. **Reiniciar a sessão** do Claude Code — server MCP novo só carrega no boot da sessão.

4. **Verificar**: as tools `marionette__*` aparecem no toolset da nova sessão.

## Lado app (setup único no repo)

- Dep `marionette_flutter` no `pubspec.yaml` (pure-Dart, sem plugin nativo).
- Um entrypoint dedicado (ex.: `lib/main_marionette.dart`): `MarionetteBinding.ensureInitialized()` + `bootstrap(...)`. O bootstrap normal não deve referenciar marionette, para que o release faça tree-shake do binding de teste.

## Config do projeto — Environments & flavors

Preencha esta tabela com os flavors reais do seu app antes de usar o skill em produção. Exemplo de shape (genérico, não copie os valores):

| Flavor | Env file | Application ID suffix | Notes |
|---|---|---|---|
| `dev` | `env.json` | `.dev` | Desenvolvimento local |
| `hml` | `env_hml.json` | `.hml` | Homologação / QA |
| `preprod` | `env_preprod.json` | `.preprod` | Staging |
| `prod` | `env_prod.json` | *(nenhum)* | Produção |

Run commands (adapte os nomes de flavor/env do seu projeto):
```bash
flutter run --flavor dev --dart-define-from-file=env.json
flutter run --flavor hml --dart-define-from-file=env_hml.json
```

Android flavors: `android/app/build.gradle` (`productFlavors` block).
iOS schemes: `ios/Runner.xcodeproj/xcshareddata/xcschemes/`.

Se o app depende de pacotes locais/monorepo (SDK, design system) via `path:`/git ref, documente aqui a convenção de branch/versão usada em dev — o script de launch só cuida do app; dependências de pacote são responsabilidade do seu workflow de pubspec.
