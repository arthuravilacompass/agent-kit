# UI Comparison — Output Format

## 1. Fidelity Scorecard

| Category | Score | Weight | Notes |
|---|---|---|---|
| Layout structure | 8/10 | 20% | Missing bottom divider before CTA |
| Token compliance | 9/10 | 25% | All tokens correct |
| Component selection | 7/10 | 20% | Used a raw framework primitive instead of the design-system divider component |
| Spacing & alignment | 8/10 | 15% | Top padding uses raw `16` instead of the spacing token |
| Typography | 10/10 | 10% | All text styles from design tokens |
| Colors & theming | 9/10 | 10% | One color hardcoded |
| **Overall** | **8.4** | | **Good — minor adjustments** |

## 2. Discrepancy Table

| # | Category | Figma Design | Implementation | Severity | Fix |
|---|---|---|---|---|---|
| 1 | Component | `<DividerComponent>` | raw framework primitive | major | Replace with the design-system divider component |
| 2 | Spacing | 16dp gap | hardcoded `16` | major | Use the project's spacing token (e.g. `spacing.gaps.MD`) |
| 3 | Layout | Bottom divider before CTA | Missing | minor | Add the divider component above the CTA |

## 3. Token Mapping Comparison

| Element | Figma Value | Expected Token | Used In Code | Match? |
|---|---|---|---|---|
| Background | #F5F5F5 | `neutral.base050` | `neutral.base050` | Yes |
| Title | 20sp Bold | `typography.titleMedium.bold` | `typography.titleMedium.bold` | Yes |
| Gap | 16dp | `spacing.gaps.MD` | hardcoded `16` | No — raw value |
