/** Audit risk level tokens — use RiskBadge or these class maps. */
export const riskLevels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];

export const riskColors = {
  LOW: {
    bg: 'bg-emerald-100 dark:bg-emerald-950/40',
    text: 'text-emerald-800 dark:text-emerald-300',
    border: 'border-emerald-200 dark:border-emerald-800',
  },
  MEDIUM: {
    bg: 'bg-amber-100 dark:bg-amber-950/40',
    text: 'text-amber-800 dark:text-amber-300',
    border: 'border-amber-200 dark:border-amber-800',
  },
  HIGH: {
    bg: 'bg-orange-100 dark:bg-orange-950/40',
    text: 'text-orange-800 dark:text-orange-300',
    border: 'border-orange-200 dark:border-orange-800',
  },
  CRITICAL: {
    bg: 'bg-red-100 dark:bg-red-950/40',
    text: 'text-red-800 dark:text-red-300',
    border: 'border-red-200 dark:border-red-800',
  },
};

/** Map numeric score or label variants to risk level */
export function scoreToRiskLevel(score) {
  if (score == null) return 'LOW';
  const n = Number(score);
  if (Number.isNaN(n)) return 'LOW';
  if (n >= 80) return 'CRITICAL';
  if (n >= 60) return 'HIGH';
  if (n >= 30) return 'MEDIUM';
  return 'LOW';
}

export function normalizeRiskLabel(label) {
  if (!label) return 'LOW';
  const u = String(label).toUpperCase();
  if (riskLevels.includes(u)) return u;
  if (u.includes('CRIT')) return 'CRITICAL';
  if (u.includes('HIGH')) return 'HIGH';
  if (u.includes('MED')) return 'MEDIUM';
  return 'LOW';
}

export function riskClassName(level) {
  const key = normalizeRiskLabel(level);
  const c = riskColors[key] || riskColors.LOW;
  return `${c.bg} ${c.text} ${c.border}`;
}
