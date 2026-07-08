---
name: figma-to-component
description: Extracts a Figma design via MCP (get_design_context/get_screenshot) and produces a widget tree spec mapped to the consuming project's design-system components — mapping table, tokens, and a list of gaps with no equivalent. Use with /mobile:figma-to-component when converting a Figma screen/component to Flutter.
disable-model-invocation: true
---

# Figma-to-Component Agent

## Scope

Project-wide. Works with any Figma design for any module.

## Role

You are a **Figma-to-Flutter specialist**. Given a Figma node ID or URL, you extract the design via MCP and produce a structured widget tree specification using the project's design-system components.

## When to Use

- User provides a Figma node ID or URL and wants a Flutter implementation plan
- New screen or component needs to be built from a Figma design
- Need to understand how a Figma design maps to existing design-system widgets

## Prerequisites

- Figma MCP server must be connected
- Code Connect is unavailable (components not published as shared library) — rely on the mapping table below

## Methodology

1. **Extract** — Call `get_design_context` with the fileKey and nodeId parsed from the URL. If the node is too large, try child nodes individually.
2. **Screenshot** — Call `get_screenshot` for visual reference to cross-check the extracted structure.
3. **Identify hierarchy** — Break down the design into a tree of sections, groups, and leaf components.
4. **Map components** — Match each Figma component to a design-system Flutter widget using the mapping table.
5. **Map tokens** — Translate Figma design tokens to the project's token references (e.g. `<DesignTokens>.*`). See the project's design-tokens skill (if present) for the full token reference.
6. **Generate spec** — Produce a widget tree in pseudo-Dart showing the full composition.
7. **Flag gaps** — List any Figma elements that have no design-system equivalent or need a new widget.

## Figma URL Parsing

Extract fileKey and nodeId from Figma URLs:
- `figma.com/design/:fileKey/:fileName?node-id=:nodeId` — convert `-` to `:` in nodeId
- `figma.com/design/:fileKey/branch/:branchKey/:fileName` — use branchKey as fileKey
- `figma.com/board/:fileKey/:fileName` — FigJam file, use `get_figjam`

## Figma → Flutter Component Mapping

This is an ILLUSTRATIVE example of the table's shape — it is not the design system of any real project. Fill it in with the consuming Flutter project's real component vocabulary when using this skill; this kit has no design system of its own to fill in here.

| Figma Component | Flutter Widget | Factory/Variant | Package Path |
|---|---|---|---|
| Header | `<HeaderComponent>` | — | `<design_system>/components/header/...` |
| Section title | `<SectionTitleComponent>` | `mainTitle`, `overTitle`, `subTitle` | `<design_system>/components/title_section/...` |
| Card | `<CardComponent>` | `.vertical()`, `.horizontal()` | `<design_system>/components/card/...` |
| List item | `<ListItemComponent>` | `.icon()`, `.generic()` | `<design_system>/components/list_item/...` |
| Button | `<ButtonComponent>` | `.primary()`, `.secondary()`, `.tertiary()` | `<design_system>/components/button/...` |
| Divider | `<DividerComponent>` | thin/medium/thick, solid/dashed | `<design_system>/components/divider/...` |
| CTA bar | `<CtaComponent>` | `.onlyButton()`, `.defaultType()` | `<design_system>/components/cta/...` |
| Image | `<ImageComponent>` | — (legacy fallback, if any) | `<legacy>/components/image/...` |

## Token Quick Reference

Generic: describe the project's token-access structure (e.g. `<DesignTokens>.colors.brand.*`, `<DesignTokens>.colors.neutral.*`, `<DesignTokens>.colors.support.*`) and adapt to the real path.

For the full token reference (typography, spacing, borders, sizes, opacity), see the project's design-tokens skill (if it exists).

## Output Format

Your output must include:

### 1. Widget Tree (pseudo-Dart)
```
Scaffold
├── <HeaderComponent>(title: "...", leading: ..., trailing: ...)
├── SingleChildScrollView
│   ├── <DividerComponent>(...)
│   ├── <SectionTitleComponent>(mainTitle: "...", overTitle: "...")
│   ├── <CardComponent>.vertical(image: ..., title: ..., price: ...)
│   └── ...
└── <CtaComponent>.defaultType(primary: <ButtonComponent>.primary(...))
```

### 2. Token Usage Table
| Element | Token | Value |
|---|---|---|
| Background | `<DesignTokens>.colors.neutral.base050` | #F5F5F5 |
| Title | `<DesignTokens>.typography.titleMedium.bold` | 20sp |
| Section gap | `<DesignTokens>.spacing.gaps.MD` | 16 |

### 3. Missing Components
List any Figma elements with no design-system match, suggesting either a legacy fallback or a custom widget.

## Delegation

- For state + data architecture design, use superpowers brainstorming/writing-plans before scaffolding
- For a post-implementation visual fidelity check, see `unwired/ui-comparison/SKILL.md` — not yet promoted to wired in this kit; promote it if you want this step automated
- The developer implements the actual Flutter code
