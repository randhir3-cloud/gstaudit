# Design System

GAIS design system — single source of truth for all UI tokens and component styling rules.

**Status:** v0.3 in progress (tokens scaffolded; page migration ongoing)

See [PRE_V1_ROADMAP.md](./PRE_V1_ROADMAP.md) Phase A for full plan.

---

## Golden Rule

```jsx
// ❌ Never in feature components
<div className="bg-zinc-900 text-red-500 rounded-xl p-4" />

// ✅ Always from theme
import theme from '../theme/theme';
<div className={cn(theme.card.shell, theme.spacing.md)} />
<span className={theme.status.error}>Error</span>
```

---

## Token Modules

All live under `frontend/src/theme/`:

| Module | Export | Example accessor |
|--------|--------|------------------|
| `colors.js` | CSS var names, semantic map | `theme.colors.danger` |
| `typography.js` | Fonts, sizes | `theme.typography.body` |
| `spacing.js` | Scale + presets | `theme.spacing.md` |
| `radius.js` | Radius scale | `theme.radius.card` |
| `shadows.js` | Elevation | `theme.shadows.card` |
| `animations.js` | Motion presets | `theme.animations.fadeIn` |
| `breakpoints.js` | Responsive | `theme.breakpoints.lg` |
| `zindex.js` | Layers | `theme.zindex.modal` |
| `tables.js` | Table parts | `theme.table.head` |
| `forms.js` | Form field styles | `theme.forms.input` |
| `charts.js` | Chart palette | `theme.charts.series[0]` |
| `cards.js` | Card shell | `theme.card.background` |
| `sidebar.js` | Nav shell | `theme.sidebar.item` |
| `layout.js` | Page structure | `theme.layout.pageMaxWidth` |
| `risk.js` | Audit risk | `theme.risk.CRITICAL` |
| `status.js` | Workflow status | `theme.status.error` |
| `theme.js` | **Unified export** | `import theme from './theme'` |

---

## Semantic Accessors (`theme.js`)

The unified `theme` object exposes dot-path accessors for components:

```js
theme.card.background    // 'bg-card'
theme.card.radius        // 'rounded-2xl'
theme.card.shell         // full card class string
theme.spacing.md         // 'p-4'
theme.spacing.page       // page padding preset
theme.status.error       // status color classes
theme.status.success
theme.risk.HIGH          // risk badge classes
theme.table.shell        // scrollable table container
theme.forms.input        // input field classes
theme.layout.pageMaxWidth // 'max-w-7xl'
theme.animations.spinner // 'animate-spin'
```

---

## Migration Checklist

Track component migration from inline Tailwind to theme tokens:

### Pages

- [x] `Dashboard.jsx`
- [ ] `ComparisonScreen.jsx`
- [ ] `InvestigationPage.jsx`
- [ ] `AuditReportPreview.jsx`
- [ ] `MergePage.jsx`
- [ ] `WorkbookViewer.jsx`

### Component groups

- [x] `components/dashboard/*` (all 22 components)
- [x] `components/Layout.jsx`
- [ ] `components/investigation/*`
- [ ] `components/eway/*`
- [ ] `components/merge/*`

### Done

- [x] CSS variables in `index.css`
- [x] Tailwind semantic colors in `tailwind.config.js`
- [x] Core token files + `theme/calendar.js`
- [x] Dashboard reference implementation complete (v0.3.1)
- [x] `DataTable`, shared cards, badges, `Icons.*` in dashboard

---

## Dark Mode

Toggle via `document.documentElement.classList` (`dark` class). All tokens use CSS variables that switch in `.dark { }` block — see [THEME_GUIDE.md](./THEME_GUIDE.md).

---

## Related

- [THEME_GUIDE.md](./THEME_GUIDE.md) — color palette reference
- [UI_STANDARDS.md](./UI_STANDARDS.md) — component usage rules
- [ADR-002-Theme.md](./DECISIONS/ADR-002-Theme.md)
