import { colors, cssColorVars } from './colors';
import { spacing as spacingScale, pagePadding, sectionGap, cardPadding } from './spacing';
import { fontFamily, fontSize, fontWeight } from './typography';
import { radius, radiusClass } from './radius';
import { shadows } from './shadows';
import { animations, transition } from './animations';
import { breakpoints } from './breakpoints';
import { zIndex } from './zindex';
import { riskColors, riskLevels, riskClassName, scoreToRiskLevel, normalizeRiskLabel } from './risk';
import { statusColors, statusClassName } from './status';
import { badgeBase } from './badges';
import { cardBase, cardPadding as cardPad, cardShell } from './cards';
import { tableShell, tableBase, tableHead, tableRow, tableRowSelected, tableCell, tableHeaderCell } from './tables';
import { forms } from './forms';
import { charts } from './charts';
import { sidebar } from './sidebar';
import { layout } from './layout';
import { calendar } from './calendar';

/** Tailwind class presets derived from spacing scale */
const spacing = {
  ...spacingScale,
  xs: 'p-2',
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6',
  xl: 'p-8',
  page: pagePadding,
  section: sectionGap,
  card: cardPad,
};

/** Semantic status shortcuts */
const status = {
  colors: statusColors,
  className: statusClassName,
  error: statusColors.failed,
  success: statusColors.complete,
  warning: statusColors.in_progress,
  info: statusColors.open,
  muted: statusColors.pending,
};

/** Semantic risk shortcuts — theme.risk.HIGH etc. */
const risk = {
  colors: riskColors,
  levels: riskLevels,
  className: riskClassName,
  scoreToRiskLevel,
  normalizeRiskLabel,
  LOW: riskColors.LOW,
  MEDIUM: riskColors.MEDIUM,
  HIGH: riskColors.HIGH,
  CRITICAL: riskColors.CRITICAL,
};

/** Semantic card shortcuts */
const card = {
  background: 'bg-card',
  foreground: 'text-card-foreground',
  border: 'border border-border',
  radius: radiusClass.card,
  padding: cardPad,
  base: cardBase,
  shell: cardShell,
  dashed: 'rounded-2xl border border-dashed border-border bg-card p-8',
  header: 'px-5 py-4 border-b border-border',
};

/** Text utilities */
const text = {
  heading: 'text-2xl font-bold text-foreground',
  subheading: 'text-lg font-semibold text-foreground',
  sectionTitle: 'font-bold text-foreground',
  body: 'text-sm text-foreground',
  muted: 'text-sm text-muted-foreground',
  label: 'text-xs text-muted-foreground',
  mono: 'font-mono text-xs',
};

/** Alert / warning surfaces */
const alert = {
  warning: 'rounded-xl border border-warning/30 bg-warning/10 p-4 text-sm text-warning',
  error: 'rounded-xl border border-danger/30 bg-danger/10 p-4 text-sm text-danger',
  info: 'rounded-xl border border-info/30 bg-info/10 p-4 text-sm text-info',
};

/** Semantic table shortcuts */
const table = {
  shell: tableShell,
  base: tableBase,
  head: tableHead,
  row: tableRow,
  rowSelected: tableRowSelected,
  cell: tableCell,
  headerCell: tableHeaderCell,
};

export const theme = {
  colors,
  cssColorVars,
  spacing,
  typography: { fontFamily, fontSize, fontWeight, body: 'text-sm', heading: 'text-2xl font-bold tracking-tight' },
  radius,
  radiusClass,
  shadows,
  animations,
  transition,
  breakpoints,
  zIndex,
  risk,
  status,
  badgeBase,
  card,
  text,
  alert,
  table,
  forms,
  charts,
  sidebar,
  layout,
  calendar,
};

export default theme;
