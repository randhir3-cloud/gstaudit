# ADR-002: Theme System

**Status:** Accepted  
**Date:** 2026-07-09  
**Deciders:** GAIS core team

## Context

GAIS is used for extended audit sessions. Officers need a readable UI in varying lighting conditions. The application must maintain visual consistency for risk signaling (success, warning, critical) across dashboard, comparison, investigation, and report views.

## Decision

Implement theming with:

1. **Tailwind CSS 3** with `darkMode: 'class'`
2. **Default theme: dark**
3. **Toggle** stored in `localStorage` key `theme`, applied to `<html class="dark">`
4. **Palette:** zinc neutrals + semantic accents (blue primary, emerald success, amber warning, rose critical)
5. **Typography:** DM Sans (UI), JetBrains Mono (tabular numbers)

Configuration files:

- `frontend/tailwind.config.js`
- `frontend/src/index.css`
- `frontend/src/App.jsx` (toggle state)

## Consequences

### Positive

- Instant theme switch without page reload
- Consistent utility classes across all components
- Dark-first suits data-dense audit dashboards
- Semantic colors align with GST risk levels

### Negative

- Some components (`ComparisonStatusCards.jsx`) lack full dark variants on status pills
- No centralized CSS custom properties yet — theme changes require Tailwind class updates
- Risk colors duplicated across components (not a single `RiskBadge` primitive)

## Future Direction

Migrate semantic tokens to CSS variables:

```css
:root { --risk-critical: theme('colors.rose.600'); }
.dark { --risk-critical: theme('colors.rose.400'); }
```

Documented in [THEME_GUIDE.md](../THEME_GUIDE.md).

## Alternatives Considered

| Alternative | Why rejected |
|-------------|--------------|
| Light-only | Officer feedback favored dark for long sessions |
| CSS-in-JS (styled-components) | Tailwind already adopted; smaller bundle |
| System preference only | Explicit toggle preferred for audit room projectors |

## References

- [THEME_GUIDE.md](../THEME_GUIDE.md)
- [UI_STANDARDS.md](../UI_STANDARDS.md)
- `frontend/src/components/Layout.jsx`
