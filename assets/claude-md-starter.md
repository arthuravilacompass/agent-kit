# claude-md-starter.md — CLAUDE.md skeleton

This file isn't read by Claude Code — it's a template. Copy the body below (starting at `# CLAUDE.md`) into the consuming project's `CLAUDE.md` and fill in the placeholders (`<...>`). The structure comes from a real `CLAUDE.md`, but all domain/company-specific content has been removed — what's left is the *shape*: which sections exist, what each one should contain, and the guiding principle of "pointer, not inline content".

## Guiding principle: pointer, not inline content

The root `CLAUDE.md` is the most expensive thing in the project's context cost — it loads every session. Golden rule: if the content is long enough to deserve its own section with examples, it lives in a separate doc/skill/rule and `CLAUDE.md` only points there (`see file.md §Section`). What stays inline is what needs to be available in one sentence at all times — project identity, one-line conventions, and the pointers themselves.

---

## Template body

```markdown
# CLAUDE.md

## Project Identity

**<Project Name>** is <one sentence: what the product is and who it's for>.

- **<Variation axis 1, e.g. supported platforms/brands>**: <list>
- **<Variation axis 2, e.g. languages>**: <list>
- **Main integrations**: <short list — analytics, crash reporting, payments, etc.>

---

## Architecture

<1-2 sentences: high-level layers/architectural pattern>. Full diagram and module catalog: `<path>/CLAUDE.md` §Architecture.

<Pointers to where structural decisions live — environment setup, module convention, etc. — not the content itself.>

---

## Key Patterns

<3-6 key patterns of the project, one line each, format "Name: short description + where to see more if you need detail.">

**<Pattern 1, e.g. Optimistic updates>:** <one-line description>. See `<reference>`.

**<Pattern 2, e.g. Navigation>:** <one-line description>.

**<Pattern 3, e.g. Error handling>:** <one-line description>.

**<Pattern 4, e.g. L10n>:** <one-line description>.

**<Pattern 5, e.g. Design system>:** <objective, verifiable rule — e.g. "every visual value comes from `<TokenSystem>.*`, never hardcoded">.

**Code review:** <team convention for review comments — prefixes, language, where the checklist is documented>.

**Advisor checkpoints:** <if the project uses escalation checkpoints to a stronger reviewer (pre-plan/post-plan/pre-done or equivalent), document it here in one line + a pointer to the mechanism>.

---

## Language

- Code, identifiers, commit messages → **<language>** (imperative mood).
- PR descriptions, review comments, project docs → **<language>**.

---

## Model Strategy

- **<Model A>** — <when to use: e.g. synthesis, structural critique, brainstorming, architecture decisions>.
- **<Model B>** — <when to use: e.g. execution — code, fixes, reviews, investigation>.
- **<Model C>** — <when to use: e.g. fallback and lower-cost long planning>.
- Use `/clear` between independent tasks.

---

> **Practical guide**: `<path to the operator's manual>` · Commands: `<path>` · Rules: `<path>` · Skills: `<path>` · **Toolkit map**: `<path>`
```

---

## How to fill it in

1. **Project Identity** — don't skip this even on a small project; it anchors everything else. One purpose sentence + the project's real variation axes (don't invent a category the project doesn't have).
2. **Architecture** — if the project already has an architecture doc, this block is just the pointer + 1-2 orienting sentences. Don't duplicate the diagram here.
3. **Key Patterns** — each line must be verifiable (someone can check whether it was followed by looking at the diff), not vague advice. If the pattern needs a code example, it lives in a skill/rule, not here.
4. **Language** — only worth declaring if the project actually mixes languages (code in English, communication in another language, etc.); if everything's in the same language, remove the section.
5. **Model Strategy** — name the real models the team uses and the criterion for when to switch; don't copy a three-model strategy if the project only uses one.
6. **Advisor checkpoints** — only include this if the project actually has an escalation mechanism (blind subagent, external reviewer, etc.); don't describe an aspirational mechanism that doesn't exist yet.
7. **Footer of pointers** — the file's last line should link to everything that has its own depth (operator's guide, commands, rules, skills). If the project doesn't have these artifacts yet, don't add the link — create the section once the artifact exists.
