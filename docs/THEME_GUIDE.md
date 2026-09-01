# Theme Guide

GAIS supports **light** and **dark** themes with Tailwind CSS class-based dark mode.

## Configuration

**Tailwind** (`frontend/tailwind.config.js`):

```javascript
export default {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        zinc: { 950: '#09090b' },
      },
    },
  },
};
```

**Toggle** (`frontend/src/App.jsx`):

- State: `theme` — `'dark'` | `'light'`
- Persistence: `localStorage.setItem('theme', theme)`
- Application: `document.documentElement.classList.add('remove')('dark')`
- Default: **dark**

## Design Tokens

### Typography

| Token | Value | Usage |
|-------|-------|-------|
| `--font-sans` | DM Sans (Google Fonts) | All UI text via `:root` in `index.css` |
| `--font-mono` | JetBrains Mono | `.font-mono`, tabular numbers |

### Surfaces

| Token (conceptual) | Light | Dark |
|--------------------|-------|------|
| `--bg-app` | `bg-zinc-50` | `dark:bg-zinc-950` |
| `--bg-header` | `bg-white/50 backdrop-blur-md` | `dark:bg-zinc-900/50` |
| `--bg-card` | `bg-white` | `dark:bg-zinc-900` |
| `--border-default` | `border-zinc-200` | `dark:border-zinc-800` |

### Text

| Role | Classes |
|------|---------|
| Heading | `text-zinc-950 dark:text-white font-bold` |
| Body | `text-zinc-900 dark:text-zinc-100` |
| Secondary | `text-zinc-600 dark:text-zinc-300` |
| Muted | `text-zinc-500 dark:text-zinc-400` |
| Footer | `text-zinc-400 dark:text-zinc-500` |

### Brand

| Token | Value |
|-------|-------|
| Primary | `blue-600` / hover `blue-700` |
| Primary shadow | `shadow-blue-500/20` on logo icon |
| Link | `text-blue-600 dark:text-blue-400` |

## Risk Colors

Used consistently across comparison, investigation, and intelligence UIs.

### Comparison result types

Mapped in UI via filter links and table badges:

| Result type | Semantic | Tailwind accent |
|-------------|----------|-----------------|
| `MATCHED` | Success | `emerald` |
| `MISSING_IN_GSTR1` | Critical omission | `rose` |
| `MISSING_IN_EWAY` | High omission | `orange` / `rose` |
| `GSTIN_MISMATCH` | Identity error | `amber` |
| `VALUE_MISMATCH` | Amount error | `amber` |
| `DATE_MISMATCH` | Timing error | `zinc` / `amber` |
| `DUPLICATE` | Data quality | `amber` |

### Risk levels (backend enum)

From `comparison/comparison_types.py`:

| Level | Score threshold | UI treatment |
|-------|-----------------|--------------|
| `LOW` | peak < 40 | neutral / zinc |
| `MEDIUM` | peak ≥ 40 | amber |
| `HIGH` | peak ≥ 80 | orange |
| `CRITICAL` | peak ≥ 95 | rose |

Per-record weights in `risk_engine.py`:

| Result type | Base score |
|-------------|------------|
| MISSING_IN_GSTR1 | 100 |
| MISSING_IN_EWAY | 95 |
| GSTIN_MISMATCH | 80 |
| VALUE_MISMATCH | 70 |
| DATE_MISMATCH | 40 |
| DUPLICATE | 30 |

### Investigation priority

| Priority | Badge classes |
|----------|---------------|
| Critical | `bg-rose-100 text-rose-800 dark:bg-rose-950/40` |
| High | orange variant |
| Medium | amber variant |
| Low | zinc variant |

### Calendar month cells

`FinancialYearCalendar.jsx`:

```javascript
const STATUS_STYLE = {
  uploaded: 'bg-emerald-50 ... border-emerald-200',
  missing: 'bg-zinc-100 ... border-zinc-200',
  duplicate: 'bg-amber-50 ... border-amber-200',
};
```

## Dark Mode Specifics

### Scrollbars

Custom webkit scrollbar in `index.css`:

- Light thumb: `#e4e4e7`
- Dark thumb: `#27272a`, hover `#3f3f46`

### Status pills (light-only caveat)

Some status badges in `ComparisonStatusCards.jsx` use light-mode-only backgrounds (`bg-emerald-100`). When extending, always add `dark:` variants per [UI_STANDARDS.md](./UI_STANDARDS.md).

### Gradients

EWB success card: `bg-gradient-to-r from-emerald-50/70 to-white dark:from-emerald-950/20 dark:to-zinc-900`

## Theme Toggle UI

Located in `Layout.jsx` header:

- Dark mode active → show **Sun** icon (click to go light)
- Light mode active → show **Moon** icon

Button: `bg-zinc-100 dark:bg-zinc-800` with border.

## Future: CSS Variables

ADR-002 recommends migrating semantic tokens to CSS custom properties for easier theming. Current v0.1 uses Tailwind classes directly. A future pass could define:

```css
:root {
  --color-risk-critical: theme('colors.rose.600');
}
.dark {
  --color-risk-critical: theme('colors.rose.400');
}
```

## Related

- [UI_STANDARDS.md](./UI_STANDARDS.md)
- [DECISIONS/ADR-002-Theme.md](./DECISIONS/ADR-002-Theme.md)
