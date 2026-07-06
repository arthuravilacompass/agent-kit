# settings-snippets.md — trechos de settings.json prontos para copiar

Este arquivo não é lido pelo Claude Code — é documentação de referência. Copie os trechos que fizerem sentido pro `settings.json` (projeto) ou `settings.local.json` (usuário) do projeto consumidor e adapte os paths/domínios aos reais.

## 1. Sandbox Flutter — `allowWrite` / `allowRead`

Um workspace Flutter/Dart precisa que o sandbox de comando libere escrita nos caches de toolchain (fora do repo) e leitura em artefatos gerados dentro do repo — sem isso, todo `flutter pub get`/`build_runner` pede aprovação manual.

```json
{
  "sandbox": {
    "enabled": true,
    "filesystem": {
      "allowWrite": [
        "/opt/homebrew/Caskroom/flutter/flutter/bin/cache",
        "~/.dart-tool",
        "~/.pub-cache",
        "~/.flutter"
      ],
      "allowRead": [
        "./**/.dart_tool",
        "./**/.flutter-plugins-dependencies",
        "./**/.flutter-plugins"
      ],
      "denyRead": [
        "~/.ssh",
        "~/.aws",
        "~/.config/gcloud",
        "~/.npmrc",
        "~/.netrc"
      ]
    },
    "excludedCommands": ["gh", "docker"],
    "allowedDomains": [
      "pub.dev",
      "*.pub.dev",
      "storage.googleapis.com",
      "github.com",
      "*.githubusercontent.com"
    ]
  }
}
```

Notas:
- `allowWrite` aqui é sempre um path de **cache de toolchain fora do repo** (Homebrew Caskroom, `~/.pub-cache`, `~/.dart-tool`, `~/.flutter`) — nunca um path dentro do projeto. Ajuste o caminho do Caskroom se o Flutter não estiver instalado via Homebrew, ou remova a entrada se usar `fvm`/outra gestão de SDK.
- `allowedDomains` acima é o núcleo genérico (pub.dev + GitHub). Adicione os domínios do backend/CDN do projeto consumidor — não herde domínios de outro projeto.
- `denyRead` de credenciais (`~/.ssh`, `~/.aws`, etc.) é defesa em profundidade — vale pra qualquer projeto, não só Flutter.

## 2. Deny-list de codegen — não editar arquivo gerado

Arquivos gerados por `build_runner` (`.g.dart`, `.freezed.dart`, `.config.dart` — json_serializable, freezed, injectable) não devem ser editados diretamente: a fonte de verdade é o arquivo anotado que os gera, e uma edição manual desaparece no próximo `build_runner build`. Bloquear a *ferramenta* de editar esses arquivos evita que o agente "conserte" um erro no lugar errado.

```json
{
  "permissions": {
    "deny": [
      "Edit(./**/*.g.dart)",
      "Edit(./**/*.freezed.dart)",
      "Edit(./**/*.config.dart)",
      "Read(./**/build/**)",
      "Read(./**/.dart_tool/**)",
      "Read(./**/ios/Pods/**)",
      "Read(./**/android/.gradle/**)",
      "Read(./**/coverage/**)",
      "Read(./**/.flutter-plugins)",
      "Read(./**/.flutter-plugins-dependencies)"
    ]
  }
}
```

Notas:
- O deny de `Edit` nos três sufixos de codegen é o item que este snippet existe para documentar — some com a maior fonte de "fix no lugar errado" num projeto Dart com codegen pesado (mobx_codegen, freezed, json_serializable, injectable).
- Os `Read(...)` de `build/`, `.dart_tool/`, `Pods/`, `.gradle/`, `coverage/` são ruído de leitura: diretórios grandes, binários ou gerados que não ajudam o agente a entender o código e custam contexto/tempo se lidos por engano.
- `Edit` aqui bloqueia a tool `Edit`/`MultiEdit`; se o harness também expõe `Write` para esses paths, replique a entrada com `Write(...)`.
