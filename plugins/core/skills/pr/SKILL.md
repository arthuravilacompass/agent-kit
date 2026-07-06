---
name: pr
description: Invoque para analisar todos os commits da branch, rodar verificação e montar a descrição de um Pull Request pronta para revisão — nunca faz push ou cria o PR sem aprovação explícita.
disable-model-invocation: true
---

# pr — Standardized Pull Request

Analyze all commits in this branch, run verification, and create a pull request following the project's conventions.

## Config do projeto

Este skill assume que o projeto consumidor define:
- **Branch base** (default sugerido: `main`; fallback chain abaixo assume `develop`/`main`/`master` se nada for configurado).
- **Comando de testes** e **comando de lint** (ex.: `flutter test --coverage` / `flutter analyze`, ou os equivalentes do stack do projeto).
- **Destino do PR**: GitHub (`gh pr create`) ou Bitbucket (URL de criação manual — org/repo). Sem essa config, assuma GitHub.

## Steps

1. **Identify base branch and collect commits**

   ```bash
   git rev-parse --abbrev-ref HEAD     # current branch
   git log <base>..HEAD --oneline      # all commits ahead of base
   git diff <base>...HEAD --stat        # files changed summary
   git diff <base>...HEAD               # full diff for analysis
   ```

   `<base>` é a branch base do projeto (config acima). Se não existir, tente `develop`, `main`, ou `master`.

2. **Select PR template**

   Determine type via commit convention from step 1: `fix:` → use `templates/pr-bugfix.md`; `feat:` → use `templates/pr-feature.md`. If mixed or ambiguous, ask the user which template to use. The user may pass an argument to force the template: `pr bug` or `pr feat`.

3. **Run verification and capture results**

   Run the project's test command (config — capture: test count, pass/fail) and the project's lint command (config — capture: issue count).

   Capture real numbers. Do not guess or estimate.

4. **Fill the template with real data**

   Read the selected template from `templates/pr-bugfix.md` or `templates/pr-feature.md` and substitute placeholders with the verification results and commit data collected in steps 1 and 3.

5. **Present complete PR for review**

   Show the user:
   - Branch name
   - Base branch
   - Complete filled-in PR description
   - Ask: "Proceed with this PR? Reply with: yes, edit [changes], or abort"

6. **Execute only after explicit approval**

   After the user confirms with "yes":

   ```bash
   # Push branch if not yet on remote
   git push -u origin <branch-name>
   ```

   Then, depending on **Destino do PR** (config):
   - **GitHub**: use `gh pr create` with the filled title/body.
   - **Bitbucket**: generate the PR creation URL and print the title + body ready to paste:

     ```
     URL: https://bitbucket.org/<org>/<repo>/pull-requests/new?source=<branch-name>&dest=<base-branch>

     Título: <commit subject>

     Corpo:
     <filled template>
     ```

     Present the URL, title, and body to the user — they open the URL and paste the title/body directly. Do **not** use `gh pr create` for a Bitbucket-hosted repo.

## Important

- Never push or create a PR without explicit user approval.
- Use real verification results — never fabricate percentages or counts.
- If any verification step fails, report the failures before presenting the PR template.
