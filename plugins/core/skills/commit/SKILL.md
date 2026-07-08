---
name: commit
description: Invoke to run pre-commit validation (lint + tests) and create a conventional commit from the staged diff — never commits without explicit user approval.
disable-model-invocation: true
---

# commit — Standardized Commit

Validates the staged diff (lint, then tests) and generates a conventional commit message from it. Only runs `git commit` after explicit user approval.

## Project config

This skill assumes the consumer project defines:
- **Lint/static analysis command** (e.g., `flutter analyze`, `eslint .`, `ruff check`).
- **Test command** (e.g., `flutter test`, `npm test`, `pytest`).

Without these configs, skip steps 2/3 and warn the user that automatic validation could not run.

## Steps

1. **Check staged files**

   Run `git diff --cached --stat` to see what's staged.

   If nothing is staged, run `git diff --stat` to show unstaged changes and ask the user: "Nothing is staged. Which files would you like to stage?"

2. **Run lint**

   Run the project's lint/static-analysis command (config above).

   If lint fails, report all errors and **STOP**. Do not proceed to commit.

3. **Run tests**

   Run the project's test command (config above).

   If tests fail, report the failures and **STOP**. Do not proceed to commit.

4. **Analyze the staged diff**

   Run `git diff --cached` to understand what's changing.

5. **Generate the commit message**

   Create a message following this format:
   ```
   <type>: <description>

   <optional body>
   ```

   Rules:
   - Type: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, or `ci`
   - Description: English, imperative mood, no trailing period, max 72 characters
   - Body: optional, add when the title alone isn't self-explanatory
   - No emojis

6. **Present for approval**

   Show the user:
   - Summary of staged files
   - Proposed commit message
   - Ask: "Proceed with this commit? Reply with: yes, edit [new message], or abort"

7. **Execute the commit only after explicit approval**

   Only run `git commit -m "..."` after the user confirms with "yes".

   If the user says "edit", use their new message.
   If the user says "abort", stop.

## Inviolable rules

Never skip lint or tests. Never commit with `--no-verify`.
