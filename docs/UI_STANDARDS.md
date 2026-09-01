# UI Standards

Visual and component conventions for the GAIS frontend (`frontend/src/`).

## Design System

GAIS uses **Tailwind CSS utility classes** with a **zinc neutral palette** and **semantic accent colors**. Typography: **DM Sans** (UI), **JetBrains Mono** (tabular/code). Defined in `frontend/src/index.css` and `frontend/tailwind.config.js`.

## Component Usage Rules

### 1. Prefer composition over new primitives

Before creating a component, check [COMPONENT_LIBRARY.md](./COMPONENT_LIBRARY.md). Dashboard widgets (`components/dashboard/`) are single-purpose and composed in `pages/Dashboard.jsx`.

### 2. Page structure

Every page follows this layout pattern:

```jsx
<div className="space-y-6">
  <DealerHeader />           {/* when dealer context exists */}
  <section>...</section>     {/* primary content cards */}
</div>
```

Cards use: `rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5`

### 3. Interactive elements

| Element | Classes |
|---------|---------|
| Primary button | `bg-blue-600 hover:bg-blue-700 text-white rounded-xl px-4 py-2.5 text-sm font-medium` |
| Destructive text | `text-rose-600 dark:text-rose-400` |
| Success banner | `bg-emerald-50 dark:bg-emerald-950/20 border-emerald-200` |
| Warning banner | `bg-amber-50 dark:bg-amber-950/20 border-amber-200` |

### 4. Icons

Use **lucide-react** exclusively. Standard size: `h-4 w-4` inline, `h-5 w-5` in buttons, `h-6 w-6` in header branding.

### 5. Testability

Add `data-testid` to:

- Primary actions (`run-comparison-btn`)
- Status indicators (`comparison-status`, `audit-not-ready`)
- Dynamic content regions (`report-error`, `duplicate-panel`)

Playwright specs in `e2e/` depend on these attributes.

## shadcn/ui Adoption

**Status:** Partial — dependencies installed, full component library not vendored.

Installed packages (`frontend/package.json`):

- `@radix-ui/react-dialog`
- `@radix-ui/react-tooltip`
- `@radix-ui/react-slot`
- `class-variance-authority`, `clsx`, `tailwind-merge`

There is **no** `frontend/src/components/ui/` directory yet. Most UI is hand-built with Tailwind. Custom tooltips use CSS hover (`StatusTooltip.jsx`) rather than Radix Tooltip.

**When adding new overlays:** prefer Radix Dialog primitives for accessibility (focus trap, ESC dismiss). See [DECISIONS/ADR-006-ShadcnAdoption.md](./DECISIONS/ADR-006-ShadcnAdoption.md).

## No Hardcoded Colors

### Allowed

- **Tailwind palette tokens:** `zinc-*`, `blue-*`, `emerald-*`, `amber-*`, `rose-*`
- **Opacity modifiers:** `dark:bg-zinc-900/50`, `border-emerald-200/70`
- **CSS variables:** none custom yet — use Tailwind classes

### Forbidden

- Raw hex/rgb in JSX: ~~`#09090b`~~, ~~`style={{ color: '#fff' }}`~~
- Inline `style={{ backgroundColor: ... }}` except dynamic widths (e.g. readiness bar progress)
- One-off colors outside the semantic map

### Semantic color map

| Meaning | Light | Dark |
|---------|-------|------|
| Background | `bg-zinc-50` | `dark:bg-zinc-950` |
| Surface / card | `bg-white` | `dark:bg-zinc-900` |
| Border | `border-zinc-200` | `dark:border-zinc-800` |
| Primary text | `text-zinc-950` | `dark:text-white` |
| Muted text | `text-zinc-500` | `dark:text-zinc-400` |
| Primary action | `bg-blue-600` | same |
| Success / uploaded | `emerald-*` | `dark:emerald-950/40` |
| Warning / duplicate | `amber-*` | `dark:amber-950/40` |
| Error / critical | `rose-*` | `dark:rose-950/40` |

Risk priority badges (`InvestigationDetailsPanel.jsx`):

```javascript
const PRIORITY_STYLE = {
  Critical: 'bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-300',
  High: 'bg-orange-100 text-orange-800 ...',
  Medium: 'bg-amber-100 text-amber-800 ...',
  Low: 'bg-zinc-100 text-zinc-700 ...',
};
```

## Responsive Design

- Mobile-first with `sm:`, `md:` breakpoints
- Dashboard calendar: compact cells on mobile (`FinancialYearCalendar.jsx`)
- Navigation wraps on small screens (`Layout.jsx`)
- Dedicated viewport E2E: `e2e/dashboard-viewport.spec.js` (tablet + mobile)

## Accessibility

- Theme toggle has `title="Toggle theme"`
- `StatusTooltip` uses `role="tooltip"` and `aria-describedby`
- Nav uses React Router `NavLink` with visible active state (not color alone)
- Radix Dialog (when adopted) provides focus management for modals

## Animation

Global fade-in: `.animate-fade-in` in `index.css` (200ms ease-out). Theme transition on `body`: 300ms background/color.

## Related

- [THEME_GUIDE.md](./THEME_GUIDE.md)
- [COMPONENT_LIBRARY.md](./COMPONENT_LIBRARY.md)
