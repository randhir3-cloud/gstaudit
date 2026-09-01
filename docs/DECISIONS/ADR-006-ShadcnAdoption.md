# ADR-006: shadcn/ui Adoption

## Status

Accepted (2026-07-09)

## Context

GAIS UI grew organically with Tailwind utility classes duplicated across 30+ components. We need a consistent design system without rewriting every screen.

## Decision

Adopt [shadcn/ui](https://ui.shadcn.com/) patterns:

1. Install foundation: `clsx`, `tailwind-merge`, `class-variance-authority`, Radix primitives
2. Add `components.json` for future CLI installs
3. Create `src/lib/utils.js` with `cn()` helper
4. Ship core wrappers in `src/components/ui/`: Button, Card, Badge, Dialog
5. Domain components in `src/components/common/` wrap ui/ primitives
6. CSS variables in `index.css` + Tailwind theme extension

Do **not** recreate shadcn components that already exist — wrap or import via CLI when needed.

## Consequences

**Positive**

- Consistent focus rings, variants, accessibility from Radix
- Incremental migration — existing screens unchanged until refactored
- AI agents can add new shadcn components via documented `components.json`

**Negative**

- Full shadcn catalog not installed in v0.1 foundation pass
- `@/` path aliases not configured in Vite yet (relative imports used)

## References

- `frontend/components.json`
- `frontend/src/components/ui/`
- `docs/UI_STANDARDS.md`
- `docs/THEME_GUIDE.md`
