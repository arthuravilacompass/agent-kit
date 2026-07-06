---
name: commit
description: Invoque para rodar validação pré-commit (lint + testes) e criar um commit convencional a partir do diff staged — nunca commita sem aprovação explícita do usuário.
disable-model-invocation: true
---

# commit — Standardized Commit

Run pre-commit validation and create a conventional commit following the project's commit conventions.

## Config do projeto

Este skill assume que o projeto consumidor define:
- **Comando de lint/static analysis** (ex.: `flutter analyze`, `eslint .`, `ruff check`).
- **Comando de testes** (ex.: `flutter test`, `npm test`, `pytest`).

Sem essas configs, pule as steps 2/3 e avise o usuário que a validação automática não pôde rodar.

## Steps

1. **Check staged files**

   Run `git diff --cached --stat` to see what is staged.

   If nothing is staged, run `git diff --stat` to show unstaged changes and ask the user: "Nothing is staged. Which files would you like to stage?"

2. **Run lint**

   Run the project's lint/static-analysis command (config above).

   If lint fails, report all errors and **STOP**. Do not proceed to commit.

3. **Run tests**

   Run the project's test command (config above).

   If tests fail, report failures and **STOP**. Do not proceed to commit.

4. **Analyze staged diff**

   Run `git diff --cached` to understand what is changing.

5. **Generate commit message**

   Create a message following this format:
   ```
   <type>: <description>

   <optional body>
   ```

   Rules:
   - Type: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, or `ci`
   - Description: English, imperative mood, no period, max 72 characters
   - Body: optional, add when the title alone is not self-explanatory
   - No emojis

6. **Present for approval**

   Show the user:
   - Summary of staged files
   - Proposed commit message
   - Ask: "Proceed with this commit? Reply with: yes, edit [new message], or abort"

7. **Execute commit only after explicit approval**

   Only run `git commit -m "..."` after the user confirms with "yes".

   If the user says "edit", use their new message.
   If the user says "abort", stop.

## Important

Never skip lint or tests. Never commit with `--no-verify`.
