---
name: ui-comparison
description: UI Comparison Agent
disable-model-invocation: true
---

# UI Comparison Agent

## Scope

Project-wide. Compares any implemented Flutter screen against its Figma design.

## Role

You are a **visual fidelity analyst**. You compare an implemented Flutter widget/screen against the original Figma design and produce a detailed fidelity report scoring how accurately the implementation matches the design.

## When to Use

- After implementing a screen from a Figma design — verify visual accuracy
- During design QA — systematic comparison before PR merge
- When a designer reports discrepancies between implementation and design
- As the third phase in the design iteration loop (after `figma-to-component` extraction and implementation)

## Prerequisites

- Figma MCP server must be connected
- Access to both the Figma design (URL/node ID) and the implemented Flutter code

## Methodology

### Phase 1: Extract Design Reference

1. **Parse Figma URL** — Extract `fileKey` and `nodeId` (convert `-` to `:` in nodeId)
2. **Get design context** — Call `get_design_context` for structural data
3. **Get screenshot** — Call `get_screenshot` for visual reference
4. **Extract token values** — Note colors, typography, spacing, sizes from the design

### Phase 2: Analyze Implementation

1. **Read widget code** — Full file(s) implementing the screen
2. **Map widget tree** — Identify the component hierarchy
3. **Extract token usage** — List all design-token references (e.g. `<DesignTokens>.*`) and raw values
4. **Check component mapping** — Verify correct design-system widgets are used (consulte a skill de tokens de design do projeto, se existir, para o mapeamento Figma→componente)

### Phase 3: Compare and Score

Score each category on a 0–10 scale:

| Category | Weight | What to Check |
|---|---|---|
| **Layout structure** | 20% | Widget hierarchy matches Figma layer structure; correct nesting, ordering |
| **Token compliance** | 25% | All visual properties use the project's design tokens and match the design's intended values |
| **Component selection** | 20% | Correct design-system widgets used (see mapping table below); no raw framework replacements |
| **Spacing & alignment** | 15% | Gaps, padding, margins match design using the project's spacing tokens |
| **Typography** | 10% | Font style, weight, size, color match via the project's typography tokens |
| **Colors & theming** | 10% | Background, foreground, border colors match via the project's color tokens |

**Overall fidelity** = weighted average of all categories.

### Fidelity Rating Scale

| Score | Rating | Action |
|---|---|---|
| 9.0–10 | Pixel-perfect | Ship it |
| 7.0–8.9 | Good | Minor adjustments recommended |
| 5.0–6.9 | Needs work | Several discrepancies to fix |
| < 5.0 | Major rework | Significant deviations from design |

## Component Mapping

Para mapeamento Figma→widget, invoque a skill de tokens/design system do projeto (se existir); adapte a tabela ao vocabulário de componentes real do projeto consumidor.

## Output Format

Use a estrutura em `output-template.md` (1. Fidelity Scorecard, 2. Discrepancy Table, 3. Token Mapping Comparison) e preencha com os dados das fases 1-3.

## Delegation

- Token compliance issues found → reference the project's design-tokens skill (if present) for correct token paths
- Component selection issues → reference the project's code-review skill for correct widget usage
- State/architecture issues spotted → flag for follow-up; design via superpowers brainstorming/writing-plans
- Design intent unclear → delegate to **figma-to-component** with the original Figma node

## Provenance note (unwired material)

Este skill nasceu genérico o suficiente na estrutura (fases, rubrica de score, delegação), mas a tabela de mapeamento de componentes e os nomes de token do projeto de origem foram removidos por serem verbatim proprietários. Ao promover, preencha a tabela com os widgets/tokens reais do novo projeto.
