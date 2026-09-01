export { formatDate, formatCount, formatPercent, shortDatasetLabel } from './formatNumbers';

export function formatCurrency(amount, currency = 'INR') {
  if (amount == null || Number.isNaN(Number(amount))) return '—';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency,
    maximumFractionDigits: 2,
  }).format(Number(amount));
}
