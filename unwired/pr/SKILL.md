---
name: pr
description: Invoke to analyze all commits in the branch, run verification, and assemble a Pull Request description ready for review — never pushes or creates the PR without explicit approval.
disable-model-invocation: true
---

# pr — Standardized Pull Request

Analyze all commits in this branch, run verification, and create a pull request following the project's conventions.

## Project config

This skill assumes the consumer project defines:
- **Base branch** (suggested default: `main`; the fallback chain below assumes `develop`/`main`/`master` if nothing is configured).
- **Test command** and **lint command** (e.g., `flutter test --coverage` / `flutter analyze`, or the project stack's equivalents).
- **PR destination**: GitHub (`gh pr create`) or Bitbucket (manual creation URL — org/repo). Without this config, assume GitHub.

## Steps

1. **Identify base branch and collect commits**

   ```bash
   git rev-parse --abbrev-ref HEAD     # current branch
   git log <base>..HEAD --oneline      # all commits ahead of base
   git diff <base>...HEAD --stat        # files changed summary
   git diff <base>...HEAD               # full diff for analysis
   ```

   `<base>` is the project's base branch (config above). If it doesn't exist, try `develop`, `main`, or `master`.

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

   Then, depending on **PR destination** (config):
   - **GitHub**: use `gh pr create` with the filled title/body.
   - **Bitbucket**: generate the PR creation URL and print the title + body ready to paste:

     ```
     URL: https://bitbucket.org/<org>/<repo>/pull-requests/new?source=<branch-name>&dest=<base-branch>

     Title: <commit subject>

     Body:
     <filled template>
     ```

     Present the URL, title, and body to the user — they open the URL and paste the title/body directly. Do **not** use `gh pr create` for a Bitbucket-hosted repo.

## Important

- Never push or create a PR without explicit user approval.
- Use real verification results — never fabricate percentages or counts.
- If any verification step fails, report the failures before presenting the PR template.
